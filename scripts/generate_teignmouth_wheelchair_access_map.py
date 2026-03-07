#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
from collections import Counter, defaultdict
from html import escape
from pathlib import Path
from typing import Any, Callable, Iterable

import server.mcp.tools  # noqa: F401
from tools.os_delivery import os_exports_dir
from tools.registry import get as get_tool

REPO_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = REPO_ROOT / "docs" / "reports"
EXPORTS_DIR = REPO_ROOT / "data" / "exports"

ROAD_COLLECTION = "trn-ntwk-roadlink-5"
PATH_COLLECTION = "trn-ntwk-pathlink-3"
WATER_COLLECTION = "wtr-fts-water-3"
RAIL_COLLECTION = "trn-fts-cartographicraildetail-1"
PAVEMENT_COLLECTION = "trn-fts-roadtrackorpath-3"

ROAD_FIELDS = [
    "name1_text",
    "geometry_length_m",
    "roadwidth_average",
    "presenceofpavement_averagewidth_m",
    "presenceofpavement_minimumwidth_m",
    "presenceofpavement_overallpercentage",
    "presenceofstreetlight_coverage",
    "elevationgain_indirection",
    "elevationgain_againstdirection",
]

PATH_FIELDS = [
    "pathname1_text",
    "description",
    "surfacetype",
    "geometry_length_m",
    "presenceofstreetlight_coverage",
    "elevationgain_indirection",
    "elevationgain_againstdirection",
]

PAVEMENT_FIELDS = ["description"]
WATER_FIELDS = ["description"]
RAIL_FIELDS = ["description"]

LIT_GOOD = {"Fully Lit", "Mostly Lit"}

PLACE_PRESETS: dict[str, dict[str, Any]] = {
    "teignmouth": {
        "slug": "teignmouth",
        "place_name": "Teignmouth",
        "bbox": [-3.5025, 50.5405, -3.4905, 50.5495],
        "title": "Teignmouth town-centre wheelchair access map",
        "subtitle": (
            "Conservative MCP-Geo route filter for a Quantum iLevel user. Width, slope, "
            "lighting, and pedestrian-path evidence are shown. Hover a coloured route in "
            "HTML for details. Dropped kerbs and crossing quality are not."
        ),
        "rail_note": "Railway line and station edge",
        "anchors": [
            {
                "label": "Teignmouth station",
                "query": "teignmouth railway station",
                "tool": "os_places.search",
            },
            {
                "label": "Shopmobility",
                "query": "teignmouth shopmobility",
                "tool": "os_places.search",
            },
        ],
        "callout_priority": {
            "Promenade": 0,
            "Bitton Park Road": 1,
            "Higher Brook Street": 2,
            "Regents Gardens": 3,
            "CLAMPET LANE": 4,
            "Riverside Walk": 5,
            "East Cliff": 6,
            "Quay Road": 7,
            "STANLEY STREET": 8,
        },
    },
    "exmouth": {
        "slug": "exmouth",
        "place_name": "Exmouth",
        "bbox": [-3.4215, 50.6095, -3.3960, 50.6238],
        "title": "Exmouth town-centre wheelchair access map",
        "subtitle": (
            "Conservative MCP-Geo route filter for a Quantum iLevel user. This comparison "
            "tests the station-to-town-centre-to-seafront core using width, slope, lighting, "
            "and pedestrian-path evidence. Hover a coloured route in HTML for details. "
            "Dropped kerbs and crossing quality are not."
        ),
        "rail_note": "Railway line and station edge",
        "anchors": [
            {
                "label": "Exmouth railway station",
                "query": "exmouth railway station",
                "tool": "os_poi.search",
            },
            {
                "label": "Exmouth indoor market",
                "query": "exmouth indoor market",
                "tool": "os_poi.search",
            },
        ],
        "callout_priority": {
            "Imperial Road": 0,
            "The Strand": 1,
            "Queen Street": 2,
            "Alexandra Terrace": 3,
            "Esplanade": 4,
            "Queens Drive": 5,
            "Rolle Street": 6,
            "Manchester Road": 7,
            "The Beacon": 8,
        },
    },
    "sidmouth": {
        "slug": "sidmouth",
        "place_name": "Sidmouth",
        "bbox": [-3.2445, 50.6760, -3.2330, 50.6826],
        "title": "Sidmouth town-centre wheelchair access map",
        "subtitle": (
            "Conservative MCP-Geo route filter for a Quantum iLevel user. This comparison "
            "tests Sidmouth's market-square to seafront core using width, slope, lighting, "
            "and pedestrian-path evidence. Hover a coloured route in HTML for details. "
            "Dropped kerbs and crossing quality are not."
        ),
        "rail_note": "Seafront and river edge context",
        "anchors": [
            {
                "label": "Tourist Information Centre",
                "query": "sidmouth tourist information",
                "tool": "os_poi.search",
            },
            {
                "label": "Sidmouth Market",
                "query": "sidmouth market place",
                "tool": "os_poi.search",
            },
        ],
        "callout_priority": {
            "The Esplanade": 0,
            "Ham Lane": 1,
            "Market Place": 2,
            "High Street": 3,
            "Station Road": 4,
            "All Saints Road": 5,
            "Peak Hill Road": 6,
            "Mill Street": 7,
            "Church Street": 8,
        },
    },
}

DEFAULT_PRESET = "teignmouth"
OS_EXPORT_RESOURCE_PREFIX = "resource://mcp-geo/os-exports/"

SLIDE_WIDTH = 1600
SLIDE_HEIGHT = 900
MAP_X = 56
MAP_Y = 96
MAP_W = 1110
MAP_H = 748
MAP_PAD = 18
PANEL_X = 1210
PANEL_Y = 96
PANEL_W = 324
PANEL_H = 748
TILE_SIZE_PX = 256
OS_LIGHT_STYLE = "Light_3857"
OS_LIGHT_TILE_URL_TEMPLATE = (
    "https://api.os.uk/maps/raster/v1/zxy/Light_3857/{z}/{x}/{y}.png?key=__OS_API_KEY__"
)
OS_BROWSER_KEY_STORAGE = "mcpGeo.osApiKey"
EARTH_CIRCUMFERENCE_M = 40_075_016.686


def _call_tool(name: str, payload: dict[str, Any]) -> dict[str, Any]:
    tool = get_tool(name)
    if tool is None:
        raise RuntimeError(f"Tool not registered: {name}")
    status, data = tool.call(payload)
    if status != 200 or not isinstance(data, dict):
        raise RuntimeError(f"{name} failed: status={status} data={data}")
    return data


def _fetch_features(
    collection: str,
    bbox: list[float],
    *,
    fields: list[str],
    include_geometry: bool = True,
) -> list[dict[str, Any]]:
    token: str | None = None
    features: list[dict[str, Any]] = []
    while True:
        payload: dict[str, Any] = {
            "tool": "os_features.query",
            "collection": collection,
            "bbox": bbox,
            "limit": 100,
            "includeGeometry": include_geometry,
        }
        if fields:
            payload["includeFields"] = fields
        if token:
            payload["pageToken"] = token
        data = _call_tool("os_features.query", payload)
        page = data.get("features")
        if not isinstance(page, list) and data.get("delivery") == "resource":
            resource_uri = data.get("resourceUri")
            if isinstance(resource_uri, str) and resource_uri.startswith(OS_EXPORT_RESOURCE_PREFIX):
                export_name = resource_uri.removeprefix(OS_EXPORT_RESOURCE_PREFIX)
                export_path = os_exports_dir() / export_name
                export_payload = json.loads(export_path.read_text(encoding="utf-8"))
                page = export_payload.get("features")
        if not isinstance(page, list):
            raise RuntimeError(f"os_features.query returned invalid features for {collection}")
        features.extend(page)
        token = data.get("nextPageToken")
        if not token:
            break
    return features


def _search_anchor(query: str, bbox: list[float], tool_name: str) -> dict[str, Any]:
    payload: dict[str, Any] = {"tool": tool_name, "limit": 25}
    if tool_name == "os_places.search":
        payload["text"] = query
    elif tool_name == "os_poi.search":
        payload["text"] = query
        payload["bbox"] = bbox
    else:
        raise RuntimeError(f"Unsupported anchor lookup tool: {tool_name}")

    data = _call_tool(tool_name, payload)
    results = data.get("results")
    if not isinstance(results, list) or not results:
        raise RuntimeError(f"{tool_name} returned no results for {query!r}")
    min_lon, min_lat, max_lon, max_lat = bbox
    for item in results:
        if not isinstance(item, dict):
            continue
        lat = item.get("lat")
        lon = item.get("lon")
        if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
            if min_lon <= lon <= max_lon and min_lat <= lat <= max_lat:
                return item
    for item in results:
        if isinstance(item, dict) and isinstance(item.get("lat"), (int, float)):
            return item
    raise RuntimeError(f"{tool_name} returned no geocoded result for {query!r}")


def _meters_per_lon_degree(lat: float) -> float:
    return 111320.0 * math.cos(math.radians(lat))


def _distance_m(a: tuple[float, float], b: tuple[float, float], mean_lat: float) -> float:
    lon_scale = _meters_per_lon_degree(mean_lat)
    return math.hypot((b[0] - a[0]) * lon_scale, (b[1] - a[1]) * 111320.0)


