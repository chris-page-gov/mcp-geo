"""Protocol version constants and negotiation helpers for MCP transports."""

from __future__ import annotations

import os
from typing import Final

# Ordered from newest to oldest for fallback negotiation.
SUPPORTED_PROTOCOL_VERSIONS: Final[tuple[str, ...]] = (
    "2025-11-25",
    "2025-06-18",
    "2025-03-26",
    "2024-11-05",
)

# MCP core protocol version this server prefers by default.
PROTOCOL_VERSION: Final[str] = SUPPORTED_PROTOCOL_VERSIONS[0]

# Streamable HTTP compatibility fallback when no explicit version is known.
HTTP_DEFAULT_PROTOCOL_VERSION: Final[str] = "2025-03-26"

# MCP Apps extension protocol (UI host <-> app iframe), tracked separately.
MCP_APPS_PROTOCOL_VERSION: Final[str] = "2026-01-26"

# MCP 2026-07-28 release-candidate protocol. This stays opt-in until the
# release candidate becomes the stable protocol target for the repo.
MCP_2026_RC_PROTOCOL_VERSION: Final[str] = "2026-07-28"

_TRUE_ENV_VALUES: Final[set[str]] = {"1", "true", "yes", "on"}


def is_mcp_2026_rc_enabled() -> bool:
    """Return True when the future 2026-07-28 protocol mode is explicitly enabled."""
    for name in ("MCP_2026_RC_ENABLED", "MCP_PROTOCOL_2026_07_28_ENABLED"):
        raw = os.getenv(name)
        if isinstance(raw, str) and raw.strip().lower() in _TRUE_ENV_VALUES:
            return True
    return False


def supported_protocol_versions() -> tuple[str, ...]:
    """Return the runtime-supported protocol versions for the current feature flags."""
    if is_mcp_2026_rc_enabled():
        return (MCP_2026_RC_PROTOCOL_VERSION, *SUPPORTED_PROTOCOL_VERSIONS)
    return SUPPORTED_PROTOCOL_VERSIONS


def is_mcp_2026_rc_protocol(value: object) -> bool:
    """Return True when value is the feature-gated 2026-07-28 protocol string."""
    return normalize_protocol_version(value) == MCP_2026_RC_PROTOCOL_VERSION


def is_supported_protocol_version(value: object) -> bool:
    """Return True when value is a supported MCP core protocol version string."""
    if not isinstance(value, str):
        return False
    return value.strip() in supported_protocol_versions()


def normalize_protocol_version(value: object) -> str | None:
    """Normalize a protocol version value; returns None for empty/non-string input."""
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def negotiate_protocol_version(requested: object) -> str:
    """Negotiate MCP protocol version for initialize responses.

    If requested is supported, return it. Otherwise return the server's newest supported version.
    """
    normalized = normalize_protocol_version(requested)
    if normalized and normalized in supported_protocol_versions():
        return normalized
    return PROTOCOL_VERSION
