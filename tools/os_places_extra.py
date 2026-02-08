from __future__ import annotations

import math
from typing import Any, TypedDict, cast

from tools.os_common import client
from tools.registry import Tool, ToolResult, register
from tools.types import DPAResult, PlacesResponse


class NormalizedAddress(TypedDict, total=False):
    uprn: str | None
    address: str | None
    lat: float
    lon: float
    classification: str | None
    classificationDescription: str | None


MAX_BBOX_AREA_M2 = 1_000_000.0
MAX_BBOX_TILE_COUNT = 25


def _meters_per_degree(lat: float) -> tuple[float, float]:
    lat_rad = math.radians(lat)
    m_per_deg_lat = (
        111_132.92
        - 559.82 * math.cos(2 * lat_rad)
        + 1.175 * math.cos(4 * lat_rad)
        - 0.0023 * math.cos(6 * lat_rad)
    )
    m_per_deg_lon = (
        111_412.84 * math.cos(lat_rad)
        - 93.5 * math.cos(3 * lat_rad)
        + 0.118 * math.cos(5 * lat_rad)
    )
    return m_per_deg_lat, m_per_deg_lon


def _bbox_area_m2(min_lon: float, min_lat: float, max_lon: float, max_lat: float) -> float:
    mid_lat = (min_lat + max_lat) / 2.0
    m_per_deg_lat, m_per_deg_lon = _meters_per_degree(mid_lat)
    width_deg = max_lon - min_lon
    height_deg = max_lat - min_lat
    width_m = width_deg * m_per_deg_lon
    height_m = height_deg * m_per_deg_lat
    return abs(width_m * height_m)


def _tile_or_clamp_bbox(
    min_lon: float,
    min_lat: float,
    max_lon: float,
    max_lat: float,
) -> tuple[list[tuple[float, float, float, float]], dict[str, Any]]:
    mid_lat = (min_lat + max_lat) / 2.0
    m_per_deg_lat, m_per_deg_lon = _meters_per_degree(mid_lat)
    width_deg = max_lon - min_lon
    height_deg = max_lat - min_lat
    area = _bbox_area_m2(min_lon, min_lat, max_lon, max_lat)
    if area <= MAX_BBOX_AREA_M2:
        return [(min_lon, min_lat, max_lon, max_lat)], {"bboxMode": "single", "tileCount": 1}
    if m_per_deg_lat <= 0 or m_per_deg_lon <= 0:
        return [(min_lon, min_lat, max_lon, max_lat)], {"bboxMode": "single", "tileCount": 1}

    target_edge_m = math.sqrt(MAX_BBOX_AREA_M2)
    tile_lon_deg = target_edge_m / m_per_deg_lon
    tile_lat_deg = target_edge_m / m_per_deg_lat
    tiles_x = max(1, math.ceil(width_deg / tile_lon_deg))
    tiles_y = max(1, math.ceil(height_deg / tile_lat_deg))
    tile_count = tiles_x * tiles_y

    if tile_count > MAX_BBOX_TILE_COUNT:
        scale = math.sqrt(MAX_BBOX_AREA_M2 / area)
        new_width_deg = width_deg * scale
        new_height_deg = height_deg * scale
        center_lon = (min_lon + max_lon) / 2.0
        center_lat = (min_lat + max_lat) / 2.0
        clamped_min_lon = center_lon - new_width_deg / 2.0
        clamped_max_lon = center_lon + new_width_deg / 2.0
        clamped_min_lat = center_lat - new_height_deg / 2.0
        clamped_max_lat = center_lat + new_height_deg / 2.0
        return [
            (clamped_min_lon, clamped_min_lat, clamped_max_lon, clamped_max_lat),
        ], {
            "bboxMode": "clamped",
            "tileCount": 1,
            "originalTileCount": tile_count,
        }

    tiles: list[tuple[float, float, float, float]] = []
    for ix in range(tiles_x):
        tile_min_lon = min_lon + ix * tile_lon_deg
        tile_max_lon = min(tile_min_lon + tile_lon_deg, max_lon)
        for iy in range(tiles_y):
            tile_min_lat = min_lat + iy * tile_lat_deg
            tile_max_lat = min(tile_min_lat + tile_lat_deg, max_lat)
            tiles.append((tile_min_lon, tile_min_lat, tile_max_lon, tile_max_lat))
    return tiles, {"bboxMode": "tiled", "tileCount": tile_count}

def _norm_dpa_list(body: PlacesResponse | dict[str, Any]) -> list[NormalizedAddress]:
    results = cast(list[DPAResult], body.get("results", []))
    out: list[NormalizedAddress] = []
    for result in results:
        dpa = result.get("DPA", {})
        if not dpa:
            continue
        classification_code = dpa.get("CLASSIFICATION_CODE") or dpa.get("CLASS")
        classification_desc = (
            dpa.get("CLASSIFICATION_CODE_DESCRIPTION")
            or dpa.get("CLASSIFICATION_DESCRIPTION")
            or dpa.get("CLASS_DESCRIPTION")
        )
        # Defensive numeric conversion
        try:
            lat = float(dpa.get("LAT", 0) or 0)
        except Exception:
            lat = 0.0
        try:
            lon = float(dpa.get("LNG", 0) or 0)
        except Exception:
            lon = 0.0
        out.append({
            "uprn": dpa.get("UPRN"),
            "address": dpa.get("ADDRESS"),
            "lat": lat,
            "lon": lon,
            "classification": classification_code,
            "classificationDescription": classification_desc,
        })
    return out

# /search/places/v1/find

