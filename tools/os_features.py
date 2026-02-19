from __future__ import annotations

import math
import re
from typing import Any

from server.config import settings
from tools.os_common import add_warning, client, features_request_policy
from tools.os_delivery import (
    parse_delivery,
    parse_inline_max_bytes,
    payload_bytes,
    select_delivery_mode,
    write_resource_payload,
)
from tools.registry import Tool, ToolResult, register


def _int_setting(value: Any, default: int, *, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    if parsed < minimum:
        return minimum
    if parsed > maximum:
        return maximum
    return parsed


def _float_setting(value: Any, default: float, *, minimum: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    if parsed < minimum:
        return minimum
    return parsed


_MAX_LIMIT = _int_setting(
    getattr(settings, "OS_FEATURES_MAX_LIMIT", 100),
    100,
    minimum=1,
    maximum=1000,
)
_DEFAULT_LIMIT = _int_setting(
    getattr(settings, "OS_FEATURES_DEFAULT_LIMIT", 50),
    50,
    minimum=1,
    maximum=_MAX_LIMIT,
)
_DEFAULT_INCLUDE_GEOMETRY = bool(
    getattr(settings, "OS_FEATURES_DEFAULT_INCLUDE_GEOMETRY", False)
)
_DEFAULT_THIN_MODE = bool(getattr(settings, "OS_FEATURES_THIN_DEFAULT", True))
_THIN_PROPERTY_LIMIT = _int_setting(
    getattr(settings, "OS_FEATURES_THIN_PROPERTY_LIMIT", 8),
    8,
    minimum=1,
    maximum=64,
)
_DEFAULT_SCAN_PAGE_BUDGET = _int_setting(
    getattr(settings, "OS_FEATURES_LOCAL_SCAN_PAGE_BUDGET", 1),
    1,
    minimum=1,
    maximum=10,
)
_MAX_POLYGON_VERTICES = _int_setting(
    getattr(settings, "OS_FEATURES_MAX_POLYGON_VERTICES", 2000),
    2000,
    minimum=4,
    maximum=50000,
)
_MAX_BBOX_AREA_DEG2 = _float_setting(
    getattr(settings, "OS_FEATURES_MAX_BBOX_AREA_DEG2", 4.0),
    4.0,
    minimum=0.01,
)

_COLLECTION_VERSION_RE = re.compile(r"^(?P<base>.+)-(?P<ver>[0-9]+)$")

_HINT_MESSAGES = [
    "This uses OS NGD OGC API Features (collections/{collection}/items).",
    "Use pageToken (offset) + limit for paging.",
    "Pass includeGeometry=true only when geometry is explicitly required.",
    "Pass polygon/filter/sortBy/includeFields/excludeFields for local post-filtering.",
    "Set resultType='hits' for count-only responses.",
]


def _parse_bbox(value: Any) -> tuple[float, float, float, float] | None:
    if not (isinstance(value, list) and len(value) == 4):
        return None
    try:
        min_lon, min_lat, max_lon, max_lat = [float(x) for x in value]
    except (TypeError, ValueError):
        return None
    if not (-180.0 <= min_lon <= 180.0 and -180.0 <= max_lon <= 180.0):
        return None
    if not (-90.0 <= min_lat <= 90.0 and -90.0 <= max_lat <= 90.0):
        return None
    if min_lon >= max_lon or min_lat >= max_lat:
        return None
    return min_lon, min_lat, max_lon, max_lat


def _bbox_area(bbox: tuple[float, float, float, float]) -> float:
    min_lon, min_lat, max_lon, max_lat = bbox
    return (max_lon - min_lon) * (max_lat - min_lat)


def _shrink_bbox(
    bbox: tuple[float, float, float, float],
    *,
    factor: float,
) -> tuple[float, float, float, float]:
    min_lon, min_lat, max_lon, max_lat = bbox
    center_lon = (min_lon + max_lon) / 2.0
    center_lat = (min_lat + max_lat) / 2.0
    half_width = ((max_lon - min_lon) * factor) / 2.0
    half_height = ((max_lat - min_lat) * factor) / 2.0
    return (
        center_lon - half_width,
        center_lat - half_height,
        center_lon + half_width,
        center_lat + half_height,
    )


def _clamp_bbox_area(
    bbox: tuple[float, float, float, float],
    *,
    warnings: list[str],
    allow_large_bbox: bool,
) -> tuple[float, float, float, float]:
    if allow_large_bbox:
        return bbox
    area = _bbox_area(bbox)
    if area <= _MAX_BBOX_AREA_DEG2:
        return bbox
    add_warning(warnings, "BBOX_AREA_CLAMPED")
    ratio = _MAX_BBOX_AREA_DEG2 / area
    factor = math.sqrt(max(0.0, min(1.0, ratio)))
    return _shrink_bbox(bbox, factor=factor)


def _bbox_to_param(bbox: tuple[float, float, float, float]) -> str:
    min_lon, min_lat, max_lon, max_lat = bbox
    return f"{min_lon},{min_lat},{max_lon},{max_lat}"


def _parse_bbox_param(value: str) -> tuple[float, float, float, float] | None:
    parts = [part.strip() for part in value.split(",")]
    if len(parts) != 4:
        return None
    try:
        raw = [float(part) for part in parts]
    except ValueError:
        return None
    return _parse_bbox(raw)


def _parse_limit(value: Any, warnings: list[str]) -> int | None:
    if value is None:
        return _DEFAULT_LIMIT
    if not isinstance(value, int) or value < 1:
        return None
    if value > _MAX_LIMIT:
        add_warning(warnings, "RESULT_LIMIT_CLAMPED")
        return _MAX_LIMIT
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


def _parse_str_list(value: Any) -> list[str] | None:
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


def _parse_polygon(
    value: Any,
) -> tuple[list[tuple[float, float]] | None, str | None]:
    if value is None:
        return None, None
    points_raw: Any
    if isinstance(value, dict):
        if str(value.get("type", "")).lower() != "polygon":
            return None, "polygon.type must be 'Polygon'"
        coords = value.get("coordinates")
        if not (
            isinstance(coords, list)
            and coords
            and isinstance(coords[0], list)
            and coords[0]
        ):
            return None, "polygon.coordinates must contain at least one ring"
        points_raw = coords[0]
    elif isinstance(value, list):
        points_raw = value
    else:
        return None, "polygon must be a coordinate ring or GeoJSON Polygon object"

    if not isinstance(points_raw, list):
        return None, "polygon ring must be a list of coordinates"
    if len(points_raw) > _MAX_POLYGON_VERTICES:
        return None, f"polygon ring exceeds max vertex count ({_MAX_POLYGON_VERTICES})"
    if len(points_raw) < 4:
        return None, "polygon ring must contain at least 4 coordinates (closed ring)"

    points: list[tuple[float, float]] = []
    for point in points_raw:
        if not (isinstance(point, list | tuple) and len(point) >= 2):
            return None, "polygon coordinates must be [lon,lat] pairs"
        try:
            lon = float(point[0])
            lat = float(point[1])
        except (TypeError, ValueError):
            return None, "polygon coordinates must be numeric [lon,lat] pairs"
        if not (-180.0 <= lon <= 180.0 and -90.0 <= lat <= 90.0):
            return None, "polygon coordinate values are out of range for WGS84"
        points.append((lon, lat))

    if points[0] != points[-1]:
        return None, "polygon ring must be closed (first coordinate must equal last)"

    unique_vertices = {vertex for vertex in points[:-1]}
    if len(unique_vertices) < 3:
        return None, "polygon ring must include at least 3 distinct vertices"
    return points, None


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
    coords = geometry.get("coordinates")
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
    *,
    thin_mode: bool,
) -> tuple[dict[str, Any], bool]:
    if not isinstance(properties, dict):
        return {}, False
    projected = dict(properties)
    trimmed = False
    if include_fields:
        projected = {key: value for key, value in projected.items() if key in include_fields}
    elif thin_mode and len(projected) > _THIN_PROPERTY_LIMIT:
        keys = sorted(projected.keys())[:_THIN_PROPERTY_LIMIT]
        projected = {key: projected[key] for key in keys}
        trimmed = True
    if exclude_fields:
        for field in exclude_fields:
            projected.pop(field, None)
    return projected, trimmed


def _upstream_has_more(
    body: dict[str, Any],
    *,
    page_size: int,
    offset: int,
    limit: int,
) -> bool:
    number_matched = body.get("numberMatched")
    if isinstance(number_matched, int):
        return offset + limit < number_matched
    return page_size >= limit and page_size > 0


def _client_get_json(
    url: str,
    params: dict[str, Any] | None,
    *,
    timeout: tuple[float, float] | None = None,
    retries: int | None = None,
) -> tuple[int, dict[str, Any]]:
    try:
        return client.get_json(url, params, timeout=timeout, retries=retries)
    except TypeError:
        return client.get_json(url, params)


def _fetch_feature_page(
    *,
    url: str,
    params: dict[str, Any],
    policy: dict[str, Any],
) -> tuple[int, dict[str, Any], list[str], bool]:
    warnings: list[str] = []
    timeout = (
        float(policy["connectTimeoutSeconds"]),
        float(policy["readTimeoutSeconds"]),
    )
    retries = int(policy["retries"])
    status, body = _client_get_json(
        url,
        params,
        timeout=timeout,
        retries=retries,
    )
    if status == 200 and isinstance(body, dict):
        return 200, body, warnings, False
    if (
        status == 501
        and isinstance(body, dict)
        and str(body.get("code", "")) == "UPSTREAM_CONNECT_ERROR"
    ):
        add_warning(warnings, "TIMEOUT_DEGRADE_APPLIED")
        degraded_params = dict(params)
        degraded_limit = min(
            int(params.get("limit", _MAX_LIMIT)),
            _int_setting(policy.get("degradedLimit"), 25, minimum=1, maximum=_MAX_LIMIT),
        )
        if degraded_limit < int(params.get("limit", degraded_limit)):
            degraded_params["limit"] = degraded_limit
            add_warning(warnings, "TIMEOUT_LIMIT_REDUCED")
        bbox_value = degraded_params.get("bbox")
        if isinstance(bbox_value, str):
            parsed_bbox = _parse_bbox_param(bbox_value)
            if parsed_bbox is not None:
                degraded_params["bbox"] = _bbox_to_param(
                    _shrink_bbox(parsed_bbox, factor=0.5)
                )
                add_warning(warnings, "TIMEOUT_BBOX_REDUCED")
        retry_status, retry_body = _client_get_json(
            url,
            degraded_params,
            timeout=timeout,
            retries=max(1, retries - 1),
        )
        if retry_status == 200 and isinstance(retry_body, dict):
            return 200, retry_body, warnings, True
        if isinstance(retry_body, dict):
            return retry_status, retry_body, warnings, True
        return 500, {
            "isError": True,
            "code": "INTEGRATION_ERROR",
            "message": "Expected JSON object response from OS NGD features API",
        }, warnings, True
    if isinstance(body, dict):
        return status, body, warnings, False
    return 500, {
        "isError": True,
        "code": "INTEGRATION_ERROR",
        "message": "Expected JSON object response from OS NGD features API",
    }, warnings, False


def _features_query(payload: dict[str, Any]) -> ToolResult:
    collection = str(payload.get("collection", "")).strip()
    if not collection:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "Missing collection"}

    warnings: list[str] = []
    include_geometry_raw = payload.get("includeGeometry")
    if include_geometry_raw is None:
        include_geometry = _DEFAULT_INCLUDE_GEOMETRY
    elif isinstance(include_geometry_raw, bool):
        include_geometry = include_geometry_raw
    else:
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "includeGeometry must be a boolean when provided",
        }

    thin_mode_raw = payload.get("thinMode")
    if thin_mode_raw is None:
        thin_mode = _DEFAULT_THIN_MODE
    elif isinstance(thin_mode_raw, bool):
        thin_mode = thin_mode_raw
    else:
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "thinMode must be a boolean when provided",
        }

    include_queryables_raw = payload.get("includeQueryables")
    if include_queryables_raw is None:
        include_queryables = False
    elif isinstance(include_queryables_raw, bool):
        include_queryables = include_queryables_raw
    else:
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "includeQueryables must be a boolean when provided",
        }

    allow_large_bbox_raw = payload.get("allowLargeBbox")
    if allow_large_bbox_raw is None:
        allow_large_bbox = False
    elif isinstance(allow_large_bbox_raw, bool):
        allow_large_bbox = allow_large_bbox_raw
    else:
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "allowLargeBbox must be a boolean when provided",
        }

    scan_page_budget_raw = payload.get("scanPageBudget")
    if scan_page_budget_raw is None:
        scan_page_budget = _DEFAULT_SCAN_PAGE_BUDGET
    elif not isinstance(scan_page_budget_raw, int):
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "scanPageBudget must be an integer between 1 and 10",
        }
    else:
        scan_page_budget = _int_setting(
            scan_page_budget_raw,
            _DEFAULT_SCAN_PAGE_BUDGET,
            minimum=1,
            maximum=10,
        )

    delivery, delivery_err = parse_delivery(payload.get("delivery"), default="auto")
    if delivery_err:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": delivery_err}
    inline_max_bytes, inline_err = parse_inline_max_bytes(payload.get("inlineMaxBytes"))
    if inline_err:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": inline_err}

    polygon, polygon_error = _parse_polygon(payload.get("polygon"))
    if polygon_error:
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": polygon_error,
        }

    bbox = _parse_bbox(payload.get("bbox"))
    if payload.get("bbox") is not None and bbox is None:
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "bbox must be [minLon,minLat,maxLon,maxLat] with valid WGS84 bounds",
        }
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
    bbox = _clamp_bbox_area(
        bbox,
        warnings=warnings,
        allow_large_bbox=allow_large_bbox,
    )

    filter_spec = payload.get("filter")
    if filter_spec is not None and not isinstance(filter_spec, dict):
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "filter must be an object when provided",
        }

    include_fields = _parse_str_list(payload.get("includeFields"))
    if include_fields is None:
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "includeFields must be a list of non-empty strings",
        }
    exclude_fields = _parse_str_list(payload.get("excludeFields"))
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
    result_type_raw = payload.get("resultType")
    if result_type_raw is None:
        result_type = "results"
    elif result_type_raw in {"hits", "results"}:
        result_type = str(result_type_raw)
    else:
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "resultType must be 'results' (default) or 'hits'",
        }

    cql_text = payload.get("cql") or payload.get("filterText")
    if cql_text is not None and (not isinstance(cql_text, str) or not cql_text.strip()):
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "cql/filterText must be a non-empty string when provided",
        }

    limit = _parse_limit(payload.get("limit"), warnings)
    if limit is None:
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": f"limit must be an integer >= 1 (max {_MAX_LIMIT})",
        }
    offset = _parse_offset(payload.get("pageToken") or payload.get("offset"))
    if offset is None:
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "pageToken/offset must be a non-negative integer",
        }

    local_filtering = polygon is not None or isinstance(filter_spec, dict)
    filter_applied = "local" if local_filtering else "none"
    if isinstance(cql_text, str) and cql_text.strip():
        if local_filtering:
            add_warning(warnings, "MIXED_FILTERING_LOCAL_POST")
        else:
            filter_applied = "upstream"

    params: dict[str, Any] = {
        "bbox": _bbox_to_param(bbox),
        "limit": limit,
    }
    if offset:
        params["offset"] = offset
    if isinstance(cql_text, str) and cql_text.strip():
        params["filter"] = cql_text.strip()

    policy = features_request_policy()
    url = f"{client.base_ngd_features}/collections/{collection}/items"
    status, body, fetch_warnings, degraded = _fetch_feature_page(
        url=url,
        params=params,
        policy=policy,
    )
    warnings.extend(fetch_warnings)
    if status != 200:
        return 501, body
    if degraded and include_geometry:
        include_geometry = False
        add_warning(warnings, "TIMEOUT_GEOMETRY_DISABLED")

    raw_features = body.get("features", [])
    if not isinstance(raw_features, list):
        raw_features = []

    filtered_features: list[dict[str, Any]] = []
    for feature in raw_features:
        if not isinstance(feature, dict):
            continue
        if polygon is not None and not _feature_intersects_polygon(feature, polygon):
            continue
        if isinstance(filter_spec, dict) and not _feature_matches_filter(feature, filter_spec):
            continue
        filtered_features.append(feature)

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

    has_more_upstream = _upstream_has_more(
        body,
        page_size=len(raw_features),
        offset=offset,
        limit=limit,
    )
    scan = {
        "mode": "local" if local_filtering else ("upstream" if filter_applied == "upstream" else "none"),
        "pagesScanned": 1,
        "pageBudget": scan_page_budget if local_filtering else 0,
        "partial": False,
    }

    number_matched: int | None = None
    local_hit_total = len(filtered_features)
    if local_filtering and result_type == "hits":
        timeout = (
            float(policy["connectTimeoutSeconds"]),
            float(policy["readTimeoutSeconds"]),
        )
        pages_scanned = 1
        next_offset = offset
        scan_incomplete = has_more_upstream
        while scan_incomplete and pages_scanned < scan_page_budget:
            next_offset += limit
            page_status, page_body = _client_get_json(
                url,
                {**params, "offset": next_offset},
                timeout=timeout,
                retries=int(policy["retries"]),
            )
            if page_status != 200 or not isinstance(page_body, dict):
                add_warning(warnings, "LOCAL_SCAN_ABORTED")
                scan["partial"] = True
                break
            page_raw = page_body.get("features", [])
            if not isinstance(page_raw, list):
                page_raw = []
            pages_scanned += 1
            scan["pagesScanned"] = pages_scanned
            for feature in page_raw:
                if not isinstance(feature, dict):
                    continue
                if polygon is not None and not _feature_intersects_polygon(feature, polygon):
                    continue
                if isinstance(filter_spec, dict) and not _feature_matches_filter(feature, filter_spec):
                    continue
                local_hit_total += 1
            scan_incomplete = _upstream_has_more(
                page_body,
                page_size=len(page_raw),
                offset=next_offset,
                limit=limit,
            )
        if scan_incomplete:
            scan["partial"] = True
            add_warning(warnings, "LOCAL_FILTER_PARTIAL_SCAN")
        if not scan["partial"]:
            number_matched = local_hit_total
    elif local_filtering:
        if has_more_upstream:
            scan["partial"] = True
            add_warning(warnings, "LOCAL_FILTER_PARTIAL_SCAN")
        elif result_type == "results":
            number_matched = len(filtered_features)
    else:
        matched = body.get("numberMatched")
        if isinstance(matched, int):
            number_matched = matched

    if result_type == "hits":
        features_out: list[dict[str, Any]] = []
    else:
        features_out = []
        trimmed_properties = False
        for feature in filtered_features:
            geometry = feature.get("geometry")
            geometry_type = geometry.get("type") if isinstance(geometry, dict) else None
            projected, trimmed = _project_properties(
                feature.get("properties"),
                include_fields or [],
                exclude_fields or [],
                thin_mode=thin_mode,
            )
            trimmed_properties = trimmed_properties or trimmed
            out_item: dict[str, Any] = {
                "id": feature.get("id"),
                "geometry_type": geometry_type,
                "properties": projected,
            }
            if include_geometry and isinstance(geometry, dict):
                out_item["geometry"] = geometry
            features_out.append(out_item)
        if trimmed_properties:
            add_warning(warnings, "THIN_PROPERTIES_APPLIED")

    queryables: dict[str, Any] | None = None
    if include_queryables:
        timeout = (
            float(policy["connectTimeoutSeconds"]),
            float(policy["readTimeoutSeconds"]),
        )
        queryables_url = f"{client.base_ngd_features}/collections/{collection}/queryables"
        queryables_status, queryables_body = _client_get_json(
            queryables_url,
            None,
            timeout=timeout,
            retries=int(policy["retries"]),
        )
        if queryables_status == 200 and isinstance(queryables_body, dict):
            queryables = queryables_body
        else:
            queryables = {
                "isError": True,
                "status": queryables_status,
                "message": "Queryables metadata unavailable for this collection.",
            }
            add_warning(warnings, "QUERYABLES_UNAVAILABLE")

    number_returned = len(features_out)
    next_token: str | None = None
    if result_type == "results" and has_more_upstream:
        next_token = str(offset + limit)

    response: dict[str, Any] = {
        "collection": collection,
        "bbox": list(bbox),
        "features": features_out,
        "count": number_returned,
        "numberMatched": number_matched,
        "numberReturned": number_returned,
        "limit": limit,
        "offset": offset,
        "nextPageToken": next_token,
        "resultType": result_type,
        "live": True,
        "hints": {
            "warnings": warnings,
            "filterApplied": filter_applied,
            "scan": scan,
        },
        "hintMessages": _HINT_MESSAGES,
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
    if include_queryables:
        response["queryables"] = queryables
    if result_type == "hits" and scan["partial"]:
        response["matchedCountLowerBound"] = local_hit_total

    selected_mode = select_delivery_mode(
        requested_delivery=delivery or "auto",
        payload_bytes=payload_bytes(response),
        inline_max_bytes=inline_max_bytes or int(
            getattr(settings, "OS_EXPORT_INLINE_MAX_BYTES", 200_000)
        ),
    )
    if selected_mode == "resource":
        meta = write_resource_payload(prefix="os-features-query", payload=response)
        return 200, {
            "collection": collection,
            "bbox": list(bbox),
            "count": response["count"],
            "numberMatched": response["numberMatched"],
            "numberReturned": response["numberReturned"],
            "limit": response["limit"],
            "offset": response["offset"],
            "nextPageToken": response["nextPageToken"],
            "resultType": result_type,
            "delivery": "resource",
            "resourceUri": meta["resourceUri"],
            "bytes": meta["bytes"],
            "sha256": meta["sha256"],
            "live": True,
            "hints": response["hints"],
            "hintMessages": _HINT_MESSAGES,
        }
    response["delivery"] = "inline"
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
                    "default": _DEFAULT_INCLUDE_GEOMETRY,
                },
                "thinMode": {
                    "type": "boolean",
                    "description": "When true, project properties to a bounded field set by default.",
                    "default": _DEFAULT_THIN_MODE,
                },
                "allowLargeBbox": {
                    "type": "boolean",
                    "description": "When true, disables bbox-area clamping guardrail.",
                },
                "scanPageBudget": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10,
                    "description": "Max pages to scan for local-filter count-only paths.",
                },
                "delivery": {
                    "type": "string",
                    "enum": ["inline", "resource", "auto"],
                },
                "inlineMaxBytes": {"type": "integer", "minimum": 1},
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
                "delivery": {"type": "string"},
                "resourceUri": {"type": "string"},
                "hints": {"type": "object"},
                "hintMessages": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["count", "numberReturned", "delivery"],
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


