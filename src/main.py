"""CLI entry point — single-shot conversation against the graph.

Usage:
    python -m src.main "I need a Figma license"
    python -m src.main --user-id alice --department Design "How do I set up email forwarding?"
"""
from __future__ import annotations

import argparse
import json
import sys

from src.graph import build_app
from src.state import GraphState, Message, UserContext


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="One-shot IT Support Copilot")
    p.add_argument("message", help="The user's message")
    p.add_argument("--user-id", default="demo.user")
    p.add_argument("--name", default="Demo User")
    p.add_argument("--email", default="demo.user@company.com")
    p.add_argument("--department", default="Engineering")
    p.add_argument("--office", default="SF")
    p.add_argument(
        "--show-trace",
        action="store_true",
        help="Print the agent trace and intermediate state as JSON.",
    )
    return p.parse_args()


def run_once(message: str, user: UserContext, show_trace: bool = False) -> GraphState:
    app = build_app()
    initial = GraphState(
        messages=[Message(role="user", content=message)],
        user=user,
    )
    final_dict = app.invoke(initial)
    final = GraphState.model_validate(final_dict)

    print()
    print("=" * 70)
    print("USER:", message)
    print("=" * 70)
    print(final.final_answer or "(no final answer set)")
    print("=" * 70)

    if show_trace:
        print("\n--- TRACE ---")
        print(
            json.dumps(
                {
                    "intent": final.intent.model_dump(),
                    "entities": final.entities,
                    "actions": [a.model_dump() for a in final.actions],
                    "tool_results": [tr.model_dump(mode="json") for tr in final.tool_results],
                    "knowledge_unknown": final.knowledge_unknown,
                    "escalation_ticket_id": final.escalation_ticket_id,
                    "trace": [t.model_dump(mode="json") for t in final.trace],
                },
                indent=2,
                default=str,
            )
        )

    return final


def main() -> int:
    args = parse_args()
    user = UserContext(
        user_id=args.user_id,
        display_name=args.name,
        email=args.email,
        department=args.department,
        office=args.office,
    )
    run_once(args.message, user, show_trace=args.show_trace)
    return 0


if __name__ == "__main__":
    sys.exit(main())
