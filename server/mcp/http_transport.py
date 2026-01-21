from __future__ import annotations

import json
import os
import threading
import time
import uuid
from typing import Any, Dict, Optional, Tuple

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse, Response

from server import stdio_adapter
from tools.registry import get as get_tool

router = APIRouter()

JSONRPC = stdio_adapter.JSONRPC
PROTOCOL_VERSION = stdio_adapter.PROTOCOL_VERSION

_SESSION_LOCK = threading.Lock()
_SESSION_STATE: Dict[str, Dict[str, Any]] = {}
try:
    _SESSION_TTL_SECONDS = float(
        (os.getenv("MCP_HTTP_SESSION_TTL", "") or "0").strip() or "0"
    )
except ValueError:
    _SESSION_TTL_SECONDS = 0.0


class MethodNotFound(Exception):
    pass


def _cleanup_sessions(now: float) -> None:
    if _SESSION_TTL_SECONDS <= 0:
        return
    cutoff = now - _SESSION_TTL_SECONDS
    with _SESSION_LOCK:
        stale = [sid for sid, state in _SESSION_STATE.items() if state.get("last_seen", 0) < cutoff]
        for sid in stale:
            _SESSION_STATE.pop(sid, None)


def _get_session(request: Request) -> Tuple[str, Dict[str, Any]]:
    session_id = request.headers.get("mcp-session-id")
    now = time.time()
    _cleanup_sessions(now)
    with _SESSION_LOCK:
        if session_id and session_id in _SESSION_STATE:
            state = _SESSION_STATE[session_id]
            state["last_seen"] = now
            return session_id, state
        resolved = session_id or str(uuid.uuid4())
        state = {"capabilities": {}, "last_seen": now}
        _SESSION_STATE[resolved] = state
        return resolved, state


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
    override = _read_bool_env("MCP_HTTP_UI_SUPPORTED")
    if override is not None:
        return override
    for key in ("uiResources", "mcpApps", "mcp_apps", "mcpAppsUi"):
        if key not in capabilities:
            continue
        value = capabilities[key]
        if isinstance(value, dict):
            return any(bool(v) for v in value.values())
        return bool(value)
    return False


def _resp_success(msg_id: Any, result: Any) -> Dict[str, Any]:
    return {"jsonrpc": JSONRPC, "id": msg_id, "result": result}


def _resp_error(msg_id: Any, code: int, message: str, data: Any = None) -> Dict[str, Any]:
    err: Dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    return {"jsonrpc": JSONRPC, "id": msg_id, "error": err}


def _initialize(params: Dict[str, Any], session_state: Dict[str, Any]) -> Dict[str, Any]:
    requested = params.get("protocolVersion")
    protocol_version = requested if isinstance(requested, str) else PROTOCOL_VERSION
    capabilities = params.get("capabilities")
    session_state["capabilities"] = capabilities if isinstance(capabilities, dict) else {}
    return {
        "protocolVersion": protocol_version,
        "serverInfo": {"name": "mcp-geo", "version": stdio_adapter.SERVER_VERSION},
        "capabilities": {
            "tools": {"list": True, "call": True, "search": True},
            "resources": {"list": True, "read": True, "describe": True},
            "toolSearch": {"query": True},
            "uiResources": {"list": True},
            "skills": {"list": True},
        },
        "server": "mcp-geo",
        "version": stdio_adapter.SERVER_VERSION,
    }


