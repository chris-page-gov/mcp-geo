from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from server.main import app


class _FakeResponse:
    def __init__(self, status_code: int, content: bytes, headers: dict[str, str] | None = None):
        self.status_code = status_code
        self.content = content
        self.headers = headers or {}


def test_static_osm_map_returns_tile(monkeypatch: pytest.MonkeyPatch) -> None:
    client = TestClient(app)

    def fake_get(url: str, timeout: float | None = None, headers: dict[str, str] | None = None) -> _FakeResponse:  # noqa: ARG001
        return _FakeResponse(200, b"png-data", {"content-type": "image/png"})

    monkeypatch.setattr("server.maps_proxy.requests.get", fake_get)

    resp = client.get("/maps/static/osm", params={"bbox": "-0.2,51.5,-0.1,51.6", "size": 256})
    assert resp.status_code == 200
    assert resp.headers.get("content-type", "").startswith("image/png")
    assert resp.headers.get("X-Map-Zoom")
    assert resp.headers.get("X-Map-Tile")
    assert resp.content == b"png-data"


def test_static_osm_map_rejects_invalid_bbox() -> None:
    client = TestClient(app)
    resp = client.get("/maps/static/osm", params={"bbox": "invalid"})
    assert resp.status_code == 400