def _worst_grade_pct(props: dict[str, Any]) -> float | None:
    length = props.get("geometry_length_m")
    try:
        length_m = float(length)
    except (TypeError, ValueError):
        return None
    if length_m <= 0:
        return None
    gain = max(
        float(props.get("elevationgain_indirection") or 0.0),
        float(props.get("elevationgain_againstdirection") or 0.0),
    )
    return (gain / length_m) * 100.0


def _classify_road(props: dict[str, Any]) -> tuple[str, list[str]]:
    reasons: list[str] = []
    min_width = props.get("presenceofpavement_minimumwidth_m")
    avg_width = props.get("presenceofpavement_averagewidth_m")
    pavement_pct = props.get("presenceofpavement_overallpercentage")
    lighting = str(props.get("presenceofstreetlight_coverage") or "").strip()
    grade = _worst_grade_pct(props)

    if grade is not None and grade > 5.0:
        return "unverified", ["steep_grade"]

    if min_width is None or avg_width is None or pavement_pct is None:
        return "unverified", ["missing_pavement_data"]

    min_width_m = float(min_width)
    avg_width_m = float(avg_width)
    pavement_pct_f = float(pavement_pct)

    if pavement_pct_f < 50.0:
        return "unverified", ["low_pavement_coverage"]
    if min_width_m < 0.9:
        return "unverified", ["very_narrow_pavement"]

    if (
        min_width_m >= 1.2
        and avg_width_m >= 1.8
        and pavement_pct_f >= 80.0
        and (grade is None or grade < 3.0)
        and lighting in LIT_GOOD
    ):
        return "preferred", []

    if (
        min_width_m >= 1.0
        and avg_width_m >= 1.4
        and pavement_pct_f >= 60.0
        and (grade is None or grade <= 5.0)
    ):
        reasons.extend(
            reason
            for condition, reason in [
                (min_width_m < 1.2, "pinch_point"),
                (avg_width_m < 1.8, "average_width_tight"),
                (pavement_pct_f < 80.0, "partial_pavement"),
                (lighting not in LIT_GOOD, "daylight_preferred"),
                (grade is not None and grade >= 3.0, "moderate_grade"),
            ]
            if condition
        )
        return "care", reasons

    return "unverified", ["below_threshold"]


def _classify_path(props: dict[str, Any]) -> tuple[str, list[str]]:
    description = str(props.get("description") or "").strip()
    surface = str(props.get("surfacetype") or "").strip()
    lighting = str(props.get("presenceofstreetlight_coverage") or "").strip()
    grade = _worst_grade_pct(props)

    if description == "Path With Steps":
        return "barrier", ["steps"]
    if description == "Footbridge":
        return "barrier", ["footbridge"]
    if description == "Subway":
        return "barrier", ["subway"]
    if grade is not None and grade > 5.0:
        return "barrier", ["steep_grade"]

    if surface == "Made Sealed" and description == "Path" and (grade is None or grade < 3.0):
        if lighting in LIT_GOOD:
            return "preferred", []
        return "care", ["daylight_preferred"]

    if description == "Path" and surface in {"Made Sealed", "Made Unsealed", "Unmade"}:
        if grade is None or grade <= 5.0:
            reasons: list[str] = []
            if surface != "Made Sealed":
                reasons.append("surface_check")
            if lighting not in LIT_GOOD:
                reasons.append("daylight_preferred")
            if grade is not None and grade >= 3.0:
                reasons.append("moderate_grade")
            return "care", reasons

    return "unverified", ["surface_or_type_unknown"]


def _midpoint(coords: list[list[float]], mean_lat: float) -> tuple[float, float]:
    if len(coords) == 1:
        return coords[0][0], coords[0][1]
    target = 0.0
    lengths: list[float] = []
    for start, end in zip(coords, coords[1:]):
        length = _distance_m((start[0], start[1]), (end[0], end[1]), mean_lat)
        lengths.append(length)
        target += length
    target /= 2.0
    seen = 0.0
    for idx, length in enumerate(lengths):
        if seen + length >= target and length > 0:
            ratio = (target - seen) / length
            start = coords[idx]
            end = coords[idx + 1]
            return (
                start[0] + (end[0] - start[0]) * ratio,
                start[1] + (end[1] - start[1]) * ratio,
            )
        seen += length
    last = coords[-1]
    return last[0], last[1]


def _distance_point_to_polyline_m(
    point: tuple[float, float],
    coords: list[list[float]],
    mean_lat: float,
) -> float:
    lon_scale = _meters_per_lon_degree(mean_lat)
    px = point[0] * lon_scale
    py = point[1] * 111320.0
    best = float("inf")
    for start, end in zip(coords, coords[1:]):
        ax = start[0] * lon_scale
        ay = start[1] * 111320.0
        bx = end[0] * lon_scale
        by = end[1] * 111320.0
        dx = bx - ax
        dy = by - ay
        if dx == 0 and dy == 0:
            dist = math.hypot(px - ax, py - ay)
        else:
            t = ((px - ax) * dx + (py - ay) * dy) / ((dx * dx) + (dy * dy))
            t = max(0.0, min(1.0, t))
            proj_x = ax + t * dx
            proj_y = ay + t * dy
            dist = math.hypot(px - proj_x, py - proj_y)
        if dist < best:
            best = dist
    return best


def _mercator_x_normalized(lon: float) -> float:
    return (lon + 180.0) / 360.0


def _mercator_y_normalized(lat: float) -> float:
    clipped = max(-85.05112878, min(85.05112878, lat))
    sin_lat = math.sin(math.radians(clipped))
    return 0.5 - (math.log((1.0 + sin_lat) / (1.0 - sin_lat)) / (4.0 * math.pi))


def _map_layout(
    bbox: list[float],
    *,
    x: float = MAP_X,
    y: float = MAP_Y,
    width: float = MAP_W,
    height: float = MAP_H,
    pad: float = MAP_PAD,
) -> dict[str, float]:
    min_lon, min_lat, max_lon, max_lat = bbox
    min_x_norm = _mercator_x_normalized(min_lon)
    max_x_norm = _mercator_x_normalized(max_lon)
    top_y_norm = _mercator_y_normalized(max_lat)
    bottom_y_norm = _mercator_y_normalized(min_lat)
    world_w = max_x_norm - min_x_norm
    world_h = bottom_y_norm - top_y_norm
    inner_w = width - (2 * pad)
    inner_h = height - (2 * pad)
    scale = min(inner_w / world_w, inner_h / world_h)
    extra_x = (inner_w - (world_w * scale)) / 2.0
    extra_y = (inner_h - (world_h * scale)) / 2.0
    return {
        "x": x,
        "y": y,
        "width": width,
        "height": height,
        "pad": pad,
        "scale": scale,
        "extra_x": extra_x,
        "extra_y": extra_y,
        "min_x_norm": min_x_norm,
        "max_x_norm": max_x_norm,
        "top_y_norm": top_y_norm,
        "bottom_y_norm": bottom_y_norm,
    }


def _projector(
    bbox: list[float],
    *,
    x: float = MAP_X,
    y: float = MAP_Y,
    width: float = MAP_W,
    height: float = MAP_H,
    pad: float = MAP_PAD,
) -> Callable[[float, float], tuple[float, float]]:
    layout = _map_layout(bbox, x=x, y=y, width=width, height=height, pad=pad)

    def project(lon: float, lat: float) -> tuple[float, float]:
        px = (
            layout["x"]
            + layout["pad"]
            + layout["extra_x"]
            + ((_mercator_x_normalized(lon) - layout["min_x_norm"]) * layout["scale"])
        )
        py = (
            layout["y"]
            + layout["pad"]
            + layout["extra_y"]
            + ((_mercator_y_normalized(lat) - layout["top_y_norm"]) * layout["scale"])
        )
        return round(px, 1), round(py, 1)

    return project


def _choose_basemap_zoom(
    bbox: list[float],
    *,
    width: float = MAP_W,
    height: float = MAP_H,
    pad: float = MAP_PAD,
    overscale: float = 1.35,
    min_zoom: int = 12,
    max_zoom: int = 18,
    max_tiles: int = 30,
) -> int:
    layout = _map_layout(bbox, width=width, height=height, pad=pad)
    span_x = layout["max_x_norm"] - layout["min_x_norm"]
    span_y = layout["bottom_y_norm"] - layout["top_y_norm"]
    inner_w = width - (2 * pad)
    inner_h = height - (2 * pad)
    zoom_x = math.log2((inner_w * overscale) / (TILE_SIZE_PX * span_x))
    zoom_y = math.log2((inner_h * overscale) / (TILE_SIZE_PX * span_y))
    zoom = max(min_zoom, min(max_zoom, math.floor(min(zoom_x, zoom_y))))
    while zoom > min_zoom:
        world_px = TILE_SIZE_PX * (2**zoom)
        min_px = layout["min_x_norm"] * world_px
        max_px = layout["max_x_norm"] * world_px
        top_py = layout["top_y_norm"] * world_px
        bottom_py = layout["bottom_y_norm"] * world_px
        tile_count = (
            (math.floor(max_px / TILE_SIZE_PX) - math.floor(min_px / TILE_SIZE_PX) + 1)
            * (math.floor(bottom_py / TILE_SIZE_PX) - math.floor(top_py / TILE_SIZE_PX) + 1)
        )
        if tile_count <= max_tiles:
            break
        zoom -= 1
    return zoom