def _places_search(payload: dict[str, Any]) -> ToolResult:
    text = str(payload.get("text", "")).strip()
    if not text:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "Missing text query"}
    params = {"query": text, "output_srs": "WGS84"}
    status, raw = client.get_json(f"{client.base_places}/find", params)
    if status != 200:
        return 501, raw
    body = cast(PlacesResponse, raw)
    norm = _norm_dpa_list(body)
    count = len(cast(list[Any], body.get("results", [])))
    return 200, {"results": norm, "count": count}

# /search/places/v1/uprn

def _places_by_uprn(payload: dict[str, Any]) -> ToolResult:
    uprn = str(payload.get("uprn", "")).strip()
    if not uprn:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "Missing uprn"}
    status, raw = client.get_json(
        f"{client.base_places}/uprn",
        {"uprn": uprn, "output_srs": "WGS84"},
    )
    if status != 200:
        return 501, raw
    body = cast(PlacesResponse, raw)
    results = _norm_dpa_list(body)
    return 200, {"result": results[0] if results else None}

# /search/places/v1/nearest

def _places_nearest(payload: dict[str, Any]) -> ToolResult:
    raw_lat = payload.get("lat")
    raw_lon = payload.get("lon")
    try:
        lat = float(raw_lat) if raw_lat is not None else 0.0
        lon = float(raw_lon) if raw_lon is not None else 0.0
    except Exception:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "lat/lon must be numeric"}
    # OS Places expects WGS84 axis order for srs=WGS84 (lat,lon).
    params = {"point": f"{lat},{lon}", "srs": "WGS84", "output_srs": "WGS84"}
    status, raw = client.get_json(f"{client.base_places}/nearest", params)
    if status != 200:
        return 501, raw
    body = cast(PlacesResponse, raw)
    results = _norm_dpa_list(body)
    return 200, {"results": results}

# /search/places/v1/bbox (assuming endpoint name 'bbox')

def _places_within(payload: dict[str, Any]) -> ToolResult:
    bbox_val = payload.get("bbox")
    if not (isinstance(bbox_val, list) and len(bbox_val) == 4):
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "bbox must be [minLon,minLat,maxLon,maxLat]",
        }
    try:
        bbox_list: list[float] = [float(x) for x in bbox_val]
    except Exception:
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "bbox values must be numeric",
        }
    min_lon, min_lat, max_lon, max_lat = bbox_list
    if min_lon >= max_lon or min_lat >= max_lat:
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "bbox must be [minLon,minLat,maxLon,maxLat] with min < max",
        }

    tiles, meta = _tile_or_clamp_bbox(min_lon, min_lat, max_lon, max_lat)
    combined: list[NormalizedAddress] = []
    for tile_min_lon, tile_min_lat, tile_max_lon, tile_max_lat in tiles:
        # For WGS84, OS Places bbox expects axis order lat,lon.
        params = {
            "bbox": f"{tile_min_lat},{tile_min_lon},{tile_max_lat},{tile_max_lon}",
            "srs": "WGS84",
            "output_srs": "WGS84",
        }
        status, raw = client.get_json(f"{client.base_places}/bbox", params)
        if status != 200:
            return 501, raw
        body = cast(PlacesResponse, raw)
        combined.extend(_norm_dpa_list(body))

    seen: set[str] = set()
    deduped: list[NormalizedAddress] = []
    for entry in combined:
        key = entry.get("uprn")
        if key is None:
            key = f"{entry.get('address')}|{entry.get('lat')}|{entry.get('lon')}"
        if key in seen:
            continue
        seen.add(key)
        deduped.append(entry)

    response: dict[str, Any] = {"results": deduped}
    if meta.get("bboxMode") != "single":
        response["provenance"] = meta
    return 200, response

# Register tools (overwrite placeholders if present)

register(Tool(
    name="os_places.search",
    description="Free text search in OS Places",
    input_schema={
        "type": "object",
        "properties": {
            "tool": {"type": "string", "const": "os_places.search"},
            "text": {"type": "string"},
        },
        "required": ["text"],
        "additionalProperties": False,
    },
    output_schema={
        "type": "object",
        "properties": {
            "results": {"type": "array"},
            "count": {"type": "number"},
        },
        "required": ["results"],
    },
    handler=_places_search
))

register(Tool(
    name="os_places.by_uprn",
    description="Lookup a single address by UPRN",
    input_schema={"type":"object","properties":{"tool":{"type":"string","const":"os_places.by_uprn"},"uprn":{"type":"string"}},"required":["uprn"],"additionalProperties":False},
    output_schema={"type":"object","properties":{"result":{"type":["object","null"]}},"required":["result"]},
    handler=_places_by_uprn
))

register(Tool(
    name="os_places.nearest",
    description="Find nearest addresses to a point",
    input_schema={"type":"object","properties":{"tool":{"type":"string","const":"os_places.nearest"},"lat":{"type":"number"},"lon":{"type":"number"}},"required":["lat","lon"],"additionalProperties":False},
    output_schema={"type":"object","properties":{"results":{"type":"array"}},"required":["results"]},
    handler=_places_nearest
))

register(Tool(
    name="os_places.within",
    description="Addresses within a bounding box",
    input_schema={"type":"object","properties":{"tool":{"type":"string","const":"os_places.within"},"bbox":{"type":"array","items":{"type":"number"},"minItems":4,"maxItems":4}},"required":["bbox"],"additionalProperties":False},
    output_schema={
        "type": "object",
        "properties": {
            "results": {"type": "array"},
            "provenance": {"type": "object"},
        },
        "required": ["results"],
        "additionalProperties": True,
    },
    handler=_places_within
))
