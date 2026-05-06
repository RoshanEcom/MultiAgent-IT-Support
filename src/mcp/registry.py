"""Tool registry — names map to callables. Mirrors MCP's `tools/list` + `tools/call`
shape so this can be swapped for a real MCP client (`mcp.client.Client`) without
changing agent code."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

ToolFn = Callable[..., dict[str, Any]]


@dataclass(frozen=True)
class ToolDescriptor:
    name: str
    description: str
    parameters: dict[str, str]  # name -> human description (kept simple; not full JSON Schema)


@dataclass
class ToolRegistry:
    tools: dict[str, ToolFn] = field(default_factory=dict)
    descriptors: dict[str, ToolDescriptor] = field(default_factory=dict)

    def register(self, descriptor: ToolDescriptor, fn: ToolFn) -> None:
        if descriptor.name in self.tools:
            raise ValueError(f"Tool {descriptor.name!r} is already registered.")
        self.tools[descriptor.name] = fn
        self.descriptors[descriptor.name] = descriptor

    def list_tools(self) -> list[ToolDescriptor]:
        return list(self.descriptors.values())

    def call(self, name: str, **params: Any) -> dict[str, Any]:
        if name not in self.tools:
            return {"error": f"Unknown tool: {name}"}
        try:
            result = self.tools[name](**params)
            if not isinstance(result, dict):
                return {"error": f"Tool {name} returned non-dict: {type(result).__name__}"}
            return result
        except TypeError as e:
            return {"error": f"Bad parameters for {name}: {e}"}
        except Exception as e:  # noqa: BLE001 - tool errors must not crash the graph
            return {"error": f"{type(e).__name__}: {e}"}
