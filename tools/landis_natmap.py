from __future__ import annotations

from server.landis import (
    LandisWarehouseDisabled,
    LandisWarehouseUnavailable,
    get_landis_warehouse,
)
from tools.landis_common import (
    error,
    natmap_area_summary_payload,
    natmap_point_payload,
    natmap_thematic_area_summary_payload,
    resolve_area_input,
)
from tools.registry import Tool, ToolResult, register

_ALLOWED_THEMATIC_PRODUCTS = {
    "natmap-soilscapes",
    "natmap-topsoil-texture",
    "natmap-subsoil-texture",
    "natmap-substrate-texture",
    "natmap-available-water",
    "natmap-carbon",
    "natmap-wrb2006",
    "natmap-regions",
}


def _disabled_error(reason: str) -> ToolResult:
    if reason == "landis_warehouse_unconfigured":
        return error("LandIS warehouse is not configured", code="LIVE_DISABLED", status=503)
    return error("LandIS live data access is disabled", code="LIVE_DISABLED", status=503)


def _point(payload: dict[str, object]) -> ToolResult:
    lat = payload.get("lat")
    lon = payload.get("lon")
    if not isinstance(lat, (int, float)):
        return error("lat must be numeric")
    if not isinstance(lon, (int, float)):
        return error("lon must be numeric")
    warehouse = get_landis_warehouse()
    try:
        row = warehouse.natmap_point(lat=float(lat), lon=float(lon))
    except LandisWarehouseDisabled as exc:
        return _disabled_error(str(exc))
    except LandisWarehouseUnavailable:
        return error("LandIS warehouse is unavailable", code="UPSTREAM_CONNECT_ERROR", status=503)
    if row is None:
        return error("No NATMAP coverage found for the supplied point", code="NOT_FOUND", status=404)
    return 200, natmap_point_payload(float(lat), float(lon), row)


def _area_summary(payload: dict[str, object]) -> ToolResult:
    area_input, message = resolve_area_input(payload)
    if area_input is None:
        return error(message or "Provide bbox or geometry")
    warehouse = get_landis_warehouse()
    try:
        summary = warehouse.natmap_area_summary(geometry=area_input.geometry)
    except LandisWarehouseDisabled as exc:
        return _disabled_error(str(exc))
    except LandisWarehouseUnavailable:
        return error("LandIS warehouse is unavailable", code="UPSTREAM_CONNECT_ERROR", status=503)
    if summary is None:
        return error("No NATMAP coverage found for the supplied area", code="NOT_FOUND", status=404)
    input_payload = {"geometry": area_input.geometry}
    if area_input.bbox is not None:
        input_payload = {"bbox": area_input.bbox}
    return 200, natmap_area_summary_payload(input_payload, summary)


def _thematic_area_summary(payload: dict[str, object]) -> ToolResult:
    product_id = payload.get("productId")
    if not isinstance(product_id, str) or product_id not in _ALLOWED_THEMATIC_PRODUCTS:
        allowed = ", ".join(sorted(_ALLOWED_THEMATIC_PRODUCTS))
        return error(f"productId must be one of: {allowed}")
    area_input, message = resolve_area_input(payload)
    if area_input is None:
        return error(message or "Provide bbox or geometry")
    warehouse = get_landis_warehouse()
    try:
        summary = warehouse.natmap_thematic_area_summary(
            product_id=product_id,
            geometry=area_input.geometry,
        )
    except LandisWarehouseDisabled as exc:
        return _disabled_error(str(exc))
    except LandisWarehouseUnavailable:
        return error("LandIS warehouse is unavailable", code="UPSTREAM_CONNECT_ERROR", status=503)
    if summary is None:
        return error(
            "No NATMAP thematic coverage found for the supplied area",
            code="NOT_FOUND",
            status=404,
        )
    input_payload = {"geometry": area_input.geometry}
    if area_input.bbox is not None:
        input_payload = {"bbox": area_input.bbox}
    return 200, natmap_thematic_area_summary_payload(input_payload, summary)


register(
    Tool(
        name="landis_natmap.point",
        description="Get the NATMAP map unit at a WGS84 lat/lon.",
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "landis_natmap.point"},
                "lat": {"type": "number"},
                "lon": {"type": "number"},
            },
            "required": ["lat", "lon"],
            "additionalProperties": False,
        },
        output_schema={"type": "object"},
        handler=_point,
    )
)

register(
    Tool(
        name="landis_natmap.area_summary",
        description="Summarize NATMAP map units across a bbox or GeoJSON polygon.",
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "landis_natmap.area_summary"},
                "bbox": {
                    "type": "array",
                    "items": {"type": "number"},
                    "minItems": 4,
                    "maxItems": 4,
                },
                "geometry": {"type": "object"},
            },
            "additionalProperties": False,
        },
        output_schema={"type": "object"},
        handler=_area_summary,
    )
)

register(
    Tool(
        name="landis_natmap.thematic_area_summary",
        description="Summarize one NATMAP thematic product across a bbox or GeoJSON polygon.",
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "landis_natmap.thematic_area_summary"},
                "productId": {"type": "string"},
                "bbox": {
                    "type": "array",
                    "items": {"type": "number"},
                    "minItems": 4,
                    "maxItems": 4,
                },
                "geometry": {"type": "object"},
            },
            "required": ["productId"],
            "additionalProperties": False,
        },
        output_schema={"type": "object"},
        handler=_thematic_area_summary,
    )
)
