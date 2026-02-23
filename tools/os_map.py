from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any, Iterable

from tools.registry import Tool, ToolResult, get as get_tool, register

_REPO_ROOT = Path(__file__).resolve().parents[1]
_EXPORTS_DIR = _REPO_ROOT / "data" / "exports"

# Base collection ids (without numeric suffix). We resolve to the latest available version
# via `os_features.collections` when needed.
_DEFAULT_COLLECTION_BASES: dict[str, str] = {
    "buildings": "bld-fts-buildingpart",
    "road_links": "trn-ntwk-roadlink",
    "path_links": "trn-ntwk-pathlink",
}

_DEFAULT_LIMITS: dict[str, int] = {
    "uprns": 100,
    "buildings": 100,
    "road_links": 100,
    "path_links": 100,
}

_MAX_LIMIT = 500

_NGD_COLLECTION_CACHE_TTL_SECONDS = 3600.0
_NGD_COLLECTION_CACHE: dict[str, Any] = {"stored_at": 0.0, "latest_by_base": {}}


def _parse_bbox(value: Any) -> list[float] | None:
    if not (isinstance(value, list) and len(value) == 4):
        return None
    try:
        min_lon, min_lat, max_lon, max_lat = [float(x) for x in value]
    except (TypeError, ValueError):
        return None
    if min_lon >= max_lon or min_lat >= max_lat:
        return None
    return [min_lon, min_lat, max_lon, max_lat]


def _parse_layers(value: Any) -> list[str] | None:
    if value is None:
        return None
    if isinstance(value, str):
        parts = [p.strip() for p in value.split(",") if p.strip()]
    elif isinstance(value, list):
        parts = [str(p).strip() for p in value if p is not None and str(p).strip()]
    else:
        return None
    allowed = {"uprns", "buildings", "road_links", "path_links"}
    out = [p for p in parts if p in allowed]
    return out or None


def _parse_limits(value: Any) -> dict[str, int]:
    limits: dict[str, int] = dict(_DEFAULT_LIMITS)
    if not isinstance(value, dict):
        return limits
    for key, raw in value.items():
        if key not in limits:
            continue
        try:
            parsed = int(raw)
        except (TypeError, ValueError):
            continue
        if parsed < 1:
            continue
        limits[key] = min(parsed, _MAX_LIMIT)
    return limits


