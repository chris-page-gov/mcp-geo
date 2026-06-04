from __future__ import annotations

import base64
import json
from collections.abc import Mapping
from typing import Any

from loguru import logger

from server import __version__ as SERVER_VERSION
from server.mcp.resource_catalog import MCP_APPS_MIME
from server.protocol import (
    is_mcp_2026_rc_enabled,
    is_mcp_2026_rc_protocol,
    normalize_protocol_version,
    supported_protocol_versions,
)
from tools.registry import all_tools

JSON_SCHEMA_2020_12_DIALECT = "https://json-schema.org/draft/2020-12/schema"
DEFAULT_LIST_TTL_MS = 300_000
DEFAULT_PRIVATE_TTL_MS = 60_000
MAX_SCHEMA_DEPTH = 64
MAX_SCHEMA_NODES = 10_000

_TRACE_META_KEYS = ("traceparent", "tracestate", "baggage")
_META_PROTOCOL_VERSION_KEYS = ("protocolVersion", "io.modelcontextprotocol/protocolVersion")
_META_CLIENT_INFO_KEYS = ("clientInfo", "io.modelcontextprotocol/clientInfo")
_META_CAPABILITY_KEYS = (
    "capabilities",
    "clientCapabilities",
    "io.modelcontextprotocol/clientCapabilities",
)


def build_server_capabilities() -> dict[str, Any]:
    """Build the shared server capability object advertised by initialize/discover."""
    return {
        "tools": {"list": True, "call": True},
        "resources": {"list": True, "read": True},
        "prompts": {"list": True, "get": True},
        "extensions": {
            "io.modelcontextprotocol/ui": {
                "mimeTypes": [MCP_APPS_MIME],
            }
        },
    }


def build_server_discover_result() -> dict[str, Any]:
    """Return the MCP 2026-07-28 `server/discover` result shape."""
    return {
        "resultType": "complete",
        "supportedVersions": list(supported_protocol_versions()),
        "capabilities": build_server_capabilities(),
        "serverInfo": {"name": "mcp-geo", "version": SERVER_VERSION},
        "instructions": (
            "MCP Geo provides Ordnance Survey, ONS, NOMIS, Council Tax, AddressBase, "
            "LandIS, resource, and MCP-Apps map tooling. Stable clients should use "
            "2025-11-25; 2026-07-28 support is feature-gated for release-candidate "
            "interop testing."
        ),
    }


def request_meta_from_params(params: Mapping[str, Any] | None) -> dict[str, Any]:
    """Extract the protocol-level `_meta` fields this repo understands."""
    if not isinstance(params, Mapping):
        return {}
    raw_meta = params.get("_meta")
    if not isinstance(raw_meta, Mapping):
        return {}
    result: dict[str, Any] = {}
    protocol_version = normalize_protocol_version(
        _first_meta_value(raw_meta, _META_PROTOCOL_VERSION_KEYS)
    )
    if protocol_version:
        result["protocolVersion"] = protocol_version
    client_info = _first_meta_value(raw_meta, _META_CLIENT_INFO_KEYS)
    if isinstance(client_info, Mapping):
        result["clientInfo"] = dict(client_info)
    capabilities = _first_meta_value(raw_meta, _META_CAPABILITY_KEYS)
    if isinstance(capabilities, Mapping):
        result["capabilities"] = dict(capabilities)
    log_level = raw_meta.get("logLevel")
    if isinstance(log_level, str) and log_level.strip():
        result["logLevel"] = log_level.strip()
    trace_context = {
        key: raw_meta[key]
        for key in _TRACE_META_KEYS
        if isinstance(raw_meta.get(key), str) and raw_meta.get(key)
    }
    if trace_context:
        result["traceContext"] = trace_context
    return result


