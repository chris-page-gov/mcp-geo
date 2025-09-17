from fastapi.testclient import TestClient
from server.main import app

client = TestClient(app)

def test_resources_list_includes_ons_observations():
    resp = client.get('/resources/list')
    assert resp.status_code == 200
    names = [r['name'] for r in resp.json()['resources']]
    assert 'ons_observations' in names


def test_get_ons_observations_basic():
    resp = client.get('/resources/get?name=ons_observations&limit=2&page=1')
    assert resp.status_code == 200
    body = resp.json()
    assert body['name'] == 'ons_observations'
    assert 'observations' in body['data']
    assert len(body['data']['observations']) == 2
    assert body['data']['nextPageToken'] == '2'
    assert 'ETag' in resp.headers


def test_get_ons_observations_second_page_and_etag_cache():
    # First page to get etag variant
    first = client.get('/resources/get?name=ons_observations&limit=2&page=2')
    assert first.status_code == 200
    etag = first.headers.get('ETag')
    assert etag
    cached = client.get('/resources/get?name=ons_observations&limit=2&page=2', headers={'If-None-Match': etag})
    assert cached.status_code == 304


def test_get_ons_observations_final_page_no_next():
    # There are 5 observations; with limit 2 page 3 is final (obs 5)
    final = client.get('/resources/get?name=ons_observations&limit=2&page=3')
    assert final.status_code == 200
    body = final.json()
    assert body['data']['nextPageToken'] is None


def test_get_ons_observations_filter_geography():
    resp = client.get('/resources/get?name=ons_observations&geography=K02000001')
    assert resp.status_code == 200
    body = resp.json()
    assert all(o['geography'] == 'K02000001' for o in body['data']['observations'])


def test_get_ons_observations_filter_measure():
    resp = client.get('/resources/get?name=ons_observations&measure=chained_volume_measure')
    assert resp.status_code == 200
    body = resp.json()
    assert all(o['measure'] == 'chained_volume_measure' for o in body['data']['observations'])
