from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import sqlite3
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Iterable

from server.ons_geo_cache import (
    ONSGeoCache,
    ONSGeoCacheReadError,
    normalize_postcode,
    normalize_uprn,
)
from tools.registry import Tool, ToolResult, get as get_tool, register

_REPO_ROOT = Path(__file__).resolve().parents[1]
_EXPORTS_DIR = _REPO_ROOT / "data" / "exports"
_OS_EXPORTS_DIR = _REPO_ROOT / "data" / "os_exports"
_OS_EXPORT_JOBS_DIR = _OS_EXPORTS_DIR / "jobs"

# Base collection ids (without numeric suffix). We resolve to the latest available version
# via `os_features.collections` when needed.
_DEFAULT_COLLECTION_BASES: dict[str, str] = {
    "buildings": "bld-fts-buildingpart",
    "road_links": "trn-ntwk-roadlink",
    "path_links": "trn-ntwk-pathlink",
    "postcode_unit_areas": "asu-gbpcd-postcodeunitarea",
    "postcode_unit_points": "asu-gbpcd-postcodeunitpoint",
    "bus_lanes": "trn-ntwk-buslane",
    "cycle_lanes": "trn-ntwk-cyclelane",
}
_NGD_LAYER_IDS = frozenset(_DEFAULT_COLLECTION_BASES)
_SUPPORTED_LAYER_IDS = frozenset({"uprns", *_NGD_LAYER_IDS})
_DEFAULT_INVENTORY_LAYERS = ["uprns", "buildings", "road_links", "path_links"]
_LAYER_DESCRIPTION = (
    "Requested layers (uprns, buildings, road_links, path_links, "
    "postcode_unit_areas, postcode_unit_points, bus_lanes, cycle_lanes)."
)

_DEFAULT_LIMITS: dict[str, int] = {
    "uprns": 100,
    "buildings": 100,
    "road_links": 100,
    "path_links": 100,
    "postcode_unit_areas": 100,
    "postcode_unit_points": 100,
    "bus_lanes": 100,
    "cycle_lanes": 100,
}

_MAX_LIMIT = 500

_NGD_COLLECTION_CACHE_TTL_SECONDS = 3600.0
_NGD_COLLECTION_CACHE: dict[str, Any] = {"stored_at": 0.0, "latest_by_base": {}}

_GSS_LEVEL_TO_COLUMN: dict[str, tuple[str, str | None]] = {
    "OA": ("oa_code", "selected_by_oa"),
    "LSOA": ("lsoa_code", "selected_by_lsoa"),
    "MSOA": ("msoa_code", "selected_by_msoa"),
    "LAD": ("lad_code", None),
    "WD": ("ward_code", None),
    "WARD": ("ward_code", None),
    "CTRY": ("country_code", None),
    "COUNTRY": ("country_code", None),
    "RGN": ("region_code", None),
    "REGION": ("region_code", None),
}

_MEMBERSHIP_COLUMNS = [
    "selected_by_oa",
    "selected_by_lsoa",
    "selected_by_msoa",
    "selected_by_postcode",
    "selected_by_uprn",
    "selected_by_polygon",
]

_CSV_COLUMNS_CANONICAL_DEFAULT = [
    "uprn",
    "postcode",
    "oa_code",
    "local_authority_name",
    "lsoa_code",
    "msoa_code",
    "lad_code",
]

_CSV_COLUMNS_DEFAULT = [
    *_CSV_COLUMNS_CANONICAL_DEFAULT,
    "selected_by_oa",
    "selected_by_lsoa",
    "selected_by_msoa",
    "selected_by_postcode",
    "selected_by_uprn",
    "selected_by_polygon",
]

_EXPORT_JOB_LOCK = threading.Lock()
_ROAD_EXPORT_FORMATS = {"geojson_bundle", "javascript_overlay", "leaflet_snippet"}
_DEFAULT_ROAD_EXPORT_LIMIT = 100


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    tmp_path.write_text(text, encoding="utf-8")
    tmp_path.replace(path)


def _normalize_export_id(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    candidate = value.strip()
    if not candidate:
        return None
    try:
        return str(uuid.UUID(candidate))
    except ValueError:
        return None


def _stable_json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True)


