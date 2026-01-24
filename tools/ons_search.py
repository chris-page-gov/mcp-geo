from __future__ import annotations

from typing import Any

from server.config import settings
from tools.ons_common import ONSClient
from tools.registry import Tool, register, ToolResult

_SEARCH_CLIENT = ONSClient()
_SEARCH_CLIENT.base_api = (
    getattr(settings, "ONS_DATASET_API_BASE", "")
    or "https://api.beta.ons.gov.uk/v1"
)


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
    if not _live_enabled():
        return 501, {
            "isError": True,
            "code": "LIVE_DISABLED",
            "message": "ONS search live mode is disabled. Set ONS_SEARCH_LIVE_ENABLED=true.",
        }
    return _live_search(term, limit, offset)

register(Tool(
    name="ons_search.query",
    description="Search live ONS datasets by term.",
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
