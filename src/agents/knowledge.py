"""Knowledge Agent — RAG over the markdown runbooks. Answers informational questions
with citations, or emits an "I don't know" sentinel that the router catches and
sends to escalation."""
from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate

from src.agents._trace import traced
from src.llm import get_chat_llm
from src.mcp.client import get_mcp_client
from src.rag.retriever import retrieve
from src.state import Action, GraphState, ToolResult

UNKNOWN_SENTINEL = "I_DONT_KNOW_FROM_RUNBOOKS"

_KNOWLEDGE_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are the Knowledge agent for an internal IT helpdesk. You answer "
            "user questions strictly from the provided runbook context.\n\n"
            "Rules:\n"
            "1. Use ONLY information present in the context. Do not invent procedures, "
            "URLs, software names, or policies.\n"
            "2. If the context does not contain the answer, reply with EXACTLY this "
            f"single token and nothing else: {UNKNOWN_SENTINEL}\n"
            "3. When you do answer, write a short paragraph or a numbered list — "
            "whichever fits the question. Cite sources inline as [1], [2], etc.\n"
            "4. If a procedure depends on the user's OS or office, say so and give "
            "instructions for both rather than guessing which they have.\n"
            "5. If the context contains a hard policy rule (e.g., 'not permitted'), "
            "state the rule clearly — do not soften it.\n"
            "6. Keep the tone direct and professional. No marketing language.",
        ),
        (
            "human",
            "User question:\n{question}\n\nUser context: department={department}, office={office}\n\n"
            "Runbook context:\n{context}",
        ),
    ]
)


def _format_context(retrieved) -> str:
    if not retrieved:
        return "(no runbook chunks retrieved)"
    blocks = []
    for i, doc in enumerate(retrieved, start=1):
        blocks.append(f"[{i}] {doc.source_file} (chunk {doc.chunk_index})\n{doc.snippet}")
    return "\n\n---\n\n".join(blocks)


@traced("knowledge")
def knowledge_node(state: GraphState) -> GraphState:
    last_user = state.latest_user_message()
    if not last_user:
        return state

    query = last_user.content
    if state.intent.system:
        query = f"{query} (system: {state.intent.system})"
    state.rag_query = query

    docs = retrieve(query, k=5, category_hint=state.intent.category)
    state.retrieved_docs = docs

    context = _format_context(docs)
    chain = _KNOWLEDGE_PROMPT | get_chat_llm()
    response = chain.invoke(
        {
            "question": last_user.content,
            "department": state.user.department,
            "office": state.user.office,
            "context": context,
        }
    )
    answer_text = (response.content or "").strip()

    if UNKNOWN_SENTINEL in answer_text:
        state.knowledge_unknown = True
        state.escalation_required = True
        state.escalation_reason = "Knowledge agent could not answer from the runbooks."
        # Don't set final_answer — escalation will set it
        return state

    # Append a citations block so the UI doesn't have to recompute it
    if docs:
        cites = "\n".join(
            f"[{i}] {d.source_file} (chunk {d.chunk_index})" for i, d in enumerate(docs, start=1)
        )
        answer_text = f"{answer_text}\n\nSources:\n{cites}"

    # Create a Jira audit ticket so AI-resolved requests appear on the board too,
    # then immediately move it to Done since the AI fully resolved the request.
    ticket_id = _create_audit_ticket(state, answer_text)

    if ticket_id:
        answer_text = f"{answer_text}\n\n**Reference: {ticket_id}**"

    state.knowledge_answer = answer_text
    state.final_answer = answer_text
    return state


def _audit_description(state: GraphState, answer: str) -> str:
    last_user = state.latest_user_message()
    user_msg = last_user.content if last_user else ""
    snippet = answer if len(answer) <= 1500 else answer[:1500] + "…"
    return (
        f"User: {state.user.display_name} ({state.user.user_id})\n"
        f"Department: {state.user.department}, Office: {state.user.office}\n"
        f"Classified as: informational / {state.intent.category}\n"
        f"Confidence: {state.intent.confidence:.2f}\n\n"
        f"User asked:\n{user_msg}\n\n"
        f"AI answered (from runbooks):\n{snippet}"
    )


def _create_audit_ticket(state: GraphState, answer_text: str) -> str | None:
    """Create a Jira ticket for the answered request and move it to Done.
    Returns the ticket_id or None on failure (failure does not break the response)."""
    last_user = state.latest_user_message()
    if not last_user:
        return None
    client = get_mcp_client()

    create_action = Action(
        tool_name="jira.create_ticket",
        parameters={
            "summary": f"[{state.intent.category}] {last_user.content[:80]}",
            "description": _audit_description(state, answer_text),
            "category": state.intent.category,
        },
        status="RUNNING",
    )
    state.actions.append(create_action)
    create_result = client.call_tool(create_action.tool_name, **create_action.parameters)
    create_success = "error" not in create_result
    state.tool_results.append(
        ToolResult(
            tool_name=create_action.tool_name,
            success=create_success,
            payload=create_result,
            error=create_result.get("error") if not create_success else None,
        )
    )
    create_action.status = "SUCCESS" if create_success else "FAILED"
    create_action.result_summary = create_result.get("summary") or str(create_result)

    if not create_success:
        return None

    ticket_id = create_result.get("ticket_id")
    if not ticket_id:
        return None
    state.escalation_ticket_id = ticket_id  # reused as the user-visible ticket reference

    # Move the ticket to Done since the AI fully resolved the request.
    transition_action = Action(
        tool_name="jira.transition_issue",
        parameters={"ticket_id": ticket_id, "target_status": "Done"},
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

    return ticket_id
