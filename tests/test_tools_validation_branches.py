from fastapi.testclient import TestClient

from server.main import app

client = TestClient(app)

def test_os_names_find_missing_text():
    resp = client.post('/tools/call', json={'tool': 'os_names.find', 'text': ''})
    assert resp.status_code == 400
    assert resp.json()['code'] == 'INVALID_INPUT'

def test_os_names_nearest_bad_coords():
    resp = client.post('/tools/call', json={'tool': 'os_names.nearest', 'lat': 'x', 'lon': 'y'})
    assert resp.status_code == 400
    assert resp.json()['code'] == 'INVALID_INPUT'

def test_os_places_search_missing_text():
    resp = client.post('/tools/call', json={'tool': 'os_places.search', 'text': ''})
    assert resp.status_code == 400
    assert resp.json()['code'] == 'INVALID_INPUT'

def test_os_places_by_uprn_missing():
    resp = client.post('/tools/call', json={'tool': 'os_places.by_uprn', 'uprn': ''})
    assert resp.status_code == 400
    assert resp.json()['code'] == 'INVALID_INPUT'

def test_os_places_nearest_bad_coords():
    resp = client.post('/tools/call', json={'tool': 'os_places.nearest', 'lat': 'a', 'lon': 'b'})
    assert resp.status_code == 400
    assert resp.json()['code'] == 'INVALID_INPUT'

def test_os_places_within_bad_bbox_type():
    resp = client.post('/tools/call', json={'tool': 'os_places.within', 'bbox': 'not-a-list'})
    assert resp.status_code == 400
    assert resp.json()['code'] == 'INVALID_INPUT'

def test_os_places_within_bad_bbox_numeric():
    resp = client.post('/tools/call', json={'tool': 'os_places.within', 'bbox': ['a','b','c','d']})
    assert resp.status_code == 400
    assert resp.json()['code'] == 'INVALID_INPUT'

def test_os_maps_render_bad_bbox():
    resp = client.post('/tools/call', json={'tool': 'os_maps.render', 'bbox': [0,1,2]})
    assert resp.status_code == 400
    assert resp.json()['code'] == 'INVALID_INPUT'

def test_os_maps_render_bad_bbox_numeric():
    resp = client.post('/tools/call', json={'tool': 'os_maps.render', 'bbox': ['a','b','c','d']})
    assert resp.status_code == 400
    assert resp.json()['code'] == 'INVALID_INPUT'

def test_os_linked_ids_get_missing_identifier():
    resp = client.post('/tools/call', json={'tool': 'os_linked_ids.get', 'identifier': ''})
    assert resp.status_code == 400
    assert resp.json()['code'] == 'INVALID_INPUT'
