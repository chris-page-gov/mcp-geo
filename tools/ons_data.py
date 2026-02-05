from __future__ import annotations
import json
import re
from typing import Any, cast
from tools.registry import Tool, register, ToolResult
from server.config import settings
from tools.ons_common import client as ons_client


def _require_live() -> ToolResult | None:
    if not settings.ONS_LIVE_ENABLED:
        return 501, {
            "isError": True,
            "code": "LIVE_DISABLED",
            "message": "ONS live mode is disabled. Set ONS_LIVE_ENABLED=true.",
        }
    return None


_MONTH_INDEX = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}

_TIME_TOKEN_PATTERNS = [
    (re.compile(r"^(?P<year>\d{4})$"), lambda m: int(m.group("year")) * 10000),
    (
        re.compile(r"^(?P<year>\d{4})\s*Q(?P<q>[1-4])$", re.IGNORECASE),
        lambda m: int(m.group("year")) * 100 + int(m.group("q")),
    ),
    (
        re.compile(r"^(?P<year>\d{4})[-\s]?(?P<month>0[1-9]|1[0-2])$"),
        lambda m: int(m.group("year")) * 100 + int(m.group("month")),
    ),
    (
        re.compile(
            r"^(?P<year>\d{4})\s*(?P<month>Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)$",
            re.IGNORECASE,
        ),
        lambda m: int(m.group("year")) * 100 + _MONTH_INDEX[m.group("month")[:3].lower()],
    ),
]

_VERSION_PATTERN = re.compile(
    r"/datasets/(?P<dataset>[^/]+)/editions/(?P<edition>[^/]+)/versions/(?P<version>[^/]+)"
)

_MAX_TIME_RANGE_OPTIONS = 48


def _parse_time_token(value: str) -> int | None:
    for pattern, builder in _TIME_TOKEN_PATTERNS:
        match = pattern.match(value.strip())
        if match:
            return builder(match)
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


def _pick_latest(items: list[dict[str, Any]], key: str) -> str | None:
    if not items:
        return None
    published = [item for item in items if item.get("state") == "published"]
    candidates = published or items
    values: list[str] = []
    for item in candidates:
        val = item.get(key) or item.get("id")
        if isinstance(val, int):
            val = str(val)
        if isinstance(val, str):
            values.append(val)
    if not values:
        return None
    if all(v.isdigit() for v in values):
        return str(max(int(v) for v in values))
    return values[0]


def _resolve_latest_version(dataset: str) -> tuple[str | None, str | None] | tuple[int, dict[str, Any]]:
    editions_url = f"{ons_client.base_api}/datasets/{dataset}/editions"
    status, items = ons_client.get_all_pages(editions_url, params={"limit": 1000, "page": 1})
    if status != 200:
        return status, cast(dict[str, Any], items)
    if not isinstance(items, list):
        return None, None
    edition_id = _pick_latest(items, "edition")
    if not edition_id:
        return None, None
    versions_url = f"{ons_client.base_api}/datasets/{dataset}/editions/{edition_id}/versions"
    status_v, versions = ons_client.get_all_pages(versions_url, params={"limit": 1000, "page": 1})
    if status_v != 200:
        return status_v, cast(dict[str, Any], versions)
    if not isinstance(versions, list):
        return edition_id, None
    version_id = _pick_latest(versions, "version")
    return edition_id, version_id


def _resolve_from_term(term: str) -> tuple[str | None, str | None, str | None, list[dict[str, Any]] | None] | tuple[int, dict[str, Any]]:
    url = f"{ons_client.base_api}/datasets"
    status, data = ons_client.get_json(url, params={"search": term, "limit": 5, "offset": 0})
    if status != 200:
        return status, data
    items = data.get("items", []) or []
    if not items:
        return None, None, None, []
    chosen = None
    for item in items:
        if isinstance(item, dict) and item.get("state") == "published":
            chosen = item
            break
    if chosen is None:
        chosen = items[0] if isinstance(items[0], dict) else None
    if not chosen:
        return None, None, None, []
    dataset_id = chosen.get("id")
    if not isinstance(dataset_id, str):
        return None, None, None, items
    latest = chosen.get("links", {}).get("latest_version", {}).get("href")
    if isinstance(latest, str):
        match = _VERSION_PATTERN.search(latest)
        if match:
            return (
                dataset_id,
                match.group("edition"),
                match.group("version"),
                items,
            )
    resolved = _resolve_latest_version(dataset_id)
    if isinstance(resolved, tuple) and len(resolved) == 2 and not isinstance(resolved[0], int):
        return dataset_id, resolved[0], resolved[1], items
    return dataset_id, None, None, items


