from __future__ import annotations

import asyncio
import base64
import binascii
import hashlib
import hmac
import json
import os
import threading
import time
import uuid
from typing import Any, cast

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse, Response, StreamingResponse
from loguru import logger

from server import stdio_adapter
from server.mcp.client_capabilities import (
    bool_env as _shared_bool_env,
)
from server.mcp.client_capabilities import (
    client_supports_ui as _shared_client_supports_ui,
)
from server.mcp.client_capabilities import (
    read_bool_env as _shared_read_bool_env,
)
from server.mcp.client_capabilities import (
    summarize_client_capabilities as _summarize_client_capabilities,
)
from server.mcp.client_capabilities import (
    ui_fallback_for_tool as _shared_ui_fallback_for_tool,
)
from server.mcp.elicitation_forms import (
    apply_ons_select_elicitation_result,
    apply_toolset_selection_elicitation_result,
    build_ons_select_elicitation_params,
    build_toolset_selection_elicitation_params,
    client_supports_elicitation_form,
)
from server.mcp.prompts import get_prompt, list_prompts
from server.mcp.resource_catalog import MCP_APPS_MIME
from server.mcp.tool_search import get_toolset_catalog, resolve_default_toolset_filters_from_env
from server.observability import record_tool_call
from server.protocol import (
    HTTP_DEFAULT_PROTOCOL_VERSION,
    PROTOCOL_VERSION,
    SUPPORTED_PROTOCOL_VERSIONS,
    is_supported_protocol_version,
    negotiate_protocol_version,
    normalize_protocol_version,
)
from tools.registry import get as get_tool

router = APIRouter()

JSONRPC = stdio_adapter.JSONRPC

_SESSION_LOCK = threading.Lock()
_SESSION_STATE: dict[str, dict[str, Any]] = {}
_MCP_HTTP_METRICS_LOCK = threading.Lock()
_AUTH_FAILURES_TOTAL: dict[str, int] = {}
_SESSION_QUOTA_REJECTIONS_TOTAL = 0
try:
    _SESSION_TTL_SECONDS = float(
        (os.getenv("MCP_HTTP_SESSION_TTL", "") or "900").strip() or "900"
    )
except ValueError:
    _SESSION_TTL_SECONDS = 0.0
try:
    _SESSION_TOOL_CALL_LIMIT = int(
        (os.getenv("MCP_HTTP_SESSION_TOOL_CALL_LIMIT", "") or "100").strip() or "100"
    )
except ValueError:
    _SESSION_TOOL_CALL_LIMIT = 0


class MethodNotFound(Exception):
    pass


class AuthenticationError(Exception):
    pass


class AuthorizationError(Exception):
    pass


class SessionQuotaExceeded(Exception):
    pass


def _cleanup_sessions(now: float) -> None:
    if _SESSION_TTL_SECONDS <= 0:
        return
    cutoff = now - _SESSION_TTL_SECONDS
    with _SESSION_LOCK:
        stale = [sid for sid, state in _SESSION_STATE.items() if state.get("last_seen", 0) < cutoff]
        for sid in stale:
            _SESSION_STATE.pop(sid, None)


def _get_session(request: Request) -> tuple[str, dict[str, Any]]:
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


def _b64url_decode(value: str) -> bytes:
    padded = value + "=" * (-len(value) % 4)
    try:
        return base64.urlsafe_b64decode(padded.encode("ascii"))
    except (ValueError, UnicodeEncodeError, binascii.Error) as exc:
        raise AuthenticationError("Invalid bearer token encoding") from exc


def _parse_scopes(claims: dict[str, Any]) -> set[str]:
    scope_claim = claims.get("scope")
    if isinstance(scope_claim, str):
        return {item for item in scope_claim.split() if item}
    scp_claim = claims.get("scp")
    if isinstance(scp_claim, list):
        return {str(item).strip() for item in scp_claim if str(item).strip()}
    if isinstance(scp_claim, str):
        return {item for item in scp_claim.split() if item}
    return set()


def _load_bearer_token() -> str:
    return (os.getenv("MCP_HTTP_AUTH_TOKEN", "") or "").strip()


def _load_jwt_secret() -> str:
    return (os.getenv("MCP_HTTP_JWT_HS256_SECRET", "") or "").strip()


def _auth_mode() -> str:
    mode = (os.getenv("MCP_HTTP_AUTH_MODE", "") or "").strip().lower()
    if not mode:
        if _load_jwt_secret():
            return "hs256_jwt"
        if _load_bearer_token():
            return "static_bearer"
        return "off"
    if mode not in {"off", "static_bearer", "hs256_jwt"}:
        return "off"
    return mode