def _slugify_name(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "road"


def _escape_cql_literal(value: str) -> str:
    return value.replace("'", "''")


def _parse_bbox(value: Any) -> list[float] | None:
    if not (isinstance(value, list) and len(value) == 4):
        return None
    try:
        min_lon, min_lat, max_lon, max_lat = [float(x) for x in value]
    except (TypeError, ValueError):
        return None
    if min_lon >= max_lon or min_lat >= max_lat:
        return None
    return [min_lon, min_lat, max_lon, max_lat]


def _parse_layers(value: Any) -> list[str] | None:
    if value is None:
        return None
    if isinstance(value, str):
        parts = [p.strip() for p in value.split(",") if p.strip()]
    elif isinstance(value, list):
        parts = [str(p).strip() for p in value if p is not None and str(p).strip()]
    else:
        return None
    out: list[str] = []
    for part in parts:
        if part in _SUPPORTED_LAYER_IDS and part not in out:
            out.append(part)
    return out or None


def _parse_limits(value: Any) -> dict[str, int]:
    limits: dict[str, int] = dict(_DEFAULT_LIMITS)
    if not isinstance(value, dict):
        return limits
    for key, raw in value.items():
        if key not in limits:
            continue
        try:
            parsed = int(raw)
        except (TypeError, ValueError):
            continue
        if parsed < 1:
            continue
        limits[key] = min(parsed, _MAX_LIMIT)
    return limits


def _parse_response_mode(value: Any) -> str | None:
    if value is None:
        return "full"
    if not isinstance(value, str):
        return None
    normalized = value.strip().lower()
    if normalized not in {"full", "summary", "counts"}:
        return None
    return normalized


def _parse_layer_tokens(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    out: dict[str, str] = {}
    for key, raw in value.items():
        if key not in _NGD_LAYER_IDS:
            continue
        if isinstance(raw, (int, float)):
            raw = str(int(raw))
        if isinstance(raw, str) and raw.strip():
            out[key] = raw.strip()
    return out


def _parse_bool_map(value: Any) -> dict[str, bool]:
    if not isinstance(value, dict):
        return {}
    out: dict[str, bool] = {}
    for key, raw in value.items():
        if key not in _NGD_LAYER_IDS:
            continue
        if isinstance(raw, bool):
            out[key] = raw
    return out


def _parse_collections_override(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    out: dict[str, str] = {}
    for key, raw in value.items():
        if key not in _NGD_LAYER_IDS:
            continue
        if isinstance(raw, str) and raw.strip():
            out[key] = raw.strip()
    return out


def _parse_selector_list(value: Any) -> list[dict[str, Any]] | None:
    if not isinstance(value, list):
        return None
    out: list[dict[str, Any]] = []
    for row in value:
        if not isinstance(row, dict):
            return None
        out.append(dict(row))
    return out


def _parse_uprn_list(value: Any) -> set[str] | None:
    if value is None:
        return set()
    if not isinstance(value, list):
        return None
    out: set[str] = set()
    for raw in value:
        if not isinstance(raw, str):
            return None
        normalized = normalize_uprn(raw)
        if normalized is None:
            return None
        out.add(normalized)
    return out


def _append_shorthand_selector(
    selectors: list[dict[str, Any]],
    selector_type: str,
    key: str,
    value: Any,
) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        return f"selectionSpec.{key} must be a non-empty string"
    selectors.append({"type": selector_type, key: value.strip()})
    return None


def _parse_selection_spec(value: Any) -> tuple[dict[str, Any] | None, str | None]:
    if not isinstance(value, dict):
        return None, "selectionSpec must be an object"
    selectors = _parse_selector_list(value.get("selectors", []))
    if selectors is None:
        return None, "selectionSpec.selectors must be an array of objects"
    selectors = list(selectors)

    postcode_error = _append_shorthand_selector(
        selectors,
        "postcode",
        "postcode",
        value.get("postcode"),
    )
    if postcode_error:
        return None, postcode_error

    uprn_error = _append_shorthand_selector(
        selectors,
        "uprn",
        "uprn",
        value.get("uprn"),
    )
    if uprn_error:
        return None, uprn_error

    geometry = value.get("geometry")
    if geometry is None:
        geometry = value.get("polygon")
    if geometry is not None:
        if not isinstance(geometry, dict):
            return None, "selectionSpec.geometry must be an object"
        selectors.append({"type": "polygon", "geometry": geometry})

    gss_code = value.get("gssCode")
    if gss_code is None:
        gss_code = value.get("gss_code")
    if gss_code is not None:
        if not isinstance(gss_code, str) or not gss_code.strip():
            return None, "selectionSpec.gssCode must be a non-empty string"
        level_raw = value.get("level")
        if not isinstance(level_raw, str) or not level_raw.strip():
            return None, "selectionSpec.level is required when selectionSpec.gssCode is provided"
        selectors.append(
            {
                "type": "gss_code",
                "level": level_raw.strip().upper(),
                "code": gss_code.strip().upper(),
            }
        )

    uprn_overrides = value.get("uprnOverrides", {})
    if uprn_overrides is None:
        uprn_overrides = {}
    if not isinstance(uprn_overrides, dict):
        return None, "selectionSpec.uprnOverrides must be an object"

    include = _parse_uprn_list(uprn_overrides.get("include", []))
    if include is None:
        return None, "selectionSpec.uprnOverrides.include must be an array of numeric strings"

    exclude = _parse_uprn_list(uprn_overrides.get("exclude", []))
    if exclude is None:
        return None, "selectionSpec.uprnOverrides.exclude must be an array of numeric strings"

    return {
        "selectors": selectors,
        "uprnOverrides": {"include": sorted(include), "exclude": sorted(exclude)},
    }, None


def _selection_cache_error(exc: Exception) -> ToolResult:
    if isinstance(exc, RuntimeError):
        return 503, {
            "isError": True,
            "code": "CACHE_UNAVAILABLE",
            "message": str(exc),
        }
    if isinstance(exc, (sqlite3.Error, ONSGeoCacheReadError)):
        return 503, {
            "isError": True,
            "code": "CACHE_READ_ERROR",
            "message": (
                "ONS geo cache is unreadable. "
                f"{exc} Run scripts/ons_geo_cache_refresh.py to rebuild the cache."
            ),
        }
    return 500, {
        "isError": True,
        "code": "INTEGRATION_ERROR",
        "message": str(exc) or "selectionSpec resolution failed",
    }


def _normalize_outer_ring(points: Any) -> list[list[float]] | None:
    if not isinstance(points, list) or len(points) < 4:
        return None
    ring: list[list[float]] = []
    for point in points:
        if not (isinstance(point, list | tuple) and len(point) >= 2):
            return None
        try:
            lon = float(point[0])
            lat = float(point[1])
        except (TypeError, ValueError):
            return None
        ring.append([lon, lat])
    if ring[0] != ring[-1]:
        ring.append(list(ring[0]))
    if len({(pt[0], pt[1]) for pt in ring[:-1]}) < 3:
        return None
    return ring


def _polygon_area_abs(ring: list[list[float]]) -> float:
    if len(ring) < 4:
        return 0.0
    area = 0.0
    for index in range(len(ring) - 1):
        x1, y1 = ring[index]
        x2, y2 = ring[index + 1]
        area += (x1 * y2) - (x2 * y1)
    return abs(area) / 2.0


def _normalize_polygon_geometry(value: Any) -> tuple[list[dict[str, Any]], list[str]]:
    warnings: list[str] = []
    if not isinstance(value, dict):
        return [], warnings
    geom_type = str(value.get("type") or "").lower()
    if geom_type == "polygon":
        coords = value.get("coordinates")
        if (
            isinstance(coords, list)
            and coords
            and isinstance(coords[0], list)
            and coords[0]
        ):
            ring = _normalize_outer_ring(coords[0])
            if ring is not None:
                if len(coords) > 1:
                    warnings.append("AOI_POLYGON_HOLES_DROPPED")
                return [{"type": "Polygon", "coordinates": [ring]}], warnings
        return [], warnings
    if geom_type == "multipolygon":
        coords = value.get("coordinates")
        polygons: list[dict[str, Any]] = []
        if isinstance(coords, list):
            for polygon in coords:
                if (
                    isinstance(polygon, list)
                    and polygon
                    and isinstance(polygon[0], list)
                    and polygon[0]
                ):
                    ring = _normalize_outer_ring(polygon[0])
                    if ring is not None:
                        polygons.append({"type": "Polygon", "coordinates": [ring]})
            if polygons:
                warnings.append("AOI_MULTIPOLYGON_SPLIT")
        return polygons, warnings
    rings = value.get("rings")
    if isinstance(rings, list):
        outer_rings: list[list[list[float]]] = []
        for ring_raw in rings:
            ring = _normalize_outer_ring(ring_raw)
            if ring is not None:
                outer_rings.append(ring)
        if not outer_rings:
            return [], warnings
        outer_rings.sort(key=_polygon_area_abs, reverse=True)
        warnings.append("AOI_ARCGIS_GEOMETRY_NORMALIZED")
        if len(outer_rings) > 1:
            warnings.append("AOI_MULTIRING_SPLIT")
        return [{"type": "Polygon", "coordinates": [ring]} for ring in outer_rings], warnings
    return [], warnings


def _meters_per_degree(lat: float) -> tuple[float, float]:
    lat_rad = math.radians(lat)
    meters_lat = (
        111_132.92
        - 559.82 * math.cos(2 * lat_rad)
        + 1.175 * math.cos(4 * lat_rad)
        - 0.0023 * math.cos(6 * lat_rad)
    )
    meters_lon = (
        111_412.84 * math.cos(lat_rad)
        - 93.5 * math.cos(3 * lat_rad)
        + 0.118 * math.cos(5 * lat_rad)
    )
    return meters_lat, meters_lon


def _geometry_bbox(geometry: dict[str, Any] | None) -> list[float] | None:
    if not isinstance(geometry, dict):
        return None
    coords = geometry.get("coordinates")
    if not isinstance(coords, list):
        return None

    points: list[tuple[float, float]] = []

    def _iter_points(value: Any) -> None:
        if isinstance(value, list):
            if len(value) >= 2 and all(isinstance(v, (int, float)) for v in value[:2]):
                points.append((float(value[0]), float(value[1])))
            else:
                for child in value:
                    _iter_points(child)

    _iter_points(coords)
    if not points:
        return None
    lons = [point[0] for point in points]
    lats = [point[1] for point in points]
    return [min(lons), min(lats), max(lons), max(lats)]


def _rect_polygon_from_bbox(bbox: list[float]) -> dict[str, Any]:
    min_lon, min_lat, max_lon, max_lat = bbox
    return {
        "type": "Polygon",
        "coordinates": [
            [
                [min_lon, min_lat],
                [max_lon, min_lat],
                [max_lon, max_lat],
                [min_lon, max_lat],
                [min_lon, min_lat],
            ]
        ],
    }


def _expand_bbox_by_meters(bbox: list[float], meters: float) -> list[float]:
    if meters <= 0.0:
        return list(bbox)
    min_lon, min_lat, max_lon, max_lat = bbox
    mid_lat = (min_lat + max_lat) / 2.0
    meters_lat, meters_lon = _meters_per_degree(mid_lat)
    delta_lat = meters / max(meters_lat, 1e-9)
    delta_lon = meters / max(meters_lon, 1e-9)
    return [
        min_lon - delta_lon,
        min_lat - delta_lat,
        max_lon + delta_lon,
        max_lat + delta_lat,
    ]


def _point_in_polygon(point: tuple[float, float], polygon: list[tuple[float, float]]) -> bool:
    x, y = point
    inside = False
    for index in range(len(polygon) - 1):
        x1, y1 = polygon[index]
        x2, y2 = polygon[index + 1]
        intersects = ((y1 > y) != (y2 > y)) and (
            x < (x2 - x1) * (y - y1) / ((y2 - y1) or 1e-12) + x1
        )
        if intersects:
            inside = not inside
    return inside


def _point_on_segment(
    point: tuple[float, float],
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    epsilon: float = 1e-12,
) -> bool:
    px, py = point
    x1, y1 = start
    x2, y2 = end
    cross = (px - x1) * (y2 - y1) - (py - y1) * (x2 - x1)
    if abs(cross) > epsilon:
        return False
    return (
        min(x1, x2) - epsilon <= px <= max(x1, x2) + epsilon
        and min(y1, y2) - epsilon <= py <= max(y1, y2) + epsilon
    )


def _segments_intersect(
    first_start: tuple[float, float],
    first_end: tuple[float, float],
    second_start: tuple[float, float],
    second_end: tuple[float, float],
    *,
    epsilon: float = 1e-12,
) -> bool:
    def _orientation(
        origin: tuple[float, float],
        point_a: tuple[float, float],
        point_b: tuple[float, float],
    ) -> float:
        return (
            (point_a[0] - origin[0]) * (point_b[1] - origin[1])
            - (point_a[1] - origin[1]) * (point_b[0] - origin[0])
        )

    o1 = _orientation(first_start, first_end, second_start)
    o2 = _orientation(first_start, first_end, second_end)
    o3 = _orientation(second_start, second_end, first_start)
    o4 = _orientation(second_start, second_end, first_end)

    if ((o1 > epsilon and o2 < -epsilon) or (o1 < -epsilon and o2 > epsilon)) and (
        (o3 > epsilon and o4 < -epsilon) or (o3 < -epsilon and o4 > epsilon)
    ):
        return True

    if abs(o1) <= epsilon and _point_on_segment(second_start, first_start, first_end):
        return True
    if abs(o2) <= epsilon and _point_on_segment(second_end, first_start, first_end):
        return True
    if abs(o3) <= epsilon and _point_on_segment(first_start, second_start, second_end):
        return True
    if abs(o4) <= epsilon and _point_on_segment(first_end, second_start, second_end):
        return True
    return False


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

    def _iter_line_sequences(value: Any):
        if not isinstance(value, list):
            return
        if value and all(
            isinstance(entry, list | tuple)
            and len(entry) >= 2
            and all(isinstance(v, (int, float)) for v in entry[:2])
            for entry in value
        ):
            yield [(float(entry[0]), float(entry[1])) for entry in value]
            return
        for child in value:
            yield from _iter_line_sequences(child)

    for point in _iter_points(coords):
        if _point_in_polygon(point, polygon):
            return True

    polygon_edges = list(zip(polygon, polygon[1:], strict=False))
    for sequence in _iter_line_sequences(coords):
        for start, end in zip(sequence, sequence[1:], strict=False):
            for polygon_start, polygon_end in polygon_edges:
                if _segments_intersect(start, end, polygon_start, polygon_end):
                    return True
    return False


def _geometry_contains_point(geometry: dict[str, Any] | None, point: tuple[float, float]) -> bool:
    polygons, _warnings = _normalize_polygon_geometry(geometry)
    for polygon in polygons:
        coords = polygon.get("coordinates")
        if not (
            isinstance(coords, list)
            and coords
            and isinstance(coords[0], list)
        ):
            continue
        ring = [
            (float(entry[0]), float(entry[1]))
            for entry in coords[0]
            if isinstance(entry, list | tuple) and len(entry) >= 2
        ]
        if len(ring) >= 4 and _point_in_polygon(point, ring):
            return True
    return False


def _normalize_export_format(value: Any) -> str:
    if not isinstance(value, str):
        return "csv"
    norm = value.strip().lower()
    return "csv" if norm != "json" else "json"


def _normalize_road_export_format(value: Any) -> str | None:
    if value is None:
        return "geojson_bundle"
    if not isinstance(value, str):
        return None
    normalized = value.strip().lower()
    if normalized not in _ROAD_EXPORT_FORMATS:
        return None
    return normalized


def _normalize_force_refresh(value: Any) -> bool | None:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    return None


def _normalize_derivation_mode(value: Any) -> str:
    if not isinstance(value, str):
        return "exact"
    norm = value.strip().lower()
    return norm if norm in {"exact", "best_fit"} else "exact"


def _normalize_columns_config(value: Any) -> dict[str, Any]:
    default = {"defaultSet": "maplab_default_v1", "selectorMembership": True}
    if not isinstance(value, dict):
        return default
    default_set_raw = value.get("defaultSet")
    default_set = (
        str(default_set_raw).strip()
        if isinstance(default_set_raw, str) and default_set_raw.strip()
        else "maplab_default_v1"
    )
    if default_set != "maplab_default_v1":
        default_set = "maplab_default_v1"
    selector_membership = value.get("selectorMembership")
    if isinstance(selector_membership, bool):
        include_membership = selector_membership
    else:
        include_membership = True
    return {"defaultSet": default_set, "selectorMembership": include_membership}


def _csv_columns_from_config(value: Any) -> list[str]:
    config = _normalize_columns_config(value)
    if config.get("selectorMembership", True):
        return list(_CSV_COLUMNS_DEFAULT)
    return list(_CSV_COLUMNS_CANONICAL_DEFAULT)


def _sort_uprns(values: Iterable[str]) -> list[str]:
    def _key(value: str) -> tuple[int, str]:
        return (0, f"{int(value):020d}") if value.isdigit() else (1, value)

    return sorted(set(values), key=_key)


def _parse_simplify_tolerance(value: Any) -> float | None:
    if value is None:
        return 0.0
    if isinstance(value, bool):
        return None
    try:
        tolerance = float(value)
    except (TypeError, ValueError):
        return None
    if tolerance < 0.0:
        return None
    return tolerance


def _meters_to_degrees(tolerance_meters: float) -> float:
    if tolerance_meters <= 0.0:
        return 0.0
    return tolerance_meters / 111_320.0


def _point_segment_distance_sq(
    point: tuple[float, float],
    start: tuple[float, float],
    end: tuple[float, float],
) -> float:
    px, py = point
    sx, sy = start
    ex, ey = end
    dx = ex - sx
    dy = ey - sy
    if dx == 0.0 and dy == 0.0:
        return (px - sx) ** 2 + (py - sy) ** 2
    t = ((px - sx) * dx + (py - sy) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    proj_x = sx + t * dx
    proj_y = sy + t * dy
    return (px - proj_x) ** 2 + (py - proj_y) ** 2


def _simplify_line_coords(coords: list[list[float]], tolerance_degrees: float) -> list[list[float]]:
    if tolerance_degrees <= 0.0 or len(coords) <= 2:
        return coords
    normalized: list[list[float]] = []
    for coord in coords:
        if not (
            isinstance(coord, list)
            and len(coord) >= 2
            and isinstance(coord[0], (int, float))
            and isinstance(coord[1], (int, float))
        ):
            return coords
        normalized.append([float(coord[0]), float(coord[1]), *coord[2:]])
    keep = [False] * len(normalized)
    keep[0] = True
    keep[-1] = True
    stack: list[tuple[int, int]] = [(0, len(normalized) - 1)]
    tolerance_sq = tolerance_degrees * tolerance_degrees

    while stack:
        first, last = stack.pop()
        start = (normalized[first][0], normalized[first][1])
        end = (normalized[last][0], normalized[last][1])
        max_dist = -1.0
        max_index = -1
        for index in range(first + 1, last):
            point = (normalized[index][0], normalized[index][1])
            dist_sq = _point_segment_distance_sq(point, start, end)
            if dist_sq > max_dist:
                max_dist = dist_sq
                max_index = index
        if max_index > 0 and max_dist > tolerance_sq:
            keep[max_index] = True
            stack.append((first, max_index))
            stack.append((max_index, last))
    return [coord for index, coord in enumerate(normalized) if keep[index]]


def _simplify_geometry(geometry: dict[str, Any] | None, tolerance_meters: float) -> dict[str, Any] | None:
    if not isinstance(geometry, dict):
        return geometry
    tolerance_degrees = _meters_to_degrees(tolerance_meters)
    if tolerance_degrees <= 0.0:
        return geometry
    geom_type = geometry.get("type")
    coords = geometry.get("coordinates")
    if geom_type == "LineString" and isinstance(coords, list):
        return {**geometry, "coordinates": _simplify_line_coords(coords, tolerance_degrees)}
    if geom_type == "MultiLineString" and isinstance(coords, list):
        simplified: list[list[list[float]]] = []
        for line in coords:
            if not isinstance(line, list):
                return geometry
            simplified.append(_simplify_line_coords(line, tolerance_degrees))
        return {**geometry, "coordinates": simplified}
    return geometry


def _parse_roads_export_specs(
    value: Any,
    *,
    default_bbox: list[float] | None,
    default_collection: str,
    allow_missing_bbox: bool = False,
) -> tuple[list[dict[str, Any]] | None, str | None]:
    if not isinstance(value, list) or not value:
        return None, "roads must be a non-empty array"
    slug_counts: dict[str, int] = {}
    out: list[dict[str, Any]] = []
    for index, raw in enumerate(value, start=1):
        if not isinstance(raw, dict):
            return None, f"roads[{index}] must be an object"
        label = raw.get("label")
        if not isinstance(label, str) or not label.strip():
            return None, f"roads[{index}].label must be a non-empty string"
        road_bbox = _parse_bbox(raw.get("bbox")) if raw.get("bbox") is not None else default_bbox
        if road_bbox is None and not allow_missing_bbox:
            return None, f"roads[{index}] requires bbox or a top-level bbox"
        collection_raw = raw.get("collection", default_collection)
        if not isinstance(collection_raw, str) or not collection_raw.strip():
            return None, f"roads[{index}].collection must be a non-empty string when provided"
        road_number = raw.get("roadClassificationNumber")
        if road_number is not None and (not isinstance(road_number, str) or not road_number.strip()):
            return None, (
                f"roads[{index}].roadClassificationNumber must be a non-empty string or null"
            )
        cql_raw = raw.get("cql")
        if cql_raw is not None and (not isinstance(cql_raw, str) or not cql_raw.strip()):
            return None, f"roads[{index}].cql must be a non-empty string when provided"
        cql = cql_raw.strip() if isinstance(cql_raw, str) else None
        if cql is None and isinstance(road_number, str) and road_number.strip():
            cql = f"roadclassificationnumber = '{_escape_cql_literal(road_number.strip())}'"
        slug_base = _slugify_name(label.strip())
        count = slug_counts.get(slug_base, 0) + 1
        slug_counts[slug_base] = count
        slug = slug_base if count == 1 else f"{slug_base}-{count}"
        out.append(
            {
                "label": label.strip(),
                "slug": slug,
                "bbox": list(road_bbox) if road_bbox is not None else None,
                "collection": collection_raw.strip(),
                "roadClassificationNumber": road_number.strip()
                if isinstance(road_number, str)
                else None,
                "cql": cql,
            }
        )
    return out, None


def _road_feature_collection(
    road: dict[str, Any],
    *,
    features: list[dict[str, Any]],
    complete: bool,
    source_pages: list[dict[str, Any]],
    warnings: list[str],
    error: dict[str, Any] | None,
) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "label": road["label"],
        "collection": road["collection"],
        "featureCount": len(features),
        "complete": complete,
        "sourcePagesFetched": source_pages,
        "warnings": warnings,
    }
    if road.get("bbox") is not None:
        metadata["bbox"] = list(road["bbox"])
    if road.get("roadClassificationNumber") is not None:
        metadata["roadClassificationNumber"] = road["roadClassificationNumber"]
    if road.get("cql") is not None:
        metadata["cql"] = road["cql"]
    if error is not None:
        metadata["error"] = error
    return {
        "type": "FeatureCollection",
        "name": road["label"],
        "features": features,
        "metadata": metadata,
    }


def _build_js_overlay_text(road_collections: dict[str, dict[str, Any]]) -> str:
    payload = json.dumps(road_collections, ensure_ascii=True, separators=(",", ":"))
    return (
        "/* Generated by os_map.export_roads */\n"
        f"const roadOverlayData = {payload};\n"
        "if (typeof globalThis !== 'undefined') {\n"
        "  globalThis.roadOverlayData = roadOverlayData;\n"
        "}\n"
        "if (typeof module !== 'undefined' && module.exports) {\n"
        "  module.exports = { roadOverlayData };\n"
        "}\n"
    )


def _build_leaflet_snippet_text(road_collections: dict[str, dict[str, Any]]) -> str:
    payload = json.dumps(road_collections, ensure_ascii=True, separators=(",", ":"))
    return (
        "/* Generated by os_map.export_roads */\n"
        f"const roadOverlayData = {payload};\n"
        "function createRoadOverlayLayers(L, options = {}) {\n"
        "  const palette = options.palette || {};\n"
        "  const defaultColors = ['#c2410c', '#0369a1', '#15803d', '#7c3aed', '#b45309'];\n"
        "  const group = L.layerGroup();\n"
        "  const layersByRoad = {};\n"
        "  let colorIndex = 0;\n"
        "  for (const [label, featureCollection] of Object.entries(roadOverlayData)) {\n"
        "    const color = palette[label] || defaultColors[colorIndex % defaultColors.length];\n"
        "    colorIndex += 1;\n"
        "    const layer = L.geoJSON(featureCollection, {\n"
        "      pane: options.pane,\n"
        "      style: () => ({ color, weight: 4, opacity: 0.92 }),\n"
        "    });\n"
        "    layersByRoad[label] = layer;\n"
        "    group.addLayer(layer);\n"
        "  }\n"
        "  return { group, layersByRoad, data: roadOverlayData };\n"
        "}\n"
        "if (typeof globalThis !== 'undefined') {\n"
        "  globalThis.roadOverlayData = roadOverlayData;\n"
        "  globalThis.createRoadOverlayLayers = createRoadOverlayLayers;\n"
        "}\n"
        "if (typeof module !== 'undefined' && module.exports) {\n"
        "  module.exports = { roadOverlayData, createRoadOverlayLayers };\n"
        "}\n"
    )


def _address_selector_spec(selection_spec: dict[str, Any]) -> dict[str, Any] | None:
    selectors = selection_spec.get("selectors")
    if not isinstance(selectors, list):
        return None
    address_selectors = [
        dict(selector)
        for selector in selectors
        if isinstance(selector, dict)
        and str(selector.get("type") or "").strip().lower() in {"uprn", "postcode"}
    ]
    uprn_overrides = selection_spec.get("uprnOverrides")
    payload: dict[str, Any] = {"selectors": address_selectors}
    if isinstance(uprn_overrides, dict):
        normalized_overrides = dict(uprn_overrides)
        include_values = normalized_overrides.get("include")
        exclude_values = normalized_overrides.get("exclude")
        include_non_empty = isinstance(include_values, list) and len(include_values) > 0
        exclude_non_empty = isinstance(exclude_values, list) and len(exclude_values) > 0
        if include_non_empty or exclude_non_empty:
            payload["uprnOverrides"] = normalized_overrides
    if address_selectors or "uprnOverrides" in payload:
        return payload
    return None


def _point_buffer_polygon(lon: float, lat: float, meters: float) -> dict[str, Any]:
    delta = _meters_to_degrees(max(meters, 1.0))
    return _rect_polygon_from_bbox([lon - delta, lat - delta, lon + delta, lat + delta])


def _pick_best_building_anchor(
    features: list[dict[str, Any]],
    *,
    point: tuple[float, float],
) -> dict[str, Any] | None:
    containing: list[tuple[float, dict[str, Any]]] = []
    fallback: list[tuple[float, dict[str, Any]]] = []
    for feature in features:
        if not isinstance(feature, dict):
            continue
        geometry = feature.get("geometry")
        bbox = _geometry_bbox(geometry if isinstance(geometry, dict) else None)
        if bbox is None:
            continue
        center_lon = (bbox[0] + bbox[2]) / 2.0
        center_lat = (bbox[1] + bbox[3]) / 2.0
        score = (center_lon - point[0]) ** 2 + (center_lat - point[1]) ** 2
        if _geometry_contains_point(geometry if isinstance(geometry, dict) else None, point):
            containing.append((score, feature))
        else:
            fallback.append((score, feature))
    if containing:
        containing.sort(key=lambda item: item[0])
        return containing[0][1]
    if fallback:
        fallback.sort(key=lambda item: item[0])
        return fallback[0][1]
    return None


def _resolve_building_anchor_polygon(
    *,
    uprn: str,
    lon: float,
    lat: float,
    search_meters: float,
    buffer_meters: float,
) -> tuple[dict[str, Any], list[str], dict[str, Any]]:
    warnings: list[str] = []
    bbox = _expand_bbox_by_meters([lon, lat, lon, lat], search_meters)
    tool = get_tool("os_features.query")
    point = (lon, lat)
    if tool is None:
        geometry = _point_buffer_polygon(lon, lat, buffer_meters)
        warnings.append("BUILDING_LOOKUP_TOOL_MISSING")
        return (
            geometry,
            warnings,
            {
                "uprn": uprn,
                "anchorType": "point_buffer",
                "source": "os_places.by_uprn",
                "bbox": bbox,
            },
        )

    status, payload = tool.call(
        {
            "tool": "os_features.query",
            "collection": "buildings",
            "bbox": bbox,
            "includeGeometry": True,
            "limit": 25,
            "thinMode": False,
        }
    )
    features = payload.get("features") if status == 200 and isinstance(payload, dict) else []
    if not isinstance(features, list):
        features = []
    picked = _pick_best_building_anchor(features, point=point)
    if picked is None:
        geometry = _point_buffer_polygon(lon, lat, buffer_meters)
        warnings.append("BUILDING_ANCHOR_FALLBACK_POINT_BUFFER")
        return (
            geometry,
            warnings,
            {
                "uprn": uprn,
                "anchorType": "point_buffer",
                "source": "os_places.by_uprn",
                "bbox": bbox,
            },
        )

    picked_geometry = picked.get("geometry") if isinstance(picked, dict) else None
    polygons, geometry_warnings = _normalize_polygon_geometry(
        picked_geometry if isinstance(picked_geometry, dict) else None
    )
    warnings.extend(geometry_warnings)
    if polygons:
        feature_bbox = _geometry_bbox(polygons[0])
        geometry = (
            _rect_polygon_from_bbox(_expand_bbox_by_meters(feature_bbox, buffer_meters))
            if feature_bbox is not None and buffer_meters > 0.0
            else polygons[0]
        )
        return (
            geometry,
            warnings,
            {
                "uprn": uprn,
                "anchorType": "building_buffer" if buffer_meters > 0.0 else "building_polygon",
                "source": "bld-fts-buildingpart",
                "featureId": picked.get("id"),
                "featureBBox": feature_bbox,
            },
        )

    geometry = _point_buffer_polygon(lon, lat, buffer_meters)
    warnings.append("BUILDING_ANCHOR_INVALID_GEOMETRY_FALLBACK")
    return (
        geometry,
        warnings,
        {
            "uprn": uprn,
            "anchorType": "point_buffer",
            "source": "os_places.by_uprn",
            "bbox": bbox,
        },
    )


def _resolve_area_limit_polygons(selection_spec: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    selectors = selection_spec.get("selectors")
    if not isinstance(selectors, list):
        return [], [], []

    polygons: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    warnings: list[str] = []
    area_tool = get_tool("admin_lookup.area_geometry")

    for index, selector in enumerate(selectors):
        if not isinstance(selector, dict):
            continue
        selector_type = str(selector.get("type") or "").strip().lower()
        if selector_type == "polygon":
            geometry = selector.get("geometry")
            normalized, geom_warnings = _normalize_polygon_geometry(geometry)
            polygons.extend(normalized)
            warnings.extend(geom_warnings)
            summaries.append(
                {
                    "selectorType": "polygon",
                    "selectorId": _selector_membership_label(selector, f"polygon-{index + 1}"),
                    "polygonCount": len(normalized),
                }
            )
            continue
        if selector_type != "gss_code":
            continue
        level = str(selector.get("level") or "").strip().upper()
        code = str(selector.get("code") or "").strip().upper()
        if not level or not code:
            warnings.append(f"selectors[{index}] gss_code missing level/code")
            continue
        if area_tool is None:
            warnings.append("AREA_GEOMETRY_TOOL_MISSING")
            continue
        status, payload = area_tool.call(
            {"tool": "admin_lookup.area_geometry", "id": code, "includeGeometry": True}
        )
        if status != 200 or not isinstance(payload, dict):
            warnings.append(f"AREA_GEOMETRY_LOOKUP_FAILED:{code}")
            continue
        geometry = payload.get("geometry")
        normalized, geom_warnings = _normalize_polygon_geometry(geometry)
        if not normalized:
            warnings.append(f"AREA_GEOMETRY_MISSING:{code}")
            continue
        polygons.extend(normalized)
        warnings.extend(geom_warnings)
        summaries.append(
            {
                "selectorType": "gss_code",
                "selectorId": code,
                "level": level,
                "polygonCount": len(normalized),
                "bbox": payload.get("bbox"),
            }
        )
    return polygons, summaries, warnings


def _resolve_address_anchor_polygons(
    *,
    selection_spec: dict[str, Any],
    derivation_mode: str,
    postal_delivery_only: bool,
    buffer_meters: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str], dict[str, int]]:
    address_spec = _address_selector_spec(selection_spec)
    if address_spec is None:
        return [], [], [], {"resolvedUprnCount": 0, "selectorCount": 0, "excludedCount": 0}

    rows, stats, warnings = _resolve_selection_rows(
        selection_spec=address_spec,
        derivation_mode=derivation_mode,
        postal_delivery_only=postal_delivery_only,
    )
    point_tool = get_tool("os_places.by_uprn")
    if point_tool is None:
        return [], [], ["UPRN_POINT_LOOKUP_TOOL_MISSING"], stats

    polygons: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    capped_rows = rows[:200]
    if len(rows) > len(capped_rows):
        warnings.append("AOI_ADDRESS_UPRN_CAP_APPLIED")

    for row in capped_rows:
        uprn = str(row.get("uprn") or "").strip()
        if not uprn:
            continue
        status, payload = point_tool.call({"tool": "os_places.by_uprn", "uprn": uprn})
        result = payload.get("result") if status == 200 and isinstance(payload, dict) else None
        if not isinstance(result, dict):
            warnings.append(f"UPRN_POINT_LOOKUP_FAILED:{uprn}")
            continue
        try:
            lat = float(result.get("lat"))
            lon = float(result.get("lon"))
        except (TypeError, ValueError):
            warnings.append(f"UPRN_POINT_INVALID:{uprn}")
            continue
        geometry, geom_warnings, summary = _resolve_building_anchor_polygon(
            uprn=uprn,
            lon=lon,
            lat=lat,
            search_meters=max(buffer_meters, 25.0),
            buffer_meters=buffer_meters,
        )
        polygons.append(geometry)
        warnings.extend(geom_warnings)
        summary["postcode"] = row.get("postcode") or ""
        summary["point"] = [lon, lat]
        summaries.append(summary)

    return polygons, summaries, warnings, stats


def _features_collection_from_polygons(
    *,
    name: str,
    polygons: list[dict[str, Any]],
    summaries: list[dict[str, Any]],
    kind: str,
) -> dict[str, Any]:
    features: list[dict[str, Any]] = []
    for index, geometry in enumerate(polygons):
        properties = dict(summaries[index]) if index < len(summaries) else {}
        properties["kind"] = kind
        features.append(
            {
                "type": "Feature",
                "id": f"{kind}-{index + 1}",
                "properties": properties,
                "geometry": geometry,
            }
        )
    return {"type": "FeatureCollection", "name": name, "features": features}


def _resolve_export_road_aoi(
    *,
    selection_spec: dict[str, Any] | None,
    derivation_mode: str,
    postal_delivery_only: bool,
    buffer_meters: float,
) -> tuple[dict[str, Any] | None, list[str] | None]:
    if selection_spec is None:
        return None, None
    limit_polygons, limit_summaries, limit_warnings = _resolve_area_limit_polygons(selection_spec)
    anchor_polygons, anchor_summaries, anchor_warnings, address_stats = _resolve_address_anchor_polygons(
        selection_spec=selection_spec,
        derivation_mode=derivation_mode,
        postal_delivery_only=postal_delivery_only,
        buffer_meters=buffer_meters,
    )
    warnings = [*limit_warnings, *anchor_warnings]
    query_polygons = anchor_polygons or limit_polygons
    if not query_polygons:
        return None, warnings or None
    limit_filter_polygons = limit_polygons if limit_polygons and anchor_polygons else None
    return (
        {
            "queryPolygons": query_polygons,
            "limitPolygons": limit_filter_polygons,
            "anchorPolygons": anchor_polygons,
            "limitAreaPolygons": limit_polygons,
            "anchorSummaries": anchor_summaries,
            "limitSummaries": limit_summaries,
            "addressStats": address_stats,
            "warnings": warnings,
        },
        warnings or None,
    )


def _write_road_export_artifact(path: Path, content: str) -> str:
    _atomic_write_text(path, content)
    return _os_export_uri(path.relative_to(_OS_EXPORTS_DIR).as_posix())


def _load_cached_roads_export(manifest_path: Path) -> dict[str, Any] | None:
    if not manifest_path.exists() or not manifest_path.is_file():
        return None
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def _fetch_road_export_features(
    road: dict[str, Any],
    *,
    simplify_tolerance_meters: float,
    query_polygons: list[dict[str, Any]] | None = None,
    limit_polygons: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    tool = get_tool("os_features.query")
    if not tool:
        return {
            "complete": False,
            "features": [],
            "warnings": ["MISSING_TOOL"],
            "error": {
                "code": "MISSING_TOOL",
                "message": "os_features.query not registered",
            },
            "sourcePagesFetched": [],
        }

    features: list[dict[str, Any]] = []
    warnings: list[str] = []
    source_pages: list[dict[str, Any]] = []
    error: dict[str, Any] | None = None
    seen_feature_keys: set[str] = set()

    polygon_filters: list[list[tuple[float, float]]] = []
    for polygon in limit_polygons or []:
        coords = polygon.get("coordinates") if isinstance(polygon, dict) else None
        if not (
            isinstance(coords, list)
            and coords
            and isinstance(coords[0], list)
        ):
            continue
        ring = [
            (float(entry[0]), float(entry[1]))
            for entry in coords[0]
            if isinstance(entry, list | tuple) and len(entry) >= 2
        ]
        if len(ring) >= 4:
            polygon_filters.append(ring)

    aoi_requests = query_polygons or [None]

    for aoi_index, polygon in enumerate(aoi_requests, start=1):
        if polygon is None and road.get("bbox") is None:
            error = {
                "status": 400,
                "code": "INVALID_INPUT",
                "message": "Road export requires bbox or selectionSpec-derived geometry",
            }
            break
        page_token: str | None = None
        seen_page_tokens: set[str] = set()
        while True:
            request: dict[str, Any] = {
                "tool": "os_features.query",
                "collection": road["collection"],
                "limit": _DEFAULT_ROAD_EXPORT_LIMIT,
                "includeGeometry": True,
                "includeFields": ["roadclassificationnumber", "roadclassification"],
                "delivery": "inline",
            }
            if polygon is not None:
                request["polygon"] = polygon
            else:
                request["bbox"] = list(road["bbox"])
            if road.get("cql"):
                request["cql"] = road["cql"]
            if page_token:
                request["pageToken"] = page_token
            status, data = tool.call(request)
            if status != 200 or not isinstance(data, dict):
                error_body = data if isinstance(data, dict) else {}
                error = {
                    "status": status,
                    "code": str(error_body.get("code") or "INTEGRATION_ERROR"),
                    "message": str(error_body.get("message") or "Road export page fetch failed"),
                }
                break
            page_warnings = ((data.get("hints") or {}).get("warnings") if isinstance(data, dict) else None)
            if isinstance(page_warnings, list):
                for warning in page_warnings:
                    if isinstance(warning, str) and warning not in warnings:
                        warnings.append(warning)
            page_features = data.get("features")
            if not isinstance(page_features, list):
                error = {
                    "status": 500,
                    "code": "INTEGRATION_ERROR",
                    "message": "Expected features array from os_features.query",
                }
                break
            next_page_token = data.get("nextPageToken")
            source_pages.append(
                {
                    "aoiIndex": aoi_index if polygon is not None else None,
                    "offset": int(data.get("offset", 0) or 0),
                    "returned": len(page_features),
                    "nextPageToken": next_page_token if isinstance(next_page_token, str) else None,
                }
            )
            for feature in page_features:
                if not isinstance(feature, dict):
                    continue
                geometry = _simplify_geometry(feature.get("geometry"), simplify_tolerance_meters)
                if not isinstance(geometry, dict):
                    if "GEOMETRY_MISSING_FILTERED" not in warnings:
                        warnings.append("GEOMETRY_MISSING_FILTERED")
                    continue
                candidate = {
                    "type": "Feature",
                    "id": feature.get("id"),
                    "properties": feature.get("properties")
                    if isinstance(feature.get("properties"), dict)
                    else {},
                    "geometry": geometry,
                }
                if polygon_filters and not any(
                    _feature_intersects_polygon(candidate, ring) for ring in polygon_filters
                ):
                    continue
                feature_id = candidate.get("id")
                key = (
                    str(feature_id)
                    if feature_id is not None
                    else _stable_json_dumps([candidate["geometry"], candidate["properties"]])
                )
                if key in seen_feature_keys:
                    continue
                seen_feature_keys.add(key)
                features.append(candidate)
            if isinstance(next_page_token, str) and next_page_token:
                if next_page_token in seen_page_tokens:
                    error = {
                        "status": 500,
                        "code": "INTEGRATION_ERROR",
                        "message": "Paging token did not advance during os_features.query export",
                    }
                    break
                seen_page_tokens.add(next_page_token)
                page_token = next_page_token
                continue
            break
        if error is not None:
            break

    return {
        "complete": error is None,
        "features": features,
        "warnings": warnings,
        "error": error,
        "sourcePagesFetched": source_pages,
    }


def _roads_export_response_from_manifest(manifest: dict[str, Any], *, cached: bool) -> ToolResult:
    response = {
        "exportId": manifest.get("exportId"),
        "requestHash": manifest.get("requestHash"),
        "delivery": "resource",
        "resourceUri": manifest.get("resourceUri"),
        "primaryUri": manifest.get("primaryUri"),
        "format": manifest.get("format"),
        "collection": manifest.get("collection"),
        "bbox": manifest.get("bbox"),
        "featureCounts": manifest.get("featureCounts", {}),
        "roads": manifest.get("roads", []),
        "parts": manifest.get("parts", []),
        "aoi": manifest.get("aoi"),
        "complete": bool(manifest.get("complete")),
        "sourcePagesFetched": int(manifest.get("sourcePagesFetched", 0) or 0),
        "createdAt": manifest.get("createdAt"),
        "cached": cached,
    }
    return 200, response


def _export_roads(payload: dict[str, Any]) -> ToolResult:
    bbox = _parse_bbox(payload.get("bbox")) if payload.get("bbox") is not None else None
    selection_spec: dict[str, Any] | None = None
    selection_spec_raw = payload.get("selectionSpec")
    if selection_spec_raw is not None:
        selection_spec, selection_error = _parse_selection_spec(selection_spec_raw)
        if selection_error or selection_spec is None:
            return 400, {
                "isError": True,
                "code": "INVALID_INPUT",
                "message": selection_error or "selectionSpec is invalid",
            }
    output_format = _normalize_road_export_format(payload.get("outputFormat"))
    if output_format is None:
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": (
                "outputFormat must be one of: geojson_bundle, javascript_overlay, "
                "leaflet_snippet"
            ),
        }
    simplify_tolerance = _parse_simplify_tolerance(payload.get("simplifyToleranceMeters"))
    if simplify_tolerance is None:
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "simplifyToleranceMeters must be a number >= 0 when provided",
        }
    force_refresh = _normalize_force_refresh(payload.get("forceRefresh"))
    if force_refresh is None:
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "forceRefresh must be a boolean when provided",
        }
    derivation_mode = _normalize_derivation_mode(payload.get("derivationMode"))
    postal_delivery_only_raw = payload.get("postalDeliveryOnly")
    if postal_delivery_only_raw is not None and not isinstance(postal_delivery_only_raw, bool):
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "postalDeliveryOnly must be a boolean when provided",
        }
    postal_delivery_only = bool(postal_delivery_only_raw)
    anchor_buffer_meters = _parse_simplify_tolerance(payload.get("anchorBufferMeters"))
    if anchor_buffer_meters is None:
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "anchorBufferMeters must be a number >= 0 when provided",
        }
    if anchor_buffer_meters == 0.0 and payload.get("anchorBufferMeters") is None:
        anchor_buffer_meters = 20.0

    top_level_collection_raw = payload.get("collection")
    if top_level_collection_raw is not None and (
        not isinstance(top_level_collection_raw, str) or not top_level_collection_raw.strip()
    ):
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "collection must be a non-empty string when provided",
        }
    default_collection = (
        top_level_collection_raw.strip()
        if isinstance(top_level_collection_raw, str)
        else (_resolve_collection_id("road_links", {}) or "trn-ntwk-roadlink")
    )
    try:
        resolved_aoi, aoi_warnings = _resolve_export_road_aoi(
            selection_spec=selection_spec,
            derivation_mode=derivation_mode,
            postal_delivery_only=postal_delivery_only,
            buffer_meters=float(anchor_buffer_meters or 0.0),
        )
    except Exception as exc:
        return _selection_cache_error(exc)
    road_specs_payload = payload.get("roads")
    if road_specs_payload is None:
        if resolved_aoi is None:
            if selection_spec is not None:
                return 404, {
                    "isError": True,
                    "code": "AOI_NOT_RESOLVED",
                    "message": "selectionSpec did not resolve any AOI geometry.",
                    "warnings": aoi_warnings or [],
                }
            return 400, {
                "isError": True,
                "code": "INVALID_INPUT",
                "message": "roads is required unless selectionSpec resolves an AOI geometry",
            }
        road_specs = [
            {
                "label": "selection",
                "slug": "selection",
                "bbox": list(bbox) if bbox is not None else None,
                "collection": default_collection,
                "roadClassificationNumber": None,
                "cql": None,
            }
        ]
    else:
        road_specs, roads_error = _parse_roads_export_specs(
            road_specs_payload,
            default_bbox=bbox,
            default_collection=default_collection,
            allow_missing_bbox=resolved_aoi is not None,
        )
        if road_specs is None:
            return 400, {
                "isError": True,
                "code": "INVALID_INPUT",
                "message": roads_error or "Invalid roads",
            }
    has_explicit_road_bbox = any(road.get("bbox") is not None for road in road_specs)
    if resolved_aoi is None and bbox is None and not has_explicit_road_bbox:
        if selection_spec is not None:
            return 404, {
                "isError": True,
                "code": "AOI_NOT_RESOLVED",
                "message": "selectionSpec did not resolve any AOI geometry.",
                "warnings": aoi_warnings or [],
            }
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "Provide bbox, or selectionSpec that resolves to AOI geometry",
        }

    request_fingerprint = {
        "bbox": bbox,
        "collection": default_collection,
        "outputFormat": output_format,
        "simplifyToleranceMeters": simplify_tolerance,
        "selectionSpec": selection_spec,
        "derivationMode": derivation_mode,
        "postalDeliveryOnly": postal_delivery_only,
        "anchorBufferMeters": anchor_buffer_meters,
        "roads": road_specs,
    }
    request_hash = hashlib.sha256(_stable_json_dumps(request_fingerprint).encode("utf-8")).hexdigest()[:16]
    export_dir = _OS_EXPORTS_DIR / "road-overlays" / request_hash
    manifest_path = export_dir / "manifest.json"
    if not force_refresh:
        cached_manifest = _load_cached_roads_export(manifest_path)
        if cached_manifest is not None:
            return _roads_export_response_from_manifest(cached_manifest, cached=True)

    export_dir.mkdir(parents=True, exist_ok=True)

    roads_summary: list[dict[str, Any]] = []
    parts: list[dict[str, Any]] = []
    road_collections: dict[str, dict[str, Any]] = {}
    feature_counts: dict[str, int] = {}
    total_pages_fetched = 0
    complete = True
    aoi_manifest: dict[str, Any] | None = None

    if resolved_aoi is not None:
        query_polygons = resolved_aoi.get("queryPolygons", [])
        limit_polygons = resolved_aoi.get("limitPolygons") or []
        aoi_manifest = {
            "selectionSpec": selection_spec,
            "derivationMode": derivation_mode,
            "postalDeliveryOnly": postal_delivery_only,
            "anchorBufferMeters": anchor_buffer_meters,
            "queryPolygonCount": len(query_polygons),
            "limitPolygonCount": len(resolved_aoi.get("limitAreaPolygons", [])),
            "anchorPolygonCount": len(resolved_aoi.get("anchorPolygons", [])),
            "addressStats": resolved_aoi.get("addressStats", {}),
            "warnings": resolved_aoi.get("warnings", []),
        }
        anchor_polygons = resolved_aoi.get("anchorPolygons", [])
        if isinstance(anchor_polygons, list) and anchor_polygons:
            anchors_collection = _features_collection_from_polygons(
                name="road-export-anchors",
                polygons=anchor_polygons,
                summaries=list(resolved_aoi.get("anchorSummaries", [])),
                kind="anchor",
            )
            anchors_path = export_dir / "aoi-anchors.geojson"
            anchors_uri = _write_road_export_artifact(
                anchors_path, json.dumps(anchors_collection, ensure_ascii=True, indent=2) + "\n"
            )
            parts.append(
                {
                    "name": anchors_path.name,
                    "uri": anchors_uri,
                    "mimeType": "application/geo+json",
                    "kind": "aoi_anchor",
                }
            )
        limit_area_polygons = resolved_aoi.get("limitAreaPolygons", [])
        if isinstance(limit_area_polygons, list) and limit_area_polygons:
            limits_collection = _features_collection_from_polygons(
                name="road-export-limits",
                polygons=limit_area_polygons,
                summaries=list(resolved_aoi.get("limitSummaries", [])),
                kind="limit",
            )
            limits_path = export_dir / "aoi-limits.geojson"
            limits_uri = _write_road_export_artifact(
                limits_path, json.dumps(limits_collection, ensure_ascii=True, indent=2) + "\n"
            )
            parts.append(
                {
                    "name": limits_path.name,
                    "uri": limits_uri,
                    "mimeType": "application/geo+json",
                    "kind": "aoi_limit",
                }
            )

    for road in road_specs:
        fetched = _fetch_road_export_features(
            road,
            simplify_tolerance_meters=float(simplify_tolerance or 0.0),
            query_polygons=list(query_polygons) if resolved_aoi is not None else None,
            limit_polygons=list(limit_polygons) if resolved_aoi is not None else None,
        )
        total_pages_fetched += len(fetched["sourcePagesFetched"])
        road_complete = bool(fetched["complete"])
        complete = complete and road_complete
        feature_collection = _road_feature_collection(
            road,
            features=fetched["features"],
            complete=road_complete,
            source_pages=fetched["sourcePagesFetched"],
            warnings=fetched["warnings"],
            error=fetched["error"],
        )
        road_collections[road["label"]] = feature_collection
        feature_counts[road["label"]] = len(fetched["features"])
        geojson_filename = f"{road['slug']}.geojson"
        geojson_path = export_dir / geojson_filename
        geojson_uri = _write_road_export_artifact(
            geojson_path,
            json.dumps(feature_collection, ensure_ascii=True, indent=2) + "\n",
        )
        parts.append(
            {
                "name": geojson_filename,
                "uri": geojson_uri,
                "mimeType": "application/geo+json",
                "label": road["label"],
                "featureCount": len(fetched["features"]),
                "complete": road_complete,
            }
        )
        road_summary: dict[str, Any] = {
            "label": road["label"],
            "collection": road["collection"],
            "featureCount": len(fetched["features"]),
            "pagesFetched": len(fetched["sourcePagesFetched"]),
            "sourcePagesFetched": fetched["sourcePagesFetched"],
            "complete": road_complete,
            "warnings": fetched["warnings"],
            "partUri": geojson_uri,
            "partName": geojson_filename,
        }
        if road.get("bbox") is not None:
            road_summary["bbox"] = list(road["bbox"])
        if road.get("roadClassificationNumber") is not None:
            road_summary["roadClassificationNumber"] = road["roadClassificationNumber"]
        if road.get("cql") is not None:
            road_summary["cql"] = road["cql"]
        if fetched["error"] is not None:
            road_summary["error"] = fetched["error"]
        roads_summary.append(road_summary)

    if not any(feature_counts.values()):
        return 502, {
            "isError": True,
            "code": "UPSTREAM_FETCH_FAILED",
            "message": "Road export returned no geometry for any requested road.",
            "roads": roads_summary,
        }

    primary_uri = _os_export_uri(manifest_path.relative_to(_OS_EXPORTS_DIR).as_posix())
    if output_format == "javascript_overlay":
        js_path = export_dir / "roads-overlay.js"
        primary_uri = _write_road_export_artifact(js_path, _build_js_overlay_text(road_collections))
        parts.append(
            {
                "name": js_path.name,
                "uri": primary_uri,
                "mimeType": "application/javascript",
                "kind": "primary",
            }
        )
    elif output_format == "leaflet_snippet":
        snippet_path = export_dir / "roads-leaflet.js"
        primary_uri = _write_road_export_artifact(
            snippet_path,
            _build_leaflet_snippet_text(road_collections),
        )
        parts.append(
            {
                "name": snippet_path.name,
                "uri": primary_uri,
                "mimeType": "application/javascript",
                "kind": "primary",
            }
        )

    manifest_uri = _os_export_uri(manifest_path.relative_to(_OS_EXPORTS_DIR).as_posix())
    manifest = {
        "exportId": request_hash,
        "requestHash": request_hash,
        "createdAt": _now_iso(),
        "delivery": "resource",
        "resourceUri": manifest_uri,
        "primaryUri": primary_uri,
        "format": output_format,
        "collection": default_collection,
        "bbox": bbox,
        "featureCounts": feature_counts,
        "roads": roads_summary,
        "parts": parts,
        "aoi": aoi_manifest,
        "complete": complete,
        "sourcePagesFetched": total_pages_fetched,
    }
    _atomic_write_text(manifest_path, json.dumps(manifest, ensure_ascii=True, indent=2) + "\n")
    return _roads_export_response_from_manifest(manifest, cached=False)


