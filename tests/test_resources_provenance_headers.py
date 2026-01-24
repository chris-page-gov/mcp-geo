from fastapi.testclient import TestClient
from server.main import app
client = TestClient(app)

def test_admin_boundaries_cache_control_and_provenance():
    resp = client.get('/resources/read', params={'name': 'admin_boundaries', 'limit': 1})
    assert resp.status_code == 404


def test_code_list_cache_control():
    resp = client.get('/resources/read', params={'name': 'address_classification_codes', 'limit': 1})
    assert resp.status_code == 404
