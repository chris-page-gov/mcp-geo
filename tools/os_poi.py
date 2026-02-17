from __future__ import annotations

from typing import Any

from tools.os_common import client
from tools.registry import Tool, ToolResult, register

MAX_LIMIT = 100
DEFAULT_LIMIT = 20
# OS Places no longer accepts "POI" for dataset; use supported address datasets.
PLACES_DATASET = "DPA,LPI"


def _invalid(message: str) -> ToolResult:
    return 400, {"isError": True, "code": "INVALID_INPUT", "message": message}


def _parse_limit(value: Any) -> int | None:
    if value is None:
        return DEFAULT_LIMIT
    try:
        limit = int(value)
    except Exception:
        return None
    if limit < 1 or limit > MAX_LIMIT:
        return None
    return limit


def _parse_bbox(value: Any) -> list[float] | None:
    if not (isinstance(value, list) and len(value) == 4):
        return None
    try:
        bbox = [float(part) for part in value]
    except Exception:
        return None
    min_lon, min_lat, max_lon, max_lat = bbox
    if min_lon >= max_lon or min_lat >= max_lat:
        return None
    return bbox


def _float_or_none(value: Any) -> float | None:
    try:
        return float(value)
    except Exception:
        return None


def _text_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _extract_source_entry(row: dict[str, Any]) -> dict[str, Any] | None:
    if not isinstance(row, dict):
        return None
    for key in ("POI", "DPA", "LPI", "GAZETTEER_ENTRY"):
        value = row.get(key)
        if isinstance(value, dict):
            return value
    return row


def _normalize_results(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = payload.get("results")
    if not isinstance(rows, list):
        return []
    normalized: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        entry = _extract_source_entry(row)
        if not isinstance(entry, dict):
            continue
        name = (
            entry.get("NAME")
            or entry.get("NAME1")
            or entry.get("ORGANISATION_NAME")
            or entry.get("ADDRESS")
            or entry.get("DESCRIPTION")
        )
        category = (
            entry.get("CLASSIFICATION")
            or entry.get("CLASSIFICATION_CODE")
            or entry.get("CLASS_DESCRIPTION")
            or entry.get("LOCAL_TYPE")
            or entry.get("TYPE")
        )
        address = entry.get("ADDRESS") or entry.get("DESCRIPTION")
        item: dict[str, Any] = {
            "name": _text_or_none(name),
            "category": _text_or_none(category),
            "address": _text_or_none(address),
            "lat": _float_or_none(entry.get("LAT")),
            "lon": _float_or_none(entry.get("LNG")),
            "id": _text_or_none(entry.get("ID") or entry.get("UPRN")),
        }
        distance = row.get("DISTANCE")
        distance_num = _float_or_none(distance)
        if distance_num is not None:
            item["distanceMeters"] = distance_num
        normalized.append(item)
    return normalized


def _search(payload: dict[str, Any]) -> ToolResult:
    text = str(payload.get("text", "")).strip()
    if not text:
        return _invalid("Missing text query")
    limit = _parse_limit(payload.get("limit"))
    if limit is None:
        return _invalid(f"limit must be an integer between 1 and {MAX_LIMIT}")

    params: dict[str, Any] = {
        "query": text,
        "dataset": PLACES_DATASET,
        "output_srs": "WGS84",
        "maxresults": limit,
    }
    bbox = payload.get("bbox")
    if bbox is not None:
        parsed_bbox = _parse_bbox(bbox)
        if parsed_bbox is None:
            return _invalid("bbox must be [minLon,minLat,maxLon,maxLat] with numeric values")
        min_lon, min_lat, max_lon, max_lat = parsed_bbox
        params["bbox"] = f"{min_lat},{min_lon},{max_lat},{max_lon}"
        params["srs"] = "WGS84"

    status, raw = client.get_json(f"{client.base_places}/find", params)
    if status != 200:
        return 501, raw
    results = _normalize_results(raw)
    return 200, {
        "results": results,
        "count": len(results),
        "provenance": {"source": "os_poi", "dataset": PLACES_DATASET},
    }


def _nearest(payload: dict[str, Any]) -> ToolResult:
    try:
        lat = float(payload.get("lat"))
        lon = float(payload.get("lon"))
    except Exception:
        return _invalid("lat and lon must be numeric")
    limit = _parse_limit(payload.get("limit"))
    if limit is None:
        return _invalid(f"limit must be an integer between 1 and {MAX_LIMIT}")

    params: dict[str, Any] = {
        "point": f"{lat},{lon}",
        "srs": "WGS84",
        "output_srs": "WGS84",
        "dataset": PLACES_DATASET,
        "maxresults": limit,
    }
    max_distance = payload.get("maxDistanceMeters")
    if max_distance is not None:
        try:
            params["radius"] = int(max_distance)
        except Exception:
            return _invalid("maxDistanceMeters must be an integer when provided")

    status, raw = client.get_json(f"{client.base_places}/nearest", params)
    if status != 200:
        return 501, raw
    results = _normalize_results(raw)
    return 200, {
        "results": results,
        "count": len(results),
        "provenance": {"source": "os_poi", "dataset": PLACES_DATASET},
    }


def _within(payload: dict[str, Any]) -> ToolResult:
    parsed_bbox = _parse_bbox(payload.get("bbox"))
    if parsed_bbox is None:
        return _invalid("bbox must be [minLon,minLat,maxLon,maxLat] with numeric values")
    limit = _parse_limit(payload.get("limit"))
    if limit is None:
        return _invalid(f"limit must be an integer between 1 and {MAX_LIMIT}")
    min_lon, min_lat, max_lon, max_lat = parsed_bbox

    params: dict[str, Any] = {
        "bbox": f"{min_lat},{min_lon},{max_lat},{max_lon}",
        "srs": "WGS84",
        "output_srs": "WGS84",
        "dataset": PLACES_DATASET,
        "maxresults": limit,
    }
    status, raw = client.get_json(f"{client.base_places}/bbox", params)
    if status != 200:
        return 501, raw
    results = _normalize_results(raw)
    return 200, {
        "results": results,
        "count": len(results),
        "provenance": {"source": "os_poi", "dataset": PLACES_DATASET},
    }


_POI_ITEM_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "id": {"type": ["string", "null"]},
        "name": {"type": ["string", "null"]},
        "category": {"type": ["string", "null"]},
        "address": {"type": ["string", "null"]},
        "lat": {"type": ["number", "null"]},
        "lon": {"type": ["number", "null"]},
        "distanceMeters": {"type": "number"},
    },
    "required": ["name", "address", "lat", "lon"],
    "additionalProperties": True,
}


