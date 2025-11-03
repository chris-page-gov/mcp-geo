from fastapi.testclient import TestClient
from server.main import app

client = TestClient(app)

def test_admin_boundaries_cache_control_and_provenance():
    resp = client.get('/resources/get', params={'name': 'admin_boundaries', 'limit': 1})
    assert resp.status_code == 200
    assert resp.headers.get('Cache-Control') == 'public, max-age=300'
    prov = resp.json().get('provenance', {})
    assert 'retrievedAt' in prov


def test_code_list_cache_control():
    resp = client.get('/resources/get', params={'name': 'address_classification_codes', 'limit': 1})
    assert resp.status_code == 200
    assert resp.headers.get('Cache-Control') == 'public, max-age=86400'
    prov = resp.json().get('provenance', {})
    assert 'retrievedAt' in prov
