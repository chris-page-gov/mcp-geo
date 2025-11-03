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

def _search(payload: dict[str, Any]) -> ToolResult:
    term = (payload.get("term") or "").strip().lower()
    if not term:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "Missing search term"}
    data = _load()
    dims = data.get("dimensions", {})
    hits: list[dict[str, str]] = []
    for dim_name, codes in dims.items():
        for code in codes:
            if term in str(code).lower():
                hits.append({"dimension": dim_name, "code": code})
    return 200, {"results": hits, "count": len(hits)}

register(Tool(
    name="ons_search.query",
    description="Search sample ONS dimensions for code fragments.",
    input_schema={
        "type": "object",
        "properties": {"tool": {"type": "string", "const": "ons_search.query"}, "term": {"type": "string"}},
        "required": ["term"],
        "additionalProperties": False,
    },
    output_schema={
        "type": "object",
        "properties": {"results": {"type": "array"}, "count": {"type": "integer"}},
        "required": ["results", "count"],
    },
    handler=_search,
))
