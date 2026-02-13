from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any
from uuid import uuid4

from server.config import settings

_REPO_ROOT = Path(__file__).resolve().parents[1]
_OS_EXPORT_RESOURCE_PREFIX = "resource://mcp-geo/os-exports/"
_DELIVERY_MODES = {"inline", "resource", "auto"}


def _resolve_repo_path(raw: str) -> Path:
    path = Path(raw)
    if not path.is_absolute():
        path = _REPO_ROOT / raw
    return path


def os_cache_dir() -> Path:
    raw = str(getattr(settings, "OS_DATA_CACHE_DIR", "data/cache/os") or "data/cache/os")
    return _resolve_repo_path(raw)


def os_exports_dir() -> Path:
    return _resolve_repo_path("data/os_exports")


def parse_delivery(value: Any, default: str = "auto") -> tuple[str | None, str | None]:
    if value is None:
        return default, None
    if not isinstance(value, str):
        return None, "delivery must be one of inline, resource, auto"
    mode = value.strip().lower()
    if mode not in _DELIVERY_MODES:
        return None, "delivery must be one of inline, resource, auto"
    return mode, None


def parse_inline_max_bytes(value: Any) -> tuple[int | None, str | None]:
    if value is None:
        return int(getattr(settings, "OS_EXPORT_INLINE_MAX_BYTES", 200_000)), None
    if not isinstance(value, int) or value < 1:
        return None, "inlineMaxBytes must be a positive integer"
    return value, None


def select_delivery_mode(
    *,
    requested_delivery: str,
    payload_bytes: int,
    inline_max_bytes: int,
) -> str:
    if requested_delivery == "resource":
        return "resource"
    if requested_delivery == "inline":
        return "inline"
    return "resource" if payload_bytes > inline_max_bytes else "inline"


def payload_bytes(value: Any) -> int:
    serialized = json.dumps(value, ensure_ascii=True, separators=(",", ":"))
    return len(serialized.encode("utf-8"))


def write_resource_payload(
    *,
    prefix: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    out_dir = os_exports_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{prefix}-{int(time.time() * 1000)}-{uuid4().hex[:8]}.json"
    path = out_dir / filename
    serialized = json.dumps(payload, ensure_ascii=True, separators=(",", ":"))
    path.write_text(serialized, encoding="utf-8")
    digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    return {
        "path": str(path),
        "resourceUri": f"{_OS_EXPORT_RESOURCE_PREFIX}{filename}",
        "bytes": len(serialized.encode("utf-8")),
        "sha256": digest,
    }


def now_utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