def _get_latest_ngd_collection_ids() -> dict[str, str]:
    """Return cached latest-by-base collection ids from `os_features.collections`."""
    now = time.time()
    cached = _NGD_COLLECTION_CACHE.get("latest_by_base")
    stored_at = float(_NGD_COLLECTION_CACHE.get("stored_at", 0.0) or 0.0)
    if isinstance(cached, dict) and cached and now - stored_at < _NGD_COLLECTION_CACHE_TTL_SECONDS:
        return {str(k): str(v) for k, v in cached.items() if isinstance(k, str) and isinstance(v, str)}

    collections_tool = get_tool("os_features.collections")
    if not collections_tool:
        return {}
    status, data = collections_tool.call({"tool": "os_features.collections"})
    if status != 200 or not isinstance(data, dict):
        return {}
    latest = data.get("latestByBaseId")
    if not isinstance(latest, dict):
        return {}
    normalized = {
        str(base): str(coll_id)
        for base, coll_id in latest.items()
        if isinstance(base, str) and isinstance(coll_id, str)
    }
    _NGD_COLLECTION_CACHE["stored_at"] = now
    _NGD_COLLECTION_CACHE["latest_by_base"] = normalized
    return normalized


def _resolve_collection_id(layer_id: str, overrides: dict[str, str]) -> str | None:
    override = overrides.get(layer_id)
    if override:
        return override
    base = _DEFAULT_COLLECTION_BASES.get(layer_id)
    if not base:
        return None
    latest = _get_latest_ngd_collection_ids()
    return latest.get(base) or base


