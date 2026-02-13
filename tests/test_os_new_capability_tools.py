from __future__ import annotations

from fastapi.testclient import TestClient

from server.main import app

client = TestClient(app)


def test_os_maps_wmts_and_raster_tile(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from tools import os_maps

    calls: list[str] = []

    def fake_get_bytes(url: str, params=None):
        calls.append(url)
        if "wmts" in url:
            return 200, {"contentType": "application/xml", "content": b"<Capabilities />"}
        return 200, {"contentType": "image/png", "content": b"\x89PNG\r\n\x1a\n"}

    monkeypatch.setattr(os_maps.client, "get_bytes", fake_get_bytes, raising=True)

    wmts = client.post("/tools/call", json={"tool": "os_maps.wmts_capabilities"})
    assert wmts.status_code == 200
    wmts_body = wmts.json()
    assert wmts_body["delivery"] == "inline"
    assert "xml" in wmts_body

    tile = client.post(
        "/tools/call",
        json={"tool": "os_maps.raster_tile", "style": "Road_3857", "z": 7, "x": 63, "y": 42},
    )
    assert tile.status_code == 200
    tile_body = tile.json()
    assert tile_body["delivery"] == "inline"
    assert tile_body["contentType"].startswith("image/")
    assert any("/maps/raster/v1/wmts" in url for url in calls)
    assert any("/maps/raster/v1/zxy/Road_3857/7/63/42.png" in url for url in calls)

    bad = client.post(
        "/tools/call",
        json={"tool": "os_maps.raster_tile", "z": -1, "x": 1, "y": 1},
    )
    assert bad.status_code == 400
    assert bad.json()["code"] == "INVALID_INPUT"


def test_os_features_wfs_capabilities(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from tools import os_features

    calls: list[str] = []

    def fake_get_bytes(url: str, params=None):
        calls.append(url)
        return 200, {"contentType": "application/xml", "content": b"<WFS_Capabilities />"}

    monkeypatch.setattr(os_features.client, "get_bytes", fake_get_bytes, raising=True)

    resp = client.post("/tools/call", json={"tool": "os_features.wfs_capabilities"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["delivery"] == "inline"
    assert "xml" in body

    archive = client.post("/tools/call", json={"tool": "os_features.wfs_archive_capabilities"})
    assert archive.status_code == 200
    assert any(url.endswith("/features/v1/wfs") for url in calls)
    assert any(url.endswith("/features/v1/wfs/archive") for url in calls)

    bad_inline = client.post(
        "/tools/call",
        json={"tool": "os_features.wfs_capabilities", "inlineMaxBytes": 0},
    )
    assert bad_inline.status_code == 400
    assert bad_inline.json()["code"] == "INVALID_INPUT"


def test_os_tiles_ota_and_os_net(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from tools import os_net, os_tiles_ota

    json_calls: list[str] = []
    bytes_calls: list[str] = []

    def fake_get_json(url: str, params=None):
        json_calls.append(url)
        if url.endswith("/rinex"):
            return 200, {"years": [2024, 2025]}
        if "/stations/" in url:
            return 200, {"id": "AMER"}
        return 200, {"ok": True}

    def fake_get_bytes(url: str, params=None):
        bytes_calls.append(url)
        return 200, {"contentType": "text/plain", "content": b"line1\nline2\n"}

    monkeypatch.setattr(os_tiles_ota.client, "get_json", fake_get_json, raising=True)
    monkeypatch.setattr(os_net.client, "get_json", fake_get_json, raising=True)
    monkeypatch.setattr(os_net.client, "get_bytes", fake_get_bytes, raising=True)

    assert client.post("/tools/call", json={"tool": "os_tiles_ota.collections"}).status_code == 200
    assert (
        client.post("/tools/call", json={"tool": "os_tiles_ota.tilematrixsets"}).status_code
        == 200
    )
    assert client.post("/tools/call", json={"tool": "os_tiles_ota.conformance"}).status_code == 200
    assert client.post("/tools/call", json={"tool": "os_net.rinex_years"}).status_code == 200
    assert client.post(
        "/tools/call", json={"tool": "os_net.station_get", "stationId": "AMER"}
    ).status_code == 200
    log_resp = client.post("/tools/call", json={"tool": "os_net.station_log", "stationId": "AMER"})
    assert log_resp.status_code == 200
    assert log_resp.json()["delivery"] == "inline"

    assert any(url.endswith("/maps/vector/ngd/ota/v1/collections") for url in json_calls)
    assert any(url.endswith("/maps/vector/ngd/ota/v1/tilematrixsets") for url in json_calls)
    assert any(url.endswith("/maps/vector/ngd/ota/v1/conformance") for url in json_calls)
    assert any(url.endswith("/positioning/osnet/v1/rinex") for url in json_calls)
    assert any(url.endswith("/positioning/osnet/v1/stations/AMER") for url in json_calls)
    assert any(url.endswith("/positioning/osnet/v1/stations/AMER/log") for url in bytes_calls)


def test_os_tiles_ota_and_os_net_errors(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from tools import os_net, os_tiles_ota

    monkeypatch.setattr(
        os_tiles_ota.client,
        "get_json",
        lambda _url, _params=None: (500, {"isError": True, "code": "OS_API_ERROR"}),
        raising=True,
    )
    monkeypatch.setattr(
        os_net.client,
        "get_json",
        lambda _url, _params=None: (500, {"isError": True, "code": "OS_API_ERROR"}),
        raising=True,
    )

    fail_ota = client.post("/tools/call", json={"tool": "os_tiles_ota.collections"})
    assert fail_ota.status_code == 500
    assert fail_ota.json()["code"] == "OS_API_ERROR"

    fail_net = client.post("/tools/call", json={"tool": "os_net.station_get", "stationId": "AMER"})
    assert fail_net.status_code == 500
    assert fail_net.json()["code"] == "OS_API_ERROR"


def test_os_maps_and_features_resource_delivery_paths(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from tools import os_features, os_maps

    def fake_maps_get_bytes(url: str, params=None):
        if "wmts" in url:
            return 200, {
                "contentType": "application/xml",
                "content": b"<Capabilities>" + (b"x" * 8000),
            }
        return 200, {
            "contentType": "image/png",
            "content": b"\x89PNG\r\n\x1a\n" + (b"x" * 8000),
        }

    def fake_features_get_bytes(_url: str, _params=None):
        return 200, {"contentType": "application/xml", "content": b"<WFS>" + (b"x" * 8000)}

    def fake_write(prefix: str, payload: dict):
        return {
            "resourceUri": f"resource://mcp-geo/os-exports/{prefix}.json",
            "bytes": 100,
            "sha256": "abc",
            "path": "/tmp/resource.json",
        }

    monkeypatch.setattr(os_maps.client, "get_bytes", fake_maps_get_bytes, raising=True)
    monkeypatch.setattr(os_features.client, "get_bytes", fake_features_get_bytes, raising=True)
    monkeypatch.setattr(os_maps, "write_resource_payload", fake_write, raising=True)
    monkeypatch.setattr(os_features, "write_resource_payload", fake_write, raising=True)

    wmts = client.post(
        "/tools/call",
        json={"tool": "os_maps.wmts_capabilities", "delivery": "auto", "inlineMaxBytes": 1},
    )
    assert wmts.status_code == 200
    assert wmts.json()["delivery"] == "resource"

    tile = client.post(
        "/tools/call",
        json={
            "tool": "os_maps.raster_tile",
            "style": "Outdoor_3857",
            "z": 7,
            "x": 63,
            "y": 42,
            "delivery": "auto",
            "inlineMaxBytes": 1,
        },
    )
    assert tile.status_code == 200
    assert tile.json()["delivery"] == "resource"

    wfs = client.post(
        "/tools/call",
        json={"tool": "os_features.wfs_capabilities", "delivery": "auto", "inlineMaxBytes": 1},
    )
    assert wfs.status_code == 200
    assert wfs.json()["delivery"] == "resource"


def test_os_maps_features_os_net_invalid_payload_branches(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from tools import os_features, os_maps, os_net

    monkeypatch.setattr(
        os_maps.client,
        "get_bytes",
        lambda _url, _params=None: (
            200,
            {"contentType": "application/xml", "content": "not-bytes"},
        ),
        raising=True,
    )
    wmts_bad = client.post("/tools/call", json={"tool": "os_maps.wmts_capabilities"})
    assert wmts_bad.status_code == 500
    assert wmts_bad.json()["code"] == "INTEGRATION_ERROR"

    raster_bad_format = client.post(
        "/tools/call",
        json={"tool": "os_maps.raster_tile", "z": 1, "x": 1, "y": 1, "format": "gif"},
    )
    assert raster_bad_format.status_code == 400
    assert raster_bad_format.json()["code"] == "INVALID_INPUT"

    monkeypatch.setattr(
        os_maps.client,
        "get_bytes",
        lambda _url, _params=None: (200, {"contentType": "image/png", "content": "not-bytes"}),
        raising=True,
    )
    raster_bad = client.post(
        "/tools/call",
        json={"tool": "os_maps.raster_tile", "z": 1, "x": 1, "y": 1},
    )
    assert raster_bad.status_code == 500
    assert raster_bad.json()["code"] == "INTEGRATION_ERROR"

    monkeypatch.setattr(
        os_features.client,
        "get_bytes",
        lambda _url, _params=None: (500, {"isError": True, "code": "OS_API_ERROR"}),
        raising=True,
    )
    wfs_upstream = client.post("/tools/call", json={"tool": "os_features.wfs_capabilities"})
    assert wfs_upstream.status_code == 500
    assert wfs_upstream.json()["code"] == "OS_API_ERROR"

    monkeypatch.setattr(
        os_features.client,
        "get_bytes",
        lambda _url, _params=None: (200, {"contentType": "application/xml", "content": "no-bytes"}),
        raising=True,
    )
    wfs_bad = client.post("/tools/call", json={"tool": "os_features.wfs_capabilities"})
    assert wfs_bad.status_code == 500
    assert wfs_bad.json()["code"] == "INTEGRATION_ERROR"

    station_missing = client.post("/tools/call", json={"tool": "os_net.station_log"})
    assert station_missing.status_code == 400
    assert station_missing.json()["code"] == "INVALID_INPUT"

    station_bad_delivery = client.post(
        "/tools/call",
        json={"tool": "os_net.station_log", "stationId": "AMER", "delivery": "invalid"},
    )
    assert station_bad_delivery.status_code == 400
    assert station_bad_delivery.json()["code"] == "INVALID_INPUT"

    station_bad_inline = client.post(
        "/tools/call",
        json={"tool": "os_net.station_log", "stationId": "AMER", "inlineMaxBytes": 0},
    )
    assert station_bad_inline.status_code == 400
    assert station_bad_inline.json()["code"] == "INVALID_INPUT"

    monkeypatch.setattr(
        os_net.client,
        "get_bytes",
        lambda _url, _params=None: (200, {"contentType": "text/plain", "content": "not-bytes"}),
        raising=True,
    )
    station_bad_bytes = client.post(
        "/tools/call",
        json={"tool": "os_net.station_log", "stationId": "AMER"},
    )
    assert station_bad_bytes.status_code == 500
    assert station_bad_bytes.json()["code"] == "INTEGRATION_ERROR"


def test_os_net_and_tiles_resource_and_error_paths(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from tools import os_net, os_tiles_ota

    def fake_write(prefix: str, payload: dict):
        return {
            "resourceUri": f"resource://mcp-geo/os-exports/{prefix}.json",
            "bytes": 55,
            "sha256": "abc",
            "path": "/tmp/os-net.json",
        }

    monkeypatch.setattr(
        os_net.client,
        "get_bytes",
        lambda _url, _params=None: (200, {"contentType": "text/plain", "content": b"x" * 5000}),
        raising=True,
    )
    monkeypatch.setattr(os_net, "write_resource_payload", fake_write, raising=True)
    station_resource = client.post(
        "/tools/call",
        json={
            "tool": "os_net.station_log",
            "stationId": "AMER",
            "delivery": "auto",
            "inlineMaxBytes": 1,
        },
    )
    assert station_resource.status_code == 200
    assert station_resource.json()["delivery"] == "resource"

    monkeypatch.setattr(
        os_tiles_ota.client,
        "get_json",
        lambda _url, _params=None: (503, {"isError": True, "code": "UPSTREAM_CONNECT_ERROR"}),
        raising=True,
    )
    tilematrixsets = client.post("/tools/call", json={"tool": "os_tiles_ota.tilematrixsets"})
    assert tilematrixsets.status_code == 503
    assert tilematrixsets.json()["code"] == "UPSTREAM_CONNECT_ERROR"

    conformance = client.post("/tools/call", json={"tool": "os_tiles_ota.conformance"})
    assert conformance.status_code == 503
    assert conformance.json()["code"] == "UPSTREAM_CONNECT_ERROR"


def test_os_features_collections_branch_paths(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from tools import os_features

    monkeypatch.setattr(
        os_features.client,
        "get_json",
        lambda _url, _params=None: (500, {"isError": True, "code": "OS_API_ERROR"}),
        raising=True,
    )
    status, body = os_features._features_collections({})
    assert status == 501
    assert body["code"] == "OS_API_ERROR"

    monkeypatch.setattr(
        os_features.client,
        "get_json",
        lambda _url, _params=None: (200, []),
        raising=True,
    )
    status, body = os_features._features_collections({})
    assert status == 500
    assert body["code"] == "INTEGRATION_ERROR"

    def fake_get_json(_url: str, _params=None):
        return 200, {
            "collections": [
                {"id": "trn-roadlink-1", "title": "Road Links"},
                {"id": "trn-roadlink-x"},
                {"id": "trn-roadlink-2", "description": "Latest"},
                {"id": "   "},
                "skip",
            ]
        }

    monkeypatch.setattr(os_features.client, "get_json", fake_get_json, raising=True)
    status, body = os_features._features_collections({"q": "road"})
    assert status == 200
    assert body["count"] == 3
    assert body["latestByBaseId"]["trn-roadlink"] == "trn-roadlink-2"
