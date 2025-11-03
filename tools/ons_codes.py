from __future__ import annotations
from tools.registry import Tool, register, ToolResult
from typing import Any
import json
from pathlib import Path

_OBS_PATH = Path(__file__).parent.parent / "resources" / "ons_observations.json"

def _load() -> dict[str, Any]:
    try:
        return json.loads(_OBS_PATH.read_text())
    except Exception:
        return {}

def _list(payload: dict[str, Any]) -> ToolResult:
    data = _load()
    dims = data.get("dimensions", {})
    return 200, {"dimensions": sorted(dims.keys())}

def _options(payload: dict[str, Any]) -> ToolResult:
    data = _load()
    dims = data.get("dimensions", {})
    dim = payload.get("dimension")
    if not isinstance(dim, str):
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "Missing dimension"}
    if dim not in dims:
        return 404, {"isError": True, "code": "INVALID_INPUT", "message": f"Unknown dimension '{dim}'"}
    return 200, {"dimension": dim, "options": dims[dim]}

register(Tool(
    name="ons_codes.list",
    description="List available ONS sample dimensions.",
    input_schema={"type": "object", "properties": {"tool": {"type": "string", "const": "ons_codes.list"}}, "required": [], "additionalProperties": False},
    output_schema={"type": "object", "properties": {"dimensions": {"type": "array"}}, "required": ["dimensions"]},
    handler=_list,
))

register(Tool(
    name="ons_codes.options",
    description="List codes/options for a given ONS sample dimension.",
    input_schema={"type": "object", "properties": {"tool": {"type": "string", "const": "ons_codes.options"}, "dimension": {"type": "string"}}, "required": ["dimension"], "additionalProperties": False},
    output_schema={"type": "object", "properties": {"dimension": {"type": "string"}, "options": {"type": "array"}}, "required": ["dimension", "options"]},
    handler=_options,
))
