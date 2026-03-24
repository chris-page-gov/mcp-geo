from __future__ import annotations

import time

from fastapi.testclient import TestClient

from server.config import settings
from server.main import app


class _DummyClient:
    host = "127.0.0.1"


class _DummyURL:
    def __init__(self, path: str = "/health") -> None:
        self.path = path


class _DummyRequest:
    def __init__(self, path: str = "/health") -> None:
        self.client = _DummyClient()
        self.url = _DummyURL(path)


def test_check_rate_limit_limit_disabled_and_window_reset():
    import server.main as main

    original_limit = settings.RATE_LIMIT_PER_MIN
    original_bypass = settings.RATE_LIMIT_BYPASS
    try:
        settings.RATE_LIMIT_BYPASS = False
        settings.RATE_LIMIT_PER_MIN = 0
        main._rate_counters.clear()
        assert main._check_rate_limit(_DummyRequest()) is True

        settings.RATE_LIMIT_PER_MIN = 1
        current_window = int(time.time() // 60)
        key = ("127.0.0.1", "health")
        main._rate_counters[key] = (1, current_window - 1)
        assert main._check_rate_limit(_DummyRequest()) is True
        assert main._rate_counters[key][1] == current_window
    finally:
        settings.RATE_LIMIT_PER_MIN = original_limit
        settings.RATE_LIMIT_BYPASS = original_bypass


def test_check_rate_limit_bypass_enabled():
    import server.main as main

    original_limit = settings.RATE_LIMIT_PER_MIN
    original_bypass = settings.RATE_LIMIT_BYPASS
    try:
        settings.RATE_LIMIT_BYPASS = True
        settings.RATE_LIMIT_PER_MIN = 1
        main._rate_counters.clear()

        assert main._check_rate_limit(_DummyRequest()) is True
        assert ("127.0.0.1", "health") not in main._rate_counters
    finally:
        settings.RATE_LIMIT_PER_MIN = original_limit
        settings.RATE_LIMIT_BYPASS = original_bypass


def test_check_rate_limit_exempt_prefix_path():
    import server.main as main

    original_limit = settings.RATE_LIMIT_PER_MIN
    original_bypass = settings.RATE_LIMIT_BYPASS
    original_exempt = settings.RATE_LIMIT_EXEMPT_PATH_PREFIXES
    try:
        settings.RATE_LIMIT_BYPASS = False
        settings.RATE_LIMIT_PER_MIN = 1
        settings.RATE_LIMIT_EXEMPT_PATH_PREFIXES = "/maps/vector/vts/tile"
        main._rate_counters.clear()

        request = _DummyRequest("/maps/vector/vts/tile/13/2726/4097.pbf")
        assert main._check_rate_limit(request) is True
        assert main._rate_counters == {}
    finally:
        settings.RATE_LIMIT_PER_MIN = original_limit
        settings.RATE_LIMIT_BYPASS = original_bypass
        settings.RATE_LIMIT_EXEMPT_PATH_PREFIXES = original_exempt


def test_metrics_disabled_branch(monkeypatch):
    client = TestClient(app)
    monkeypatch.setattr(settings, "METRICS_ENABLED", False, raising=False)
    resp = client.get("/metrics")
    assert resp.status_code == 404
    assert resp.json()["code"] == "NOT_ENABLED"


def test_metrics_include_mcp_http_metrics(monkeypatch):
    from server.mcp import http_transport

    client = TestClient(app)
    monkeypatch.setattr(settings, "METRICS_ENABLED", True, raising=False)
    monkeypatch.setattr(
        http_transport,
        "_AUTH_FAILURES_TOTAL",
        {"authentication": 2},
        raising=False,
    )
    monkeypatch.setattr(
        http_transport,
        "_SESSION_QUOTA_REJECTIONS_TOTAL",
        1,
        raising=False,
    )
    http_transport._SESSION_STATE.clear()
    http_transport._SESSION_STATE["session-1"] = {"last_seen": time.time()}

    resp = client.get("/metrics")

    assert resp.status_code == 200
    body = resp.text
    assert 'mcp_http_auth_failures_total{reason="authentication"} 2' in body
    assert "mcp_http_session_quota_rejections_total 1" in body
    assert "mcp_http_sessions_active 1" in body


def test_generic_exception_handler_non_debug_path(monkeypatch):
    from tools.registry import Tool, register

    def boom(_payload):
        raise RuntimeError(
            "non-debug crash "
            f"{settings.NOMIS_SIGNATURE} "
            f"{settings.MCP_HTTP_AUTH_TOKEN} "
            f"{settings.MCP_HTTP_JWT_HS256_SECRET}"
        )

    name = f"temp.non_debug.{int(time.time() * 1000000)}"
    register(Tool(name=name, description="non-debug tool", handler=boom))
    monkeypatch.setattr(settings, "DEBUG_ERRORS", False, raising=False)
    monkeypatch.setattr(settings, "NOMIS_SIGNATURE", "signature-secret-value", raising=False)
    monkeypatch.setattr(settings, "MCP_HTTP_AUTH_TOKEN", "handler-auth-token", raising=False)
    monkeypatch.setattr(settings, "MCP_HTTP_JWT_HS256_SECRET", "handler-jwt-secret", raising=False)

    client = TestClient(app, raise_server_exceptions=False)
    resp = client.post("/tools/call", json={"tool": name})
    assert resp.status_code == 500
    body = resp.json()
    assert body["code"] == "INTERNAL_ERROR"
    assert "traceback" not in body
    assert "signature-secret-value" not in body["message"]
    assert "handler-auth-token" not in body["message"]
    assert "handler-jwt-secret" not in body["message"]
    assert "[REDACTED]" in body["message"]


def test_observability_json_size_and_cache_hit_edges():
    from server import observability

    class Unserializable:
        def __str__(self) -> str:
            return "fallback-value"

    assert observability._json_size_bytes(Unserializable()) == len("fallback-value")
    assert observability._result_has_cache_hit({"fromCache": True}) is True
    assert observability._result_has_cache_hit({"meta": {"cacheHit": True}}) is True
    assert observability._result_has_fallback({"fallback": {"kind": "map"}}) is True


def test_observability_delivery_fallback_detection():
    from server import observability

    assert observability._requested_delivery_mode({}) is None
    assert observability._requested_delivery_mode({"delivery": "AUTO"}) == "auto"
    assert observability._requested_delivery_mode({"delivery": "resource"}) == "resource"
    assert observability._requested_delivery_mode({"delivery": "bad"}) is None
    assert observability._result_delivery_mode({"delivery": "resource"}) == "resource"
    assert observability._result_delivery_mode({"delivery": "inline"}) == "inline"
    assert observability._result_delivery_mode({"delivery": 1}) is None
    assert observability._result_has_delivery_resource_fallback(
        {"delivery": "auto"},
        {"delivery": "resource"},
    ) is True
    assert observability._result_has_delivery_resource_fallback(
        {},
        {"delivery": "resource"},
    ) is False
    assert observability._result_has_delivery_resource_fallback(
        {"delivery": "inline"},
        {"delivery": "resource"},
    ) is False
    assert observability._result_has_delivery_resource_fallback(
        {"delivery": "auto"},
        {"delivery": "inline"},
    ) is False


def test_observability_delivery_fallback_metric_line():
    from server import observability

    observability.record_tool_call(
        tool_name="obs_delivery_fallback_test",
        transport="unit",
        payload={},
        result={"delivery": "resource"},
        status_code=200,
        latency_ms=1.2,
    )
    lines = observability.build_prometheus_lines()
    assert any(
        line.startswith("mcp_tool_delivery_resource_fallback_total")
        and 'tool="obs_delivery_fallback_test"' in line
        and 'transport="unit"' in line
        for line in lines
    )


def test_record_latency_overflow_bucket():
    import server.main as main

    original_overflow = main._latency_overflow
    main._latency_overflow = 0
    try:
        main._record_latency(999999.0)
        assert main._latency_overflow == 1
    finally:
        main._latency_overflow = original_overflow


def test_rate_limit_helper_edges_and_health_endpoint():
    import server.main as main

    original_exempt = settings.RATE_LIMIT_EXEMPT_PATH_PREFIXES
    try:
        settings.RATE_LIMIT_EXEMPT_PATH_PREFIXES = []
        assert main._rate_limit_exempt_prefixes() == ()
        settings.RATE_LIMIT_EXEMPT_PATH_PREFIXES = "/maps/vector"
        assert main._is_rate_limit_exempt("/maps/vector/vts") is True
        assert main._is_rate_limit_exempt("/health") is False
    finally:
        settings.RATE_LIMIT_EXEMPT_PATH_PREFIXES = original_exempt

    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "OK"}


