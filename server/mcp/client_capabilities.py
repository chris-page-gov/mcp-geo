from __future__ import annotations

import os
from typing import Any, Callable, Dict, Optional

from server.protocol import SUPPORTED_PROTOCOL_VERSIONS, normalize_protocol_version

from server.mcp.resource_catalog import MCP_APPS_MIME


def read_bool_env(name: str) -> Optional[bool]:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return None
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def bool_env(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def client_supports_ui(
    capabilities: Dict[str, Any],
    *,
    override_env: str | None = None,
) -> bool:
    if override_env:
        override = read_bool_env(override_env)
        if override is not None:
            return override
    extensions = capabilities.get("extensions", {}) if isinstance(capabilities, dict) else {}
    ui_ext = extensions.get("io.modelcontextprotocol/ui")
    if isinstance(ui_ext, dict):
        mime_types = ui_ext.get("mimeTypes")
        if isinstance(mime_types, list):
            return MCP_APPS_MIME in mime_types
    return False


def client_supports_elicitation_form(capabilities: Dict[str, Any]) -> bool:
    """Return True when client capabilities advertise elicitation form support."""
    if not isinstance(capabilities, dict):
        return False
    elicitation = capabilities.get("elicitation")
    if elicitation is None:
        return False
    if not isinstance(elicitation, dict):
        return False
    if not elicitation:
        return True
    return isinstance(elicitation.get("form"), dict)


def summarize_client_capabilities(
    *,
    capabilities: Dict[str, Any],
    requested_protocol_version: object,
    negotiated_protocol_version: object,
) -> Dict[str, Any]:
    """Build a compact initialize-time capability summary for audit logs."""
    requested = normalize_protocol_version(requested_protocol_version)
    negotiated = normalize_protocol_version(negotiated_protocol_version)
    top_level_keys = sorted(key for key in capabilities.keys() if isinstance(key, str))
    requested_supported: bool | None
    if requested is None:
        requested_supported = None
    else:
        requested_supported = requested in SUPPORTED_PROTOCOL_VERSIONS
    return {
        "requestedProtocolVersion": requested,
        "negotiatedProtocolVersion": negotiated,
        "requestedProtocolSupportedByServer": requested_supported,
        "capabilityKeys": top_level_keys,
        "supports": {
            "tools": isinstance(capabilities.get("tools"), dict),
            "resources": isinstance(capabilities.get("resources"), dict),
            "prompts": isinstance(capabilities.get("prompts"), dict),
            "elicitationForm": client_supports_elicitation_form(capabilities),
            "mcpAppsUi": client_supports_ui(capabilities),
            "sampling": isinstance(capabilities.get("sampling"), dict),
            "roots": isinstance(capabilities.get("roots"), dict),
        },
    }


def ui_fallback_for_tool(
    tool_name: str,
    payload: Dict[str, Any],
    data: Any,
    *,
    ui_supported: bool,
    build_static_map_fallback: Callable[[Dict[str, Any], Any], Optional[Dict[str, Any]]],
    build_stats_dashboard_fallback: Callable[[Dict[str, Any]], Optional[Dict[str, Any]]],
) -> Optional[Dict[str, Any]]:
    if ui_supported or not tool_name.startswith("os_apps.render_"):
        return None
    if tool_name == "os_apps.render_statistics_dashboard":
        return build_stats_dashboard_fallback(payload)
    return build_static_map_fallback(payload, data)
