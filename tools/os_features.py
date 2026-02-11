from __future__ import annotations

import re
from typing import Any

from tools.os_common import client
from tools.registry import Tool, ToolResult, register

_DEFAULT_LIMIT = 100
_MAX_LIMIT = 500

_COLLECTION_VERSION_RE = re.compile(r"^(?P<base>.+)-(?P<ver>[0-9]+)$")


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


def _parse_str_list(value: Any, *, field: str) -> list[str] | None:
    if value is None:
        return []
    if not isinstance(value, list):
        return None
    cleaned: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            return None
        cleaned.append(item.strip())
    return cleaned


def _parse_sort_by(value: Any) -> list[tuple[str, bool]] | None:
    if value is None:
        return []
    items: list[str]
    if isinstance(value, str):
        items = [item.strip() for item in value.split(",") if item.strip()]
    elif isinstance(value, list):
        if not all(isinstance(item, str) for item in value):
            return None
        items = [str(item).strip() for item in value if str(item).strip()]
    else:
        return None
    parsed: list[tuple[str, bool]] = []
    for item in items:
        descending = item.startswith("-")
        field = item[1:] if descending else item
        if not field:
            return None
        parsed.append((field, descending))
    return parsed


def _parse_polygon(value: Any) -> list[tuple[float, float]] | None:
    points_raw: Any = None
    if isinstance(value, dict):
        if str(value.get("type", "")).lower() != "polygon":
            return None
        coords = value.get("coordinates")
        if (
            isinstance(coords, list)
            and coords
            and isinstance(coords[0], list)
            and coords[0]
        ):
            points_raw = coords[0]
    elif isinstance(value, list):
        points_raw = value
    if not isinstance(points_raw, list):
        return None
    points: list[tuple[float, float]] = []
    for point in points_raw:
        if not (isinstance(point, list) and len(point) >= 2):
            return None
        try:
            lon = float(point[0])
            lat = float(point[1])
        except (TypeError, ValueError):
            return None
        points.append((lon, lat))
    if len(points) < 4:
        return None
    if points[0] != points[-1]:
        points.append(points[0])
    return points


def _bbox_from_polygon(points: list[tuple[float, float]]) -> tuple[float, float, float, float]:
    lons = [point[0] for point in points]
    lats = [point[1] for point in points]
    return min(lons), min(lats), max(lons), max(lats)


def _point_in_polygon(point: tuple[float, float], polygon: list[tuple[float, float]]) -> bool:
    x, y = point
    inside = False
    n = len(polygon)
    for i in range(n - 1):
        x1, y1 = polygon[i]
        x2, y2 = polygon[i + 1]
        intersects = ((y1 > y) != (y2 > y)) and (
            x < (x2 - x1) * (y - y1) / ((y2 - y1) or 1e-12) + x1
        )
        if intersects:
            inside = not inside
    return inside


def _feature_intersects_polygon(feature: dict[str, Any], polygon: list[tuple[float, float]]) -> bool:
    geometry = feature.get("geometry")
    if not isinstance(geometry, dict):
        return False
    geom_type = str(geometry.get("type") or "").lower()
    coords = geometry.get("coordinates")
    if geom_type == "point" and isinstance(coords, list) and len(coords) >= 2:
        try:
            return _point_in_polygon((float(coords[0]), float(coords[1])), polygon)
        except (TypeError, ValueError):
            return False
    if not isinstance(coords, list):
        return False

    def _iter_points(value: Any):
        if isinstance(value, list):
            if len(value) >= 2 and all(isinstance(v, (int, float)) for v in value[:2]):
                yield float(value[0]), float(value[1])
            else:
                for child in value:
                    yield from _iter_points(child)

    for point in _iter_points(coords):
        if _point_in_polygon(point, polygon):
            return True
    return False