def _build_basemap_tiles(bbox: list[float]) -> dict[str, Any]:
    layout = _map_layout(bbox)
    zoom = _choose_basemap_zoom(bbox)
    world_px = TILE_SIZE_PX * (2**zoom)
    min_px = layout["min_x_norm"] * world_px
    max_px = layout["max_x_norm"] * world_px
    top_py = layout["top_y_norm"] * world_px
    bottom_py = layout["bottom_y_norm"] * world_px
    tile_x_min = math.floor(min_px / TILE_SIZE_PX)
    tile_x_max = math.floor(max_px / TILE_SIZE_PX)
    tile_y_min = math.floor(top_py / TILE_SIZE_PX)
    tile_y_max = math.floor(bottom_py / TILE_SIZE_PX)
    tiles: list[dict[str, Any]] = []
    for tile_x in range(tile_x_min, tile_x_max + 1):
        for tile_y in range(tile_y_min, tile_y_max + 1):
            tile_min_x_norm = (tile_x * TILE_SIZE_PX) / world_px
            tile_max_x_norm = ((tile_x + 1) * TILE_SIZE_PX) / world_px
            tile_top_y_norm = (tile_y * TILE_SIZE_PX) / world_px
            tile_bottom_y_norm = ((tile_y + 1) * TILE_SIZE_PX) / world_px
            left = (
                layout["x"]
                + layout["pad"]
                + layout["extra_x"]
                + ((tile_min_x_norm - layout["min_x_norm"]) * layout["scale"])
            )
            right = (
                layout["x"]
                + layout["pad"]
                + layout["extra_x"]
                + ((tile_max_x_norm - layout["min_x_norm"]) * layout["scale"])
            )
            top = (
                layout["y"]
                + layout["pad"]
                + layout["extra_y"]
                + ((tile_top_y_norm - layout["top_y_norm"]) * layout["scale"])
            )
            bottom = (
                layout["y"]
                + layout["pad"]
                + layout["extra_y"]
                + ((tile_bottom_y_norm - layout["top_y_norm"]) * layout["scale"])
            )
            tiles.append(
                {
                    "z": zoom,
                    "x": tile_x,
                    "y": tile_y,
                    "left": round(left, 1),
                    "top": round(top, 1),
                    "width": round(right - left, 1),
                    "height": round(bottom - top, 1),
                }
            )
    return {
        "style": OS_LIGHT_STYLE,
        "zoom": zoom,
        "storage_key": OS_BROWSER_KEY_STORAGE,
        "tile_url_template": OS_LIGHT_TILE_URL_TEMPLATE,
        "tiles": tiles,
    }


def _scale_bar_spec(bbox: list[float], *, target_px: float = 220.0) -> dict[str, float | str]:
    layout = _map_layout(bbox)
    center_lat = (bbox[1] + bbox[3]) / 2.0
    meters_per_px = (EARTH_CIRCUMFERENCE_M * math.cos(math.radians(center_lat))) / layout["scale"]
    max_length_m = target_px * meters_per_px
    exponent = math.floor(math.log10(max_length_m))
    fraction = max_length_m / (10**exponent)
    if fraction >= 5:
        nice = 5
    elif fraction >= 2:
        nice = 2
    else:
        nice = 1
    length_m = nice * (10**exponent)
    width_px = length_m / meters_per_px
    if length_m >= 1000:
        label = f"{length_m / 1000:.1f} km"
    else:
        label = f"{int(length_m)} m"
    return {
        "length_m": length_m,
        "width_px": round(width_px, 1),
        "half_width_px": round(width_px / 2.0, 1),
        "label": label,
        "half_label": f"{int(length_m / 2)} m" if length_m < 1000 else f"{length_m / 2000:.2f} km",
    }


def _line_path(coords: list[list[float]], project: Callable[[float, float], tuple[float, float]]) -> str:
    points = [project(lon, lat) for lon, lat in coords]
    if not points:
        return ""
    head = f"M {points[0][0]} {points[0][1]}"
    tail = " ".join(f"L {x} {y}" for x, y in points[1:])
    return f"{head} {tail}".strip()


def _polygon_path(
    rings: list[list[list[float]]],
    project: Callable[[float, float], tuple[float, float]],
) -> str:
    parts: list[str] = []
    for ring in rings:
        if not ring:
            continue
        points = [project(lon, lat) for lon, lat in ring]
        head = f"M {points[0][0]} {points[0][1]}"
        tail = " ".join(f"L {x} {y}" for x, y in points[1:])
        parts.append(f"{head} {tail} Z".strip())
    return " ".join(parts)


def _geom_paths(
    geometry: dict[str, Any],
    project: Callable[[float, float], tuple[float, float]],
) -> list[str]:
    gtype = geometry.get("type")
    coords = geometry.get("coordinates")
    if gtype == "LineString" and isinstance(coords, list):
        return [_line_path(coords, project)]
    if gtype == "MultiLineString" and isinstance(coords, list):
        return [_line_path(line, project) for line in coords if isinstance(line, list)]
    if gtype == "Polygon" and isinstance(coords, list):
        return [_polygon_path(coords, project)]
    if gtype == "MultiPolygon" and isinstance(coords, list):
        return [_polygon_path(poly, project) for poly in coords if isinstance(poly, list)]
    return []


def _route_widths(segment: dict[str, Any]) -> tuple[float, float]:
    props = segment.get("properties", {})
    if segment.get("kind") == "road":
        try:
            road_width = float(props.get("roadwidth_average") or 0.0)
        except (TypeError, ValueError):
            road_width = 0.0
        core = max(2.6, min(4.0, 1.9 + (road_width * 0.18)))
    else:
        core = 2.6 if segment.get("status") == "preferred" else 2.4
    if segment.get("status") == "barrier":
        core = min(core, 2.4)
    outline = core + 1.8
    return round(core, 1), round(outline, 1)


def _segment_title(segment: dict[str, Any]) -> str:
    status_map = {
        "preferred": "Preferred route",
        "care": "Use with care",
        "barrier": "Barrier in data",
        "unverified": "Context only",
    }
    name = str(segment.get("name") or "").strip()
    if not name:
        name = "Unnamed pedestrian path" if segment.get("kind") == "path" else "Unnamed road segment"
    props = segment.get("properties", {})
    parts = [name, status_map.get(segment.get("status"), "Route")]

    grade = segment.get("worst_grade_pct")
    if isinstance(grade, (int, float)):
        parts.append(f"grade up to {grade:.1f}%")

    lighting = props.get("presenceofstreetlight_coverage")
    if lighting:
        parts.append(str(lighting))

    if segment.get("kind") == "road":
        min_width = props.get("presenceofpavement_minimumwidth_m")
        avg_width = props.get("presenceofpavement_averagewidth_m")
        if isinstance(min_width, (int, float)):
            parts.append(f"minimum pavement {float(min_width):.2f} m")
        if isinstance(avg_width, (int, float)):
            parts.append(f"average pavement {float(avg_width):.2f} m")
    else:
        description = props.get("description")
        surface = props.get("surfacetype")
        if description:
            parts.append(str(description))
        if surface:
            parts.append(str(surface))

    reasons = segment.get("reasons") or []
    if reasons:
        parts.append("notes: " + ", ".join(str(reason).replace("_", " ") for reason in reasons))

    return " | ".join(parts)


