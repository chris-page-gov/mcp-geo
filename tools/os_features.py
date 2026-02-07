from __future__ import annotations

from typing import Any

from tools.os_common import client
from tools.registry import Tool, ToolResult, register

_DEFAULT_LIMIT = 100
_MAX_LIMIT = 500


def _parse_bbox(value: Any) -> tuple[float, float, float, float] | None:
    if not (isinstance(value, list) and len(value) == 4):
        return None
    try:
        min_lon, min_lat, max_lon, max_lat = [float(x) for x in value]
    except (TypeError, ValueError):
        return None
    return min_lon, min_lat, max_lon, max_lat


def _parse_limit(value: Any) -> int | None:
    if value is None:
        return _DEFAULT_LIMIT
    if not isinstance(value, int):
        return None
    if value < 1 or value > _MAX_LIMIT:
        return None
    return value


def _parse_offset(value: Any) -> int | None:
    if value is None:
        return 0
    if isinstance(value, int):
        if value < 0:
            return None
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return 0
        try:
            parsed = int(text)
        except ValueError:
            return None
        if parsed < 0:
            return None
        return parsed
    return None


def _features_query(payload: dict[str, Any]) -> ToolResult:
    """Query OS NGD features within a bbox for a given collection id.

    Uses OS NGD OGC API Features:
      GET {base}/collections/{collectionId}/items?bbox=minLon,minLat,maxLon,maxLat
    """
    collection = str(payload.get("collection", "")).strip()
    if not collection:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "Missing collection"}

    bbox = _parse_bbox(payload.get("bbox"))
    if bbox is None:
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "bbox must be [minLon,minLat,maxLon,maxLat] with numeric values",
        }
    min_lon, min_lat, max_lon, max_lat = bbox

    limit = _parse_limit(payload.get("limit"))
    if limit is None:
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": f"limit must be an integer between 1 and {_MAX_LIMIT}",
        }

    offset = _parse_offset(payload.get("pageToken") or payload.get("offset"))
    if offset is None:
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "pageToken/offset must be a non-negative integer",
        }

    params: dict[str, Any] = {
        "bbox": f"{min_lon},{min_lat},{max_lon},{max_lat}",
        "limit": limit,
    }
    if offset:
        params["offset"] = offset

    url = f"{client.base_ngd_features}/collections/{collection}/items"
    status, body = client.get_json(url, params)
    if status != 200:
        return 501, body
    if not isinstance(body, dict):
        return 500, {
            "isError": True,
            "code": "INTEGRATION_ERROR",
            "message": "Expected JSON object response from OS NGD features API",
        }

    raw_features = body.get("features", [])
    if not isinstance(raw_features, list):
        raw_features = []

    features_out: list[dict[str, Any]] = []
    for feat in raw_features:
        if not isinstance(feat, dict):
            continue
        geometry = feat.get("geometry")
        geometry_type = None
        if isinstance(geometry, dict):
            geometry_type = geometry.get("type")
        features_out.append({
            "id": feat.get("id"),
            "geometry_type": geometry_type,
            "properties": feat.get("properties", {}),
        })

    number_matched = body.get("numberMatched")
    if not isinstance(number_matched, int):
        number_matched = None

    next_token: str | None = None
    if number_matched is not None:
        if offset + limit < number_matched:
            next_token = str(offset + limit)
    else:
        # Best-effort: if we got a full page, assume there may be more.
        if len(features_out) == limit:
            next_token = str(offset + limit)

    return 200, {
        "collection": collection,
        "bbox": [min_lon, min_lat, max_lon, max_lat],
        "features": features_out,
        "count": len(features_out),
        "limit": limit,
        "offset": offset,
        "nextPageToken": next_token,
        "live": True,
        "hints": [
            "This uses OS NGD OGC API Features (collections/{collection}/items).",
            "Use pageToken (offset) + limit for paging.",
        ],
    }


register(
    Tool(
        name="os_features.query",
        description="Query OS NGD features by collection and bbox (OGC API Features).",
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "os_features.query"},
                "collection": {"type": "string", "description": "NGD collection id"},
                "bbox": {
                    "type": "array",
                    "items": {"type": "number"},
                    "minItems": 4,
                    "maxItems": 4,
                    "description": "WGS84 bbox [minLon,minLat,maxLon,maxLat]",
                },
                "limit": {"type": "integer", "minimum": 1, "maximum": _MAX_LIMIT},
                "pageToken": {
                    "type": ["string", "integer", "null"],
                    "description": "Offset for paging (use nextPageToken from the previous response).",
                },
            },
            "required": ["collection", "bbox"],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "collection": {"type": "string"},
                "bbox": {"type": "array", "items": {"type": "number"}},
                "features": {"type": "array"},
                "count": {"type": "integer"},
                "limit": {"type": "integer"},
                "offset": {"type": "integer"},
                "nextPageToken": {"type": ["string", "null"]},
            },
            "required": ["features", "count"],
            "additionalProperties": True,
        },
        handler=_features_query,
    )
)

