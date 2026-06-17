from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Any

from tools.registry import Tool, ToolResult, get, register

WORKFLOW_VERSION = "2026-06-17"
MAX_RECORDS = 500

_NON_ALNUM_RE = re.compile(r"[^A-Z0-9]+")
_POSTCODE_RE = re.compile(r"\b([A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2})\b", re.IGNORECASE)
_POLYGON_RE = re.compile(r"^\s*POLYGON\s*\(\((?P<body>.+)\)\)\s*$", re.IGNORECASE | re.DOTALL)

_ADDRESS_TOKEN_REPLACEMENTS = {
    "AVE": "AVENUE",
    "CL": "CLOSE",
    "DR": "DRIVE",
    "LN": "LANE",
    "RD": "ROAD",
    "ST": "STREET",
}

_WORKFLOWS: dict[str, dict[str, Any]] = {
    "batch_address_match": {
        "title": "Batch address to UPRN match review",
        "stakeholderScenarios": ["SG02", "SG01", "SG06", "SG07", "SG09", "SG10"],
        "purpose": (
            "Normalise address rows, classify supplied or resolved UPRNs into confidence "
            "bands, flag duplicate/collision cases, and return review/export queues."
        ),
        "requiredInputs": ["records"],
        "optionalInputs": ["fieldMap"],
        "primaryTools": ["os_places.search", "os_places.by_postcode"],
        "outputContracts": ["matchedRows", "reviewQueue", "duplicateGroups", "export"],
    },
    "incident_impact": {
        "title": "Incident geometry to affected premises and support counts",
        "stakeholderScenarios": ["SG01", "SG06", "SG07"],
        "purpose": (
            "Intersect resolved premises or household records with an incident polygon, "
            "deduplicate affected premises, summarise support categories, and expose "
            "records that still need OS Places or manual review."
        ),
        "requiredInputs": ["geometryWkt", "records"],
        "optionalInputs": ["fieldMap"],
        "primaryTools": [
            "os_places.search",
            "admin_lookup.containing_areas",
            "os_apps.render_boundary_explorer",
        ],
        "outputContracts": [
            "affectedPremises",
            "categorySummary",
            "reviewQueue",
            "anomalies",
            "export",
        ],
    },
    "planning_constraints": {
        "title": "Planning and environmental constraint review",
        "stakeholderScenarios": ["SG05"],
        "purpose": (
            "Create a first-class site-constraint workflow contract for planning.data "
            "and local-plan layers, with explicit source dependencies and review gates."
        ),
        "requiredInputs": ["site or siteGeometryWkt"],
        "optionalInputs": ["layers", "fieldMap"],
        "primaryTools": [
            "os_places.search",
            "admin_lookup.containing_areas",
            "os_features.collections",
            "os_apps.render_boundary_explorer",
        ],
        "outputContracts": ["constraintLayers", "intersectionPlan", "reviewQueue", "export"],
    },
}


def _invalid(message: str) -> ToolResult:
    return 400, {"isError": True, "code": "INVALID_INPUT", "message": message}


def _normalize_postcode(text: Any) -> str:
    raw = str(text or "").strip().upper()
    match = _POSTCODE_RE.search(raw)
    if match:
        return _NON_ALNUM_RE.sub("", match.group(1).upper())
    return ""


def _normalize_address(text: Any) -> str:
    raw = str(text or "").upper()
    postcode = _normalize_postcode(raw)
    if postcode:
        raw = raw.replace(postcode, " ")
    raw = _NON_ALNUM_RE.sub(" ", raw)
    tokens = [
        _ADDRESS_TOKEN_REPLACEMENTS.get(token.rstrip("."), token.rstrip("."))
        for token in raw.split()
        if token
    ]
    return " ".join(tokens)


def _core_tokens(text: Any) -> list[str]:
    stopwords = {
        "AND",
        "APARTMENT",
        "AVENUE",
        "CLOSE",
        "COURT",
        "DRIVE",
        "FLAT",
        "HOUSE",
        "LANE",
        "PLACE",
        "ROAD",
        "STREET",
        "THE",
        "UNIT",
    }
    return [token for token in _normalize_address(text).split() if token not in stopwords]


