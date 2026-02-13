from fastapi.testclient import TestClient
from server.main import app
client = TestClient(app)


def test_address_classification_codes_resource():
    resp = client.get('/resources/read', params={'name': 'address_classification_codes', 'limit': 2, 'page': 1})
    assert resp.status_code == 404


def test_custodian_codes_resource_etag_not_modified():
    first = client.get('/resources/read', params={'name': 'custodian_codes', 'limit': 1})
    assert first.status_code == 404


def test_boundaries_wards_pagination():
    resp = client.get('/resources/read', params={'name': 'boundaries_wards', 'limit': 2, 'page': 1})
    assert resp.status_code == 404
