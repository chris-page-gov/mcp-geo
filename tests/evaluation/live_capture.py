from __future__ import annotations

import contextlib
import contextvars
import hashlib
import json
import time
from dataclasses import dataclass
from typing import Any, Callable
from urllib.parse import urlparse

import psycopg
from psycopg.types.json import Json

_CAPTURE_CONTEXT: contextvars.ContextVar["CaptureContext | None"] = contextvars.ContextVar(
    "live_capture_context",
    default=None,
)
_CAPTURE_ENABLED: contextvars.ContextVar[bool] = contextvars.ContextVar(
    "live_capture_enabled",
    default=False,
)
_ATTEMPT_COUNTER: contextvars.ContextVar[int] = contextvars.ContextVar(
    "live_capture_attempts",
    default=0,
)

_SENSITIVE_KEYS = {
    "authorization",
    "api_key",
    "apikey",
    "key",
    "token",
    "bearer",
    "password",
    "secret",
}


@dataclass(frozen=True)
class CaptureContext:
    run_id: str
    correlation_id: str
    question_id: str
    tool_name: str


def _scrub_mapping(value: dict[str, Any] | None) -> dict[str, Any]:
    if not value:
        return {}
    scrubbed: dict[str, Any] = {}
    for key, val in value.items():
        key_lower = str(key).lower()
        if (
            key_lower in _SENSITIVE_KEYS
            or key_lower.endswith("_key")
            or key_lower.endswith("_token")
        ):
            scrubbed[key] = "***"
        else:
            scrubbed[key] = val
    return scrubbed


def _coerce_payload(payload: Any) -> Any:
    if isinstance(payload, (dict, list, str, int, float, bool)) or payload is None:
        return payload
    return {"_raw": str(payload)}