def _token_overlap_ratio(left: list[str], right: list[str]) -> float:
    if not left or not right:
        return 0.0
    left_counter = Counter(left)
    right_counter = Counter(right)
    overlap = sum((left_counter & right_counter).values())
    total = max(sum(left_counter.values()), sum(right_counter.values()))
    return overlap / total if total else 0.0


def _address_match_score(query: Any, candidate: Any) -> float:
    query_text = str(query or "")
    candidate_text = str(candidate or "")
    query_postcode = _normalize_postcode(query_text)
    candidate_postcode = _normalize_postcode(candidate_text)
    postcode_score = 1.0 if query_postcode and query_postcode == candidate_postcode else 0.0
    query_norm = _normalize_address(query_text)
    candidate_norm = _normalize_address(candidate_text)
    containment_score = (
        1.0
        if query_norm
        and candidate_norm
        and (query_norm in candidate_norm or candidate_norm in query_norm)
        else 0.0
    )
    token_score = _token_overlap_ratio(_core_tokens(query_text), _core_tokens(candidate_text))
    score = (0.4 * postcode_score) + (0.3 * containment_score) + (0.3 * token_score)
    return round(min(score, 1.0), 4)


def _resolve_with_os_places(row: dict[str, Any], *, limit: int) -> dict[str, Any]:
    address = str(row.get("address") or "").strip()
    if not address:
        return {"status": "skipped", "reason": "missing_address"}
    tool = get("os_places.search")
    if tool is None or tool.handler is None:
        return {"status": "skipped", "reason": "os_places.search_not_registered"}
    status, body = tool.call({"text": address, "limit": limit})
    if status != 200 or not isinstance(body, dict) or body.get("isError"):
        return {
            "status": "error",
            "statusCode": status,
            "code": body.get("code") if isinstance(body, dict) else None,
            "message": body.get("message") if isinstance(body, dict) else "OS Places error",
        }
    results = body.get("results", [])
    if not isinstance(results, list) or not results:
        return {"status": "unmatched", "candidateCount": 0}
    scored: list[tuple[float, dict[str, Any]]] = []
    for result in results:
        if isinstance(result, dict):
            scored.append((_address_match_score(address, result.get("address")), result))
    if not scored:
        return {"status": "unmatched", "candidateCount": 0}
    scored.sort(key=lambda item: item[0], reverse=True)
    best_score, best = scored[0]
    second_score = scored[1][0] if len(scored) > 1 else 0.0
    match_type = "high_confidence"
    if best_score < 0.65:
        match_type = "unmatched"
    elif best_score < 0.85 or abs(best_score - second_score) <= 0.03:
        match_type = "review"
    return {
        "status": "resolved" if match_type != "unmatched" else "unmatched",
        "candidateCount": len(scored),
        "matchType": match_type,
        "score": best_score,
        "uprn": best.get("uprn"),
        "address": best.get("address"),
        "lat": best.get("lat"),
        "lon": best.get("lon"),
        "classification": best.get("classificationDescription") or best.get("classification"),
    }


def _first_present(row: dict[str, Any], field_map: dict[str, str], key: str) -> Any:
    mapped = field_map.get(key)
    if mapped and mapped in row:
        return row.get(mapped)
    candidates = {
        "id": ("record_id", "source_id", "asset_id", "site_id", "id"),
        "address": ("address_text", "address", "site_address", "full_address", "text", "query"),
        "postcode": ("postcode", "post_code", "POSTCODE"),
        "uprn": ("uprn", "UPRN"),
        "category": ("resident_group", "category", "vulnerability_category", "support_category"),
        "lat": ("lat", "LAT", "latitude", "Latitude"),
        "lon": ("lon", "lng", "LNG", "longitude", "Longitude"),
        "matchType": ("matchType", "match_type", "match_status"),
        "score": ("score", "match_score", "confidence"),
    }.get(key, ())
    for candidate in candidates:
        if candidate in row and row.get(candidate) not in (None, ""):
            return row.get(candidate)
    return None


def _safe_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _record_id(row: dict[str, Any], field_map: dict[str, str], index: int) -> str:
    value = _first_present(row, field_map, "id")
    if value not in (None, ""):
        return str(value)
    return f"row-{index + 1}"