def _coerce_number(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _match_filter_value(prop_value: Any, condition: Any) -> bool:
    if isinstance(condition, dict):
        for op, expected in condition.items():
            if op == "eq" and prop_value != expected:
                return False
            if op == "ne" and prop_value == expected:
                return False
            if op in {"gt", "gte", "lt", "lte"}:
                left = _coerce_number(prop_value)
                right = _coerce_number(expected)
                if left is None or right is None:
                    return False
                if op == "gt" and not (left > right):
                    return False
                if op == "gte" and not (left >= right):
                    return False
                if op == "lt" and not (left < right):
                    return False
                if op == "lte" and not (left <= right):
                    return False
            if op == "in":
                if not isinstance(expected, list) or prop_value not in expected:
                    return False
            if op == "contains":
                if isinstance(prop_value, str) and isinstance(expected, str):
                    if expected.lower() not in prop_value.lower():
                        return False
                elif isinstance(prop_value, list):
                    if expected not in prop_value:
                        return False
                else:
                    return False
        return True
    return prop_value == condition


def _feature_matches_filter(feature: dict[str, Any], filter_spec: dict[str, Any]) -> bool:
    properties = feature.get("properties")
    if not isinstance(properties, dict):
        return False
    for field, condition in filter_spec.items():
        if field not in properties:
            return False
        if not _match_filter_value(properties.get(field), condition):
            return False
    return True


def _project_properties(
    properties: Any,
    include_fields: list[str],
    exclude_fields: list[str],
) -> dict[str, Any]:
    if not isinstance(properties, dict):
        return {}
    projected = dict(properties)
    if include_fields:
        projected = {key: value for key, value in projected.items() if key in include_fields}
    if exclude_fields:
        for field in exclude_fields:
            projected.pop(field, None)
    return projected


def _features_query(payload: dict[str, Any]) -> ToolResult:
    """Query OS NGD features within a bbox for a given collection id.

    Uses OS NGD OGC API Features:
      GET {base}/collections/{collectionId}/items?bbox=minLon,minLat,maxLon,maxLat
    """
    collection = str(payload.get("collection", "")).strip()
    if not collection:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "Missing collection"}

    include_geometry = bool(payload.get("includeGeometry"))
    polygon = _parse_polygon(payload.get("polygon"))
    bbox = _parse_bbox(payload.get("bbox"))
    if bbox is None and polygon is not None:
        bbox = _bbox_from_polygon(polygon)
    if bbox is None:
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": (
                "Provide bbox=[minLon,minLat,maxLon,maxLat] or a valid polygon "
                "(GeoJSON Polygon or coordinate ring)."
            ),
        }
    min_lon, min_lat, max_lon, max_lat = bbox

    filter_spec = payload.get("filter")
    if filter_spec is not None and not isinstance(filter_spec, dict):
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "filter must be an object when provided",
        }
    include_fields = _parse_str_list(payload.get("includeFields"), field="includeFields")
    if include_fields is None:
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "includeFields must be a list of non-empty strings",
        }
    exclude_fields = _parse_str_list(payload.get("excludeFields"), field="excludeFields")
    if exclude_fields is None:
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "excludeFields must be a list of non-empty strings",
        }
    sort_by = _parse_sort_by(payload.get("sortBy"))
    if sort_by is None:
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "sortBy must be a string or list of strings",
        }
    result_type = payload.get("resultType")
    if result_type is not None and result_type not in {"hits", "results"}:
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "resultType must be 'results' (default) or 'hits'",
        }
    if result_type is None:
        result_type = "results"
    include_queryables = bool(payload.get("includeQueryables"))
    cql_text = payload.get("cql") or payload.get("filterText")
    if cql_text is not None and (not isinstance(cql_text, str) or not cql_text.strip()):
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "cql/filterText must be a non-empty string when provided",
        }

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
    if isinstance(cql_text, str) and cql_text.strip():
        params["filter"] = cql_text.strip()
    queryables: dict[str, Any] | None = None

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

    filtered_features: list[dict[str, Any]] = []
    for feat in raw_features:
        if not isinstance(feat, dict):
            continue
        if polygon is not None and not _feature_intersects_polygon(feat, polygon):
            continue
        if isinstance(filter_spec, dict) and not _feature_matches_filter(feat, filter_spec):
            continue
        filtered_features.append(feat)

    if sort_by:
        for field, descending in reversed(sort_by):
            filtered_features.sort(
                key=lambda feature: (
                    (feature.get("properties") or {}).get(field)
                    if field != "id"
                    else feature.get("id")
                ),
                reverse=descending,
            )

    filtered_count = len(filtered_features)
    if result_type == "hits":
        features_out: list[dict[str, Any]] = []
    else:
        features_out = []
        for feat in filtered_features:
            if not isinstance(feat, dict):
                continue
            geometry = feat.get("geometry")
            geometry_type = None
            if isinstance(geometry, dict):
                geometry_type = geometry.get("type")
            out_item: dict[str, Any] = {
                "id": feat.get("id"),
                "geometry_type": geometry_type,
                "properties": _project_properties(
                    feat.get("properties"),
                    include_fields or [],
                    exclude_fields or [],
                ),
            }
            if include_geometry and isinstance(geometry, dict):
                out_item["geometry"] = geometry
            features_out.append(out_item)

    if include_queryables:
        queryables_url = f"{client.base_ngd_features}/collections/{collection}/queryables"
        queryables_status, queryables_body = client.get_json(queryables_url, None)
        if queryables_status == 200 and isinstance(queryables_body, dict):
            queryables = queryables_body
        else:
            queryables = {
                "isError": True,
                "status": queryables_status,
                "message": "Queryables metadata unavailable for this collection.",
            }

    number_matched = body.get("numberMatched")
    if not isinstance(number_matched, int):
        number_matched = None
    number_returned = body.get("numberReturned")
    if not isinstance(number_returned, int):
        number_returned = None
    if polygon is not None or isinstance(filter_spec, dict):
        number_matched = filtered_count
    if result_type == "hits":
        number_returned = 0
    elif number_returned is None:
        number_returned = len(features_out)

    next_token: str | None = None
    if result_type == "results":
        if number_matched is not None:
            if offset + limit < number_matched:
                next_token = str(offset + limit)
        else:
            if len(filtered_features) == limit:
                next_token = str(offset + limit)

    response: dict[str, Any] = {
        "collection": collection,
        "bbox": [min_lon, min_lat, max_lon, max_lat],
        "features": features_out,
        "count": filtered_count if result_type == "hits" else len(features_out),
        "numberMatched": number_matched,
        "numberReturned": number_returned,
        "limit": limit,
        "offset": offset,
        "nextPageToken": next_token,
        "live": True,
        "hints": [
            "This uses OS NGD OGC API Features (collections/{collection}/items).",
            "Use pageToken (offset) + limit for paging.",
            "Pass includeGeometry=true to include GeoJSON geometry in each feature (larger payloads).",
            "Pass polygon/filter/sortBy/includeFields/excludeFields for local post-filtering.",
            "Set resultType='hits' for count-only responses.",
        ],
    }
    if polygon is not None:
        response["polygon"] = [[lon, lat] for lon, lat in polygon]
    if isinstance(filter_spec, dict):
        response["filter"] = filter_spec
    if sort_by:
        response["sortBy"] = [
            f"-{field}" if descending else field for field, descending in sort_by
        ]
    if include_fields:
        response["includeFields"] = include_fields
    if exclude_fields:
        response["excludeFields"] = exclude_fields
    if result_type == "hits":
        response["resultType"] = "hits"
    if include_queryables:
        response["queryables"] = queryables

    return 200, response


