from __future__ import annotations

import re
from typing import Any

from server.route_graph import RouteGraph, SUPPORTED_ROUTE_PROFILES
from server.route_planning import normalize_coordinates, normalize_route_profile, normalize_stop
from tools.os_delivery import (
    parse_delivery,
    parse_inline_max_bytes,
    payload_bytes,
    select_delivery_mode,
    write_resource_payload,
)
from tools.os_names import _names_find
from tools.os_places import _by_postcode
from tools.os_places_extra import _places_by_uprn, _places_search
from tools.registry import Tool, ToolResult, register

_POSTCODE_ONLY_REGEX = re.compile(
    r"^[A-Z]{1,2}[0-9][0-9A-Z]?\s*[0-9][A-Z]{2}$",
    re.IGNORECASE,
)
_ADDRESS_HINT_REGEX = re.compile(
    r"\b(\d|street|st\.?|road|rd\.?|lane|ln\.?|avenue|ave\.?|place|close|drive|library|hall)\b",
    re.IGNORECASE,
)

def _error(status: int, code: str, message: str, **extra: Any) -> ToolResult:
    body: dict[str, Any] = {"isError": True, "code": code, "message": message}
    body.update(extra)
    return status, body


def _route_descriptor(_payload: dict[str, Any]) -> ToolResult:
    descriptor = _route_graph().descriptor()
    descriptor["status"] = "ready" if descriptor["graph"].get("ready") else "not_ready"
    return 200, descriptor


def _route_get(payload: dict[str, Any]) -> ToolResult:
    stops_value = payload.get("stops")
    via_value = payload.get("via")
    if not isinstance(stops_value, list) or len(stops_value) < 2:
        return _error(400, "INVALID_INPUT", "stops must contain at least two route stops")
    route_graph = _route_graph()
    if len(stops_value) > route_graph.max_stops():
        return _error(
            400,
            "INVALID_INPUT",
            f"stops supports at most {route_graph.max_stops()} entries",
        )
    if via_value is not None and not isinstance(via_value, list):
        return _error(400, "INVALID_INPUT", "via must be a list when provided")

    stops = [normalize_stop(stop) for stop in stops_value]
    via = [normalize_stop(stop) for stop in (via_value or [])]
    if any(stop is None for stop in stops) or any(stop is None for stop in via):
        return _error(
            400,
            "INVALID_INPUT",
            "Each stop must include exactly one of query, uprn, or coordinates",
        )

    constraints = payload.get("constraints", {})
    if constraints is None:
        constraints = {}
    if not isinstance(constraints, dict):
        return _error(400, "INVALID_INPUT", "constraints must be an object when provided")
    constraints = {
        "avoidAreas": constraints.get("avoidAreas") if isinstance(constraints.get("avoidAreas"), list) else [],
        "avoidIds": constraints.get("avoidIds") if isinstance(constraints.get("avoidIds"), list) else [],
        "softAvoid": bool(constraints.get("softAvoid", True)),
    }

    profile = normalize_route_profile(payload.get("profile"))
    delivery, delivery_error = parse_delivery(payload.get("delivery"), default="inline")
    if delivery_error:
        return _error(400, "INVALID_INPUT", delivery_error)
    inline_max_bytes, inline_error = parse_inline_max_bytes(payload.get("inlineMaxBytes"))
    if inline_error:
        return _error(400, "INVALID_INPUT", inline_error)

    ordered_stops = [stop for stop in stops if stop]  # type: ignore[list-item]
    if via:
        ordered_stops = [ordered_stops[0], *[stop for stop in via if stop], *ordered_stops[1:]]
    if len(ordered_stops) > route_graph.max_stops():
        return _error(
            400,
            "INVALID_INPUT",
            f"Combined stops and via entries support at most {route_graph.max_stops()} entries",
        )

    resolved_stops: list[dict[str, Any]] = []
    for index, stop in enumerate(ordered_stops):
        try:
            status, body = _resolve_stop(stop, index=index)
        except ValueError as exc:
            return _error(404, "STOP_NOT_FOUND", str(exc))
        if status != 200:
            return status, body
        resolved_stops.append(body)

    status, route_body = route_graph.compute_route(
        resolved_stops,
        profile=profile,
        constraints=constraints,
    )
    if status != 200:
        return status, route_body

    response = {
        "profile": profile,
        "requestedStops": ordered_stops,
        "requestedConstraints": constraints,
        **route_body,
    }
    mode = select_delivery_mode(
        requested_delivery=delivery or "inline",
        payload_bytes=payload_bytes(response),
        inline_max_bytes=inline_max_bytes or 200_000,
    )
    if mode == "inline":
        response["delivery"] = "inline"
        return 200, response
    export_meta = write_resource_payload(prefix="os-route", payload=response)
    return 200, {
        "delivery": "resource",
        "resourceUri": export_meta["resourceUri"],
        "bytes": export_meta["bytes"],
        "sha256": export_meta["sha256"],
        "path": export_meta["path"],
        "graph": response.get("graph"),
        "resolvedStops": response.get("resolvedStops"),
        "profile": profile,
    }


