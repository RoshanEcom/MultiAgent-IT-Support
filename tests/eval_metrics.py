"""Evaluation harness — runs every scenario in gold_set.json against the live
graph and reports triage accuracy, latency percentiles, and final-answer-kind
match rate.

Usage:  python tests/eval_metrics.py
"""
from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path

# Make `src` importable when running as a script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.graph import build_app  # noqa: E402
from src.state import GraphState, Message, UserContext  # noqa: E402

GOLD_SET = json.loads((Path(__file__).parent / "gold_set.json").read_text(encoding="utf-8"))


def _final_answer_kind(state: GraphState) -> str:
    if state.escalation_required and state.escalation_ticket_id:
        return "escalated"
    if state.knowledge_answer:
        return "informational"
    if any(
        a.tool_name.startswith("idp.") or a.tool_name.startswith("catalog.")
        for a in state.actions
    ):
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


def main() -> int:
    app = build_app()
    results = []
    latencies_ms: list[int] = []

    print(f"Running {len(GOLD_SET['scenarios'])} scenarios…\n")
    for scenario in GOLD_SET["scenarios"]:
        user_overrides = scenario.get("user", {})
        user = UserContext(
            user_id="eval.user",
            display_name="Eval User",
            email="eval.user@company.com",
            department=user_overrides.get("department", "Engineering"),
            office=user_overrides.get("office", "SF"),
        )
        initial = GraphState(
            messages=[Message(role="user", content=scenario["message"])],
            user=user,
        )

        t0 = time.monotonic()
        final_dict = app.invoke(initial)
        latency_ms = int((time.monotonic() - t0) * 1000)
        latencies_ms.append(latency_ms)

        final = GraphState.model_validate(final_dict)
        expected = scenario["expected"]
        kind = _final_answer_kind(final)

        rt_match = final.intent.request_type == expected["request_type"]
        cat_match = final.intent.category == expected["category"]
        sev_match = (
            "severity" not in expected
            or final.intent.severity == expected["severity"]
        )
        kind_match = _kind_matches(expected["final_answer_kind"], kind)

        all_match = rt_match and cat_match and sev_match and kind_match
        symbol = "✓" if all_match else "✗"
        print(
            f"{symbol} {scenario['id']:30s} "
            f"rt={final.intent.request_type:13s} "
            f"cat={final.intent.category:18s} "
            f"sev={final.intent.severity:6s} "
            f"kind={kind:25s} "
            f"{latency_ms:>5d}ms"
        )
        results.append(
            {
                "id": scenario["id"],
                "rt_match": rt_match,
                "cat_match": cat_match,
                "sev_match": sev_match,
                "kind_match": kind_match,
                "all_match": all_match,
                "latency_ms": latency_ms,
            }
        )

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    n = len(results)
    print(f"  request_type accuracy: {sum(r['rt_match'] for r in results)}/{n}")
    print(f"  category accuracy:     {sum(r['cat_match'] for r in results)}/{n}")
    print(f"  severity accuracy:     {sum(r['sev_match'] for r in results)}/{n}")
    print(f"  final-answer-kind:     {sum(r['kind_match'] for r in results)}/{n}")
    print(f"  all four agree:        {sum(r['all_match'] for r in results)}/{n}")
    print()
    sorted_lat = sorted(latencies_ms)
    print(f"  latency p50: {statistics.median(sorted_lat):.0f}ms")
    print(f"  latency p95: {sorted_lat[int(0.95 * (n - 1))]}ms")
    print(f"  latency max: {max(sorted_lat)}ms")
    return 0


if __name__ == "__main__":
    sys.exit(main())