def _inventory(payload: dict[str, Any]) -> ToolResult:
    """Return a bounded inventory for common map layers within a bbox.

    This tool is intended for UI clients to avoid orchestrating multiple OS calls themselves.
    It enforces per-layer limits and returns truncation flags so clients can apply progressive
    disclosure (aggregate at low zoom, drill down at high zoom).
    """
    bbox = _parse_bbox(payload.get("bbox"))
    if bbox is None:
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "bbox must be [minLon,minLat,maxLon,maxLat] with min < max",
        }

    layers = _parse_layers(payload.get("layers")) or list(_DEFAULT_INVENTORY_LAYERS)
    limits = _parse_limits(payload.get("limits"))
    page_tokens = _parse_layer_tokens(payload.get("pageTokens"))
    include_geometry = _parse_bool_map(payload.get("includeGeometry"))
    collections_override = _parse_collections_override(payload.get("collections"))
    response_mode = _parse_response_mode(payload.get("responseMode"))
    if response_mode is None:
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "responseMode must be one of: full, summary, counts",
        }

    result_layers: dict[str, Any] = {}
    hints: list[str] = []

    if "uprns" in layers:
        tool = get_tool("os_places.within")
        if not tool:
            result_layers["uprns"] = {
                "isError": True,
                "code": "MISSING_TOOL",
                "message": "os_places.within not registered",
            }
        else:
            status, data = tool.call({"tool": "os_places.within", "bbox": bbox})
            if status != 200:
                result_layers["uprns"] = data
            else:
                raw_results = data.get("results") if isinstance(data, dict) else None
                if not isinstance(raw_results, list):
                    raw_results = []
                limit = limits.get("uprns", _DEFAULT_LIMITS["uprns"])
                matched_count = len(raw_results)
                sample_limit = min(limit, 10)
                truncated = matched_count > limit
                layer_payload: dict[str, Any] = {
                    "mode": response_mode,
                    "notes": (
                        ["UPRNs are sourced via OS Places bbox search; results may be truncated upstream."]
                        + (["Increase limits.uprns or zoom in for detail."] if truncated else [])
                    ),
                }
                if response_mode == "full":
                    layer_payload.update(
                        {
                            "results": raw_results[:limit],
                            "count": min(matched_count, limit),
                            "truncated": truncated,
                        }
                    )
                elif response_mode == "summary":
                    layer_payload.update(
                        {
                            "count": matched_count,
                            "sample": raw_results[:sample_limit],
                            "sampleCount": min(matched_count, sample_limit),
                            "sampleTruncated": matched_count > sample_limit,
                        }
                    )
                else:
                    layer_payload.update({"count": matched_count})
                result_layers["uprns"] = layer_payload
                if isinstance(data, dict) and isinstance(data.get("provenance"), dict):
                    result_layers["uprns"]["provenance"] = data.get("provenance")

    def _fetch_features(layer_id: str) -> None:
        if layer_id not in layers:
            return
        tool = get_tool("os_features.query")
        if not tool:
            result_layers[layer_id] = {
                "isError": True,
                "code": "MISSING_TOOL",
                "message": "os_features.query not registered",
            }
            return
        collection_id = _resolve_collection_id(layer_id, collections_override)
        if not collection_id:
            result_layers[layer_id] = {
                "isError": True,
                "code": "INVALID_INPUT",
                "message": f"No default collection mapping for layer '{layer_id}'.",
            }
            return
        limit = limits.get(layer_id, _DEFAULT_LIMITS[layer_id])
        include_geom = include_geometry.get(layer_id, True)
        req: dict[str, Any] = {
            "tool": "os_features.query",
            "collection": collection_id,
            "bbox": bbox,
            "limit": 1 if response_mode in {"summary", "counts"} else limit,
            "includeGeometry": include_geom if response_mode == "full" else False,
        }
        if response_mode in {"summary", "counts"}:
            req["resultType"] = "hits"
        token = page_tokens.get(layer_id)
        if token:
            req["pageToken"] = token
        status, data = tool.call(req)
        if status != 200:
            result_layers[layer_id] = data
            return
        if not isinstance(data, dict):
            result_layers[layer_id] = {
                "isError": True,
                "code": "INTEGRATION_ERROR",
                "message": "Expected object response from os_features.query",
            }
            return
        if response_mode == "full":
            result_layers[layer_id] = data
            # Cosmetic rename so UIs can treat layers uniformly.
            result_layers[layer_id].setdefault("layer", layer_id)
        else:
            compact_layer: dict[str, Any] = {
                "layer": layer_id,
                "mode": response_mode,
                "collection": data.get("collection"),
                "count": data.get("count"),
                "numberMatched": data.get("numberMatched"),
                "resultType": data.get("resultType"),
                "live": data.get("live", True),
            }
            if "requestedCollection" in data:
                compact_layer["requestedCollection"] = data.get("requestedCollection")
            if isinstance(data.get("hints"), dict):
                compact_layer["hints"] = data.get("hints")
            result_layers[layer_id] = compact_layer
        if response_mode == "full" and not include_geom:
            hints.append(f"{layer_id}: pass includeGeometry.{layer_id}=true to render on a map.")

    for layer_id in layers:
        if layer_id == "uprns":
            continue
        _fetch_features(layer_id)

    return 200, {
        "bbox": bbox,
        "layers": result_layers,
        "requestedLayers": layers,
        "limits": {k: limits[k] for k in layers if k in limits},
        "responseMode": response_mode,
        "hints": hints,
        "live": True,
    }


