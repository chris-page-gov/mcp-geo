from fastapi.testclient import TestClient
from server.main import app
from tests.helpers import resource_json

client = TestClient(app)


def test_address_classification_codes_resource():
    resp = client.get('/resources/read', params={'name': 'address_classification_codes', 'limit': 2, 'page': 1})
    assert resp.status_code == 200
    body = resource_json(resp)
    assert body['name'] == 'address_classification_codes'
    assert 'items' in body['data'] and body['data']['limit'] == 2


def test_custodian_codes_resource_etag_not_modified():
    first = client.get('/resources/read', params={'name': 'custodian_codes', 'limit': 1})
    assert first.status_code == 200
    etag = first.headers.get('ETag')
    assert etag
    second = client.get('/resources/read', params={'name': 'custodian_codes', 'limit': 1}, headers={'If-None-Match': etag})
    assert second.status_code == 304


def test_boundaries_wards_pagination():
    resp = client.get('/resources/read', params={'name': 'boundaries_wards', 'limit': 2, 'page': 1})
    assert resp.status_code == 200
    body = resource_json(resp)
    assert body['count'] >= 4
    assert len(body['data']['items']) == 2
