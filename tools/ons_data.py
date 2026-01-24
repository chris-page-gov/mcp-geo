from __future__ import annotations
import json
from typing import Any, cast
from tools.registry import Tool, register, ToolResult
from server.config import settings
from tools.ons_common import client as ons_client


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
            "message": "dataset, edition, and version are required for live ONS queries.",
        }
    return None


def _query(payload: dict[str, Any]) -> ToolResult:
    dataset = payload.get("dataset")
    edition = payload.get("edition")
    version = payload.get("version")
    geography = payload.get("geography")
    measure = payload.get("measure")
    time_range = payload.get("timeRange")  # format: "YYYY Qn-YYYY Qn" or single period
    limit = payload.get("limit", 50)
    page = payload.get("page", 1)
    live_check = _require_live(dataset, edition, version)
    if live_check:
        return live_check
    if not isinstance(limit, int) or not 1 <= limit <= 500:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "limit must be 1-500"}
    if not isinstance(page, int) or page < 1:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "page must be >=1"}
    if time_range and "-" in str(time_range):
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "timeRange ranges are not supported in live mode; use a single time value.",
        }
    params = ons_client.build_paged_params(limit, page, {})
    if geography:
        params["geography"] = geography
    if measure:
        params["measure"] = measure
    if time_range:
        params["time"] = time_range
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


def _dimensions(payload: dict[str, Any]) -> ToolResult:
    dataset = payload.get("dataset")
    edition = payload.get("edition")
    version = payload.get("version")
    only = payload.get("dimension")
    live_check = _require_live(dataset, edition, version)
    if live_check:
        return live_check

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
    return 200, {
        "dimensions": result_map,
        "live": True,
        "dataset": dataset,
        "edition": edition,
        "version": version,
    }


register(Tool(
    name="ons_data.query",
    description="Query live ONS observations (requires dataset/edition/version).",
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
        "required": ["dataset", "edition", "version"],
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
    description="List available ONS observation dimensions from the live API.",
    input_schema={
        "type": "object",
        "properties": {
            "tool": {"type": "string", "const": "ons_data.dimensions"},
            "dimension": {"type": "string", "description": "Return only this dimension's codes"},
            "dataset": {"type": "string"},
            "edition": {"type": "string"},
            "version": {"type": "string"},
        },
        "required": ["dataset", "edition", "version"],
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
    # Live-only: return first matching observation.
    dataset = payload.get("dataset")
    edition = payload.get("edition")
    version = payload.get("version")
    geography = payload.get("geography")
    measure = payload.get("measure")
    time = payload.get("time")
    live_check = _require_live(dataset, edition, version)
    if live_check:
        return live_check
    if not (geography and measure and time):
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "geography, measure, time required"}
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

def _create_filter(payload: dict[str, Any]) -> ToolResult:
    global _FILTER_COUNTER
    # Accept same filtering fields as query + dataset metadata
    dataset = payload.get("dataset")
    edition = payload.get("edition")
    version = payload.get("version")
    live_check = _require_live(dataset, edition, version)
    if live_check:
        return live_check
    filter_payload = {
        k: payload.get(k)
        for k in ["geography", "measure", "timeRange", "dataset", "edition", "version"]
        if payload.get(k) is not None
    }
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
    # Re-use _query logic for live queries
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
    description="Fetch a single observation by geography, measure, time from the live ONS API.",
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
        "required": ["dataset", "edition", "version", "geography", "measure", "time"],
        "additionalProperties": False,
    },
    output_schema={"type": "object", "properties": {"observation": {"type": "object"}, "live": {"type": "boolean"}}, "required": ["observation", "live"]},
    handler=_get_observation,
))

register(Tool(
    name="ons_data.create_filter",
    description="Create a filter for live ONS observations. Returns filterId.",
    input_schema={"type": "object", "properties": {"tool": {"type": "string", "const": "ons_data.create_filter"}, "geography": {"type": "string"}, "measure": {"type": "string"}, "timeRange": {"type": "string"}, "dataset": {"type": "string"}, "edition": {"type": "string"}, "version": {"type": "string"}}, "required": ["dataset", "edition", "version"], "additionalProperties": False},
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
