"""Mock IDP (Okta-style) tool implementations. In a real deployment these would
call out to Okta / Azure AD / Workspace Admin SDK; here they return realistic
shapes so the rest of the system can be exercised end-to-end."""
from __future__ import annotations

import random
import time
from typing import Any

# Software catalog mirrors knowledge_base/software_licenses.md so the workflow
# planner can reference the same names users see in the runbook.
SOFTWARE_CATALOG = {
    "figma": {"sku": "FIGMA-PRO", "auto_approve": False, "cost_center": "Design"},
    "figjam": {"sku": "FIGJAM-STD", "auto_approve": True, "cost_center": "Design"},
    "jetbrains": {"sku": "JB-ALL", "auto_approve": False, "cost_center": "Engineering"},
    "adobe creative cloud": {"sku": "ADOBE-CC-FULL", "auto_approve": False, "cost_center": "Design"},
    "adobe acrobat": {"sku": "ADOBE-ACROBAT", "auto_approve": True, "cost_center": "Any"},
    "notion": {"sku": "NOTION-PLUS", "auto_approve": True, "cost_center": "Any"},
    "linear": {"sku": "LINEAR-STD", "auto_approve": True, "cost_center": "Engineering"},
    "loom": {"sku": "LOOM-BIZ", "auto_approve": True, "cost_center": "Any"},
    "1password": {"sku": "1P-BIZ", "auto_approve": True, "cost_center": "Any"},
    "tableau": {"sku": "TABLEAU-CRTR", "auto_approve": False, "cost_center": "Data"},
    "zoom": {"sku": "ZOOM-PRO", "auto_approve": True, "cost_center": "Any"},
}


def _normalize_software_name(name: str) -> str | None:
    n = name.lower().strip()
    if n in SOFTWARE_CATALOG:
        return n
    for catalog_name in SOFTWARE_CATALOG:
        if catalog_name in n or n in catalog_name:
            return catalog_name
    return None


def idp_provision_software(
    *, user_id: str, software: str, justification: str = ""
) -> dict[str, Any]:
    canonical = _normalize_software_name(software)
    if not canonical:
        return {
            "error": f"Software '{software}' is not in the approved catalog. "
            f"Submit a procurement request instead.",
        }
    entry = SOFTWARE_CATALOG[canonical]
    # Simulate small latency to make demo feel realistic
    time.sleep(0.15)

    if not entry["auto_approve"]:
        return {
            "status": "PENDING_MANAGER_APPROVAL",
            "software": canonical,
            "sku": entry["sku"],
            "cost_center": entry["cost_center"],
            "user_id": user_id,
            "justification": justification,
            "summary": (
                f"Provisioning request for {canonical} ({entry['sku']}) recorded. "
                f"Awaiting manager approval before assignment."
            ),
        }

    return {
        "status": "PROVISIONED",
        "software": canonical,
        "sku": entry["sku"],
        "cost_center": entry["cost_center"],
        "user_id": user_id,
        "summary": (
            f"Assigned {canonical} license ({entry['sku']}) to {user_id}. "
            f"Visible in Okta dashboard within 5 minutes."
        ),
    }


# Group catalog for access requests
GROUP_CATALOG = {
    # Slack channels
    "#data-platform": {"type": "slack_channel", "owner_managed": True},
    "#eng-everyone": {"type": "slack_channel", "owner_managed": False},
    "#new-hires": {"type": "slack_channel", "owner_managed": False},
    "#it-help": {"type": "slack_channel", "owner_managed": False},
    # Mailing lists
    "team-design@company.com": {"type": "mailing_list", "owner_managed": True},
    "project-payments-q3@company.com": {"type": "mailing_list", "owner_managed": True},
    "announce-engineering@company.com": {"type": "mailing_list", "owner_managed": False},
    # Drives
    "Engineering - Internal": {"type": "drive", "owner_managed": True},
    "Finance - Q3 Forecast": {"type": "drive", "owner_managed": True},
}


def idp_add_to_group(*, user_id: str, group_name: str, justification: str = "") -> dict[str, Any]:
    # Look up group, allowing partial matches against catalog keys
    canonical = None
    for key in GROUP_CATALOG:
        if key.lower() == group_name.lower() or key.lower() in group_name.lower():
            canonical = key
            break
    if not canonical:
        # Unknown group — treat as request to be reviewed, not an error
        return {
            "status": "UNKNOWN_GROUP",
            "group_name": group_name,
            "summary": (
                f"Group '{group_name}' is not in the IT-managed catalog. "
                f"Recording the request for manual review by IT."
            ),
        }
    entry = GROUP_CATALOG[canonical]
    time.sleep(0.1)
    if entry["owner_managed"]:
        return {
            "status": "PENDING_OWNER_APPROVAL",
            "group_name": canonical,
            "group_type": entry["type"],
            "user_id": user_id,
            "justification": justification,
            "summary": (
                f"Request to add {user_id} to {canonical} ({entry['type']}) routed to the group owner."
            ),
        }
    return {
        "status": "ADDED",
        "group_name": canonical,
        "group_type": entry["type"],
        "user_id": user_id,
        "summary": f"Added {user_id} to {canonical} ({entry['type']}). Effective immediately.",
    }


def idp_reset_password(*, user_id: str, system: str = "Okta") -> dict[str, Any]:
    """Generate a one-time-use temporary password for the named system."""
    time.sleep(0.1)
    temp_password = f"Tmp-{random.randint(10000, 99999)}-Reset!"
    return {
        "status": "RESET",
        "user_id": user_id,
        "system": system,
        "temp_password": temp_password,
        "summary": (
            f"Temporary password generated for {user_id} on {system}. "
            f"User must change at next sign-in. Expires in 24h."
        ),
    }
