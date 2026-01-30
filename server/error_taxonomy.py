from __future__ import annotations

from typing import Dict

ERROR_TAXONOMY: Dict[str, str] = {
    "INVALID_INPUT": "input",
    "NO_API_KEY": "auth",
    "OS_API_KEY_INVALID": "auth",
    "OS_API_KEY_EXPIRED": "auth",
    "MISSING_DEPENDENCY": "dependency",
    "LIVE_DISABLED": "config",
    "NOT_ENABLED": "config",
    "RATE_LIMITED": "rate_limit",
    "UNKNOWN_TOOL": "not_found",
    "UNKNOWN_FILTER": "not_found",
    "NO_OBSERVATION": "not_found",
    "NOT_FOUND": "not_found",
    "OS_API_ERROR": "upstream",
    "ONS_API_ERROR": "upstream",
    "ADMIN_LOOKUP_API_ERROR": "upstream",
    "BOUNDARY_CACHE_ERROR": "dependency",
    "UPSTREAM_TLS_ERROR": "upstream",
    "UPSTREAM_CONNECT_ERROR": "upstream",
    "INTEGRATION_ERROR": "integration",
    "INTERNAL_ERROR": "internal",
}


def classify_error(code: str | None) -> str:
    if not code:
        return "unknown"
    return ERROR_TAXONOMY.get(code, "unknown")
