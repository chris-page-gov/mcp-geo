from fastapi.testclient import TestClient
from server.main import app

client = TestClient(app)


def test_admin_boundaries_filter_level():
    r = client.get("/resources/get", params={"name": "admin_boundaries", "level": "MSOA"})
    assert r.status_code == 200
    body = r.json()
    assert body["count"] >= 1
    feats = body["data"]["features"]
    assert all(f["level"] == "MSOA" for f in feats)


def test_admin_boundaries_filter_name_contains():
    r = client.get("/resources/get", params={"name": "admin_boundaries", "nameContains": "Westminster"})
    assert r.status_code == 200
    body = r.json()
    feats = body["data"]["features"]
    assert any("Westminster" in f["name"] for f in feats)
    # Ensure filtered count reported
    assert body["count"] == body["data"]["total"]


def test_admin_boundaries_pagination_two_pages():
    # Force small page size to exercise paging even with small dataset
    r1 = client.get("/resources/get", params={"name": "admin_boundaries", "limit": 2, "page": 1})
    assert r1.status_code == 200
    b1 = r1.json()
    assert b1["data"]["limit"] == 2
    assert b1["data"]["page"] == 1
    assert b1["data"]["nextPageToken"] == "2"
    # Second page
    r2 = client.get("/resources/get", params={"name": "admin_boundaries", "limit": 2, "page": 2})
    assert r2.status_code == 200
    b2 = r2.json()
    assert b2["data"]["page"] == 2
    # Distinct feature sets expected across pages (unless dataset smaller than limit*2)
    ids1 = {f["id"] for f in b1["data"]["features"]}
    ids2 = {f["id"] for f in b2["data"]["features"]}
    assert ids1.isdisjoint(ids2) or len(ids1.union(ids2)) <= len(ids1)


def test_admin_boundaries_variant_etag_changes():
    r_base = client.get("/resources/get", params={"name": "admin_boundaries"})
    r_lvl = client.get("/resources/get", params={"name": "admin_boundaries", "level": "MSOA"})
    assert r_base.status_code == 200 and r_lvl.status_code == 200
    assert r_base.json()["etag"] != r_lvl.json()["etag"]


def test_admin_boundaries_gzip_negotiation():
    r = client.get(
        "/resources/get",
        params={"name": "admin_boundaries"},
        headers={"Accept-Encoding": "gzip"},
    )
    assert r.status_code == 200
    # Starlette/ FastAPI should apply gzip since payload > minimum_size
    assert r.headers.get("Content-Encoding") == "gzip"