def _bearer_token_from_request(request: Request) -> str:
    auth_header = (request.headers.get("authorization") or "").strip()
    if not auth_header.lower().startswith("bearer "):
        raise AuthenticationError("Missing bearer token")
    token = auth_header[7:].strip()
    if not token:
        raise AuthenticationError("Missing bearer token")
    return token


def _verify_hs256_jwt(token: str) -> dict[str, Any]:
    secret = _load_jwt_secret()
    if not secret:
        raise AuthenticationError("JWT auth secret is not configured")
    parts = token.split(".")
    if len(parts) != 3:
        raise AuthenticationError("Invalid bearer token format")
    try:
        signing_input = ".".join(parts[:2]).encode("ascii")
    except UnicodeEncodeError as exc:
        raise AuthenticationError("Invalid bearer token encoding") from exc
    signature = _b64url_decode(parts[2])
    expected = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    if not hmac.compare_digest(signature, expected):
        raise AuthenticationError("Invalid bearer token signature")
    try:
        header = json.loads(_b64url_decode(parts[0]).decode("utf-8"))
        claims = json.loads(_b64url_decode(parts[1]).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AuthenticationError("Invalid bearer token payload") from exc
    if not isinstance(header, dict) or header.get("alg") != "HS256":
        raise AuthenticationError("Unsupported bearer token algorithm")
    if not isinstance(claims, dict):
        raise AuthenticationError("Invalid bearer token claims")

    now = time.time()
    leeway_raw = (os.getenv("MCP_HTTP_JWT_CLOCK_SKEW_SECONDS", "") or "").strip()
    try:
        leeway = float(leeway_raw or "30")
    except ValueError:
        leeway = 30.0
    exp = claims.get("exp")
    if not isinstance(exp, (int, float)) or float(exp) < now - leeway:
        raise AuthenticationError("Bearer token is expired")
    nbf = claims.get("nbf")
    if isinstance(nbf, (int, float)) and float(nbf) > now + leeway:
        raise AuthenticationError("Bearer token is not yet valid")
    sub = claims.get("sub")
    if not isinstance(sub, str) or not sub.strip():
        raise AuthenticationError("Bearer token is missing subject")
    audience = (os.getenv("MCP_HTTP_JWT_AUDIENCE", "") or "").strip()
    if audience:
        aud = claims.get("aud")
        if isinstance(aud, str):
            aud_values = {aud}
        elif isinstance(aud, list):
            aud_values = {str(item) for item in aud}
        else:
            aud_values = set()
        if audience not in aud_values:
            raise AuthorizationError("Bearer token audience is not permitted")
    issuer = (os.getenv("MCP_HTTP_JWT_ISSUER", "") or "").strip()
    if issuer and claims.get("iss") != issuer:
        raise AuthorizationError("Bearer token issuer is not permitted")
    required_scope_env = (os.getenv("MCP_HTTP_JWT_REQUIRED_SCOPES", "") or "").strip()
    required_scopes = {item.strip() for item in required_scope_env.split(",") if item.strip()}
    if required_scopes:
        scopes = _parse_scopes(claims)
        missing = sorted(required_scopes - scopes)
        if missing:
            raise AuthorizationError(
                "Bearer token is missing required scopes: " + ", ".join(missing)
            )
    return claims


def _authenticate_request(request: Request, session_state: dict[str, Any]) -> dict[str, Any] | None:
    mode = _auth_mode()
    if mode == "off":
        return None
    token = _bearer_token_from_request(request)
    if mode == "static_bearer":
        expected = _load_bearer_token()
        if not expected:
            raise AuthenticationError("Static bearer auth token is not configured")
        if not hmac.compare_digest(token, expected):
            raise AuthenticationError("Invalid bearer token")
        subject = "static-bearer-client"
        claims: dict[str, Any] = {"sub": subject, "scope": "mcp"}
    else:
        claims = _verify_hs256_jwt(token)
        subject = str(claims["sub"])

    bound_subject = session_state.get("auth_subject")
    if bound_subject is None:
        session_state["auth_subject"] = subject
    elif bound_subject != subject:
        raise AuthorizationError("Session is bound to a different authenticated subject")
    session_state["auth_mode"] = mode
    return claims


def _enforce_session_quota(
    method: str,
    session_state: dict[str, Any],
    auth_claims: dict[str, Any] | None = None,
) -> None:
    if method != "tools/call":
        return
    if _SESSION_TOOL_CALL_LIMIT <= 0:
        return
    with _SESSION_LOCK:
        current = int(session_state.get("tool_call_count", 0))
        if current >= _SESSION_TOOL_CALL_LIMIT:
            raise SessionQuotaExceeded("Per-session tool call limit exceeded")
        session_state["tool_call_count"] = current + 1
        if auth_claims and isinstance(auth_claims.get("sub"), str):
            session_state["last_authenticated_subject"] = auth_claims["sub"]


def _record_auth_failure(reason: str) -> None:
    normalized = reason.strip().lower().replace(" ", "_") if reason.strip() else "unknown"
    with _MCP_HTTP_METRICS_LOCK:
        _AUTH_FAILURES_TOTAL[normalized] = _AUTH_FAILURES_TOTAL.get(normalized, 0) + 1


def _record_session_quota_rejection() -> None:
    global _SESSION_QUOTA_REJECTIONS_TOTAL
    with _MCP_HTTP_METRICS_LOCK:
        _SESSION_QUOTA_REJECTIONS_TOTAL += 1


def _authentication_failure_response(msg_id: Any, headers: dict[str, str]) -> JSONResponse:
    _record_auth_failure("authentication")
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=_resp_error(msg_id, 1004, "Authentication failed"),
        headers=headers,
    )


