import pytest
from fastapi.testclient import TestClient

from server.main import app
import importlib
from typing import Any, Callable

@pytest.fixture
def mock_os_client(monkeypatch):
    import tools.os_common as os_common
    # Force API key and reload client module
    monkeypatch.setattr(os_common.settings, "OS_API_KEY", "test-key", raising=False)
    importlib.reload(os_common)
    handlers: dict[str, Callable[[str, dict[str, Any]], tuple[int, dict[str, Any]]]] = {}
    real = os_common.OSClient(api_key="test-key")

    def fake_get_json(url: str, params: dict[str, Any] | None = None):  # type: ignore[override]
        for key, fn in handlers.items():
            if key in url:
                return fn(url, params or {})
        return 200, {"results": []}

    real.get_json = fake_get_json  # type: ignore
    monkeypatch.setattr("tools.os_common.client", real)
    return handlers

@pytest.fixture(scope="session")
def client():
    return TestClient(app)