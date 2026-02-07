from __future__ import annotations

import asyncio
import json
import os
import threading
import time
import uuid
from typing import Any, Dict, Optional, Tuple

from loguru import logger

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse, Response, StreamingResponse

from server import stdio_adapter
from server.mcp.elicitation_forms import (
    apply_ons_select_elicitation_result,
    build_ons_select_elicitation_params,
    client_supports_elicitation_form,
)
from server.mcp.resource_catalog import MCP_APPS_MIME
from server.mcp.prompts import get_prompt, list_prompts
from server.protocol import PROTOCOL_VERSION
from tools.registry import get as get_tool

router = APIRouter()

JSONRPC = stdio_adapter.JSONRPC

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
    extensions = capabilities.get("extensions", {}) if isinstance(capabilities, dict) else {}
    ui_ext = extensions.get("io.modelcontextprotocol/ui")
    if isinstance(ui_ext, dict):
        mime_types = ui_ext.get("mimeTypes")
        if isinstance(mime_types, list):
            return MCP_APPS_MIME in mime_types
    return False


def _accepts_event_stream(request: Request) -> bool:
    accept = request.headers.get("accept", "")
    if not isinstance(accept, str):
        return False
    accept_lower = accept.lower()
    # Some clients (and test harnesses) send "*/*"; treat that as compatible.
    return ("text/event-stream" in accept_lower) or ("*/*" in accept_lower) or (not accept_lower.strip())


def _sse_event(data: str, *, event_id: Optional[str] = None, retry_ms: Optional[int] = None) -> str:
    # SSE requires each field on its own line; terminate events with a blank line.
    lines: list[str] = []
    if retry_ms is not None:
        lines.append(f"retry: {retry_ms}")
    if event_id:
        lines.append(f"id: {event_id}")
    # Spec: "data field" can be empty; keep a single data line.
    lines.append(f"data: {data}")
    lines.append("")
    return "\n".join(lines) + "\n"


def _pending_bucket(session_state: Dict[str, Any]) -> Dict[str, Any]:
    pending = session_state.get("pending")
    if isinstance(pending, dict):
        return pending
    pending = {}
    session_state["pending"] = pending
    return pending


def _next_elicitation_request_id(session_state: Dict[str, Any]) -> str:
    with _SESSION_LOCK:
        raw = session_state.get("elicitation_seq", 0)
        try:
            seq = int(raw)
        except (TypeError, ValueError):
            seq = 0
        seq += 1
        session_state["elicitation_seq"] = seq
    return f"elicitation-{seq}"


def _register_pending(session_state: Dict[str, Any], request_id: str) -> asyncio.Future[Any]:
    loop = asyncio.get_running_loop()
    fut: asyncio.Future[Any] = loop.create_future()
    with _SESSION_LOCK:
        pending = _pending_bucket(session_state)
        pending[request_id] = {"loop": loop, "future": fut, "created_at": time.time()}
    return fut


