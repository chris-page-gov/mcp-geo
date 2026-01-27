from __future__ import annotations

from typing import Any

from tools.registry import Tool, register

from .os_common import client

# Vector tiles descriptor returning style + tile URL template

def _vector_tiles_descriptor(payload: dict[str, Any]):
    style = "OS_VTS_3857_Light.json"
    tiles = f"{client.base_vector_tiles}/vts/tiles/{{z}}/{{x}}/{{y}}.pbf?srs=3857&key={{API_KEY}}"
    style_url = f"{client.base_vector_tiles}/vts/resources/styles?style={style}&srs=3857&key={{API_KEY}}"
    return 200, {"vectorTiles": {"style": style, "styleUrl": style_url, "tileTemplate": tiles}}

register(Tool(
    name="os_vector_tiles.descriptor",
    description="Return vector tiles style and tile template URLs",
    input_schema={"type":"object","properties":{"tool":{"type":"string","const":"os_vector_tiles.descriptor"}},"required":[],"additionalProperties":False},
    output_schema={"type":"object","properties":{"vectorTiles":{"type":"object"}},"required":["vectorTiles"]},
    handler=_vector_tiles_descriptor
))
