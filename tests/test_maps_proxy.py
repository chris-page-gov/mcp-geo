from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from server.config import settings
from server.main import app


class _FakeResponse:
    def __init__(
        self,
        status_code: int,
        content: bytes,
        headers: dict[str, str] | None = None,
        text: str | None = None,
    ):
        self.status_code = status_code
        self.content = content
        self.headers = headers or {}
        self.text = text or content.decode("utf-8", errors="ignore")


def test_static_osm_map_returns_tile(monkeypatch: pytest.MonkeyPatch) -> None:
    client = TestClient(app)

    def fake_get(
        url: str,
        timeout: float | None = None,
        headers: dict[str, str] | None = None,
    ) -> _FakeResponse:
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


def test_static_osm_map_honors_large_size_with_multi_tile_render(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from server import maps_proxy

    client = TestClient(app)
    maps_proxy._OSM_CACHE.clear()
    calls: list[str] = []
    png_bytes = _make_png()

    def fake_get(
        url: str,
        timeout: float | None = None,
        headers: dict[str, str] | None = None,
    ) -> _FakeResponse:
        calls.append(url)
        return _FakeResponse(200, png_bytes, {"content-type": "image/png"})

    monkeypatch.setattr("server.maps_proxy.requests.get", fake_get)
    resp = client.get("/maps/static/osm", params={"bbox": "-0.2,51.5,-0.1,51.6", "size": 1024})
    assert resp.status_code == 200
    assert resp.headers.get("content-type", "").startswith("image/png")
    assert int(resp.headers.get("X-Map-Tiles", "0")) > 1
    assert len(calls) > 1


def test_vector_proxy_prefers_bearer_token(monkeypatch: pytest.MonkeyPatch) -> None:
    client = TestClient(app)

    def fake_get(
        url: str,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> _FakeResponse:
        assert headers == {"Authorization": "Bearer test-token"}
        assert "key" not in (params or {})
        return _FakeResponse(
            200,
            b"tile-bytes",
            {"content-type": "application/x-protobuf"},
        )

    monkeypatch.setattr("server.maps_proxy.requests.get", fake_get)
    monkeypatch.setattr("server.maps_proxy.settings.OS_API_KEY", "env-key", raising=False)

    resp = client.get(
        "/maps/vector/vts/tile/7/42/63.pbf",
        params={"srs": "3857"},
        headers={"Authorization": "Bearer test-token"},
    )
    assert resp.status_code == 200
    assert resp.content == b"tile-bytes"


def test_vector_proxy_falls_back_to_env_key(monkeypatch: pytest.MonkeyPatch) -> None:
    client = TestClient(app)

    def fake_get(
        url: str,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> _FakeResponse:
        assert (params or {}).get("key") == "env-key"
        assert headers in (None, {})
        return _FakeResponse(
            200,
            b"tile-bytes",
            {"content-type": "application/x-protobuf"},
        )

    monkeypatch.setattr("server.maps_proxy.requests.get", fake_get)
    monkeypatch.setattr("server.maps_proxy.settings.OS_API_KEY", "env-key", raising=False)

    resp = client.get("/maps/vector/vts/tile/7/42/63.pbf", params={"srs": "3857"})
    assert resp.status_code == 200
    assert resp.content == b"tile-bytes"


def test_vector_proxy_supports_key_header(monkeypatch: pytest.MonkeyPatch) -> None:
    client = TestClient(app)

    def fake_get(
        url: str,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> _FakeResponse:
        assert (params or {}).get("key") == "header-key"
        assert headers in (None, {})
        return _FakeResponse(
            200,
            b"tile-bytes",
            {"content-type": "application/x-protobuf"},
        )

    monkeypatch.setattr("server.maps_proxy.requests.get", fake_get)
    monkeypatch.setattr("server.maps_proxy.settings.OS_API_KEY", "", raising=False)

    resp = client.get(
        "/maps/vector/vts/tile/7/42/63.pbf",
        params={"srs": "3857"},
        headers={"key": "header-key"},
    )
    assert resp.status_code == 200
    assert resp.content == b"tile-bytes"


def test_vector_proxy_requires_auth_when_no_key_or_token(monkeypatch: pytest.MonkeyPatch) -> None:
    client = TestClient(app)
    monkeypatch.setattr("server.maps_proxy.settings.OS_API_KEY", "", raising=False)

    resp = client.get("/maps/vector/vts/tile/7/42/63.pbf", params={"srs": "3857"})
    assert resp.status_code == 401
    assert "OS authentication required" in resp.text


def test_vector_proxy_vts_style_query_honors_selected_style(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from server import maps_proxy

    client = TestClient(app)
    monkeypatch.setattr("server.maps_proxy.settings.OS_API_KEY", "env-key", raising=False)
    monkeypatch.setattr(maps_proxy, "_LOCAL_STYLE_DIR", tmp_path)

    def _unexpected_get(*args: object, **kwargs: object) -> _FakeResponse:
        raise AssertionError("requests.get should not be called when local style exists")

    monkeypatch.setattr("server.maps_proxy.requests.get", _unexpected_get)

    style_template = {
        "version": 8,
        "sprite": "https://example.test/sprite",
        "glyphs": "https://example.test/fonts/{fontstack}/{range}.pbf",
        "sources": {"esri": {"type": "vector", "url": "https://api.os.uk/maps/vector/v1/vts"}},
        "layers": [{"id": "background", "type": "background", "paint": {}}],
    }

    light_style = dict(style_template)
    light_style["layers"] = [
        {"id": "background", "type": "background", "paint": {"background-color": "#ffffff"}}
    ]
    dark_style = dict(style_template)
    dark_style["layers"] = [
        {"id": "background", "type": "background", "paint": {"background-color": "#111111"}}
    ]

    (tmp_path / "OS_VTS_3857_Light.json").write_text(json.dumps(light_style), encoding="utf-8")
    (tmp_path / "OS_VTS_3857_Dark.json").write_text(json.dumps(dark_style), encoding="utf-8")

    resp_light = client.get(
        "/maps/vector/vts/resources/styles",
        params={"style": "OS_VTS_3857_Light.json", "srs": "3857"},
    )
    resp_dark = client.get(
        "/maps/vector/vts/resources/styles",
        params={"style": "OS_VTS_3857_Dark.json", "srs": "3857"},
    )

    assert resp_light.status_code == 200
    assert resp_dark.status_code == 200
    payload_light = resp_light.json()
    payload_dark = resp_dark.json()

    assert payload_light["layers"][0]["paint"]["background-color"] == "#ffffff"
    assert payload_dark["layers"][0]["paint"]["background-color"] == "#111111"
    assert (
        payload_dark["sources"]["esri"]["tiles"][0]
        == "http://testserver/maps/vector/vts/tile/{z}/{y}/{x}.pbf?srs=3857"
    )


def test_vector_tile_route_is_exempt_from_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    from server import main

    client = TestClient(app)
    calls: list[str] = []

    def fake_get(
        url: str,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> _FakeResponse:
        calls.append(url)
        return _FakeResponse(200, b"pbf-bytes", {"content-type": "application/x-protobuf"})

    monkeypatch.setattr("server.maps_proxy.requests.get", fake_get)
    monkeypatch.setattr(settings, "OS_API_KEY", "test-key", raising=False)
    monkeypatch.setattr(settings, "RATE_LIMIT_PER_MIN", 1, raising=False)
    monkeypatch.setattr(settings, "RATE_LIMIT_BYPASS", False, raising=False)
    monkeypatch.setattr(
        settings,
        "RATE_LIMIT_EXEMPT_PATH_PREFIXES",
        "/maps/vector/vts/tile",
        raising=False,
    )
    with main._rate_lock:
        main._rate_counters.clear()

    first = client.get("/maps/vector/vts/tile/13/2726/4097.pbf", params={"srs": "3857"})
    second = client.get("/maps/vector/vts/tile/13/2726/4098.pbf", params={"srs": "3857"})

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.content == b"pbf-bytes"
    assert second.content == b"pbf-bytes"
    assert len(calls) == 2


def _make_png() -> bytes:
    image = Image.new("RGBA", (1, 1), (0, 128, 255, 255))
    from io import BytesIO

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
