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
from pathlib import Path
from typing import Any, Dict, List, Optional, TextIO

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Import side-effects to register tools
import tools.registry as _reg  # noqa: F401
from server.mcp import tools as _mcp_import  # noqa: F401

from tools.registry import all_tools, get as get_tool
from server.mcp.resource_catalog import (
    DATA_RESOURCE_PREFIX,
    MCP_APPS_MIME,
    list_skill_resources,
    list_ui_resources,
    load_skill_content,
    load_ui_content,
    resolve_skill_resource,
    resolve_ui_resource,
)
from tools.os_apps import build_ui_tool_meta
from server.mcp.tool_search import get_tool_metadata, search_tools
from server import __version__ as SERVER_VERSION
from server.protocol import PROTOCOL_VERSION

JSONRPC = "2.0"

RESOURCE_LIST: List[dict[str, Any]] = []
RESOURCE_LIST.extend(list_skill_resources())
RESOURCE_LIST.extend(list_ui_resources())


def handle_get_resource(params: Dict[str, Any]) -> Any:
    name = params.get("name")
    uri = params.get("uri")
    if not name and not uri:
        raise ValueError("Missing resource name or uri")
    if uri:
        if isinstance(uri, str) and uri.startswith(DATA_RESOURCE_PREFIX):
            name = uri[len(DATA_RESOURCE_PREFIX):]
            raise LookupError("Resource not available in live-only mode")
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


def _sanitize_tool_name(name: str, seen: Dict[str, str]) -> str:
    base = re.sub(r"[^A-Za-z0-9_-]", "_", name)
    if not base:
        base = "tool"
    candidate = base
    if len(candidate) > 64:
        digest = hashlib.sha1(name.encode()).hexdigest()[:8]
        max_prefix = 64 - 1 - len(digest)
        candidate = f"{candidate[:max_prefix]}_{digest}"
    if candidate in seen and seen[candidate] != name:
        digest = hashlib.sha1(name.encode()).hexdigest()[:8]
        max_prefix = 64 - 1 - len(digest)
        candidate = f"{base[:max_prefix]}_{digest}"
    return candidate


def _build_tool_name_maps() -> tuple[Dict[str, str], Dict[str, str]]:
    original_to_sanitized: Dict[str, str] = {}
    sanitized_to_original: Dict[str, str] = {}
    for tool in all_tools():
        original = tool.name
        sanitized = _sanitize_tool_name(original, sanitized_to_original)
        original_to_sanitized[original] = sanitized
        sanitized_to_original[sanitized] = original
    return original_to_sanitized, sanitized_to_original


def _resolve_tool_name(name: str) -> str:
    if get_tool(name):
        return name
    _, sanitized_to_original = _build_tool_name_maps()
    return sanitized_to_original.get(name, name)


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

def _read_bool_env(name: str) -> Optional[bool]:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return None
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _bool_env(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _client_supports_ui(capabilities: Dict[str, Any]) -> bool:
    override = _read_bool_env("MCP_STDIO_UI_SUPPORTED")
    if override is not None:
        return override
    extensions = capabilities.get("extensions", {}) if isinstance(capabilities, dict) else {}
    ui_ext = extensions.get("io.modelcontextprotocol/ui")
    if isinstance(ui_ext, dict):
        mime_types = ui_ext.get("mimeTypes")
        if isinstance(mime_types, list):
            return MCP_APPS_MIME in mime_types
    return False


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
    content.append({"type": "text", "text": text})
    return content


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


def _extract_initial_view(payload: Dict[str, Any], data: Any) -> tuple[Optional[float], Optional[float], Optional[int]]:
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


def _build_static_map_fallback(payload: Dict[str, Any], data: Any) -> Optional[Dict[str, Any]]:
    lat, lng, zoom = _extract_initial_view(payload, data)
    if lat is None or lng is None:
        return None
    bbox = _fallback_bbox(lat, lng, zoom)
    maps_tool = get_tool("os_maps.render")
    render: Optional[Dict[str, Any]] = None
    status: Optional[int] = None
    if maps_tool:
        status, render_data = maps_tool.call({"tool": "os_maps.render", "bbox": bbox})
        if status == 200 and isinstance(render_data, dict):
            render = render_data.get("render")
    fallback: Dict[str, Any] = {
        "type": "static_map",
        "center": {"lat": lat, "lng": lng},
        "bbox": bbox,
        "note": "Client does not support MCP-Apps UI; use render.urlTemplate with your API key.",
    }
    if zoom is not None:
        fallback["zoom"] = zoom
    if render is not None:
        fallback["render"] = render
    if status is not None and status != 200:
        fallback["mapError"] = {"status": status}
    return fallback


def handle_initialize(params: Dict[str, Any]) -> Any:
    requested = params.get("protocolVersion")
    protocol_version = requested if isinstance(requested, str) else PROTOCOL_VERSION
    global CLIENT_CAPABILITIES
    capabilities = params.get("capabilities")
    CLIENT_CAPABILITIES = capabilities if isinstance(capabilities, dict) else {}
    return {
        "protocolVersion": protocol_version,
        "serverInfo": {"name": "mcp-geo", "version": SERVER_VERSION},
        "capabilities": {
            "tools": {"list": True, "call": True},
            "resources": {"list": True, "read": True},
            "extensions": {
                "io.modelcontextprotocol/ui": {
                    "mimeTypes": [MCP_APPS_MIME],
                }
            },
        },
        "server": "mcp-geo",
        "version": SERVER_VERSION,
    }

def handle_list_tools(_params: Dict[str, Any]) -> Any:
    tool_entries: list[dict[str, Any]] = []
    original_to_sanitized, _ = _build_tool_name_maps()
    for t in all_tools():
        meta = get_tool_metadata(t)
        name = original_to_sanitized.get(t.name, t.name)
        annotations = dict(meta.get("annotations", {}))
        if name != t.name:
            annotations["originalName"] = t.name
        entry: Dict[str, Any] = {
            "name": name,
            "description": t.description,
            "version": t.version,
            "inputSchema": t.input_schema,
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
    return {"tools": tool_entries}


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
    results = search_tools(
        query,
        mode=mode,
        limit=limit,
        category=category,
        include_schemas=include_schemas,
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
        entry["name"] = sanitized
    return {"tools": results, "count": len(results), "mode": mode}

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
    status, data = tool.call(payload)
    if isinstance(data, dict):
        data = dict(data)
        if resolved_name == "os_mcp.descriptor":
            data.setdefault("transport", "stdio")
        ui_supported = _client_supports_ui(CLIENT_CAPABILITIES)
        if resolved_name.startswith("os_apps.render_") and not ui_supported:
            fallback = _build_static_map_fallback(payload, data)
            if fallback:
                data["fallback"] = fallback
    ok = 200 <= status < 300
    result: Dict[str, Any] = {"status": status, "ok": ok, "data": data}
    allow_resource = _bool_env("MCP_STDIO_RESOURCE_CONTENT", default=False)
    if isinstance(data, dict):
        content_override = data.get("content")
        if isinstance(content_override, list):
            result["content"] = content_override
        else:
            result["content"] = _tool_content_from_data(data, allow_resource=allow_resource)
        if "structuredContent" in data:
            result["structuredContent"] = data["structuredContent"]
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
                            _resp_error(msg_id, -32603, f"Internal error: {e}"),
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
        sys.stdout = orig_stdout  # type: ignore

if __name__ == "__main__":  # pragma: no cover
    main()
