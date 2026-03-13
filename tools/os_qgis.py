from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from server.config import settings
from tools.os_common import client
from tools.os_delivery import (
    now_utc_iso,
    os_cache_dir,
    parse_delivery,
    parse_inline_max_bytes,
    payload_bytes,
    select_delivery_mode,
    write_resource_payload,
)
from tools.registry import Tool, ToolResult, register

_REPO_ROOT = Path(__file__).resolve().parents[1]
_STYLE_ROOT = _REPO_ROOT / "submodules" / "os-vector-tile-api-stylesheets"
_QML_DIR = _STYLE_ROOT / "QGIS Stylesheets (QML)"
_FALLBACK_STYLE_IDS = {
    3857: [
        "OS_VTS_3857_Light",
        "OS_VTS_3857_Dark",
        "OS_VTS_3857_Road",
        "OS_VTS_3857_Outdoor",
    ],
    27700: [
        "OS_VTS_27700_Light",
        "OS_VTS_27700_Dark",
        "OS_VTS_27700_Road",
        "OS_VTS_27700_Outdoor",
    ],
}


def _invalid(message: str) -> ToolResult:
    return 400, {"isError": True, "code": "INVALID_INPUT", "message": message}


def _safe_prefix_component(value: str) -> str:
    candidate = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip().lower())
    candidate = candidate.strip("._-")
    return candidate or "layer"


def _resolve_style_id(raw: Any, srs: int) -> str:
    default_style = f"OS_VTS_{srs}_Light"
    if not isinstance(raw, str) or not raw.strip():
        return default_style
    style = raw.strip()
    if style.lower().endswith(".json"):
        style = style[:-5]
    return style


def _available_style_ids(srs: int) -> list[str]:
    prefix = f"OS_VTS_{srs}_"
    out: list[str] = []
    if not _STYLE_ROOT.exists():
        return list(_FALLBACK_STYLE_IDS.get(srs, []))
    for path in sorted(_STYLE_ROOT.glob(f"{prefix}*.json")):
        out.append(path.stem)
    return out or list(_FALLBACK_STYLE_IDS.get(srs, []))


def _style_asset_paths(style_id: str) -> dict[str, Any]:
    qml_path = _QML_DIR / f"{style_id}.qml"
    json_path = _STYLE_ROOT / f"{style_id}.json"
    return {
        "qmlPath": str(qml_path),
        "jsonPath": str(json_path),
        "qmlExists": qml_path.exists(),
        "jsonExists": json_path.exists(),
    }


def _delivery_wrap(
    *,
    prefix: str,
    payload: dict[str, Any],
    delivery: str,
    inline_max_bytes: int,
) -> ToolResult:
    size = payload_bytes(payload)
    selected = select_delivery_mode(
        requested_delivery=delivery,
        payload_bytes=size,
        inline_max_bytes=inline_max_bytes,
    )
    if selected == "inline":
        return 200, {"delivery": "inline", "bytes": size, **payload}
    meta = write_resource_payload(prefix=prefix, payload=payload)
    return 200, {
        "delivery": "resource",
        "resourceUri": meta["resourceUri"],
        "bytes": meta["bytes"],
        "sha256": meta["sha256"],
    }


def _vector_tile_profile(payload: dict[str, Any]) -> ToolResult:
    srs = payload.get("srs", 3857)
    if not isinstance(srs, int) or srs not in {3857, 27700}:
        return _invalid("srs must be one of 3857 or 27700")
    style_id = _resolve_style_id(payload.get("style"), srs=srs)
    available = _available_style_ids(srs)
    if style_id not in available:
        return _invalid(
            "style must match an available OS VTS style for the selected srs "
            f"(for example: {', '.join(available[:5])})"
        )

    delivery, delivery_err = parse_delivery(payload.get("delivery"), default="auto")
    if delivery_err:
        return _invalid(delivery_err)
    inline_max_bytes, max_err = parse_inline_max_bytes(payload.get("inlineMaxBytes"))
    if max_err:
        return _invalid(max_err)
    use_proxy = bool(payload.get("useProxy", True))

    style_filename = f"{style_id}.json"
    direct_style_url = (
        f"{client.base_vector_tiles}/vts/resources/styles?style={style_filename}&srs={srs}&key={{API_KEY}}"
    )
    direct_tile_url = (
        f"{client.base_vector_tiles}/vts/tile/{{z}}/{{y}}/{{x}}.pbf"
        f"?srs={srs}&key={{API_KEY}}"
    )
    proxy_style_url = f"/maps/vector/vts/resources/styles?style={style_filename}&srs={srs}"
    proxy_tile_url = f"/maps/vector/vts/tile/{{z}}/{{y}}/{{x}}.pbf?srs={srs}"

    profile = {
        "kind": "qgis_vector_tile_profile",
        "createdAt": now_utc_iso(),
        "style": style_id,
        "styleFile": style_filename,
        "srs": srs,
        "crs": f"EPSG:{srs}",
        "provider": "vectortile",
        "connection": {
            "mode": "proxy" if use_proxy else "direct",
            "tileTemplate": proxy_tile_url if use_proxy else direct_tile_url,
            "styleUrl": proxy_style_url if use_proxy else direct_style_url,
            "directTileTemplate": direct_tile_url,
            "directStyleUrl": direct_style_url,
            "proxyTileTemplate": proxy_tile_url,
            "proxyStyleUrl": proxy_style_url,
        },
        "styleAssets": _style_asset_paths(style_id),
        "availableStyles": available,
        "qgisHints": [
            "Set layer type to vector tile and use connection.tileTemplate.",
            "Apply styleAssets.qmlPath in QGIS if local style overrides are required.",
            "Use direct URLs only when injecting a valid OS API key.",
        ],
    }
    response_payload = {"profile": profile, "live": False}
    return _delivery_wrap(
        prefix=f"os-qgis-vts-profile-{style_id.lower()}",
        payload=response_payload,
        delivery=delivery or "auto",
        inline_max_bytes=inline_max_bytes
        or int(getattr(settings, "OS_EXPORT_INLINE_MAX_BYTES", 200_000)),
    )


