from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from server.config import settings
from tools.ons_common import ONSClient
from tools.registry import Tool, register, ToolResult

_OBS_PATH = Path(__file__).parent.parent / "resources" / "ons_observations.json"
_SEARCH_CLIENT = ONSClient()
_SEARCH_CLIENT.base_api = (
    getattr(settings, "ONS_DATASET_API_BASE", "")
    or "https://api.beta.ons.gov.uk/v1"
)


def _load() -> dict[str, Any]:
    try:
        return json.loads(_OBS_PATH.read_text())
    except Exception:
        return {}


def _live_enabled() -> bool:
    return bool(getattr(settings, "ONS_SEARCH_LIVE_ENABLED", True))


def _live_search(term: str, limit: int, offset: int) -> ToolResult:
    url = f"{_SEARCH_CLIENT.base_api}/datasets"
    params = {"search": term, "limit": limit, "offset": offset}
    status, data = _SEARCH_CLIENT.get_json(url, params=params)
    if status != 200 or not isinstance(data, dict):
        return status, data
    items = data.get("items", []) or []
    results: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        results.append({
            "kind": "dataset",
            "id": item.get("id"),
            "title": item.get("title"),
            "description": item.get("description"),
            "keywords": item.get("keywords", []),
            "state": item.get("state"),
            "links": item.get("links", {}),
        })
    return 200, {
        "results": results,
        "count": len(results),
        "offset": data.get("offset", offset),
        "limit": data.get("limit", limit),
        "total": data.get("total_count"),
        "live": True,
    }


def _sample_search(term: str) -> ToolResult:
    data = _load()
    dims = data.get("dimensions", {})
    hits: list[dict[str, Any]] = []
    for dim_name, codes in dims.items():
        for code in codes:
            if term in str(code).lower():
                hits.append({"kind": "code", "dimension": dim_name, "code": code})
    return 200, {"results": hits, "count": len(hits), "live": False}


def _search(payload: dict[str, Any]) -> ToolResult:
    term = (payload.get("term") or "").strip()
    if not term:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "Missing search term"}
    limit = payload.get("limit", 20)
    offset = payload.get("offset", 0)
    if not isinstance(limit, int) or limit < 1:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "limit must be >= 1"}
    if not isinstance(offset, int) or offset < 0:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "offset must be >= 0"}
    if _live_enabled():
        status, data = _live_search(term, limit, offset)
        if status == 200:
            return status, data
    return _sample_search(term.lower())

register(Tool(
    name="ons_search.query",
    description=(
        "Search live ONS datasets by term; falls back to sample dimension codes "
        "when live search is disabled or unavailable."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "tool": {"type": "string", "const": "ons_search.query"},
            "term": {"type": "string"},
            "limit": {"type": "integer", "minimum": 1, "maximum": 500},
            "offset": {"type": "integer", "minimum": 0},
        },
        "required": ["term"],
        "additionalProperties": False,
    },
    output_schema={
        "type": "object",
        "properties": {
            "results": {"type": "array"},
            "count": {"type": "integer"},
            "limit": {"type": ["integer", "null"]},
            "offset": {"type": ["integer", "null"]},
            "total": {"type": ["integer", "null"]},
            "live": {"type": "boolean"},
        },
        "required": ["results", "count"],
    },
    handler=_search,
))
