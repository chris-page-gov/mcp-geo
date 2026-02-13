from __future__ import annotations

from typing import Any

from server.config import settings
from tools.os_common import client
from tools.os_delivery import (
    now_utc_iso,
    parse_delivery,
    parse_inline_max_bytes,
    payload_bytes,
    select_delivery_mode,
    write_resource_payload,
)
from tools.registry import Tool, ToolResult, register

_OSNET_BASE = "https://api.os.uk/positioning/osnet/v1"


def _invalid(message: str) -> ToolResult:
    return 400, {"isError": True, "code": "INVALID_INPUT", "message": message}


def _rinex_years(_payload: dict[str, Any]) -> ToolResult:
    status, body = client.get_json(f"{_OSNET_BASE}/rinex", None)
    if status != 200:
        return status, body
    return 200, {"rinex": body, "live": True}


def _station_get(payload: dict[str, Any]) -> ToolResult:
    station_id = str(payload.get("stationId", "")).strip()
    if not station_id:
        return _invalid("stationId is required")
    status, body = client.get_json(f"{_OSNET_BASE}/stations/{station_id}", None)
    if status != 200:
        return status, body
    return 200, {"stationId": station_id, "station": body, "live": True}


def _station_log(payload: dict[str, Any]) -> ToolResult:
    station_id = str(payload.get("stationId", "")).strip()
    if not station_id:
        return _invalid("stationId is required")

    delivery, delivery_err = parse_delivery(payload.get("delivery"), default="auto")
    if delivery_err:
        return _invalid(delivery_err)
    inline_max_bytes, max_err = parse_inline_max_bytes(payload.get("inlineMaxBytes"))
    if max_err:
        return _invalid(max_err)

    status, body = client.get_bytes(f"{_OSNET_BASE}/stations/{station_id}/log", None)
    if status != 200:
        return status, body
    content = body.get("content")
    if not isinstance(content, (bytes, bytearray)):
        return 500, {
            "isError": True,
            "code": "INTEGRATION_ERROR",
            "message": "OS Net station log returned invalid bytes payload.",
        }
    text = bytes(content).decode("utf-8", "replace")
    payload_data = {
        "stationId": station_id,
        "contentType": body.get("contentType", "text/plain"),
        "encoding": "utf-8",
        "text": text,
        "createdAt": now_utc_iso(),
    }
    size = payload_bytes(payload_data)
    mode = select_delivery_mode(
        requested_delivery=delivery or "auto",
        payload_bytes=size,
        inline_max_bytes=inline_max_bytes or int(getattr(settings, "OS_EXPORT_INLINE_MAX_BYTES", 200_000)),
    )
    if mode == "resource":
        meta = write_resource_payload(prefix=f"os-net-station-log-{station_id}", payload=payload_data)
        return 200, {
            "stationId": station_id,
            "delivery": "resource",
            "resourceUri": meta["resourceUri"],
            "bytes": meta["bytes"],
            "sha256": meta["sha256"],
            "live": True,
        }
    return 200, {
        "stationId": station_id,
        "delivery": "inline",
        "bytes": size,
        "log": payload_data,
        "live": True,
    }


register(
    Tool(
        name="os_net.rinex_years",
        description="List OS Net RINEX years.",
        input_schema={
            "type": "object",
            "properties": {"tool": {"type": "string", "const": "os_net.rinex_years"}},
            "required": [],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {"rinex": {"type": ["object", "array"]}, "live": {"type": "boolean"}},
            "required": ["rinex"],
            "additionalProperties": True,
        },
        handler=_rinex_years,
    )
)

register(
    Tool(
        name="os_net.station_get",
        description="Get OS Net station metadata by stationId.",
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "os_net.station_get"},
                "stationId": {"type": "string"},
            },
            "required": ["stationId"],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "stationId": {"type": "string"},
                "station": {"type": ["object", "array"]},
                "live": {"type": "boolean"},
            },
            "required": ["stationId", "station"],
            "additionalProperties": True,
        },
        handler=_station_get,
    )
)

register(
    Tool(
        name="os_net.station_log",
        description="Get OS Net station log text with inline/resource delivery controls.",
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "os_net.station_log"},
                "stationId": {"type": "string"},
                "delivery": {"type": "string", "enum": ["inline", "resource", "auto"]},
                "inlineMaxBytes": {"type": "integer", "minimum": 1},
            },
            "required": ["stationId"],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "stationId": {"type": "string"},
                "delivery": {"type": "string"},
                "resourceUri": {"type": "string"},
                "log": {"type": "object"},
            },
            "required": ["stationId", "delivery"],
            "additionalProperties": True,
        },
        handler=_station_log,
    )
)

