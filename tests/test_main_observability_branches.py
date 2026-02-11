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
        raise RuntimeError("non-debug crash")

    name = f"temp.non_debug.{int(time.time() * 1000000)}"
    register(Tool(name=name, description="non-debug tool", handler=boom))
    monkeypatch.setattr(settings, "DEBUG_ERRORS", False, raising=False)

    client = TestClient(app, raise_server_exceptions=False)
    resp = client.post("/tools/call", json={"tool": name})
    assert resp.status_code == 500
    body = resp.json()
    assert body["code"] == "INTERNAL_ERROR"
    assert "traceback" not in body


def test_observability_json_size_and_cache_hit_edges():
    from server import observability

    class Unserializable:
        def __str__(self) -> str:
            return "fallback-value"

    assert observability._json_size_bytes(Unserializable()) == len("fallback-value")
    assert observability._result_has_cache_hit({"fromCache": True}) is True
    assert observability._result_has_cache_hit({"meta": {"cacheHit": True}}) is True