def _resolve_time_options(dataset: str, edition: str, version: str) -> tuple[list[str] | None, dict[str, Any] | None]:
    version_url = f"{ons_client.base_api}/datasets/{dataset}/editions/{edition}/versions/{version}"
    status_meta, meta = ons_client.get_json(version_url, params=None)
    if status_meta != 200:
        return None, meta
    dim_ids = _extract_dim_ids(meta)
    time_dim = None
    for dim in dim_ids:
        if dim.lower() in {"time", "date"}:
            time_dim = dim
            break
    if not time_dim:
        for dim in dim_ids:
            if "time" in dim.lower() or "date" in dim.lower():
                time_dim = dim
                break
    if not time_dim:
        return None, {"isError": True, "code": "INVALID_INPUT", "message": "No time dimension found"}
    opt_url = f"{ons_client.base_api}/datasets/{dataset}/editions/{edition}/versions/{version}/dimensions/{time_dim}/options"
    status_opt, opt_data = ons_client.get_all_pages(opt_url, params={"limit": 1000, "page": 1})
    if status_opt != 200:
        return None, cast(dict[str, Any], opt_data)
    if not isinstance(opt_data, list):
        return None, {
            "isError": True,
            "code": "INTEGRATION_ERROR",
            "message": "Expected time option list from ONS API",
        }
    options: list[str] = []
    for entry in opt_data:
        if isinstance(entry, dict):
            val: Any = entry.get("option") or entry.get("id") or entry.get("value") or entry.get("code")
            if isinstance(val, str):
                options.append(val)
    return options, None


