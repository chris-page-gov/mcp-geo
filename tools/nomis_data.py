from __future__ import annotations

import re
from typing import Any

from server.config import settings
from tools.nomis_common import client as nomis_client
from tools.registry import Tool, ToolResult, register

_DATASET_ID_PATTERN = re.compile(r"^[A-Z0-9]+(?:_[A-Z0-9]+)+$", re.IGNORECASE)


def _require_live() -> ToolResult | None:
    if not settings.NOMIS_LIVE_ENABLED:
        return 501, {
            "isError": True,
            "code": "LIVE_DISABLED",
            "message": "NOMIS live mode is disabled. Set NOMIS_LIVE_ENABLED=true.",
        }
    return None


def _extract_nomis_error(data: Any) -> str | None:
    if not isinstance(data, dict):
        return None
    err = data.get("error") or data.get("errors")
    if not err:
        return None
    if isinstance(err, list):
        return "; ".join(str(item) for item in err if item)[:200]
    return str(err)


def _build_url(path: str) -> str:
    base = nomis_client.base_api.rstrip("/")
    return f"{base}/{path.lstrip('/')}"


def _extract_text(value: Any) -> str | None:
    if isinstance(value, str):
        text = value.strip()
        return text or None
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, dict):
        for key in ("value", "#text", "$", "en", "name", "label", "title", "description"):
            nested = _extract_text(value.get(key))
            if nested:
                return nested
    if isinstance(value, list):
        for item in value:
            nested = _extract_text(item)
            if nested:
                return nested
    return None


def _looks_like_dataset_id(value: str) -> bool:
    return bool(_DATASET_ID_PATTERN.fullmatch(value))


def _dataset_entry_from_dict(entry: dict[str, Any]) -> dict[str, str | None] | None:
    dataset_id = _extract_text(entry.get("id")) or _extract_text(entry.get("dataset"))
    if not dataset_id or not _looks_like_dataset_id(dataset_id):
        return None
    name = (
        _extract_text(entry.get("name"))
        or _extract_text(entry.get("label"))
        or _extract_text(entry.get("title"))
    )
    description = _extract_text(entry.get("description")) or _extract_text(entry.get("notes"))
    return {"id": dataset_id, "name": name or dataset_id, "description": description}


def _collect_dataset_entries(node: Any, out: list[dict[str, str | None]], *, deep: bool) -> None:
    if isinstance(node, list):
        for item in node:
            _collect_dataset_entries(item, out, deep=deep)
        return
    if not isinstance(node, dict):
        return
    candidate = _dataset_entry_from_dict(node)
    if candidate:
        out.append(candidate)
    keys = ("keyfamily", "dataset", "datasets", "items", "results", "children")
    if deep:
        for value in node.values():
            _collect_dataset_entries(value, out, deep=False)
    else:
        for key in keys:
            if key in node:
                _collect_dataset_entries(node[key], out, deep=False)


def _extract_dataset_entries(data: Any) -> list[dict[str, str | None]]:
    entries: list[dict[str, str | None]] = []
    if not isinstance(data, dict):
        return entries
    paths = [
        ("structure", "keyfamilies", "keyfamily"),
        ("structure", "datasets", "dataset"),
        ("datasets", "dataset"),
        ("datasets",),
        ("dataset",),
        ("items",),
        ("results",),
    ]
    for path in paths:
        node: Any = data
        for key in path:
            if not isinstance(node, dict):
                node = None
                break
            node = node.get(key)
        if node is not None:
            _collect_dataset_entries(node, entries, deep=False)
    if not entries:
        _collect_dataset_entries(data, entries, deep=True)
    deduped: dict[str, dict[str, str | None]] = {}
    for entry in entries:
        dataset_id = entry.get("id")
        if not dataset_id:
            continue
        key = str(dataset_id).lower()
        if key not in deduped:
            deduped[key] = entry
    return sorted(deduped.values(), key=lambda item: str(item.get("id", "")))


def _filter_dataset_entries(
    entries: list[dict[str, str | None]],
    query: str | None,
) -> list[dict[str, str | None]]:
    if not query:
        return entries
    query_norm = query.strip().lower()
    if not query_norm:
        return entries
    filtered: list[dict[str, str | None]] = []
    for entry in entries:
        haystack = " ".join(
            str(entry.get(field, "") or "").lower() for field in ("id", "name", "description")
        )
        if query_norm in haystack:
            filtered.append(entry)
    return filtered


