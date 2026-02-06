from __future__ import annotations

import json
import random
import time
from typing import Any, Dict, Tuple

try:
    import requests
    from requests import exceptions as req_exc
except ImportError:  # pragma: no cover - optional dependency fallback
    requests = None  # type: ignore[assignment]

    class _ReqExc:
        SSLError = Exception
        ConnectionError = Exception
        Timeout = Exception

    req_exc = _ReqExc()

from server.config import settings
from server.circuit_breaker import get_circuit_breaker
from server.error_taxonomy import classify_error
from server.logging import log_upstream_error

DEFAULT_TIMEOUT = 5
DEFAULT_RETRIES = 3


class _CacheEntry:
    __slots__ = ("value", "expires_at")

    def __init__(self, value: Any, ttl: float) -> None:
        self.value = value
        self.expires_at = time.time() + ttl

    def valid(self) -> bool:
        return time.time() < self.expires_at


class TTLCache:
    def __init__(self, maxsize: int = 256, ttl: float = 60.0) -> None:
        self.maxsize = maxsize
        self.ttl = ttl
        self._store: Dict[str, _CacheEntry] = {}

    def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if not entry:
            return None
        if not entry.valid():
            del self._store[key]
            return None
        return entry.value

    def set(self, key: str, value: Any) -> None:
        if len(self._store) >= self.maxsize:
            for k, v in list(self._store.items()):
                if not v.valid():
                    del self._store[k]
                    break
            else:
                self._store.pop(next(iter(self._store)))
        self._store[key] = _CacheEntry(value, self.ttl)


class NomisClient:
    base_api = getattr(settings, "NOMIS_API_BASE", "") or "https://www.nomisweb.co.uk/api/v01"

    def __init__(
        self,
        retries: int = DEFAULT_RETRIES,
        cache_ttl: float | None = None,
        cache_size: int | None = None,
    ):
        self.retries = retries
        ttl = cache_ttl if cache_ttl is not None else getattr(settings, "ONS_CACHE_TTL", 60.0)
        size = cache_size if cache_size is not None else getattr(settings, "ONS_CACHE_SIZE", 256)
        self.cache = TTLCache(maxsize=size, ttl=ttl)
        self._breaker = get_circuit_breaker("nomis")

    def _cache_key(self, url: str, params: dict[str, Any] | None) -> str:
        return json.dumps([url, params], sort_keys=True)

    def _with_auth(self, params: dict[str, Any] | None) -> dict[str, Any]:
        merged = dict(params or {})
        uid = getattr(settings, "NOMIS_UID", "")
        signature = getattr(settings, "NOMIS_SIGNATURE", "")
        if uid and "uid" not in merged:
            merged["uid"] = uid
        if signature and "signature" not in merged:
            merged["signature"] = signature
        return merged

    def get_json(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        use_cache: bool = True,
    ) -> Tuple[int, dict[str, Any]]:
        if requests is None:
            return 501, {
                "isError": True,
                "code": "MISSING_DEPENDENCY",
                "message": "requests is not installed",
            }
        key = self._cache_key(url, params)
        if use_cache:
            cached = self.cache.get(key)
            if cached is not None:
                return 200, cached
        if not self._breaker.allow():
            return 503, {
                "isError": True,
                "code": "CIRCUIT_OPEN",
                "message": "NOMIS upstream circuit breaker is open.",
            }
        merged = self._with_auth(params)
        last_exc: Exception | None = None
        for attempt in range(1, self.retries + 1):
            try:
                resp = requests.get(url, params=merged, timeout=DEFAULT_TIMEOUT)
                if resp.status_code != 200:
                    if resp.status_code >= 500:
                        self._breaker.record_failure()
                    resp_url = getattr(resp, "url", url)
                    log_upstream_error(
                        service="nomis",
                        code="NOMIS_API_ERROR",
                        status_code=resp.status_code,
                        url=resp_url,
                        params=merged,
                        detail=resp.text[:200],
                        attempt=attempt,
                        error_category=classify_error("NOMIS_API_ERROR"),
                    )
                    return resp.status_code, {
                        "isError": True,
                        "code": "NOMIS_API_ERROR",
                        "message": f"NOMIS API error: {resp.text[:200]}",
                    }
                try:
                    data = resp.json()
                except Exception as exc:
                    self._breaker.record_failure()
                    log_upstream_error(
                        service="nomis",
                        code="UPSTREAM_INVALID_RESPONSE",
                        status_code=resp.status_code,
                        url=url,
                        params=merged,
                        detail=f"{exc}: {resp.text[:200]}",
                        attempt=attempt,
                        error_category=classify_error("UPSTREAM_INVALID_RESPONSE"),
                    )
                    return 502, {
                        "isError": True,
                        "code": "UPSTREAM_INVALID_RESPONSE",
                        "message": "NOMIS API returned invalid JSON.",
                    }
                if use_cache:
                    self.cache.set(key, data)
                self._breaker.record_success()
                return 200, data
            except req_exc.SSLError as exc:
                self._breaker.record_failure()
                log_upstream_error(
                    service="nomis",
                    code="UPSTREAM_TLS_ERROR",
                    url=url,
                    params=merged,
                    detail=str(exc),
                    attempt=attempt,
                    error_category=classify_error("UPSTREAM_TLS_ERROR"),
                )
                return 501, {
                    "isError": True,
                    "code": "UPSTREAM_TLS_ERROR",
                    "message": str(exc),
                }
            except (req_exc.ConnectionError, req_exc.Timeout) as exc:
                last_exc = exc
                self._breaker.record_failure()
                if attempt == self.retries:
                    log_upstream_error(
                        service="nomis",
                        code="UPSTREAM_CONNECT_ERROR",
                        url=url,
                        params=merged,
                        detail=str(exc),
                        attempt=attempt,
                        error_category=classify_error("UPSTREAM_CONNECT_ERROR"),
                    )
                    return 501, {
                        "isError": True,
                        "code": "UPSTREAM_CONNECT_ERROR",
                        "message": str(exc),
                    }
                _sleep_with_jitter(attempt, base=0.1, cap=1.0)
            except Exception as exc:  # pragma: no cover
                self._breaker.record_failure()
                log_upstream_error(
                    service="nomis",
                    code="INTEGRATION_ERROR",
                    url=url,
                    params=merged,
                    detail=str(exc),
                    attempt=attempt,
                    error_category=classify_error("INTEGRATION_ERROR"),
                )
                return 500, {
                    "isError": True,
                    "code": "INTEGRATION_ERROR",
                    "message": str(exc),
                }
        return 501, {
            "isError": True,
            "code": "UPSTREAM_CONNECT_ERROR",
            "message": f"Failed after retries: {last_exc}",
        }


def _sleep_with_jitter(attempt: int, base: float, cap: float) -> None:
    sleep = min(base * (2 ** (attempt - 1)), cap)
    sleep += random.uniform(0, sleep / 4)
    time.sleep(sleep)


client = NomisClient()
