"""Protocol version constants and negotiation helpers for MCP transports."""

from __future__ import annotations

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


def is_supported_protocol_version(value: object) -> bool:
    """Return True when value is a supported MCP core protocol version string."""
    if not isinstance(value, str):
        return False
    return value.strip() in SUPPORTED_PROTOCOL_VERSIONS


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
    if normalized and normalized in SUPPORTED_PROTOCOL_VERSIONS:
        return normalized
    return PROTOCOL_VERSION

