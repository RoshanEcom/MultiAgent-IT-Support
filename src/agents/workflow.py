"""Workflow Agent — plans + executes a deterministic sequence of MCP tool calls
based on the Intake classification and extracted entities.

The planner is intentionally rule-based (not an LLM) so the audit trail is
predictable and the action set is bounded — important for an automation system
that operates on user accounts and money."""
from __future__ import annotations

from src.agents._trace import traced
from src.mcp.client import get_mcp_client
from src.state import Action, GraphState, ToolResult


def _plan(state: GraphState) -> list[Action]:
    intent = state.intent
    entities = state.entities
    user = state.user
    actions: list[Action] = []

    if intent.category == "software_license" and intent.request_type == "action":
        software = entities.get("software") or entities.get("software_name") or intent.system or ""
        actions.append(
            Action(
                tool_name="idp.provision_software",
                parameters={
                    "user_id": user.user_id,
                    "software": software,
                    "justification": entities.get("justification", ""),
                },
            )
        )

    elif intent.category == "hardware" and intent.request_type in ("action", "incident"):
        item = (
            entities.get("hardware")
            or entities.get("item")
            or entities.get("device")
            or intent.system
            or ""
        )
        actions.append(
            Action(
                tool_name="catalog.lookup_hardware",
                parameters={"description": item},
            )
        )
        # The actual order is appended at execution time once we have the SKU.

    elif intent.category == "access" and intent.request_type == "action":
        group = (
            entities.get("group")
            or entities.get("channel")
            or entities.get("group_name")
            or intent.system
            or ""
        )
        actions.append(
            Action(
                tool_name="idp.add_to_group",
                parameters={
                    "user_id": user.user_id,
                    "group_name": group,
                    "justification": entities.get("justification", ""),
                },
            )
        )

    elif intent.request_type == "incident":
        # Incidents always pull recent logs to attach to whatever ticket gets created.
        service = "av" if intent.category == "av" else (
            "printer" if intent.category == "printer" else "network"
        )
        room = entities.get("room") or intent.system or ""
        host = entities.get("host", "")
        actions.append(
            Action(
                tool_name="logs.get_recent",
                parameters={
                    "service": service,
                    "hours": 2,
                    "user_id": user.user_id,
                    "room": room,
                    "host": host,
                },
            )
        )

    return actions


def _execute(state: GraphState) -> None:
    client = get_mcp_client()

    for action in state.actions:
        if action.status != "PLANNED":
            continue
        action.status = "RUNNING"
        result = client.call_tool(action.tool_name, **action.parameters)
        success = "error" not in result
        state.tool_results.append(
            ToolResult(
                tool_name=action.tool_name,
                success=success,
                payload=result,
                error=result.get("error") if not success else None,
            )
        )
        if not success:
            action.status = "FAILED"
            action.error = result.get("error")
            continue

        action.status = "SUCCESS"
        action.result_summary = str(result.get("summary") or result.get("status") or result)

        # Hardware: chain the order placement after the lookup
        if action.tool_name == "catalog.lookup_hardware" and result.get("found"):
            state.actions.append(
                Action(
                    tool_name="catalog.place_order",
                    parameters={
                        "sku": result["sku"],
                        "user_id": state.user.user_id,
                        "office": state.user.office,
                    },
                )
            )


def _audit_ticket_summary(state: GraphState) -> str:
    last_user = state.latest_user_message()
    snippet = (last_user.content[:120] + "…") if last_user and len(last_user.content) > 120 else (
        last_user.content if last_user else state.intent.category
    )
    return f"[{state.intent.category}] {snippet}"


def _audit_ticket_description(state: GraphState) -> str:
    lines = [
        f"User: {state.user.display_name} ({state.user.user_id})",
        f"Department: {state.user.department}, Office: {state.user.office}",
        f"Classified as: {state.intent.request_type} / {state.intent.category}",
        f"Severity: {state.intent.severity} (confidence {state.intent.confidence:.2f})",
        "",
        "Actions taken:",
    ]
    for a in state.actions:
        if a.tool_name.startswith("jira."):
            continue
        lines.append(f"  - {a.tool_name} → {a.status}: {a.result_summary or a.error or ''}")
    return "\n".join(lines)


def _user_facing_summary(state: GraphState, ticket_id: str | None) -> str:
    completed_actions = [a for a in state.actions if a.status == "SUCCESS" and not a.tool_name.startswith("jira.")]
    pending = [
        a for a in state.actions
        if a.status == "SUCCESS"
        and not a.tool_name.startswith("jira.")
        and "PENDING" in (a.result_summary or "")
    ]

    if not completed_actions:
        return "I logged your request but didn't complete any actions automatically."

    bullets = "\n".join(f"- {a.result_summary}" for a in completed_actions)
    parts = [bullets]
    if pending:
        parts.append("\nSome steps require approval and will complete once approved.")
    if ticket_id:
        parts.append(f"\nTracked under ticket {ticket_id}.")
    return "Done — here's what I did:\n" + "\n".join(parts)


@traced("workflow")
def workflow_node(state: GraphState) -> GraphState:
    if not state.actions:
        state.actions = _plan(state)

    if not state.actions:
        # No automation exists for this combination — fall back to Knowledge so
        # the runbooks get a chance to answer (e.g., "I need a password reset"
        # has no auto-action but does have self-service steps documented).
        state.workflow_no_plan = True
        return state

    _execute(state)

    any_failed = any(a.status == "FAILED" for a in state.actions if not a.tool_name.startswith("jira."))

    # Open audit ticket alongside the actions (Workflow always opens one for action requests)
    client = get_mcp_client()
    ticket_id: str | None = None
    if state.intent.request_type == "action" and not any_failed:
        ticket_action = Action(
            tool_name="jira.create_ticket",
            parameters={
                "summary": _audit_ticket_summary(state),
                "description": _audit_ticket_description(state),
                "category": state.intent.category,
            },
            status="RUNNING",
        )
        state.actions.append(ticket_action)
        result = client.call_tool(ticket_action.tool_name, **ticket_action.parameters)
        success = "error" not in result
        state.tool_results.append(
            ToolResult(
                tool_name=ticket_action.tool_name,
                success=success,
                payload=result,
                error=result.get("error") if not success else None,
            )
        )
        ticket_action.status = "SUCCESS" if success else "FAILED"
        ticket_action.result_summary = result.get("summary") or str(result)
        if success:
            ticket_id = result.get("ticket_id")
            state.escalation_ticket_id = ticket_id
            # The AI fully resolved the request — move the audit ticket to Done.
            if ticket_id:
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

    if any_failed or state.intent.severity == "high":
        state.escalation_required = True
        state.escalation_reason = (
            "One or more workflow actions failed."
            if any_failed
            else "Severity is high — escalating for human awareness even though automation succeeded."
        )
        return state

    # Compose final answer for the user
    state.final_answer = _user_facing_summary(state, ticket_id)
    return state
