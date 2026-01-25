from __future__ import annotations

import sys
from typing import Iterable

from loguru import logger

from server.config import settings
from server.security import mask_in_text, mask_in_value


def _build_redactions() -> list[str]:
    secrets: list[str] = []
    if settings.OS_API_KEY:
        secrets.append(settings.OS_API_KEY)
    return secrets


def configure_logging() -> None:
    redactions = _build_redactions()

    def _patch(record: dict) -> dict:
        record["message"] = mask_in_text(record["message"], redactions)
        record["extra"] = mask_in_value(record.get("extra", {}), redactions)
        return record

    logger.remove()
    logger.configure(patcher=_patch)
    logger.add(sys.stdout, serialize=settings.LOG_JSON)


def log_upstream_error(
    *,
    service: str,
    code: str,
    url: str | None = None,
    status_code: int | None = None,
    params: dict | None = None,
    detail: str | None = None,
    attempt: int | None = None,
    error_category: str | None = None,
) -> None:
    payload = {
        "service": service,
        "code": code,
        "error_category": error_category,
        "status_code": status_code,
        "url": url,
        "params": params,
        "detail": detail,
        "attempt": attempt,
    }
    logger.bind(**{k: v for k, v in payload.items() if v is not None}).warning(
        "Upstream error"
    )
