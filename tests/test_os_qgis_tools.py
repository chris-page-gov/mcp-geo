from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from server.main import app

client = TestClient(app)


def test_os_qgis_vector_tile_profile_inline_success() -> None:
    resp = client.post(
        "/tools/call",
        json={"tool": "os_qgis.vector_tile_profile", "style": "OS_VTS_3857_Light"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["delivery"] == "inline"
    profile = body["profile"]
    assert profile["kind"] == "qgis_vector_tile_profile"
    assert profile["srs"] == 3857
    assert profile["connection"]["proxyTileTemplate"].startswith("/maps/vector/vts/tile/")
    assert profile["styleAssets"]["qmlPath"].endswith("OS_VTS_3857_Light.qml")


def test_os_qgis_vector_tile_profile_invalid_style() -> None:
    resp = client.post(
        "/tools/call",
        json={"tool": "os_qgis.vector_tile_profile", "style": "NOT_A_STYLE"},
    )
    assert resp.status_code == 400
    body = resp.json()
    assert body["code"] == "INVALID_INPUT"


def test_os_qgis_vector_tile_profile_resource_delivery(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from tools import os_qgis

    def fake_write_resource_payload(prefix: str, payload: dict):
        return {
            "resourceUri": f"resource://mcp-geo/os-exports/{prefix}.json",
            "bytes": 123,
            "sha256": "abc123",
            "path": "/tmp/os-qgis-profile.json",
        }

    monkeypatch.setattr(
        os_qgis,
        "write_resource_payload",
        fake_write_resource_payload,
        raising=True,
    )
    resp = client.post(
        "/tools/call",
        json={
            "tool": "os_qgis.vector_tile_profile",
            "style": "OS_VTS_3857_Light",
            "delivery": "auto",
            "inlineMaxBytes": 1,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["delivery"] == "resource"
    assert body["resourceUri"].startswith("resource://mcp-geo/os-exports/")


def test_os_qgis_vector_tile_profile_without_styles_submodule(
    monkeypatch,
) -> None:  # type: ignore[no-untyped-def]
    from tools import os_qgis

    monkeypatch.setattr(
        os_qgis,
        "_STYLE_ROOT",
        Path("/tmp/mcp-geo-missing-styles-submodule"),
        raising=True,
    )
    resp = client.post(
        "/tools/call",
        json={
            "tool": "os_qgis.vector_tile_profile",
            "style": "OS_VTS_3857_Light",
            "srs": 3857,
        },
    )
    assert resp.status_code == 200
    profile = resp.json()["profile"]
    assert "OS_VTS_3857_Light" in profile["availableStyles"]


def test_os_qgis_geopackage_descriptor_inline_and_invalid() -> None:
    invalid = client.post(
        "/tools/call",
        json={
            "tool": "os_qgis.export_geopackage_descriptor",
            "sourceResourceUri": "https://example.com/x.json",
        },
    )
    assert invalid.status_code == 400
    assert invalid.json()["code"] == "INVALID_INPUT"

    ok = client.post(
        "/tools/call",
        json={
            "tool": "os_qgis.export_geopackage_descriptor",
            "sourceResourceUri": "resource://mcp-geo/os-exports/demo.json",
            "layerName": "roads",
        },
    )
    assert ok.status_code == 200
    body = ok.json()
    assert body["delivery"] == "inline"
    descriptor = body["descriptor"]
    assert descriptor["kind"] == "qgis_geopackage_descriptor"
    assert descriptor["source"]["resourceUri"] == "resource://mcp-geo/os-exports/demo.json"
    assert descriptor["qgis"]["uri"].endswith("|layername=roads")


def test_os_qgis_geopackage_descriptor_resource(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from tools import os_qgis

    def fake_write_resource_payload(prefix: str, payload: dict):
        return {
            "resourceUri": f"resource://mcp-geo/os-exports/{prefix}.json",
            "bytes": 321,
            "sha256": "def456",
            "path": "/tmp/os-qgis-descriptor.json",
        }

    monkeypatch.setattr(
        os_qgis,
        "write_resource_payload",
        fake_write_resource_payload,
        raising=True,
    )
    resp = client.post(
        "/tools/call",
        json={
            "tool": "os_qgis.export_geopackage_descriptor",
            "sourceResourceUri": "resource://mcp-geo/ons-exports/demo.json",
            "delivery": "resource",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["delivery"] == "resource"
    assert body["resourceUri"].startswith("resource://mcp-geo/os-exports/")


def test_os_qgis_geopackage_descriptor_sanitizes_prefix_component(
    monkeypatch,
) -> None:  # type: ignore[no-untyped-def]
    from tools import os_qgis

    seen_prefixes: list[str] = []

    def fake_write_resource_payload(prefix: str, payload: dict):
        seen_prefixes.append(prefix)
        return {
            "resourceUri": f"resource://mcp-geo/os-exports/{prefix}.json",
            "bytes": 111,
            "sha256": "abc",
            "path": "/tmp/os-qgis-descriptor.json",
        }

    monkeypatch.setattr(
        os_qgis,
        "write_resource_payload",
        fake_write_resource_payload,
        raising=True,
    )
    resp = client.post(
        "/tools/call",
        json={
            "tool": "os_qgis.export_geopackage_descriptor",
            "sourceResourceUri": "resource://mcp-geo/os-exports/demo.json",
            "layerName": "roads/main",
            "delivery": "resource",
        },
    )
    assert resp.status_code == 200
    assert seen_prefixes
    assert "/" not in seen_prefixes[0]