register(
    Tool(
        name="os_poi.search",
        description="Search OS Points of Interest by text, with optional bbox filtering.",
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "os_poi.search"},
                "text": {"type": "string", "description": "POI search text"},
                "limit": {"type": "integer", "minimum": 1, "maximum": MAX_LIMIT},
                "bbox": {
                    "type": "array",
                    "items": {"type": "number"},
                    "minItems": 4,
                    "maxItems": 4,
                    "description": "[minLon,minLat,maxLon,maxLat]",
                },
            },
            "required": ["text"],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "results": {"type": "array", "items": _POI_ITEM_SCHEMA},
                "count": {"type": "integer"},
                "provenance": {"type": "object"},
            },
            "required": ["results", "count"],
            "additionalProperties": True,
        },
        handler=_search,
    )
)


register(
    Tool(
        name="os_poi.nearest",
        description="Find nearby OS Points of Interest for a latitude/longitude point.",
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "os_poi.nearest"},
                "lat": {"type": "number"},
                "lon": {"type": "number"},
                "limit": {"type": "integer", "minimum": 1, "maximum": MAX_LIMIT},
                "maxDistanceMeters": {"type": "integer", "minimum": 1},
            },
            "required": ["lat", "lon"],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "results": {"type": "array", "items": _POI_ITEM_SCHEMA},
                "count": {"type": "integer"},
                "provenance": {"type": "object"},
            },
            "required": ["results", "count"],
            "additionalProperties": True,
        },
        handler=_nearest,
    )
)


register(
    Tool(
        name="os_poi.within",
        description="Find OS Points of Interest within a WGS84 bounding box.",
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "os_poi.within"},
                "bbox": {
                    "type": "array",
                    "items": {"type": "number"},
                    "minItems": 4,
                    "maxItems": 4,
                    "description": "[minLon,minLat,maxLon,maxLat]",
                },
                "limit": {"type": "integer", "minimum": 1, "maximum": MAX_LIMIT},
            },
            "required": ["bbox"],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "results": {"type": "array", "items": _POI_ITEM_SCHEMA},
                "count": {"type": "integer"},
                "provenance": {"type": "object"},
            },
            "required": ["results", "count"],
            "additionalProperties": True,
        },
        handler=_within,
    )
)