def _authorization_failure_response(msg_id: Any, headers: dict[str, str]) -> JSONResponse:
    _record_auth_failure("authorization")
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content=_resp_error(msg_id, 1005, "Forbidden"),
        headers=headers,
    )


def _session_quota_failure_response(msg_id: Any, headers: dict[str, str]) -> JSONResponse:
    _record_session_quota_rejection()
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content=_resp_error(msg_id, 1006, "Session quota exceeded"),
        headers=headers,
    )


def build_prometheus_lines() -> list[str]:
    lines = [
        "# HELP mcp_http_auth_failures_total Total failed MCP HTTP auth decisions by reason",
        "# TYPE mcp_http_auth_failures_total counter",
        "# HELP mcp_http_session_quota_rejections_total Total MCP HTTP session quota rejections",
        "# TYPE mcp_http_session_quota_rejections_total counter",
        "# HELP mcp_http_sessions_active Current active MCP HTTP sessions",
        "# TYPE mcp_http_sessions_active gauge",
    ]
    with _MCP_HTTP_METRICS_LOCK:
        auth_failures = dict(_AUTH_FAILURES_TOTAL)
        quota_rejections = _SESSION_QUOTA_REJECTIONS_TOTAL
    for reason, count in sorted(auth_failures.items()):
        lines.append(f'mcp_http_auth_failures_total{{reason="{reason}"}} {count}')
    lines.append(f"mcp_http_session_quota_rejections_total {quota_rejections}")
    with _SESSION_LOCK:
        lines.append(f"mcp_http_sessions_active {len(_SESSION_STATE)}")
    return lines


def _read_bool_env(name: str) -> bool | None:
    return cast(bool | None, _shared_read_bool_env(name))


def _bool_env(name: str, default: bool = False) -> bool:
    return cast(bool, _shared_bool_env(name, default=default))


def _client_supports_ui(capabilities: dict[str, Any]) -> bool:
    return cast(
        bool,
        _shared_client_supports_ui(capabilities, override_env="MCP_HTTP_UI_SUPPORTED"),
    )


def _accepts_event_stream(request: Request) -> bool:
    accept = request.headers.get("accept", "")
    if not isinstance(accept, str):
        return False
    accept_lower = accept.lower()
    # Some clients (and test harnesses) send "*/*"; treat that as compatible.
    return (
        ("text/event-stream" in accept_lower)
        or ("*/*" in accept_lower)
        or (not accept_lower.strip())
    )


def _needs_toolset_elicitation(payload: dict[str, Any]) -> bool:
    if payload.get("skipElicitation") is True:
        return False
    return not any(
        payload.get(key) is not None
        for key in ("toolset", "includeToolsets", "excludeToolsets")
    )


def _build_toolset_elicitation_params(payload: dict[str, Any]) -> dict[str, Any]:
    catalog = get_toolset_catalog()
    default_toolset, default_include, default_exclude = resolve_default_toolset_filters_from_env()
    include_seed = list(default_include)
    if default_toolset:
        include_seed.append(default_toolset)
    query = payload.get("query")
    query_text = query.strip() if isinstance(query, str) else ""
    return cast(
        dict[str, Any],
        build_toolset_selection_elicitation_params(
        query=query_text,
        toolset_names=sorted(catalog.keys()),
        default_include=include_seed,
        default_exclude=default_exclude,
        ),
    )


def _sse_event(data: str, *, event_id: str | None = None, retry_ms: int | None = None) -> str:
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