def _query(payload: dict[str, Any]) -> ToolResult:
    dataset = payload.get("dataset")
    edition = payload.get("edition")
    version = payload.get("version")
    geography = payload.get("geography")
    measure = payload.get("measure")
    time_range = payload.get("timeRange")  # format: "YYYY Qn-YYYY Qn" or single period
    limit = payload.get("limit", 50)
    page = payload.get("page", 1)
    live_check = _require_live()
    if live_check:
        return live_check
    if not isinstance(limit, int) or not 1 <= limit <= 500:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "limit must be 1-500"}
    if not isinstance(page, int) or page < 1:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "page must be >=1"}
    term = payload.get("term") or payload.get("query") or payload.get("datasetQuery")
    if not (isinstance(dataset, str) and dataset):
        if isinstance(term, str) and term.strip():
            resolved = _resolve_from_term(term.strip())
            if isinstance(resolved[0], int):
                return resolved  # type: ignore[return-value]
            dataset, edition, version, candidates = resolved  # type: ignore[misc]
            if not dataset or not edition or not version:
                return 400, {
                    "isError": True,
                    "code": "INVALID_INPUT",
                    "message": "Unable to resolve dataset edition/version from term.",
                    "candidates": candidates or [],
                }
        else:
            return 400, {
                "isError": True,
                "code": "INVALID_INPUT",
                "message": "dataset, edition, and version are required (or provide term for auto-resolution).",
            }
    if not (isinstance(edition, str) and edition) or not (isinstance(version, str) and version):
        resolved = _resolve_latest_version(dataset)
        if isinstance(resolved[0], int):
            return resolved  # type: ignore[return-value]
        edition, version = resolved
    if not (isinstance(edition, str) and edition) or not (isinstance(version, str) and version):
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "dataset, edition, and version are required for live ONS queries.",
        }
    if time_range and "-" in str(time_range):
        range_text = str(time_range)
        parts = [part.strip() for part in range_text.split("-", 1)]
        if len(parts) != 2 or not all(parts):
            return 400, {
                "isError": True,
                "code": "INVALID_INPUT",
                "message": "timeRange must be formatted like 'YYYY Qn-YYYY Qn' or 'YYYY-YYYY'.",
            }
        start_val = _parse_time_token(parts[0])
        end_val = _parse_time_token(parts[1])
        if start_val is None or end_val is None:
            return 400, {
                "isError": True,
                "code": "INVALID_INPUT",
                "message": "timeRange format not recognized.",
            }
        if start_val > end_val:
            start_val, end_val = end_val, start_val
        options, err = _resolve_time_options(dataset, edition, version)
        if err is not None:
            return 400, err
        if not options:
            return 404, {"isError": True, "code": "NOT_FOUND", "message": "No time options found."}
        option_values: list[tuple[str, int]] = []
        for opt in options:
            parsed = _parse_time_token(opt)
            if parsed is not None:
                option_values.append((opt, parsed))
        in_range = [opt for opt, parsed in option_values if start_val <= parsed <= end_val]
        if not in_range:
            return 404, {"isError": True, "code": "NOT_FOUND", "message": "No time options in range."}
        if len(in_range) > _MAX_TIME_RANGE_OPTIONS:
            return 400, {
                "isError": True,
                "code": "INVALID_INPUT",
                "message": f"timeRange expands to {len(in_range)} values; narrow the range.",
            }
        results: list[dict[str, Any]] = []
        for time_value in in_range:
            params = ons_client.build_paged_params(limit, 1, {})
            if geography:
                params["geography"] = geography
            if measure:
                params["measure"] = measure
            params["time"] = time_value
            url = (
                f"{ons_client.base_api}/datasets/{dataset}/editions/{edition}/versions/{version}/observations"
            )
            status, data = ons_client.get_json(url, params=params)
            if status != 200:
                return status, data
            results.extend(data.get("observations", []))
        return 200, {
            "results": results,
            "count": len(results),
            "limit": limit,
            "page": 1,
            "nextPageToken": None,
            "live": True,
            "dataset": dataset,
            "edition": edition,
            "version": version,
            "timeRange": range_text,
            "timeValues": in_range,
        }
    params = ons_client.build_paged_params(limit, page, {})
    if geography:
        params["geography"] = geography
    if measure:
        params["measure"] = measure
    if time_range:
        params["time"] = time_range
    url = f"{ons_client.base_api}/datasets/{dataset}/editions/{edition}/versions/{version}/observations"
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
    live_check = _require_live()
    if live_check:
        return live_check
    if not all(isinstance(val, str) and val for val in (dataset, edition, version)):
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "dataset, edition, and version are required for live ONS dimensions.",
        }

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

    version_url = f"{ons_client.base_api}/datasets/{dataset}/editions/{edition}/versions/{version}"
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
        opt_url = f"{ons_client.base_api}/datasets/{dataset}/editions/{edition}/versions/{version}/dimensions/{dim_id}/options"
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

def _editions(payload: dict[str, Any]) -> ToolResult:
    dataset = payload.get("dataset")
    if not settings.ONS_LIVE_ENABLED:
        return 501, {
            "isError": True,
            "code": "LIVE_DISABLED",
            "message": "ONS live mode is disabled. Set ONS_LIVE_ENABLED=true.",
        }
    if not isinstance(dataset, str) or not dataset:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "dataset is required"}
    url = f"{ons_client.base_api}/datasets/{dataset}/editions"
    status, items = ons_client.get_all_pages(url, params={"limit": 1000, "page": 1})
    if status != 200:
        return status, items
    if not isinstance(items, list):
        return 500, {
            "isError": True,
            "code": "INTEGRATION_ERROR",
            "message": "Expected editions list from ONS API",
        }
    editions: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        edition_id = item.get("edition") or item.get("id")
        if isinstance(edition_id, int):
            edition_id = str(edition_id)
        if not isinstance(edition_id, str):
            continue
        editions.append({
            "id": edition_id,
            "title": item.get("edition") or item.get("title"),
            "state": item.get("state"),
        })
    return 200, {"dataset": dataset, "editions": editions, "count": len(editions), "live": True}


