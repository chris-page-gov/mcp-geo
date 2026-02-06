from __future__ import annotations

import re
from typing import Any

from server.config import settings
from tools.nomis_common import client as nomis_client
from tools.registry import Tool, ToolResult, register

_DATASET_ID_PATTERN = re.compile(r"^[A-Z0-9]+(?:_[A-Z0-9]+)+$", re.IGNORECASE)
_GSS_CODE_PATTERN = re.compile(r"^[EWNS]\d{8}$", re.IGNORECASE)
_WARD_PREFIXES = ("E05", "W05", "S13", "N08")
_SEARCH_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
_MULTI_TERM_SYNONYMS: dict[str, tuple[str, ...]] = {
    "population": ("resident", "census", "demography"),
    "employment": ("labour", "jobs", "work", "unemployment"),
    "housing": ("tenure", "dwelling", "residential", "property"),
    "health": ("wellbeing", "disability"),
    "education": ("qualification", "qualifications", "students"),
}


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
    raw_tokens = [token for token in _SEARCH_TOKEN_PATTERN.findall(query_norm) if token]
    # Preserve prior behavior for short, single-term queries.
    if len(raw_tokens) <= 1:
        filtered: list[dict[str, str | None]] = []
        for entry in entries:
            haystack = " ".join(
                str(entry.get(field, "") or "").lower() for field in ("id", "name", "description")
            )
            if query_norm in haystack:
                filtered.append(entry)
        return filtered

    direct_tokens = tuple(dict.fromkeys(raw_tokens))
    expanded_tokens: list[str] = list(direct_tokens)
    for token in direct_tokens:
        expanded_tokens.extend(_MULTI_TERM_SYNONYMS.get(token, ()))
    expanded_tokens = list(dict.fromkeys(expanded_tokens))

    scored: list[tuple[int, dict[str, str | None]]] = []
    for entry in entries:
        haystack = " ".join(
            str(entry.get(field, "") or "").lower() for field in ("id", "name", "description")
        )
        if not haystack:
            continue
        direct_hits = sum(1 for token in direct_tokens if token in haystack)
        expanded_hits = sum(
            1 for token in expanded_tokens if token not in direct_tokens and token in haystack
        )
        if direct_hits == 0 and query_norm not in haystack:
            continue
        score = direct_hits * 10 + expanded_hits
        if query_norm in haystack:
            score += 25
        score -= max(0, len(haystack) // 250)
        scored.append((score, entry))

    scored.sort(key=lambda item: (-item[0], str(item[1].get("id", ""))))
    return [entry for _, entry in scored]


def _extract_dataset_definition_summary(
    dataset_id: str,
    data: Any,
) -> dict[str, Any]:
    summary: dict[str, Any] = {"id": dataset_id}
    if not isinstance(data, dict):
        return summary

    structure = data.get("structure")
    if not isinstance(structure, dict):
        return summary

    keyfamilies = structure.get("keyfamilies")
    if not isinstance(keyfamilies, dict):
        return summary

    keyfamily_node = keyfamilies.get("keyfamily")
    keyfamilies_list = keyfamily_node if isinstance(keyfamily_node, list) else [keyfamily_node]
    selected: dict[str, Any] | None = None
    for item in keyfamilies_list:
        if not isinstance(item, dict):
            continue
        item_id = _extract_text(item.get("id"))
        if item_id and item_id.lower() == dataset_id.lower():
            selected = item
            break
        if selected is None:
            selected = item
    if not selected:
        return summary

    name = _extract_text(selected.get("name"))
    if name:
        summary["name"] = name

    annotations_node = selected.get("annotations")
    annotations_map: dict[str, str] = {}
    if isinstance(annotations_node, dict):
        raw_annotations = annotations_node.get("annotation")
        annotations = raw_annotations if isinstance(raw_annotations, list) else [raw_annotations]
        for annotation in annotations:
            if not isinstance(annotation, dict):
                continue
            title = _extract_text(annotation.get("annotationtitle"))
            text = _extract_text(annotation.get("annotationtext"))
            if title and text and title not in annotations_map:
                annotations_map[title] = text
    if annotations_map.get("SubDescription"):
        summary["description"] = annotations_map["SubDescription"]
    elif annotations_map.get("MetadataText0"):
        summary["description"] = annotations_map["MetadataText0"]
    if annotations_map.get("Status"):
        summary["status"] = annotations_map["Status"]
    if annotations_map.get("Keywords"):
        summary["keywords"] = annotations_map["Keywords"]
    if annotations_map.get("Mnemonic"):
        summary["mnemonic"] = annotations_map["Mnemonic"]

    components = selected.get("components")
    if isinstance(components, dict):
        dimensions_node = components.get("dimension")
        dimensions = dimensions_node if isinstance(dimensions_node, list) else [dimensions_node]
        dimension_names: list[str] = []
        for dimension in dimensions:
            if not isinstance(dimension, dict):
                continue
            concept_ref = _extract_text(dimension.get("conceptref"))
            if concept_ref:
                dimension_names.append(concept_ref)
        if dimension_names:
            summary["dimensions"] = dimension_names
        primary_measure = components.get("primarymeasure")
        if isinstance(primary_measure, dict):
            primary_measure_ref = _extract_text(primary_measure.get("conceptref"))
            if primary_measure_ref:
                summary["primaryMeasure"] = primary_measure_ref

    return summary


def _overview_dimensions(overview_data: Any) -> list[dict[str, Any]]:
    if not isinstance(overview_data, dict):
        return []
    overview = overview_data.get("overview")
    if not isinstance(overview, dict):
        return []
    dimensions_node = overview.get("dimensions")
    if not isinstance(dimensions_node, dict):
        return []
    dimension_values = dimensions_node.get("dimension")
    dimensions = dimension_values if isinstance(dimension_values, list) else [dimension_values]
    out: list[dict[str, Any]] = []
    for dimension in dimensions:
        if not isinstance(dimension, dict):
            continue
        concept = _extract_text(dimension.get("concept"))
        if not concept:
            continue
        name = _extract_text(dimension.get("name")) or concept
        sample_values: list[str] = []
        codes_node = dimension.get("codes")
        if isinstance(codes_node, dict):
            code_values = codes_node.get("code")
            codes = code_values if isinstance(code_values, list) else [code_values]
            for code in codes:
                if not isinstance(code, dict):
                    continue
                value = _extract_text(code.get("value"))
                if value:
                    sample_values.append(value)
        size_raw = dimension.get("size")
        try:
            size = int(size_raw) if size_raw is not None else None
        except (TypeError, ValueError):
            size = None
        out.append(
            {
                "concept": concept,
                "name": name,
                "size": size,
                "sampleValues": sample_values[:10],
            }
        )
    return out


def _fetch_dataset_overview(dataset: str) -> dict[str, Any] | None:
    overview_path = (
        f"dataset/{dataset}.overview.json?select=DatasetInfo,Coverage,Keywords,Dimensions,Codes"
    )
    status, overview_data = nomis_client.get_json(_build_url(overview_path))
    if status != 200:
        return None
    if not isinstance(overview_data, dict):
        return None
    overview = overview_data.get("overview")
    if not isinstance(overview, dict):
        return None
    keywords_text = _extract_text(overview.get("keywords")) or ""
    keywords = [item.strip() for item in keywords_text.split(",") if item.strip()]
    return {
        "coverage": _extract_text(overview.get("coverage")),
        "description": _extract_text(overview.get("description")),
        "keywords": keywords,
        "dimensions": _overview_dimensions(overview_data),
    }


def _infer_query_template(dataset: str, overview: dict[str, Any] | None) -> dict[str, str]:
    template: dict[str, str] = {}
    if not overview:
        return template
    dimensions = overview.get("dimensions")
    if not isinstance(dimensions, list):
        return template
    for dim in dimensions:
        if not isinstance(dim, dict):
            continue
        concept = _extract_text(dim.get("concept"))
        if not concept:
            continue
        concept_key = concept.lower()
        if concept_key == "geography":
            continue
        sample_values = dim.get("sampleValues")
        values = sample_values if isinstance(sample_values, list) else []
        selected: str | None = None
        if len(values) == 1:
            selected = str(values[0])
        elif concept_key == "measures":
            values_text = [str(v) for v in values]
            if "20100" in values_text:
                selected = "20100"
            elif values_text:
                selected = values_text[0]
        elif values:
            selected = str(values[0])
        if selected:
            template[concept_key] = selected
    if "geography" not in template:
        # NOMIS Census 2021 ward queries require a TYPE selector before GSS ward codes.
        template["geography"] = "TYPE499,E05012621,E05012622"
    return template


def _is_plain_gss_geography(geography: str) -> bool:
    parts = [part.strip().upper() for part in geography.split(",") if part.strip()]
    if not parts:
        return False
    if any(part.startswith("TYPE") for part in parts):
        return False
    return all(_GSS_CODE_PATTERN.fullmatch(part) for part in parts)


def _maybe_add_ward_type_selector(params: dict[str, Any]) -> dict[str, Any] | None:
    geography = params.get("geography")
    if not isinstance(geography, str):
        return None
    if not _is_plain_gss_geography(geography):
        return None
    parts = [part.strip().upper() for part in geography.split(",") if part.strip()]
    if not parts:
        return None
    if not all(part.startswith(_WARD_PREFIXES) for part in parts):
        return None
    adjusted = dict(params)
    adjusted["geography"] = f"TYPE499,{','.join(parts)}"
    return adjusted


def _missing_dimensions_message(
    params: dict[str, Any],
    overview: dict[str, Any] | None,
) -> tuple[list[str], dict[str, str]]:
    dimensions = overview.get("dimensions") if isinstance(overview, dict) else []
    required_keys = [
        str(dim.get("concept", "")).lower()
        for dim in dimensions
        if isinstance(dim, dict) and str(dim.get("concept", "")).strip()
    ]
    provided = {str(key).strip().lower() for key in params.keys()}
    missing = [key for key in required_keys if key not in provided]
    template = _infer_query_template("unknown", overview)
    return missing, template


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
        if include_raw:
            result: dict[str, Any] = {"live": True, "dataset": dataset, "format": fmt, "data": data}
            result["raw"] = data
            return 200, result
        summary = _extract_dataset_definition_summary(dataset, data)
        overview = _fetch_dataset_overview(dataset)
        if overview:
            if overview.get("description") and not summary.get("description"):
                summary["description"] = overview["description"]
            if overview.get("coverage"):
                summary["coverage"] = overview["coverage"]
            if overview.get("keywords"):
                summary["keywords"] = overview["keywords"]
            if overview.get("dimensions"):
                summary["dimensions"] = [
                    dim.get("concept")
                    for dim in overview["dimensions"]
                    if isinstance(dim, dict) and dim.get("concept")
                ]
        entries = _extract_dataset_entries(data)
        matched_entry = next(
            (entry for entry in entries if str(entry.get("id", "")).lower() == dataset.lower()),
            None,
        )
        if matched_entry:
            if matched_entry.get("name") and not summary.get("name"):
                summary["name"] = matched_entry["name"]
            if matched_entry.get("description") and not summary.get("description"):
                summary["description"] = matched_entry["description"]
        return 200, {
            "live": True,
            "dataset": dataset,
            "format": fmt,
            "summary": summary,
            "overview": overview,
            "queryTemplate": _infer_query_template(dataset, overview),
            "hints": [
                "Dataset definitions can be large; this response is a compact summary.",
                "Set includeRaw=true to return the full upstream definition payload.",
                (
                    "If querying Census wards with GSS codes, geography usually needs "
                    "TYPE499 prefixed (for example TYPE499,E05012621,E05012622)."
                ),
            ],
            "data": {"dataset": summary},
        }
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
        params_dict = params or {}
        if "incomplete" in err.lower():
            adjusted = _maybe_add_ward_type_selector(params_dict)
            if adjusted:
                retry_status, retry_data = nomis_client.get_json(_build_url(path), params=adjusted)
                if retry_status == 200:
                    retry_err = _extract_nomis_error(retry_data)
                    if not retry_err:
                        return 200, {
                            "live": True,
                            "dataset": dataset,
                            "format": fmt,
                            "data": retry_data,
                            "queryAdjusted": {
                                "geographySelectorInjected": True,
                                "originalGeography": params_dict.get("geography"),
                                "adjustedGeography": adjusted.get("geography"),
                            },
                            "hints": [
                                (
                                    "NOMIS required a geography TYPE selector; the query was retried "
                                    "with TYPE499 prefixed to ward GSS codes."
                                )
                            ],
                        }
            overview = _fetch_dataset_overview(dataset)
            missing, template = _missing_dimensions_message(params_dict, overview)
            hint = (
                "Required dimensions likely missing or malformed. "
                "Use nomis.datasets with dataset=<id> to inspect queryTemplate and dimensions."
            )
            if isinstance(params_dict.get("geography"), str):
                hint = (
                    f"{hint} For ward GSS codes, try geography='TYPE499,{params_dict.get('geography')}'."
                )
            return 400, {
                "isError": True,
                "code": "NOMIS_QUERY_ERROR",
                "message": err,
                "missingDimensions": missing,
                "suggestedParams": template,
                "hint": hint,
            }
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
                "description": (
                    "Include the full upstream payload (required to fetch full "
                    "dataset definitions when dataset is provided)."
                ),
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
            "summary": {"type": "object"},
            "overview": {"type": "object"},
            "queryTemplate": {"type": "object"},
            "hints": {"type": "array", "items": {"type": "string"}},
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
