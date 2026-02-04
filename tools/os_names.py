from __future__ import annotations
from typing import Any, cast

from tools.accessors import get_gaz
from tools.os_common import client
from tools.registry import Tool, ToolResult, register
from tools.typing_utils import parse_float
from tools.types import NamesResponse

try:
    from pyproj import Transformer
except ImportError:  # pragma: no cover - optional dependency fallback
    Transformer = None  # type: ignore[assignment]

# OS Names API basic handlers

def _parse_number(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _extract_lat_lon(geometry: Any) -> tuple[float | None, float | None]:
    if isinstance(geometry, dict):
        lat = _parse_number(geometry.get("LAT"))
        if lat is None:
            lat = _parse_number(geometry.get("LATITUDE"))
        lon = _parse_number(geometry.get("LNG"))
        if lon is None:
            lon = _parse_number(geometry.get("LON"))
        if lon is None:
            lon = _parse_number(geometry.get("LONGITUDE"))
        if lat is not None and lon is not None:
            return lat, lon
        x = _parse_number(geometry.get("X"))
        y = _parse_number(geometry.get("Y"))
        if x is not None and y is not None and abs(x) <= 180 and abs(y) <= 90:
            return y, x
    if isinstance(geometry, list) and len(geometry) == 2:
        x = _parse_number(geometry[0])
        y = _parse_number(geometry[1])
        if x is not None and y is not None:
            if abs(x) <= 180 and abs(y) <= 90:
                return y, x
    return None, None


_BNG_TRANSFORMER: Any = None


def _wgs84_to_bng(lat: float, lon: float) -> tuple[float, float] | None:
    if Transformer is None:
        return None
    global _BNG_TRANSFORMER
    if _BNG_TRANSFORMER is None:
        _BNG_TRANSFORMER = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)
    try:
        easting, northing = _BNG_TRANSFORMER.transform(lon, lat)
    except Exception:
        return None
    return float(easting), float(northing)


def _normalize_coord_system(value: Any) -> str:
    if value is None:
        return "EPSG:4326"
    text = str(value).strip().upper().replace(" ", "")
    if text in {"WGS84", "EPSG:4326", "4326"}:
        return "EPSG:4326"
    if text in {"BNG", "OSGB36", "EPSG:27700", "27700"}:
        return "EPSG:27700"
    return text


def _names_find(payload: dict[str, Any]) -> ToolResult:
    text = str(payload.get("text", "")).strip()
    if not text:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "Missing text"}
    status, raw = client.get_json(
        f"{client.base_names}/find",
        {"query": text},
    )
    if status != 200:
        return 501, raw
    body = cast(NamesResponse, raw)
    results = cast(list[dict[str, Any]], body.get("results", []))
    out: list[dict[str, Any]] = []
    for r in results:
        gaz = get_gaz(r)
        geometry = gaz.get("GEOMETRY")
        lat, lon = _extract_lat_lon(geometry)
        out.append({
            "id": gaz.get("ID"),
            "name1": gaz.get("NAME1"),
            "type": gaz.get("TYPE"),
            "local_type": gaz.get("LOCAL_TYPE"),
            "coordinates": geometry,
            "lat": lat,
            "lon": lon,
        })
    return 200, {"results": out}

def _names_nearest(payload: dict[str, Any]) -> ToolResult:
    raw_lat = payload.get("lat")
    raw_lon = payload.get("lon")
    lat = parse_float(raw_lat)
    lon = parse_float(raw_lon)
    if lat is None or lon is None:
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "lat/lon must be numeric",
        }
    coord_system = _normalize_coord_system(payload.get("coordSystem"))
    if coord_system == "EPSG:27700":
        easting, northing = lon, lat
    elif coord_system == "EPSG:4326":
        converted = _wgs84_to_bng(lat, lon)
        if not converted:
            return 501, {
                "isError": True,
                "code": "MISSING_DEPENDENCY",
                "message": "pyproj is required to convert WGS84 lat/lon to British National Grid",
            }
        easting, northing = converted
    else:
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "coordSystem must be EPSG:4326 or EPSG:27700",
        }
    status, raw = client.get_json(
        f"{client.base_names}/nearest",
        {"point": f"{easting:.2f},{northing:.2f}"},
    )
    if status != 200:
        return 501, raw
    body = cast(NamesResponse, raw)
    results = cast(list[dict[str, Any]], body.get("results", []))
    feats: list[dict[str, Any]] = []
    for r in results:
        gaz = get_gaz(r)
        geometry = gaz.get("GEOMETRY")
        lat, lon = _extract_lat_lon(geometry)
        feats.append({
            "id": gaz.get("ID"),
            "name1": gaz.get("NAME1"),
            "type": gaz.get("TYPE"),
            "distance": gaz.get("DISTANCE"),
            "coordinates": geometry,
            "lat": lat,
            "lon": lon,
        })
    return 200, {"results": feats}

register(Tool(
    name="os_names.find",
    description="Find place names",
    input_schema={"type":"object","properties":{"tool":{"type":"string","const":"os_names.find"},"text":{"type":"string"}},"required":["text"],"additionalProperties":False},
    output_schema={"type":"object","properties":{"results":{"type":"array"}},"required":["results"]},
    handler=_names_find
))

register(Tool(
    name="os_names.nearest",
    description="Nearest named features",
    input_schema={"type":"object","properties":{"tool":{"type":"string","const":"os_names.nearest"},"lat":{"type":"number"},"lon":{"type":"number"},"coordSystem":{"type":"string","enum":["EPSG:4326","EPSG:27700"],"default":"EPSG:4326"}},"required":["lat","lon"],"additionalProperties":False},
    output_schema={"type":"object","properties":{"results":{"type":"array"}},"required":["results"]},
    handler=_names_nearest
))
