from __future__ import annotations

import json

from fastapi.testclient import TestClient

from server.main import app
from tests.helpers import resource_contents

client = TestClient(app)

PACK_RESOURCE_URIS = {
    "resource://mcp-geo/okf-discovery-descriptor",
    "resource://mcp-geo/okf-discovery-manifest",
    "resource://mcp-geo/okf-discovery-overview",
    "resource://mcp-geo/okf-discovery-records",
    "resource://mcp-geo/okf-discovery-spatial-index",
    "resource://mcp-geo/okf-discovery-mcp-bindings",
}


def test_okf_discovery_resources_are_listed_and_readable() -> None:
    listed = client.get("/resources/list", params={"limit": 200, "page": 1})
    assert listed.status_code == 200
    resources = listed.json()["resources"]
    uris = {entry["uri"] for entry in resources}
    assert PACK_RESOURCE_URIS <= uris
    assert "ui://mcp-geo/okf-discovery" in uris

    descriptor_response = client.get(
        "/resources/read",
        params={"uri": "resource://mcp-geo/okf-discovery-descriptor"},
    )
    assert descriptor_response.status_code == 200
    descriptor = json.loads(resource_contents(descriptor_response)[0]["text"])
    assert descriptor["schema"] == "okf-explorer-large-corpus.v1"
    assert descriptor["extensions"]["okf-geospatial.v1"]["entrypoint"] == "spatial_index"
    assert descriptor["extensions"]["okf-mcp-binding.v1"]["entrypoint"] == "mcp_bindings"
    descriptor_delivery = descriptor["delivery"]["artifacts"]["descriptor"]
    assert descriptor_delivery["mcp_resource_uri"] in PACK_RESOURCE_URIS
    assert descriptor_delivery["http_path"] == "/okf-discovery/data/descriptor.json"


def test_okf_discovery_raw_data_route_is_allowlisted_and_cacheable() -> None:
    response = client.get("/okf-discovery/data/descriptor.json")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.json()["kind"] == "okf-large-corpus"
    etag = response.headers["etag"]

    cached = client.get(
        "/okf-discovery/data/descriptor.json",
        headers={"If-None-Match": etag},
    )
    assert cached.status_code == 304

    missing = client.get("/okf-discovery/data/not-a-pack-file.json")
    traversal = client.get("/okf-discovery/data/..%2Fdescriptor.json")
    assert missing.status_code == 404
    assert traversal.status_code == 404


def test_okf_discovery_ui_and_short_route_are_served() -> None:
    short_route = client.get("/okf-discovery", follow_redirects=False)
    assert short_route.status_code == 307
    assert short_route.headers["location"] == "/ui/okf-discovery"

    page = client.get("/ui/okf-discovery")
    assert page.status_code == 200
    assert page.headers["content-type"].startswith("text/html")
    assert "Find the data behind the map" in page.text
    assert 'href="/ui/vendor/maplibre-gl.css"' in page.text
    assert 'src="/ui/shared/okf_discovery.js"' in page.text

    css = client.get("/ui/shared/okf_discovery.css")
    javascript = client.get("/ui/shared/okf_discovery.js")
    assert css.status_code == 200
    assert css.headers["content-type"].startswith("text/css")
    assert javascript.status_code == 200
    assert javascript.headers["content-type"].startswith("application/javascript")
    assert "event.source !== window.parent" in javascript.text
    for uri in (
        "resource://mcp-geo/okf-discovery-records",
        "resource://mcp-geo/okf-discovery-spatial-index",
        "resource://mcp-geo/okf-discovery-mcp-bindings",
    ):
        assert uri in PACK_RESOURCE_URIS
        assert uri in javascript.text
        assert client.get("/resources/read", params={"uri": uri}).status_code == 200


def test_okf_discovery_routes_share_http_auth_boundary(monkeypatch) -> None:
    monkeypatch.setenv("MCP_HTTP_AUTH_MODE", "static_bearer")
    monkeypatch.setenv("MCP_HTTP_AUTH_TOKEN", "okf-demo-token")

    for path in (
        "/okf-discovery",
        "/okf-discovery/data/descriptor.json",
        "/ui/shared/okf_discovery.js",
    ):
        unauthorized = client.get(path, follow_redirects=False)
        assert unauthorized.status_code == 401

    headers = {"Authorization": "Bearer okf-demo-token"}
    redirect = client.get("/okf-discovery", headers=headers, follow_redirects=False)
    data = client.get("/okf-discovery/data/descriptor.json", headers=headers)
    javascript = client.get("/ui/shared/okf_discovery.js", headers=headers)
    assert redirect.status_code == 307
    assert data.status_code == 200
    assert javascript.status_code == 200


def test_generated_mcp_binding_round_trips_as_a_request(client, monkeypatch) -> None:
    from server.config import settings
    from tools import os_common

    monkeypatch.setattr(settings, "OS_API_KEY", "", raising=False)
    monkeypatch.setattr(os_common.client, "api_key", "")
    binding_payload = client.get("/okf-discovery/data/mcp-bindings.json").json()
    binding = next(
        row
        for row in binding_payload["bindings"]
        if row["tool_name"] == "os_places.by_postcode"
    )
    request = binding["request_template"]

    initialized = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": "init-okf", "method": "initialize", "params": {}},
    )
    session_id = initialized.headers["mcp-session-id"]
    response = client.post(
        "/mcp",
        headers={"mcp-session-id": session_id},
        json=request,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == request["id"]
    assert payload["result"]["isError"] is True
    assert payload["result"]["data"]["code"] == "NO_API_KEY"