def _route_graph() -> RouteGraph:
    return RouteGraph.from_settings()


def _resolve_stop(stop: dict[str, Any], *, index: int) -> ToolResult:
    coordinates = normalize_coordinates(stop.get("coordinates"))
    if coordinates is not None:
        lon, lat = coordinates
        return 200, {
            "index": index,
            "input": stop,
            "label": f"{lat:.6f}, {lon:.6f}",
            "lat": lat,
            "lon": lon,
            "source": "coordinates",
            "confidence": "exact",
        }

    uprn = stop.get("uprn")
    if isinstance(uprn, str) and uprn.strip():
        status, body = _places_by_uprn({"uprn": uprn.strip()})
        if status != 200:
            return status, body
        result = body.get("result") if isinstance(body, dict) else None
        if not isinstance(result, dict):
            return _error(404, "STOP_NOT_FOUND", f"No stop found for UPRN {uprn}")
        return 200, _resolved_stop_payload(
            input_stop=stop,
            index=index,
            label=result.get("address") or uprn.strip(),
            lat=result.get("lat"),
            lon=result.get("lon"),
            source="os_places.by_uprn",
            confidence="exact",
            uprn=uprn.strip(),
        )

    query = stop.get("query")
    if not isinstance(query, str) or not query.strip():
        return _error(
            400,
            "INVALID_INPUT",
            "Each stop must include a query, uprn, or coordinates",
        )
    query_text = query.strip()

    if _POSTCODE_ONLY_REGEX.match(query_text):
        status, body = _by_postcode({"postcode": query_text})
        if status != 200:
            return status, body
        uprns = body.get("uprns") if isinstance(body, dict) else None
        if not isinstance(uprns, list) or not uprns:
            return _error(404, "STOP_NOT_FOUND", f"No stop found for postcode {query_text}")
        if len(uprns) > 1:
            return _error(
                409,
                "AMBIGUOUS_STOP",
                f"Postcode {query_text} resolves to multiple premises; provide a fuller address.",
                candidates=uprns[:5],
            )
        result = uprns[0]
        return 200, _resolved_stop_payload(
            input_stop=stop,
            index=index,
            label=result.get("address") or query_text,
            lat=result.get("lat"),
            lon=result.get("lon"),
            source="os_places.by_postcode",
            confidence="high",
            uprn=result.get("uprn"),
        )

    address_like = bool(_ADDRESS_HINT_REGEX.search(query_text))
    status, body = _places_search({"text": query_text, "limit": 5})
    if status == 200 and isinstance(body, dict):
        results = body.get("results")
        if isinstance(results, list) and results:
            if address_like:
                top = results[0]
                return 200, _resolved_stop_payload(
                    input_stop=stop,
                    index=index,
                    label=top.get("address") or query_text,
                    lat=top.get("lat"),
                    lon=top.get("lon"),
                    source="os_places.search",
                    confidence="high" if len(results) == 1 else "medium",
                    uprn=top.get("uprn"),
                    alternatives=results[1:5] if len(results) > 1 else [],
                )
            if len(results) == 1:
                top = results[0]
                return 200, _resolved_stop_payload(
                    input_stop=stop,
                    index=index,
                    label=top.get("address") or query_text,
                    lat=top.get("lat"),
                    lon=top.get("lon"),
                    source="os_places.search",
                    confidence="high",
                    uprn=top.get("uprn"),
                )

    status, body = _names_find({"text": query_text, "limit": 5})
    if status != 200:
        if address_like and isinstance(body, dict):
            return _error(
                404,
                "STOP_NOT_FOUND",
                f"No route stop found for '{query_text}'",
                upstream=body,
            )
        return status, body
    results = body.get("results") if isinstance(body, dict) else None
    if not isinstance(results, list) or not results:
        return _error(404, "STOP_NOT_FOUND", f"No route stop found for '{query_text}'")
    if len(results) > 1:
        exact_matches = [
            item
            for item in results
            if str(item.get("name1") or "").strip().lower() == query_text.lower()
        ]
        if len(exact_matches) == 1:
            top = exact_matches[0]
            return 200, _resolved_stop_payload(
                input_stop=stop,
                index=index,
                label=top.get("name1") or query_text,
                lat=top.get("lat"),
                lon=top.get("lon"),
                source="os_names.find",
                confidence="medium",
                alternatives=results[:5],
            )
        return _error(
            409,
            "AMBIGUOUS_STOP",
            f"Multiple route stop candidates matched '{query_text}'",
            candidates=results[:5],
        )
    top = results[0]
    return 200, _resolved_stop_payload(
        input_stop=stop,
        index=index,
        label=top.get("name1") or query_text,
        lat=top.get("lat"),
        lon=top.get("lon"),
        source="os_names.find",
        confidence="high",
    )