def _parse_layer_tokens(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    out: dict[str, str] = {}
    for key, raw in value.items():
        if key not in {"buildings", "road_links", "path_links"}:
            continue
        if isinstance(raw, (int, float)):
            raw = str(int(raw))
        if isinstance(raw, str) and raw.strip():
            out[key] = raw.strip()
    return out


def _parse_bool_map(value: Any) -> dict[str, bool]:
    if not isinstance(value, dict):
        return {}
    out: dict[str, bool] = {}
    for key, raw in value.items():
        if key not in {"buildings", "road_links", "path_links"}:
            continue
        if isinstance(raw, bool):
            out[key] = raw
    return out


def _parse_collections_override(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    out: dict[str, str] = {}
    for key, raw in value.items():
        if key not in {"buildings", "road_links", "path_links"}:
            continue
        if isinstance(raw, str) and raw.strip():
            out[key] = raw.strip()
    return out


def _get_latest_ngd_collection_ids() -> dict[str, str]:
    """Return cached latest-by-base collection ids from `os_features.collections`."""
    now = time.time()
    cached = _NGD_COLLECTION_CACHE.get("latest_by_base")
    stored_at = float(_NGD_COLLECTION_CACHE.get("stored_at", 0.0) or 0.0)
    if isinstance(cached, dict) and cached and now - stored_at < _NGD_COLLECTION_CACHE_TTL_SECONDS:
        return {str(k): str(v) for k, v in cached.items() if isinstance(k, str) and isinstance(v, str)}

    collections_tool = get_tool("os_features.collections")
    if not collections_tool:
        return {}
    status, data = collections_tool.call({"tool": "os_features.collections"})
    if status != 200 or not isinstance(data, dict):
        return {}
    latest = data.get("latestByBaseId")
    if not isinstance(latest, dict):
        return {}
    normalized = {
        str(base): str(coll_id)
        for base, coll_id in latest.items()
        if isinstance(base, str) and isinstance(coll_id, str)
    }
    _NGD_COLLECTION_CACHE["stored_at"] = now
    _NGD_COLLECTION_CACHE["latest_by_base"] = normalized
    return normalized


def _resolve_collection_id(layer_id: str, overrides: dict[str, str]) -> str | None:
    override = overrides.get(layer_id)
    if override:
        return override
    base = _DEFAULT_COLLECTION_BASES.get(layer_id)
    if not base:
        return None
    latest = _get_latest_ngd_collection_ids()
    return latest.get(base) or base


def _inventory(payload: dict[str, Any]) -> ToolResult:
    """Return a bounded inventory for common map layers within a bbox.

    This tool is intended for UI clients to avoid orchestrating multiple OS calls themselves.
    It enforces per-layer limits and returns truncation flags so clients can apply progressive
    disclosure (aggregate at low zoom, drill down at high zoom).
    """
    bbox = _parse_bbox(payload.get("bbox"))
    if bbox is None:
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "bbox must be [minLon,minLat,maxLon,maxLat] with min < max",
        }

    layers = _parse_layers(payload.get("layers")) or ["uprns", "buildings", "road_links", "path_links"]
    limits = _parse_limits(payload.get("limits"))
    page_tokens = _parse_layer_tokens(payload.get("pageTokens"))
    include_geometry = _parse_bool_map(payload.get("includeGeometry"))
    collections_override = _parse_collections_override(payload.get("collections"))

    result_layers: dict[str, Any] = {}
    hints: list[str] = []

    if "uprns" in layers:
        tool = get_tool("os_places.within")
        if not tool:
            result_layers["uprns"] = {
                "isError": True,
                "code": "MISSING_TOOL",
                "message": "os_places.within not registered",
            }
        else:
            status, data = tool.call({"tool": "os_places.within", "bbox": bbox})
            if status != 200:
                result_layers["uprns"] = data
            else:
                raw_results = data.get("results") if isinstance(data, dict) else None
                if not isinstance(raw_results, list):
                    raw_results = []
                limit = limits.get("uprns", _DEFAULT_LIMITS["uprns"])
                truncated = len(raw_results) > limit
                result_layers["uprns"] = {
                    "results": raw_results[:limit],
                    "count": min(len(raw_results), limit),
                    "truncated": truncated,
                    "notes": (
                        ["UPRNs are sourced via OS Places bbox search; results may be truncated upstream."]
                        + (["Increase limits.uprns or zoom in for detail."] if truncated else [])
                    ),
                }
                if isinstance(data, dict) and isinstance(data.get("provenance"), dict):
                    result_layers["uprns"]["provenance"] = data.get("provenance")

    def _fetch_features(layer_id: str) -> None:
        if layer_id not in layers:
            return
        tool = get_tool("os_features.query")
        if not tool:
            result_layers[layer_id] = {
                "isError": True,
                "code": "MISSING_TOOL",
                "message": "os_features.query not registered",
            }
            return
        collection_id = _resolve_collection_id(layer_id, collections_override)
        if not collection_id:
            result_layers[layer_id] = {
                "isError": True,
                "code": "INVALID_INPUT",
                "message": f"No default collection mapping for layer '{layer_id}'.",
            }
            return
        limit = limits.get(layer_id, _DEFAULT_LIMITS[layer_id])
        include_geom = include_geometry.get(layer_id, True)
        req: dict[str, Any] = {
            "tool": "os_features.query",
            "collection": collection_id,
            "bbox": bbox,
            "limit": limit,
            "includeGeometry": include_geom,
        }
        token = page_tokens.get(layer_id)
        if token:
            req["pageToken"] = token
        status, data = tool.call(req)
        if status != 200:
            result_layers[layer_id] = data
            return
        if not isinstance(data, dict):
            result_layers[layer_id] = {
                "isError": True,
                "code": "INTEGRATION_ERROR",
                "message": "Expected object response from os_features.query",
            }
            return
        result_layers[layer_id] = data
        # Cosmetic rename so UIs can treat layers uniformly.
        result_layers[layer_id].setdefault("layer", layer_id)
        if not include_geom:
            hints.append(f"{layer_id}: pass includeGeometry.{layer_id}=true to render on a map.")

    _fetch_features("buildings")
    _fetch_features("road_links")
    _fetch_features("path_links")

    return 200, {
        "bbox": bbox,
        "layers": result_layers,
        "requestedLayers": layers,
        "limits": {k: limits[k] for k in layers if k in limits},
        "hints": hints,
        "live": True,
    }


def _export(payload: dict[str, Any]) -> ToolResult:
    """Export an inventory snapshot to a local file and return a resource URI."""
    bbox = _parse_bbox(payload.get("bbox"))
    if bbox is None:
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "bbox must be [minLon,minLat,maxLon,maxLat] with min < max",
        }
    name = payload.get("name")
    if name is not None and not isinstance(name, str):
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "name must be a string"}
    recipe = payload.get("recipe")
    if recipe is not None and not isinstance(recipe, dict):
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "recipe must be an object"}
    layers = _parse_layers(payload.get("layers"))
    limits = _parse_limits(payload.get("limits"))
    include_geometry = _parse_bool_map(payload.get("includeGeometry"))
    collections_override = _parse_collections_override(payload.get("collections"))

    inv_status, inv = _inventory(
        {
            "bbox": bbox,
            "layers": layers,
            "limits": limits,
            "includeGeometry": include_geometry,
            "collections": collections_override,
        }
    )
    if inv_status != 200:
        return inv_status, inv

    export_id = str(uuid.uuid4())
    _EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{export_id}.json"
    path = _EXPORTS_DIR / filename
    payload_out = {
        "exportId": export_id,
        "name": name or "",
        "createdAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "recipe": recipe or {},
        "inventory": inv,
    }
    path.write_text(json.dumps(payload_out, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    uri = f"resource://mcp-geo/exports/{filename}"
    return 200, {
        "exportId": export_id,
        "uri": uri,
        "path": str(path),
        "notes": [
            "Use resources/read with the returned uri to fetch the exported JSON content.",
        ],
    }


register(
    Tool(
        name="os_map.inventory",
        description="Return a bounded inventory (UPRNs, buildings, road links, path links) for a bbox.",
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "os_map.inventory"},
                "bbox": {
                    "type": "array",
                    "items": {"type": "number"},
                    "minItems": 4,
                    "maxItems": 4,
                    "description": "WGS84 bbox [minLon,minLat,maxLon,maxLat]",
                },
                "layers": {
                    "oneOf": [
                        {"type": "array", "items": {"type": "string"}, "minItems": 1},
                        {"type": "string", "minLength": 1},
                        {"type": "null"},
                    ],
                    "description": "Requested layers (uprns, buildings, road_links, path_links).",
                },
                "limits": {"type": "object", "description": "Per-layer max features (budgets)."},
                "pageTokens": {"type": "object", "description": "Per-layer paging tokens for NGD layers."},
                "includeGeometry": {
                    "type": "object",
                    "description": "Per-layer includeGeometry overrides (NGD layers only).",
                },
                "collections": {
                    "type": "object",
                    "description": "Per-layer NGD collection id overrides (NGD layers only).",
                },
            },
            "required": ["bbox"],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "bbox": {
                    "type": "array",
                    "items": {"type": "number"},
                    "minItems": 4,
                    "maxItems": 4,
                },
                "layers": {"type": "object"},
                "requestedLayers": {"type": "array", "items": {"type": "string"}},
                "limits": {"type": "object"},
                "hints": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["layers"],
            "additionalProperties": True,
        },
        handler=_inventory,
    )
)

register(
    Tool(
        name="os_map.export",
        description="Export an inventory snapshot for a bbox to a local JSON file and return a resource URI.",
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "os_map.export"},
                "bbox": {
                    "type": "array",
                    "items": {"type": "number"},
                    "minItems": 4,
                    "maxItems": 4,
                },
                "name": {"type": "string"},
                "recipe": {"type": "object"},
                "layers": {
                    "oneOf": [
                        {"type": "array", "items": {"type": "string"}, "minItems": 1},
                        {"type": "string", "minLength": 1},
                        {"type": "null"},
                    ],
                    "description": "Requested layers (uprns, buildings, road_links, path_links).",
                },
                "limits": {"type": "object"},
                "includeGeometry": {"type": "object"},
                "collections": {"type": "object"},
            },
            "required": ["bbox"],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "exportId": {"type": "string"},
                "uri": {"type": "string"},
                "path": {"type": "string"},
                "notes": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["exportId", "uri", "path"],
            "additionalProperties": True,
        },
        handler=_export,
    )
)