def _wfs_capabilities_common(path: str, payload: dict[str, Any]) -> ToolResult:
    delivery, delivery_err = parse_delivery(payload.get("delivery"), default="auto")
    if delivery_err:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": delivery_err}
    inline_max_bytes, max_err = parse_inline_max_bytes(payload.get("inlineMaxBytes"))
    if max_err:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": max_err}

    params: dict[str, Any] = {"service": "WFS", "request": "GetCapabilities"}
    version = payload.get("version")
    if isinstance(version, str) and version.strip():
        params["version"] = version.strip()

    status, body = client.get_bytes(path, params)
    if status != 200:
        return status, body
    content = body.get("content")
    if not isinstance(content, (bytes, bytearray)):
        return 500, {
            "isError": True,
            "code": "INTEGRATION_ERROR",
            "message": "WFS capabilities response was not binary content.",
        }
    xml_text = bytes(content).decode("utf-8", "replace")
    response_payload = {
        "service": "WFS",
        "request": "GetCapabilities",
        "contentType": str(body.get("contentType", "application/xml")),
        "xml": xml_text,
        "bytes": len(content),
        "live": True,
    }
    selected_mode = select_delivery_mode(
        requested_delivery=delivery or "auto",
        payload_bytes=payload_bytes(response_payload),
        inline_max_bytes=inline_max_bytes or int(getattr(settings, "OS_EXPORT_INLINE_MAX_BYTES", 200_000)),
    )
    if selected_mode == "resource":
        prefix = "os-features-wfs-archive-capabilities" if "archive" in path else "os-features-wfs-capabilities"
        meta = write_resource_payload(prefix=prefix, payload=response_payload)
        return 200, {
            "delivery": "resource",
            "resourceUri": meta["resourceUri"],
            "bytes": meta["bytes"],
            "sha256": meta["sha256"],
            "contentType": response_payload["contentType"],
            "live": True,
        }
    response_payload["delivery"] = "inline"
    return 200, response_payload


