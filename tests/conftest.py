import pytest
from fastapi.testclient import TestClient

from server.main import app
from typing import Any, Callable

@pytest.fixture
def mock_os_client(monkeypatch):
    import tools.os_common as os_common
    handlers: dict[str, Callable[[str, dict[str, Any]], tuple[int, dict[str, Any]]]] = {}
    # Avoid importlib.reload(os_common): tools import the shared client instance at import-time.
    # Reloading would create a new client object and break those references.
    monkeypatch.setattr(os_common.settings, "OS_API_KEY", "test-key", raising=False)
    os_common.client.api_key = "test-key"

    def fake_get_json(url: str, params: dict[str, Any] | None = None):  # type: ignore[override]
        for key, fn in handlers.items():
            if key in url:
                return fn(url, params or {})
        return 200, {"results": []}

    monkeypatch.setattr(os_common.client, "get_json", fake_get_json)
    return handlers

@pytest.fixture(scope="session")
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def disable_circuit_breaker(monkeypatch):
    from server.config import settings
    monkeypatch.setattr(settings, "CIRCUIT_BREAKER_ENABLED", False, raising=False)


@pytest.fixture(autouse=True)
def enable_rate_limit_bypass_for_tests(monkeypatch):
    from server.config import settings
    monkeypatch.setattr(settings, "RATE_LIMIT_BYPASS", True, raising=False)