def _export_inventory_snapshot(payload: dict[str, Any]) -> ToolResult:
    bbox = _parse_bbox(payload.get("bbox"))
    if bbox is None:
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "bbox must be [minLon,minLat,maxLon,maxLat] with min < max",
        }
    name = payload.get("name")
    if name is not None and not isinstance(name, str):
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "name must be a string"}
    recipe = payload.get("recipe")
    if recipe is not None and not isinstance(recipe, dict):
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "recipe must be an object"}
    layers = _parse_layers(payload.get("layers"))
    limits = _parse_limits(payload.get("limits"))
    include_geometry = _parse_bool_map(payload.get("includeGeometry"))
    collections_override = _parse_collections_override(payload.get("collections"))

    inv_status, inv = _inventory(
        {
            "bbox": bbox,
            "layers": layers,
            "limits": limits,
            "includeGeometry": include_geometry,
            "collections": collections_override,
        }
    )
    if inv_status != 200:
        return inv_status, inv

    export_id = str(uuid.uuid4())
    _EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{export_id}.json"
    path = _EXPORTS_DIR / filename
    payload_out = {
        "exportId": export_id,
        "name": name or "",
        "createdAt": _now_iso(),
        "recipe": recipe or {},
        "inventory": inv,
    }
    _atomic_write_text(path, json.dumps(payload_out, ensure_ascii=True, indent=2) + "\n")
    uri = f"resource://mcp-geo/exports/{filename}"
    return 200, {
        "exportId": export_id,
        "uri": uri,
        "resourceUri": uri,
        "notes": [
            "Use os_resources.get or resources/read with the returned uri to fetch the exported JSON content.",
        ],
    }


