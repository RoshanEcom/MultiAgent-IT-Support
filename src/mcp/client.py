"""MCP client — thin wrapper around the local registry. Same surface area as
`mcp.client.Client.call_tool(...)` so this can be swapped for a real MCP transport
without changing agent code."""
from __future__ import annotations

from functools import lru_cache

from src.mcp.catalog_tool import catalog_lookup_hardware, catalog_place_order
from src.mcp.idp_tool import idp_add_to_group, idp_provision_software, idp_reset_password
from src.mcp.jira_tool import jira_create_incident, jira_create_ticket, jira_transition_issue
from src.mcp.logs_tool import logs_get_recent
from src.mcp.registry import ToolDescriptor, ToolRegistry


def _build_registry() -> ToolRegistry:
    reg = ToolRegistry()

    # Jira
    reg.register(
        ToolDescriptor(
            name="jira.create_ticket",
            description="Create a Task ticket in Jira as the audit record for an automated action.",
            parameters={
                "summary": "Short title for the ticket",
                "description": "Free-text body, plain text",
                "category": "Category tag for routing",
            },
        ),
        jira_create_ticket,
    )
    reg.register(
        ToolDescriptor(
            name="jira.create_incident",
            description="Create a high-priority Jira ticket for human handoff.",
            parameters={
                "summary": "Short title",
                "description": "Free-text body, plain text",
                "severity": "low | medium | high",
            },
        ),
        jira_create_incident,
    )
    reg.register(
        ToolDescriptor(
            name="jira.transition_issue",
            description="Move a Jira ticket to a named status (e.g., 'Done', 'In Progress').",
            parameters={
                "ticket_id": "Jira issue key, e.g., TIC-12",
                "target_status": "Destination status name as shown on the board",
            },
        ),
        jira_transition_issue,
    )

    # IDP
    reg.register(
        ToolDescriptor(
            name="idp.provision_software",
            description="Assign a software license from the corporate catalog to a user.",
            parameters={
                "user_id": "The user receiving the license",
                "software": "Software name (looked up against approved catalog)",
                "justification": "Optional business justification",
            },
        ),
        idp_provision_software,
    )
    reg.register(
        ToolDescriptor(
            name="idp.add_to_group",
            description="Add a user to a Slack channel, mailing list, drive, or other group.",
            parameters={
                "user_id": "User being added",
                "group_name": "Name of the group, channel, list, or drive",
                "justification": "Optional reason for the access",
            },
        ),
        idp_add_to_group,
    )
    reg.register(
        ToolDescriptor(
            name="idp.reset_password",
            description="Generate a one-time-use temporary password for a system.",
            parameters={"user_id": "User", "system": "System name (e.g., Okta)"},
        ),
        idp_reset_password,
    )

    # Catalog
    reg.register(
        ToolDescriptor(
            name="catalog.lookup_hardware",
            description="Look up a hardware item in the IT catalog by free-text description.",
            parameters={"description": "Free-text item description"},
        ),
        catalog_lookup_hardware,
    )
    reg.register(
        ToolDescriptor(
            name="catalog.place_order",
            description="Place an order for a known SKU.",
            parameters={
                "sku": "Catalog SKU",
                "user_id": "User receiving the item",
                "office": "Office code (SF, NYC, Reno)",
                "shipping_address": "Optional override shipping address",
            },
        ),
        catalog_place_order,
    )

    # Logs
    reg.register(
        ToolDescriptor(
            name="logs.get_recent",
            description="Retrieve recent log events for a service to attach to incident context.",
            parameters={
                "service": "av | printer | network | sso",
                "hours": "Lookback window in hours",
                "user_id": "Filter by user (optional)",
                "room": "Filter by room (optional, AV only)",
                "host": "Filter by host (optional)",
            },
        ),
        logs_get_recent,
    )

    return reg


@lru_cache(maxsize=1)
def get_mcp_client() -> "MCPClient":
    return MCPClient(_build_registry())


class MCPClient:
    """Thin façade over ToolRegistry. Mirrors `mcp.client.Client` surface area."""

    def __init__(self, registry: ToolRegistry):
        self._registry = registry

    def list_tools(self) -> list[ToolDescriptor]:
        return self._registry.list_tools()

    def call_tool(self, name: str, **params) -> dict:
        return self._registry.call(name, **params)

    # Convenience alias matching the reference example's signature
    def call(self, name: str, **params) -> dict:
        return self.call_tool(name, **params)