def _hash_payload(payload: Any) -> str:
    try:
        raw = json.dumps(payload, sort_keys=True, ensure_ascii=True, default=str)
    except TypeError:
        raw = json.dumps({"_raw": str(payload)}, ensure_ascii=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _guess_endpoint(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if "api.os.uk" in host:
        return "os"
    if "api.ons.gov.uk" in host or "api.beta.ons.gov.uk" in host:
        return "ons"
    if "arcgis.com" in host:
        return "arcgis"
    return "unknown"


class LiveApiRecorder:
    def __init__(self, dsn: str):
        self._conn = psycopg.connect(dsn, autocommit=True)

    def close(self) -> None:
        self._conn.close()

    def ensure_schema(self) -> None:
        with self._conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS api_call_log (
                    id BIGSERIAL PRIMARY KEY,
                    run_id TEXT,
                    correlation_id TEXT,
                    question_id TEXT,
                    tool_name TEXT,
                    endpoint TEXT,
                    url TEXT,
                    params JSONB,
                    headers JSONB,
                    status INTEGER,
                    latency_ms DOUBLE PRECISION,
                    retry_count INTEGER,
                    retrieved_at TIMESTAMPTZ DEFAULT NOW()
                );
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS api_raw (
                    id BIGSERIAL PRIMARY KEY,
                    api_call_id BIGINT REFERENCES api_call_log(id) ON DELETE CASCADE,
                    run_id TEXT,
                    endpoint TEXT,
                    url TEXT,
                    params JSONB,
                    payload JSONB,
                    content_hash TEXT,
                    retrieved_at TIMESTAMPTZ DEFAULT NOW()
                );
                """
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS api_call_log_run_id_idx ON api_call_log(run_id);"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS api_raw_content_hash_idx ON api_raw(content_hash);"
            )

    def record_call(
        self,
        *,
        context: CaptureContext,
        endpoint: str,
        url: str,
        params: dict[str, Any],
        headers: dict[str, Any],
        status: int,
        latency_ms: float,
        retry_count: int,
    ) -> int:
        with self._conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO api_call_log (
                    run_id,
                    correlation_id,
                    question_id,
                    tool_name,
                    endpoint,
                    url,
                    params,
                    headers,
                    status,
                    latency_ms,
                    retry_count
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id;
                """,
                (
                    context.run_id,
                    context.correlation_id,
                    context.question_id,
                    context.tool_name,
                    endpoint,
                    url,
                    Json(params),
                    Json(headers),
                    status,
                    latency_ms,
                    retry_count,
                ),
            )
            row = cur.fetchone()
        return int(row[0]) if row else 0

    def record_raw(
        self,
        *,
        context: CaptureContext,
        call_id: int,
        endpoint: str,
        url: str,
        params: dict[str, Any],
        payload: Any,
    ) -> None:
        payload_obj = _coerce_payload(payload)
        content_hash = _hash_payload(payload_obj)
        with self._conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO api_raw (
                    api_call_id,
                    run_id,
                    endpoint,
                    url,
                    params,
                    payload,
                    content_hash
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s);
                """,
                (
                    call_id,
                    context.run_id,
                    endpoint,
                    url,
                    Json(params),
                    Json(payload_obj),
                    content_hash,
                ),
            )

    def record_response(
        self,
        *,
        context: CaptureContext,
        endpoint: str,
        url: str,
        params: dict[str, Any],
        headers: dict[str, Any],
        status: int,
        latency_ms: float,
        retry_count: int,
        payload: Any,
    ) -> None:
        call_id = self.record_call(
            context=context,
            endpoint=endpoint,
            url=url,
            params=params,
            headers=headers,
            status=status,
            latency_ms=latency_ms,
            retry_count=retry_count,
        )
        if call_id:
            self.record_raw(
                context=context,
                call_id=call_id,
                endpoint=endpoint,
                url=url,
                params=params,
                payload=payload,
            )

    def count_calls(self, run_id: str) -> int:
        with self._conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM api_call_log WHERE run_id = %s;",
                (run_id,),
            )
            row = cur.fetchone()
        return int(row[0]) if row else 0


class LiveApiCapture:
    def __init__(self, recorder: LiveApiRecorder, *, run_id: str):
        self._recorder = recorder
        self.run_id = run_id

    @contextlib.contextmanager
    def context(
        self,
        *,
        question_id: str,
        tool_name: str,
        correlation_id: str,
    ):
        ctx = CaptureContext(
            run_id=self.run_id,
            correlation_id=correlation_id,
            question_id=question_id,
            tool_name=tool_name,
        )
        token = _CAPTURE_CONTEXT.set(ctx)
        try:
            yield
        finally:
            _CAPTURE_CONTEXT.reset(token)

    def install(self, monkeypatch) -> None:
        import requests
        from tools import admin_lookup, ons_common, ons_search, os_common

        original_requests_get = requests.get

        def wrapped_requests_get(*args: Any, **kwargs: Any):
            if _CAPTURE_ENABLED.get():
                _ATTEMPT_COUNTER.set(_ATTEMPT_COUNTER.get() + 1)
            return original_requests_get(*args, **kwargs)

        monkeypatch.setattr(requests, "get", wrapped_requests_get)

        def wrap_get_json(
            original: Callable[..., Any],
            *,
            force_no_cache: bool = False,
        ) -> Callable[..., Any]:
            def _wrapped(url: str, params: dict[str, Any] | None = None, **kwargs: Any):
                context = _CAPTURE_CONTEXT.get()
                if context is None:
                    return original(url, params=params, **kwargs)

                start = time.time()
                token_enabled = _CAPTURE_ENABLED.set(True)
                token_attempts = _ATTEMPT_COUNTER.set(0)
                if force_no_cache:
                    code_obj = getattr(original, "__code__", None)
                    if code_obj and "use_cache" in code_obj.co_varnames:
                        kwargs["use_cache"] = False
                status, payload = original(url, params=params, **kwargs)
                latency_ms = (time.time() - start) * 1000
                attempts = _ATTEMPT_COUNTER.get()
                _ATTEMPT_COUNTER.reset(token_attempts)
                _CAPTURE_ENABLED.reset(token_enabled)

                retry_count = max(attempts - 1, 0)
                endpoint = _guess_endpoint(url)
                safe_params = _scrub_mapping(params or {})
                safe_headers = _scrub_mapping(kwargs.get("headers"))
                self._recorder.record_response(
                    context=context,
                    endpoint=endpoint,
                    url=url,
                    params=safe_params,
                    headers=safe_headers,
                    status=status,
                    latency_ms=latency_ms,
                    retry_count=retry_count,
                    payload=payload,
                )
                return status, payload

            return _wrapped

        monkeypatch.setattr(
            os_common.client,
            "get_json",
            wrap_get_json(os_common.client.get_json),
        )
        monkeypatch.setattr(
            ons_common.client,
            "get_json",
            wrap_get_json(ons_common.client.get_json, force_no_cache=True),
        )
        monkeypatch.setattr(
            ons_search._SEARCH_CLIENT,
            "get_json",
            wrap_get_json(ons_search._SEARCH_CLIENT.get_json, force_no_cache=True),
        )
        monkeypatch.setattr(
            admin_lookup._ARCGIS_CLIENT,
            "get_json",
            wrap_get_json(admin_lookup._ARCGIS_CLIENT.get_json),
        )
