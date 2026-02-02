from __future__ import annotations

from typing import Any

from tools.registry import Tool, register

# Maps render metadata: return a usable static image URL (OSM-backed proxy)

def _maps_render(payload: dict[str, Any]):
    bbox = payload.get("bbox")
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
    bbox_str = f"{min_lon},{min_lat},{max_lon},{max_lat}"
    image_url = f"/maps/static/osm?bbox={bbox_str}&size=256"
    center_lon = (min_lon + max_lon) / 2.0
    center_lat = (min_lat + max_lat) / 2.0
    return 200, {
        "render": {
            "imageUrl": image_url,
            "imageWidth": 256,
            "imageHeight": 256,
            "bbox": [min_lon, min_lat, max_lon, max_lat],
            "center": {"lon": center_lon, "lat": center_lat},
            "source": "osm",
            "notes": "Image URL is served by the MCP Geo map proxy.",
        }
    }

register(Tool(
    name="os_maps.render",
    description="Return metadata for rendering a static map image (proxy URL)",
    input_schema={"type":"object","properties":{"tool":{"type":"string","const":"os_maps.render"},"bbox":{"type":"array","items":{"type":"number"},"minItems":4,"maxItems":4}},"required":["bbox"],"additionalProperties":False},
    output_schema={"type":"object","properties":{"render":{"type":"object"}},"required":["render"]},
    handler=_maps_render
))
