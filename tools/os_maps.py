from __future__ import annotations

import base64
from typing import Any

from server.config import settings
from tools.os_common import client
from tools.os_delivery import (
    parse_delivery,
    parse_inline_max_bytes,
    payload_bytes,
    select_delivery_mode,
    write_resource_payload,
)
from tools.registry import get as get_tool
from tools.registry import Tool, register

# Maps render metadata: return a usable static image URL (OSM-backed proxy)


def _error(message: str) -> tuple[int, dict[str, Any]]:
    return 400, {
        "isError": True,
        "code": "INVALID_INPUT",
        "message": message,
    }


def _num(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _feature_point(item: Any) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None
    if item.get("type") == "Feature":
        geometry = item.get("geometry")
        if (
            isinstance(geometry, dict)
            and geometry.get("type") == "Point"
            and isinstance(geometry.get("coordinates"), list)
            and len(geometry["coordinates"]) >= 2
        ):
            return item
        return None
    coords = item.get("coordinates")
    if isinstance(coords, list) and len(coords) >= 2:
        lon = _num(coords[0])
        lat = _num(coords[1])
    else:
        lon = _num(item.get("lon"))
        if lon is None:
            lon = _num(item.get("lng"))
        lat = _num(item.get("lat"))
    if lon is None or lat is None:
        return None
    return {
        "type": "Feature",
        "properties": item.get("properties") if isinstance(item.get("properties"), dict) else {},
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
    }


def _feature_line(item: Any) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None
    if item.get("type") == "Feature":
        geometry = item.get("geometry")
        if isinstance(geometry, dict) and geometry.get("type") in {"LineString", "MultiLineString"}:
            return item
        return None
    geometry = item.get("geometry")
    if isinstance(geometry, dict) and geometry.get("type") in {"LineString", "MultiLineString"}:
        return {
            "type": "Feature",
            "properties": item.get("properties") if isinstance(item.get("properties"), dict) else {},
            "geometry": geometry,
        }
    return None


def _feature_polygon(item: Any) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None
    if item.get("type") == "Feature":
        geometry = item.get("geometry")
        if isinstance(geometry, dict) and geometry.get("type") in {"Polygon", "MultiPolygon"}:
            return item
        return None
    geometry = item.get("geometry")
    if isinstance(geometry, dict) and geometry.get("type") in {"Polygon", "MultiPolygon"}:
        return {
            "type": "Feature",
            "properties": item.get("properties") if isinstance(item.get("properties"), dict) else {},
            "geometry": geometry,
        }
    return None


def _normalize_feature_collection(raw: Any, *, kind: str) -> list[dict[str, Any]]:
    if raw is None:
        return []
    items: list[Any]
    if isinstance(raw, dict) and raw.get("type") == "FeatureCollection":
        feats = raw.get("features")
        items = feats if isinstance(feats, list) else []
    elif isinstance(raw, list):
        items = raw
    else:
        return []
    out: list[dict[str, Any]] = []
    for item in items:
        feature: dict[str, Any] | None
        if kind == "point":
            feature = _feature_point(item)
        elif kind == "line":
            feature = _feature_line(item)
        else:
            feature = _feature_polygon(item)
        if feature:
            out.append(feature)
    return out


def _normalize_local_layers(raw: Any) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    layers: list[dict[str, Any]] = []
    for idx, item in enumerate(raw):
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        if not isinstance(name, str) or not name.strip():
            name = f"local_layer_{idx + 1}"
        geojson = item.get("geojson")
        features = _normalize_feature_collection(geojson, kind="polygon")
        if not features and isinstance(geojson, dict):
            if geojson.get("type") == "Feature":
                features = [geojson]
        if not features:
            continue
        kind = item.get("kind")
        if not isinstance(kind, str) or kind not in {"point", "line", "polygon"}:
            first_geom = features[0].get("geometry") if isinstance(features[0], dict) else None
            gtype = first_geom.get("type") if isinstance(first_geom, dict) else None
            if gtype in {"Point", "MultiPoint"}:
                kind = "point"
            elif gtype in {"LineString", "MultiLineString"}:
                kind = "line"
            else:
                kind = "polygon"
        layers.append(
            {
                "id": item.get("id") if isinstance(item.get("id"), str) else f"local_{idx + 1}",
                "name": name,
                "kind": kind,
                "source": "local",
                "interactive": True,
                "features": features,
            }
        )
    return layers


def _build_uprn_features(raw: Any) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    out: list[dict[str, Any]] = []
    for row in raw:
        if not isinstance(row, dict):
            continue
        lon = _num(row.get("lon"))
        lat = _num(row.get("lat"))
        if lon is None or lat is None:
            continue
        props = {
            "uprn": row.get("uprn"),
            "address": row.get("address"),
            "postcode": row.get("postcode"),
        }
        out.append(
            {
                "type": "Feature",
                "properties": {k: v for k, v in props.items() if v is not None},
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
            }
        )
    return out


def _extract_inventory_overlay_layers(inventory: dict[str, Any]) -> list[dict[str, Any]]:
    layers = inventory.get("layers")
    if not isinstance(layers, dict):
        return []
    out: list[dict[str, Any]] = []
    uprn = layers.get("uprns")
    if isinstance(uprn, dict):
        features = _build_uprn_features(uprn.get("results"))
        if features:
            out.append(
                {
                    "id": "inventory_uprns",
                    "name": "UPRNs",
                    "kind": "point",
                    "source": "os_map.inventory",
                    "interactive": True,
                    "features": features,
                    "count": len(features),
                }
            )
    ngd_map = {
        "buildings": ("inventory_buildings", "Buildings", "polygon"),
        "road_links": ("inventory_road_links", "Road Links", "line"),
        "path_links": ("inventory_path_links", "Path Links", "line"),
    }
    for key, (layer_id, title, kind) in ngd_map.items():
        row = layers.get(key)
        if not isinstance(row, dict):
            continue
        feats = row.get("features")
        if not isinstance(feats, list) or not feats:
            continue
        out.append(
            {
                "id": layer_id,
                "name": title,
                "kind": kind,
                "source": "os_map.inventory",
                "interactive": False,
                "collection": row.get("collection"),
                "features": feats,
                "count": len(feats),
                "nextPageToken": row.get("nextPageToken"),
            }
        )
    return out


def _normalize_overlay_layers(payload: dict[str, Any]) -> list[dict[str, Any]]:
    overlays = payload.get("overlays")
    if overlays is None:
        overlays = {}
    if not isinstance(overlays, dict):
        return []
    points = _normalize_feature_collection(overlays.get("points"), kind="point")
    lines = _normalize_feature_collection(overlays.get("lines"), kind="line")
    polygons = _normalize_feature_collection(overlays.get("polygons"), kind="polygon")
    out: list[dict[str, Any]] = []
    if points:
        out.append(
            {
                "id": "input_points",
                "name": "Input points",
                "kind": "point",
                "source": "input",
                "interactive": True,
                "features": points,
                "count": len(points),
            }
        )
    if lines:
        out.append(
            {
                "id": "input_lines",
                "name": "Input lines",
                "kind": "line",
                "source": "input",
                "interactive": True,
                "features": lines,
                "count": len(lines),
            }
        )
    if polygons:
        out.append(
            {
                "id": "input_polygons",
                "name": "Input polygons",
                "kind": "polygon",
                "source": "input",
                "interactive": True,
                "features": polygons,
                "count": len(polygons),
            }
        )
    out.extend(_normalize_local_layers(overlays.get("localLayers")))
    for layer in out:
        layer.setdefault("count", len(layer.get("features", [])))
    return out


def _overlay_summary(layers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summary: list[dict[str, Any]] = []
    for layer in layers:
        summary.append(
            {
                "id": layer.get("id"),
                "name": layer.get("name"),
                "kind": layer.get("kind"),
                "source": layer.get("source"),
                "count": layer.get("count", 0),
                "interactive": bool(layer.get("interactive")),
                "collection": layer.get("collection"),
                "nextPageToken": layer.get("nextPageToken"),
            }
        )
    return summary


def _build_inventory_request(payload: dict[str, Any], bbox: list[float]) -> dict[str, Any]:
    req: dict[str, Any] = {"tool": "os_map.inventory", "bbox": bbox}
    inv = payload.get("inventory")
    if not isinstance(inv, dict):
        inv = {}
    for key in ("layers", "limits", "pageTokens", "includeGeometry", "collections"):
        value = inv.get(key)
        if value is not None:
            req[key] = value
    return req


def _maps_wmts_capabilities(payload: dict[str, Any]):
    delivery, delivery_err = parse_delivery(payload.get("delivery"), default="auto")
    if delivery_err:
        return _error(delivery_err)
    inline_max_bytes, max_err = parse_inline_max_bytes(payload.get("inlineMaxBytes"))
    if max_err:
        return _error(max_err)

    params: dict[str, Any] = {"service": "WMTS", "request": "GetCapabilities"}
    version = payload.get("version")
    if isinstance(version, str) and version.strip():
        params["version"] = version.strip()

    status, body = client.get_bytes("https://api.os.uk/maps/raster/v1/wmts", params)
    if status != 200:
        return status, body
    content = body.get("content")
    if not isinstance(content, (bytes, bytearray)):
        return 500, {
            "isError": True,
            "code": "INTEGRATION_ERROR",
            "message": "WMTS capabilities response was not binary content.",
        }
    text = bytes(content).decode("utf-8", "replace")
    response_payload = {
        "contentType": str(body.get("contentType", "application/xml")),
        "service": "WMTS",
        "request": "GetCapabilities",
        "xml": text,
        "bytes": len(content),
        "live": True,
    }
    selected_mode = select_delivery_mode(
        requested_delivery=delivery or "auto",
        payload_bytes=payload_bytes(response_payload),
        inline_max_bytes=inline_max_bytes or int(getattr(settings, "OS_EXPORT_INLINE_MAX_BYTES", 200_000)),
    )
    if selected_mode == "resource":
        meta = write_resource_payload(prefix="os-maps-wmts-capabilities", payload=response_payload)
        return 200, {
            "delivery": "resource",
            "resourceUri": meta["resourceUri"],
            "bytes": meta["bytes"],
            "sha256": meta["sha256"],
            "contentType": response_payload["contentType"],
            "live": True,
        }
    response_payload["delivery"] = "inline"
    return 200, response_payload


def _maps_raster_tile(payload: dict[str, Any]):
    style = str(payload.get("style", "Road_3857")).strip() or "Road_3857"
    try:
        z = int(payload.get("z"))
        x = int(payload.get("x"))
        y = int(payload.get("y"))
    except Exception:
        return _error("z/x/y must be integers")
    if min(z, x, y) < 0:
        return _error("z/x/y must be non-negative")

    image_format = str(payload.get("format", "png")).strip().lower() or "png"
    if image_format not in {"png", "jpg", "jpeg"}:
        return _error("format must be one of png, jpg, jpeg")

    delivery, delivery_err = parse_delivery(payload.get("delivery"), default="auto")
    if delivery_err:
        return _error(delivery_err)
    inline_max_bytes, max_err = parse_inline_max_bytes(payload.get("inlineMaxBytes"))
    if max_err:
        return _error(max_err)

    url = f"https://api.os.uk/maps/raster/v1/zxy/{style}/{z}/{x}/{y}.{image_format}"
    status, body = client.get_bytes(url, None)
    if status != 200:
        return status, body
    content = body.get("content")
    if not isinstance(content, (bytes, bytearray)):
        return 500, {
            "isError": True,
            "code": "INTEGRATION_ERROR",
            "message": "Raster tile response was not binary content.",
        }

    response_payload = {
        "style": style,
        "z": z,
        "x": x,
        "y": y,
        "contentType": str(body.get("contentType", "image/png")),
        "encoding": "base64",
        "dataBase64": base64.b64encode(bytes(content)).decode("ascii"),
        "bytes": len(content),
        "live": True,
    }
    selected_mode = select_delivery_mode(
        requested_delivery=delivery or "auto",
        payload_bytes=payload_bytes(response_payload),
        inline_max_bytes=inline_max_bytes or int(getattr(settings, "OS_EXPORT_INLINE_MAX_BYTES", 200_000)),
    )
    if selected_mode == "resource":
        meta = write_resource_payload(prefix=f"os-maps-raster-{style}-{z}-{x}-{y}", payload=response_payload)
        return 200, {
            "delivery": "resource",
            "resourceUri": meta["resourceUri"],
            "bytes": meta["bytes"],
            "sha256": meta["sha256"],
            "contentType": response_payload["contentType"],
            "style": style,
            "z": z,
            "x": x,
            "y": y,
            "live": True,
        }
    response_payload["delivery"] = "inline"
    return 200, response_payload

def _maps_render(payload: dict[str, Any]):
    bbox = payload.get("bbox")
    if not (isinstance(bbox, list) and len(bbox) == 4):
        return _error("bbox must be [minLon,minLat,maxLon,maxLat]")
    try:
        min_lon, min_lat, max_lon, max_lat = [float(x) for x in bbox]
    except (TypeError, ValueError):
        return _error("bbox values must be numeric")
    if min_lon >= max_lon or min_lat >= max_lat:
        return _error("bbox must satisfy min < max for both lon/lat")
    size = payload.get("size", 256)
    try:
        size = int(size)
    except (TypeError, ValueError):
        return _error("size must be an integer")
    if size < 128 or size > 2048:
        return _error("size must be between 128 and 2048")

    include_inventory = bool(payload.get("includeInventory"))
    has_inventory_overrides = isinstance(payload.get("inventory"), dict)
    bbox_str = f"{min_lon},{min_lat},{max_lon},{max_lat}"
    image_url = f"/maps/static/osm?bbox={bbox_str}&size={size}"
    center_lon = (min_lon + max_lon) / 2.0
    center_lat = (min_lat + max_lat) / 2.0
    normalized_bbox = [min_lon, min_lat, max_lon, max_lat]

    overlay_layers = _normalize_overlay_layers(payload)
    inventory: dict[str, Any] | None = None
    if include_inventory or has_inventory_overrides:
        inv_tool = get_tool("os_map.inventory")
        if inv_tool is None:
            return 501, {
                "isError": True,
                "code": "MISSING_TOOL",
                "message": "os_map.inventory is not registered",
            }
        status, data = inv_tool.call(_build_inventory_request(payload, normalized_bbox))
        if status != 200:
            return status, data
        if not isinstance(data, dict):
            return 500, {
                "isError": True,
                "code": "INTEGRATION_ERROR",
                "message": "os_map.inventory returned a non-object payload",
            }
        inventory = data
        overlay_layers.extend(_extract_inventory_overlay_layers(data))

    hints = [
        "Image URL is served by the MCP Geo map proxy.",
        "Overlay geometries are returned for client-side rendering on top of the static image.",
    ]
    if any(layer.get("source") == "os_map.inventory" for layer in overlay_layers):
        hints.append(
            "Inventory overlays align with os_map.inventory layer ids (uprns/buildings/road_links/path_links)."
        )

    return 200, {
        "render": {
            "imageUrl": image_url,
            "imageWidth": size,
            "imageHeight": size,
            "bbox": normalized_bbox,
            "center": {"lon": center_lon, "lat": center_lat},
            "source": "osm",
            "notes": "Image URL is served by the MCP Geo map proxy.",
        },
        "overlayLayers": _overlay_summary(overlay_layers),
        "overlayCollections": [
            {
                "id": layer.get("id"),
                "name": layer.get("name"),
                "kind": layer.get("kind"),
                "featureCollection": {"type": "FeatureCollection", "features": layer.get("features", [])},
            }
            for layer in overlay_layers
        ],
        "inventory": inventory,
        "hints": hints,
    }


register(Tool(
    name="os_maps.wmts_capabilities",
    description="Fetch WMTS GetCapabilities with inline/resource delivery controls.",
    input_schema={
        "type": "object",
        "properties": {
            "tool": {"type": "string", "const": "os_maps.wmts_capabilities"},
            "version": {"type": "string"},
            "delivery": {"type": "string", "enum": ["inline", "resource", "auto"]},
            "inlineMaxBytes": {"type": "integer", "minimum": 1},
        },
        "required": [],
        "additionalProperties": False,
    },
    output_schema={
        "type": "object",
        "properties": {
            "delivery": {"type": "string"},
            "xml": {"type": "string"},
            "resourceUri": {"type": "string"},
        },
        "required": ["delivery"],
        "additionalProperties": True,
    },
    handler=_maps_wmts_capabilities
))

register(Tool(
    name="os_maps.raster_tile",
    description="Fetch a raster ZXY tile with inline/resource delivery controls.",
    input_schema={
        "type": "object",
        "properties": {
            "tool": {"type": "string", "const": "os_maps.raster_tile"},
            "style": {"type": "string"},
            "z": {"type": "integer", "minimum": 0},
            "x": {"type": "integer", "minimum": 0},
            "y": {"type": "integer", "minimum": 0},
            "format": {"type": "string"},
            "delivery": {"type": "string", "enum": ["inline", "resource", "auto"]},
            "inlineMaxBytes": {"type": "integer", "minimum": 1},
        },
        "required": ["z", "x", "y"],
        "additionalProperties": False,
    },
    output_schema={
        "type": "object",
        "properties": {
            "delivery": {"type": "string"},
            "dataBase64": {"type": "string"},
            "resourceUri": {"type": "string"},
            "contentType": {"type": "string"},
        },
        "required": ["delivery", "contentType"],
        "additionalProperties": True,
    },
    handler=_maps_raster_tile
))

register(Tool(
    name="os_maps.render",
    description=(
        "Return metadata for rendering a static map image (proxy URL) with overlay-ready geometry "
        "contracts and optional os_map.inventory hydration."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "tool": {"type": "string", "const": "os_maps.render"},
            "bbox": {
                "type": "array",
                "items": {"type": "number"},
                "minItems": 4,
                "maxItems": 4,
            },
            "size": {"type": "integer", "minimum": 128, "maximum": 2048},
            "includeInventory": {"type": "boolean"},
            "inventory": {
                "type": "object",
                "description": "Optional os_map.inventory options (layers, limits, includeGeometry, pageTokens).",
            },
            "overlays": {
                "type": "object",
                "description": (
                    "Optional overlay inputs: points/lines/polygons arrays or FeatureCollections, and "
                    "localLayers[] with {name,geojson,kind}."
                ),
            },
        },
        "required": ["bbox"],
        "additionalProperties": False,
    },
    output_schema={
        "type": "object",
        "properties": {
            "render": {"type": "object"},
            "overlayLayers": {"type": "array", "items": {"type": "object"}},
            "overlayCollections": {"type": "array", "items": {"type": "object"}},
            "inventory": {"type": ["object", "null"]},
            "hints": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["render"],
        "additionalProperties": True,
    },
    handler=_maps_render
))
