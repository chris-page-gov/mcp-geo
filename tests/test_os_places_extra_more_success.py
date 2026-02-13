import pytest
from fastapi.testclient import TestClient
from server.main import app

def _fake_body(uprn: str):
    return {
        "results": [
            {
                "DPA": {
                    "UPRN": uprn,
                    "ADDRESS": f"Addr {uprn}",
                    "LAT": 50.0,
                    "LNG": -1.0,
                    "CLASS": "R",
                }
            }
        ]
    }

def test_os_places_by_uprn_success(monkeypatch):
    from tools import os_places_extra
    captured = {}
    def fake_get_json(url, params):
        captured.update(params)
        return 200, _fake_body(params["uprn"])  # echo uprn
    fake_client = type(
        "C",
        (),
        {
            "get_json": staticmethod(fake_get_json),
            "base_places": "http://example",
        },
    )()
    monkeypatch.setattr(os_places_extra, "client", fake_client)
    client = TestClient(app)
    resp = client.post(
        "/tools/call",
        json={"tool": "os_places.by_uprn", "uprn": "12345"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["result"]["uprn"] == "12345"
    assert captured["output_srs"] == "WGS84"

def test_os_places_nearest_success(monkeypatch):
    from tools import os_places_extra
    captured = {}
    def fake_get_json(url, params):
        captured.update(params)
        return 200, _fake_body("N1")
    fake_client = type(
        "C",
        (),
        {
            "get_json": staticmethod(fake_get_json),
            "base_places": "http://example",
        },
    )()
    monkeypatch.setattr(os_places_extra, "client", fake_client)
    client = TestClient(app)
    resp = client.post(
        "/tools/call",
        json={"tool": "os_places.nearest", "lat": 51.0, "lon": -0.1},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["results"][0]["uprn"] == "N1"
    assert captured["srs"] == "WGS84"
    assert captured["output_srs"] == "WGS84"
    assert captured["point"] == "51.0,-0.1"

def test_os_places_within_success(monkeypatch):
    from tools import os_places_extra
    captured = {}
    def fake_get_json(url, params):
        captured.update(params)
        return 200, _fake_body("W1")
    fake_client = type(
        "C",
        (),
        {
            "get_json": staticmethod(fake_get_json),
            "base_places": "http://example",
        },
    )()
    monkeypatch.setattr(os_places_extra, "client", fake_client)
    client = TestClient(app)
    resp = client.post(
        "/tools/call",
        json={
            "tool": "os_places.within",
            "bbox": [-1.2, 50.1, -1.198, 50.102],
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["results"][0]["uprn"] == "W1"
    assert captured["srs"] == "WGS84"
    assert captured["output_srs"] == "WGS84"
    bbox_vals = [float(val) for val in captured["bbox"].split(",")]
    assert bbox_vals == pytest.approx([50.1, -1.2, 50.102, -1.198], abs=1e-6)

def test_os_places_within_tiles_large_bbox(monkeypatch):
    from tools import os_places_extra
    calls = []
    counter = {"i": 0}
    def fake_get_json(url, params):
        counter["i"] += 1
        calls.append(params)
        return 200, _fake_body(f"T{counter['i']}")
    fake_client = type(
        "C",
        (),
        {
            "get_json": staticmethod(fake_get_json),
            "base_places": "http://example",
        },
    )()
    monkeypatch.setattr(os_places_extra, "client", fake_client)
    client = TestClient(app)
    resp = client.post(
        "/tools/call",
        json={
            "tool": "os_places.within",
            "bbox": [-0.15, 51.50, -0.12, 51.52],
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["provenance"]["bboxMode"] == "tiled"
    assert data["provenance"]["tileCount"] == len(calls)
    assert len(data["results"]) == len(calls)
    for params in calls:
        assert params["srs"] == "WGS84"
        assert params["output_srs"] == "WGS84"
        bbox_vals = [float(val) for val in params["bbox"].split(",")]
        assert bbox_vals[0] > 0
        assert bbox_vals[1] < 0

def test_os_places_within_clamps_huge_bbox(monkeypatch):
    from tools import os_places_extra
    calls = []
    def fake_get_json(url, params):
        calls.append(params)
        return 200, _fake_body("C1")
    fake_client = type(
        "C",
        (),
        {
            "get_json": staticmethod(fake_get_json),
            "base_places": "http://example",
        },
    )()
    monkeypatch.setattr(os_places_extra, "client", fake_client)
    client = TestClient(app)
    resp = client.post(
        "/tools/call",
        json={"tool": "os_places.within", "bbox": [-5.0, 49.0, 2.0, 58.0]},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["provenance"]["bboxMode"] == "clamped"
    assert data["provenance"]["tileCount"] == 1
    assert data["provenance"]["originalTileCount"] > 1
    assert len(calls) == 1
    bbox_vals = [float(val) for val in calls[0]["bbox"].split(",")]
    assert calls[0]["output_srs"] == "WGS84"
    assert bbox_vals[0] > 0
    assert bbox_vals[1] < 0
    assert (bbox_vals[3] - bbox_vals[1]) < 7.0
    assert (bbox_vals[2] - bbox_vals[0]) < 9.0
