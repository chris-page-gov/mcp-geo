from typing import Any, Dict, List
from fastapi.testclient import TestClient
from server.main import app


client = TestClient(app)


def test_admin_boundaries_resource_unavailable():
    r1 = client.get("/resources/read", params={"name": "admin_boundaries"})
    assert r1.status_code == 404


def test_resources_list_excludes_sample_resources():
    r = client.get("/resources/list")
    assert r.status_code == 200
    body: Dict[str, Any] = r.json()
    resources: List[Any] = body["resources"]
    names = {res.get("name") for res in resources if isinstance(res, dict)}
    assert "admin_boundaries" not in names