def _resolved_stop_payload(
    *,
    input_stop: dict[str, Any],
    index: int,
    label: Any,
    lat: Any,
    lon: Any,
    source: str,
    confidence: str,
    uprn: Any = None,
    alternatives: list[Any] | None = None,
) -> dict[str, Any]:
    try:
        lat_value = float(lat)
        lon_value = float(lon)
    except (TypeError, ValueError):
        raise ValueError(f"Resolved stop {index} is missing coordinates") from None
    payload = {
        "index": index,
        "input": input_stop,
        "label": str(label or input_stop.get("query") or input_stop.get("uprn") or f"Stop {index + 1}"),
        "lat": lat_value,
        "lon": lon_value,
        "source": source,
        "confidence": confidence,
    }
    if uprn is not None:
        payload["uprn"] = uprn
    if alternatives:
        payload["alternatives"] = alternatives
    return payload


register(
    Tool(
        name="os_route.descriptor",
        description="Describe MCP Geo route-planning capabilities and graph readiness.",
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "os_route.descriptor"},
            },
            "required": [],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "supportedProfiles": {
                    "type": "array",
                    "items": {"type": "string", "enum": list(SUPPORTED_ROUTE_PROFILES)},
                },
                "constraintTypes": {"type": "array", "items": {"type": "string"}},
                "maxStops": {"type": "integer"},
                "graph": {"type": "object"},
            },
            "required": ["status", "supportedProfiles", "constraintTypes", "maxStops", "graph"],
        },
        handler=_route_descriptor,
    )
)

register(
    Tool(
        name="os_route.get",
        description="Resolve route stops and compute a pgRouting-backed route.",
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "os_route.get"},
                "stops": {
                    "type": "array",
                    "minItems": 2,
                    "items": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "uprn": {"type": "string"},
                            "coordinates": {
                                "oneOf": [
                                    {
                                        "type": "array",
                                        "items": {"type": "number"},
                                        "minItems": 2,
                                        "maxItems": 2,
                                    },
                                    {
                                        "type": "object",
                                        "properties": {
                                            "lat": {"type": "number"},
                                            "lon": {"type": "number"},
                                        },
                                        "required": ["lat", "lon"],
                                        "additionalProperties": False,
                                    },
                                ]
                            },
                        },
                        "additionalProperties": False,
                    },
                },
                "via": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "uprn": {"type": "string"},
                            "coordinates": {
                                "oneOf": [
                                    {
                                        "type": "array",
                                        "items": {"type": "number"},
                                        "minItems": 2,
                                        "maxItems": 2,
                                    },
                                    {
                                        "type": "object",
                                        "properties": {
                                            "lat": {"type": "number"},
                                            "lon": {"type": "number"},
                                        },
                                        "required": ["lat", "lon"],
                                        "additionalProperties": False,
                                    },
                                ]
                            },
                        },
                        "additionalProperties": False,
                    },
                },
                "profile": {
                    "type": "string",
                    "enum": list(SUPPORTED_ROUTE_PROFILES),
                },
                "constraints": {
                    "type": "object",
                    "properties": {
                        "avoidAreas": {
                            "type": "array",
                            "items": {
                                "oneOf": [
                                    {
                                        "type": "array",
                                        "items": {"type": "number"},
                                        "minItems": 4,
                                        "maxItems": 4,
                                    },
                                    {
                                        "type": "object",
                                        "properties": {
                                            "type": {"type": "string", "const": "Polygon"},
                                            "coordinates": {
                                                "type": "array",
                                                "items": {
                                                    "type": "array",
                                                    "items": {
                                                        "type": "array",
                                                        "items": {"type": "number"},
                                                    },
                                                },
                                            },
                                        },
                                        "required": ["type", "coordinates"],
                                        "additionalProperties": False,
                                    },
                                    {
                                        "type": "object",
                                        "properties": {
                                            "type": {"type": "string", "const": "MultiPolygon"},
                                            "coordinates": {
                                                "type": "array",
                                                "items": {
                                                    "type": "array",
                                                    "items": {
                                                        "type": "array",
                                                        "items": {
                                                            "type": "array",
                                                            "items": {"type": "number"},
                                                        },
                                                    },
                                                },
                                            },
                                        },
                                        "required": ["type", "coordinates"],
                                        "additionalProperties": False,
                                    },
                                ]
                            },
                        },
                        "avoidIds": {"type": "array", "items": {"type": "string"}},
                        "softAvoid": {"type": "boolean"},
                    },
                    "additionalProperties": False,
                },
                "delivery": {"type": "string", "enum": ["inline", "resource", "auto"]},
                "inlineMaxBytes": {"type": "integer", "minimum": 1},
            },
            "required": ["stops"],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "profile": {"type": "string"},
                "resolvedStops": {"type": "array", "items": {"type": "object"}},
                "distanceMeters": {"type": "number"},
                "durationSeconds": {"type": "number"},
                "route": {"type": "object"},
                "legs": {"type": "array", "items": {"type": "object"}},
                "steps": {"type": "array", "items": {"type": "object"}},
                "modeChanges": {"type": "array", "items": {"type": "object"}},
                "warnings": {"type": "array", "items": {"type": "object"}},
                "restrictions": {"type": "array", "items": {"type": "object"}},
                "graph": {"type": "object"},
                "delivery": {"type": "string"},
                "resourceUri": {"type": "string"},
            },
            "required": ["profile"],
        },
        handler=_route_get,
    )
)
