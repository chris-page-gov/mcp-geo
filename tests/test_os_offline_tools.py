from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from server.main import app

client = TestClient(app)


def test_os_offline_descriptor_lists_catalog_packs() -> None:
    resp = client.post("/tools/call", json={"tool": "os_offline.descriptor"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["mode"] == "offline_catalog"
    assert isinstance(body.get("packs"), list) and body["packs"]
    assert body["fallbackOrder"] == ["map_card", "overlay_bundle", "export_handoff"]


def test_os_offline_descriptor_single_pack_lookup() -> None:
    resp = client.post(
        "/tools/call",
        json={"tool": "os_offline.descriptor", "packId": "gb_basemap_light_pmtiles"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["pack"]["id"] == "gb_basemap_light_pmtiles"


def test_os_offline_get_returns_handoff_contracts() -> None:
    resp = client.post(
        "/tools/call",
        json={
            "tool": "os_offline.get",
            "packId": "gb_transport_mbtiles",
            "bbox": [-0.18, 51.49, -0.05, 51.54],
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["map_card"]["type"] == "map_card"
    assert body["overlay_bundle"]["type"] == "overlay_bundle"
    assert body["export_handoff"]["type"] == "export_handoff"
    assert body["export_handoff"]["format"] == "mbtiles"


def test_os_offline_get_invalid_bbox_and_unknown_pack() -> None:
    bad_bbox = client.post(
        "/tools/call",
        json={"tool": "os_offline.get", "packId": "gb_transport_mbtiles", "bbox": [1, 2, 3]},
    )
    assert bad_bbox.status_code == 400
    assert bad_bbox.json()["code"] == "INVALID_INPUT"

    missing_pack = client.post(
        "/tools/call",
        json={"tool": "os_offline.get", "packId": "does-not-exist"},
    )
    assert missing_pack.status_code == 404
    assert missing_pack.json()["code"] == "NOT_FOUND"


def test_os_offline_missing_catalog(monkeypatch, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    from tools import os_offline

    missing_catalog = tmp_path / "missing_catalog.json"
    monkeypatch.setattr(os_offline, "_OFFLINE_CATALOG_PATH", missing_catalog)

    desc = client.post("/tools/call", json={"tool": "os_offline.descriptor"})
    assert desc.status_code == 404
    assert desc.json()["code"] == "NOT_FOUND"

    get_resp = client.post("/tools/call", json={"tool": "os_offline.get", "packId": "x"})
    assert get_resp.status_code == 404
    assert get_resp.json()["code"] == "NOT_FOUND"


def test_os_offline_catalog_load_failure_returns_500(monkeypatch, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    from tools import os_offline

    broken_catalog = tmp_path / "broken_catalog.json"
    broken_catalog.write_text("{not-json", encoding="utf-8")
    monkeypatch.setattr(os_offline, "_OFFLINE_CATALOG_PATH", broken_catalog)

    desc = client.post("/tools/call", json={"tool": "os_offline.descriptor"})
    assert desc.status_code == 500
    assert desc.json()["code"] == "CATALOG_LOAD_FAILED"

    get_resp = client.post("/tools/call", json={"tool": "os_offline.get", "packId": "x"})
    assert get_resp.status_code == 500
    assert get_resp.json()["code"] == "CATALOG_LOAD_FAILED"
