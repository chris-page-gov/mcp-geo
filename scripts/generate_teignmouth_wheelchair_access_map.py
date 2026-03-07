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
from tools.registry import get as get_tool

REPO_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = REPO_ROOT / "docs" / "reports"
EXPORTS_DIR = REPO_ROOT / "data" / "exports"

TEIGNMOUTH_BBOX = [-3.5025, 50.5405, -3.4905, 50.5495]

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

CALLOUT_PRIORITY = {
    "Promenade": 0,
    "Bitton Park Road": 1,
    "Higher Brook Street": 2,
    "Regents Gardens": 3,
    "CLAMPET LANE": 4,
    "Riverside Walk": 5,
    "East Cliff": 6,
    "Quay Road": 7,
    "STANLEY STREET": 8,
}

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
        if not isinstance(page, list):
            raise RuntimeError(f"os_features.query returned invalid features for {collection}")
        features.extend(page)
        token = data.get("nextPageToken")
        if not token:
            break
    return features


def _search_place(text: str, bbox: list[float]) -> dict[str, Any]:
    data = _call_tool("os_places.search", {"tool": "os_places.search", "text": text, "limit": 25})
    results = data.get("results")
    if not isinstance(results, list) or not results:
        raise RuntimeError(f"os_places.search returned no results for {text!r}")
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
    raise RuntimeError(f"os_places.search returned no geocoded result for {text!r}")


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


