from __future__ import annotations

import time

from fastapi.testclient import TestClient

from server.config import settings
from server.main import app


class _DummyClient:
    host = "127.0.0.1"


class _DummyURL:
    path = "/health"


class _DummyRequest:
    client = _DummyClient()
    url = _DummyURL()


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


def test_metrics_disabled_branch(monkeypatch):
    client = TestClient(app)
    monkeypatch.setattr(settings, "METRICS_ENABLED", False, raising=False)
    resp = client.get("/metrics")
    assert resp.status_code == 404
    assert resp.json()["code"] == "NOT_ENABLED"


def test_generic_exception_handler_non_debug_path(monkeypatch):
    from tools.registry import Tool, register

    def boom(_payload):
        raise RuntimeError(f"non-debug crash {settings.NOMIS_SIGNATURE}")

    name = f"temp.non_debug.{int(time.time() * 1000000)}"
    register(Tool(name=name, description="non-debug tool", handler=boom))
    monkeypatch.setattr(settings, "DEBUG_ERRORS", False, raising=False)
    monkeypatch.setattr(settings, "NOMIS_SIGNATURE", "signature-secret-value", raising=False)

    client = TestClient(app, raise_server_exceptions=False)
    resp = client.post("/tools/call", json={"tool": name})
    assert resp.status_code == 500
    body = resp.json()
    assert body["code"] == "INTERNAL_ERROR"
    assert "traceback" not in body
    assert "signature-secret-value" not in body["message"]
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
