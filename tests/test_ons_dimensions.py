from fastapi.testclient import TestClient
from server.main import app

client = TestClient(app)

def test_dimensions_all():
    resp = client.post('/tools/call', json={'tool': 'ons_data.dimensions'})
    assert resp.status_code == 200
    body = resp.json()
    assert 'dimensions' in body and body['live'] is False
    assert 'geography' in body['dimensions'] and isinstance(body['dimensions']['geography'], list)


def test_dimensions_single():
    resp = client.post('/tools/call', json={'tool': 'ons_data.dimensions', 'dimension': 'time'})
    assert resp.status_code == 200
    body = resp.json()
    assert list(body['dimensions'].keys()) == ['time']


def test_dimensions_invalid():
    resp = client.post('/tools/call', json={'tool': 'ons_data.dimensions', 'dimension': 'unknown_dim'})
    assert resp.status_code == 400
    err = resp.json()
    assert err['isError'] and err['code'] == 'INVALID_INPUT'