def _projector(
    bbox: list[float],
    *,
    x: float = MAP_X,
    y: float = MAP_Y,
    width: float = MAP_W,
    height: float = MAP_H,
    pad: float = MAP_PAD,
) -> Callable[[float, float], tuple[float, float]]:
    min_lon, min_lat, max_lon, max_lat = bbox
    mid_lat = (min_lat + max_lat) / 2.0
    lon_scale = math.cos(math.radians(mid_lat))
    world_w = (max_lon - min_lon) * lon_scale
    world_h = max_lat - min_lat
    scale = min((width - (2 * pad)) / world_w, (height - (2 * pad)) / world_h)
    extra_x = (width - (2 * pad) - (world_w * scale)) / 2.0
    extra_y = (height - (2 * pad) - (world_h * scale)) / 2.0

    def project(lon: float, lat: float) -> tuple[float, float]:
        px = x + pad + extra_x + ((lon - min_lon) * lon_scale * scale)
        py = y + pad + extra_y + ((max_lat - lat) * scale)
        return round(px, 1), round(py, 1)

    return project


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
            CALLOUT_PRIORITY.get(str(item["name"]), 999),
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
          <line x1="4" y1="9" x2="50" y2="9" stroke="{color}" stroke-width="5" stroke-linecap="round" {dash_attr} />
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
    callouts = _select_callouts(payload["display"]["preferred"] + payload["display"]["care"], bbox, project)

    def route_svg(features: list[dict[str, Any]], css_class: str) -> str:
        chunks: list[str] = []
        for feature in features:
            title = escape(_segment_title(feature))
            for path in _geom_paths(feature["geometry"], project):
                if not path:
                    continue
                chunks.append(f'<path d="{path}" class="{css_class}"><title>{title}</title></path>')
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
    station_gap = round(payload["anchors"][0]["nearest_access_m"])
    shopmobility_gap = round(payload["anchors"][1]["nearest_access_m"])

    scale_bar_x = MAP_X + 34
    scale_bar_y = MAP_Y + MAP_H - 30
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
    <title>Teignmouth wheelchair access map</title>
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

      .panel {{
        position: absolute;
        left: {PANEL_X}px;
        top: {PANEL_Y}px;
        width: {PANEL_W}px;
        height: {PANEL_H}px;
        padding: 22px 20px 18px 20px;
        border-radius: 24px;
        background: #fffdf8;
        border: 1px solid #ddd5c8;
        display: flex;
        flex-direction: column;
        gap: 14px;
      }}

      .metric {{
        min-height: 74px;
        padding: 10px 12px;
        border-radius: 18px;
        border: 1px solid #d9d1c4;
        background: #fcfaf5;
      }}

      .metric strong {{
        display: block;
        margin-top: 7px;
        font-size: 24px;
        line-height: 1;
        letter-spacing: -0.03em;
      }}

      .metric-label {{
        font-size: 12px;
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
        font-size: 16px;
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
        font-size: 12px;
      }}

      .access-row span {{
        display: block;
        margin-top: 2px;
        font-size: 11px;
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
        font-size: 12px;
      }}

      .legend-row span {{
        display: block;
        margin-top: 2px;
        font-size: 11px;
        line-height: 1.4;
        color: #53646c;
      }}

      .checks {{
        margin-top: 2px;
      }}

      .checks h2 {{
        margin: 0 0 10px 0;
      }}

      .checks ul {{
        margin: 0;
        padding-left: 18px;
        color: #42575f;
        font-size: 12px;
        line-height: 1.45;
      }}

      .checks li + li {{
        margin-top: 7px;
      }}

      .source-note {{
        margin-top: auto;
        padding-top: 12px;
        border-top: 1px solid #e4dccd;
        color: #617078;
        font-size: 10px;
        line-height: 1.45;
      }}

      svg {{
        width: 100%;
        height: 100%;
        display: block;
      }}

      .water-fill {{
        fill: #c9e5ef;
        stroke: #96bfcc;
        stroke-width: 1;
      }}

      .pavement-fill {{
        fill: #eee6d8;
        stroke: none;
        opacity: 0.72;
      }}

      .road-context {{
        fill: none;
        stroke: #b8b0a5;
        stroke-width: 2.4;
        stroke-linecap: round;
        stroke-linejoin: round;
      }}

      .path-context {{
        fill: none;
        stroke: #cbc5bc;
        stroke-width: 1.6;
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

      .route-preferred {{
        fill: none;
        stroke: #0d7d7f;
        stroke-width: 5.6;
        stroke-linecap: round;
        stroke-linejoin: round;
        cursor: help;
      }}

      .route-care {{
        fill: none;
        stroke: #d08c1f;
        stroke-width: 4.8;
        stroke-linecap: round;
        stroke-linejoin: round;
        cursor: help;
      }}

      .route-barrier {{
        fill: none;
        stroke: #c64d3d;
        stroke-width: 4.2;
        stroke-linecap: round;
        stroke-linejoin: round;
        stroke-dasharray: 10 8;
        cursor: help;
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
    </style>
  </head>
  <body>
    <div class="page">
      <div class="slide-shell">
      <article class="slide">
        <header class="title">
          <h1>Teignmouth town-centre wheelchair access map</h1>
          <p>
            Conservative MCP-Geo route filter for a Quantum iLevel user.
            Width, slope, lighting, and pedestrian-path evidence are shown. Hover a coloured route in HTML for details. Dropped kerbs and crossing quality are not.
          </p>
        </header>

        <section class="map-frame" aria-label="Wheelchair access map">
          <svg viewBox="0 0 {MAP_W} {MAP_H}" role="img" aria-label="Teignmouth wheelchair access map">
            <g transform="translate(-{MAP_X}, -{MAP_Y})">
              {water_svg}
              {pavement_svg}
              {road_background_svg}
              {path_background_svg}
              {rail_svg}
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
                <line x1="0" y1="0" x2="212" y2="0" stroke="#17333a" stroke-width="4" stroke-linecap="round" />
                <line x1="0" y1="-7" x2="0" y2="7" stroke="#17333a" stroke-width="2" />
                <line x1="106" y1="-7" x2="106" y2="7" stroke="#17333a" stroke-width="2" />
                <line x1="212" y1="-7" x2="212" y2="7" stroke="#17333a" stroke-width="2" />
                <text x="0" y="-12" class="scale-label">0</text>
                <text x="92" y="-12" class="scale-label">125 m</text>
                <text x="195" y="-12" class="scale-label">250 m</text>
              </g>
              <text x="{MAP_X + 30}" y="{MAP_Y + 42}" class="map-note">Railway line and station edge</text>
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
              <li>Final approach still needs checking: station about {station_gap} m; Shopmobility about {shopmobility_gap} m.</li>
              <li>Not captured in current data: dropped kerbs, crossing type, tactile paving, parked cars, bins, café furniture, or temporary works.</li>
              <li>In HTML, hover a coloured route or anchor label for the recorded name and evidence summary.</li>
            </ul>
          </section>

          <div class="source-note">
            Live MCP-Geo extract on {escape(payload['generated_on'])}: roads, paths, pavement polygons,
            rail detail, water context, and OS Places anchors. Route filter uses UK accessible-footway guidance
            and a conservative 5% maximum grade rule for display.
          </div>
        </aside>
      </article>
      </div>
    </div>
    <script>
      (() => {{
        const root = document.documentElement;
        const fit = () => {{
          const availableWidth = Math.max(320, window.innerWidth - 32);
          const scale = Math.min(1, availableWidth / {SLIDE_WIDTH});
          root.style.setProperty("--slide-scale", scale.toFixed(4));
        }};
        fit();
        window.addEventListener("resize", fit);
      }})();
    </script>
  </body>
</html>
"""


def _build_payload(bbox: list[float]) -> dict[str, Any]:
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

    station = _search_place("teignmouth railway station", bbox)
    shopmobility = _search_place("teignmouth shopmobility", bbox)

    assessed = preferred + care
    for anchor in (station, shopmobility):
        nearest = float("inf")
        point = (float(anchor["lon"]), float(anchor["lat"]))
        for segment in assessed:
            nearest = min(
                nearest,
                _distance_point_to_polyline_m(point, segment["geometry"]["coordinates"], mean_lat),
            )
        anchor["nearest_access_m"] = round(nearest, 1)

    anchor_rows = [
        {
            "index": 1,
            "label": "Teignmouth station",
            "lon": float(station["lon"]),
            "lat": float(station["lat"]),
            "address": station["address"],
            "nearest_access_m": station["nearest_access_m"],
        },
        {
            "index": 2,
            "label": "Shopmobility",
            "lon": float(shopmobility["lon"]),
            "lat": float(shopmobility["lat"]),
            "address": shopmobility["address"],
            "nearest_access_m": shopmobility["nearest_access_m"],
        },
    ]

    return {
        "generated_on": dt.date.today().isoformat(),
        "bbox": bbox,
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
        description="Generate a Teignmouth wheelchair-access map from live MCP-Geo data."
    )
    parser.add_argument(
        "--date",
        default=dt.date.today().isoformat(),
        help="Output date stamp in YYYY-MM-DD format. Defaults to today.",
    )
    args = parser.parse_args()

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

    payload = _build_payload(TEIGNMOUTH_BBOX)
    payload["generated_on"] = args.date

    json_path = EXPORTS_DIR / f"teignmouth_wheelchair_access_map_{args.date}.json"
    html_path = REPORTS_DIR / f"teignmouth_wheelchair_access_map_{args.date}.html"

    _write_json(json_path, payload)
    _write_text(html_path, _render_html(payload))

    summary = {
        "json": str(json_path),
        "html": str(html_path),
        "preferred_km": payload["metrics"]["lengths_m"]["preferred"] / 1000.0,
        "care_km": payload["metrics"]["lengths_m"]["care"] / 1000.0,
        "barrier_km": payload["metrics"]["lengths_m"]["barrier"] / 1000.0,
        "station_gap_m": payload["anchors"][0]["nearest_access_m"],
        "shopmobility_gap_m": payload["anchors"][1]["nearest_access_m"],
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
