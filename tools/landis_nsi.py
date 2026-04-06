from __future__ import annotations

from tools.landis_common import error, nsi_profile_payload, nsi_sites_payload, parse_limit, parse_offset, resolve_area_input
from tools.registry import Tool, ToolResult, register
from tools.typing_utils import is_strict_int
from server.landis import LandisWarehouseDisabled, LandisWarehouseUnavailable, get_landis_warehouse


def _disabled_error(reason: str) -> ToolResult:
    if reason == "landis_warehouse_unconfigured":
        return error("LandIS warehouse is not configured", code="LIVE_DISABLED", status=503)
    return error("LandIS live data access is disabled", code="LIVE_DISABLED", status=503)


def _parse_distance(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)) and float(value) > 0:
        return float(value)
    return None


def _nearest_sites(payload: dict[str, object]) -> ToolResult:
    lat = payload.get("lat")
    lon = payload.get("lon")
    if not isinstance(lat, (int, float)):
        return error("lat must be numeric")
    if not isinstance(lon, (int, float)):
        return error("lon must be numeric")
    limit = parse_limit(payload.get("limit"))
    if limit is None:
        return error("limit must be an integer between 1 and 100")
    max_distance_km = _parse_distance(payload.get("maxDistanceKm"))
    if payload.get("maxDistanceKm") is not None and max_distance_km is None:
        return error("maxDistanceKm must be a positive number")
    warehouse = get_landis_warehouse()
    try:
        summary = warehouse.nsi_nearest_sites(
            lat=float(lat),
            lon=float(lon),
            limit=limit,
            max_distance_km=max_distance_km,
        )
    except LandisWarehouseDisabled as exc:
        return _disabled_error(str(exc))
    except LandisWarehouseUnavailable:
        return error("LandIS warehouse is unavailable", code="UPSTREAM_CONNECT_ERROR", status=503)
    return 200, nsi_sites_payload({"location": {"lat": float(lat), "lon": float(lon)}}, summary)


def _within_area(payload: dict[str, object]) -> ToolResult:
    area_input, message = resolve_area_input(payload)
    if area_input is None:
        return error(message or "Provide bbox or geometry")
    limit = parse_limit(payload.get("limit"))
    if limit is None:
        return error("limit must be an integer between 1 and 100")
    offset = parse_offset(payload.get("offset"))
    if offset is None:
        return error("offset must be a non-negative integer")
    warehouse = get_landis_warehouse()
    try:
        summary = warehouse.nsi_sites_within_area(
            geometry=area_input.geometry,
            limit=limit,
            offset=offset,
        )
    except LandisWarehouseDisabled as exc:
        return _disabled_error(str(exc))
    except LandisWarehouseUnavailable:
        return error("LandIS warehouse is unavailable", code="UPSTREAM_CONNECT_ERROR", status=503)
    input_payload: dict[str, object] = {"geometry": area_input.geometry}
    if area_input.bbox is not None:
        input_payload = {"bbox": area_input.bbox, "offset": offset, "limit": limit}
    return 200, nsi_sites_payload(input_payload, summary)


def _profile_summary(payload: dict[str, object]) -> ToolResult:
    nsi_id = payload.get("nsiId")
    if not is_strict_int(nsi_id) or int(nsi_id) <= 0:
        return error("nsiId must be a positive integer")
    warehouse = get_landis_warehouse()
    try:
        summary = warehouse.nsi_profile_summary(nsi_id=int(nsi_id))
    except LandisWarehouseDisabled as exc:
        return _disabled_error(str(exc))
    except LandisWarehouseUnavailable:
        return error("LandIS warehouse is unavailable", code="UPSTREAM_CONNECT_ERROR", status=503)
    if summary is None:
        return error("Unknown NSI site identifier", code="NOT_FOUND", status=404)
    return 200, nsi_profile_payload(int(nsi_id), summary)


register(
    Tool(
        name="landis_nsi.nearest_sites",
        description="Find the nearest LandIS NSI evidence sites to a WGS84 point.",
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "landis_nsi.nearest_sites"},
                "lat": {"type": "number"},
                "lon": {"type": "number"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 100},
                "maxDistanceKm": {"type": "number", "exclusiveMinimum": 0},
            },
            "required": ["lat", "lon"],
            "additionalProperties": False,
        },
        output_schema={"type": "object"},
        handler=_nearest_sites,
    )
)

register(
    Tool(
        name="landis_nsi.within_area",
        description="List LandIS NSI evidence sites within a bbox or GeoJSON polygon.",
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "landis_nsi.within_area"},
                "bbox": {
                    "type": "array",
                    "items": {"type": "number"},
                    "minItems": 4,
                    "maxItems": 4,
                },
                "geometry": {"type": "object"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 100},
                "offset": {"oneOf": [{"type": "integer", "minimum": 0}, {"type": "string"}]},
            },
            "additionalProperties": False,
        },
        output_schema={"type": "object"},
        handler=_within_area,
    )
)

register(
    Tool(
        name="landis_nsi.profile_summary",
        description="Get an evidence summary for one LandIS NSI site identifier.",
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "landis_nsi.profile_summary"},
                "nsiId": {"type": "integer", "minimum": 1},
            },
            "required": ["nsiId"],
            "additionalProperties": False,
        },
        output_schema={"type": "object"},
        handler=_profile_summary,
    )
)
