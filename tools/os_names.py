from __future__ import annotations
from typing import Any
from tools.registry import Tool, register
from .os_common import client

# OS Names API basic handlers

def _names_find(payload: dict[str, Any]):
    text = str(payload.get("text", "")).strip()
    if not text:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "Missing text"}
    status, body = client.get_json(f"{client.base_names}/find", {"query": text})
    if status != 200:
        return status, body
    results = []
    for r in body.get("results", []):
        gaz = r.get("GAZETTEER_ENTRY", {})
        results.append({
            "id": gaz.get("ID"),
            "name1": gaz.get("NAME1"),
            "type": gaz.get("TYPE"),
            "local_type": gaz.get("LOCAL_TYPE"),
            "coordinates": gaz.get("GEOMETRY"),
        })
    return 200, {"results": results}

def _names_nearest(payload: dict[str, Any]):
    try:
        lat = float(payload.get("lat"))
        lon = float(payload.get("lon"))
    except Exception:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "lat/lon must be numeric"}
    status, body = client.get_json(f"{client.base_names}/nearest", {"point": f"{lon},{lat}"})
    if status != 200:
        return status, body
    feats = []
    for r in body.get("results", []):
        gaz = r.get("GAZETTEER_ENTRY", {})
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
