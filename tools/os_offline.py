from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from tools.registry import Tool, ToolResult, register

_REPO_ROOT = Path(__file__).resolve().parents[1]
_OFFLINE_CATALOG_PATH = _REPO_ROOT / "resources" / "offline_map_catalog.json"
_OFFLINE_PACKS_DIR = _REPO_ROOT / "data" / "offline_packs"
_DEFAULT_BBOX = [-0.18, 51.49, -0.05, 51.54]


def _now_iso() -> str:
    return datetime.now(tz=UTC).isoformat().replace("+00:00", "Z")


def _error(message: str, *, code: str = "INVALID_INPUT", status: int = 400) -> ToolResult:
    return status, {"isError": True, "code": code, "message": message}


def _load_catalog() -> tuple[int, dict[str, Any] | None]:
    if not _OFFLINE_CATALOG_PATH.exists():
        return 404, None
    try:
        parsed = json.loads(_OFFLINE_CATALOG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return 500, None
    if not isinstance(parsed, dict):
        return 500, None
    return 200, parsed


def _catalog_error(status: int) -> ToolResult:
    if status == 404:
        return _error("Offline map catalog not found.", code="NOT_FOUND", status=404)
    return _error(
        "Offline map catalog could not be loaded.",
        code="CATALOG_LOAD_FAILED",
        status=500,
    )


def _catalog_packs(catalog: dict[str, Any]) -> list[dict[str, Any]]:
    packs = catalog.get("packs")
    if not isinstance(packs, list):
        return []
    return [entry for entry in packs if isinstance(entry, dict)]


def _find_pack(catalog: dict[str, Any], pack_id: str) -> dict[str, Any] | None:
    for entry in _catalog_packs(catalog):
        if str(entry.get("id", "")).strip() == pack_id:
            return entry
    return None


def _normalize_bbox(raw: Any) -> list[float] | None:
    if raw is None:
        return list(_DEFAULT_BBOX)
    if not isinstance(raw, list) or len(raw) != 4:
        return None
    try:
        out = [float(raw[0]), float(raw[1]), float(raw[2]), float(raw[3])]
    except (TypeError, ValueError):
        return None
    if out[0] >= out[2] or out[1] >= out[3]:
        return None
    return out


def _path_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _pack_hash(pack: dict[str, Any]) -> str:
    declared = str(pack.get("sha256", "")).strip().lower()
    if declared:
        if declared.startswith("sha256:"):
            declared = declared.split(":", 1)[1]
        if len(declared) == 64 and all(ch in "0123456789abcdef" for ch in declared):
            return f"sha256:{declared}"

    resource_uri = str(pack.get("resourceUri", "")).strip()
    prefix = "resource://mcp-geo/offline-packs/"
    if resource_uri.startswith(prefix):
        filename = resource_uri[len(prefix):]
        candidate = (_OFFLINE_PACKS_DIR / filename).resolve()
        if _path_within(candidate, _OFFLINE_PACKS_DIR.resolve()) and candidate.exists():
            return f"sha256:{_sha256_file(candidate)}"

    stable_source = resource_uri or str(pack.get("id", ""))
    digest = hashlib.sha256(stable_source.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _offline_descriptor(payload: dict[str, Any]) -> ToolResult:
    status, catalog = _load_catalog()
    if status != 200 or catalog is None:
        return _catalog_error(status)
    requested_pack = payload.get("packId")
    if requested_pack is None:
        return 200, {
            "mode": "offline_catalog",
            "catalogVersion": catalog.get("version", "unknown"),
            "packs": _catalog_packs(catalog),
            "retrievalContracts": catalog.get("retrievalContracts", []),
            "fallbackOrder": ["map_card", "overlay_bundle", "export_handoff"],
        }
    if not isinstance(requested_pack, str) or not requested_pack.strip():
        return _error("packId must be a non-empty string")
    pack = _find_pack(catalog, requested_pack.strip())
    if not pack:
        return _error(f"Unknown offline pack '{requested_pack}'.", code="NOT_FOUND", status=404)
    return 200, {
        "mode": "offline_catalog",
        "catalogVersion": catalog.get("version", "unknown"),
        "pack": pack,
        "retrievalContracts": catalog.get("retrievalContracts", []),
        "fallbackOrder": ["map_card", "overlay_bundle", "export_handoff"],
    }


def _offline_get(payload: dict[str, Any]) -> ToolResult:
    status, catalog = _load_catalog()
    if status != 200 or catalog is None:
        return _catalog_error(status)

    pack_id = payload.get("packId")
    if not isinstance(pack_id, str) or not pack_id.strip():
        return _error("packId is required")
    pack_id = pack_id.strip()
    pack = _find_pack(catalog, pack_id)
    if not pack:
        return _error(f"Unknown offline pack '{pack_id}'.", code="NOT_FOUND", status=404)

    bbox = _normalize_bbox(payload.get("bbox"))
    if bbox is None:
        return _error("bbox must be [minLon,minLat,maxLon,maxLat]")
    include_overlay_template = bool(payload.get("includeOverlayTemplate", True))

    title = str(payload.get("title") or pack.get("title") or "Offline map handoff")
    download_uri = str(pack.get("resourceUri") or "")
    format_name = str(pack.get("format") or "pmtiles").lower()
    generated_at = _now_iso()
    guidance = {
        "widgetUnsupported": True,
        "widgetUnsupportedReason": "offline_delivery_mode",
        "degradationMode": "no_ui",
        "preferredNextTools": ["os_offline.get", "os_maps.render"],
    }

    map_card = {
        "type": "map_card",
        "title": title,
        "bbox": bbox,
        "render": {
            "imageUrl": (
                f"/maps/static/osm?bbox={bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}&size=640&zoom=13"
            ),
            "offlinePackUri": download_uri,
        },
        "guidance": guidance,
    }

    overlay_bundle: dict[str, Any] = {
        "type": "overlay_bundle",
        "layers": [],
        "source": {"packId": pack_id, "generatedAt": generated_at},
    }
    if include_overlay_template:
        overlay_bundle["layers"] = [
            {
                "id": "offline_template_layer",
                "name": "Offline overlay template",
                "kind": "polygon",
                "featureCollection": {"type": "FeatureCollection", "features": []},
            }
        ]

    export_handoff = {
        "type": "export_handoff",
        "resourceUri": download_uri,
        "format": format_name,
        "generatedAt": generated_at,
        "hash": _pack_hash(pack),
        "provenance": {
            "catalogVersion": catalog.get("version", "unknown"),
            "packVersion": pack.get("version"),
            "packId": pack_id,
        },
    }

    return 200, {
        "pack": pack,
        "map_card": map_card,
        "overlay_bundle": overlay_bundle,
        "export_handoff": export_handoff,
        "fallbackOrder": ["map_card", "overlay_bundle", "export_handoff"],
    }


register(
    Tool(
        name="os_offline.descriptor",
        description="Describe PMTiles/MBTiles offline map packs and retrieval contracts.",
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "os_offline.descriptor"},
                "packId": {"type": "string"},
            },
            "required": [],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "catalogVersion": {"type": "string"},
                "packs": {"type": "array"},
                "pack": {"type": "object"},
                "retrievalContracts": {"type": "array"},
                "fallbackOrder": {"type": "array"},
            },
        },
        handler=_offline_descriptor,
    )
)

register(
    Tool(
        name="os_offline.get",
        description="Return offline delivery handoff skeletons for a PMTiles/MBTiles pack.",
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "os_offline.get"},
                "packId": {"type": "string"},
                "title": {"type": "string"},
                "bbox": {
                    "type": "array",
                    "items": {"type": "number"},
                    "minItems": 4,
                    "maxItems": 4,
                },
                "includeOverlayTemplate": {"type": "boolean"},
            },
            "required": ["packId"],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "pack": {"type": "object"},
                "map_card": {"type": "object"},
                "overlay_bundle": {"type": "object"},
                "export_handoff": {"type": "object"},
                "fallbackOrder": {"type": "array"},
            },
            "required": ["pack", "map_card", "overlay_bundle", "export_handoff"],
        },
        handler=_offline_get,
    )
)