register(
    Tool(
        name="os_features.query",
        description=(
            "Query OS NGD features by collection using bbox or polygon constraints, "
            "with optional filter/projection/sort/queryables support."
        ),
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
                "polygon": {
                    "description": "Polygon ring coordinates or GeoJSON Polygon object.",
                },
                "limit": {"type": "integer", "minimum": 1, "maximum": _MAX_LIMIT},
                "pageToken": {
                    "type": ["string", "integer", "null"],
                    "description": "Offset for paging (use nextPageToken from the previous response).",
                },
                "includeGeometry": {
                    "type": "boolean",
                    "description": "When true, include GeoJSON geometry per feature (larger payloads).",
                    "default": False,
                },
                "filter": {"type": "object", "description": "Property filter object."},
                "cql": {"type": "string", "description": "Pass-through CQL filter text."},
                "filterText": {"type": "string", "description": "Alias for cql text."},
                "includeFields": {"type": "array", "items": {"type": "string"}},
                "excludeFields": {"type": "array", "items": {"type": "string"}},
                "sortBy": {
                    "description": "Sort fields (for example 'name,-height').",
                },
                "resultType": {
                    "type": "string",
                    "enum": ["results", "hits"],
                    "description": "Use 'hits' for count-only responses.",
                },
                "includeQueryables": {
                    "type": "boolean",
                    "description": "Include collection queryables metadata.",
                },
            },
            "required": ["collection"],
            "additionalProperties": False,
            "anyOf": [{"required": ["bbox"]}, {"required": ["polygon"]}],
        },
        output_schema={
            "type": "object",
            "properties": {
                "collection": {"type": "string"},
                "bbox": {"type": "array", "items": {"type": "number"}},
                "polygon": {"type": "array"},
                "features": {"type": "array"},
                "count": {"type": "integer"},
                "numberMatched": {"type": ["integer", "null"]},
                "numberReturned": {"type": ["integer", "null"]},
                "limit": {"type": "integer"},
                "offset": {"type": "integer"},
                "nextPageToken": {"type": ["string", "null"]},
                "queryables": {"type": ["object", "null"]},
                "resultType": {"type": "string"},
            },
            "required": ["features", "count"],
            "additionalProperties": True,
        },
        handler=_features_query,
    )
)