def _export_geopackage_descriptor(payload: dict[str, Any]) -> ToolResult:
    source_uri = payload.get("sourceResourceUri")
    if not isinstance(source_uri, str) or not source_uri.strip():
        return _invalid("sourceResourceUri is required")
    source_uri = source_uri.strip()
    if not source_uri.startswith("resource://mcp-geo/"):
        return _invalid("sourceResourceUri must begin with resource://mcp-geo/")

    layer_name = payload.get("layerName")
    if not isinstance(layer_name, str) or not layer_name.strip():
        layer_name = "os_export_layer"
    layer_name = layer_name.strip()

    file_name = payload.get("fileName")
    if not isinstance(file_name, str) or not file_name.strip():
        file_name = "os_export.gpkg"
    file_name = file_name.strip()
    if not file_name.lower().endswith(".gpkg"):
        file_name = f"{file_name}.gpkg"

    target_dir_raw = payload.get("targetDir")
    default_dir = os_cache_dir() / "qgis_exports"
    if isinstance(target_dir_raw, str) and target_dir_raw.strip():
        target_dir = Path(target_dir_raw.strip())
        if not target_dir.is_absolute():
            target_dir = (_REPO_ROOT / target_dir).resolve()
    else:
        target_dir = default_dir.resolve()
    target_path = (target_dir / file_name).resolve()

    crs = payload.get("crs")
    if not isinstance(crs, str) or not crs.strip():
        crs = "EPSG:27700"
    crs = crs.strip()

    delivery, delivery_err = parse_delivery(payload.get("delivery"), default="auto")
    if delivery_err:
        return _invalid(delivery_err)
    inline_max_bytes, max_err = parse_inline_max_bytes(payload.get("inlineMaxBytes"))
    if max_err:
        return _invalid(max_err)

    descriptor = {
        "kind": "qgis_geopackage_descriptor",
        "createdAt": now_utc_iso(),
        "source": {"resourceUri": source_uri},
        "target": {
            "path": str(target_path),
            "directory": str(target_dir),
            "fileName": file_name,
            "format": "GPKG",
            "layerName": layer_name,
            "crs": crs,
        },
        "qgis": {
            "provider": "ogr",
            "uri": f"{target_path}|layername={layer_name}",
            "driver": "GPKG",
        },
        "workflow": [
            "Read source.resourceUri with resources/read.",
            "Transform features into target.path GeoPackage layers.",
            "Open qgis.uri in QGIS via the OGR provider.",
        ],
    }
    response_payload = {"descriptor": descriptor, "live": False}
    return _delivery_wrap(
        prefix=f"os-qgis-gpkg-descriptor-{_safe_prefix_component(layer_name)}",
        payload=response_payload,
        delivery=delivery or "auto",
        inline_max_bytes=inline_max_bytes
        or int(getattr(settings, "OS_EXPORT_INLINE_MAX_BYTES", 200_000)),
    )


register(
    Tool(
        name="os_qgis.vector_tile_profile",
        description="Return a QGIS-ready OS vector tile profile (proxy or direct URL mode).",
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "os_qgis.vector_tile_profile"},
                "style": {"type": "string"},
                "srs": {"type": "integer", "enum": [3857, 27700]},
                "useProxy": {"type": "boolean"},
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
                "profile": {"type": "object"},
                "resourceUri": {"type": "string"},
            },
            "required": ["delivery"],
            "additionalProperties": True,
        },
        handler=_vector_tile_profile,
    )
)

register(
    Tool(
        name="os_qgis.export_geopackage_descriptor",
        description=(
            "Build a QGIS GeoPackage import descriptor for a resource-backed "
            "export artifact."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "os_qgis.export_geopackage_descriptor"},
                "sourceResourceUri": {"type": "string"},
                "targetDir": {"type": "string"},
                "fileName": {"type": "string"},
                "layerName": {"type": "string"},
                "crs": {"type": "string"},
                "delivery": {"type": "string", "enum": ["inline", "resource", "auto"]},
                "inlineMaxBytes": {"type": "integer", "minimum": 1},
            },
            "required": ["sourceResourceUri"],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "delivery": {"type": "string"},
                "descriptor": {"type": "object"},
                "resourceUri": {"type": "string"},
            },
            "required": ["delivery"],
            "additionalProperties": True,
        },
        handler=_export_geopackage_descriptor,
    )
)
