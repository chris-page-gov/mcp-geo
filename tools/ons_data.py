from __future__ import annotations
import json
from pathlib import Path
from typing import Any, cast
from tools.registry import Tool, register, ToolResult
from server.config import settings
from tools.ons_common import client as ons_client

_RESOURCE_PATH = Path(__file__).parent.parent / "resources" / "ons_observations.json"


def _load() -> dict[str, Any]:
    if not _RESOURCE_PATH.exists():  # pragma: no cover
        return {"observations": []}
    return json.loads(_RESOURCE_PATH.read_text())


def _query(payload: dict[str, Any]) -> ToolResult:
    # Live path: when enabled and dataset parameters provided
    dataset = payload.get("dataset")
    edition = payload.get("edition")
    version = payload.get("version")
    if settings.ONS_LIVE_ENABLED and dataset and edition and version:
        limit = payload.get("limit", 50)
        page = payload.get("page", 1)
        if not isinstance(limit, int) or not 1 <= limit <= 500:
            return 400, {"isError": True, "code": "INVALID_INPUT", "message": "limit must be 1-500"}
        if not isinstance(page, int) or page < 1:
            return 400, {"isError": True, "code": "INVALID_INPUT", "message": "page must be >=1"}
        params = ons_client.build_paged_params(limit, page, {})
        url = f"{ons_client.base_api}/dataset/{dataset}/edition/{edition}/version/{version}/observations"
        status, data = ons_client.get_json(url, params=params)
        if status != 200:
            return status, data
        observations = data.get("observations", [])
        next_token = str(page + 1) if len(observations) == limit else None
        return 200, {
            "results": observations,
            "count": data.get("total", len(observations)),
            "limit": limit,
            "page": page,
            "nextPageToken": next_token,
            "live": True,
            "dataset": dataset,
            "edition": edition,
            "version": version,
        }
    data = _load()
    obs = data.get("observations", [])
    # Filters
    geography = payload.get("geography")
    measure = payload.get("measure")
    time_range = payload.get("timeRange")  # format: "YYYY Qn-YYYY Qn" or single period
    limit = payload.get("limit", 50)
    page = payload.get("page", 1)
    if not isinstance(limit, int) or not 1 <= limit <= 500:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "limit must be 1-500"}
    if not isinstance(page, int) or page < 1:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "page must be >=1"}

    def within_range(period: str) -> bool:
        if not time_range:
            return True
        if "-" not in time_range:
            return period == time_range
        start, end = [p.strip() for p in time_range.split('-', 1)]
        series = data.get("dimensions", {}).get("time", [])
        try:
            si = series.index(start)
            ei = series.index(end)
            pi = series.index(period)
        except ValueError:
            return False
        return si <= pi <= ei

    filtered: list[dict[str, Any]] = []
    for o in obs:
        if geography and o.get("geography") != geography:
            continue
        if measure and o.get("measure") != measure:
            continue
        if not within_range(o.get("time", "")):
            continue
        filtered.append(o)

    start = (page - 1) * limit
    end = start + limit
    page_items = filtered[start:end]
    next_page_token = str(page + 1) if end < len(filtered) else None
    return 200, {
        "results": page_items,
        "count": len(filtered),
        "limit": limit,
        "page": page,
        "nextPageToken": next_page_token,
    }


def _dimensions(payload: dict[str, Any]) -> ToolResult:
    dataset = payload.get("dataset")
    edition = payload.get("edition")
    version = payload.get("version")
    only = payload.get("dimension")
    if settings.ONS_LIVE_ENABLED and dataset and edition and version:
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

        version_url = f"{ons_client.base_api}/dataset/{dataset}/edition/{edition}/version/{version}"
        status_meta, meta = ons_client.get_json(version_url, params=None)
        if status_meta != 200:
            return status_meta, meta
        dim_ids = _extract_dim_ids(meta)
        if only:
            if only not in dim_ids:
                return 400, {"isError": True, "code": "INVALID_INPUT", "message": f"Unknown dimension '{only}'"}
            dim_ids = [only]
        result_map: dict[str, list[str]] = {}
        for dim_id in dim_ids:
            opt_url = f"{ons_client.base_api}/dataset/{dataset}/edition/{edition}/version/{version}/dimensions/{dim_id}/options"
            status_opt, opt_data = ons_client.get_json(opt_url, params={"limit": 1000, "page": 1})
            if status_opt != 200:
                return status_opt, opt_data
            result_map[dim_id] = _extract_codes(opt_data)
        return 200, {"dimensions": result_map, "live": True, "dataset": dataset, "edition": edition, "version": version}
    data = _load()
    dims = data.get("dimensions", {})
    # Optional single dimension filter (sample)
    if only:
        if only not in dims:
            return 400, {"isError": True, "code": "INVALID_INPUT", "message": f"Unknown dimension '{only}'"}
        return 200, {"dimensions": {only: dims[only]}, "live": False}
    return 200, {"dimensions": dims, "live": False}


register(Tool(
    name="ons_data.query",
    description="Query ONS observations. Uses live ONS API when ONS_LIVE_ENABLED and dataset/edition/version provided; otherwise queries bundled sample (filters: geography, measure, timeRange; pagination).",
    input_schema={
        "type": "object",
        "properties": {
            "tool": {"type": "string", "const": "ons_data.query"},
            "geography": {"type": "string"},
            "measure": {"type": "string"},
            "timeRange": {"type": "string", "description": "Format 'YYYY Qn-YYYY Qn' or single period 'YYYY Qn'"},
            "limit": {"type": "integer", "minimum": 1, "maximum": 500},
            "page": {"type": "integer", "minimum": 1},
            "dataset": {"type": "string", "description": "ONS dataset ID for live mode"},
            "edition": {"type": "string", "description": "ONS dataset edition for live mode"},
            "version": {"type": "string", "description": "ONS dataset version for live mode"},
        },
        "required": [],
        "additionalProperties": False,
    },
    output_schema={
        "type": "object",
        "properties": {
            "results": {"type": "array", "items": {"type": "object"}},
            "count": {"type": "integer"},
            "limit": {"type": "integer"},
            "page": {"type": "integer"},
            "nextPageToken": {"type": ["string", "null"]},
        },
        "required": ["results", "count", "limit", "page"],
    },
    handler=_query,
))

register(Tool(
    name="ons_data.dimensions",
    description="List available ONS observation dimensions (sample or live dataset metadata). Optionally restrict to one dimension via 'dimension' field.",
    input_schema={
        "type": "object",
        "properties": {
            "tool": {"type": "string", "const": "ons_data.dimensions"},
            "dimension": {"type": "string", "description": "Return only this dimension's codes"},
            "dataset": {"type": "string"},
            "edition": {"type": "string"},
            "version": {"type": "string"},
        },
        "required": [],
        "additionalProperties": False,
    },
    output_schema={
        "type": "object",
        "properties": {
            "dimensions": {"type": "object"},
            "live": {"type": "boolean"},
        },
        "required": ["dimensions", "live"],
    },
    handler=_dimensions,
))