def _datasets(payload: dict[str, Any]) -> ToolResult:
    live = _require_live()
    if live:
        return live
    dataset = payload.get("dataset")
    query = payload.get("q")
    limit = payload.get("limit", 25)
    include_raw = payload.get("includeRaw", False)
    fmt = (payload.get("format") or "sdmx").lower()
    if dataset and not isinstance(dataset, str):
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "dataset must be a string"}
    if query is not None and not isinstance(query, str):
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "q must be a string"}
    if not isinstance(limit, int) or limit < 1 or limit > 100:
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "limit must be an integer between 1 and 100",
        }
    if not isinstance(include_raw, bool):
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "includeRaw must be a boolean"}
    if fmt not in {"sdmx", "json"}:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "format must be 'sdmx' or 'json'"}
    suffix = "def.sdmx.json" if fmt == "sdmx" else "def.json"
    path = f"dataset/{suffix}" if not dataset else f"dataset/{dataset}/{suffix}"
    status, data = nomis_client.get_json(_build_url(path))
    if status != 200:
        return status, data
    err = _extract_nomis_error(data)
    if err:
        return 502, {"isError": True, "code": "NOMIS_API_ERROR", "message": err}
    if dataset:
        result: dict[str, Any] = {"live": True, "dataset": dataset, "format": fmt, "data": data}
        if include_raw:
            result["raw"] = data
        return 200, result
    entries = _extract_dataset_entries(data)
    filtered = _filter_dataset_entries(entries, query)
    page = filtered[:limit]
    truncated = len(filtered) > len(page)
    result = {
        "live": True,
        "dataset": None,
        "format": fmt,
        "query": query,
        "limit": limit,
        "returned": len(page),
        "total": len(filtered),
        "truncated": truncated,
        "datasets": page,
        "hints": [
            "Use nomis.query with a selected dataset id.",
            "Use q to filter dataset discovery before querying.",
        ],
        "data": {
            "datasets": page,
            "total": len(filtered),
            "returned": len(page),
            "truncated": truncated,
        },
    }
    if include_raw:
        result["raw"] = data
    return 200, result


def _concepts(payload: dict[str, Any]) -> ToolResult:
    live = _require_live()
    if live:
        return live
    concept = payload.get("concept")
    fmt = (payload.get("format") or "sdmx").lower()
    if concept and not isinstance(concept, str):
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "concept must be a string"}
    if fmt not in {"sdmx", "json"}:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "format must be 'sdmx' or 'json'"}
    suffix = "def.sdmx.json" if fmt == "sdmx" else "def.json"
    path = f"concept/{suffix}" if not concept else f"concept/{concept}/{suffix}"
    status, data = nomis_client.get_json(_build_url(path))
    if status != 200:
        return status, data
    err = _extract_nomis_error(data)
    if err:
        return 502, {"isError": True, "code": "NOMIS_API_ERROR", "message": err}
    return 200, {"live": True, "concept": concept, "format": fmt, "data": data}


def _codelists(payload: dict[str, Any]) -> ToolResult:
    live = _require_live()
    if live:
        return live
    codelist = payload.get("codelist")
    fmt = (payload.get("format") or "sdmx").lower()
    if codelist and not isinstance(codelist, str):
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "codelist must be a string"}
    if fmt not in {"sdmx", "json"}:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "format must be 'sdmx' or 'json'"}
    suffix = "def.sdmx.json" if fmt == "sdmx" else "def.json"
    path = f"codelist/{suffix}" if not codelist else f"codelist/{codelist}/{suffix}"
    status, data = nomis_client.get_json(_build_url(path))
    if status != 200:
        return status, data
    err = _extract_nomis_error(data)
    if err:
        return 502, {"isError": True, "code": "NOMIS_API_ERROR", "message": err}
    return 200, {"live": True, "codelist": codelist, "format": fmt, "data": data}


