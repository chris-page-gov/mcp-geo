from scripts.rate_limit_assessor import ProbePoint, parse_prometheus_metrics, percentile, recommend_limit


def test_parse_prometheus_metrics_basic():
    text = """
# HELP app_requests_total Total HTTP requests
# TYPE app_requests_total counter
app_requests_total 120
app_rate_limited_total 5
app_request_latency_ms_bucket{le="50"} 40
"""
    parsed = parse_prometheus_metrics(text)
    assert parsed["app_requests_total"] == 120.0
    assert parsed["app_rate_limited_total"] == 5.0
    assert parsed["app_request_latency_ms_bucket"] == 40.0


def test_percentile_handles_small_lists():
    assert percentile([], 95.0) == 0.0
    assert percentile([10.0], 95.0) == 10.0
    assert round(percentile([10.0, 20.0], 50.0), 2) == 15.0


def test_recommend_limit_with_limited_next_step():
    points = [
        ProbePoint(
            rpm=60,
            duration_sec=20,
            requests=20,
            success=20,
            limited=0,
            errors=0,
            mean_ms=10.0,
            p95_ms=15.0,
        ),
        ProbePoint(
            rpm=90,
            duration_sec=20,
            requests=30,
            success=29,
            limited=1,
            errors=0,
            mean_ms=11.0,
            p95_ms=16.0,
        ),
        ProbePoint(
            rpm=120,
            duration_sec=20,
            requests=40,
            success=35,
            limited=5,
            errors=0,
            mean_ms=12.0,
            p95_ms=17.0,
        ),
    ]
    rec = recommend_limit(
        points,
        target_429_ratio=0.05,
        headroom_percent=20.0,
        target_p95_ms=None,
    )
    assert rec["max_stable_rpm"] == 90
    assert rec["first_limited_rpm"] == 120
    # 90 * 1.2 == 108, below first limited step, so keep buffered value.
    assert rec["recommended_rate_limit_per_min"] == 108


def test_recommend_limit_when_no_limiter_hit():
    points = [
        ProbePoint(
            rpm=60,
            duration_sec=20,
            requests=20,
            success=20,
            limited=0,
            errors=0,
            mean_ms=10.0,
            p95_ms=15.0,
        ),
        ProbePoint(
            rpm=90,
            duration_sec=20,
            requests=30,
            success=30,
            limited=0,
            errors=0,
            mean_ms=10.0,
            p95_ms=15.0,
        ),
    ]
    rec = recommend_limit(
        points,
        target_429_ratio=0.01,
        headroom_percent=10.0,
        target_p95_ms=None,
    )
    assert rec["max_stable_rpm"] == 90
    assert rec["first_limited_rpm"] is None
    assert rec["reason"] == "no_limiter_hit_in_probe_range"
    assert rec["recommended_rate_limit_per_min"] == 99


def test_recommend_limit_with_p95_guardrail():
    points = [
        ProbePoint(
            rpm=60,
            duration_sec=20,
            requests=20,
            success=20,
            limited=0,
            errors=0,
            mean_ms=10.0,
            p95_ms=35.0,
        ),
        ProbePoint(
            rpm=90,
            duration_sec=20,
            requests=30,
            success=30,
            limited=0,
            errors=0,
            mean_ms=10.0,
            p95_ms=80.0,
        ),
    ]
    rec = recommend_limit(
        points,
        target_429_ratio=0.01,
        headroom_percent=10.0,
        target_p95_ms=50.0,
    )
    assert rec["max_stable_rpm"] == 60
    assert rec["first_limited_rpm"] == 90
    assert rec["recommended_rate_limit_per_min"] == 60
