from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Dict

from server.config import settings


@dataclass
class BreakerState:
    state: str
    failure_count: int
    opened_at: float | None
    half_open_successes: int


class CircuitBreaker:
    def __init__(
        self,
        name: str,
        failure_threshold: int,
        reset_timeout: float,
        half_open_successes: int = 1,
    ) -> None:
        self.name = name
        self.failure_threshold = max(1, int(failure_threshold))
        self.reset_timeout = max(1.0, float(reset_timeout))
        self.half_open_successes = max(1, int(half_open_successes))
        self._lock = threading.Lock()
        self._state = BreakerState(
            state="closed",
            failure_count=0,
            opened_at=None,
            half_open_successes=0,
        )

    def allow(self) -> bool:
        if not _breaker_enabled():
            return True
        with self._lock:
            if self._state.state == "open":
                if self._state.opened_at is None:
                    return False
                if time.time() - self._state.opened_at >= self.reset_timeout:
                    self._state.state = "half_open"
                    self._state.half_open_successes = 0
                    return True
                return False
            return True

    def record_success(self) -> None:
        if not _breaker_enabled():
            return
        with self._lock:
            if self._state.state == "half_open":
                self._state.half_open_successes += 1
                if self._state.half_open_successes >= self.half_open_successes:
                    self._state.state = "closed"
                    self._state.failure_count = 0
                    self._state.opened_at = None
                    self._state.half_open_successes = 0
            elif self._state.state == "open":
                # Success while open should reset to closed.
                self._state.state = "closed"
                self._state.failure_count = 0
                self._state.opened_at = None
                self._state.half_open_successes = 0
            else:
                self._state.failure_count = 0

    def record_failure(self) -> None:
        if not _breaker_enabled():
            return
        with self._lock:
            if self._state.state == "half_open":
                self._open()
                return
            self._state.failure_count += 1
            if self._state.failure_count >= self.failure_threshold:
                self._open()

    def _open(self) -> None:
        self._state.state = "open"
        self._state.opened_at = time.time()
        self._state.failure_count = 0
        self._state.half_open_successes = 0

    def snapshot(self) -> BreakerState:
        with self._lock:
            return BreakerState(**self._state.__dict__)


def _breaker_enabled() -> bool:
    return bool(getattr(settings, "CIRCUIT_BREAKER_ENABLED", True))


def _breaker_failure_threshold() -> int:
    return int(getattr(settings, "CIRCUIT_BREAKER_FAILURE_THRESHOLD", 5))


def _breaker_reset_seconds() -> float:
    return float(getattr(settings, "CIRCUIT_BREAKER_RESET_SECONDS", 30.0))


def _breaker_half_open_successes() -> int:
    return int(getattr(settings, "CIRCUIT_BREAKER_HALF_OPEN_SUCCESSES", 1))


_BREAKERS: Dict[str, CircuitBreaker] = {}


def get_circuit_breaker(name: str) -> CircuitBreaker:
    breaker = _BREAKERS.get(name)
    if breaker is None:
        breaker = CircuitBreaker(
            name=name,
            failure_threshold=_breaker_failure_threshold(),
            reset_timeout=_breaker_reset_seconds(),
            half_open_successes=_breaker_half_open_successes(),
        )
        _BREAKERS[name] = breaker
    return breaker


__all__ = ["CircuitBreaker", "get_circuit_breaker"]