def _os_export_uri(filename: str) -> str:
    return f"resource://mcp-geo/os-exports/{filename}"


def _job_status_uri(export_id: str) -> str:
    return _os_export_uri(f"jobs/{export_id}.json")


def _job_path(export_id: str) -> Path:
    normalized = _normalize_export_id(export_id)
    if not normalized:
        raise ValueError("invalid export id")
    root = _OS_EXPORT_JOBS_DIR.resolve()
    path = (root / f"{normalized}.json").resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError("invalid export id") from exc
    return path


def _read_job(export_id: str) -> dict[str, Any] | None:
    try:
        path = _job_path(export_id)
    except ValueError:
        return None
    if not path.exists() or not path.is_file():
        return None
    for _attempt in range(3):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            time.sleep(0.01)
            continue
        except Exception:
            return None
        return raw if isinstance(raw, dict) else None
    return None


def _write_job(job: dict[str, Any]) -> None:
    normalized = _normalize_export_id(job.get("exportId"))
    if not normalized:
        return
    _OS_EXPORT_JOBS_DIR.mkdir(parents=True, exist_ok=True)
    path = _job_path(normalized)
    _atomic_write_text(path, json.dumps(job, ensure_ascii=True, indent=2) + "\n")


def _membership_value(values: set[str]) -> str:
    if not values:
        return ""
    return "|".join(sorted(values))


