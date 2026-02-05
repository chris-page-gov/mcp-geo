from __future__ import annotations

from typing import Any

from server.config import settings
from tools.nomis_common import client as nomis_client
from tools.registry import Tool, ToolResult, register


def _require_live() -> ToolResult | None:
    if not settings.NOMIS_LIVE_ENABLED:
        return 501, {
            "isError": True,
            "code": "LIVE_DISABLED",
            "message": "NOMIS live mode is disabled. Set NOMIS_LIVE_ENABLED=true.",
        }
    return None


def _build_url(path: str) -> str:
    base = nomis_client.base_api.rstrip("/")
    return f"{base}/{path.lstrip('/')}"


def _datasets(payload: dict[str, Any]) -> ToolResult:
    live = _require_live()
    if live:
        return live
    dataset = payload.get("dataset")
    fmt = (payload.get("format") or "sdmx").lower()
    if dataset and not isinstance(dataset, str):
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "dataset must be a string"}
    if fmt not in {"sdmx", "json"}:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "format must be 'sdmx' or 'json'"}
    suffix = "def.sdmx.json" if fmt == "sdmx" else "def.json"
    path = f"dataset/{suffix}" if not dataset else f"dataset/{dataset}/{suffix}"
    status, data = nomis_client.get_json(_build_url(path))
    if status != 200:
        return status, data
    return 200, {"live": True, "dataset": dataset, "format": fmt, "data": data}


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
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "format must be 'jsonstat' or 'sdmx'"}
    if params is not None and not isinstance(params, dict):
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "params must be an object"}
    suffix = "jsonstat.json" if fmt == "jsonstat" else "generic.sdmx.json"
    path = f"dataset/{dataset}.{suffix}"
    status, data = nomis_client.get_json(_build_url(path), params=params or {})
    if status != 200:
        return status, data
    return 200, {"live": True, "dataset": dataset, "format": fmt, "data": data}


register(Tool(
    name="nomis.datasets",
    description="List NOMIS datasets or return a dataset definition.",
    input_schema={
        "type": "object",
        "properties": {
            "tool": {"type": "string", "const": "nomis.datasets"},
            "dataset": {"type": "string", "description": "Optional dataset id"},
            "format": {"type": "string", "enum": ["sdmx", "json"]},
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
            "data": {"type": "object"},
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
