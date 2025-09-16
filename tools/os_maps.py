from __future__ import annotations
from typing import Any
from tools.registry import Tool, register
from .os_common import client

# Maps render metadata: construct a static map URL template (hypothetical)

def _maps_render(payload: dict[str, Any]):
    bbox = payload.get("bbox")
    if not (isinstance(bbox, list) and len(bbox) == 4):
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "bbox must be [minLon,minLat,maxLon,maxLat]"}
    try:
        min_lon, min_lat, max_lon, max_lat = [float(x) for x in bbox]
    except Exception:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "bbox values must be numeric"}
    # Provide a URL template (not fetching binary in this implementation)
    base = client.base_maps
    layer = "raster"  # placeholder layer
    url_template = f"{base}/{layer}/wms?bbox={min_lon},{min_lat},{max_lon},{max_lat}&key={{API_KEY}}"
    return 200, {"render": {"urlTemplate": url_template, "layer": layer}}

register(Tool(
    name="os_maps.render",
    description="Return metadata for rendering a map image (URL template)",
    input_schema={"type":"object","properties":{"tool":{"type":"string","const":"os_maps.render"},"bbox":{"type":"array","items":{"type":"number"},"minItems":4,"maxItems":4}},"required":["bbox"],"additionalProperties":False},
    output_schema={"type":"object","properties":{"render":{"type":"object"}},"required":["render"]},
    handler=_maps_render
))
