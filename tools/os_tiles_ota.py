from __future__ import annotations

from typing import Any

from tools.os_common import client
from tools.registry import Tool, ToolResult, register

_OTA_BASE = "https://api.os.uk/maps/vector/ngd/ota/v1"


def _collections(_payload: dict[str, Any]) -> ToolResult:
    status, body = client.get_json(f"{_OTA_BASE}/collections", None)
    if status != 200:
        return status, body
    return 200, {"collections": body, "live": True}


def _tilematrixsets(_payload: dict[str, Any]) -> ToolResult:
    status, body = client.get_json(f"{_OTA_BASE}/tilematrixsets", None)
    if status != 200:
        return status, body
    return 200, {"tileMatrixSets": body, "live": True}


def _conformance(_payload: dict[str, Any]) -> ToolResult:
    status, body = client.get_json(f"{_OTA_BASE}/conformance", None)
    if status != 200:
        return status, body
    return 200, {"conformance": body, "live": True}


register(
    Tool(
        name="os_tiles_ota.collections",
        description="List OS NGD OTA tile collections.",
        input_schema={
            "type": "object",
            "properties": {"tool": {"type": "string", "const": "os_tiles_ota.collections"}},
            "required": [],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {"collections": {"type": ["object", "array"]}, "live": {"type": "boolean"}},
            "required": ["collections"],
            "additionalProperties": True,
        },
        handler=_collections,
    )
)

register(
    Tool(
        name="os_tiles_ota.tilematrixsets",
        description="List OS NGD OTA tile matrix sets.",
        input_schema={
            "type": "object",
            "properties": {"tool": {"type": "string", "const": "os_tiles_ota.tilematrixsets"}},
            "required": [],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {"tileMatrixSets": {"type": ["object", "array"]}, "live": {"type": "boolean"}},
            "required": ["tileMatrixSets"],
            "additionalProperties": True,
        },
        handler=_tilematrixsets,
    )
)

register(
    Tool(
        name="os_tiles_ota.conformance",
        description="List OGC conformance classes supported by OS NGD OTA.",
        input_schema={
            "type": "object",
            "properties": {"tool": {"type": "string", "const": "os_tiles_ota.conformance"}},
            "required": [],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {"conformance": {"type": ["object", "array"]}, "live": {"type": "boolean"}},
            "required": ["conformance"],
            "additionalProperties": True,
        },
        handler=_conformance,
    )
)

