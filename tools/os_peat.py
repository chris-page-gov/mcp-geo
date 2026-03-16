from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tools.registry import Tool, ToolResult, register
from tools.registry import get as get_tool
from tools.typing_utils import is_strict_int

_REPO_ROOT = Path(__file__).resolve().parents[1]
_RESOURCE_PATH = _REPO_ROOT / "resources" / "peat_layers_england.json"
_DEFAULT_LIMIT = 25
_DEFAULT_RESULT_TYPE = "hits"
_CACHE: dict[str, Any] | None = None
AOIResolution = tuple[list[float], dict[str, Any]]


def _error(message: str, *, code: str = "INVALID_INPUT", status: int = 400) -> ToolResult:
    return status, {"isError": True, "code": code, "message": message}


def _normalize_text(value: str) -> str:
    return " ".join(value.strip().lower().split())


def _load_catalog() -> dict[str, Any]:
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    fallback = {
        "version": "missing",
        "scope": "england",
        "source": {},
        "layers": [],
    }
    try:
        payload = json.loads(_RESOURCE_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        _CACHE = fallback
        return _CACHE
    except Exception:
        fallback["version"] = "invalid"
        _CACHE = fallback
        return _CACHE
    if not isinstance(payload, dict):
        fallback["version"] = "invalid"
        _CACHE = fallback
        return _CACHE
    _CACHE = payload
    return _CACHE


def _layer_entries() -> list[dict[str, Any]]:
    raw = _load_catalog().get("layers")
    if not isinstance(raw, list):
        return []
    return [entry for entry in raw if isinstance(entry, dict)]


def _parse_bbox(raw: Any) -> list[float] | None:
    if not isinstance(raw, list) or len(raw) != 4:
        return None
    try:
        bbox = [float(raw[0]), float(raw[1]), float(raw[2]), float(raw[3])]
    except (TypeError, ValueError):
        return None
    if bbox[0] >= bbox[2] or bbox[1] >= bbox[3]:
        return None
    return bbox


def _resolve_aoi(payload: dict[str, Any]) -> AOIResolution | ToolResult:
    raw_bbox = payload.get("bbox")
    if raw_bbox is not None:
        bbox = _parse_bbox(raw_bbox)
        if bbox is None:
            return _error("bbox must be [minLon,minLat,maxLon,maxLat]")
        return bbox, {"source": "input_bbox"}

    landscape_id = payload.get("landscapeId")
    landscape_name = payload.get("landscapeName")
    if landscape_id is None and landscape_name is None:
        return _error("Provide bbox or landscapeId/landscapeName for AOI resolution")
    if landscape_id is not None and not isinstance(landscape_id, str):
        return _error("landscapeId must be a string")
    if landscape_name is not None and not isinstance(landscape_name, str):
        return _error("landscapeName must be a string")

    landscape_tool = get_tool("os_landscape.get")
    if landscape_tool is None:
        return _error("os_landscape.get is unavailable", code="DEPENDENCY_UNAVAILABLE", status=500)

    req: dict[str, Any] = {"tool": "os_landscape.get", "includeGeometry": False}
    if isinstance(landscape_id, str) and landscape_id.strip():
        req["id"] = landscape_id.strip()
    elif isinstance(landscape_name, str) and landscape_name.strip():
        req["name"] = landscape_name.strip()
    else:
        return _error("landscapeId/landscapeName must be non-empty when provided")

    status, result = landscape_tool.call(req)
    if status != 200 or not isinstance(result, dict):
        if status == 404:
            return _error("Landscape AOI not found", code="NOT_FOUND", status=404)
        return _error(
            "Failed to resolve AOI from os_landscape.get",
            code="INTEGRATION_ERROR",
            status=502,
        )

    landscape = result.get("landscape")
    if not isinstance(landscape, dict):
        return _error(
            "Landscape AOI response missing landscape metadata",
            code="INTEGRATION_ERROR",
            status=502,
        )

    bbox = _parse_bbox(landscape.get("bbox"))
    if bbox is None:
        return _error(
            "Landscape AOI response missing valid bbox",
            code="INTEGRATION_ERROR",
            status=502,
        )

    return bbox, {
        "source": "os_landscape.get",
        "landscapeId": landscape.get("id"),
        "landscapeName": landscape.get("name"),
    }


def _layer_summary(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": entry.get("id"),
        "title": entry.get("title"),
        "kind": entry.get("kind"),
        "dimension": entry.get("dimension"),
        "availability": entry.get("availability"),
        "provider": entry.get("provider"),
        "datasetUrl": entry.get("datasetUrl"),
        "resourceUri": entry.get("resourceUri"),
        "caveats": entry.get("caveats", []),
        "provenance": entry.get("provenance", {}),
    }


def _layers(payload: dict[str, Any]) -> ToolResult:
    kind = payload.get("kind", "all")
    if not isinstance(kind, str):
        return _error("kind must be a string")
    kind = _normalize_text(kind)
    if kind not in {"all", "direct", "proxy"}:
        return _error("kind must be one of: all, direct, proxy")

    layers = []
    for entry in _layer_entries():
        entry_kind = _normalize_text(str(entry.get("kind") or ""))
        if kind != "all" and entry_kind != kind:
            continue
        layers.append(_layer_summary(entry))

    catalog = _load_catalog()
    return 200, {
        "scope": catalog.get("scope"),
        "source": catalog.get("source"),
        "layerCount": len(layers),
        "layers": layers,
        "hints": [
            "Use os_peat.evidence_paths with bbox or landscapeId for AOI-scoped plans.",
            "Treat proxy layers as contextual indicators, not definitive peat evidence.",
        ],
    }


def _evidence_paths(payload: dict[str, Any]) -> ToolResult:
    limit_raw = payload.get("limit", _DEFAULT_LIMIT)
    if not is_strict_int(limit_raw) or limit_raw < 1 or limit_raw > 100:
        return _error("limit must be an integer between 1 and 100")

    result_type = payload.get("resultType", _DEFAULT_RESULT_TYPE)
    if not isinstance(result_type, str) or not result_type.strip():
        return _error("resultType must be a non-empty string")

    include_layers = payload.get("includeLayers")
    include_set: set[str] | None = None
    if include_layers is not None:
        if (
            not isinstance(include_layers, list)
            or not all(isinstance(v, str) for v in include_layers)
        ):
            return _error("includeLayers must be a list of strings")
        include_set = {_normalize_text(v) for v in include_layers if v.strip()}
        if not include_set:
            return _error("includeLayers must include at least one non-empty layer id")

    aoi_resolved = _resolve_aoi(payload)
    if isinstance(aoi_resolved, tuple) and isinstance(aoi_resolved[0], list):
        bbox, aoi_meta = aoi_resolved
    else:
        return aoi_resolved

    plans: list[dict[str, Any]] = []
    direct_ids: list[str] = []
    proxy_ids: list[str] = []

    for entry in _layer_entries():
        layer_id = str(entry.get("id") or "").strip()
        if not layer_id:
            continue
        if include_set is not None and _normalize_text(layer_id) not in include_set:
            continue

        layer_kind = _normalize_text(str(entry.get("kind") or ""))
        availability = _normalize_text(str(entry.get("availability") or ""))

        row = _layer_summary(entry)
        row["aoi"] = {"bbox": bbox}

        if layer_kind == "direct":
            direct_ids.append(layer_id)
        elif layer_kind == "proxy":
            proxy_ids.append(layer_id)

        query_template = entry.get("queryTemplate")
        if availability == "live_query" and isinstance(query_template, dict):
            template_params = query_template.get("parameters")
            params = dict(template_params) if isinstance(template_params, dict) else {}
            params["bbox"] = bbox
            params.setdefault("resultType", result_type)
            params.setdefault("limit", limit_raw)
            params.setdefault("includeGeometry", False)
            params.setdefault("thinMode", True)
            params.setdefault("delivery", "auto")
            row["queryPlan"] = {
                "tool": query_template.get("tool") or "os_features.query",
                "parameters": params,
            }
        else:
            row["queryPlan"] = None
            row["strategy"] = {
                "mode": "resource_reference",
                "resourceUri": entry.get("resourceUri") or "resource://mcp-geo/peat-layers-england",
            }

        plans.append(row)

    if not plans:
        return _error(
            "No peat layers matched the request for this AOI",
            code="NOT_FOUND",
            status=404,
        )

    confidence_score = 0.78 if direct_ids and proxy_ids else 0.62
    confidence_level = "high" if confidence_score >= 0.75 else "medium"

    return 200, {
        "aoi": {
            "bbox": bbox,
            **aoi_meta,
        },
        "layerCount": len(plans),
        "layers": plans,
        "evidenceSummary": {
            "directLayerIds": direct_ids,
            "proxyLayerIds": proxy_ids,
            "separation": (
                "Direct layers are peat evidence sources; proxy layers are contextual indicators."
            ),
        },
        "confidence": {
            "score": confidence_score,
            "level": confidence_level,
            "notes": [
                (
                    "Confidence reflects source availability and proxy usage, "
                    "not field validation certainty."
                )
            ],
        },
        "caveats": [
            (
                "Proxy indicators must not be treated as definitive peat condition "
                "or depth measurements."
            ),
            "Validate AOI findings with domain-specific datasets and field survey workflows.",
        ],
        "hints": [
            (
                "Use queryPlan tool calls with resultType=hits before geometry "
                "retrieval to keep responses bounded."
            ),
            "Use os_map.export or resource-backed outputs for larger downstream evidence bundles.",
        ],
    }


register(
    Tool(
        name="os_peat.layers",
        description="List peat evidence layers and proxy layers with provenance and caveats.",
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "os_peat.layers"},
                "kind": {"type": "string", "enum": ["all", "direct", "proxy"], "default": "all"},
            },
            "required": [],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "scope": {"type": "string"},
                "source": {"type": "object"},
                "layerCount": {"type": "integer"},
                "layers": {"type": "array"},
            },
            "required": ["layerCount", "layers"],
            "additionalProperties": True,
        },
        handler=_layers,
    )
)

register(
    Tool(
        name="os_peat.evidence_paths",
        description=(
            "Build AOI-scoped peat evidence and proxy query plans with explicit provenance, "
            "confidence, and caveats."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "os_peat.evidence_paths"},
                "bbox": {
                    "type": "array",
                    "items": {"type": "number"},
                    "minItems": 4,
                    "maxItems": 4,
                },
                "landscapeId": {"type": "string"},
                "landscapeName": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 25},
                "resultType": {"type": "string", "default": "hits"},
                "includeLayers": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "required": [],
            "additionalProperties": False,
            "anyOf": [
                {"required": ["bbox"]},
                {"required": ["landscapeId"]},
                {"required": ["landscapeName"]},
            ],
        },
        output_schema={
            "type": "object",
            "properties": {
                "aoi": {"type": "object"},
                "layerCount": {"type": "integer"},
                "layers": {"type": "array"},
                "evidenceSummary": {"type": "object"},
                "confidence": {"type": "object"},
                "caveats": {"type": "array"},
            },
            "required": ["aoi", "layerCount", "layers", "evidenceSummary", "confidence", "caveats"],
            "additionalProperties": True,
        },
        handler=_evidence_paths,
    )
)