def _fetch_index_rows_by_column(
    conn: sqlite3.Connection,
    *,
    derivation_mode: str,
    column: str,
    values: Iterable[str],
) -> dict[str, dict[str, Any]]:
    normalized_values = [str(v).strip() for v in values if str(v).strip()]
    if not normalized_values:
        return {}
    placeholders = ",".join("?" for _ in normalized_values)
    sql = (
        "SELECT uprn, postcode, oa_code, lsoa_code, msoa_code, lad_code, lad_name, "
        "ward_code, country_code, region_code, postal_delivery "
        "FROM ons_geo_uprn_index "
        f"WHERE derivation_mode = ? AND {column} IN ({placeholders})"
    )
    params: list[Any] = [derivation_mode, *normalized_values]
    rows = conn.execute(sql, params).fetchall()
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        uprn = str(row["uprn"])
        out.setdefault(
            uprn,
            {
                "uprn": uprn,
                "postcode": row["postcode"],
                "oa_code": row["oa_code"],
                "lsoa_code": row["lsoa_code"],
                "msoa_code": row["msoa_code"],
                "lad_code": row["lad_code"],
                "lad_name": row["lad_name"],
                "ward_code": row["ward_code"],
                "country_code": row["country_code"],
                "region_code": row["region_code"],
                "postal_delivery": row["postal_delivery"],
            },
        )
    return out


def _fetch_index_rows_for_uprns(
    conn: sqlite3.Connection,
    *,
    derivation_mode: str,
    uprns: Iterable[str],
) -> dict[str, dict[str, Any]]:
    uprn_list = _sort_uprns(uprns)
    if not uprn_list:
        return {}

    out: dict[str, dict[str, Any]] = {}
    chunk = 800
    for start in range(0, len(uprn_list), chunk):
        part = uprn_list[start : start + chunk]
        placeholders = ",".join("?" for _ in part)
        sql = (
            "SELECT uprn, postcode, oa_code, lsoa_code, msoa_code, lad_code, lad_name, "
            "ward_code, country_code, region_code, postal_delivery "
            "FROM ons_geo_uprn_index "
            f"WHERE derivation_mode = ? AND uprn IN ({placeholders})"
        )
        params: list[Any] = [derivation_mode, *part]
        rows = conn.execute(sql, params).fetchall()
        for row in rows:
            uprn = str(row["uprn"])
            out.setdefault(
                uprn,
                {
                    "uprn": uprn,
                    "postcode": row["postcode"],
                    "oa_code": row["oa_code"],
                    "lsoa_code": row["lsoa_code"],
                    "msoa_code": row["msoa_code"],
                    "lad_code": row["lad_code"],
                    "lad_name": row["lad_name"],
                    "ward_code": row["ward_code"],
                    "country_code": row["country_code"],
                    "region_code": row["region_code"],
                    "postal_delivery": row["postal_delivery"],
                },
            )
    return out


def _selector_membership_label(selector: dict[str, Any], fallback: str) -> str:
    selector_id = selector.get("id")
    if isinstance(selector_id, str) and selector_id.strip():
        return selector_id.strip()
    return fallback


def _resolve_polygon_selector(selector: dict[str, Any]) -> tuple[set[str], str | None]:
    geometry = selector.get("geometry")
    if not isinstance(geometry, dict):
        return set(), "polygon selector requires geometry"

    tool = get_tool("os_places.polygon")
    if not tool:
        return set(), "os_places.polygon not available for polygon selector"

    status, payload = tool.call({"tool": "os_places.polygon", "polygon": geometry, "limit": 50000})
    if status != 200:
        if isinstance(payload, dict):
            msg = str(payload.get("message") or payload.get("code") or "polygon lookup failed")
        else:
            msg = "polygon lookup failed"
        return set(), msg

    results = payload.get("results") if isinstance(payload, dict) else None
    if not isinstance(results, list):
        return set(), None

    uprns: set[str] = set()
    for row in results:
        if not isinstance(row, dict):
            continue
        raw = row.get("uprn")
        if isinstance(raw, str):
            normalized = normalize_uprn(raw)
            if normalized:
                uprns.add(normalized)
    return uprns, None


def _resolve_selection_rows(
    *,
    selection_spec: dict[str, Any],
    derivation_mode: str,
    postal_delivery_only: bool,
) -> tuple[list[dict[str, Any]], dict[str, int], list[str]]:
    cache = ONSGeoCache.from_settings()
    if not cache.available():
        raise RuntimeError("ONS geo cache is unavailable. Run scripts/ons_geo_cache_refresh.py.")

    conn = sqlite3.connect(str(cache.db_path))
    conn.row_factory = sqlite3.Row

    warnings: list[str] = []
    include_uprns: set[str] = set()
    membership: dict[str, dict[str, set[str]]] = {}

    def _mark_membership(uprn: str, column: str, value: str) -> None:
        entry = membership.setdefault(uprn, {name: set() for name in _MEMBERSHIP_COLUMNS})
        if column in entry and value:
            entry[column].add(value)

    selectors = selection_spec.get("selectors", [])
    if not isinstance(selectors, list):
        selectors = []

    for idx, selector in enumerate(selectors):
        if not isinstance(selector, dict):
            warnings.append(f"selectors[{idx}] skipped: expected object")
            continue
        selector_type = str(selector.get("type") or "").strip().lower()
        if not selector_type:
            warnings.append(f"selectors[{idx}] skipped: missing type")
            continue

        if selector_type == "gss_code":
            level = str(selector.get("level") or "").strip().upper()
            code = str(selector.get("code") or "").strip().upper()
            mapping = _GSS_LEVEL_TO_COLUMN.get(level)
            if not mapping or not code:
                warnings.append(
                    f"selectors[{idx}] skipped: gss_code requires supported level and code"
                )
                continue
            db_col, membership_col = mapping
            matches = _fetch_index_rows_by_column(
                conn,
                derivation_mode=derivation_mode,
                column=db_col,
                values=[code],
            )
            include_uprns.update(matches.keys())
            if membership_col:
                for uprn in matches:
                    _mark_membership(uprn, membership_col, code)
            continue

        if selector_type == "postcode":
            postcode_raw = selector.get("postcode")
            if not isinstance(postcode_raw, str):
                warnings.append(f"selectors[{idx}] skipped: postcode selector requires postcode")
                continue
            postcode = normalize_postcode(postcode_raw)
            if postcode is None:
                warnings.append(f"selectors[{idx}] skipped: invalid postcode")
                continue
            matches = _fetch_index_rows_by_column(
                conn,
                derivation_mode=derivation_mode,
                column="postcode",
                values=[postcode],
            )
            include_uprns.update(matches.keys())
            for uprn in matches:
                _mark_membership(uprn, "selected_by_postcode", postcode)
            continue

        if selector_type == "uprn":
            uprn_raw = selector.get("uprn")
            if not isinstance(uprn_raw, str):
                warnings.append(f"selectors[{idx}] skipped: uprn selector requires uprn")
                continue
            uprn = normalize_uprn(uprn_raw)
            if uprn is None:
                warnings.append(f"selectors[{idx}] skipped: invalid uprn")
                continue
            include_uprns.add(uprn)
            _mark_membership(
                uprn,
                "selected_by_uprn",
                _selector_membership_label(selector, uprn),
            )
            continue

        if selector_type == "polygon":
            matched, warning = _resolve_polygon_selector(selector)
            if warning:
                warnings.append(f"selectors[{idx}] polygon: {warning}")
                continue
            include_uprns.update(matched)
            label = _selector_membership_label(selector, f"polygon-{idx + 1}")
            for uprn in matched:
                _mark_membership(uprn, "selected_by_polygon", label)
            continue

        warnings.append(f"selectors[{idx}] skipped: unsupported selector type '{selector_type}'")

    uprn_overrides = selection_spec.get("uprnOverrides", {})
    include_overrides = uprn_overrides.get("include", []) if isinstance(uprn_overrides, dict) else []
    exclude_overrides = uprn_overrides.get("exclude", []) if isinstance(uprn_overrides, dict) else []

    for raw in include_overrides:
        if isinstance(raw, str):
            normalized = normalize_uprn(raw)
            if normalized:
                include_uprns.add(normalized)
                _mark_membership(normalized, "selected_by_uprn", normalized)

    exclusions: set[str] = set()
    for raw in exclude_overrides:
        if isinstance(raw, str):
            normalized = normalize_uprn(raw)
            if normalized:
                exclusions.add(normalized)

    include_uprns.difference_update(exclusions)

    indexed_rows = _fetch_index_rows_for_uprns(
        conn,
        derivation_mode=derivation_mode,
        uprns=include_uprns,
    )

    has_delivery_flags = any(
        row.get("postal_delivery") in {0, 1}
        for row in indexed_rows.values()
    )
    if postal_delivery_only:
        if has_delivery_flags:
            include_uprns = {
                uprn
                for uprn in include_uprns
                if indexed_rows.get(uprn, {}).get("postal_delivery") == 1
            }
            warnings.append("postalDeliveryOnly applied using indexed postal-delivery flags")
        else:
            warnings.append(
                "postalDeliveryOnly requested but delivery flags unavailable; export used best-effort fallback"
            )

    rows: list[dict[str, Any]] = []
    for uprn in _sort_uprns(include_uprns):
        data = indexed_rows.get(uprn, {})
        mem = membership.get(uprn, {name: set() for name in _MEMBERSHIP_COLUMNS})
        rows.append(
            {
                "uprn": uprn,
                "postcode": data.get("postcode") or "",
                "oa_code": data.get("oa_code") or "",
                "local_authority_name": data.get("lad_name") or "",
                "lsoa_code": data.get("lsoa_code") or "",
                "msoa_code": data.get("msoa_code") or "",
                "lad_code": data.get("lad_code") or "",
                "selected_by_oa": _membership_value(mem.get("selected_by_oa", set())),
                "selected_by_lsoa": _membership_value(mem.get("selected_by_lsoa", set())),
                "selected_by_msoa": _membership_value(mem.get("selected_by_msoa", set())),
                "selected_by_postcode": _membership_value(mem.get("selected_by_postcode", set())),
                "selected_by_uprn": _membership_value(mem.get("selected_by_uprn", set())),
                "selected_by_polygon": _membership_value(mem.get("selected_by_polygon", set())),
            }
        )

    conn.close()

    stats = {
        "resolvedUprnCount": len(rows),
        "selectorCount": len(selectors),
        "excludedCount": len(exclusions),
    }
    return rows, stats, warnings


def _write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    with tmp_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in columns})
    tmp_path.replace(path)


def _update_job(export_id: str, **updates: Any) -> dict[str, Any]:
    with _EXPORT_JOB_LOCK:
        current = _read_job(export_id) or {"exportId": export_id}
        current.update(updates)
        current["updatedAt"] = _now_iso()
        _write_job(current)
        return current


