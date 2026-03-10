from __future__ import annotations

from pathlib import Path
from typing import Any

from server.audit.redaction import (
    VALID_DISCLOSURE_PROFILES,
    build_redacted_pack,
    normalize_disclosure_profile,
)

__all__ = [
    "VALID_DISCLOSURE_PROFILES",
    "build_redacted_pack",
    "normalize_disclosure_profile",
]


def describe_disclosure_profile(profile: str) -> dict[str, Any]:
    resolved = normalize_disclosure_profile(profile)
    descriptions = {
        "internal_full": "Full internal disclosure with retained evidence references preserved.",
        "internal_restricted": "Internal disclosure with sensitive fields summarized or withheld.",
        "foi_redacted": "FOI-style derivative disclosure with protected content redacted.",
    }
    return {"name": resolved, "description": descriptions[resolved]}


def redact_pack(pack_dir: Path, *, disclosure_profile: str) -> dict[str, Any]:
    return build_redacted_pack(pack_dir, disclosure_profile=disclosure_profile)
