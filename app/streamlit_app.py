"""Streamlit UI — IT Support ticket portal.

Flow:
    1. User clicks "Submit a ticket" / sees the form on landing.
    2. Types their issue in plain English.
    3. The multi-agent graph processes it.
    4. They see either an answer (Knowledge), an action confirmation (Workflow),
       or a "transferred to human support" message (Escalation).
    5. A satisfaction survey captures 1-5 stars + optional feedback.
    6. They can submit another ticket.

Run:  streamlit run app/streamlit_app.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Make `src` importable when Streamlit runs this file directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st  # noqa: E402

from src.config import SETTINGS  # noqa: E402
from src.graph import build_app  # noqa: E402
from src.state import GraphState, Message, UserContext  # noqa: E402

st.set_page_config(page_title="IT Support", page_icon="🛠️", layout="centered")

FEEDBACK_FILE = Path(__file__).resolve().parent.parent / "feedback.jsonl"


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
def _init_state() -> None:
    defaults = {
        "view": "form",        # form | result
        "history": [],          # list of submitted-ticket records (for the sidebar)
        "result_state": None,   # GraphState of the latest submission
        "user": UserContext(),
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


_init_state()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _outcome_label(state: GraphState) -> str:
    """Map a final GraphState to a short outcome label for the history sidebar."""
    if state.escalation_required and state.escalation_ticket_id:
        return "Transferred to human support"
    if state.knowledge_answer:
        return "Answered from documentation"
    if state.actions and any(a.status == "SUCCESS" for a in state.actions):
        return "Action completed"
    return "Unknown"


def _save_feedback(state: GraphState, rating_stars: int, comment: str) -> None:
    """Append a feedback record. rating_stars is 1-5."""
    record = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "user_id": state.user.user_id,
        "ticket_id": state.escalation_ticket_id,
        "rating_stars": rating_stars,
        "comment": comment.strip(),
        "outcome": _outcome_label(state),
        "request_type": state.intent.request_type,
        "category": state.intent.category,
        "user_message": (state.latest_user_message().content if state.latest_user_message() else ""),
    }
    with FEEDBACK_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def _process_ticket(issue: str) -> None:
    """Run the issue through the multi-agent graph and stash the result."""
    # Carry prior tickets in the same session as conversation history so the
    # Intake agent can detect "I tried that, it didn't work" follow-ups.
    messages: list[Message] = []
    for h in st.session_state.history:
        messages.append(Message(role="user", content=h["issue"]))
        if h.get("answer"):
            messages.append(Message(role="assistant", content=h["answer"]))
    messages.append(Message(role="user", content=issue))

    app = build_app()
    initial = GraphState(messages=messages, user=st.session_state.user)
    final_dict = app.invoke(initial)
    final = GraphState.model_validate(final_dict)

    st.session_state.result_state = final
    st.session_state.history.append(
        {
            "idx": len(st.session_state.history) + 1,
            "issue": issue,
            "answer": final.final_answer or "",
            "outcome": _outcome_label(final),
            "rating": None,
        }
    )
    st.session_state.view = "result"


# ---------------------------------------------------------------------------
# Sidebar — submitter context, system info, history of this session
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Your info")
    user = st.session_state.user
    st.session_state.user = UserContext(
        user_id=st.text_input("User ID", value=user.user_id),
        display_name=st.text_input("Name", value=user.display_name),
        email=st.text_input("Email", value=user.email),
        department=st.text_input("Department", value=user.department),
        office=st.selectbox(
            "Office",
            ["SF", "NYC", "Reno"],
            index=["SF", "NYC", "Reno"].index(user.office),
        ),
    )

    st.divider()
    with st.expander("System info", expanded=False):
        st.write(f"**LLM:** `{SETTINGS.openai_llm_model}`")
        st.write(f"**Embeddings:** `{SETTINGS.openai_embedding_model}`")
        st.write(
            "**Jira:** "
            + (f"real ({SETTINGS.jira_base_url})" if SETTINGS.jira_enabled else "mock (console)")
        )

    st.divider()
    if st.session_state.history:
        st.header("Tickets this session")
        for h in reversed(st.session_state.history):
            with st.expander(f"#{h['idx']} · {h['outcome']}"):
                st.caption(h["issue"])
                if h.get("rating") is not None:
                    st.caption(f"Rating: {'⭐' * h['rating']}")

    if st.button("Reset session", use_container_width=True):
        st.session_state.history = []
        st.session_state.result_state = None
        st.session_state.view = "form"
        st.rerun()


# ---------------------------------------------------------------------------
# Main — two views: ticket form, or result + survey
# ---------------------------------------------------------------------------
st.title("🛠️ IT Support")


def render_form() -> None:
    st.write(
        "Submit a ticket and we'll either answer your question from our documentation, "
        "complete the action for you, or transfer you to our IT team."
    )
    st.write("")

    with st.form("ticket_form", clear_on_submit=True):
        issue = st.text_area(
            "What do you need help with?",
            placeholder=(
                "Describe your issue in your own words. "
                "Examples: 'My mouse died, can I get a new one' · "
                "'How do I set my out-of-office reply' · "
                "'Locked out of my account' · "
                "'I need a Figma license'"
            ),
            height=160,
        )
        submitted = st.form_submit_button("Submit ticket", type="primary", use_container_width=True)

    if submitted:
        if not issue.strip():
            st.warning("Please describe your issue before submitting.")
            return
        with st.spinner("Looking up your issue…"):
            _process_ticket(issue.strip())
        st.rerun()


def render_result() -> None:
    final: GraphState | None = st.session_state.result_state
    if final is None:
        st.session_state.view = "form"
        st.rerun()
        return

    answer = final.final_answer or "(no answer was generated)"
    outcome = _outcome_label(final)

    # Color the response container by outcome
    if "human support" in outcome:
        st.warning(f"**{outcome}**")
    elif "Action completed" in outcome:
        st.success(f"**{outcome}**")
    else:
        st.info(f"**{outcome}**")

    st.markdown(answer)

    # Agent trace
    with st.expander("How we figured this out", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Classification**")
            st.json(final.intent.model_dump(), expanded=False)
            if final.entities:
                st.markdown("**Extracted details**")
                st.json(final.entities, expanded=False)
        with col2:
            if final.actions:
                st.markdown("**Actions taken**")
                for a in final.actions:
                    icon = {"SUCCESS": "✅", "FAILED": "❌"}.get(a.status, "⏳")
                    st.write(f"{icon} `{a.tool_name}` — {a.status}")
                    if a.result_summary:
                        st.caption(a.result_summary)
            if final.retrieved_docs:
                st.markdown("**Sources consulted**")
                for d in final.retrieved_docs:
                    st.caption(f"• {d.source_file} (chunk {d.chunk_index})")
        if final.trace:
            durations = [
                f"{t.node} {t.duration_ms}ms"
                for t in final.trace
                if t.phase == "exit" and t.duration_ms is not None
            ]
            st.caption("Per-agent latency: " + " · ".join(durations))

    st.divider()

    # Survey
    st.subheader("How satisfied were you with this response?")
    rating_idx = st.feedback("stars", key="rating_widget")
    comment = st.text_input(
        "Anything else you'd like to add? (optional)",
        key="comment_widget",
        placeholder="What worked well, or what could be better?",
    )

    col_a, col_b = st.columns([1, 1])
    with col_a:
        submit_disabled = rating_idx is None
        if st.button(
            "Submit feedback",
            type="primary",
            use_container_width=True,
            disabled=submit_disabled,
            help="Pick a star rating to enable" if submit_disabled else None,
        ):
            stars = int(rating_idx) + 1
            _save_feedback(final, stars, comment)
            if st.session_state.history:
                st.session_state.history[-1]["rating"] = stars
            st.session_state.view = "form"
            st.session_state.result_state = None
            st.toast("Thanks for your feedback!", icon="✅")
            st.rerun()
    with col_b:
        if st.button("Submit another ticket", use_container_width=True):
            st.session_state.view = "form"
            st.session_state.result_state = None
            st.rerun()


if st.session_state.view == "result":
    render_result()
else:
    render_form()
