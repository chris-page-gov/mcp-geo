from __future__ import annotations

from _pytest.monkeypatch import MonkeyPatch

import server.circuit_breaker as circuit_breaker
from server.config import settings


def test_circuit_breaker_opens_and_recovers(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "CIRCUIT_BREAKER_ENABLED", True, raising=False)
    now = [0.0]
    monkeypatch.setattr(circuit_breaker.time, "time", lambda: now[0])
    breaker = circuit_breaker.CircuitBreaker(
        name="test",
        failure_threshold=2,
        reset_timeout=1.0,
        half_open_successes=1,
    )
    assert breaker.allow()
    breaker.record_failure()
    assert breaker.allow()
    breaker.record_failure()
    assert not breaker.allow()
    now[0] += 2.0
    assert breaker.allow()
    breaker.record_success()
    assert breaker.allow()


def test_circuit_breaker_open_state_controls(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "CIRCUIT_BREAKER_ENABLED", True, raising=False)
    breaker = circuit_breaker.CircuitBreaker(
        name="test-open",
        failure_threshold=1,
        reset_timeout=1.0,
        half_open_successes=1,
    )
    breaker._state.state = "open"
    breaker._state.opened_at = None
    assert breaker.allow() is False
    breaker._state.opened_at = 0.0
    breaker.record_success()
    assert breaker.allow() is True


def test_circuit_breaker_half_open_failure(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "CIRCUIT_BREAKER_ENABLED", True, raising=False)
    breaker = circuit_breaker.CircuitBreaker(
        name="test-half",
        failure_threshold=1,
        reset_timeout=1.0,
        half_open_successes=1,
    )
    breaker._state.state = "half_open"
    breaker._state.opened_at = 0.0
    breaker.record_failure()
    assert breaker._state.state == "open"
    assert breaker.snapshot().state == "open"


def test_circuit_breaker_disabled(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "CIRCUIT_BREAKER_ENABLED", False, raising=False)
    breaker = circuit_breaker.CircuitBreaker(
        name="test-disabled",
        failure_threshold=1,
        reset_timeout=1.0,
        half_open_successes=1,
    )
    breaker.record_failure()
    assert breaker.allow() is True


def test_circuit_breaker_record_success_closed(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "CIRCUIT_BREAKER_ENABLED", True, raising=False)
    breaker = circuit_breaker.CircuitBreaker(
        name="test-closed",
        failure_threshold=2,
        reset_timeout=1.0,
        half_open_successes=1,
    )
    breaker._state.failure_count = 2
    breaker.record_success()
    assert breaker._state.failure_count == 0
