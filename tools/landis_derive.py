from __future__ import annotations

from server.landis import LandisWarehouseDisabled, LandisWarehouseUnavailable, get_landis_warehouse
from tools.landis_common import error, pipe_risk_payload, resolve_area_input
from tools.registry import Tool, ToolResult, register


def _live_disabled_message(reason: str) -> str:
    if reason == "landis_warehouse_unconfigured":
        return "LandIS live mode requires LANDIS_WAREHOUSE_DSN or BOUNDARY_CACHE_DSN."
    return "LandIS live mode is disabled. Set LANDIS_ENABLED=true and LANDIS_LIVE_ENABLED=true."


def _pipe_risk(payload: dict[str, object]) -> ToolResult:
    area_input, err = resolve_area_input(payload)
    if err:
        return error(err)
    assert area_input is not None
    warehouse = get_landis_warehouse()
    try:
        summary = warehouse.pipe_risk_summary(geometry=area_input.geometry)
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
            "No LandIS pipe-risk coverage found for the supplied area",
            code="NOT_FOUND",
            status=404,
        )
    input_payload = {
        "bbox": area_input.bbox,
        "geometryType": area_input.geometry.get("type"),
    }
    return 200, pipe_risk_payload(input_payload, summary)


register(
    Tool(
        name="landis_derive.pipe_risk",
        description=(
            "Screen corrosion and shrink-swell pipe risk for a bbox or "
            "GeoJSON Polygon/MultiPolygon."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "landis_derive.pipe_risk"},
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
                "riskBand": {"type": "string"},
                "scores": {"type": "object"},
                "rawEvidence": {"type": "object"},
                "explanation": {"type": "string"},
                "caveats": {"type": "array"},
                "verificationChecklist": {"type": "array"},
                "provenance": {"type": "object"},
            },
            "required": [
                "input",
                "riskBand",
                "scores",
                "rawEvidence",
                "explanation",
                "caveats",
                "verificationChecklist",
                "provenance",
            ],
            "additionalProperties": False,
        },
        handler=_pipe_risk,
    )
)
