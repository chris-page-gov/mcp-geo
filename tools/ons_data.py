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

# --- Additional ONS Tools (D1 & D2) -------------------------------------------------

_FILTER_STORE: dict[str, dict[str, Any]] = {}
_FILTER_COUNTER = 0

def _get_observation(payload: dict[str, Any]) -> ToolResult:
    # Simplified: return first matching observation (sample or live)
    dataset = payload.get("dataset")
    edition = payload.get("edition")
    version = payload.get("version")
    geography = payload.get("geography")
    measure = payload.get("measure")
    time = payload.get("time")
    if settings.ONS_LIVE_ENABLED and dataset and edition and version and geography and measure and time:
        # Live single observation path (simulate by querying observations then filtering)
        params = {"geography": geography, "measure": measure, "time": time}
        url = f"{ons_client.base_api}/dataset/{dataset}/edition/{edition}/version/{version}/observations"
        status, data = ons_client.get_json(url, params=params)
        if status != 200:
            return status, data
        obs = data.get("observations", [])
        first = obs[0] if obs else None
        if not first:
            return 404, {"isError": True, "code": "NO_OBSERVATION", "message": "No matching observation"}
        return 200, {"observation": first, "live": True}
    # Sample path
    if not (geography and measure and time):
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "geography, measure, time required"}
    data = _load()
    for o in data.get("observations", []):
        if o.get("geography") == geography and o.get("measure") == measure and o.get("time") == time:
            return 200, {"observation": o, "live": False}
    return 404, {"isError": True, "code": "NO_OBSERVATION", "message": "No matching observation"}

def _create_filter(payload: dict[str, Any]) -> ToolResult:
    global _FILTER_COUNTER
    # Accept same filtering fields as query + dataset metadata
    filter_payload = {k: payload.get(k) for k in ["geography", "measure", "timeRange", "dataset", "edition", "version"] if payload.get(k) is not None}
    _FILTER_COUNTER += 1
    filter_id = f"f{_FILTER_COUNTER:04d}"
    # Always store; if no params provided store empty dict (interpreted as unfiltered sample)
    _FILTER_STORE[filter_id] = filter_payload or {}
    return 201, {"filterId": filter_id, "params": filter_payload}

def _get_filter_output(payload: dict[str, Any]) -> ToolResult:
    filter_id = payload.get("filterId")
    fmt = (payload.get("format") or "JSON").upper()
    if not isinstance(filter_id, str):
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "Missing filterId"}
    stored = _FILTER_STORE.get(filter_id)
    if stored is None:
        # Treat unknown id as 404
        return 404, {"isError": True, "code": "UNKNOWN_FILTER", "message": "Filter not found"}
    # Re-use _query logic for sample; ignore live for now
    status, result = _query(stored)
    if status != 200:
        return status, result
    # Supported formats: JSON (structured object), CSV (text), XLSX (base64 binary)
    if fmt == "JSON":
        return 200, {"filterId": filter_id, "format": fmt, "data": result}
    rows = result.get("results", [])
    if fmt == "CSV":
        # Build header from union of keys
        headers: list[str] = []
        for r in rows:
            if isinstance(r, dict):
                for k in r.keys():
                    if k not in headers:
                        headers.append(k)
        import io, csv
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(headers)
        for r in rows:
            if isinstance(r, dict):
                writer.writerow([r.get(h, "") for h in headers])
        csv_text = buf.getvalue()
        return 200, {"filterId": filter_id, "format": fmt, "contentType": "text/csv", "dataBase64": csv_text.encode().decode(), "rows": len(rows), "columns": len(headers)}
    if fmt == "XLSX":
        try:
            import io
            from openpyxl import Workbook  # type: ignore
            wb = Workbook()
            ws = wb.active
            headers: list[str] = []
            for r in rows:
                if isinstance(r, dict):
                    for k in r.keys():
                        if k not in headers:
                            headers.append(k)
            ws.append(headers)
            for r in rows:
                if isinstance(r, dict):
                    ws.append([r.get(h, "") for h in headers])
            stream = io.BytesIO()
            wb.save(stream)
            b64 = stream.getvalue().hex()  # hex to keep simple (could use base64)
            return 200, {"filterId": filter_id, "format": fmt, "contentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "dataHex": b64, "rows": len(rows), "columns": len(headers)}
        except Exception as exc:  # pragma: no cover
            return 500, {"isError": True, "code": "INTEGRATION_ERROR", "message": f"XLSX generation failed: {exc}"}
    return 400, {"isError": True, "code": "INVALID_INPUT", "message": "Unsupported format (use JSON, CSV, XLSX)"}

register(Tool(
    name="ons_data.get_observation",
    description="Fetch a single observation by geography, measure, time (live or sample).",
    input_schema={
        "type": "object",
        "properties": {
            "tool": {"type": "string", "const": "ons_data.get_observation"},
            "geography": {"type": "string"},
            "measure": {"type": "string"},
            "time": {"type": "string"},
            "dataset": {"type": "string"},
            "edition": {"type": "string"},
            "version": {"type": "string"},
        },
        "required": ["geography", "measure", "time"],
        "additionalProperties": False,
    },
    output_schema={"type": "object", "properties": {"observation": {"type": "object"}, "live": {"type": "boolean"}}, "required": ["observation", "live"]},
    handler=_get_observation,
))

register(Tool(
    name="ons_data.create_filter",
    description="Create a filter for ONS observations (sample subset). Returns filterId.",
    input_schema={"type": "object", "properties": {"tool": {"type": "string", "const": "ons_data.create_filter"}, "geography": {"type": "string"}, "measure": {"type": "string"}, "timeRange": {"type": "string"}}, "required": [], "additionalProperties": False},
    output_schema={"type": "object", "properties": {"filterId": {"type": "string"}, "params": {"type": "object"}}, "required": ["filterId", "params"]},
    handler=_create_filter,
))

register(Tool(
    name="ons_data.get_filter_output",
    description="Retrieve data for a previously created filter (formats: JSON, CSV, XLSX).",
    input_schema={"type": "object", "properties": {"tool": {"type": "string", "const": "ons_data.get_filter_output"}, "filterId": {"type": "string"}, "format": {"type": "string", "enum": ["JSON", "CSV", "XLSX"]}}, "required": ["filterId"], "additionalProperties": False},
    output_schema={"type": "object", "properties": {"filterId": {"type": "string"}, "format": {"type": "string"}, "data": {"type": "object"}, "contentType": {"type": ["string", "null"]}, "dataBase64": {"type": ["string", "null"]}, "dataHex": {"type": ["string", "null"]}, "rows": {"type": ["integer", "null"]}, "columns": {"type": ["integer", "null"]}}, "required": ["filterId", "format"]},
    handler=_get_filter_output,
))