def _resolve_pending(session_state: Dict[str, Any], request_id: Any, result: Any) -> bool:
    if not isinstance(request_id, str):
        return False
    with _SESSION_LOCK:
        pending = session_state.get("pending")
        if not isinstance(pending, dict):
            return False
        entry = pending.pop(request_id, None)
    if not isinstance(entry, dict):
        return False
    loop = entry.get("loop")
    fut = entry.get("future")
    if not isinstance(loop, asyncio.AbstractEventLoop):
        return False
    if not isinstance(fut, asyncio.Future):
        return False
    try:
        loop.call_soon_threadsafe(fut.set_result, result)
    except RuntimeError:
        return False
    return True


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
    logger.info(
        "MCP initialize (http) capabilities={capabilities}",
        capabilities=session_state["capabilities"],
    )
    return {
        "protocolVersion": protocol_version,
        "serverInfo": {"name": "mcp-geo", "version": stdio_adapter.SERVER_VERSION},
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
        if resolved_name == "os_mcp.descriptor":
            data.setdefault("transport", "http")
        ui_supported = _client_supports_ui(capabilities)
        if resolved_name.startswith("os_apps.render_") and not ui_supported:
            fallback = stdio_adapter._build_static_map_fallback(payload, data)
            if fallback:
                data["fallback"] = fallback
    ok = 200 <= status_code < 300
    result: Dict[str, Any] = {"status": status_code, "ok": ok, "data": data}
    allow_resource = _bool_env("MCP_HTTP_RESOURCE_CONTENT", default=True)
    if isinstance(data, dict):
        content_override = data.get("content")
        if isinstance(content_override, list):
            result["content"] = content_override
        else:
            result["content"] = stdio_adapter._tool_content_from_data(
                data,
                allow_resource=allow_resource,
            )
        if "structuredContent" in data:
            result["structuredContent"] = data["structuredContent"]
        meta = data.get("_meta")
        if isinstance(meta, dict):
            result["_meta"] = meta
    else:
        result["content"] = stdio_adapter._tool_content_from_data(
            data,
            allow_resource=allow_resource,
        )
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
    if method == "resources/templates/list":
        return stdio_adapter.handle_list_resource_templates(params)
    if method == "resources/describe":
        return {"resources": stdio_adapter.RESOURCE_LIST}
    if method == "resources/read":
        return stdio_adapter.handle_get_resource(params)
    if method == "prompts/list":
        return {"prompts": list_prompts()}
    if method == "prompts/get":
        name = params.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Missing prompt name")
        prompt = get_prompt(name)
        if prompt is None:
            raise LookupError(f"Unknown prompt '{name}'")
        return prompt
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
    if method is None:
        # JSON-RPC response from the client (e.g., elicitation result).
        if msg_id is not None and ("result" in msg or "error" in msg):
            result = msg.get("result")
            if not _resolve_pending(session_state, msg_id, result):
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content=_resp_error(None, -32600, "Invalid Request"),
                    headers=headers,
                )
            return Response(status_code=status.HTTP_202_ACCEPTED, headers=headers)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=_resp_error(msg_id, -32600, "Invalid Request"),
            headers=headers,
        )
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
        return Response(status_code=status.HTTP_202_ACCEPTED, headers=headers)
    try:
        if method == "tools/call":
            capabilities = session_state.get("capabilities", {})
            if not isinstance(capabilities, dict):
                capabilities = {}
            name = params.get("tool") or params.get("name")
            if not isinstance(name, str):
                raise ValueError("Missing tool name")
            resolved_name = stdio_adapter._resolve_tool_name(name)
            payload = params.get("args") or params.get("arguments") or params.get("payload") or {}
            if not isinstance(payload, dict):
                raise TypeError("Payload must be object")
            payload = dict(payload)
            call_params = dict(params)
            call_params["args"] = payload
            call_params["arguments"] = payload
            call_params["payload"] = payload
            initial_result = _call_tool(call_params, capabilities)
            data = initial_result.get("data") if isinstance(initial_result, dict) else None
            if (
                resolved_name == "ons_select.search"
                and isinstance(data, dict)
                and data.get("needsElicitation") is True
                and _bool_env("MCP_HTTP_ELICITATION_ENABLED", default=True)
                and _accepts_event_stream(request)
                and client_supports_elicitation_form(capabilities)
            ):
                query = data.get("query") or payload.get("query") or payload.get("q") or ""
                if isinstance(query, str) and query.strip():
                    questions = data.get("elicitationQuestions")
                    question_list = questions if isinstance(questions, list) else None
                    elicitation_params = build_ons_select_elicitation_params(
                        query.strip(),
                        payload,
                        question_list,
                    )
                    elicitation_id = _next_elicitation_request_id(session_state)
                    fut = _register_pending(session_state, elicitation_id)

                    async def _gen():
                        try:
                            yield _sse_event("", event_id=f"{elicitation_id}-prime")
                            req_msg = {
                                "jsonrpc": JSONRPC,
                                "id": elicitation_id,
                                "method": "elicitation/create",
                                "params": elicitation_params,
                            }
                            yield _sse_event(
                                json.dumps(req_msg, separators=(",", ":")),
                                event_id=f"{elicitation_id}-request",
                            )
                            timeout_env = (
                                os.getenv("MCP_HTTP_ELICITATION_TIMEOUT_SECONDS", "") or ""
                            ).strip()
                            timeout_s = 120.0
                            if timeout_env:
                                try:
                                    timeout_s = float(timeout_env)
                                except ValueError:
                                    timeout_s = 120.0
                            try:
                                elicitation_result = await asyncio.wait_for(fut, timeout=timeout_s)
                            except asyncio.TimeoutError:
                                final_result = initial_result
                            else:
                                final_result = initial_result
                                if isinstance(elicitation_result, dict):
                                    changed, _error = apply_ons_select_elicitation_result(
                                        payload,
                                        elicitation_result,
                                    )
                                    if changed:
                                        final_result = _call_tool(call_params, capabilities)
                            yield _sse_event(
                                json.dumps(_resp_success(msg_id, final_result), separators=(",", ":")),
                                event_id=f"{elicitation_id}-response",
                            )
                        finally:
                            with _SESSION_LOCK:
                                pending = session_state.get("pending")
                                if isinstance(pending, dict):
                                    pending.pop(elicitation_id, None)

                    stream_headers = dict(headers)
                    stream_headers.setdefault("cache-control", "no-cache")
                    return StreamingResponse(
                        _gen(),
                        media_type="text/event-stream",
                        headers=stream_headers,
                    )
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=_resp_success(msg_id, initial_result),
                headers=headers,
            )

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
