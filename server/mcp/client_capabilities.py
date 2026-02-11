from __future__ import annotations

import os
from typing import Any, Callable, Dict, Optional

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
