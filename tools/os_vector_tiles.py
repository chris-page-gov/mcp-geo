from __future__ import annotations

from typing import Any

from tools.registry import Tool, register

from .os_common import client

# Vector tiles descriptor returning style + tile URL template

def _vector_tiles_descriptor(payload: dict[str, Any]):
    style = "OS_VTS_3857_Light.json"
    # OS VTS uses /vts/tile/{z}/{y}/{x}.pbf (y/x order, singular "tile").
    tiles = f"{client.base_vector_tiles}/vts/tile/{{z}}/{{y}}/{{x}}.pbf?srs=3857&key={{API_KEY}}"
    style_url = f"{client.base_vector_tiles}/vts/resources/styles?style={style}&srs=3857&key={{API_KEY}}"
    proxy_tiles = "/maps/vector/vts/tile/{z}/{y}/{x}.pbf?srs=3857"
    proxy_style = f"/maps/vector/vts/resources/styles?style={style}&srs=3857"
    return 200, {
        "vectorTiles": {
            "style": style,
            "styleUrl": style_url,
            "tileTemplate": tiles,
            "proxyStyleUrl": proxy_style,
            "proxyTileTemplate": proxy_tiles,
            "notes": [
                "Prefer proxyStyleUrl/proxyTileTemplate for local-first MCP hosts.",
                "OS API key should be provided server-side via OS_API_KEY environment variable.",
            ],
        }
    }

register(Tool(
    name="os_vector_tiles.descriptor",
    description="Return vector tiles style and tile template URLs",
    input_schema={"type":"object","properties":{"tool":{"type":"string","const":"os_vector_tiles.descriptor"}},"required":[],"additionalProperties":False},
    output_schema={"type":"object","properties":{"vectorTiles":{"type":"object"}},"required":["vectorTiles"]},
    handler=_vector_tiles_descriptor
))
