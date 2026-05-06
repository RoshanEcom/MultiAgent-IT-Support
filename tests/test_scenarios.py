"""End-to-end scenario tests against the live graph.

These hit the real OpenAI API (the assignment requires it). Skipped when
OPENAI_API_KEY is not set, so CI without secrets won't fail.

Run with:  pytest tests/test_scenarios.py -v
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set; live agent tests skipped.",
)

from src.graph import build_app  # noqa: E402
from src.state import GraphState, Message, UserContext  # noqa: E402

GOLD_SET = json.loads((Path(__file__).parent / "gold_set.json").read_text(encoding="utf-8"))


def _final_answer_kind(state: GraphState) -> str:
    """Map terminal state → one of: informational, action_completed, action_pending, escalated."""
    if state.escalation_required and state.escalation_ticket_id:
        return "escalated"
    if state.knowledge_answer:
        return "informational"
    if any(a.tool_name.startswith("idp.") or a.tool_name.startswith("catalog.") for a in state.actions):
        # Pending if any of the IDP/catalog actions is in PENDING_* state
        if any(
            a.status == "SUCCESS" and "PENDING" in (a.result_summary or "")
            for a in state.actions
        ):
            return "action_pending"
        return "action_completed"
    return "unknown"


def _kind_matches(expected: str, actual: str) -> bool:
    if expected == "action_completed_or_pending":
        return actual in {"action_completed", "action_pending"}
    return expected == actual


@pytest.mark.parametrize("scenario", GOLD_SET["scenarios"], ids=lambda s: s["id"])
def test_scenario(scenario):
    app = build_app()
    user_overrides = scenario.get("user", {})
    user = UserContext(
        user_id="test.user",
        display_name="Test User",
        email="test.user@company.com",
        department=user_overrides.get("department", "Engineering"),
        office=user_overrides.get("office", "SF"),
    )
    initial = GraphState(
        messages=[Message(role="user", content=scenario["message"])],
        user=user,
    )
    final_dict = app.invoke(initial)
    final = GraphState.model_validate(final_dict)
    expected = scenario["expected"]

    assert final.intent.request_type == expected["request_type"], (
        f"request_type mismatch: expected {expected['request_type']}, got {final.intent.request_type}"
    )
    assert final.intent.category == expected["category"], (
        f"category mismatch: expected {expected['category']}, got {final.intent.category}"
    )
    if "severity" in expected:
        assert final.intent.severity == expected["severity"], (
            f"severity mismatch: expected {expected['severity']}, got {final.intent.severity}"
        )
    actual_kind = _final_answer_kind(final)
    assert _kind_matches(expected["final_answer_kind"], actual_kind), (
        f"final_answer_kind mismatch: expected {expected['final_answer_kind']}, got {actual_kind}"
    )
    assert final.final_answer, "final_answer must be set"
