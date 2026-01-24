from fastapi.testclient import TestClient
from server.main import app
client = TestClient(app)


def test_admin_boundaries_resource_unavailable():
    r = client.get("/resources/read", params={"name": "admin_boundaries"})
    assert r.status_code == 404
