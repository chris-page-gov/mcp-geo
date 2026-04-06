from __future__ import annotations

from typing import Any

from server.landis import (
    LandisWarehouseDisabled,
    LandisWarehouseUnavailable,
    get_landis_warehouse,
)
from tools.landis_common import (
    area_summary_payload,
    error,
    resolve_area_input,
    soilscape_response_payload,
)
from tools.registry import Tool, ToolResult, register


def _live_disabled_message(reason: str) -> str:
    if reason == "landis_warehouse_unconfigured":
        return "LandIS live mode requires LANDIS_WAREHOUSE_DSN or BOUNDARY_CACHE_DSN."
    return "LandIS live mode is disabled. Set LANDIS_ENABLED=true and LANDIS_LIVE_ENABLED=true."


def _point(payload: dict[str, Any]) -> ToolResult:
    lat = payload.get("lat")
    lon = payload.get("lon")
    if not isinstance(lat, (int, float)):
        return error("lat must be a number")
    if not isinstance(lon, (int, float)):
        return error("lon must be a number")

    warehouse = get_landis_warehouse()
    try:
        result = warehouse.soilscapes_point(lat=float(lat), lon=float(lon))
    except LandisWarehouseDisabled as exc:
        return 501, {
            "isError": True,
            "code": "LIVE_DISABLED",
            "message": _live_disabled_message(str(exc)),
        }
    except LandisWarehouseUnavailable:
        return 502, {
            "isError": True,
            "code": "UPSTREAM_CONNECT_ERROR",
            "message": "LandIS warehouse is unavailable.",
        }
    if result is None:
        return error(
            "No LandIS Soilscapes coverage found for the supplied location",
            code="NOT_FOUND",
            status=404,
        )
    return 200, soilscape_response_payload(float(lat), float(lon), result)


def _area_summary(payload: dict[str, Any]) -> ToolResult:
    area_input, err = resolve_area_input(payload)
    if err:
        return error(err)
    assert area_input is not None

    warehouse = get_landis_warehouse()
    try:
        summary = warehouse.soilscapes_area_summary(geometry=area_input.geometry)
    except LandisWarehouseDisabled as exc:
        return 501, {
            "isError": True,
            "code": "LIVE_DISABLED",
            "message": _live_disabled_message(str(exc)),
        }
    except LandisWarehouseUnavailable:
        return 502, {
            "isError": True,
            "code": "UPSTREAM_CONNECT_ERROR",
            "message": "LandIS warehouse is unavailable.",
        }
    if summary is None:
        return error(
            "No LandIS Soilscapes coverage found for the supplied area",
            code="NOT_FOUND",
            status=404,
        )
    input_payload = {
        "bbox": area_input.bbox,
        "geometryType": area_input.geometry.get("type"),
    }
    return 200, area_summary_payload(input_payload, summary)


register(
    Tool(
        name="landis_soilscapes.point",
        description="Return the LandIS Soilscapes class and caveats for a WGS84 point.",
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "landis_soilscapes.point"},
                "lat": {"type": "number"},
                "lon": {"type": "number"},
            },
            "required": ["lat", "lon"],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "location": {"type": "object"},
                "soilscape": {"type": "object"},
                "caveats": {"type": "array"},
                "provenance": {"type": "object"},
            },
            "required": ["location", "soilscape", "caveats", "provenance"],
            "additionalProperties": False,
        },
        handler=_point,
    )
)

register(
    Tool(
        name="landis_soilscapes.area_summary",
        description=(
            "Summarize LandIS Soilscapes coverage for a bbox or GeoJSON "
            "Polygon/MultiPolygon."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "landis_soilscapes.area_summary"},
                "bbox": {
                    "type": "array",
                    "items": {"type": "number"},
                    "minItems": 4,
                    "maxItems": 4,
                },
                "geometry": {"type": "object"},
            },
            "additionalProperties": False,
            "anyOf": [{"required": ["bbox"]}, {"required": ["geometry"]}],
        },
        output_schema={
            "type": "object",
            "properties": {
                "input": {"type": "object"},
                "areaSqM": {"type": "number"},
                "classes": {"type": "array"},
                "dominantClass": {"type": ["object", "null"]},
                "caveats": {"type": "array"},
                "provenance": {"type": "object"},
            },
            "required": ["input", "areaSqM", "classes", "caveats", "provenance"],
            "additionalProperties": False,
        },
        handler=_area_summary,
    )
)
