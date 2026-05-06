"""Real Jira REST API tool implementations + console-mock fallback when Jira creds
are not configured. The fallback is what makes the system demoable with only an
OpenAI key."""
from __future__ import annotations

import itertools
from typing import Any

import requests
from requests.auth import HTTPBasicAuth

from src.config import SETTINGS

_mock_counter = itertools.count(1)


def _to_adf(text: str) -> dict[str, Any]:
    """Wrap plaintext in Atlassian Document Format — Jira's required body shape."""
    return {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": text}],
            }
        ],
    }


def _create_issue(
    summary: str, description: str, issue_type: str, priority: str | None = None
) -> dict[str, Any]:
    if not SETTINGS.jira_enabled:
        ticket_id = f"{SETTINGS.jira_project_key}-MOCK-{next(_mock_counter)}"
        print(f"[jira-mock] {issue_type} [{ticket_id}] {summary}")
        print(f"[jira-mock]   {description[:200]}{'…' if len(description) > 200 else ''}")
        return {
            "ticket_id": ticket_id,
            "summary": summary,
            "issue_type": issue_type,
            "priority": priority,
            "mock": True,
        }

    url = f"{SETTINGS.jira_base_url}/rest/api/3/issue"
    fields: dict[str, Any] = {
        "project": {"key": SETTINGS.jira_project_key},
        "summary": summary,
        "description": _to_adf(description),
        "issuetype": {"name": issue_type},
    }
    if priority:
        fields["priority"] = {"name": priority}

    resp = requests.post(
        url,
        json={"fields": fields},
        auth=HTTPBasicAuth(SETTINGS.jira_email, SETTINGS.jira_api_token),
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        timeout=20,
    )
    if resp.status_code >= 400:
        return {
            "error": f"Jira API returned {resp.status_code}: {resp.text[:300]}",
        }
    body = resp.json()
    return {
        "ticket_id": body.get("key"),
        "summary": summary,
        "issue_type": issue_type,
        "priority": priority,
    }


def jira_create_ticket(*, summary: str, description: str = "", category: str = "general") -> dict[str, Any]:
    """Audit-trail ticket created alongside successful automated actions."""
    full_description = f"[Auto-generated audit record · category={category}]\n\n{description}"
    return _create_issue(
        summary=summary,
        description=full_description,
        issue_type="Task",
        priority="Low",
    )


def jira_create_incident(
    *,
    summary: str,
    description: str = "",
    severity: str = "medium",
) -> dict[str, Any]:
    """Higher-priority ticket for human handoff."""
    priority_map = {"low": "Low", "medium": "Medium", "high": "High"}
    full_description = f"[Escalated by IT Support Copilot · severity={severity}]\n\n{description}"
    result = _create_issue(
        summary=summary,
        description=full_description,
        issue_type="Task",  # Many free Jira workspaces don't have an Incident issue type configured
        priority=priority_map.get(severity.lower(), "Medium"),
    )
    # Surface incident_id alongside ticket_id for the Escalation agent's convenience
    if "ticket_id" in result:
        result["incident_id"] = result["ticket_id"]
    return result


def jira_transition_issue(*, ticket_id: str, target_status: str) -> dict[str, Any]:
    """Move a ticket to a named status (e.g., 'Done', 'In Progress').

    Jira workflows expose transitions, not direct status writes. We list the
    available transitions for the issue, find one whose destination status
    matches `target_status` (case-insensitive), and apply it.
    """
    if not SETTINGS.jira_enabled or not ticket_id or "MOCK" in ticket_id:
        print(f"[jira-mock] transition {ticket_id} -> {target_status}")
        return {
            "ticket_id": ticket_id,
            "new_status": target_status,
            "mock": True,
            "summary": f"(mock) moved {ticket_id} to {target_status}",
        }

    auth = HTTPBasicAuth(SETTINGS.jira_email, SETTINGS.jira_api_token)
    transitions_url = f"{SETTINGS.jira_base_url}/rest/api/3/issue/{ticket_id}/transitions"

    list_resp = requests.get(
        transitions_url,
        auth=auth,
        headers={"Accept": "application/json"},
        timeout=20,
    )
    if list_resp.status_code >= 400:
        return {"error": f"List transitions failed ({list_resp.status_code}): {list_resp.text[:200]}"}

    transitions = list_resp.json().get("transitions", [])
    target_lower = target_status.lower()
    chosen = None
    for t in transitions:
        to_name = (t.get("to") or {}).get("name", "")
        if to_name.lower() == target_lower or t.get("name", "").lower() == target_lower:
            chosen = t
            break
    if not chosen:
        available = [(t.get("to") or {}).get("name") or t.get("name") for t in transitions]
        return {
            "error": f"No transition to '{target_status}' available for {ticket_id}. Available: {available}",
            "available": available,
        }

    apply_resp = requests.post(
        transitions_url,
        json={"transition": {"id": chosen["id"]}},
        auth=auth,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        timeout=20,
    )
    if apply_resp.status_code >= 400:
        return {"error": f"Apply transition failed ({apply_resp.status_code}): {apply_resp.text[:200]}"}

    new_status = (chosen.get("to") or {}).get("name", target_status)
    return {
        "ticket_id": ticket_id,
        "new_status": new_status,
        "transition_id": chosen["id"],
        "summary": f"Moved {ticket_id} to {new_status}.",
    }