def test_record_latency_bucket_and_counter_increment():
    import server.main as main

    original_hist = dict(main._latency_hist)
    original_requests = main._requests_total
    original_limited = main._rate_limited_total
    try:
        main._latency_hist = dict.fromkeys(main._latency_buckets, 0)
        main._requests_total = 0
        main._rate_limited_total = 0
        main._record_latency(1.0)
        main._increment_counter()
        main._increment_counter(rate_limited=True)
        assert main._latency_hist[5] == 1
        assert main._requests_total == 2
        assert main._rate_limited_total == 1
    finally:
        main._latency_hist = original_hist
        main._requests_total = original_requests
        main._rate_limited_total = original_limited


def test_generic_exception_handler_debug_path(monkeypatch):
    from tools.registry import Tool, register

    def boom(_payload):
        raise RuntimeError(
            "debug crash "
            f"{settings.NOMIS_SIGNATURE} "
            f"{settings.MCP_HTTP_AUTH_TOKEN} "
            f"{settings.MCP_HTTP_JWT_HS256_SECRET}"
        )

    name = f"temp.debug.{int(time.time() * 1000000)}"
    register(Tool(name=name, description="debug tool", handler=boom))
    monkeypatch.setattr(settings, "DEBUG_ERRORS", True, raising=False)
    monkeypatch.setattr(settings, "NOMIS_SIGNATURE", "debug-signature-secret", raising=False)
    monkeypatch.setattr(settings, "MCP_HTTP_AUTH_TOKEN", "debug-auth-secret", raising=False)
    monkeypatch.setattr(settings, "MCP_HTTP_JWT_HS256_SECRET", "debug-jwt-secret", raising=False)

    client = TestClient(app, raise_server_exceptions=False)
    resp = client.post("/tools/call", json={"tool": name})
    assert resp.status_code == 500
    body = resp.json()
    assert body["code"] == "INTERNAL_ERROR"
    assert "traceback" in body
    assert "debug-signature-secret" not in body["message"]
    assert "debug-auth-secret" not in body["message"]
    assert "debug-jwt-secret" not in body["message"]
    assert "[REDACTED]" in body["message"]
