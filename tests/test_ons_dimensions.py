from fastapi.testclient import TestClient
from server.main import app

client = TestClient(app)

def test_dimensions_requires_dataset_params():
    resp = client.post('/tools/call', json={'tool': 'ons_data.dimensions'})
    assert resp.status_code == 400
    err = resp.json()
    assert err['isError'] and err['code'] == 'INVALID_INPUT'
