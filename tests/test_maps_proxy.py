from __future__ import annotations

from copy import deepcopy
from types import SimpleNamespace

from server import maps_proxy


def test_rewrite_style_urls_rewrites_os_urls():
    style = {
        "version": 8,
        "_sprite": f"{maps_proxy._OS_BASE}/sprites/basic",
        "glyphs": f"{maps_proxy._OS_BASE}/fonts/{{fontstack}}/{{range}}.pbf",
        "sources": {
            "os": {
                "type": "vector",
                "url": f"{maps_proxy._OS_BASE}/vts/resources/styles",
            }
        },
    }
    rewritten = maps_proxy._rewrite_style_urls(
        deepcopy(style),
        "test-key",
        srs="3857",
        base_url="http://localhost:8000",
    )

    assert rewritten["sprite"].startswith("http://localhost:8000/maps/vector")
    assert "key=test-key" in rewritten["sprite"]
    assert rewritten["glyphs"].startswith("http://localhost:8000/maps/vector")

    source = rewritten["sources"]["os"]
    assert source.get("tileSize") == 512
    assert source["tiles"][0].startswith("http://localhost:8000/maps/vector/vts/tile/")
    assert "key=test-key" in source["tiles"][0]
    assert "srs=3857" in source["tiles"][0]


def test_osm_proxy_caches_tiles(monkeypatch, client):
    class DummyResponse:
        def __init__(self, content: bytes = b"tile") -> None:
            self.status_code = 200
            self.content = content
            self.headers = {"content-type": "image/png"}

    calls: list[tuple[str, dict[str, str]]] = []

    def fake_get(url: str, timeout: float, headers: dict[str, str]):
        calls.append((url, headers))
        return DummyResponse()

    maps_proxy._OSM_CACHE.clear()
    monkeypatch.setattr(maps_proxy, "requests", SimpleNamespace(get=fake_get))
    monkeypatch.setattr(maps_proxy.settings, "OSM_TILE_CACHE_TTL", 60)
    monkeypatch.setattr(maps_proxy.settings, "OSM_TILE_CACHE_SIZE", 10)
    monkeypatch.setattr(maps_proxy.settings, "OSM_TILE_BASE", "https://tile.example.com")
    monkeypatch.setattr(maps_proxy.settings, "OSM_TILE_USER_AGENT", "mcp-geo-test")
    monkeypatch.setattr(maps_proxy.settings, "OSM_TILE_CONTACT", "mailto:test@example.com")

    first = client.get("/maps/raster/osm/1/2/3.png")
    assert first.status_code == 200
    assert first.headers.get("X-Cache") == "MISS"
    assert "Cache-Control" in first.headers

    second = client.get("/maps/raster/osm/1/2/3.png")
    assert second.status_code == 200
    assert second.headers.get("X-Cache") == "HIT"
    assert len(calls) == 1
    assert "mailto:test@example.com" in calls[0][1]["User-Agent"]
