from __future__ import annotations

import time
from typing import Any

try:
    import requests
    from requests import exceptions as req_exc
except ImportError:  # pragma: no cover - optional dependency fallback
    requests = None  # type: ignore[assignment]

    class _ReqExc:  # minimal shim for exception names used below
        SSLError = Exception
        ConnectionError = Exception
        Timeout = Exception

    req_exc = _ReqExc()

from server.config import settings
from server.error_taxonomy import classify_error
from server.logging import log_upstream_error

DEFAULT_TIMEOUT = 5
DEFAULT_RETRIES = 3

_AUTH_MISSING_TOKENS = (
    "missing",
    "not provided",
    "no api key",
    "apikey required",
    "api key required",
    "key required",
    "provide an api key",
)
_AUTH_EXPIRED_TOKENS = ("expired", "expiry")
_AUTH_INVALID_TOKENS = (
    "invalid",
    "unauthorized",
    "not authorized",
    "not authorised",
    "forbidden",
    "access denied",
    "not enabled",
    "disallowed",
)


def classify_os_api_key_error(status_code: int, body: str | None) -> tuple[str, str] | None:
    if status_code not in (401, 403):
        return None
    text = (body or "").lower()
    if any(token in text for token in _AUTH_EXPIRED_TOKENS):
        return "OS_API_KEY_EXPIRED", "OS API key expired."
    if any(token in text for token in _AUTH_MISSING_TOKENS):
        return "NO_API_KEY", "OS API key missing."
    if any(token in text for token in _AUTH_INVALID_TOKENS):
        return "OS_API_KEY_INVALID", "OS API key invalid or not authorized."
    return "OS_API_KEY_INVALID", "OS API key invalid or not authorized."


class OSClient:
    base_places = "https://api.os.uk/search/places/v1"
    base_names = "https://api.os.uk/search/names/v1"
    base_features = "https://api.os.uk/features/v1"
    base_maps = "https://api.os.uk/maps/v1"
    base_vector_tiles = "https://api.os.uk/maps/vector/v1"

    def __init__(self, api_key: str | None = None, retries: int = DEFAULT_RETRIES):
        self.api_key = api_key or getattr(settings, "OS_API_KEY", "")
        self.retries = retries

    def _auth_params(self) -> dict[str, Any]:
        if not self.api_key:
            return {}
        return {"key": self.api_key}

    def get_json(
        self, url: str, params: dict[str, Any] | None = None
    ) -> tuple[int, dict[str, Any]]:
        if not self.api_key:
            return 501, {
                "isError": True,
                "code": "NO_API_KEY",
                "message": "OS API key missing.",
            }
        if requests is None:
            return 501, {
                "isError": True,
                "code": "MISSING_DEPENDENCY",
                "message": "requests is not installed",
            }
        merged = {**(params or {}), **self._auth_params()}
        last_exc: Exception | None = None
        for attempt in range(1, self.retries + 1):
            try:
                resp = requests.get(url, params=merged, timeout=DEFAULT_TIMEOUT)
                if resp.status_code != 200:
                    auth_error = classify_os_api_key_error(resp.status_code, resp.text)
                    if auth_error:
                        code, message = auth_error
                        log_upstream_error(
                            service="os",
                            code=code,
                            status_code=resp.status_code,
                            url=getattr(resp, "url", url),
                            params=merged,
                            detail=resp.text[:200],
                            attempt=attempt,
                            error_category=classify_error(code),
                        )
                        return (
                            resp.status_code,
                            {
                                "isError": True,
                                "code": code,
                                "message": message,
                            },
                        )
                    resp_url = getattr(resp, "url", url)
                    log_upstream_error(
                        service="os",
                        code="OS_API_ERROR",
                        status_code=resp.status_code,
                        url=resp_url,
                        params=merged,
                        detail=resp.text[:200],
                        attempt=attempt,
                        error_category=classify_error("OS_API_ERROR"),
                    )
                    return (
                        resp.status_code,
                        {
                            "isError": True,
                            "code": "OS_API_ERROR",
                            "message": f"OS API error: {resp.text[:200]}",
                        },
                    )
                return 200, resp.json()
            except req_exc.SSLError as exc:
                log_upstream_error(
                    service="os",
                    code="UPSTREAM_TLS_ERROR",
                    url=url,
                    params=merged,
                    detail=str(exc),
                    attempt=attempt,
                    error_category=classify_error("UPSTREAM_TLS_ERROR"),
                )
                return 501, {"isError": True, "code": "UPSTREAM_TLS_ERROR", "message": str(exc)}
            except (req_exc.ConnectionError, req_exc.Timeout) as exc:
                last_exc = exc
                if attempt == self.retries:
                    log_upstream_error(
                        service="os",
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
                time.sleep(min(0.1 * (2 ** (attempt - 1)), 1.0))
            except Exception as exc:  # pragma: no cover
                log_upstream_error(
                    service="os",
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

client = OSClient()
