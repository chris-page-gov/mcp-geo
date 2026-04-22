from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.integration
_LIVE_SKIP_REASON = "Set MCP_GEO_RUN_LIVE_OS_NGD=1 for live OS NGD tests"
_TRANSIENT_UPSTREAM_CODES = {"UPSTREAM_CONNECT_ERROR", "CIRCUIT_OPEN"}
_LIVE_QUERY_BBOX = [-0.1300, 51.5000, -0.1295, 51.5005]
_EXPECTED_BASES = {
    "buildings": "bld-fts-buildingpart",
    "road_links": "trn-ntwk-roadlink",
    "path_links": "trn-ntwk-pathlink",
    "postcode_unit_areas": "asu-gbpcd-postcodeunitarea",
    "postcode_unit_points": "asu-gbpcd-postcodeunitpoint",
    "bus_lanes": "trn-ntwk-buslane",
    "cycle_lanes": "trn-ntwk-cyclelane",
}
_LIVE_LAYER_QUERIES = {
    "buildings": "buildings",
    "road_links": "trn-ntwk-roadlink",
    "path_links": "trn-ntwk-pathlink",
    "postcode_unit_areas": "postcode_unit_areas",
    "postcode_unit_points": "postcode_unit_points",
    "bus_lanes": "bus_lanes",
    "cycle_lanes": "cycle_lanes",
}


def _live_enabled() -> bool:
    return os.getenv("MCP_GEO_RUN_LIVE_OS_NGD") == "1"


def _reset_live_os_client() -> None:
    from server.config import settings
    from tools import os_common, os_map

    os_common.client.api_key = settings.OS_API_KEY
    os_common.client.auth_mode = os_common._normalize_auth_mode(settings.OS_API_AUTH_MODE)
    os_common.client.access_token = settings.OS_API_ACCESS_TOKEN
    os_map._NGD_COLLECTION_CACHE["stored_at"] = 0.0
    os_map._NGD_COLLECTION_CACHE["latest_by_base"] = {}


@pytest.mark.skipif(not _live_enabled(), reason=_LIVE_SKIP_REASON)
def test_live_os_ngd_spring_2026_collections_and_existing_bases(client) -> None:  # type: ignore[no-untyped-def]
    _reset_live_os_client()

    resp = client.post("/tools/call", json={"tool": "os_features.collections"})
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("live") is True
    latest = body.get("latestByBaseId")
    assert isinstance(latest, dict)

    missing = sorted(base for base in _EXPECTED_BASES.values() if base not in latest)
    assert missing == []


@pytest.mark.skipif(not _live_enabled(), reason=_LIVE_SKIP_REASON)
def test_live_os_ngd_queries_existing_and_spring_2026_layers(client) -> None:  # type: ignore[no-untyped-def]
    _reset_live_os_client()

    transient: dict[str, str] = {}
    for layer_id, expected_base in _EXPECTED_BASES.items():
        requested_collection = _LIVE_LAYER_QUERIES[layer_id]
        resp = client.post(
            "/tools/call",
            json={
                "tool": "os_features.query",
                "collection": requested_collection,
                "bbox": _LIVE_QUERY_BBOX,
                "limit": 1,
                "includeGeometry": False,
            },
        )
        body = resp.json()
        if resp.status_code != 200:
            code = body.get("code") if isinstance(body, dict) else None
            if code in _TRANSIENT_UPSTREAM_CODES:
                transient[layer_id] = str(body.get("message", code))
                continue
            pytest.fail(f"{layer_id}: status={resp.status_code} body={body}")
        assert body["collection"].startswith(f"{expected_base}-")
        assert body["requestedCollection"] == requested_collection
        assert body["live"] is True
    if transient:
        pytest.skip(f"OS API transient item endpoint failure(s): {sorted(transient)}")


@pytest.mark.skipif(not _live_enabled(), reason=_LIVE_SKIP_REASON)
def test_live_os_api_key_header_auth_mode_reaches_collections() -> None:
    from server.config import settings
    from tools.os_common import OSClient

    api_key = str(settings.OS_API_KEY or "").strip()
    assert api_key
    client_obj = OSClient(api_key=api_key, auth_mode="header", retries=1)

    status, body = client_obj.get_json(f"{client_obj.base_ngd_features}/collections")
    assert status == 200
    assert isinstance(body.get("collections"), list)
