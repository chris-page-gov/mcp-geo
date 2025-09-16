from __future__ import annotations

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


def _norm_dpa_list(body: PlacesResponse | dict[str, Any]) -> list[NormalizedAddress]:
    results = cast(list[DPAResult], body.get("results", []))
    out: list[NormalizedAddress] = []
    for result in results:
        dpa = result.get("DPA", {})
        if not dpa:
            continue
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
            "classification": dpa.get("CLASS"),
        })
    return out

# /search/places/v1/find

def _places_search(payload: dict[str, Any]) -> ToolResult:
    text = str(payload.get("text", "")).strip()
    if not text:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "Missing text query"}
    params = {"query": text}
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
    status, raw = client.get_json(f"{client.base_places}/uprn", {"uprn": uprn})
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
    params = {"point": f"{lon},{lat}"}
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
    params = {"bbox": f"{min_lon},{min_lat},{max_lon},{max_lat}"}
    status, raw = client.get_json(f"{client.base_places}/bbox", params)
    if status != 200:
        return 501, raw
    body = cast(PlacesResponse, raw)
    return 200, {"results": _norm_dpa_list(body)}

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
    output_schema={"type":"object","properties":{"results":{"type":"array"}},"required":["results"]},
    handler=_places_within
))
