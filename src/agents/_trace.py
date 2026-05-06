"""Tiny helper to wrap node functions with consistent enter/exit trace events."""
from __future__ import annotations

import time
from collections.abc import Callable
from datetime import datetime, timezone
from functools import wraps

from src.state import GraphState, TraceEvent


def traced(node_name: str) -> Callable[[Callable[[GraphState], GraphState]], Callable[[GraphState], GraphState]]:
    def decorator(fn: Callable[[GraphState], GraphState]) -> Callable[[GraphState], GraphState]:
        @wraps(fn)
        def wrapped(state: GraphState) -> GraphState:
            start = time.monotonic()
            state.trace.append(
                TraceEvent(
                    node=node_name,
                    phase="enter",
                    ts=datetime.now(timezone.utc),
                )
            )
            result_state = fn(state)
            duration_ms = int((time.monotonic() - start) * 1000)
            result_state.trace.append(
                TraceEvent(
                    node=node_name,
                    phase="exit",
                    ts=datetime.now(timezone.utc),
                    duration_ms=duration_ms,
                )
            )
            return result_state

        return wrapped

    return decorator
