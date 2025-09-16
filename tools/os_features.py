from __future__ import annotations

from typing import Any

from tools.registry import Tool, register

from .os_common import client

# Simplified features query: bbox + collection

def _features_query(payload: dict[str, Any]):
    collection = str(payload.get("collection", "")).strip()
    bbox = payload.get("bbox")
    if not collection:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "Missing collection"}
    if not (isinstance(bbox, list) and len(bbox) == 4):
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "bbox must be [minLon,minLat,maxLon,maxLat]",
        }
    try:
        min_lon, min_lat, max_lon, max_lat = [float(x) for x in bbox]
    except Exception:
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "bbox values must be numeric",
        }
    params = {"bbox": f"{min_lon},{min_lat},{max_lon},{max_lat}"}
    status, body = client.get_json(f"{client.base_features}/{collection}", params)
    if status != 200:
        return status, body
    # Return a trimmed feature list (id + geometry type)
    features_out = []
    for feat in body.get("features", []):
        features_out.append({
            "id": feat.get("id"),
            "geometry_type": (feat.get("geometry") or {}).get("type"),
            "properties": feat.get("properties", {}),
        })
    return 200, {"features": features_out, "count": len(features_out)}

register(Tool(
    name="os_features.query",
    description="Query features by bbox",
    input_schema={"type":"object","properties":{"tool":{"type":"string","const":"os_features.query"},"collection":{"type":"string"},"bbox":{"type":"array","items":{"type":"number"},"minItems":4,"maxItems":4}},"required":["collection","bbox"],"additionalProperties":False},
    output_schema={"type":"object","properties":{"features":{"type":"array"},"count":{"type":"number"}},"required":["features"]},
    handler=_features_query
))
