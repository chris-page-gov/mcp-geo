from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Tool:
    name: str
    description: str
    version: str = "0.1.0"
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)
    handler: (
        Callable[[dict[str, Any]], tuple[int, dict[str, Any]]] | None
    ) = None

    def call(self, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        if not self.handler:
            return 501, {
                "isError": True,
                "code": "NOT_IMPLEMENTED",
                "message": f"Tool '{self.name}' is not implemented yet",
            }
        return self.handler(payload)


_REGISTRY: dict[str, Tool] = {}


def register(tool: Tool) -> None:
    _REGISTRY[tool.name] = tool


def get(tool_name: str) -> Tool | None:
    return _REGISTRY.get(tool_name)


def list_tools() -> list[str]:
    return sorted(_REGISTRY.keys())


def all_tools() -> list[Tool]:
    return [_REGISTRY[name] for name in sorted(_REGISTRY.keys())]