def _select_callouts(
    segments: list[dict[str, Any]],
    bbox: list[float],
    project: Callable[[float, float], tuple[float, float]],
    callout_priority: dict[str, int],
) -> list[dict[str, Any]]:
    min_lon, min_lat, max_lon, max_lat = bbox
    mean_lat = (min_lat + max_lat) / 2.0
    status_rank = {"preferred": 0, "care": 1, "barrier": 2, "unverified": 3}
    by_name: dict[str, dict[str, Any]] = {}
    for segment in segments:
        name = str(segment.get("name") or "").strip()
        if not name:
            continue
        if name.upper() == "THE STREET WITH NO NAME":
            continue
        length_m = float(segment.get("length_m") or 0.0)
        if length_m < 18.0:
            continue
        key = name.casefold()
        current = by_name.get(key)
        if current is None:
            by_name[key] = segment
            continue
        candidate_order = (
            status_rank.get(str(segment.get("status")), 9),
            -length_m,
            name,
        )
        current_order = (
            status_rank.get(str(current.get("status")), 9),
            -float(current.get("length_m") or 0.0),
            str(current.get("name") or ""),
        )
        if candidate_order < current_order:
            by_name[key] = segment

    candidates = sorted(
        by_name.values(),
        key=lambda item: (
            callout_priority.get(str(item["name"]), 999),
            0 if item["status"] == "preferred" else 1,
            -float(item["length_m"]),
            item["name"],
        ),
    )
    slot_map: dict[str, list[tuple[float, float]]] = {
        "left": [
            (MAP_X + 104, MAP_Y + 196),
            (MAP_X + 118, MAP_Y + 350),
            (MAP_X + 132, MAP_Y + 618),
        ],
        "top": [
            (MAP_X + 408, MAP_Y + 94),
            (MAP_X + 660, MAP_Y + 96),
        ],
        "right": [
            (MAP_X + MAP_W - 192, MAP_Y + 138),
            (MAP_X + MAP_W - 184, MAP_Y + 268),
            (MAP_X + MAP_W - 206, MAP_Y + 640),
        ],
        "bottom": [
            (MAP_X + 560, MAP_Y + MAP_H - 34),
            (MAP_X + 758, MAP_Y + MAP_H - 36),
        ],
    }
    chosen: list[dict[str, Any]] = []
    for candidate in candidates:
        lon, lat = _midpoint(candidate["geometry"]["coordinates"], mean_lat)
        if not (min_lon <= lon <= max_lon and min_lat <= lat <= max_lat):
            continue
        px, py = project(lon, lat)
        if py < MAP_Y + 30 or py > MAP_Y + MAP_H - 24:
            continue
        if any(math.hypot(px - callout["target_x"], py - callout["target_y"]) < 88 for callout in chosen):
            continue

        if px < MAP_X + (MAP_W * 0.34):
            side = "left"
        elif px > MAP_X + (MAP_W * 0.72):
            side = "right"
        elif py < MAP_Y + (MAP_H * 0.34):
            side = "top"
        else:
            side = "bottom"

        side_order = [side, "right", "left", "bottom", "top"]
        slot: tuple[float, float] | None = None
        chosen_side = side
        for side_name in side_order:
            options = slot_map.get(side_name, [])
            if options:
                slot = options.pop(0)
                chosen_side = side_name
                break
        if slot is None:
            continue

        chosen.append(
            {
                "name": candidate["name"],
                "status": candidate["status"],
                "x": slot[0],
                "y": slot[1],
                "side": chosen_side,
                "target_x": px,
                "target_y": py,
            }
        )
        if len(chosen) >= 6:
            break
    return chosen


def _format_length_km(value_m: float) -> str:
    return f"{value_m / 1000.0:.2f} km"


def _tile(label: str, value: str, tone: str) -> str:
    return f"""
      <div class="metric metric-{tone}">
        <span class="metric-label">{escape(label)}</span>
        <strong>{escape(value)}</strong>
      </div>
    """


def _access_row(anchor: dict[str, Any]) -> str:
    return f"""
      <div class="access-row">
        <div class="access-badge">{anchor["index"]}</div>
        <div>
          <strong>{escape(anchor["label"])}</strong>
          <span>{round(anchor["nearest_access_m"])} m to nearest cleared route</span>
        </div>
      </div>
    """


def _legend_row(color: str, dash: str, label: str, body: str) -> str:
    dash_attr = f'stroke-dasharray="{dash}"' if dash else ""
    return f"""
      <div class="legend-row">
        <svg width="54" height="18" viewBox="0 0 54 18" aria-hidden="true">
          <line x1="4" y1="9" x2="50" y2="9" stroke="rgba(19, 32, 36, 0.28)" stroke-width="7.2" stroke-linecap="round" {dash_attr} />
          <line x1="4" y1="9" x2="50" y2="9" stroke="{color}" stroke-width="3.2" stroke-linecap="round" {dash_attr} />
        </svg>
        <div>
          <strong>{escape(label)}</strong>
          <span>{escape(body)}</span>
        </div>
      </div>
    """