def _call_tool(params: Dict[str, Any], capabilities: Dict[str, Any]) -> Dict[str, Any]:
    name = params.get("tool") or params.get("name")
    if not isinstance(name, str):
        raise ValueError("Missing tool name")
    resolved_name = stdio_adapter._resolve_tool_name(name)
    tool = get_tool(resolved_name)
    if not tool:
        raise LookupError(f"Unknown tool '{name}'")
    payload = params.get("args") or params.get("arguments") or params.get("payload") or {}
    if not isinstance(payload, dict):
        raise TypeError("Payload must be object")
    status_code, data = tool.call(payload)
    if isinstance(data, dict):
        data = dict(data)
        ui_supported = _client_supports_ui(capabilities)
        if resolved_name.startswith("os_apps.render_") and not ui_supported:
            fallback = stdio_adapter._build_static_map_fallback(payload, data)
            if fallback:
                data["fallback"] = fallback
    ok = 200 <= status_code < 300
    result: Dict[str, Any] = {"status": status_code, "ok": ok, "data": data}
    allow_resource = _bool_env("MCP_HTTP_RESOURCE_CONTENT", default=True)
    result["content"] = stdio_adapter._tool_content_from_data(data, allow_resource=allow_resource)
    ui_uris = stdio_adapter._extract_ui_resource_uris(data)
    if ui_uris:
        result["uiResourceUris"] = ui_uris
        if isinstance(data, dict):
            meta = data.get("_meta")
            if isinstance(meta, dict):
                result["_meta"] = meta
    if not ok or (isinstance(data, dict) and data.get("isError") is True):
        result["isError"] = True
    return result


def _dispatch(method: str, params: Dict[str, Any], session_state: Dict[str, Any]) -> Any:
    if method == "initialize":
        return _initialize(params, session_state)
    if method == "tools/list":
        return stdio_adapter.handle_list_tools(params)
    if method == "tools/search":
        return stdio_adapter.handle_search_tools(params)
    if method == "tools/call":
        return _call_tool(params, session_state.get("capabilities", {}))
    if method == "resources/list":
        return stdio_adapter.handle_list_resources(params)
    if method == "resources/describe":
        return {"resources": stdio_adapter.RESOURCE_LIST}
    if method == "resources/get":
        return stdio_adapter.handle_get_resource(params)
    if method == "shutdown":
        return None
    raise MethodNotFound(f"Method not found: {method}")


@router.post("/mcp")
async def mcp_endpoint(request: Request):
    session_id, session_state = _get_session(request)
    headers = {"mcp-session-id": session_id}
    try:
        raw_body = await request.body()
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=_resp_error(None, -32700, "Parse error"),
            headers=headers,
        )
    if not raw_body:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=_resp_error(None, -32600, "Empty request"),
            headers=headers,
        )
    try:
        msg = json.loads(raw_body)
    except json.JSONDecodeError:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=_resp_error(None, -32700, "Parse error"),
            headers=headers,
        )
    if not isinstance(msg, dict):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=_resp_error(None, -32600, "Invalid Request"),
            headers=headers,
        )
    msg_id = msg.get("id")
    if msg.get("jsonrpc") != JSONRPC:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=_resp_error(msg_id, -32600, "Invalid Request"),
            headers=headers,
        )
    method = msg.get("method")
    if not isinstance(method, str):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=_resp_error(msg_id, -32600, "Invalid Request"),
            headers=headers,
        )
    params = msg.get("params")
    if params is None:
        params = {}
    if not isinstance(params, dict):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=_resp_error(msg_id, -32602, "Invalid params"),
            headers=headers,
        )
    if msg_id is None:
        try:
            _dispatch(method, params, session_state)
        except Exception:
            pass
        return Response(status_code=status.HTTP_204_NO_CONTENT, headers=headers)
    try:
        result = _dispatch(method, params, session_state)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=_resp_success(msg_id, result),
            headers=headers,
        )
    except MethodNotFound as exc:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=_resp_error(msg_id, -32601, str(exc)),
            headers=headers,
        )
    except LookupError as exc:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=_resp_error(msg_id, 1001, str(exc)),
            headers=headers,
        )
    except ValueError as exc:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=_resp_error(msg_id, 1002, str(exc)),
            headers=headers,
        )
    except TypeError as exc:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=_resp_error(msg_id, 1003, str(exc)),
            headers=headers,
        )
    except Exception as exc:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=_resp_error(msg_id, -32603, f"Internal error: {exc}"),
            headers=headers,
        )