def _versions(payload: dict[str, Any]) -> ToolResult:
    dataset = payload.get("dataset")
    edition = payload.get("edition")
    if not settings.ONS_LIVE_ENABLED:
        return 501, {
            "isError": True,
            "code": "LIVE_DISABLED",
            "message": "ONS live mode is disabled. Set ONS_LIVE_ENABLED=true.",
        }
    if not isinstance(dataset, str) or not dataset:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "dataset is required"}
    if not isinstance(edition, str) or not edition:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "edition is required"}
    url = f"{ons_client.base_api}/datasets/{dataset}/editions/{edition}/versions"
    status, items = ons_client.get_all_pages(url, params={"limit": 1000, "page": 1})
    if status != 200:
        return status, items
    if not isinstance(items, list):
        return 500, {
            "isError": True,
            "code": "INTEGRATION_ERROR",
            "message": "Expected versions list from ONS API",
        }
    versions: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        version_id = item.get("version") or item.get("id")
        if isinstance(version_id, int):
            version_id = str(version_id)
        if not isinstance(version_id, str):
            continue
        versions.append({
            "id": version_id,
            "state": item.get("state"),
            "releaseDate": item.get("release_date"),
        })
    return 200, {
        "dataset": dataset,
        "edition": edition,
        "versions": versions,
        "count": len(versions),
        "live": True,
    }


register(Tool(
    name="ons_data.query",
    description="Query live ONS observations (dataset/edition/version or search term).",
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
            "term": {"type": "string", "description": "Search term for auto-resolving dataset/edition/version"},
            "query": {"type": "string", "description": "Alias for term"},
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
            "timeRange": {"type": ["string", "null"]},
            "timeValues": {"type": ["array", "null"]},
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

register(Tool(
    name="ons_data.editions",
    description="List live editions for an ONS dataset.",
    input_schema={
        "type": "object",
        "properties": {
            "tool": {"type": "string", "const": "ons_data.editions"},
            "dataset": {"type": "string"},
        },
        "required": ["dataset"],
        "additionalProperties": False,
    },
    output_schema={
        "type": "object",
        "properties": {
            "dataset": {"type": "string"},
            "editions": {"type": "array"},
            "count": {"type": "integer"},
            "live": {"type": "boolean"},
        },
        "required": ["dataset", "editions", "count", "live"],
    },
    handler=_editions,
))

register(Tool(
    name="ons_data.versions",
    description="List live versions for an ONS dataset edition.",
    input_schema={
        "type": "object",
        "properties": {
            "tool": {"type": "string", "const": "ons_data.versions"},
            "dataset": {"type": "string"},
            "edition": {"type": "string"},
        },
        "required": ["dataset", "edition"],
        "additionalProperties": False,
    },
    output_schema={
        "type": "object",
        "properties": {
            "dataset": {"type": "string"},
            "edition": {"type": "string"},
            "versions": {"type": "array"},
            "count": {"type": "integer"},
            "live": {"type": "boolean"},
        },
        "required": ["dataset", "edition", "versions", "count", "live"],
    },
    handler=_versions,
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
    live_check = _require_live()
    if live_check:
        return live_check
    if not all(isinstance(val, str) and val for val in (dataset, edition, version)):
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "dataset, edition, and version are required for live ONS queries.",
        }
    if not (geography and measure and time):
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "geography, measure, time required"}
    params = {"geography": geography, "measure": measure, "time": time}
    url = f"{ons_client.base_api}/datasets/{dataset}/editions/{edition}/versions/{version}/observations"
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
    live_check = _require_live()
    if live_check:
        return live_check
    if not all(isinstance(val, str) and val for val in (dataset, edition, version)):
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "dataset, edition, and version are required for live ONS filters.",
        }
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
