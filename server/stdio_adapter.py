"""STDIO JSON-RPC 2.0 adapter for mcp-geo.

Moved from `scripts/os_mcp.py` into the `server` package for consistency. The legacy
entry points (`scripts/os-mcp`, console script `mcp-geo-stdio`) still work by
delegating to this module's `main`.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
from datetime import UTC, datetime
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TextIO

from loguru import logger

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Import side-effects to register tools
import tools.registry as _reg  # noqa: F401
from server.mcp import tools as _mcp_import  # noqa: F401

from tools.registry import all_tools, get as get_tool
from server.mcp.resource_catalog import (
    DATA_RESOURCE_PREFIX,
    list_data_resources,
    MCP_APPS_MIME,
    list_skill_resources,
    list_ui_resources,
    load_data_content,
    load_skill_content,
    load_ui_content,
    resolve_data_resource,
    resolve_skill_resource,
    resolve_ui_resource,
)
from server.mcp.prompts import get_prompt as get_prompt_def, list_prompts as list_prompt_defs
from tools.os_apps import build_ui_tool_meta
from server.mcp.tool_search import (
    apply_default_toolset_filters,
    filter_tools_by_toolsets,
    get_tool_metadata,
    get_toolset_catalog,
    parse_toolset_list,
    resolve_default_toolset_filters_from_env,
    search_tools,
)
from server.mcp.elicitation_forms import (
    apply_ons_select_elicitation_result,
    apply_toolset_selection_elicitation_result,
    build_ons_select_elicitation_params,
    build_toolset_selection_elicitation_params,
)
from server.mcp.client_capabilities import (
    bool_env as _shared_bool_env,
    client_supports_ui as _shared_client_supports_ui,
    summarize_client_capabilities as _summarize_client_capabilities,
    read_bool_env as _shared_read_bool_env,
    ui_fallback_for_tool as _shared_ui_fallback_for_tool,
)
from server import __version__ as SERVER_VERSION
from server.observability import record_tool_call
from server.protocol import negotiate_protocol_version
from server.tool_naming import (
    build_tool_name_maps,
    resolve_tool_name,
    rewrite_tool_schema,
    sanitize_tool_name,
)

JSONRPC = "2.0"
_STDIO_TOOL_CONTENT_MAX_BYTES_DEFAULT = 32_000

RESOURCE_LIST: List[dict[str, Any]] = []
RESOURCE_LIST.extend(list_skill_resources())
RESOURCE_LIST.extend(list_ui_resources())
RESOURCE_LIST.extend(list_data_resources())


def handle_get_resource(params: Dict[str, Any]) -> Any:
    name = params.get("name")
    uri = params.get("uri")
    if not name and not uri:
        raise ValueError("Missing resource name or uri")
    if uri:
        if isinstance(uri, str) and uri.startswith(DATA_RESOURCE_PREFIX):
            entry = resolve_data_resource(uri)
            if entry:
                content, _etag, meta = load_data_content(entry)
                return _read_result(uri, "application/json", content, meta)
            raise LookupError(f"Unknown resource '{uri}'")
        else:
            ui_entry = resolve_ui_resource(str(uri))
            if ui_entry:
                content, _etag = load_ui_content(ui_entry)
                return _read_result(
                    ui_entry["uri"],
                    ui_entry["mimeType"],
                    content,
                    ui_entry.get("resourceMeta"),
                )
            skill_entry = resolve_skill_resource(str(uri))
            if skill_entry:
                content, _etag = load_skill_content()
                return _read_result(skill_entry["uri"], skill_entry["mimeType"], content)
            raise LookupError(f"Unknown resource '{uri}'")
    if name:
        ui_entry = resolve_ui_resource(str(name))
        if ui_entry:
            content, _etag = load_ui_content(ui_entry)
            return _read_result(
                ui_entry["uri"],
                ui_entry["mimeType"],
                content,
                ui_entry.get("resourceMeta"),
            )
        skill_entry = resolve_skill_resource(str(name))
        if skill_entry:
            content, _etag = load_skill_content()
            return _read_result(skill_entry["uri"], skill_entry["mimeType"], content)
        if str(name).startswith(DATA_RESOURCE_PREFIX) or resolve_data_resource(str(name)):
            entry = resolve_data_resource(str(name))
            if entry:
                content, _etag, meta = load_data_content(entry)
                uri_value = (
                    str(name)
                    if str(name).startswith(DATA_RESOURCE_PREFIX)
                    else f"{DATA_RESOURCE_PREFIX}{entry.get('slug', '')}"
                )
                return _read_result(uri_value, "application/json", content, meta)
    if not isinstance(name, str):
        raise ValueError("Missing resource name")
    raise LookupError(f"Unknown resource '{name}'")

def _resolve_framing() -> Optional[str]:
    raw = os.environ.get("MCP_STDIO_FRAMING", "").strip().lower()
    if raw in {"content-length", "content_length", "contentlength", "lsp"}:
        return "content-length"
    if raw in {"line", "lines", "jsonl", "newline"}:
        return "line"
    return None

CLIENT_CAPABILITIES: Dict[str, Any] = {}
CLIENT_CAPABILITY_SUMMARY: Dict[str, Any] = {}
CLIENT_INFO: Dict[str, Any] = {}
_ELICITATION_HANDLER: Optional[Callable[[Dict[str, Any]], Dict[str, Any] | None]] = None
_ELICITATION_REQUEST_SEQ = 0


def _sanitize_tool_name(name: str, seen: Dict[str, str]) -> str:
    return sanitize_tool_name(name, seen)


def _build_tool_name_maps() -> tuple[Dict[str, str], Dict[str, str]]:
    originals = [tool.name for tool in all_tools()]
    return build_tool_name_maps(originals)


def _resolve_tool_name(name: str) -> str:
    originals = [tool.name for tool in all_tools()]
    return resolve_tool_name(name, originals)


def _rewrite_tool_schema(
    schema: Dict[str, Any],
    *,
    sanitized_name: str,
    original_name: str,
) -> Dict[str, Any]:
    return rewrite_tool_schema(
        schema,
        sanitized_name=sanitized_name,
        original_name=original_name,
    )


def _write_message(payload: Dict[str, Any], framing: str) -> None:
    data = json.dumps(payload, separators=(",", ":"))
    try:
        if framing == "line":
            sys.stdout.write(f"{data}\n")
        else:
            sys.stdout.write(f"Content-Length: {len(data)}\r\n\r\n{data}")
        sys.stdout.flush()
    except BrokenPipeError:  # pragma: no cover
        pass

def _resp_success(msg_id: Any, result: Any) -> Dict[str, Any]:
    return {"jsonrpc": JSONRPC, "id": msg_id, "result": result}

def _resp_error(msg_id: Any, code: int, message: str, data: Any = None) -> Dict[str, Any]:
    err: Dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    return {"jsonrpc": JSONRPC, "id": msg_id, "error": err}


def _internal_error(msg_id: Any, method: str | None, exc: Exception) -> Dict[str, Any]:
    correlation_id = str(uuid.uuid4())
    logger.error(
        "MCP stdio internal error correlation_id={} method={} msg_id={} error_type={}",
        correlation_id,
        method,
        msg_id,
        type(exc).__name__,
    )
    return _resp_error(msg_id, -32603, "Internal error", {"correlationId": correlation_id})

def _read_bool_env(name: str) -> Optional[bool]:
    return _shared_read_bool_env(name)


def _bool_env(name: str, default: bool = False) -> bool:
    return _shared_bool_env(name, default=default)


def _client_supports_ui(capabilities: Dict[str, Any]) -> bool:
    return _shared_client_supports_ui(capabilities, override_env="MCP_STDIO_UI_SUPPORTED")


def _is_claude_client() -> bool:
    name = CLIENT_INFO.get("name")
    if not isinstance(name, str):
        return False
    return name.strip().lower().startswith("claude")


def _normalize_apps_content_mode(value: str) -> Optional[str]:
    raw = value.strip().lower()
    if raw in {"text", "plain"}:
        return "text"
    if raw in {"resource_link", "link"}:
        return "resource_link"
    if raw in {"embedded", "resource", "inline"}:
        return "embedded"
    return None


def _client_supports_elicitation_form(capabilities: Dict[str, Any]) -> bool:
    if not isinstance(capabilities, dict):
        return False
    elicitation = capabilities.get("elicitation")
    if elicitation is None:
        return False
    if not isinstance(elicitation, dict):
        return False
    # Spec compatibility: empty object implies form support.
    if not elicitation:
        return True
    return isinstance(elicitation.get("form"), dict)


def _set_elicitation_handler(
    handler: Optional[Callable[[Dict[str, Any]], Dict[str, Any] | None]],
) -> None:
    global _ELICITATION_HANDLER
    _ELICITATION_HANDLER = handler


def _next_elicitation_request_id() -> str:
    global _ELICITATION_REQUEST_SEQ
    _ELICITATION_REQUEST_SEQ += 1
    return f"elicitation-{_ELICITATION_REQUEST_SEQ}"


def _is_stats_comparison_query(query: str) -> bool:
    query_lower = query.lower()
    if " between " in query_lower:
        return True
    patterns = [r"\bcompare\b", r"\bcomparison\b", r"\bvs\.?\b", r"\bversus\b"]
    return any(re.search(pattern, query_lower) for pattern in patterns)


def _build_stats_routing_elicitation_params(
    query: str,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    comparison_level_default = "WARD"
    provider_preference_default = "AUTO"
    comparison_level = payload.get("comparisonLevel")
    if isinstance(comparison_level, str):
        normalized_level = comparison_level.strip().upper()
        if normalized_level in {"WARD", "LSOA", "MSOA"}:
            comparison_level_default = normalized_level
    provider_preference = payload.get("providerPreference")
    if isinstance(provider_preference, str):
        normalized_provider = provider_preference.strip().upper()
        if normalized_provider in {"AUTO", "NOMIS", "ONS"}:
            provider_preference_default = normalized_provider
    return {
        "mode": "form",
        "message": (
            "Choose how to compare these locations before statistics routing continues."
        ),
        "requestedSchema": {
            "type": "object",
            "properties": {
                "comparisonLevel": {
                    "type": "string",
                    "title": "Comparison level",
                    "description": "Pick the area granularity used for comparison.",
                    "enum": ["WARD", "LSOA", "MSOA"],
                    "default": comparison_level_default,
                },
                "providerPreference": {
                    "type": "string",
                    "title": "Statistics provider",
                    "description": "Choose provider preference for this routing call.",
                    "enum": ["AUTO", "NOMIS", "ONS"],
                    "default": provider_preference_default,
                },
            },
            "required": [],
        },
        "_meta": {"reason": "stats_routing_comparison", "query": query},
    }


def _apply_stats_routing_elicitation_choices(
    payload: Dict[str, Any],
    response: Dict[str, Any],
) -> tuple[bool, Dict[str, Any] | None]:
    action = response.get("action")
    if action in {"cancel", "decline"}:
        return False, {
            "isError": True,
            "code": "ELICITATION_CANCELLED",
            "message": "User cancelled or declined comparison settings.",
            "action": action,
        }
    if action != "accept":
        return False, {
            "isError": True,
            "code": "ELICITATION_INVALID_RESULT",
            "message": "Client returned an invalid elicitation result.",
        }
    content = response.get("content")
    if not isinstance(content, dict):
        return True, None
    level = content.get("comparisonLevel")
    if isinstance(level, str):
        level_norm = level.strip().upper()
        if level_norm in {"WARD", "LSOA", "MSOA"}:
            payload["comparisonLevel"] = level_norm
    provider = content.get("providerPreference")
    if isinstance(provider, str):
        provider_norm = provider.strip().upper()
        if provider_norm in {"AUTO", "NOMIS", "ONS"}:
            payload["providerPreference"] = provider_norm
    return True, None


def _maybe_elicit_stats_routing(payload: Dict[str, Any]) -> tuple[bool, Dict[str, Any] | None]:
    if not _bool_env("MCP_STDIO_ELICITATION_ENABLED", default=True):
        return True, None
    if not _client_supports_elicitation_form(CLIENT_CAPABILITIES):
        return True, None
    if _ELICITATION_HANDLER is None:
        return True, None
    query = payload.get("query")
    if not isinstance(query, str) or not query.strip():
        return True, None
    if not _is_stats_comparison_query(query):
        return True, None
    if (
        payload.get("comparisonLevel") is not None
        and payload.get("providerPreference") is not None
    ):
        return True, None
    response = _ELICITATION_HANDLER(_build_stats_routing_elicitation_params(query, payload))
    if not isinstance(response, dict):
        return False, {
            "isError": True,
            "code": "ELICITATION_UNAVAILABLE",
            "message": "No elicitation response received from client.",
        }
    return _apply_stats_routing_elicitation_choices(payload, response)


def _maybe_elicit_ons_select(payload: Dict[str, Any], data: Dict[str, Any]) -> bool:
    if not _bool_env("MCP_STDIO_ELICITATION_ENABLED", default=True):
        return False
    if not _client_supports_elicitation_form(CLIENT_CAPABILITIES):
        return False
    if _ELICITATION_HANDLER is None:
        return False
    if data.get("needsElicitation") is not True:
        return False
    query = data.get("query") or payload.get("query") or payload.get("q") or ""
    if not isinstance(query, str) or not query.strip():
        return False
    questions = data.get("elicitationQuestions")
    question_list = questions if isinstance(questions, list) else None
    response = _ELICITATION_HANDLER(
        build_ons_select_elicitation_params(query.strip(), payload, question_list)
    )
    if not isinstance(response, dict):
        return False
    changed, _error = apply_ons_select_elicitation_result(payload, response)
    return changed


def _maybe_elicit_select_toolsets(payload: Dict[str, Any]) -> tuple[bool, Dict[str, Any] | None]:
    if not _bool_env("MCP_STDIO_ELICITATION_ENABLED", default=True):
        return True, None
    if not _client_supports_elicitation_form(CLIENT_CAPABILITIES):
        return True, None
    if _ELICITATION_HANDLER is None:
        return True, None
    if payload.get("skipElicitation") is True:
        return True, None
    has_explicit_filters = any(
        payload.get(key) is not None for key in ("toolset", "includeToolsets", "excludeToolsets")
    )
    if has_explicit_filters:
        return True, None
    catalog = get_toolset_catalog()
    default_toolset, default_include, default_exclude = resolve_default_toolset_filters_from_env()
    include_seed = list(default_include)
    if default_toolset:
        include_seed.append(default_toolset)
    query = payload.get("query")
    query_text = query.strip() if isinstance(query, str) else ""
    params = build_toolset_selection_elicitation_params(
        query=query_text,
        toolset_names=sorted(catalog.keys()),
        default_include=include_seed,
        default_exclude=default_exclude,
    )
    response = _ELICITATION_HANDLER(params)
    if not isinstance(response, dict):
        return False, {
            "isError": True,
            "code": "ELICITATION_UNAVAILABLE",
            "message": "No elicitation response received from client.",
        }
    return apply_toolset_selection_elicitation_result(payload, response)


def _tool_content_limit_bytes() -> int:
    raw = os.getenv("MCP_STDIO_TOOL_CONTENT_MAX_BYTES", "").strip()
    if not raw:
        return _STDIO_TOOL_CONTENT_MAX_BYTES_DEFAULT
    try:
        value = int(raw)
    except ValueError:
        return _STDIO_TOOL_CONTENT_MAX_BYTES_DEFAULT
    return max(512, value)


def _tool_content_from_data(data: Any, allow_resource: bool = True) -> List[Dict[str, Any]]:
    if data is None:
        return []
    content: List[Dict[str, Any]] = []
    if isinstance(data, str):
        text = data
    else:
        try:
            text = json.dumps(data, ensure_ascii=True, separators=(",", ":"))
        except TypeError:
            text = str(data)
    encoded = text.encode("utf-8")
    limit = _tool_content_limit_bytes()
    if len(encoded) > limit:
        # Keep a deterministic preview and point clients at structured result data.
        preview_bytes = encoded[: max(0, limit - 240)]
        preview = preview_bytes.decode("utf-8", errors="ignore")
        omitted = len(encoded) - len(preview_bytes)
        text = (
            f"{preview}\n...[content truncated by stdio adapter; omitted {omitted} bytes. "
            "Use result.data for complete payload.]"
        )
    content.append({"type": "text", "text": text})
    return content


def _default_structured_content(data: Dict[str, Any]) -> Dict[str, Any]:
    """Return a structured payload that omits transport-only wrapper keys."""
    return {
        key: value
        for key, value in data.items()
        if key not in {"content", "_meta", "structuredContent"}
    }


def _read_result(
    uri: str,
    mime_type: Optional[str],
    text: str,
    meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    item: Dict[str, Any] = {"uri": uri, "text": text}
    if mime_type:
        item["mimeType"] = mime_type
    if meta:
        item["_meta"] = meta
    return {"contents": [item]}


def _extract_initial_view(
    payload: Dict[str, Any],
    data: Any,
) -> tuple[Optional[float], Optional[float], Optional[int]]:
    lat = payload.get("initialLat")
    lng = payload.get("initialLng")
    zoom = payload.get("initialZoom")
    if isinstance(data, dict):
        config = data.get("config")
        if isinstance(config, dict):
            view = config.get("initialView")
            if isinstance(view, dict):
                lat = view.get("lat", lat)
                lng = view.get("lng", lng)
            zoom = config.get("initialZoom", zoom)
    try:
        lat_f = float(lat) if lat is not None else None
        lng_f = float(lng) if lng is not None else None
    except (TypeError, ValueError):
        return None, None, None
    zoom_i: Optional[int] = None
    if zoom is not None:
        try:
            zoom_i = int(zoom)
        except (TypeError, ValueError):
            zoom_i = None
    return lat_f, lng_f, zoom_i


def _fallback_bbox(lat: float, lng: float, zoom: Optional[int]) -> list[float]:
    span_env = os.getenv("MCP_STDIO_FALLBACK_BBOX_DEG", "").strip()
    span: float
    if span_env:
        try:
            span = float(span_env)
        except ValueError:
            span = 0.01
    else:
        z = zoom if isinstance(zoom, int) else 16
        z = max(1, min(z, 20))
        deg_per_tile = 360.0 / (2 ** z)
        span = deg_per_tile * 2
    half = span / 2.0
    min_lon = max(-180.0, lng - half)
    max_lon = min(180.0, lng + half)
    min_lat = max(-90.0, lat - half)
    max_lat = min(90.0, lat + half)
    return [min_lon, min_lat, max_lon, max_lat]


def _now_iso() -> str:
    return datetime.now(tz=UTC).isoformat().replace("+00:00", "Z")


def _build_overlay_bundle_from_render(render_data: Any) -> dict[str, Any]:
    layers: list[dict[str, Any]] = []
    layer_meta: dict[str, dict[str, Any]] = {}
    if isinstance(render_data, dict):
        summary = render_data.get("overlayLayers")
        if isinstance(summary, list):
            for row in summary:
                if not isinstance(row, dict):
                    continue
                layer_id = row.get("id")
                if isinstance(layer_id, str) and layer_id:
                    layer_meta[layer_id] = row
        collections = render_data.get("overlayCollections")
        if isinstance(collections, list):
            for row in collections:
                if not isinstance(row, dict):
                    continue
                layer_id = row.get("id")
                if not isinstance(layer_id, str) or not layer_id:
                    continue
                feature_collection = row.get("featureCollection")
                if not isinstance(feature_collection, dict):
                    continue
                features = feature_collection.get("features")
                if not isinstance(features, list):
                    continue
                layer: dict[str, Any] = {
                    "id": layer_id,
                    "name": row.get("name") or layer_id,
                    "kind": row.get("kind") or "unknown",
                    "featureCollection": feature_collection,
                }
                meta = layer_meta.get(layer_id, {})
                if isinstance(meta.get("source"), str):
                    layer["source"] = meta["source"]
                if "interactive" in meta:
                    layer["interactive"] = bool(meta.get("interactive"))
                layers.append(layer)
    return {
        "type": "overlay_bundle",
        "layers": layers,
        "source": {"tool": "os_maps.render", "generatedAt": _now_iso()},
    }


def _build_static_map_fallback(payload: Dict[str, Any], data: Any) -> Optional[Dict[str, Any]]:
    lat, lng, zoom = _extract_initial_view(payload, data)
    if lat is None or lng is None:
        return None
    bbox = _fallback_bbox(lat, lng, zoom)
    maps_tool = get_tool("os_maps.render")
    render: Optional[Dict[str, Any]] = None
    render_payload: Optional[Dict[str, Any]] = None
    status: Optional[int] = None
    if maps_tool:
        status, render_data = maps_tool.call({"tool": "os_maps.render", "bbox": bbox})
        if status == 200 and isinstance(render_data, dict):
            render_payload = render_data
            render = render_data.get("render")
    fallback: Dict[str, Any] = {
        "type": "static_map",
        "center": {"lat": lat, "lng": lng},
        "bbox": bbox,
        "note": "Client does not support MCP-Apps UI; use render.urlTemplate with your API key.",
        "widgetUnsupported": True,
        "widgetUnsupportedReason": "ui_extension_not_advertised",
        "degradationMode": "no_ui",
        "guidance": {
            "widgetUnsupported": True,
            "widgetUnsupportedReason": "ui_extension_not_advertised",
            "degradationMode": "no_ui",
            "preferredNextTools": [
                "os_maps.render",
                "admin_lookup.area_geometry",
                "os_map.inventory",
            ],
            "transportParity": ["stdio", "http"],
        },
    }
    if zoom is not None:
        fallback["zoom"] = zoom
    if render is not None:
        fallback["render"] = render
    if status is not None and status != 200:
        fallback["mapError"] = {"status": status}
    fallback_image_url: str | None = None
    if isinstance(render, dict):
        image_url = render.get("imageUrl")
        if isinstance(image_url, str) and image_url:
            fallback_image_url = image_url
    if fallback_image_url is None:
        fallback_image_url = (
            f"/maps/static/osm?bbox={bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}&size=640"
        )
    map_card: Dict[str, Any] = {
        "type": "map_card",
        "title": "Static map fallback",
        "bbox": bbox,
        "center": {"lat": lat, "lng": lng},
        "guidance": fallback["guidance"],
    }
    if render is not None:
        map_card["render"] = render
    else:
        map_card["render"] = {"imageUrl": fallback_image_url}
    overlay_bundle = _build_overlay_bundle_from_render(render_payload or {})
    export_fingerprint = {
        "resourceUri": fallback_image_url,
        "bbox": bbox,
        "center": {"lat": lat, "lng": lng},
        "status": status,
    }
    export_hash = hashlib.sha256(
        json.dumps(export_fingerprint, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    export_handoff = {
        "type": "export_handoff",
        "resourceUri": fallback_image_url,
        "format": "url",
        "hash": f"sha256:{export_hash}",
        "generatedAt": _now_iso(),
        "provenance": {"tool": "os_maps.render", "status": status},
    }
    fallback["map_card"] = map_card
    fallback["overlay_bundle"] = overlay_bundle
    fallback["export_handoff"] = export_handoff
    fallback["fallbackOrder"] = ["map_card", "overlay_bundle", "export_handoff"]
    return fallback


def _build_stats_dashboard_fallback(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    area_codes = payload.get("areaCodes")
    dataset = payload.get("dataset")
    measure = payload.get("measure")
    if area_codes is not None and not isinstance(area_codes, list):
        area_codes = None
    return {
        "type": "statistics_dashboard",
        "note": "Client does not support MCP-Apps UI. Use data tools directly.",
        "areaCodes": area_codes or [],
        "dataset": dataset,
        "measure": measure,
        "widgetUnsupported": True,
        "widgetUnsupportedReason": "ui_extension_not_advertised",
        "degradationMode": "no_ui",
        "suggestedTools": [
            "ons_search.query",
            "ons_data.dimensions",
            "ons_data.query",
            "nomis.datasets",
            "nomis.query",
        ],
        "guidance": {
            "widgetUnsupported": True,
            "widgetUnsupportedReason": "ui_extension_not_advertised",
            "degradationMode": "no_ui",
            "preferredNextTools": [
                "ons_search.query",
                "ons_data.dimensions",
                "ons_data.query",
                "nomis.datasets",
                "nomis.query",
            ],
            "transportParity": ["stdio", "http"],
        },
    }


def handle_initialize(params: Dict[str, Any]) -> Any:
    requested = params.get("protocolVersion")
    protocol_version = negotiate_protocol_version(requested)
    global CLIENT_CAPABILITIES, CLIENT_CAPABILITY_SUMMARY, CLIENT_INFO
    capabilities = params.get("capabilities")
    CLIENT_CAPABILITIES = capabilities if isinstance(capabilities, dict) else {}
    client_info = params.get("clientInfo")
    CLIENT_INFO = client_info if isinstance(client_info, dict) else {}
    CLIENT_CAPABILITY_SUMMARY = _summarize_client_capabilities(
        capabilities=CLIENT_CAPABILITIES,
        requested_protocol_version=requested,
        negotiated_protocol_version=protocol_version,
    )
    logger.info(
        "MCP initialize (stdio) support_summary={summary}",
        summary=CLIENT_CAPABILITY_SUMMARY,
    )
    return {
        "protocolVersion": protocol_version,
        "serverInfo": {"name": "mcp-geo", "version": SERVER_VERSION},
        "capabilities": {
            "tools": {"list": True, "call": True},
            "resources": {"list": True, "read": True},
            "prompts": {"list": True, "get": True},
            "extensions": {
                "io.modelcontextprotocol/ui": {
                    "mimeTypes": [MCP_APPS_MIME],
                }
            },
        },
        "server": "mcp-geo",
        "version": SERVER_VERSION,
    }


def _build_list_tool_entries(filtered_tools: list[Any]) -> list[dict[str, Any]]:
    tool_entries: list[dict[str, Any]] = []
    original_to_sanitized, _ = _build_tool_name_maps()
    for t in filtered_tools:
        meta = get_tool_metadata(t)
        name = original_to_sanitized.get(t.name, t.name)
        annotations = dict(meta.get("annotations", {}))
        if name != t.name:
            annotations["originalName"] = t.name
        input_schema = t.input_schema
        if name != t.name:
            input_schema = _rewrite_tool_schema(
                t.input_schema,
                sanitized_name=name,
                original_name=t.name,
            )
        entry: Dict[str, Any] = {
            "name": name,
            "description": t.description,
            "version": t.version,
            "inputSchema": input_schema,
            "outputSchema": t.output_schema,
            "annotations": annotations,
        }
        ui_meta = build_ui_tool_meta(t.name)
        internal_meta: dict[str, Any] = {}
        if meta.get("category") is not None:
            internal_meta["category"] = meta.get("category")
        if meta.get("keywords"):
            internal_meta["keywords"] = meta.get("keywords", [])
        if meta.get("defer_loading") is not None:
            internal_meta["deferLoading"] = meta.get("defer_loading")
        if ui_meta or internal_meta:
            merged: dict[str, Any] = {}
            if ui_meta:
                merged.update(ui_meta)
            if internal_meta:
                merged["mcp-geo"] = internal_meta
            entry["_meta"] = merged
        tool_entries.append(entry)
    return tool_entries


def handle_list_tools(_params: Dict[str, Any]) -> Any:
    toolset = _params.get("toolset")
    if toolset is not None and not isinstance(toolset, str):
        raise ValueError("toolset must be a string")
    include_toolsets = parse_toolset_list(_params.get("includeToolsets"))
    exclude_toolsets = parse_toolset_list(_params.get("excludeToolsets"))
    toolset, include_toolsets, exclude_toolsets = apply_default_toolset_filters(
        toolset=toolset,
        include_toolsets=include_toolsets,
        exclude_toolsets=exclude_toolsets,
    )
    tool_entries: list[dict[str, Any]] = []
    filtered_tools = filter_tools_by_toolsets(
        all_tools(),
        toolset=toolset,
        include_toolsets=include_toolsets,
        exclude_toolsets=exclude_toolsets,
    )
    query = _params.get("query") or _params.get("q")
    if query is not None:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must be a non-empty string")
        mode = _params.get("mode", "token")
        if not isinstance(mode, str):
            raise ValueError("mode must be a string")
        limit = _params.get("limit", 10)
        if not isinstance(limit, int) or limit < 1:
            raise ValueError("limit must be >= 1")
        category = _params.get("category")
        if category is not None and not isinstance(category, str):
            raise ValueError("category must be a string")
        ranked = search_tools(
            query,
            mode=mode,
            limit=limit,
            category=category,
            include_schemas=False,
            toolset=toolset,
            include_toolsets=include_toolsets,
            exclude_toolsets=exclude_toolsets,
        )
        ranked_names = [
            item["name"] for item in ranked if isinstance(item.get("name"), str)
        ]
        by_name = {tool.name: tool for tool in filtered_tools}
        filtered_tools = [by_name[name] for name in ranked_names if name in by_name]
    return {
        "tools": _build_list_tool_entries(filtered_tools),
        "toolsets": get_toolset_catalog(),
    }


def handle_search_tools(params: Dict[str, Any]) -> Any:
    query = params.get("query") or params.get("q")
    if not isinstance(query, str) or not query.strip():
        raise ValueError("Missing query")
    mode = params.get("mode", "token")
    if not isinstance(mode, str):
        raise ValueError("mode must be a string")
    limit = params.get("limit", 10)
    if not isinstance(limit, int) or limit < 1:
        raise ValueError("limit must be >= 1")
    category = params.get("category")
    if category is not None and not isinstance(category, str):
        raise ValueError("category must be a string")
    include_schemas = params.get("includeSchemas", False)
    if not isinstance(include_schemas, bool):
        raise ValueError("includeSchemas must be a boolean")
    toolset = params.get("toolset")
    if toolset is not None and not isinstance(toolset, str):
        raise ValueError("toolset must be a string")
    include_toolsets = parse_toolset_list(params.get("includeToolsets"))
    exclude_toolsets = parse_toolset_list(params.get("excludeToolsets"))
    results = search_tools(
        query,
        mode=mode,
        limit=limit,
        category=category,
        include_schemas=include_schemas,
        toolset=toolset,
        include_toolsets=include_toolsets,
        exclude_toolsets=exclude_toolsets,
    )
    original_to_sanitized, _ = _build_tool_name_maps()
    for entry in results:
        original = entry.get("name")
        if not isinstance(original, str):
            continue
        sanitized = original_to_sanitized.get(original, original)
        if sanitized != original:
            annotations = dict(entry.get("annotations", {}) or {})
            annotations["originalName"] = original
            entry["annotations"] = annotations
            if include_schemas and isinstance(entry.get("inputSchema"), dict):
                entry["inputSchema"] = _rewrite_tool_schema(
                    entry["inputSchema"],
                    sanitized_name=sanitized,
                    original_name=original,
                )
        entry["name"] = sanitized
    return {"tools": results, "count": len(results), "mode": mode, "toolsets": get_toolset_catalog()}

def handle_call_tool(params: Dict[str, Any]) -> Any:
    name = params.get("tool") or params.get("name")
    if not isinstance(name, str):
        raise ValueError("Missing tool name")
    resolved_name = _resolve_tool_name(name)
    tool = get_tool(resolved_name)
    if not tool:
        raise LookupError(f"Unknown tool '{name}'")
    payload = params.get("args") or params.get("arguments") or params.get("payload") or {}
    if not isinstance(payload, dict):
        raise TypeError("Payload must be object")
    payload = dict(payload)
    if (
        resolved_name.startswith("os_apps.render_")
        and "contentMode" not in payload
        and _is_claude_client()
    ):
        # Claude should receive a UI-launchable content block by default.
        # `resource_link` avoids embedding full HTML while still pointing hosts
        # at the MCP-Apps resource URI.
        preferred_mode_raw = os.getenv("MCP_STDIO_CLAUDE_APPS_CONTENT_MODE", "resource_link")
        preferred_mode = _normalize_apps_content_mode(preferred_mode_raw)
        if preferred_mode:
            payload["contentMode"] = preferred_mode
    if resolved_name == "os_mcp.stats_routing":
        should_continue, elicitation_error = _maybe_elicit_stats_routing(payload)
        if not should_continue:
            status = 409
            data = elicitation_error or {
                "isError": True,
                "code": "ELICITATION_CANCELLED",
                "message": "Elicitation cancelled.",
            }
            result: Dict[str, Any] = {"status": status, "ok": False, "data": data, "isError": True}
            result["content"] = _tool_content_from_data(data, allow_resource=False)
            return result
    if resolved_name == "os_mcp.select_toolsets":
        should_continue, elicitation_error = _maybe_elicit_select_toolsets(payload)
        if not should_continue:
            status = 409
            data = elicitation_error or {
                "isError": True,
                "code": "ELICITATION_CANCELLED",
                "message": "Elicitation cancelled.",
            }
            result = {"status": status, "ok": False, "data": data, "isError": True}
            result["content"] = _tool_content_from_data(data, allow_resource=False)
            return result
    started = time.perf_counter()
    status, data = tool.call(payload)
    if resolved_name == "ons_select.search" and isinstance(data, dict):
        if _maybe_elicit_ons_select(payload, data):
            status, data = tool.call(payload)
    if isinstance(data, dict):
        data = dict(data)
        if resolved_name == "os_mcp.descriptor":
            data.setdefault("transport", "stdio")
        fallback = _shared_ui_fallback_for_tool(
            resolved_name,
            payload,
            data,
            ui_supported=_client_supports_ui(CLIENT_CAPABILITIES),
            build_static_map_fallback=_build_static_map_fallback,
            build_stats_dashboard_fallback=_build_stats_dashboard_fallback,
        )
        if fallback:
            data["fallback"] = fallback
    record_tool_call(
        tool_name=resolved_name,
        transport="stdio",
        payload=payload,
        result=data,
        status_code=status,
        latency_ms=(time.perf_counter() - started) * 1000.0,
    )
    ok = 200 <= status < 300
    result: Dict[str, Any] = {"status": status, "ok": ok, "data": data}
    allow_resource = _bool_env("MCP_STDIO_RESOURCE_CONTENT", default=False)
    if isinstance(data, dict):
        content_override = data.get("content")
        if isinstance(content_override, list):
            result["content"] = content_override
        else:
            result["content"] = _tool_content_from_data(data, allow_resource=allow_resource)
        structured = data.get("structuredContent")
        if isinstance(structured, dict):
            result["structuredContent"] = structured
        else:
            result["structuredContent"] = _default_structured_content(data)
        meta = data.get("_meta")
        if isinstance(meta, dict):
            result["_meta"] = meta
    else:
        result["content"] = _tool_content_from_data(data, allow_resource=allow_resource)
    if not ok or (isinstance(data, dict) and data.get("isError") is True):
        result["isError"] = True
    return result

def handle_list_resources(_params: Dict[str, Any]) -> Any:
    return {"resources": RESOURCE_LIST}

def handle_list_resource_templates(_params: Dict[str, Any]) -> Any:
    return {"resourceTemplates": []}

def handle_list_prompts(_params: Dict[str, Any]) -> Any:
    return {"prompts": list_prompt_defs()}

def handle_get_prompt(params: Dict[str, Any]) -> Any:
    name = params.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Missing prompt name")
    prompt = get_prompt_def(name)
    if prompt is None:
        raise LookupError(f"Unknown prompt '{name}'")
    return prompt

def handle_shutdown(_params: Dict[str, Any]) -> Any:
    return None

HANDLERS: Dict[str, Any] = {
    "initialize": handle_initialize,
    "tools/list": handle_list_tools,
    "tools/search": handle_search_tools,
    "tools/call": handle_call_tool,
    "resources/list": handle_list_resources,
    "resources/templates/list": handle_list_resource_templates,
    "resources/describe": lambda _p: {"resources": RESOURCE_LIST},
    "resources/read": handle_get_resource,
    "prompts/list": handle_list_prompts,
    "prompts/get": handle_get_prompt,
    "shutdown": handle_shutdown,
}

def _read_headers(stdin, first_line: Optional[str] = None) -> tuple[Optional[int], Optional[str]]:
    content_length: Optional[int] = None
    line = first_line
    while True:
        if line is None:
            line = stdin.readline()
        if line == "":
            return None, None
        if line in ("\n", "\r\n"):
            break
        lower = line.lower()
        if lower.startswith("content-length:"):
            try:
                content_length = int(line.split(":", 1)[1].strip())
            except ValueError:
                return None, "Invalid Content-Length"
        line = None
    if content_length is None:
        return None, "Missing Content-Length"
    return content_length, None


def _read_message(
    stdin: TextIO,
    framing: Optional[str],
) -> tuple[Optional[Dict[str, Any]], Optional[str], Optional[str]]:
    if framing == "content-length":
        length, error = _read_headers(stdin)
        if error:
            return None, framing, error
        if length is None:
            return None, framing, None
        body = stdin.read(length)
        if not body:
            return None, framing, None
        try:
            return json.loads(body), framing, None
        except json.JSONDecodeError:
            return None, framing, "Parse error"
    if framing == "line":
        while True:
            line = stdin.readline()
            if line == "":
                return None, framing, None
            text = line.strip()
            if not text:
                continue
            try:
                return json.loads(text), framing, None
            except json.JSONDecodeError:
                return None, framing, "Parse error"
    while True:
        line = stdin.readline()
        if line == "":
            return None, framing, None
        if line in ("\n", "\r\n"):
            continue
        if line.lower().startswith("content-length:"):
            framing = "content-length"
            length, error = _read_headers(stdin, first_line=line)
            if error:
                return None, framing, error
            if length is None:
                return None, framing, None
            body = stdin.read(length)
            if not body:
                return None, framing, None
            try:
                return json.loads(body), framing, None
            except json.JSONDecodeError:
                return None, framing, "Parse error"
        framing = "line"
        text = line.strip()
        if not text:
            continue
        try:
            return json.loads(text), framing, None
        except json.JSONDecodeError:
            return None, framing, "Parse error"

def main(stdin: Optional[TextIO] = None, stdout: Optional[TextIO] = None) -> None:
    """Run adapter loop with optional injected streams (for unit tests).

    stdin/stdout may be injected StringIO objects in tests; in production they
    default to process stdio. Framing auto-detects Content-Length vs JSON lines;
    set MCP_STDIO_FRAMING=content-length or MCP_STDIO_FRAMING=line to force.
    """
    if stdin is None:
        stdin = sys.stdin  # type: ignore[assignment]
    if stdout is None:
        stdout = sys.stdout  # type: ignore[assignment]
    orig_stdout = sys.stdout
    sys.stdout = stdout  # type: ignore
    try:
        framing = _resolve_framing()
        startup_log_pending = _bool_env("MCP_STDIO_LOG_STARTUP")
        global _ELICITATION_REQUEST_SEQ
        _ELICITATION_REQUEST_SEQ = 0

        def _request_elicitation(params: Dict[str, Any]) -> Dict[str, Any] | None:
            nonlocal framing
            if not framing:
                return None
            req_id = _next_elicitation_request_id()
            _write_message(
                {"jsonrpc": JSONRPC, "id": req_id, "method": "elicitation/create", "params": params},
                framing,
            )
            while True:
                msg, framing, error = _read_message(stdin, framing)
                if msg is None:
                    if error:
                        continue
                    return {"action": "cancel"}
                if msg.get("jsonrpc") != JSONRPC:
                    continue
                if msg.get("id") == req_id:
                    result = msg.get("result")
                    return result if isinstance(result, dict) else {"action": "cancel"}
                incoming_id = msg.get("id")
                if incoming_id is not None and framing:
                    _write_message(
                        _resp_error(incoming_id, -32001, "Server busy awaiting elicitation response"),
                        framing,
                    )

        _set_elicitation_handler(_request_elicitation)
        while True:
            msg, framing, error = _read_message(stdin, framing)
            if msg is None:
                if error and framing:
                    _write_message(_resp_error(None, -32700, error), framing)
                    continue
                break
            is_notification = msg.get("id") is None
            if msg.get("jsonrpc") != JSONRPC:
                if framing:
                    if not is_notification:
                        _write_message(
                            _resp_error(msg.get("id"), -32600, "Invalid Request"),
                            framing,
                        )
                continue
            method = msg.get("method")
            msg_id = msg.get("id")
            if method == "exit":
                break
            handler = HANDLERS.get(method)
            if not handler:
                if framing:
                    if not is_notification:
                        _write_message(
                            _resp_error(msg_id, -32601, f"Method not found: {method}"),
                            framing,
                        )
                continue
            # Preserve original type to validate; only default to empty dict when param key absent.
            params = msg.get("params")
            if params is None:
                params = {}
            if not isinstance(params, dict):
                if framing:
                    if not is_notification:
                        _write_message(_resp_error(msg_id, -32602, "Invalid params"), framing)
                continue
            try:
                result = handler(params)
                if framing:
                    if not is_notification:
                        _write_message(_resp_success(msg_id, result), framing)
            except LookupError as e:
                if framing:
                    if not is_notification:
                        _write_message(_resp_error(msg_id, 1001, str(e)), framing)
            except ValueError as e:
                if framing:
                    if not is_notification:
                        _write_message(_resp_error(msg_id, 1002, str(e)), framing)
            except TypeError as e:
                if framing:
                    if not is_notification:
                        _write_message(_resp_error(msg_id, 1003, str(e)), framing)
            except Exception as e:  # pragma: no cover
                if framing:
                    if not is_notification:
                        _write_message(
                            _internal_error(msg_id, method if isinstance(method, str) else None, e),
                            framing,
                        )
            if startup_log_pending and framing:
                _write_message(
                    {
                        "jsonrpc": JSONRPC,
                        "method": "log",
                        "params": {
                            "level": "info",
                            "message": "mcp-geo stdio adapter starting",
                        },
                    },
                    framing,
                )
                startup_log_pending = False
        try:
            if framing and _bool_env("MCP_STDIO_LOG_STARTUP"):
                _write_message(
                    {
                        "jsonrpc": JSONRPC,
                        "method": "log",
                        "params": {"level": "info", "message": "adapter exiting"},
                    },
                    framing,
                )
        except Exception:  # pragma: no cover
            pass
    finally:
        _set_elicitation_handler(None)
        sys.stdout = orig_stdout  # type: ignore

if __name__ == "__main__":  # pragma: no cover
    main()