def _pending_bucket(session_state: dict[str, Any]) -> dict[str, Any]:
    pending = session_state.get("pending")
    if isinstance(pending, dict):
        return pending
    pending = {}
    session_state["pending"] = pending
    return pending


def _next_elicitation_request_id(session_state: dict[str, Any]) -> str:
    with _SESSION_LOCK:
        raw = session_state.get("elicitation_seq", 0)
        try:
            seq = int(raw)
        except (TypeError, ValueError):
            seq = 0
        seq += 1
        session_state["elicitation_seq"] = seq
    return f"elicitation-{seq}"


def _register_pending(session_state: dict[str, Any], request_id: str) -> asyncio.Future[Any]:
    loop = asyncio.get_running_loop()
    fut: asyncio.Future[Any] = loop.create_future()
    with _SESSION_LOCK:
        pending = _pending_bucket(session_state)
        pending[request_id] = {"loop": loop, "future": fut, "created_at": time.time()}
    return fut


def _resolve_pending(session_state: dict[str, Any], request_id: Any, result: Any) -> bool:
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


def _resp_success(msg_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": JSONRPC, "id": msg_id, "result": result}


def _resp_error(msg_id: Any, code: int, message: str, data: Any = None) -> dict[str, Any]:
    err: dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    return {"jsonrpc": JSONRPC, "id": msg_id, "error": err}


def _internal_error(msg_id: Any, method: str | None, exc: Exception) -> dict[str, Any]:
    correlation_id = str(uuid.uuid4())
    logger.error(
        "MCP http internal error correlation_id={} method={} msg_id={} error_type={}",
        correlation_id,
        method,
        msg_id,
        type(exc).__name__,
    )
    return _resp_error(msg_id, -32603, "Internal error", {"correlationId": correlation_id})


def _initialize(params: dict[str, Any], session_state: dict[str, Any]) -> dict[str, Any]:
    requested = params.get("protocolVersion")
    protocol_version = negotiate_protocol_version(requested)
    capabilities = params.get("capabilities")
    session_state["capabilities"] = capabilities if isinstance(capabilities, dict) else {}
    session_state["capabilitySummary"] = _summarize_client_capabilities(
        capabilities=session_state["capabilities"],
        requested_protocol_version=requested,
        negotiated_protocol_version=protocol_version,
    )
    session_state["protocolVersion"] = protocol_version
    logger.info(
        "MCP initialize (http) support_summary={summary}",
        summary=session_state["capabilitySummary"],
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


def _protocol_error_response(
    *,
    headers: dict[str, str],
    message: str,
    requested: str | None = None,
    negotiated: str | None = None,
) -> JSONResponse:
    data: dict[str, Any] = {"supported": list(SUPPORTED_PROTOCOL_VERSIONS)}
    if requested is not None:
        data["requested"] = requested
    if negotiated is not None:
        data["negotiated"] = negotiated
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=_resp_error(None, -32600, message, data),
        headers=headers,
    )


def _resolve_request_protocol_version(
    *,
    request: Request,
    method: str,
    session_state: dict[str, Any],
    headers: dict[str, str],
) -> tuple[str, JSONResponse | None]:
    header_version = normalize_protocol_version(request.headers.get("mcp-protocol-version"))
    if header_version and not is_supported_protocol_version(header_version):
        return (
            PROTOCOL_VERSION,
            _protocol_error_response(
                headers=headers,
                message="Unsupported protocol version",
                requested=header_version,
            ),
        )

    negotiated = normalize_protocol_version(session_state.get("protocolVersion"))
    if negotiated and not is_supported_protocol_version(negotiated):
        negotiated = None

    # initialize performs negotiation in-band using params.protocolVersion.
    if method == "initialize":
        if header_version:
            return header_version, None
        if negotiated:
            return negotiated, None
        return HTTP_DEFAULT_PROTOCOL_VERSION, None

    if negotiated and header_version and header_version != negotiated:
        return (
            negotiated,
            _protocol_error_response(
                headers=headers,
                message="MCP-Protocol-Version does not match negotiated session protocol",
                requested=header_version,
                negotiated=negotiated,
            ),
        )

    if header_version:
        return header_version, None
    if negotiated:
        return negotiated, None
    return HTTP_DEFAULT_PROTOCOL_VERSION, None


def _call_tool(params: dict[str, Any], capabilities: dict[str, Any]) -> dict[str, Any]:
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
    started = time.perf_counter()
    status_code, data = tool.call(payload)
    if isinstance(data, dict):
        data = dict(data)
        if resolved_name == "os_mcp.descriptor":
            data.setdefault("transport", "http")
        fallback = _shared_ui_fallback_for_tool(
            resolved_name,
            payload,
            data,
            ui_supported=_client_supports_ui(capabilities),
            build_static_map_fallback=stdio_adapter._build_static_map_fallback,
            build_stats_dashboard_fallback=stdio_adapter._build_stats_dashboard_fallback,
        )
        if fallback:
            data["fallback"] = fallback
    record_tool_call(
        tool_name=resolved_name,
        transport="mcp_http",
        payload=payload,
        result=data,
        status_code=status_code,
        latency_ms=(time.perf_counter() - started) * 1000.0,
    )
    ok = 200 <= status_code < 300
    result: dict[str, Any] = {"status": status_code, "ok": ok, "data": data}
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
        structured = data.get("structuredContent")
        if isinstance(structured, dict):
            result["structuredContent"] = structured
        else:
            result["structuredContent"] = stdio_adapter._default_structured_content(data)
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


def _dispatch(method: str, params: dict[str, Any], session_state: dict[str, Any]) -> Any:
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
    msg_id: Any = None
    method: str | None = None
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
        try:
            _authenticate_request(request, session_state)
        except AuthenticationError:
            return _authentication_failure_response(msg_id, headers)
        except AuthorizationError:
            return _authorization_failure_response(msg_id, headers)
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
    protocol_version, protocol_error = _resolve_request_protocol_version(
        request=request,
        method=method,
        session_state=session_state,
        headers=headers,
    )
    headers["mcp-protocol-version"] = protocol_version
    if protocol_error is not None:
        return protocol_error
    params = msg.get("params")
    if params is None:
        params = {}
    if not isinstance(params, dict):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=_resp_error(msg_id, -32602, "Invalid params"),
            headers=headers,
        )
    try:
        auth_claims = _authenticate_request(request, session_state)
        _enforce_session_quota(method, session_state, auth_claims)
    except AuthenticationError:
        return _authentication_failure_response(msg_id, headers)
    except AuthorizationError:
        return _authorization_failure_response(msg_id, headers)
    except SessionQuotaExceeded:
        return _session_quota_failure_response(msg_id, headers)
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
            wants_elicitation = (
                _bool_env("MCP_HTTP_ELICITATION_ENABLED", default=True)
                and _accepts_event_stream(request)
                and client_supports_elicitation_form(capabilities)
            )
            if resolved_name == "os_mcp.select_toolsets" and wants_elicitation:
                if _needs_toolset_elicitation(payload):
                    elicitation_params = _build_toolset_elicitation_params(payload)
                    elicitation_id = _next_elicitation_request_id(session_state)
                    fut = _register_pending(session_state, elicitation_id)

                    async def _gen_toolset():
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
                            except TimeoutError:
                                final_result = _call_tool(call_params, capabilities)
                            else:
                                if isinstance(elicitation_result, dict):
                                    should_continue, elicitation_error = (
                                        apply_toolset_selection_elicitation_result(
                                            payload,
                                            elicitation_result,
                                        )
                                    )
                                    if should_continue:
                                        final_result = _call_tool(call_params, capabilities)
                                    else:
                                        data = elicitation_error or {
                                            "isError": True,
                                            "code": "ELICITATION_CANCELLED",
                                            "message": "Elicitation cancelled.",
                                        }
                                        final_result = {
                                            "status": 409,
                                            "ok": False,
                                            "data": data,
                                            "isError": True,
                                            "content": stdio_adapter._tool_content_from_data(
                                                data,
                                                allow_resource=False,
                                            ),
                                        }
                                else:
                                    final_result = _call_tool(call_params, capabilities)
                            response_payload = json.dumps(
                                _resp_success(msg_id, final_result),
                                separators=(",", ":"),
                            )
                            yield _sse_event(
                                response_payload,
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
                        _gen_toolset(),
                        media_type="text/event-stream",
                        headers=stream_headers,
                    )
            initial_result = _call_tool(call_params, capabilities)
            data = initial_result.get("data") if isinstance(initial_result, dict) else None
            if (
                resolved_name == "ons_select.search"
                and isinstance(data, dict)
                and data.get("needsElicitation") is True
                and wants_elicitation
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
                            except TimeoutError:
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
                            response_payload = json.dumps(
                                _resp_success(msg_id, final_result),
                                separators=(",", ":"),
                            )
                            yield _sse_event(
                                response_payload,
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
        if method == "initialize" and isinstance(result, dict):
            negotiated = normalize_protocol_version(result.get("protocolVersion"))
            if negotiated and is_supported_protocol_version(negotiated):
                headers["mcp-protocol-version"] = negotiated
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
            content=_internal_error(msg_id, method, exc),
            headers=headers,
        )
