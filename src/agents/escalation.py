"""Escalation Agent — produces an engineer-ready diagnostic summary and opens a
high-priority Jira ticket. Runs whenever an upstream agent flags
`escalation_required`."""
from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate

from src.agents._trace import traced
from src.llm import get_chat_llm
from src.mcp.client import get_mcp_client
from src.state import Action, GraphState, ToolResult

_ESCALATION_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are the Escalation agent for an internal IT helpdesk. Your output "
            "is read by an on-call IT engineer who has zero context. Produce a "
            "structured handoff with these sections, in this order:\n\n"
            "PROBLEM — one or two sentences restating what the user asked for, in "
            "the user's own framing.\n\n"
            "USER CONTEXT — id, department, office.\n\n"
            "AGENT CLASSIFICATION — request_type, category, system, severity, confidence.\n\n"
            "PRIOR CONVERSATION — what the assistant has already told the user, if "
            "anything. Include any self-service steps that were suggested. Use 'none' "
            "if this is the first turn.\n\n"
            "AUTOMATION STEPS ALREADY TAKEN — bullet list of tool calls with their status. "
            "Use 'none' if the workflow didn't run.\n\n"
            "DIAGNOSTIC DATA — relevant log events, retrieved doc chunks, or tool outputs "
            "that the engineer should look at first. Quote the events directly.\n\n"
            "SUGGESTED NEXT STEPS — your best 1-3 hypotheses for what to check next.\n\n"
            "Be terse. No marketing language. No apologies.",
        ),
        (
            "human",
            "User message:\n{user_message}\n\nUser context:\n{user_context}\n\n"
            "Intake classification:\n{intake}\n\nReason for escalation:\n{reason}\n\n"
            "Conversation history (oldest → newest):\n{history}\n\n"
            "Tool results so far:\n{tool_results}\n\nRetrieved runbook chunks:\n{retrieved}",
        ),
    ]
)


def _format_history(state: GraphState, max_turns: int = 8) -> str:
    if len(state.messages) <= 1:
        return "(no prior turns)"
    history = state.messages[:-1][-max_turns:]
    if not history:
        return "(no prior turns)"
    lines = []
    for m in history:
        snippet = m.content if len(m.content) <= 500 else m.content[:500] + "…"
        lines.append(f"{m.role}: {snippet}")
    return "\n".join(lines)


def _format_tool_results(state: GraphState) -> str:
    if not state.tool_results:
        return "(none)"
    lines = []
    for tr in state.tool_results:
        status = "ok" if tr.success else f"FAIL: {tr.error}"
        # Cap payload size to keep prompt small
        payload_str = str(tr.payload)
        if len(payload_str) > 400:
            payload_str = payload_str[:400] + "…"
        lines.append(f"- {tr.tool_name} [{status}] {payload_str}")
    return "\n".join(lines)


def _format_retrieved(state: GraphState) -> str:
    if not state.retrieved_docs:
        return "(none)"
    return "\n".join(
        f"- {d.source_file} (chunk {d.chunk_index}): {d.snippet[:200]}…"
        for d in state.retrieved_docs[:3]
    )


def _format_intake(state: GraphState) -> str:
    i = state.intent
    return (
        f"request_type={i.request_type}, category={i.category}, "
        f"system={i.system or 'N/A'}, severity={i.severity}, confidence={i.confidence:.2f}"
    )


@traced("escalation")
def escalation_node(state: GraphState) -> GraphState:
    last_user = state.latest_user_message()
    user_message = last_user.content if last_user else "(no message)"
    user_ctx = (
        f"{state.user.display_name} ({state.user.user_id}), "
        f"department={state.user.department}, office={state.user.office}"
    )
    reason = state.escalation_reason or "Routed to escalation by workflow."

    chain = _ESCALATION_PROMPT | get_chat_llm()
    response = chain.invoke(
        {
            "user_message": user_message,
            "user_context": user_ctx,
            "intake": _format_intake(state),
            "reason": reason,
            "history": _format_history(state),
            "tool_results": _format_tool_results(state),
            "retrieved": _format_retrieved(state),
        }
    )
    summary = (response.content or "").strip()
    state.escalation_summary = summary

    # File the high-priority ticket
    client = get_mcp_client()
    incident_action = Action(
        tool_name="jira.create_incident",
        parameters={
            "summary": f"[{state.intent.category}] {user_message[:80]}",
            "description": summary,
            "severity": state.intent.severity,
        },
        status="RUNNING",
    )
    state.actions.append(incident_action)
    result = client.call_tool(incident_action.tool_name, **incident_action.parameters)
    success = "error" not in result
    state.tool_results.append(
        ToolResult(
            tool_name=incident_action.tool_name,
            success=success,
            payload=result,
            error=result.get("error") if not success else None,
        )
    )
    incident_action.status = "SUCCESS" if success else "FAILED"
    incident_action.result_summary = result.get("summary") or str(result)

    ticket_id = result.get("incident_id") or result.get("ticket_id")
    state.escalation_ticket_id = ticket_id

    # Move the escalation ticket to "In Progress" so it visually surfaces in the
    # human IT team's active work column rather than sitting in the To Do backlog.
    if ticket_id:
        transition_action = Action(
            tool_name="jira.transition_issue",
            parameters={"ticket_id": ticket_id, "target_status": "In Progress"},
            status="RUNNING",
        )
        state.actions.append(transition_action)
        t_result = client.call_tool(transition_action.tool_name, **transition_action.parameters)
        t_success = "error" not in t_result
        state.tool_results.append(
            ToolResult(
                tool_name=transition_action.tool_name,
                success=t_success,
                payload=t_result,
                error=t_result.get("error") if not t_success else None,
            )
        )
        transition_action.status = "SUCCESS" if t_success else "FAILED"
        transition_action.result_summary = t_result.get("summary") or t_result.get("error") or ""

    if ticket_id:
        urgency = " This was flagged as urgent." if state.intent.severity == "high" else ""
        state.final_answer = (
            "We weren't able to answer this from our documentation, so we've transferred "
            "your request to our human IT support team. They'll get back to you as soon "
            f"as possible.{urgency}\n\n"
            f"**Reference: {ticket_id}**"
        )
    else:
        state.final_answer = (
            "We tried to transfer this to our IT team but the ticket system returned an "
            "error. Please try again in a moment, or contact #it-help directly."
        )
    state.escalation_required = True
    return state
