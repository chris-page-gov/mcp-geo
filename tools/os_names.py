from __future__ import annotations
from typing import Any, cast

from tools.accessors import get_gaz
from tools.os_common import client
from tools.registry import Tool, ToolResult, register
from tools.typing_utils import parse_float
from tools.types import NamesResponse

# OS Names API basic handlers

def _names_find(payload: dict[str, Any]) -> ToolResult:
    text = str(payload.get("text", "")).strip()
    if not text:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "Missing text"}
    status, raw = client.get_json(f"{client.base_names}/find", {"query": text})
    if status != 200:
        return 501, raw
    body = cast(NamesResponse, raw)
    results = cast(list[dict[str, Any]], body.get("results", []))
    out: list[dict[str, Any]] = []
    for r in results:
        gaz = get_gaz(r)
        out.append({
            "id": gaz.get("ID"),
            "name1": gaz.get("NAME1"),
            "type": gaz.get("TYPE"),
            "local_type": gaz.get("LOCAL_TYPE"),
            "coordinates": gaz.get("GEOMETRY"),
        })
    return 200, {"results": out}

def _names_nearest(payload: dict[str, Any]) -> ToolResult:
    raw_lat = payload.get("lat")
    raw_lon = payload.get("lon")
    # Basic validation: must be int/float or numeric string
    for raw in (raw_lat, raw_lon):
        if isinstance(raw, (int, float)):
            continue
        if not (isinstance(raw, str) and raw.strip() and raw.strip().replace(".", "", 1).isdigit()):
            return 400, {
                "isError": True,
                "code": "INVALID_INPUT",
                "message": "lat/lon must be numeric",
            }
    lat = parse_float(raw_lat)
    lon = parse_float(raw_lon)
    status, raw = client.get_json(f"{client.base_names}/nearest", {"point": f"{lon},{lat}"})
    if status != 200:
        return 501, raw
    body = cast(NamesResponse, raw)
    results = cast(list[dict[str, Any]], body.get("results", []))
    feats: list[dict[str, Any]] = []
    for r in results:
        gaz = get_gaz(r)
        feats.append({
            "id": gaz.get("ID"),
            "name1": gaz.get("NAME1"),
            "type": gaz.get("TYPE"),
            "distance": gaz.get("DISTANCE"),
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
    input_schema={"type":"object","properties":{"tool":{"type":"string","const":"os_names.nearest"},"lat":{"type":"number"},"lon":{"type":"number"}},"required":["lat","lon"],"additionalProperties":False},
    output_schema={"type":"object","properties":{"results":{"type":"array"}},"required":["results"]},
    handler=_names_nearest
))
