from __future__ import annotations

import json
import threading
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
    base_api = "https://api.ons.gov.uk"

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
        merged = params or {}
        last_exc: Exception | None = None
        for attempt in range(1, self.retries + 1):
            try:
                resp = requests.get(url, params=merged, timeout=DEFAULT_TIMEOUT)
                if resp.status_code != 200:
                    return resp.status_code, {
                        "isError": True,
                        "code": "ONS_API_ERROR",
                        "message": f"ONS API error: {resp.text[:200]}",
                    }
                data = resp.json()
                if use_cache:
                    self.cache.set(key, data)
                return 200, data
            except req_exc.SSLError as exc:
                return 501, {
                    "isError": True,
                    "code": "UPSTREAM_TLS_ERROR",
                    "message": str(exc),
                }
            except (req_exc.ConnectionError, req_exc.Timeout) as exc:
                last_exc = exc
                if attempt == self.retries:
                    return 501, {
                        "isError": True,
                        "code": "UPSTREAM_CONNECT_ERROR",
                        "message": str(exc),
                    }
                time.sleep(min(0.1 * (2 ** (attempt - 1)), 1.0))
            except Exception as exc:  # pragma: no cover
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


client = ONSClient()
