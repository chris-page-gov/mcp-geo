from __future__ import annotations

import re
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


_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
_MAX_SCAN_LIMIT = 500


def _search_text(item: dict[str, Any]) -> str:
    keywords = item.get("keywords")
    keyword_list = keywords if isinstance(keywords, list) else []
    keyword_text = " ".join(str(token) for token in keyword_list if isinstance(token, str))
    return " ".join(
        [
            str(item.get("id") or ""),
            str(item.get("title") or ""),
            str(item.get("description") or ""),
            keyword_text,
        ]
    ).lower()


def _score_item(item: dict[str, Any], query: str, tokens: list[str]) -> int:
    haystack = _search_text(item)
    if not haystack:
        return 0
    query_hit = query in haystack
    token_hits = sum(1 for token in tokens if token in haystack)
    if not query_hit and token_hits == 0:
        return 0
    item_id = str(item.get("id") or "").lower()
    score = token_hits * 10
    if query_hit:
        score += 25
    if item_id.startswith(query):
        score += 20
    return score


def _live_search(term: str, limit: int, offset: int) -> ToolResult:
    url = f"{_SEARCH_CLIENT.base_api}/datasets"
    scan_params = {"limit": _MAX_SCAN_LIMIT, "offset": 0}
    status, data = _SEARCH_CLIENT.get_json(url, params=scan_params)
    if status != 200 or not isinstance(data, dict):
        return status, data

    items = data.get("items", []) or []
    if not isinstance(items, list):
        items = []

    total_count = data.get("total_count")
    fetched = len(items)
    while (
        isinstance(total_count, int)
        and fetched < total_count
        and len(items) >= _MAX_SCAN_LIMIT
    ):
        scan_params["offset"] = fetched
        status_more, data_more = _SEARCH_CLIENT.get_json(url, params=scan_params)
        if status_more != 200 or not isinstance(data_more, dict):
            break
        page_items = data_more.get("items", []) or []
        if not isinstance(page_items, list) or not page_items:
            break
        items.extend(page_items)
        fetched += len(page_items)

    query = term.strip().lower()
    tokens = [token for token in _TOKEN_PATTERN.findall(query) if token]
    scored: list[tuple[int, dict[str, Any]]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        score = _score_item(item, query, tokens)
        if score <= 0:
            continue
        scored.append((score, item))
    scored.sort(
        key=lambda pair: (
            -pair[0],
            str(pair[1].get("id") or ""),
            str(pair[1].get("title") or ""),
        )
    )

    results: list[dict[str, Any]] = []
    filtered_items = [item for _, item in scored]
    paged_items = filtered_items[offset : offset + limit]
    for item in paged_items:
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
        "offset": offset,
        "limit": limit,
        "total": len(filtered_items),
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