def _normalise_records(
    records: list[dict[str, Any]], field_map: dict[str, str]
) -> list[dict[str, Any]]:
    normalised: list[dict[str, Any]] = []
    for index, row in enumerate(records):
        address = str(_first_present(row, field_map, "address") or "").strip()
        postcode = str(_first_present(row, field_map, "postcode") or "").strip()
        uprn_value = _first_present(row, field_map, "uprn")
        uprn = str(uprn_value).strip() if uprn_value not in (None, "") else ""
        match_type = str(_first_present(row, field_map, "matchType") or "").strip()
        score = _safe_float(_first_present(row, field_map, "score"))
        normalised_address = _normalize_address(address)
        normalised_postcode = _normalize_postcode(postcode or address)
        duplicate_key = uprn or f"{normalised_address}|{normalised_postcode}"
        normalised.append(
            {
                "recordId": _record_id(row, field_map, index),
                "source": row,
                "address": address,
                "normalizedAddress": normalised_address,
                "postcode": normalised_postcode,
                "uprn": uprn or None,
                "category": _first_present(row, field_map, "category"),
                "lat": _safe_float(_first_present(row, field_map, "lat")),
                "lon": _safe_float(_first_present(row, field_map, "lon")),
                "matchType": match_type or None,
                "score": score,
                "duplicateKey": duplicate_key,
            }
        )
    return normalised


def _load_records(payload: dict[str, Any]) -> tuple[ToolResult | None, list[dict[str, Any]]]:
    raw_records = payload.get("records", [])
    if raw_records is None:
        raw_records = []
    if not isinstance(raw_records, list):
        return _invalid("records must be an array when provided"), []
    if len(raw_records) > MAX_RECORDS:
        return _invalid(f"records must contain {MAX_RECORDS} rows or fewer"), []
    records: list[dict[str, Any]] = []
    for index, item in enumerate(raw_records):
        if not isinstance(item, dict):
            return _invalid(f"records[{index}] must be an object"), []
        records.append(item)
    return None, records


def _load_field_map(payload: dict[str, Any]) -> tuple[ToolResult | None, dict[str, str]]:
    raw = payload.get("fieldMap", {})
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        return _invalid("fieldMap must be an object when provided"), {}
    out: dict[str, str] = {}
    for key, value in raw.items():
        if not isinstance(key, str) or not isinstance(value, str):
            return _invalid("fieldMap keys and values must be strings"), {}
        out[key] = value
    return None, out


def _parse_polygon_wkt(value: Any) -> tuple[ToolResult | None, list[tuple[float, float]]]:
    text = str(value or "").strip()
    if not text:
        return _invalid("geometryWkt is required for incident_impact"), []
    match = _POLYGON_RE.match(text)
    if not match:
        return _invalid("geometryWkt must be a POLYGON((lon lat,...)) WKT string"), []
    points: list[tuple[float, float]] = []
    for part in match.group("body").split(","):
        coords = part.strip().split()
        if len(coords) < 2:
            return _invalid("geometryWkt contains an invalid coordinate pair"), []
        lon = _safe_float(coords[0])
        lat = _safe_float(coords[1])
        if lon is None or lat is None:
            return _invalid("geometryWkt contains a non-numeric coordinate"), []
        points.append((lon, lat))
    if len(points) < 4:
        return _invalid("geometryWkt polygon must contain at least four coordinate pairs"), []
    return None, points


def _point_in_polygon(lon: float, lat: float, polygon: list[tuple[float, float]]) -> bool:
    inside = False
    for index, (x1, y1) in enumerate(polygon):
        x2, y2 = polygon[(index + 1) % len(polygon)]
        if ((y1 > lat) != (y2 > lat)) and (
            lon < (x2 - x1) * (lat - y1) / ((y2 - y1) or 1e-12) + x1
        ):
            inside = not inside
    return inside