def _query(payload: dict[str, Any]) -> ToolResult:
    live = _require_live()
    if live:
        return live
    dataset = payload.get("dataset")
    fmt = (payload.get("format") or "jsonstat").lower()
    params = payload.get("params")
    if not isinstance(dataset, str) or not dataset:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "dataset is required"}
    if fmt not in {"jsonstat", "sdmx"}:
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "format must be 'jsonstat' or 'sdmx'",
        }
    if params is not None and not isinstance(params, dict):
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "params must be an object"}
    suffix = "jsonstat.json" if fmt == "jsonstat" else "generic.sdmx.json"
    path = f"dataset/{dataset}.{suffix}"
    status, data = nomis_client.get_json(_build_url(path), params=params or {})
    if status != 200:
        return status, data
    err = _extract_nomis_error(data)
    if err:
        return 400, {"isError": True, "code": "NOMIS_QUERY_ERROR", "message": err}
    return 200, {"live": True, "dataset": dataset, "format": fmt, "data": data}


register(Tool(
    name="nomis.datasets",
    description=(
        "List NOMIS datasets (filtered and limited summary by default), "
        "or return a dataset definition."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "tool": {"type": "string", "const": "nomis.datasets"},
            "dataset": {"type": "string", "description": "Optional dataset id"},
            "format": {"type": "string", "enum": ["sdmx", "json"]},
            "q": {"type": "string", "description": "Optional case-insensitive dataset filter."},
            "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 25},
            "includeRaw": {
                "type": "boolean",
                "default": False,
                "description": "Include the full upstream payload.",
            },
        },
        "required": [],
        "additionalProperties": False,
    },
    output_schema={
        "type": "object",
        "properties": {
            "live": {"type": "boolean"},
            "dataset": {"type": ["string", "null"]},
            "format": {"type": "string"},
            "query": {"type": ["string", "null"]},
            "limit": {"type": "integer"},
            "returned": {"type": "integer"},
            "total": {"type": "integer"},
            "truncated": {"type": "boolean"},
            "datasets": {"type": "array", "items": {"type": "object"}},
            "data": {"type": "object"},
            "raw": {"type": "object"},
        },
        "required": ["live", "format", "data"],
    },
    handler=_datasets,
))

register(Tool(
    name="nomis.concepts",
    description="List NOMIS concepts or return a concept definition.",
    input_schema={
        "type": "object",
        "properties": {
            "tool": {"type": "string", "const": "nomis.concepts"},
            "concept": {"type": "string"},
            "format": {"type": "string", "enum": ["sdmx", "json"]},
        },
        "required": [],
        "additionalProperties": False,
    },
    output_schema={
        "type": "object",
        "properties": {
            "live": {"type": "boolean"},
            "concept": {"type": ["string", "null"]},
            "format": {"type": "string"},
            "data": {"type": "object"},
        },
        "required": ["live", "format", "data"],
    },
    handler=_concepts,
))

register(Tool(
    name="nomis.codelists",
    description="List NOMIS codelists or return a codelist definition.",
    input_schema={
        "type": "object",
        "properties": {
            "tool": {"type": "string", "const": "nomis.codelists"},
            "codelist": {"type": "string"},
            "format": {"type": "string", "enum": ["sdmx", "json"]},
        },
        "required": [],
        "additionalProperties": False,
    },
    output_schema={
        "type": "object",
        "properties": {
            "live": {"type": "boolean"},
            "codelist": {"type": ["string", "null"]},
            "format": {"type": "string"},
            "data": {"type": "object"},
        },
        "required": ["live", "format", "data"],
    },
    handler=_codelists,
))

register(Tool(
    name="nomis.query",
    description="Query NOMIS datasets (JSON-stat or SDMX JSON).",
    input_schema={
        "type": "object",
        "properties": {
            "tool": {"type": "string", "const": "nomis.query"},
            "dataset": {"type": "string"},
            "format": {"type": "string", "enum": ["jsonstat", "sdmx"]},
            "params": {"type": "object"},
        },
        "required": ["dataset"],
        "additionalProperties": False,
    },
    output_schema={
        "type": "object",
        "properties": {
            "live": {"type": "boolean"},
            "dataset": {"type": "string"},
            "format": {"type": "string"},
            "data": {"type": "object"},
        },
        "required": ["live", "dataset", "format", "data"],
    },
    handler=_query,
))
