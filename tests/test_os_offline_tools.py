from __future__ import annotations

import hashlib
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
    from tools import os_offline

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
    pack_path = os_offline._OFFLINE_PACKS_DIR / "gb_transport_mbtiles.mbtiles"
    expected_hash = f"sha256:{hashlib.sha256(pack_path.read_bytes()).hexdigest()}"
    assert body["export_handoff"]["hash"] == expected_hash


def test_os_offline_get_export_hash_stable_across_bbox() -> None:
    first = client.post(
        "/tools/call",
        json={
            "tool": "os_offline.get",
            "packId": "gb_transport_mbtiles",
            "bbox": [-0.18, 51.49, -0.05, 51.54],
        },
    )
    second = client.post(
        "/tools/call",
        json={
            "tool": "os_offline.get",
            "packId": "gb_transport_mbtiles",
            "bbox": [-1.0, 50.0, 0.2, 52.0],
        },
    )
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["export_handoff"]["hash"] == second.json()["export_handoff"]["hash"]


def test_os_offline_pack_hash_prefers_declared_sha256() -> None:
    from tools import os_offline

    declared = "a" * 64
    digest = os_offline._pack_hash({"sha256": f"sha256:{declared}"})
    assert digest == f"sha256:{declared}"


def test_os_offline_pack_hash_uses_digest_cache(monkeypatch, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    from tools import os_offline

    packs_dir = tmp_path / "offline_packs"
    packs_dir.mkdir(parents=True, exist_ok=True)
    pack_file = packs_dir / "cached.pmtiles"
    pack_file.write_bytes(b"PACK-DATA")

    monkeypatch.setattr(os_offline, "_OFFLINE_PACKS_DIR", packs_dir)
    os_offline._PACK_SHA256_CACHE.clear()

    calls = {"count": 0}

    def _fake_sha256_file(path: Path) -> str:
        calls["count"] += 1
        return "b" * 64

    monkeypatch.setattr(os_offline, "_sha256_file", _fake_sha256_file)
    pack = {"resourceUri": "resource://mcp-geo/offline-packs/cached.pmtiles"}
    assert os_offline._pack_hash(pack) == f"sha256:{'b' * 64}"
    assert os_offline._pack_hash(pack) == f"sha256:{'b' * 64}"
    assert calls["count"] == 1


def test_os_offline_pack_hash_falls_back_to_stable_id_hash() -> None:
    from tools import os_offline

    digest = os_offline._pack_hash({"id": "pack-no-uri-no-declared-hash"})
    assert digest.startswith("sha256:")
    assert len(digest.split(":", 1)[1]) == 64


def test_os_offline_rejects_empty_pack_id() -> None:
    descriptor = client.post(
        "/tools/call",
        json={"tool": "os_offline.descriptor", "packId": ""},
    )
    assert descriptor.status_code == 400
    assert descriptor.json()["code"] == "INVALID_INPUT"

    getter = client.post(
        "/tools/call",
        json={"tool": "os_offline.get", "packId": ""},
    )
    assert getter.status_code == 400
    assert getter.json()["code"] == "INVALID_INPUT"


def test_os_offline_catalog_helpers_cover_invalid_shapes(monkeypatch, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    from tools import os_offline

    invalid_shape = tmp_path / "invalid_shape.json"
    invalid_shape.write_text("[]", encoding="utf-8")
    monkeypatch.setattr(os_offline, "_OFFLINE_CATALOG_PATH", invalid_shape)
    status, catalog = os_offline._load_catalog()
    assert status == 500
    assert catalog is None
    assert os_offline._catalog_packs({"packs": "not-a-list"}) == []


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