def _duplicate_groups(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = str(row.get("duplicateKey") or "")
        if key:
            grouped[key].append(row)
    out: list[dict[str, Any]] = []
    for key, group in sorted(grouped.items()):
        if len(group) <= 1:
            continue
        out.append(
            {
                "key": key,
                "count": len(group),
                "recordIds": [str(item["recordId"]) for item in group],
                "uprn": group[0].get("uprn"),
            }
        )
    return out


def _classify_match(row: dict[str, Any], duplicate_keys: set[str]) -> tuple[str, str, str]:
    explicit_type = str(row.get("matchType") or "").strip().lower()
    if explicit_type in {"high_confidence", "review", "unmatched"}:
        band = explicit_type
    elif row.get("uprn"):
        band = "high_confidence"
    elif row.get("address"):
        band = "review"
    else:
        band = "unmatched"

    reasons: list[str] = []
    if row.get("duplicateKey") in duplicate_keys:
        reasons.append("duplicate_input")
        if band == "high_confidence":
            band = "review"
    if not row.get("uprn") and row.get("address"):
        reasons.append("needs_os_places_resolution")
    if not row.get("address") and not row.get("uprn"):
        reasons.append("missing_address_or_uprn")
    if row.get("score") is not None and float(row["score"]) < 0.65:
        reasons.append("low_similarity")
        band = "unmatched"
    status = "matched" if band == "high_confidence" else "needs_review"
    if band == "unmatched":
        status = "unmatched"
    return band, status, reasons[0] if reasons else ""


def _resolve_addresses_if_requested(
    rows: list[dict[str, Any]], payload: dict[str, Any]
) -> list[dict[str, Any]]:
    if payload.get("resolveAddresses") is not True:
        return []
    raw_limit = payload.get("candidateLimit", 10)
    if not isinstance(raw_limit, int) or raw_limit < 1 or raw_limit > 25:
        raw_limit = 10
    resolution_evidence: list[dict[str, Any]] = []
    for row in rows:
        if row.get("uprn"):
            resolution_evidence.append({"recordId": row["recordId"], "status": "already_resolved"})
            continue
        resolution = _resolve_with_os_places(row, limit=raw_limit)
        resolution_evidence.append({"recordId": row["recordId"], **resolution})
        if resolution.get("uprn"):
            row["uprn"] = str(resolution["uprn"])
            row["duplicateKey"] = row["uprn"]
        if resolution.get("lat") is not None:
            row["lat"] = _safe_float(resolution.get("lat"))
        if resolution.get("lon") is not None:
            row["lon"] = _safe_float(resolution.get("lon"))
        if resolution.get("address"):
            row["resolvedAddress"] = resolution.get("address")
        if resolution.get("matchType"):
            row["matchType"] = resolution.get("matchType")
        if resolution.get("score") is not None:
            row["score"] = _safe_float(resolution.get("score"))
    return resolution_evidence


def _run_batch_address_match(payload: dict[str, Any]) -> ToolResult:
    records_error, records = _load_records(payload)
    if records_error is not None:
        return records_error
    field_error, field_map = _load_field_map(payload)
    if field_error is not None:
        return field_error
    rows = _normalise_records(records, field_map)
    resolution_evidence = _resolve_addresses_if_requested(rows, payload)
    duplicates = _duplicate_groups(rows)
    duplicate_keys = {str(item["key"]) for item in duplicates}
    matched_rows: list[dict[str, Any]] = []
    review_queue: list[dict[str, Any]] = []
    for row in rows:
        band, status, reason = _classify_match(row, duplicate_keys)
        result = {
            "recordId": row["recordId"],
            "address": row["address"],
            "postcode": row["postcode"],
            "uprn": row["uprn"],
            "confidenceBand": band,
            "status": status,
            "score": row["score"],
            "reviewReason": reason or None,
        }
        matched_rows.append(result)
        if status != "matched":
            review_queue.append(
                {
                    "recordId": row["recordId"],
                    "address": row["address"],
                    "uprn": row["uprn"],
                    "reason": reason or band,
                }
            )
    counts = Counter(str(row["confidenceBand"]) for row in matched_rows)
    return 200, _base_response(
        "batch_address_match",
        answer_status="ready_for_review",
        summary=(
            f"Processed {len(rows)} rows into {counts.get('high_confidence', 0)} "
            f"high-confidence matches, {counts.get('review', 0)} review rows and "
            f"{counts.get('unmatched', 0)} unmatched rows."
        ),
        method=[
            "Normalise address, postcode and supplied UPRN fields.",
            "Use supplied matchType/score where present, otherwise classify UPRN-backed rows.",
            "Flag duplicate UPRN or normalised-address keys for manual review.",
            "Return review and export queues without fabricating missing UPRNs.",
        ],
        results={
            "inputRecords": len(rows),
            "highConfidenceMatches": counts.get("high_confidence", 0),
            "reviewMatches": counts.get("review", 0),
            "unmatched": counts.get("unmatched", 0),
            "matchedRows": matched_rows,
            "duplicateGroups": duplicates,
            "resolutionEvidence": resolution_evidence,
        },
        review_queue=review_queue,
        next_actions=[
            "Call os_places.search for rows with needs_os_places_resolution.",
            "Resolve duplicate_input groups before using counts in operational decisions.",
        ],
    )


def _run_incident_impact(payload: dict[str, Any]) -> ToolResult:
    records_error, records = _load_records(payload)
    if records_error is not None:
        return records_error
    field_error, field_map = _load_field_map(payload)
    if field_error is not None:
        return field_error
    polygon_error, polygon = _parse_polygon_wkt(payload.get("geometryWkt"))
    if polygon_error is not None:
        return polygon_error

    rows = _normalise_records(records, field_map)
    resolution_evidence = _resolve_addresses_if_requested(rows, payload)
    affected: list[dict[str, Any]] = []
    review_queue: list[dict[str, Any]] = []
    for row in rows:
        lon = row.get("lon")
        lat = row.get("lat")
        if lon is None or lat is None:
            review_queue.append(
                {
                    "recordId": row["recordId"],
                    "address": row["address"],
                    "uprn": row["uprn"],
                    "reason": "needs_coordinate_resolution",
                }
            )
            continue
        inside = _point_in_polygon(float(lon), float(lat), polygon)
        if inside:
            affected.append(row)

    affected_duplicates = _duplicate_groups(affected)
    premise_keys = {str(row.get("duplicateKey")) for row in affected if row.get("duplicateKey")}
    category_counts = Counter(
        str(row.get("category") or "uncategorised") for row in affected
    )
    affected_rows = [
        {
            "recordId": row["recordId"],
            "address": row["address"],
            "uprn": row["uprn"],
            "category": row.get("category"),
            "lat": row.get("lat"),
            "lon": row.get("lon"),
        }
        for row in affected
    ]
    answer_status = "ready_for_review" if affected or not review_queue else "needs_resolution"
    if review_queue and not affected:
        answer_status = "needs_coordinate_resolution"
    return 200, _base_response(
        "incident_impact",
        answer_status=answer_status,
        summary=(
            f"Found {len(affected)} affected records across {len(premise_keys)} "
            f"deduplicated premise keys; {len(review_queue)} rows still need coordinate "
            "resolution or manual review."
        ),
        method=[
            "Parse the incident polygon from WKT.",
            "Use supplied lat/lon for point-in-polygon testing.",
            "Deduplicate affected records by UPRN, falling back to normalised address/postcode.",
            "Summarise affected records by support category and return review rows.",
        ],
        results={
            "inputRecords": len(rows),
            "affectedRecords": len(affected),
            "affectedPremises": len(premise_keys),
            "affectedRows": affected_rows,
            "categorySummary": [
                {"category": category, "records": count}
                for category, count in sorted(category_counts.items())
            ],
            "duplicateGroups": affected_duplicates,
            "resolutionEvidence": resolution_evidence,
        },
        review_queue=review_queue,
        next_actions=[
            "Resolve review rows through os_places.search or os_places.by_uprn.",
            "Call admin_lookup.containing_areas for a representative affected point.",
            "Open os_apps.render_boundary_explorer for map review before operational export.",
        ],
    )


def _default_constraint_layers(raw_layers: Any) -> list[dict[str, Any]]:
    if isinstance(raw_layers, list) and raw_layers:
        layers: list[dict[str, Any]] = []
        for index, item in enumerate(raw_layers):
            if isinstance(item, dict):
                name = str(item.get("name") or item.get("dataset") or f"layer-{index + 1}")
                source = str(item.get("source") or "user_supplied")
                status = str(item.get("status") or "supplied")
            else:
                name = str(item)
                source = "user_supplied"
                status = "supplied"
            layers.append({"name": name, "source": source, "status": status})
        return layers
    return [
        {
            "name": "flood-risk-zone",
            "source": "https://www.planning.data.gov.uk/dataset/flood-risk-zone",
            "status": "connector_needed",
        },
        {
            "name": "conservation-area",
            "source": "https://www.planning.data.gov.uk/dataset/conservation-area",
            "status": "connector_needed",
        },
        {
            "name": "listed-building",
            "source": "https://www.planning.data.gov.uk/dataset/listed-building",
            "status": "connector_needed",
        },
        {
            "name": "tree-preservation-zone",
            "source": "https://www.planning.data.gov.uk/dataset/tree-preservation-zone",
            "status": "connector_needed",
        },
    ]


def _run_planning_constraints(payload: dict[str, Any]) -> ToolResult:
    site = str(payload.get("site") or "").strip()
    site_geometry = str(payload.get("siteGeometryWkt") or "").strip()
    bbox = payload.get("bbox")
    if not site and not site_geometry and not bbox:
        return _invalid("planning_constraints requires site, siteGeometryWkt, or bbox")
    layers = _default_constraint_layers(payload.get("layers"))
    supplied_layers = [layer for layer in layers if layer["status"] == "supplied"]
    needs_connectors = [layer for layer in layers if layer["status"] != "supplied"]
    return 200, _base_response(
        "planning_constraints",
        answer_status="ready_for_review" if supplied_layers else "needs_external_layers",
        summary=(
            "Planning constraint workflow contract is ready. "
            f"{len(supplied_layers)} layer(s) were supplied and "
            f"{len(needs_connectors)} public connector(s) still need live data."
        ),
        method=[
            "Resolve the site to a point, polygon, or bbox.",
            "Place the site in administrative context with admin_lookup.containing_areas.",
            "Fetch or ingest planning.data and local-plan layers with source freshness metadata.",
            "Intersect the site geometry with every supplied layer and record caveats.",
            "Return a human-review queue before any planning or enforcement decision is made.",
        ],
        results={
            "site": site or None,
            "siteGeometrySupplied": bool(site_geometry),
            "bbox": bbox,
            "constraintLayers": layers,
            "intersectionPlan": [
                {
                    "step": index + 1,
                    "layer": layer["name"],
                    "operation": "intersect_site_geometry",
                    "status": (
                        "ready"
                        if layer["status"] == "supplied"
                        else "blocked_until_ingested"
                    ),
                }
                for index, layer in enumerate(layers)
            ],
        },
        review_queue=[
            {
                "layer": layer["name"],
                "reason": "connector_needed",
                "source": layer["source"],
            }
            for layer in needs_connectors
        ],
        next_actions=[
            "Resolve the site through os_places.search when only a textual address is supplied.",
            "Ingest planning.data layers with publication date and licence metadata.",
            "Run geometry intersections and have a planning officer review constraints before use.",
        ],
    )


def _base_response(
    workflow_id: str,
    *,
    answer_status: str,
    summary: str,
    method: list[str],
    results: dict[str, Any],
    review_queue: list[dict[str, Any]],
    next_actions: list[str],
) -> dict[str, Any]:
    workflow = _WORKFLOWS[workflow_id]
    return {
        "workflowId": workflow_id,
        "version": WORKFLOW_VERSION,
        "title": workflow["title"],
        "productSurfaceReady": True,
        "answerStatus": answer_status,
        "stakeholderScenarios": workflow["stakeholderScenarios"],
        "summary": summary,
        "method": method,
        "datasetsToolsUsed": workflow["primaryTools"],
        "results": results,
        "reviewQueue": review_queue,
        "export": {
            "formats": ["json", "csv"],
            "fields": _export_fields(workflow_id),
            "manualReviewRequired": bool(review_queue),
        },
        "confidenceCaveats": _caveats(workflow_id),
        "nextActions": next_actions,
        "provenance": {
            "source": "mcp-geo native workflow",
            "workflowVersion": WORKFLOW_VERSION,
            "syntheticDataHandling": (
                "Inputs are treated as caller-supplied records; sensitive or synthetic "
                "status must be preserved in downstream exports."
            ),
        },
    }


def _export_fields(workflow_id: str) -> list[str]:
    if workflow_id == "incident_impact":
        return ["recordId", "uprn", "address", "category", "lat", "lon", "insideIncident"]
    if workflow_id == "planning_constraints":
        return ["site", "layer", "source", "operation", "status", "reviewReason"]
    return ["recordId", "uprn", "address", "postcode", "confidenceBand", "reviewReason"]


def _caveats(workflow_id: str) -> list[str]:
    shared = [
        "Do not treat unresolved rows as negative evidence.",
        (
            "Human review is required before outputs influence emergency, planning "
            "or support decisions."
        ),
    ]
    if workflow_id == "incident_impact":
        return [
            "Point-in-polygon results depend on the quality of supplied coordinates.",
            (
                "Household vulnerability attributes may be sensitive or synthetic "
                "and require access controls."
            ),
            *shared,
        ]
    if workflow_id == "planning_constraints":
        return [
            "Planning.data and local-plan layers must be checked for freshness and coverage.",
            "Constraint intersections are decision-support evidence, not a planning decision.",
            *shared,
        ]
    return [
        (
            "UPRNs are only confirmed where supplied or resolved upstream; this tool "
            "does not invent them."
        ),
        (
            "Duplicate rows can represent either repeated source records or multiple "
            "households at one premises."
        ),
        *shared,
    ]


def _descriptor(payload: dict[str, Any]) -> ToolResult:
    workflow_id = payload.get("workflowId")
    if workflow_id is not None and not isinstance(workflow_id, str):
        return _invalid("workflowId must be a string when provided")
    if workflow_id:
        workflow = _WORKFLOWS.get(workflow_id)
        if workflow is None:
            return _invalid(f"Unknown workflowId '{workflow_id}'")
        return 200, {"workflowId": workflow_id, "version": WORKFLOW_VERSION, **workflow}
    return 200, {
        "version": WORKFLOW_VERSION,
        "workflows": [
            {"workflowId": key, **value}
            for key, value in sorted(_WORKFLOWS.items(), key=lambda item: item[0])
        ],
    }


def _query(payload: dict[str, Any]) -> ToolResult:
    workflow_id = payload.get("workflowId")
    if not isinstance(workflow_id, str) or not workflow_id.strip():
        return _invalid("workflowId must be a non-empty string")
    workflow_id = workflow_id.strip()
    if workflow_id == "batch_address_match":
        return _run_batch_address_match(payload)
    if workflow_id == "incident_impact":
        return _run_incident_impact(payload)
    if workflow_id == "planning_constraints":
        return _run_planning_constraints(payload)
    return _invalid(f"Unknown workflowId '{workflow_id}'")


register(
    Tool(
        name="os_workflows.descriptor",
        description="Describe native MCP-Geo stakeholder and PoC workflow contracts.",
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "os_workflows.descriptor"},
                "workflowId": {"type": "string"},
            },
            "required": [],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "version": {"type": "string"},
                "workflowId": {"type": "string"},
                "workflows": {"type": "array"},
            },
            "additionalProperties": True,
        },
        handler=_descriptor,
    )
)