def _first_meta_value(raw_meta: Mapping[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in raw_meta:
            return raw_meta[key]
    return None


def update_state_from_request_meta(
    session_state: dict[str, Any],
    params: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Persist request `_meta` details for diagnostics and stateless RC routing."""
    meta = request_meta_from_params(params)
    if not meta:
        return {}
    session_state["lastRequestMeta"] = meta
    protocol_version = meta.get("protocolVersion")
    if isinstance(protocol_version, str):
        session_state["lastRequestProtocolVersion"] = protocol_version
    capabilities = meta.get("capabilities")
    if isinstance(capabilities, dict) and not session_state.get("capabilities"):
        session_state["capabilities"] = capabilities
    client_info = meta.get("clientInfo")
    if isinstance(client_info, dict):
        session_state["lastClientInfo"] = client_info
    trace_context = meta.get("traceContext")
    if isinstance(trace_context, dict):
        session_state["lastTraceContext"] = trace_context
    return meta


def requested_protocol_from_params(
    method: str | None,
    params: Mapping[str, Any] | None,
) -> str | None:
    """Resolve a protocol-version hint from request params or params `_meta`."""
    meta_version = request_meta_from_params(params).get("protocolVersion")
    if isinstance(meta_version, str):
        return meta_version
    if method == "initialize" and isinstance(params, Mapping):
        return normalize_protocol_version(params.get("protocolVersion"))
    return None


def wants_2026_rc_protocol(
    *,
    header_version: object,
    method: str | None,
    params: Mapping[str, Any] | None,
) -> bool:
    """Return True when the request explicitly opts into the RC protocol."""
    if not is_mcp_2026_rc_enabled():
        return False
    if is_mcp_2026_rc_protocol(header_version):
        return True
    return is_mcp_2026_rc_protocol(requested_protocol_from_params(method, params))


def add_cache_metadata(
    result: Any,
    *,
    method: str,
    protocol_version: str,
) -> Any:
    """Attach RC cache metadata to cacheable MCP result objects."""
    if not is_mcp_2026_rc_protocol(protocol_version):
        return result
    if not isinstance(result, dict):
        return result
    if method not in {
        "tools/list",
        "prompts/list",
        "resources/list",
        "resources/read",
        "resources/templates/list",
    }:
        return result
    decorated = dict(result)
    decorated.setdefault("resultType", "complete")
    if method == "resources/read":
        decorated.setdefault("ttlMs", DEFAULT_PRIVATE_TTL_MS)
        decorated.setdefault("cacheScope", "private")
    elif method == "resources/list":
        decorated.setdefault("ttlMs", DEFAULT_LIST_TTL_MS)
        decorated.setdefault("cacheScope", "private")
    else:
        decorated.setdefault("ttlMs", DEFAULT_LIST_TTL_MS)
        decorated.setdefault("cacheScope", "public")
    return decorated


def encode_request_state(payload: Mapping[str, Any]) -> str:
    body = json.dumps(dict(payload), ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return base64.urlsafe_b64encode(body.encode("utf-8")).rstrip(b"=").decode("ascii")


def build_input_required_result(
    *,
    key: str,
    method: str,
    params: Mapping[str, Any],
    request_state: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "resultType": "input_required",
        "inputRequests": {
            key: {
                "method": method,
                "params": dict(params),
            }
        },
    }
    if request_state:
        result["requestState"] = encode_request_state(request_state)
    return result


def input_response(params: Mapping[str, Any], key: str) -> dict[str, Any] | None:
    raw = params.get("inputResponses")
    if not isinstance(raw, Mapping):
        return None
    value = raw.get(key)
    return dict(value) if isinstance(value, Mapping) else None


def client_supports_elicitation_request(capabilities: Mapping[str, Any] | None) -> bool:
    if not isinstance(capabilities, Mapping):
        return False
    elicitation = capabilities.get("elicitation")
    return isinstance(elicitation, Mapping)


def validate_json_schema_2020_12_guardrails(
    schema: Mapping[str, Any],
    *,
    require_root_object: bool = False,
    max_depth: int = MAX_SCHEMA_DEPTH,
    max_nodes: int = MAX_SCHEMA_NODES,
) -> list[str]:
    """Validate schema guardrails needed before exposing schemas to RC clients."""
    issues: list[str] = []
    nodes = 0

    def _walk(value: Any, depth: int, path: str) -> None:
        nonlocal nodes
        nodes += 1
        if nodes > max_nodes:
            issues.append(f"{path}: schema exceeds {max_nodes} nodes")
            return
        if depth > max_depth:
            issues.append(f"{path}: schema exceeds depth {max_depth}")
            return
        if isinstance(value, Mapping):
            ref = value.get("$ref")
            if isinstance(ref, str) and not ref.startswith("#"):
                issues.append(f"{path}: external $ref is not allowed")
            for key, child in value.items():
                _walk(child, depth + 1, f"{path}.{key}")
        elif isinstance(value, list):
            for idx, child in enumerate(value):
                _walk(child, depth + 1, f"{path}[{idx}]")

    if require_root_object and schema.get("type") != "object":
        issues.append("$: inputSchema root type must be object")
    _walk(schema, 0, "$")
    return issues


def validate_registered_tool_schemas(
    *,
    ignore_tool_prefixes: tuple[str, ...] = (),
) -> list[str]:
    """Return guardrail issues across registered tool schemas."""
    issues: list[str] = []
    for tool in all_tools():
        if ignore_tool_prefixes and tool.name.startswith(ignore_tool_prefixes):
            continue
        if isinstance(tool.input_schema, Mapping):
            for issue in validate_json_schema_2020_12_guardrails(
                tool.input_schema,
                require_root_object=True,
            ):
                issues.append(f"{tool.name}.inputSchema: {issue}")
        if isinstance(tool.output_schema, Mapping):
            for issue in validate_json_schema_2020_12_guardrails(tool.output_schema):
                issues.append(f"{tool.name}.outputSchema: {issue}")
    if issues:
        logger.warning("MCP 2026 RC schema guardrail issues: {}", issues[:20])
    return issues
