from fastapi.testclient import TestClient
from server.main import app
client = TestClient(app)


def test_admin_boundaries_resource_unavailable():
    r = client.get("/resources/read", params={"name": "admin_boundaries"})
    assert r.status_code == 404


def test_resources_list_pagination_advances_page_token():
    first = client.get("/resources/list", params={"limit": 5, "page": 1})
    assert first.status_code == 200
    first_body = first.json()
    assert len(first_body["resources"]) <= 5
    assert first_body["nextPageToken"] is not None

    second = client.get("/resources/list", params={"limit": 5, "page": 2})
    assert second.status_code == 200
    second_body = second.json()
    first_uris = {row.get("uri") for row in first_body["resources"] if isinstance(row, dict)}
    second_uris = {row.get("uri") for row in second_body["resources"] if isinstance(row, dict)}
    assert first_uris
    assert second_uris
    assert first_uris != second_uris


def test_resources_describe_matches_list_shape():
    listed = client.get("/resources/list", params={"limit": 20, "page": 1})
    described = client.get("/resources/describe", params={"limit": 20, "page": 1})
    assert listed.status_code == 200
    assert described.status_code == 200
    list_uris = {row.get("uri") for row in listed.json()["resources"] if isinstance(row, dict)}
    describe_uris = {row.get("uri") for row in described.json()["resources"] if isinstance(row, dict)}
    assert list_uris == describe_uris