register(
    Tool(
        name="os_workflows.query",
        description=(
            "Run native MCP-Geo workflow contracts for batch address matching, "
            "incident impact review, and planning constraints."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "os_workflows.query"},
                "workflowId": {
                    "type": "string",
                    "enum": [
                        "batch_address_match",
                        "incident_impact",
                        "planning_constraints",
                    ],
                },
                "records": {"type": "array", "items": {"type": "object"}},
                "fieldMap": {"type": "object", "additionalProperties": {"type": "string"}},
                "resolveAddresses": {"type": "boolean"},
                "candidateLimit": {"type": "integer", "minimum": 1, "maximum": 25},
                "geometryWkt": {"type": "string"},
                "site": {"type": "string"},
                "siteGeometryWkt": {"type": "string"},
                "bbox": {
                    "type": "array",
                    "items": {"type": "number"},
                    "minItems": 4,
                    "maxItems": 4,
                },
                "layers": {"type": "array"},
            },
            "required": ["workflowId"],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "workflowId": {"type": "string"},
                "version": {"type": "string"},
                "title": {"type": "string"},
                "productSurfaceReady": {"type": "boolean"},
                "answerStatus": {"type": "string"},
                "summary": {"type": "string"},
                "method": {"type": "array"},
                "datasetsToolsUsed": {"type": "array"},
                "results": {"type": "object"},
                "reviewQueue": {"type": "array"},
                "export": {"type": "object"},
                "confidenceCaveats": {"type": "array"},
                "nextActions": {"type": "array"},
                "provenance": {"type": "object"},
            },
            "required": [
                "workflowId",
                "productSurfaceReady",
                "answerStatus",
                "summary",
                "results",
            ],
            "additionalProperties": True,
        },
        handler=_query,
    )
)