def _wfs_capabilities(payload: dict[str, Any]) -> ToolResult:
    return _wfs_capabilities_common("https://api.os.uk/features/v1/wfs", payload)


def _wfs_archive_capabilities(payload: dict[str, Any]) -> ToolResult:
    return _wfs_capabilities_common("https://api.os.uk/features/v1/wfs/archive", payload)


register(
    Tool(
        name="os_features.wfs_capabilities",
        description="Fetch WFS GetCapabilities for OS Features API.",
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "os_features.wfs_capabilities"},
                "version": {"type": "string"},
                "delivery": {"type": "string", "enum": ["inline", "resource", "auto"]},
                "inlineMaxBytes": {"type": "integer", "minimum": 1},
            },
            "required": [],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "delivery": {"type": "string"},
                "xml": {"type": "string"},
                "resourceUri": {"type": "string"},
            },
            "required": ["delivery"],
            "additionalProperties": True,
        },
        handler=_wfs_capabilities,
    )
)

register(
    Tool(
        name="os_features.wfs_archive_capabilities",
        description="Fetch WFS archive GetCapabilities (entitlement dependent).",
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "os_features.wfs_archive_capabilities"},
                "version": {"type": "string"},
                "delivery": {"type": "string", "enum": ["inline", "resource", "auto"]},
                "inlineMaxBytes": {"type": "integer", "minimum": 1},
            },
            "required": [],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "delivery": {"type": "string"},
                "xml": {"type": "string"},
                "resourceUri": {"type": "string"},
            },
            "required": ["delivery"],
            "additionalProperties": True,
        },
        handler=_wfs_archive_capabilities,
    )
)