def _run_selection_export_job(export_id: str, payload: dict[str, Any]) -> None:
    _update_job(export_id, status="running")
    try:
        selection_spec, parse_error = _parse_selection_spec(payload.get("selectionSpec"))
        if parse_error or selection_spec is None:
            raise ValueError(parse_error or "invalid selectionSpec")

        filters = payload.get("filters", {})
        if filters is None:
            filters = {}
        if not isinstance(filters, dict):
            raise ValueError("filters must be an object")

        derivation_mode = _normalize_derivation_mode(payload.get("derivationMode"))
        columns_config = _normalize_columns_config(payload.get("columns"))
        output_columns = _csv_columns_from_config(columns_config)
        postal_delivery_only = bool(filters.get("postalDeliveryOnly", False))
        try:
            rows, stats, warnings = _resolve_selection_rows(
                selection_spec=selection_spec,
                derivation_mode=derivation_mode,
                postal_delivery_only=postal_delivery_only,
            )
        except Exception as exc:
            status, error_payload = _selection_cache_error(exc)
            raise ValueError(
                json.dumps(
                    {
                        "status": status,
                        "code": error_payload.get("code"),
                        "message": error_payload.get("message"),
                    },
                    ensure_ascii=True,
                )
            ) from exc

        file_stem = f"maplab-selection-{export_id}"
        export_format = _normalize_export_format(payload.get("format"))
        if export_format == "json":
            filename = f"{file_stem}.json"
            out_path = _OS_EXPORTS_DIR / filename
            _atomic_write_text(
                out_path,
                json.dumps(
                    {
                        "exportId": export_id,
                        "createdAt": _now_iso(),
                        "selectionSpec": selection_spec,
                        "columns": columns_config,
                        "rows": rows,
                        "stats": stats,
                        "warnings": warnings,
                    },
                    ensure_ascii=True,
                    indent=2,
                )
                + "\n",
            )
        else:
            filename = f"{file_stem}.csv"
            out_path = _OS_EXPORTS_DIR / filename
            _write_csv(out_path, rows, output_columns)

        result_uri = _os_export_uri(filename)
        _update_job(
            export_id,
            status="completed",
            completedAt=_now_iso(),
            resultUri=result_uri,
            rowCount=len(rows),
            columns=columns_config,
            stats=stats,
            warnings=warnings,
            path=str(out_path),
        )
    except Exception as exc:  # pragma: no cover - guarded by tests via get_export status
        code = "EXPORT_FAILED"
        message = str(exc)
        try:
            payload = json.loads(message)
        except json.JSONDecodeError:
            payload = None
        if isinstance(payload, dict):
            code = str(payload.get("code") or code)
            message = str(payload.get("message") or message)
        _update_job(
            export_id,
            status="failed",
            failedAt=_now_iso(),
            error={"message": message, "code": code},
        )


def _start_selection_export(payload: dict[str, Any]) -> ToolResult:
    selection_spec, parse_error = _parse_selection_spec(payload.get("selectionSpec"))
    if parse_error or selection_spec is None:
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": parse_error or "selectionSpec is required",
        }

    columns = payload.get("columns", {})
    if columns is not None and not isinstance(columns, dict):
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "columns must be an object"}
    filters = payload.get("filters", {})
    if filters is not None and not isinstance(filters, dict):
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "filters must be an object"}

    export_id = str(uuid.uuid4())
    created_at = _now_iso()
    job = {
        "exportId": export_id,
        "status": "queued",
        "exportType": "selection_uprn",
        "createdAt": created_at,
        "updatedAt": created_at,
        "statusUri": _job_status_uri(export_id),
        "resultUri": None,
        "request": {
            "selectionSpec": selection_spec,
            "format": _normalize_export_format(payload.get("format")),
            "columns": _normalize_columns_config(columns),
            "filters": filters or {"postalDeliveryOnly": False},
            "derivationMode": _normalize_derivation_mode(payload.get("derivationMode")),
        },
    }
    _write_job(job)

    worker = threading.Thread(
        target=_run_selection_export_job,
        kwargs={"export_id": export_id, "payload": dict(payload)},
        daemon=True,
        name=f"os-map-export-{export_id[:8]}",
    )
    worker.start()

    return 200, {
        "exportId": export_id,
        "status": "queued",
        "statusUri": _job_status_uri(export_id),
        "resultUri": None,
    }


def _export(payload: dict[str, Any]) -> ToolResult:
    export_type = str(payload.get("exportType") or "inventory_snapshot").strip().lower()
    if export_type == "selection_uprn":
        return _start_selection_export(payload)
    return _export_inventory_snapshot(payload)


def _get_export(payload: dict[str, Any]) -> ToolResult:
    export_id = payload.get("exportId")
    normalized = _normalize_export_id(export_id)
    if not normalized:
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "exportId must be a UUID string",
        }
    job = _read_job(normalized)
    if not job:
        return 404, {
            "isError": True,
            "code": "NOT_FOUND",
            "message": f"Export job not found for {normalized}",
        }
    job.setdefault("statusUri", _job_status_uri(normalized))
    return 200, job


register(
    Tool(
        name="os_map.export_roads",
        description=(
            "Export complete road overlay artifacts server-side from road numbers and/or "
            "selectionSpec-derived AOIs, including all upstream pages and semantic parts."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "os_map.export_roads"},
                "bbox": {
                    "type": "array",
                    "items": {"type": "number"},
                    "minItems": 4,
                    "maxItems": 4,
                    "description": (
                        "Optional fallback WGS84 bbox [minLon,minLat,maxLon,maxLat]. "
                        "Prefer selectionSpec for postcode, UPRN, GSS-code, or polygon AOIs."
                    ),
                },
                "collection": {
                    "type": "string",
                    "description": "Optional default NGD collection id.",
                },
                "roads": {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                        "type": "object",
                        "properties": {
                            "label": {"type": "string"},
                            "bbox": {
                                "type": "array",
                                "items": {"type": "number"},
                                "minItems": 4,
                                "maxItems": 4,
                            },
                            "collection": {"type": "string"},
                            "roadClassificationNumber": {"type": ["string", "null"]},
                            "cql": {"type": "string"},
                        },
                        "required": ["label"],
                        "additionalProperties": False,
                    },
                },
                "selectionSpec": {
                    "type": "object",
                    "description": (
                        "Selector-driven AOI definition. Supports postcode, uprn, gss_code, "
                        "and polygon selectors plus uprnOverrides."
                    ),
                },
                "derivationMode": {
                    "type": "string",
                    "enum": ["exact", "best_fit"],
                    "default": "exact",
                },
                "postalDeliveryOnly": {"type": "boolean"},
                "anchorBufferMeters": {
                    "type": "number",
                    "minimum": 0,
                    "description": (
                        "Optional buffer applied around resolved building anchors before "
                        "fetching RoadLinks."
                    ),
                },
                "outputFormat": {
                    "type": "string",
                    "enum": ["geojson_bundle", "javascript_overlay", "leaflet_snippet"],
                    "default": "geojson_bundle",
                },
                "simplifyToleranceMeters": {"type": "number", "minimum": 0},
                "forceRefresh": {"type": "boolean"},
            },
            "required": [],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "exportId": {"type": "string"},
                "requestHash": {"type": "string"},
                "delivery": {"type": "string"},
                "resourceUri": {"type": "string"},
                "primaryUri": {"type": "string"},
                "format": {"type": "string"},
                "collection": {"type": ["string", "null"]},
                "bbox": {
                    "type": ["array", "null"],
                    "items": {"type": "number"},
                    "minItems": 4,
                    "maxItems": 4,
                },
                "featureCounts": {"type": "object"},
                "roads": {"type": "array", "items": {"type": "object"}},
                "parts": {"type": "array", "items": {"type": "object"}},
                "aoi": {"type": ["object", "null"]},
                "complete": {"type": "boolean"},
                "sourcePagesFetched": {"type": "integer"},
                "cached": {"type": "boolean"},
            },
            "required": ["exportId", "delivery", "resourceUri", "format", "featureCounts", "complete"],
            "additionalProperties": True,
        },
        handler=_export_roads,
    )
)

register(
    Tool(
        name="os_map.inventory",
        description="Return a bounded inventory (UPRNs, buildings, road links, path links) for a bbox.",
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "os_map.inventory"},
                "bbox": {
                    "type": "array",
                    "items": {"type": "number"},
                    "minItems": 4,
                    "maxItems": 4,
                    "description": "WGS84 bbox [minLon,minLat,maxLon,maxLat]",
                },
                "layers": {
                    "oneOf": [
                        {"type": "array", "items": {"type": "string"}, "minItems": 1},
                        {"type": "string", "minLength": 1},
                        {"type": "null"},
                    ],
                    "description": _LAYER_DESCRIPTION,
                },
                "limits": {"type": "object", "description": "Per-layer max features (budgets)."},
                "pageTokens": {"type": "object", "description": "Per-layer paging tokens for NGD layers."},
                "includeGeometry": {
                    "type": "object",
                    "description": "Per-layer includeGeometry overrides (NGD layers only).",
                },
                "responseMode": {
                    "type": "string",
                    "enum": ["full", "summary", "counts"],
                    "default": "full",
                    "description": (
                        "Use summary or counts to avoid large raw payloads when only a compact "
                        "layer summary is needed."
                    ),
                },
                "collections": {
                    "type": "object",
                    "description": "Per-layer NGD collection id overrides (NGD layers only).",
                },
            },
            "required": ["bbox"],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "bbox": {
                    "type": "array",
                    "items": {"type": "number"},
                    "minItems": 4,
                    "maxItems": 4,
                },
                "layers": {"type": "object"},
                "requestedLayers": {"type": "array", "items": {"type": "string"}},
                "limits": {"type": "object"},
                "responseMode": {"type": "string"},
                "hints": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["layers"],
            "additionalProperties": True,
        },
        handler=_inventory,
    )
)

register(
    Tool(
        name="os_map.export",
        description=(
            "Export a map artifact. "
            "Legacy mode exports inventory snapshots from bbox; selection_uprn mode queues async "
            "selector-driven UPRN exports."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "os_map.export"},
                "exportType": {
                    "type": "string",
                    "enum": ["inventory_snapshot", "selection_uprn"],
                    "default": "inventory_snapshot",
                },
                "bbox": {
                    "type": "array",
                    "items": {"type": "number"},
                    "minItems": 4,
                    "maxItems": 4,
                },
                "name": {"type": "string"},
                "recipe": {"type": "object"},
                "layers": {
                    "oneOf": [
                        {"type": "array", "items": {"type": "string"}, "minItems": 1},
                        {"type": "string", "minLength": 1},
                        {"type": "null"},
                    ],
                    "description": _LAYER_DESCRIPTION,
                },
                "limits": {"type": "object"},
                "includeGeometry": {"type": "object"},
                "collections": {"type": "object"},
                "selectionSpec": {"type": "object"},
                "format": {"type": "string", "enum": ["csv", "json"]},
                "columns": {"type": "object"},
                "filters": {"type": "object"},
                "delivery": {"type": "string", "enum": ["resource", "auto", "inline"]},
                "derivationMode": {"type": "string", "enum": ["exact", "best_fit"]},
            },
            "required": [],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "exportId": {"type": "string"},
                "uri": {"type": "string"},
                "path": {"type": "string"},
                "notes": {"type": "array", "items": {"type": "string"}},
                "status": {"type": "string"},
                "statusUri": {"type": "string"},
                "resultUri": {"type": ["string", "null"]},
            },
            "required": ["exportId"],
            "additionalProperties": True,
        },
        handler=_export,
    )
)

register(
    Tool(
        name="os_map.get_export",
        description="Get async export status for a selector-driven os_map.export job.",
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "os_map.get_export"},
                "exportId": {"type": "string"},
            },
            "required": ["exportId"],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "exportId": {"type": "string"},
                "status": {"type": "string"},
                "statusUri": {"type": "string"},
                "resultUri": {"type": ["string", "null"]},
                "error": {"type": ["object", "null"]},
                "warnings": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["exportId", "status"],
            "additionalProperties": True,
        },
        handler=_get_export,
    )
)