def _features_collections(payload: dict[str, Any]) -> ToolResult:
    """List OS NGD OGC API Features collections (id/title/description) + latest version mapping."""
    status, body = client.get_json(f"{client.base_ngd_features}/collections", None)
    if status != 200:
        return 501, body
    if not isinstance(body, dict):
        return 500, {
            "isError": True,
            "code": "INTEGRATION_ERROR",
            "message": "Expected JSON object response from OS NGD features collections endpoint",
        }
    raw = body.get("collections", [])
    if not isinstance(raw, list):
        raw = []

    q = payload.get("q") or payload.get("query")
    q_norm = str(q).strip().lower() if isinstance(q, str) else ""

    collections: list[dict[str, Any]] = []
    latest_by_base: dict[str, str] = {}
    latest_versions: dict[str, int] = {}

    for item in raw:
        if not isinstance(item, dict):
            continue
        coll_id = item.get("id")
        if not isinstance(coll_id, str) or not coll_id.strip():
            continue
        coll_id = coll_id.strip()
        title = item.get("title")
        desc = item.get("description")
        record = {
            "id": coll_id,
            "title": title if isinstance(title, str) else "",
            "description": desc if isinstance(desc, str) else "",
        }
        if q_norm:
            hay = f"{record['id']} {record['title']} {record['description']}".lower()
            if q_norm not in hay:
                continue
        collections.append(record)

        m = _COLLECTION_VERSION_RE.match(coll_id)
        if not m:
            continue
        base = m.group("base")
        try:
            ver = int(m.group("ver"))
        except ValueError:
            continue
        prev = latest_versions.get(base, -1)
        if ver > prev:
            latest_versions[base] = ver
            latest_by_base[base] = coll_id

    collections.sort(key=lambda x: x.get("id", ""))
    return 200, {
        "count": len(collections),
        "collections": collections,
        "latestByBaseId": latest_by_base,
        "live": True,
        "hints": [
            "Use latestByBaseId to pick the newest collection version (highest numeric suffix).",
            "Pass q to filter by substring match in id/title/description.",
        ],
    }


register(
    Tool(
        name="os_features.collections",
        description="List OS NGD OGC API Features collections (and a latest-by-base mapping).",
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "os_features.collections"},
                "q": {"type": "string", "description": "Optional substring filter."},
            },
            "required": [],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "count": {"type": "integer"},
                "collections": {"type": "array"},
                "latestByBaseId": {"type": "object"},
            },
            "required": ["collections", "latestByBaseId"],
            "additionalProperties": True,
        },
        handler=_features_collections,
    )
)
