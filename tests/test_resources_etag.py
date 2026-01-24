from typing import Any, Dict, List
from fastapi.testclient import TestClient
from server.main import app
from tests.helpers import resource_json


client = TestClient(app)


def test_admin_boundaries_get_etag_and_304():
    r1 = client.get("/resources/read", params={"name": "admin_boundaries"})
    assert r1.status_code == 200
    etag = r1.headers.get("ETag")
    assert etag
    # Now conditional
    r2 = client.get("/resources/read", params={"name": "admin_boundaries"}, headers={"If-None-Match": etag})
    assert r2.status_code == 304
    # ETag header still present
    assert r2.headers.get("ETag") == etag


def test_resources_list_includes_provenance_fields():
    r = client.get("/resources/list")
    assert r.status_code == 200
    body: Dict[str, Any] = r.json()
    resources: List[Any] = body["resources"]
    admin_entry: Dict[str, Any] | None = None
    for res in resources:
        if isinstance(res, dict) and "name" in res and res["name"] == "admin_boundaries":
            admin_entry = res  # type: ignore[assignment]
            break
    assert admin_entry is not None
    assert "version" in admin_entry
    assert "source" in admin_entry
    assert "license" in admin_entry


def test_admin_boundaries_payload_has_provenance():
    r = client.get("/resources/read", params={"name": "admin_boundaries"})
    assert r.status_code == 200
    payload = resource_json(r)
    assert "provenance" in payload
    prov = payload["provenance"]
    assert prov.get("version")
    assert prov.get("license") == "Open Government Licence v3"
