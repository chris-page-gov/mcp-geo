from fastapi.testclient import TestClient
from server.main import app
from server.config import settings

client = TestClient(app)


def test_metrics_endpoint_exposes_counters():
    if not settings.METRICS_ENABLED:
        return
    r = client.get("/metrics")
    assert r.status_code == 200
    text = r.text
    assert "app_requests_total" in text
    assert "app_request_latency_ms_bucket" in text


def test_rate_limit_enforced():
    # Temporarily lower limit for test (monkeypatch style inline)
    original = settings.RATE_LIMIT_PER_MIN
    orig_bypass = settings.RATE_LIMIT_BYPASS
    settings.RATE_LIMIT_PER_MIN = 5
    settings.RATE_LIMIT_BYPASS = False
    hits: list[int] = []
    for _ in range(7):
        resp = client.get("/health")
        status: int = resp.status_code
        hits.append(status)
    # Restore
    settings.RATE_LIMIT_PER_MIN = original
    settings.RATE_LIMIT_BYPASS = orig_bypass
    assert any(code == 429 for code in hits), hits
