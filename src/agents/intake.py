"""Intake Agent — classifies the incoming user message into a structured Intent.

Multi-turn aware: when prior assistant messages exist, the agent looks for
follow-up signals like "I tried that, it still doesn't work" and bumps the
classification to incident/high so the router escalates to a human."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from src.agents._trace import traced
from src.llm import get_chat_llm
from src.state import GraphState, Intent

_SYSTEM_PROMPT = """You are the Intake agent for a corporate IT helpdesk.
Classify the user's most recent message into the structured schema below.

request_type guide:
- informational: the user is asking for instructions or steps. ANY message that
  contains "how do I…", "what's the process for…", "where do I find…", or that
  asks for steps, even if it's prefixed with a problem statement like
  "I'm locked out — how do I reset my password?". The user wants self-service
  guidance first, not immediate escalation.
- action: a direct, concrete request to have the system perform an operation on
  their behalf, with no question mark. Examples: "provision Figma for me",
  "add me to #data-platform", "order a new monitor". Note: a request like
  "reset my password" is action only when the user is asking the system to do
  it. "How do I reset my password?" is informational.
- incident: the user is reporting that something is broken AND is NOT asking for
  steps. Examples: "the projector is dead, demo starts in 10 min", "my deploy
  is failing right now". Use this only when the user implicitly needs a human
  to act, not when they want to self-serve.
- unclear: you can't tell which of the above this is, OR the request is out of IT's scope.

Tie-breaker: when in doubt between informational and incident, prefer
informational. Users overwhelmingly prefer trying steps themselves first.

Account category specifically (passwords, lockouts, MFA): default to
informational unless the user is EXPLICITLY asking IT to do it for them
(e.g., "MFA is broken, can someone reset it on my end" — that's action).
Phrasings like "I need a password reset" / "I need to reset my password" /
"reset my password please" should be informational — the runbook explains
the self-service flow and that's what the user wants first.

NATURAL PHRASING — these are all real ways users describe IT issues. Use the
INTENT not the wording. Don't require canonical phrasing.

Examples (user phrasing → request_type / category):
- "can you hook me up with figma" → action / software_license
- "i need adobe acrobat asap" → action / software_license
- "give me access to figma plz" → action / software_license
- "want a loom license" → action / software_license
- "my mouse died send me a new one" → action / hardware
- "need a 2nd monitor for wfh" → action / hardware
- "battery on my mac is toast" → action / hardware (request_type=action because user wants a replacement)
- "wifi is busted in the SF office and my call starts in 5" → incident / other / high
- "add me to the data slack pls" → action / access
- "can i get into the finance drive" → action / access
- "im stuck out of my account" → informational / account (user wants the steps)
- "okta is rejecting my password" → informational / account
- "got a new phone, lost my mfa" → informational / account
- "how do i set my OOO" → informational / email
- "what's the deal with email signatures" → informational / email
- "where do i find my new hire checklist" → informational / new_hire
- "i just started today" → informational / new_hire
- "printer on 3 isnt working" → incident / printer
- "how do i scan something" → informational / printer
- "the projector in conf room B is dead, demo in 10" → incident / av / high
- "zoom room not joining the meeting" → incident / av
- "no idea what's going on, my laptop just died" → incident / hardware / high

If the message is missing context but the keywords clearly point to a category
(e.g., "figma access?" or "new keyboard?"), still extract the category — don't
fall back to "other" just because the message is short. Use confidence to
reflect any uncertainty.

category guide:
- software_license: corporate software / SaaS license requests, license issues
- hardware: laptops, monitors, peripherals, keyboards, batteries
- access: Slack channels, mailing lists, drives, repos, group/system permissions
- account: password resets, account lockouts, MFA issues, suspected account compromise
- email: email signature, forwarding, OOO, distribution lists
- printer: printer setup, print failures
- av: conference room displays, projectors, cameras, mics, video calls
- new_hire: day-1 setup, onboarding checklists, "I just started"
- other: anything that doesn't cleanly fit above

severity guide:
- low: routine request, no time pressure
- medium: standard SLA, some impact on the user's day
- high: blocking the user from working right now, OR has a hard external deadline (meeting starting, demo in 10 min, locked out and time-pressured)

confidence is your own self-rated confidence in the request_type+category from 0 to 1.
Set confidence < 0.5 only when the message is genuinely ambiguous or off-topic.

follow_up_after_failed_help — set to true ONLY if the conversation history
shows the assistant previously gave self-service steps AND the user's current
message indicates those steps did not work. Phrases that suggest this:
"that didn't work", "still not working", "tried that already", "doesn't help",
"same error", "same problem". When you set this to true, also set
request_type=incident and severity=high — the user has exhausted self-service
and needs a human.

Extract entities into a list of key/value pairs — software name, hardware item,
channel name, room name, office, etc. Keep keys snake_case and values short strings."""


class EntityPair(BaseModel):
    """One extracted entity as a key/value pair. Using a list of pairs instead of a
    dict because OpenAI's strict structured-output mode rejects open-ended objects."""

    key: str = Field(description="snake_case name (e.g., software, room, channel, hardware)")
    value: str = Field(description="extracted value as a short string")


class IntakeSchema(BaseModel):
    request_type: Literal["informational", "action", "incident", "unclear"]
    category: Literal[
        "software_license",
        "hardware",
        "access",
        "account",
        "email",
        "printer",
        "av",
        "new_hire",
        "other",
    ]
    system: str = Field(description="Affected system, app, or location. Use empty string if N/A.")
    severity: Literal["low", "medium", "high"]
    confidence: float = Field(ge=0.0, le=1.0)
    follow_up_after_failed_help: bool = Field(
        description="True if the user is reporting that previously suggested self-service steps did not work."
    )
    entities: list[EntityPair] = Field(description="Extracted entities as key/value pairs (may be empty list)")


def _format_history(state: GraphState, max_turns: int = 6) -> str:
    """Format the last N messages as 'role: content' lines, excluding the latest
    user message (which the prompt presents separately)."""
    if len(state.messages) <= 1:
        return "(this is the first message in the conversation)"
    history = state.messages[:-1][-max_turns:]
    if not history:
        return "(this is the first message in the conversation)"
    lines = []
    for m in history:
        snippet = m.content if len(m.content) <= 400 else m.content[:400] + "…"
        lines.append(f"{m.role}: {snippet}")
    return "\n".join(lines)


@traced("intake")
def intake_node(state: GraphState) -> GraphState:
    last_user = state.latest_user_message()
    if not last_user:
        state.intent = Intent(request_type="unclear", confidence=0.0)
        return state

    user_ctx = state.user
    prompt = (
        f"{_SYSTEM_PROMPT}\n\n"
        f"User context (for disambiguation only — do not echo in the classification):\n"
        f"- user_id: {user_ctx.user_id}\n"
        f"- department: {user_ctx.department}\n"
        f"- office: {user_ctx.office}\n\n"
        f"Conversation history (oldest → newest, current message excluded):\n"
        f"{_format_history(state)}\n\n"
        f"Current user message to classify:\n{last_user.content}"
    )

    structured_llm = get_chat_llm().with_structured_output(IntakeSchema)
    result: IntakeSchema = structured_llm.invoke(prompt)

    state.intent = Intent(
        request_type=result.request_type,
        category=result.category,
        system=result.system or None,
        severity=result.severity,
        confidence=result.confidence,
        follow_up_after_failed_help=result.follow_up_after_failed_help,
    )
    state.entities = {e.key: e.value for e in result.entities}
    return state
