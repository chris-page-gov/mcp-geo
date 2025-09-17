from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from tools.registry import Tool, register, ToolResult

_RESOURCE_PATH = Path(__file__).parent.parent / "resources" / "admin_boundaries.json"

# Lazy cache
_BOUNDARIES_CACHE: list[dict[str, Any]] | None = None


def _load() -> list[dict[str, Any]]:
    global _BOUNDARIES_CACHE
    if _BOUNDARIES_CACHE is None:
        data = json.loads(_RESOURCE_PATH.read_text())
        _BOUNDARIES_CACHE = data.get("features", [])
    return _BOUNDARIES_CACHE or []


def _point_in_bbox(lat: float, lon: float, bbox: list[float]) -> bool:
    min_lon, min_lat, max_lon, max_lat = bbox
    return (min_lon <= lon <= max_lon) and (min_lat <= lat <= max_lat)


def _containing_areas(payload: dict[str, Any]) -> ToolResult:
    raw_lat = payload.get("lat")
    raw_lon = payload.get("lon")
    try:
        lat = float(raw_lat)
        lon = float(raw_lon)
    except Exception:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "lat/lon must be numeric"}
    feats = _load()
    matches: list[dict[str, Any]] = []
    for feat in feats:
        bbox = feat.get("bbox")
        if not (isinstance(bbox, list) and len(bbox) == 4):
            continue
        if _point_in_bbox(lat, lon, bbox):
            matches.append({
                "id": feat.get("id"),
                "level": feat.get("level"),
                "name": feat.get("name"),
                "parent": feat.get("parent"),
            })
    if not matches:
        return 200, {"results": []}
    # Order by hierarchy depth using provided list order (already smallest -> largest)
    return 200, {"results": matches}

register(Tool(
    name="admin_lookup.containing_areas",
    description="Return containing administrative areas for a point (lat/lon)",
    input_schema={
        "type": "object",
        "properties": {
            "tool": {"type": "string", "const": "admin_lookup.containing_areas"},
            "lat": {"type": "number"},
            "lon": {"type": "number"},
        },
        "required": ["lat", "lon"],
        "additionalProperties": False,
    },
    output_schema={
        "type": "object",
        "properties": {
            "results": {"type": "array", "items": {"type": "object"}},
        },
        "required": ["results"],
    },
    handler=_containing_areas,
))


def _reverse_hierarchy(payload: dict[str, Any]) -> ToolResult:
    area_id = str(payload.get("id", "")).strip()
    if not area_id:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "Missing id"}
    feats = {f.get("id"): f for f in _load()}
    if area_id not in feats:
        return 404, {"isError": True, "code": "NOT_FOUND", "message": "Area not found"}
    chain = []
    current = feats[area_id]
    while current:
        chain.append({
            "id": current.get("id"),
            "level": current.get("level"),
            "name": current.get("name"),
        })
        parent_id = current.get("parent")
        current = feats.get(parent_id) if parent_id else None
    return 200, {"chain": chain}


register(Tool(
    name="admin_lookup.reverse_hierarchy",
    description="Return ancestor chain for a given area id",
    input_schema={
        "type": "object",
        "properties": {
            "tool": {"type": "string", "const": "admin_lookup.reverse_hierarchy"},
            "id": {"type": "string"},
        },
        "required": ["id"],
        "additionalProperties": False,
    },
    output_schema={"type": "object", "properties": {"chain": {"type": "array"}}, "required": ["chain"]},
    handler=_reverse_hierarchy,
))


def _area_geometry(payload: dict[str, Any]) -> ToolResult:
    area_id = str(payload.get("id", "")).strip()
    if not area_id:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "Missing id"}
    for feat in _load():
        if feat.get("id") == area_id:
            return 200, {"id": area_id, "bbox": feat.get("bbox")}
    return 404, {"isError": True, "code": "NOT_FOUND", "message": "Area not found"}


register(Tool(
    name="admin_lookup.area_geometry",
    description="Return bbox geometry for a given area id",
    input_schema={
        "type": "object",
        "properties": {
            "tool": {"type": "string", "const": "admin_lookup.area_geometry"},
            "id": {"type": "string"},
        },
        "required": ["id"],
        "additionalProperties": False,
    },
    output_schema={"type": "object", "properties": {"id": {"type": "string"}, "bbox": {"type": "array"}}, "required": ["id", "bbox"]},
    handler=_area_geometry,
))


def _find_by_name(payload: dict[str, Any]) -> ToolResult:
    text = str(payload.get("text", "")).strip().lower()
    if not text:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "Missing text"}
    matches = []
    for feat in _load():
        name = str(feat.get("name", ""))
        if text in name.lower():
            matches.append({
                "id": feat.get("id"),
                "level": feat.get("level"),
                "name": name,
            })
    return 200, {"results": matches}


register(Tool(
    name="admin_lookup.find_by_name",
    description="Substring case-insensitive search by area name",
    input_schema={
        "type": "object",
        "properties": {
            "tool": {"type": "string", "const": "admin_lookup.find_by_name"},
            "text": {"type": "string"},
        },
        "required": ["text"],
        "additionalProperties": False,
    },
    output_schema={"type": "object", "properties": {"results": {"type": "array"}}, "required": ["results"]},
    handler=_find_by_name,
))
