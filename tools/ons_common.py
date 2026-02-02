from __future__ import annotations

import json
import random
import threading
import time
from typing import Any, Dict, Tuple
from urllib.parse import urljoin

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
from server.error_taxonomy import classify_error
from server.logging import log_upstream_error
from server.circuit_breaker import get_circuit_breaker

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
        self._lock = threading.Lock()

    def get(self, key: str) -> Any | None:
        with self._lock:
            entry = self._store.get(key)
            if not entry:
                return None
            if not entry.valid():
                del self._store[key]
                return None
            return entry.value

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            if len(self._store) >= self.maxsize:
                # naive eviction: remove first expired or oldest
                for k, v in list(self._store.items()):
                    if not v.valid():
                        del self._store[k]
                        break
                else:
                    # pop arbitrary oldest
                    self._store.pop(next(iter(self._store)))
            self._store[key] = _CacheEntry(value, self.ttl)


class ONSClient:
    base_api = getattr(settings, "ONS_DATASET_API_BASE", "") or "https://api.beta.ons.gov.uk/v1"

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
        self._breaker = get_circuit_breaker("ons")

    def _cache_key(self, url: str, params: dict[str, Any] | None) -> str:
        return json.dumps([url, params], sort_keys=True)

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
                "message": "ONS upstream circuit breaker is open.",
            }
        merged = params or {}
        last_exc: Exception | None = None
        for attempt in range(1, self.retries + 1):
            try:
                resp = requests.get(url, params=merged, timeout=DEFAULT_TIMEOUT)
                if resp.status_code != 200:
                    if resp.status_code >= 500:
                        self._breaker.record_failure()
                    resp_url = getattr(resp, "url", url)
                    log_upstream_error(
                        service="ons",
                        code="ONS_API_ERROR",
                        status_code=resp.status_code,
                        url=resp_url,
                        params=merged,
                        detail=resp.text[:200],
                        attempt=attempt,
                        error_category=classify_error("ONS_API_ERROR"),
                    )
                    return resp.status_code, {
                        "isError": True,
                        "code": "ONS_API_ERROR",
                        "message": f"ONS API error: {resp.text[:200]}",
                    }
                data = resp.json()
                if use_cache:
                    self.cache.set(key, data)
                self._breaker.record_success()
                return 200, data
            except req_exc.SSLError as exc:
                self._breaker.record_failure()
                log_upstream_error(
                    service="ons",
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
                        service="ons",
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
                    service="ons",
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

    def build_paged_params(
        self, limit: int, page: int, extra: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        # ONS APIs often expose pagination using limit/offset or page parameters.
        # We simulate limit/page for consistent usage in tests.
        params = {"limit": limit, "page": page}
        if extra:
            params.update(extra)
        return params

    def get_all_pages(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        item_key: str = "items",
    ) -> Tuple[int, list[dict[str, Any]] | dict[str, Any]]:
        results: list[dict[str, Any]] = []
        merged = dict(params or {})
        page = int(merged.get("page", 1))
        limit = int(merged.get("limit", 1000))
        while True:
            status, data = self.get_json(url, params=merged, use_cache=False)
            if status != 200:
                return status, data
            items = data.get(item_key, [])
            if not isinstance(items, list):
                return 500, {
                    "isError": True,
                    "code": "INTEGRATION_ERROR",
                    "message": f"Expected list at '{item_key}'",
                }
            results.extend([item for item in items if isinstance(item, dict)])
            next_url = None
            links = data.get("links", [])
            if isinstance(links, list):
                for link in links:
                    if isinstance(link, dict) and link.get("rel") == "next":
                        href = link.get("href")
                        if isinstance(href, str) and href:
                            next_url = urljoin(url, href)
                        break
            total = data.get("total") or data.get("count")
            if next_url:
                url = next_url
                merged = {}
                continue
            if total is None and not links:
                break
            if isinstance(total, int):
                if page * limit >= total:
                    break
            if len(items) < limit:
                break
            page += 1
            merged["page"] = page
            merged["limit"] = limit
        return 200, results


def _sleep_with_jitter(attempt: int, base: float, cap: float) -> None:
    delay = min(base * (2 ** (attempt - 1)), cap)
    jitter = random.uniform(0, delay * 0.25)
    time.sleep(delay + jitter)


client = ONSClient()
