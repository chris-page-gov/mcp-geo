from __future__ import annotations
from pathlib import Path
from typing import Any, cast

from server.config import settings
from server.dataset_cache import DatasetCache
from tools.ons_common import ONSClient
from tools.registry import Tool, register, ToolResult

_CLIENT = ONSClient()
_CLIENT.base_api = (
    getattr(settings, "ONS_DATASET_API_BASE", "")
    or "https://api.beta.ons.gov.uk/v1"
)


def _dataset_cache() -> DatasetCache | None:
    if not settings.ONS_DATASET_CACHE_ENABLED:
        return None
    return DatasetCache(Path(settings.ONS_DATASET_CACHE_DIR))


def _require_live(dataset: Any, edition: Any, version: Any) -> ToolResult | None:
    if not settings.ONS_LIVE_ENABLED:
        return 501, {
            "isError": True,
            "code": "LIVE_DISABLED",
            "message": "ONS live mode is disabled. Set ONS_LIVE_ENABLED=true.",
        }
    if not all(isinstance(val, str) and val for val in (dataset, edition, version)):
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "dataset, edition, and version are required for live ONS codes.",
        }
    return None


def _extract_dim_ids(meta_doc: dict[str, Any]) -> list[str]:
    raw_any = meta_doc.get("dimensions")
    if not isinstance(raw_any, list):
        return []
    ids: list[str] = []
    for entry in raw_any:  # type: ignore[assignment]
        if isinstance(entry, dict):
            entry_dict = cast(dict[str, Any], entry)
            ident: Any = entry_dict.get("id") or entry_dict.get("name")
            if isinstance(ident, str):
                ids.append(ident)
    return ids


def _extract_codes(opt_doc: dict[str, Any]) -> list[str]:
    raw_any = opt_doc.get("items") or opt_doc.get("options") or opt_doc.get("results") or []
    if not isinstance(raw_any, list):
        return []
    codes: list[str] = []
    for entry in raw_any:  # type: ignore[assignment]
        if isinstance(entry, dict):
            entry_dict = cast(dict[str, Any], entry)
            val: Any = (
                entry_dict.get("option")
                or entry_dict.get("id")
                or entry_dict.get("value")
                or entry_dict.get("code")
            )
            if isinstance(val, str):
                codes.append(val)
    return codes


def _list(payload: dict[str, Any]) -> ToolResult:
    dataset = payload.get("dataset")
    edition = payload.get("edition")
    version = payload.get("version")
    live_check = _require_live(dataset, edition, version)
    if live_check:
        return live_check
    cache = _dataset_cache()
    cache_key = f"ons_codes:dimensions:{dataset}:{edition}:{version}"
    if cache:
        cached = cache.read(cache_key)
        if cached and isinstance(cached.get("dimensions"), list):
            return 200, {
                "dimensions": cached.get("dimensions", []),
                "live": True,
                "cached": True,
            }
    version_url = f"{_CLIENT.base_api}/dataset/{dataset}/edition/{edition}/version/{version}"
    status_meta, meta = _CLIENT.get_json(version_url, params=None)
    if status_meta != 200:
        return status_meta, meta
    dimensions = _extract_dim_ids(meta)
    if cache:
        cache.write(
            cache_key,
            {"dimensions": dimensions, "source_url": version_url},
        )
    return 200, {"dimensions": dimensions, "live": True}


def _options(payload: dict[str, Any]) -> ToolResult:
    dataset = payload.get("dataset")
    edition = payload.get("edition")
    version = payload.get("version")
    dim = payload.get("dimension")
    live_check = _require_live(dataset, edition, version)
    if live_check:
        return live_check
    if not isinstance(dim, str) or not dim:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "Missing dimension"}
    cache = _dataset_cache()
    cache_key = f"ons_codes:options:{dataset}:{edition}:{version}:{dim}"
    if cache:
        cached = cache.read(cache_key)
        if cached and isinstance(cached.get("options"), list):
            return 200, {
                "dimension": dim,
                "options": cached.get("options", []),
                "live": True,
                "cached": True,
            }
    opt_url = f"{_CLIENT.base_api}/dataset/{dataset}/edition/{edition}/version/{version}/dimensions/{dim}/options"
    status_opt, opt_data = _CLIENT.get_all_pages(opt_url, params={"limit": 1000, "page": 1})
    if status_opt != 200:
        return status_opt, opt_data
    if not isinstance(opt_data, list):
        return 500, {
            "isError": True,
            "code": "INTEGRATION_ERROR",
            "message": "Expected option list from ONS API",
        }
    options = _extract_codes({"items": opt_data})
    if cache:
        cache.write(
            cache_key,
            {"options": options, "source_url": opt_url},
        )
    return 200, {"dimension": dim, "options": options, "live": True}

register(Tool(
    name="ons_codes.list",
    description="List available ONS dimensions for a live dataset version.",
    input_schema={"type": "object", "properties": {"tool": {"type": "string", "const": "ons_codes.list"}, "dataset": {"type": "string"}, "edition": {"type": "string"}, "version": {"type": "string"}}, "required": ["dataset", "edition", "version"], "additionalProperties": False},
    output_schema={"type": "object", "properties": {"dimensions": {"type": "array"}, "live": {"type": "boolean"}, "cached": {"type": "boolean"}}, "required": ["dimensions", "live"]},
    handler=_list,
))

register(Tool(
    name="ons_codes.options",
    description="List codes/options for a given ONS live dimension.",
    input_schema={"type": "object", "properties": {"tool": {"type": "string", "const": "ons_codes.options"}, "dimension": {"type": "string"}, "dataset": {"type": "string"}, "edition": {"type": "string"}, "version": {"type": "string"}}, "required": ["dataset", "edition", "version", "dimension"], "additionalProperties": False},
    output_schema={"type": "object", "properties": {"dimension": {"type": "string"}, "options": {"type": "array"}, "live": {"type": "boolean"}, "cached": {"type": "boolean"}}, "required": ["dimension", "options", "live"]},
    handler=_options,
))