def _render_html(payload: dict[str, Any]) -> str:
    bbox = payload["bbox"]
    project = _projector(bbox)
    basemap = payload["basemap"]
    scale_bar = _scale_bar_spec(bbox)
    water_paths = [
        path
        for feature in payload["context"]["water"]
        for path in _geom_paths(feature["geometry"], project)
    ]
    pavement_paths = [
        path
        for feature in payload["context"]["pavements"]
        for path in _geom_paths(feature["geometry"], project)
    ]
    road_background_paths = [
        path
        for feature in payload["display"]["background_roads"]
        for path in _geom_paths(feature["geometry"], project)
    ]
    path_background_paths = [
        path
        for feature in payload["display"]["background_paths"]
        for path in _geom_paths(feature["geometry"], project)
    ]
    rail_paths = [
        path
        for feature in payload["context"]["rail"]
        for path in _geom_paths(feature["geometry"], project)
    ]
    callouts = _select_callouts(
        payload["display"]["preferred"] + payload["display"]["care"],
        bbox,
        project,
        payload["callout_priority"],
    )

    def route_svg(features: list[dict[str, Any]], css_class: str) -> str:
        chunks: list[str] = []
        for feature in features:
            title = escape(_segment_title(feature))
            core_width, outline_width = _route_widths(feature)
            for path in _geom_paths(feature["geometry"], project):
                if not path:
                    continue
                chunks.append(
                    f"""
                    <g class="route-group {css_class}" style="--route-core-width:{core_width}px; --route-outline-width:{outline_width}px;">
                      <path d="{path}" class="route-outline"><title>{title}</title></path>
                      <path d="{path}" class="route-core"><title>{title}</title></path>
                    </g>
                    """
                )
        return "\n".join(chunks)

    preferred_line_svg = route_svg(payload["display"]["preferred"], "route-preferred")
    care_line_svg = route_svg(payload["display"]["care"], "route-care")
    barrier_line_svg = route_svg(payload["display"]["barriers"], "route-barrier")
    road_background_svg = "\n".join(
        f'<path d="{path}" class="road-context" />' for path in road_background_paths if path
    )
    path_background_svg = "\n".join(
        f'<path d="{path}" class="path-context" />' for path in path_background_paths if path
    )
    rail_svg = "\n".join(f'<path d="{path}" class="rail-line" />' for path in rail_paths if path)
    water_svg = "\n".join(f'<path d="{path}" class="water-fill" />' for path in water_paths if path)
    pavement_svg = "\n".join(
        f'<path d="{path}" class="pavement-fill" />' for path in pavement_paths if path
    )
    basemap_tile_svg = "\n".join(
        (
            f'<image x="{tile["left"]}" y="{tile["top"]}" width="{tile["width"]}" '
            f'height="{tile["height"]}" preserveAspectRatio="none" class="os-tile" '
            f'data-tile-src-template="{basemap["tile_url_template"].format(z=tile["z"], x=tile["x"], y=tile["y"])}" />'
        )
        for tile in basemap["tiles"]
    )

    callout_svg_parts: list[str] = []
    for callout in callouts:
        chip_w = max(104, len(callout["name"]) * 7.4 + 26)
        chip_h = 28
        chip_x = callout["x"]
        chip_y = callout["y"] - (chip_h / 2)
        text_x = chip_x + 14
        text_y = callout["y"]
        side = callout["side"]
        target_x = callout["target_x"]
        target_y = callout["target_y"]
        if side == "left":
            anchor_x = chip_x + chip_w
            anchor_y = callout["y"]
        elif side == "right":
            anchor_x = chip_x
            anchor_y = callout["y"]
        elif side == "top":
            anchor_x = chip_x + (chip_w / 2)
            anchor_y = chip_y + chip_h
        else:
            anchor_x = chip_x + (chip_w / 2)
            anchor_y = chip_y
        path = f"M {target_x} {target_y} L {anchor_x} {anchor_y}"
        callout_svg_parts.append(
            f"""
            <g class="callout callout-{callout['status']}">
              <path d="{path}" class="callout-line" />
              <circle cx="{target_x}" cy="{target_y}" r="4.6" class="callout-target" />
              <rect x="{chip_x}" y="{chip_y}" width="{chip_w}" height="{chip_h}" rx="11" class="callout-chip" />
              <text x="{text_x}" y="{text_y}" class="callout-text">{escape(callout['name'])}</text>
            </g>
            """
        )
    callout_svg = "\n".join(callout_svg_parts)

    anchor_svg_parts: list[str] = []
    for anchor in payload["anchors"]:
        lon = anchor["lon"]
        lat = anchor["lat"]
        px, py = project(lon, lat)
        anchor_svg_parts.append(
            f"""
            <g class="anchor">
              <circle cx="{px}" cy="{py}" r="12.5" class="anchor-ring" />
              <circle cx="{px}" cy="{py}" r="8.5" class="anchor-dot" />
              <text x="{px}" y="{py + 0.5}" class="anchor-index">{anchor["index"]}</text>
              <title>{escape(anchor['address'])}</title>
            </g>
            """
        )
    anchor_svg = "\n".join(anchor_svg_parts)

    metrics = payload["metrics"]
    preferred_total = _format_length_km(metrics["lengths_m"]["preferred"])
    care_total = _format_length_km(metrics["lengths_m"]["care"])
    barrier_total = _format_length_km(metrics["lengths_m"]["barrier"])
    anchor_check_text = "; ".join(
        f"{anchor['label']} about {round(anchor['nearest_access_m'])} m"
        for anchor in payload["anchors"]
    )

    scale_bar_x = MAP_X + 34
    scale_bar_y = MAP_Y + MAP_H - 34
    north_x = MAP_X + MAP_W - 54
    north_y = MAP_Y + 28

    metrics_html = "\n".join(
        [
            _tile("Preferred routes", preferred_total, "preferred"),
            _tile("Use with care", care_total, "care"),
            _tile("Barriers flagged", barrier_total, "barrier"),
            _tile("Pavement polygons", str(metrics["counts"]["pavements"]), "neutral"),
        ]
    )
    legends_html = "\n".join(
        [
            _legend_row(
                "#0d7d7f",
                "",
                "Preferred route",
                "Cleared pavement or sealed path, gentle slope, better lighting.",
            ),
            _legend_row(
                "#d08c1f",
                "",
                "Use with care",
                "Pinch point, moderate slope, or weaker lighting.",
            ),
            _legend_row(
                "#c64d3d",
                "12 10",
                "Barrier in data",
                "Steps, footbridge, subway, or steep path section.",
            ),
            _legend_row(
                "#9aa4aa",
                "",
                "Context only",
                "Shown for orientation. It did not clear the wheelchair route filter.",
            ),
        ]
    )
    access_html = "\n".join(_access_row(anchor) for anchor in payload["anchors"])

    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{escape(payload['title'])}</title>
    <style>
      :root {{
        color-scheme: light;
        font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
        --slide-scale: 1;
      }}

      * {{
        box-sizing: border-box;
      }}

      body {{
        margin: 0;
        background: linear-gradient(180deg, #eef3f2 0%, #dfe8e6 100%);
        color: #132024;
      }}

      .page {{
        min-height: 100vh;
        display: grid;
        place-items: center;
        padding: 16px;
        overflow: auto;
      }}

      .slide-shell {{
        position: relative;
        width: calc({SLIDE_WIDTH}px * var(--slide-scale));
        height: calc({SLIDE_HEIGHT}px * var(--slide-scale));
      }}

      .slide {{
        position: relative;
        width: {SLIDE_WIDTH}px;
        height: {SLIDE_HEIGHT}px;
        border-radius: 28px;
        background: #f7f4ee;
        box-shadow: 0 26px 60px rgba(24, 45, 53, 0.18);
        overflow: hidden;
        transform: scale(var(--slide-scale));
        transform-origin: top left;
      }}

      .title {{
        position: absolute;
        left: 56px;
        top: 36px;
      }}

      .title h1 {{
        margin: 0;
        font-size: 34px;
        line-height: 1.05;
        letter-spacing: -0.03em;
      }}

      .title p {{
        margin: 10px 0 0 0;
        max-width: 780px;
        color: #42575f;
        font-size: 14px;
      }}

      .map-frame {{
        position: absolute;
        left: {MAP_X}px;
        top: {MAP_Y}px;
        width: {MAP_W}px;
        height: {MAP_H}px;
        border-radius: 24px;
        background: linear-gradient(180deg, #e8f0ef 0%, #edf0e9 100%);
        border: 1px solid #d2d8d3;
        overflow: hidden;
      }}

      .map-controls {{
        position: absolute;
        left: 18px;
        top: 18px;
        z-index: 4;
        display: flex;
        gap: 8px;
        align-items: center;
      }}

      .mode-group {{
        display: flex;
        align-items: center;
        gap: 6px;
        padding: 6px;
        border-radius: 999px;
        background: rgba(255, 252, 245, 0.94);
        border: 1px solid rgba(19, 56, 64, 0.12);
        backdrop-filter: blur(10px);
      }}

      .mode-label {{
        padding: 0 6px 0 8px;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #50636a;
      }}

      .mode-button {{
        appearance: none;
        border: 0;
        border-radius: 999px;
        padding: 9px 14px;
        background: rgba(236, 232, 222, 0.9);
        color: #17333a;
        font: inherit;
        font-size: 12px;
        font-weight: 600;
        cursor: pointer;
      }}

      .mode-button.is-active {{
        background: #173840;
        color: #ffffff;
      }}

      .mode-key {{
        background: rgba(255, 252, 245, 0.94);
        border: 1px solid rgba(19, 56, 64, 0.12);
      }}

      .map-status {{
        position: absolute;
        left: 18px;
        top: 70px;
        z-index: 4;
        max-width: 420px;
        padding: 8px 12px;
        border-radius: 14px;
        background: rgba(255, 252, 245, 0.92);
        border: 1px solid rgba(19, 56, 64, 0.12);
        color: #4f636a;
        font-size: 11px;
        line-height: 1.35;
        backdrop-filter: blur(10px);
      }}

      .map-status[data-tone="warning"] {{
        background: rgba(255, 243, 225, 0.95);
        color: #7a4f12;
      }}

      .map-status[data-tone="success"] {{
        background: rgba(238, 247, 244, 0.95);
        color: #175153;
      }}

      .panel {{
        position: absolute;
        left: {PANEL_X}px;
        top: {PANEL_Y}px;
        width: {PANEL_W}px;
        height: {PANEL_H}px;
        padding: 18px 18px 16px 18px;
        border-radius: 24px;
        background: #fffdf8;
        border: 1px solid #ddd5c8;
        display: flex;
        flex-direction: column;
        gap: 10px;
      }}

      .metric {{
        min-height: 66px;
        padding: 9px 11px;
        border-radius: 18px;
        border: 1px solid #d9d1c4;
        background: #fcfaf5;
      }}

      .metric strong {{
        display: block;
        margin-top: 5px;
        font-size: 20px;
        line-height: 1;
        letter-spacing: -0.03em;
      }}

      .metric-label {{
        font-size: 11px;
        color: #50626b;
      }}

      .metric-preferred {{
        background: #edf7f5;
      }}

      .metric-care {{
        background: #fff4df;
      }}

      .metric-barrier {{
        background: #fff0ee;
      }}

      .metric-neutral {{
        background: #f3f1eb;
      }}

      .panel h2 {{
        margin: 0;
        font-size: 15px;
        line-height: 1.2;
      }}

      .metrics-grid {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px;
      }}

      .legend-block {{
        display: grid;
        gap: 12px;
      }}

      .access-block {{
        display: grid;
        gap: 10px;
      }}

      .access-row {{
        display: grid;
        grid-template-columns: 30px 1fr;
        gap: 10px;
        align-items: start;
      }}

      .access-badge {{
        width: 30px;
        height: 30px;
        border-radius: 999px;
        display: grid;
        place-items: center;
        background: #173840;
        color: #ffffff;
        font-size: 12px;
        font-weight: 700;
      }}

      .access-row strong {{
        display: block;
        font-size: 11px;
      }}

      .access-row span {{
        display: block;
        margin-top: 2px;
        font-size: 10px;
        line-height: 1.35;
        color: #53646c;
      }}

      .legend-row {{
        display: grid;
        grid-template-columns: 58px 1fr;
        gap: 10px;
        align-items: start;
      }}

      .legend-row strong {{
        display: block;
        font-size: 11px;
      }}

      .legend-row span {{
        display: block;
        margin-top: 2px;
        font-size: 10px;
        line-height: 1.35;
        color: #53646c;
      }}

      .checks {{
        margin-top: 2px;
      }}

      .checks h2 {{
        margin: 0 0 8px 0;
      }}

      .checks ul {{
        margin: 0;
        padding-left: 16px;
        color: #42575f;
        font-size: 10.5px;
        line-height: 1.35;
      }}

      .checks li + li {{
        margin-top: 5px;
      }}

      .source-note {{
        margin-top: auto;
        padding-top: 10px;
        border-top: 1px solid #e4dccd;
        color: #617078;
        font-size: 9px;
        line-height: 1.35;
      }}

      .map-svg {{
        width: 100%;
        height: 100%;
        display: block;
      }}

      .slide[data-basemap="simplified"] .basemap-os {{
        opacity: 0;
      }}

      .slide[data-basemap="os-light"] .simple-context {{
        opacity: 0;
      }}

      .slide[data-basemap="os-light"] .basemap-os {{
        opacity: 1;
      }}

      .simple-context,
      .basemap-os {{
        transition: opacity 160ms ease;
      }}

      .basemap-os {{
        opacity: 0;
      }}

      .os-tile {{
        pointer-events: none;
      }}

      .water-fill {{
        fill: #c9e5ef;
        stroke: #96bfcc;
        stroke-width: 1;
      }}

      .pavement-fill {{
        fill: #eee6d8;
        stroke: none;
        opacity: 0.66;
      }}

      .road-context {{
        fill: none;
        stroke: #bbb4aa;
        stroke-width: 2.1;
        stroke-linecap: round;
        stroke-linejoin: round;
      }}

      .path-context {{
        fill: none;
        stroke: #cdc6bd;
        stroke-width: 1.4;
        stroke-linecap: round;
        stroke-linejoin: round;
        stroke-dasharray: 4 7;
      }}

      .rail-line {{
        fill: none;
        stroke: #57656c;
        stroke-width: 2.4;
        stroke-linecap: round;
        stroke-linejoin: round;
        stroke-dasharray: 18 10;
      }}

      .route-group {{
        cursor: help;
      }}

      .route-outline,
      .route-core {{
        fill: none;
        stroke-linecap: round;
        stroke-linejoin: round;
        pointer-events: stroke;
      }}

      .route-outline {{
        stroke-width: var(--route-outline-width, 4.6px);
      }}

      .route-core {{
        stroke-width: var(--route-core-width, 2.8px);
      }}

      .route-preferred .route-outline {{
        stroke: rgba(8, 42, 43, 0.24);
      }}

      .route-preferred .route-core {{
        stroke: #0d7d7f;
      }}

      .route-care .route-outline {{
        stroke: rgba(94, 67, 19, 0.24);
      }}

      .route-care .route-core {{
        stroke: #d08c1f;
      }}

      .route-barrier .route-outline {{
        stroke: rgba(98, 42, 34, 0.22);
        stroke-dasharray: 10 8;
      }}

      .route-barrier .route-core {{
        stroke: #c64d3d;
        stroke-dasharray: 10 8;
      }}

      .anchor-dot {{
        fill: #143840;
      }}

      .anchor-ring {{
        fill: none;
        stroke: rgba(20, 56, 64, 0.2);
        stroke-width: 8;
      }}

      .anchor-chip {{
        fill: rgba(19, 56, 64, 0.92);
      }}

      .anchor-index {{
        fill: #ffffff;
        font-size: 10px;
        font-weight: 600;
        dominant-baseline: central;
        text-anchor: middle;
        pointer-events: none;
      }}

      .callout-line {{
        fill: none;
        stroke: #90a0a7;
        stroke-width: 2;
        stroke-linecap: round;
        stroke-linejoin: round;
      }}

      .callout-chip {{
        fill: rgba(255, 252, 245, 0.97);
        stroke: rgba(19, 56, 64, 0.12);
      }}

      .callout-target {{
        fill: #ffffff;
        stroke: #17333a;
        stroke-width: 1.5;
      }}

      .callout-text {{
        font-size: 12px;
        font-weight: 600;
        fill: #17333a;
        dominant-baseline: central;
      }}

      .callout-care .callout-chip {{
        fill: rgba(255, 246, 228, 0.97);
      }}

      .north-label {{
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.14em;
        fill: #17333a;
      }}

      .map-note {{
        font-size: 12px;
        fill: #4f646b;
      }}

      .scale-label {{
        font-size: 11px;
        fill: #17333a;
      }}

      .scale-label-start {{
        text-anchor: start;
      }}

      .scale-label-middle {{
        text-anchor: middle;
      }}

      .scale-label-end {{
        text-anchor: end;
      }}

      .os-key-dialog {{
        width: min(420px, calc(100vw - 32px));
        padding: 0;
        border: 0;
        border-radius: 22px;
        box-shadow: 0 22px 54px rgba(18, 33, 39, 0.28);
      }}

      .os-key-dialog::backdrop {{
        background: rgba(17, 31, 35, 0.32);
      }}

      .os-key-form {{
        display: grid;
        gap: 12px;
        padding: 24px;
        background: #fffdf8;
      }}

      .os-key-form h2 {{
        margin: 0;
        font-size: 22px;
        line-height: 1.05;
      }}

      .os-key-form p {{
        margin: 0;
        color: #4d6168;
        font-size: 13px;
        line-height: 1.45;
      }}

      .os-key-label {{
        font-size: 12px;
        font-weight: 600;
      }}

      .os-key-input {{
        width: 100%;
        padding: 12px 14px;
        border: 1px solid #cfd5d0;
        border-radius: 14px;
        font: inherit;
        font-size: 13px;
      }}

      .os-key-actions {{
        display: flex;
        justify-content: flex-end;
        gap: 10px;
        flex-wrap: wrap;
      }}

      .dialog-button {{
        appearance: none;
        border: 0;
        border-radius: 999px;
        padding: 10px 16px;
        font: inherit;
        font-size: 12px;
        font-weight: 600;
        cursor: pointer;
      }}

      .dialog-button-ghost {{
        background: #ede8de;
        color: #17333a;
      }}

      .dialog-button-primary {{
        background: #173840;
        color: #ffffff;
      }}
    </style>
  </head>
  <body>
    <div class="page">
      <div class="slide-shell">
      <article class="slide" data-basemap="simplified">
        <header class="title">
          <h1>{escape(payload['title'])}</h1>
          <p>
            {escape(payload['subtitle'])}
          </p>
        </header>

        <section class="map-frame" aria-label="Wheelchair access map">
          <div class="map-controls">
            <div class="mode-group" role="group" aria-label="Map context">
              <span class="mode-label">Context</span>
              <button type="button" class="mode-button is-active" data-basemap-mode="simplified">Simplified</button>
              <button type="button" class="mode-button" data-basemap-mode="os-light">OS Light</button>
            </div>
            <button type="button" class="mode-button mode-key" data-open-os-key>OS key</button>
          </div>
          <div class="map-status" data-basemap-status>
            Simplified context is shown. OS Light loads when a browser key is set.
          </div>
          <svg class="map-svg" viewBox="0 0 {MAP_W} {MAP_H}" role="img" aria-label="{escape(payload['title'])}">
            <g transform="translate(-{MAP_X}, -{MAP_Y})">
              <g class="basemap-os">
                {basemap_tile_svg}
              </g>
              <g class="simple-context">
                {water_svg}
                {pavement_svg}
                {road_background_svg}
                {path_background_svg}
                {rail_svg}
              </g>
              {preferred_line_svg}
              {care_line_svg}
              {barrier_line_svg}
              {callout_svg}
              {anchor_svg}
              <g transform="translate({north_x}, {north_y})">
                <text x="0" y="-8" class="north-label">N</text>
                <path d="M 0 0 L 12 28 L 0 22 L -12 28 Z" fill="#17333a" />
              </g>
              <g transform="translate({scale_bar_x}, {scale_bar_y})">
                <line x1="0" y1="0" x2="{scale_bar['width_px']}" y2="0" stroke="#17333a" stroke-width="4" stroke-linecap="round" />
                <line x1="0" y1="-7" x2="0" y2="7" stroke="#17333a" stroke-width="2" />
                <line x1="{scale_bar['half_width_px']}" y1="-7" x2="{scale_bar['half_width_px']}" y2="7" stroke="#17333a" stroke-width="2" />
                <line x1="{scale_bar['width_px']}" y1="-7" x2="{scale_bar['width_px']}" y2="7" stroke="#17333a" stroke-width="2" />
                <text x="0" y="-12" class="scale-label scale-label-start">0</text>
                <text x="{scale_bar['half_width_px']}" y="-12" class="scale-label scale-label-middle">{escape(str(scale_bar['half_label']))}</text>
                <text x="{scale_bar['width_px']}" y="-12" class="scale-label scale-label-end">{escape(str(scale_bar['label']))}</text>
              </g>
              <text x="{MAP_X + 30}" y="{MAP_Y + 100}" class="map-note">{escape(payload['rail_note'])}</text>
            </g>
          </svg>
        </section>

        <aside class="panel">
          <h2>Read this map</h2>
          <div class="metrics-grid">
            {metrics_html}
          </div>

          <div class="legend-block">
            {legends_html}
          </div>

          <section class="access-block">
            <h2>Access points</h2>
            {access_html}
          </section>

          <section class="checks">
            <h2>Check before travel</h2>
            <ul>
              <li>Grey streets are context only. They did not clear the wheelchair route filter.</li>
              <li>Final approach still needs checking: {escape(anchor_check_text)}.</li>
              <li>Not captured in current data: dropped kerbs, crossing type, tactile paving, parked cars, bins, café furniture, or temporary works.</li>
              <li>In HTML, hover a coloured route for evidence text and use the OS Light toggle for street-name context when a browser-stored key is available.</li>
            </ul>
          </section>

          <div class="source-note">
            Live MCP-Geo extract on {escape(payload['generated_on'])}: roads, paths, pavement polygons,
            rail detail, water context, and named anchors. Route filter uses UK accessible-footway guidance,
            a conservative 5% maximum grade rule, and optional OS Light browser tiles for map context.
          </div>
        </aside>
      </article>
      </div>
    </div>
    <dialog class="os-key-dialog" id="os-key-dialog">
      <form method="dialog" class="os-key-form">
        <h2>Load OS Light basemap</h2>
        <p>
          Enter your OS Maps API key to request `Light_3857` tiles directly from Ordnance Survey.
          The key is stored only in this browser on this machine and is never written into the report file.
        </p>
        <label class="os-key-label" for="os-key-input">OS Maps API key</label>
        <input id="os-key-input" class="os-key-input" data-os-key-input type="password" autocomplete="off" />
        <div class="os-key-actions">
          <button type="button" class="dialog-button dialog-button-ghost" data-clear-os-key>Clear saved key</button>
          <button value="cancel" class="dialog-button dialog-button-ghost">Cancel</button>
          <button type="button" class="dialog-button dialog-button-primary" data-save-os-key>Use OS Light</button>
        </div>
      </form>
    </dialog>
    <script>
      (() => {{
        const root = document.documentElement;
        const slide = document.querySelector(".slide");
        const modeButtons = Array.from(document.querySelectorAll("[data-basemap-mode]"));
        const statusEl = document.querySelector("[data-basemap-status]");
        const openKeyButton = document.querySelector("[data-open-os-key]");
        const dialog = document.getElementById("os-key-dialog");
        const keyInput = dialog?.querySelector("[data-os-key-input]");
        const saveKeyButton = dialog?.querySelector("[data-save-os-key]");
        const clearKeyButton = dialog?.querySelector("[data-clear-os-key]");
        const osTiles = Array.from(document.querySelectorAll(".os-tile"));
        const storageKey = {json.dumps(OS_BROWSER_KEY_STORAGE)};
        let osApiKey = "";
        let osTilesHydrated = false;

        const fit = () => {{
          const availableWidth = Math.max(320, window.innerWidth - 32);
          const scale = Math.min(1, availableWidth / {SLIDE_WIDTH});
          root.style.setProperty("--slide-scale", scale.toFixed(4));
        }};
        const setStatus = (text, tone = "info") => {{
          if (!statusEl) {{
            return;
          }}
          statusEl.textContent = text;
          statusEl.dataset.tone = tone;
        }};
        const syncButtons = (mode) => {{
          modeButtons.forEach((button) => {{
            button.classList.toggle("is-active", button.dataset.basemapMode === mode);
          }});
        }};
        const clearTileRefs = () => {{
          osTiles.forEach((tile) => {{
            tile.removeAttribute("href");
            tile.removeAttributeNS("http://www.w3.org/1999/xlink", "href");
          }});
          osTilesHydrated = false;
        }};
        const hydrateTiles = () => {{
          if (!osApiKey || osTilesHydrated) {{
            return;
          }}
          osTiles.forEach((tile) => {{
            const template = tile.dataset.tileSrcTemplate || "";
            const url = template.replace("__OS_API_KEY__", encodeURIComponent(osApiKey));
            tile.setAttribute("href", url);
            tile.setAttributeNS("http://www.w3.org/1999/xlink", "href", url);
          }});
          osTilesHydrated = true;
        }};
        const fallbackPrompt = () => {{
          const value = window.prompt("Enter your OS Maps API key for the OS Light basemap", osApiKey);
          if (value === null) {{
            return false;
          }}
          const trimmed = value.trim();
          if (!trimmed) {{
            setStatus("Enter a valid OS Maps API key to load the OS Light basemap.", "warning");
            return false;
          }}
          osApiKey = trimmed;
          window.localStorage.setItem(storageKey, osApiKey);
          clearTileRefs();
          hydrateTiles();
          return true;
        }};
        const openKeyDialog = () => {{
          if (!(dialog instanceof HTMLDialogElement) || typeof dialog.showModal !== "function") {{
            if (fallbackPrompt()) {{
              setMode("os-light", {{ allowDialog: false }});
            }}
            return;
          }}
          if (keyInput instanceof HTMLInputElement) {{
            keyInput.value = osApiKey;
          }}
          dialog.showModal();
        }};
        const setMode = (mode, options = {{}}) => {{
          const allowDialog = options.allowDialog !== false;
          if (!slide) {{
            return;
          }}
          if (mode === "os-light") {{
            if (!osApiKey) {{
              slide.dataset.basemap = "simplified";
              syncButtons("simplified");
              setStatus("OS Light needs your OS Maps API key in this browser. Use OS key.", "warning");
              if (allowDialog) {{
                openKeyDialog();
              }}
              return;
            }}
            hydrateTiles();
            slide.dataset.basemap = "os-light";
            syncButtons("os-light");
            setStatus("Loading OS Light basemap under the route markup...", "info");
            return;
          }}
          slide.dataset.basemap = "simplified";
          syncButtons("simplified");
          if (osApiKey) {{
            setStatus("Simplified context is shown. OS Light is ready in this browser.", "info");
          }} else {{
            setStatus("Simplified context is shown. OS Light loads when a browser key is set.", "info");
          }}
        }};

        fit();
        window.addEventListener("resize", fit);
        try {{
          osApiKey = window.localStorage.getItem(storageKey) || "";
        }} catch (_error) {{
          osApiKey = "";
        }}
        modeButtons.forEach((button) => {{
          button.addEventListener("click", () => {{
            setMode(button.dataset.basemapMode || "simplified");
          }});
        }});
        openKeyButton?.addEventListener("click", openKeyDialog);
        saveKeyButton?.addEventListener("click", () => {{
          if (!(keyInput instanceof HTMLInputElement)) {{
            if (fallbackPrompt()) {{
              if (dialog instanceof HTMLDialogElement) {{
                dialog.close();
              }}
              setMode("os-light", {{ allowDialog: false }});
            }}
            return;
          }}
          const trimmed = keyInput.value.trim();
          if (!trimmed) {{
            setStatus("Enter a valid OS Maps API key to load the OS Light basemap.", "warning");
            keyInput.focus();
            return;
          }}
          osApiKey = trimmed;
          window.localStorage.setItem(storageKey, osApiKey);
          clearTileRefs();
          hydrateTiles();
          if (dialog instanceof HTMLDialogElement) {{
            dialog.close();
          }}
          setMode("os-light", {{ allowDialog: false }});
        }});
        clearKeyButton?.addEventListener("click", () => {{
          osApiKey = "";
          try {{
            window.localStorage.removeItem(storageKey);
          }} catch (_error) {{
            // ignore storage failures and keep the simplified view available
          }}
          clearTileRefs();
          if (dialog instanceof HTMLDialogElement) {{
            dialog.close();
          }}
          setMode("simplified", {{ allowDialog: false }});
          setStatus("Saved OS Maps API key cleared. Simplified context is shown.", "info");
        }});
        osTiles.forEach((tile) => {{
          tile.addEventListener("load", () => {{
            if (slide?.dataset.basemap === "os-light") {{
              setStatus("OS Light basemap is shown under the route markup.", "success");
            }}
          }});
          tile.addEventListener("error", () => {{
            if (slide?.dataset.basemap === "os-light") {{
              setStatus("One or more OS tiles failed to load. Check the key or switch back to Simplified.", "warning");
            }}
          }});
        }});
        setMode("simplified", {{ allowDialog: false }});
      }})();
    </script>
  </body>
</html>
"""


def _top_named_segments(
    payload: dict[str, Any],
    *,
    status: str,
    kind: str,
    limit: int = 5,
) -> list[str]:
    totals: defaultdict[str, float] = defaultdict(float)
    for segment in payload["segments"]:
        if segment.get("status") != status or segment.get("kind") != kind:
            continue
        name = str(segment.get("name") or "").strip()
        if not name or name.upper() == "THE STREET WITH NO NAME":
            continue
        totals[name] += float(segment.get("length_m") or 0.0)
    ranked = sorted(totals.items(), key=lambda item: (-item[1], item[0]))
    return [name for name, _ in ranked[:limit]]


def _format_name_list(names: list[str]) -> str:
    if not names:
        return "No stable named segments cleared this category in the current extract."
    return ", ".join(f"`{name}`" for name in names)


def _render_note(payload: dict[str, Any]) -> str:
    counts = payload["metrics"]["counts"]
    lengths = payload["metrics"]["lengths_m"]
    anchor_lines = "\n".join(
        f"- `{anchor['label']}` is about `{round(anchor['nearest_access_m'])} m` "
        "from the nearest cleared route segment."
        for anchor in payload["anchors"]
    )
    anchor_tools = ", ".join(f"`{tool}`" for tool in payload["anchor_tools"])
    slug = payload["slug"]
    date = payload["generated_on"]
    place_name = payload["place_name"]
    return f"""# {place_name} wheelchair access map

Generated artefacts:

- HTML map: `docs/reports/{slug}_wheelchair_access_map_{date}.html`
- JSON export: `data/exports/{slug}_wheelchair_access_map_{date}.json`
- PNG render: `output/playwright/{slug}-wheelchair-access-map-{date}.png`

## Scope

This map is a conservative town-centre access aid for a powered wheelchair user in {place_name}.
It uses live MCP-Geo extracts from `{date}` and focuses on what the current data can validate:

- road links with recorded pavement width and pavement coverage
- path links with path type, surface, lighting coverage, and elevation gain
- pavement polygons for pedestrian-realm context
- rail and water geometry for orientation
- exact named anchors from search tools

The HTML report also includes an optional `OS Light` basemap toggle. That layer loads
browser-side from Ordnance Survey when the user supplies an OS Maps API key locally.

It does **not** claim to validate dropped kerbs, crossing design, tactile paving, camber,
temporary obstructions, parked cars, café furniture, or works on the day.

## Current MCP-Geo data used

Primary map layers:

- `{ROAD_COLLECTION}`
- `{PATH_COLLECTION}`
- `{PAVEMENT_COLLECTION}` filtered to `Pavement`
- `{RAIL_COLLECTION}`
- `{WATER_COLLECTION}`
- {anchor_tools}
- OS `Light_3857` raster tiles in the HTML view only, when a browser key is supplied

## Live findings from this extract

Area used: `{payload['bbox']}`

Counts:

- `{counts['roads_total']}` road links
- `{counts['paths_total']}` path links
- `{counts['pavements']}` pavement polygons
- `{counts['rail_features']}` rail-detail features
- `{counts['water_features']}` water features

Accessible-network summary:

- Preferred route length: `{_format_length_km(lengths['preferred'])}`
- Use-with-care route length: `{_format_length_km(lengths['care'])}`
- Barrier length shown on the map: `{_format_length_km(lengths['barrier'])}`

Named sections that read best in the current data:

- Preferred roads: {_format_name_list(_top_named_segments(payload, status='preferred', kind='road'))}
- Preferred paths: {_format_name_list(_top_named_segments(payload, status='preferred', kind='path'))}
- Use-with-care roads: {_format_name_list(_top_named_segments(payload, status='care', kind='road'))}
- Use-with-care paths: {_format_name_list(_top_named_segments(payload, status='care', kind='path'))}
- Recorded barrier paths: {_format_name_list(_top_named_segments(payload, status='barrier', kind='path'))}

Anchor-point check:

{anchor_lines}

That means the current route filter is useful for planning within the core, but the final approach to
those anchor points still needs an on-the-ground crossing and kerb check.

## Filtering logic used

Road links:

- `Preferred`: recorded pavement, minimum width at least `1.2 m`, average pavement width at least
  `1.8 m`, pavement coverage at least `80%`, gentle grade under `3%`, and mostly or fully lit
- `Use with care`: minimum width at least `1.0 m`, average pavement width at least `1.4 m`,
  pavement coverage at least `60%`, and grade up to `5%`
- `Context only`: anything else, including steep or missing pavement evidence

Path links:

- `Preferred`: `Path`, `Made Sealed`, under `3%`, and mostly or fully lit
- `Use with care`: plain `Path` up to `5%`, including unlit or less certain surfaces
- `Barrier`: `Path With Steps`, `Footbridge`, `Subway`, or grade above `5%`

These thresholds are deliberately stricter than “can a chair physically squeeze through”.
`iLevel` is a seating system across multiple Quantum chair bases, so the map uses public-realm
guidance rather than assuming one exact chair width.

Reference guidance:

- GOV.UK, *Inclusive Mobility*: <https://www.gov.uk/government/publications/inclusive-mobility-making-transport-accessible-for-passengers-and-pedestrians>
- Active Travel England inclusive design guidance: <https://www.activetravelengland.gov.uk/>
- Quantum Rehab `iLevel` product family: <https://www.quantumrehab.com/>

## What MCP-Geo should consider adding

Highest-value additions for a real disabled-navigation product:

1. Dropped kerbs and crossing metadata:
   kerb height, flush status, tactile paving, crossing type, refuge islands, signal control.
2. Accessible parking:
   Blue Badge bays, step-free access from car parks, payment constraints, and surface type.
3. Public transport accessibility:
   bus stop locations, raised kerbs, shelter availability, route identifiers, and timetable / GTFS links.
4. Rest and support points:
   public toilets, benches, Changing Places toilets, pharmacies, charging points, and mobility support.
5. Temporary and environmental constraints:
   works, diversions, flood / overtopping risk, and tide-sensitive waterfront access.
6. Better amenity categorisation:
   category-coded tourist and daily-life destinations instead of broad text search alone.
"""


def _build_payload(preset: dict[str, Any]) -> dict[str, Any]:
    bbox = list(preset["bbox"])
    mean_lat = (bbox[1] + bbox[3]) / 2.0
    roads = _fetch_features(ROAD_COLLECTION, bbox, fields=ROAD_FIELDS)
    paths = _fetch_features(PATH_COLLECTION, bbox, fields=PATH_FIELDS)
    water = [
        feature
        for feature in _fetch_features(WATER_COLLECTION, bbox, fields=WATER_FIELDS)
        if str(feature.get("properties", {}).get("description") or "") != "Swimming Pool"
    ]
    rail = _fetch_features(RAIL_COLLECTION, bbox, fields=RAIL_FIELDS)
    pavements = [
        feature
        for feature in _fetch_features(PAVEMENT_COLLECTION, bbox, fields=PAVEMENT_FIELDS)
        if str(feature.get("properties", {}).get("description") or "") == "Pavement"
    ]

    preferred: list[dict[str, Any]] = []
    care: list[dict[str, Any]] = []
    barriers: list[dict[str, Any]] = []
    background_roads: list[dict[str, Any]] = []
    background_paths: list[dict[str, Any]] = []
    all_segments: list[dict[str, Any]] = []
    lengths = Counter()
    counts = Counter()

    for kind, features, classifier, name_key in [
        ("road", roads, _classify_road, "name1_text"),
        ("path", paths, _classify_path, "pathname1_text"),
    ]:
        for feature in features:
            geometry = feature.get("geometry")
            props = feature.get("properties", {})
            if not isinstance(geometry, dict) or geometry.get("type") != "LineString":
                continue
            coords = geometry.get("coordinates")
            if not isinstance(coords, list) or len(coords) < 2:
                continue
            status, reasons = classifier(props)
            grade = _worst_grade_pct(props)
            record = {
                "id": feature.get("id"),
                "kind": kind,
                "status": status,
                "reasons": reasons,
                "name": props.get(name_key),
                "length_m": float(props.get("geometry_length_m") or 0.0),
                "lighting": props.get("presenceofstreetlight_coverage"),
                "worst_grade_pct": grade,
                "geometry": geometry,
                "properties": props,
            }
            counts[f"{kind}_{status}"] += 1
            lengths[status] += record["length_m"]
            all_segments.append(record)
            if kind == "road":
                background_roads.append(record)
            else:
                background_paths.append(record)
            if status == "preferred":
                preferred.append(record)
            elif status == "care":
                care.append(record)
            elif status == "barrier":
                barriers.append(record)

    assessed = preferred + care
    anchor_rows: list[dict[str, Any]] = []
    anchor_tools: list[str] = []
    for index, anchor_spec in enumerate(preset["anchors"], start=1):
        anchor = _search_anchor(anchor_spec["query"], bbox, anchor_spec["tool"])
        anchor_tools.append(anchor_spec["tool"])
        nearest = float("inf")
        point = (float(anchor["lon"]), float(anchor["lat"]))
        for segment in assessed:
            nearest = min(
                nearest,
                _distance_point_to_polyline_m(point, segment["geometry"]["coordinates"], mean_lat),
            )
        anchor_rows.append(
            {
                "index": index,
                "label": anchor_spec["label"],
                "lon": float(anchor["lon"]),
                "lat": float(anchor["lat"]),
                "address": str(anchor.get("address") or anchor.get("name") or anchor_spec["query"]),
                "nearest_access_m": round(nearest, 1),
            }
        )

    return {
        "slug": preset["slug"],
        "place_name": preset["place_name"],
        "title": preset["title"],
        "subtitle": preset["subtitle"],
        "rail_note": preset["rail_note"],
        "callout_priority": dict(preset["callout_priority"]),
        "anchor_tools": sorted(set(anchor_tools)),
        "generated_on": dt.date.today().isoformat(),
        "bbox": bbox,
        "basemap": _build_basemap_tiles(bbox),
        "collections": {
            "roads": ROAD_COLLECTION,
            "paths": PATH_COLLECTION,
            "pavements": PAVEMENT_COLLECTION,
            "water": WATER_COLLECTION,
            "rail": RAIL_COLLECTION,
        },
        "thresholds": {
            "road_preferred_min_width_m": 1.2,
            "road_care_min_width_m": 1.0,
            "preferred_max_grade_pct": 3.0,
            "care_max_grade_pct": 5.0,
        },
        "metrics": {
            "counts": {
                **counts,
                "roads_total": len(roads),
                "paths_total": len(paths),
                "pavements": len(pavements),
                "water_features": len(water),
                "rail_features": len(rail),
            },
            "lengths_m": {
                "preferred": round(lengths["preferred"], 1),
                "care": round(lengths["care"], 1),
                "barrier": round(lengths["barrier"], 1),
            },
        },
        "anchors": anchor_rows,
        "display": {
            "preferred": preferred,
            "care": care,
            "barriers": barriers,
            "background_roads": background_roads,
            "background_paths": background_paths,
        },
        "context": {
            "water": water,
            "rail": rail,
            "pavements": pavements,
        },
        "segments": all_segments,
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a wheelchair-access map from live MCP-Geo data."
    )
    parser.add_argument(
        "--preset",
        choices=sorted(PLACE_PRESETS),
        default=DEFAULT_PRESET,
        help="Named place preset to render. Defaults to teignmouth.",
    )
    parser.add_argument(
        "--date",
        default=dt.date.today().isoformat(),
        help="Output date stamp in YYYY-MM-DD format. Defaults to today.",
    )
    args = parser.parse_args()

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

    preset = PLACE_PRESETS[args.preset]
    payload = _build_payload(preset)
    payload["generated_on"] = args.date

    slug = payload["slug"]
    json_path = EXPORTS_DIR / f"{slug}_wheelchair_access_map_{args.date}.json"
    html_path = REPORTS_DIR / f"{slug}_wheelchair_access_map_{args.date}.html"
    note_path = REPORTS_DIR / f"{slug}_wheelchair_access_map_{args.date}.md"

    _write_json(json_path, payload)
    _write_text(html_path, _render_html(payload))
    _write_text(note_path, _render_note(payload))

    summary = {
        "preset": args.preset,
        "json": str(json_path),
        "html": str(html_path),
        "note": str(note_path),
        "preferred_km": payload["metrics"]["lengths_m"]["preferred"] / 1000.0,
        "care_km": payload["metrics"]["lengths_m"]["care"] / 1000.0,
        "barrier_km": payload["metrics"]["lengths_m"]["barrier"] / 1000.0,
        "anchor_gaps_m": {
            anchor["label"]: anchor["nearest_access_m"] for anchor in payload["anchors"]
        },
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
