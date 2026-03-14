from __future__ import annotations

import json

from fastapi.testclient import TestClient

from server.main import app

client = TestClient(app)


def test_os_peat_layers_lists_direct_and_proxy() -> None:
    resp = client.post("/tools/call", json={"tool": "os_peat.layers"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["layerCount"] >= 2
    kinds = {str(layer.get("kind")) for layer in body["layers"]}
    assert "direct" in kinds
    assert "proxy" in kinds


def test_os_peat_layers_filter_kind() -> None:
    resp = client.post("/tools/call", json={"tool": "os_peat.layers", "kind": "direct"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["layerCount"] >= 1
    assert all(layer.get("kind") == "direct" for layer in body["layers"])


def test_os_peat_evidence_paths_requires_aoi() -> None:
    resp = client.post("/tools/call", json={"tool": "os_peat.evidence_paths"})
    assert resp.status_code == 400
    assert resp.json()["code"] == "INVALID_INPUT"

    resp = client.post(
        "/tools/call",
        json={"tool": "os_peat.evidence_paths", "bbox": [-2.95, 53.78, -2.4, 54.15], "limit": True},
    )
    assert resp.status_code == 400
    assert resp.json()["code"] == "INVALID_INPUT"


def test_os_peat_evidence_paths_with_bbox() -> None:
    resp = client.post(
        "/tools/call",
        json={
            "tool": "os_peat.evidence_paths",
            "bbox": [-2.95, 53.78, -2.4, 54.15],
            "limit": 25,
            "resultType": "hits",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["aoi"]["source"] == "input_bbox"
    assert body["evidenceSummary"]["directLayerIds"]
    assert body["evidenceSummary"]["proxyLayerIds"]
    assert body["confidence"]["level"] in {"medium", "high"}
    assert body["caveats"]

    proxy_layers = [layer for layer in body["layers"] if layer.get("kind") == "proxy"]
    assert proxy_layers
    query_plan = proxy_layers[0].get("queryPlan")
    assert isinstance(query_plan, dict)
    assert query_plan["tool"] == "os_features.query"
    assert query_plan["parameters"]["bbox"] == [-2.95, 53.78, -2.4, 54.15]


def test_os_peat_evidence_paths_with_landscape_id() -> None:
    resp = client.post(
        "/tools/call",
        json={
            "tool": "os_peat.evidence_paths",
            "landscapeId": "aonb-forest-of-bowland",
            "limit": 25,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["aoi"]["source"] == "os_landscape.get"
    assert body["aoi"]["landscapeId"] == "aonb-forest-of-bowland"


def test_os_peat_evidence_paths_unknown_landscape() -> None:
    resp = client.post(
        "/tools/call",
        json={
            "tool": "os_peat.evidence_paths",
            "landscapeId": "missing-landscape",
        },
    )
    assert resp.status_code == 404
    assert resp.json()["code"] == "NOT_FOUND"


def test_peat_layers_resource_is_readable() -> None:
    resp = client.get(
        "/resources/read",
        params={"uri": "resource://mcp-geo/peat-layers-england"},
    )
    assert resp.status_code == 200
    body = resp.json()
    text = body["contents"][0]["text"]
    parsed = json.loads(text)
    assert parsed["scope"] == "england"
    assert any(layer.get("id") == "england-peat-map" for layer in parsed.get("layers", []))
