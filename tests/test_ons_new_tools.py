from fastapi.testclient import TestClient
from server.config import settings
from server.main import app

client = TestClient(app)

def test_get_observation_success():
    resp = client.post(
        "/tools/call",
        json={
            "tool": "ons_data.get_observation",
            "geography": "K02000001",
            "measure": "chained_volume_measure",
            "time": "2023 Q2",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body['observation']['time'] == '2023 Q2'
    assert body['live'] is False


def test_get_observation_not_found():
    resp = client.post(
        "/tools/call",
        json={
            "tool": "ons_data.get_observation",
            "geography": "K02000001",
            "measure": "chained_volume_measure",
            "time": "1999 Q1",
        },
    )
    assert resp.status_code == 404
    err = resp.json()
    assert err['isError'] and err['code'] == 'NO_OBSERVATION'


def test_create_filter_and_get_output():
    create = client.post(
        "/tools/call",
        json={
            "tool": "ons_data.create_filter",
            "geography": "K02000001",
            "measure": "chained_volume_measure",
            "timeRange": "2023 Q1-2023 Q2",
        },
    )
    assert create.status_code == 201
    fid = create.json()['filterId']
    get = client.post(
        "/tools/call",
        json={"tool": "ons_data.get_filter_output", "filterId": fid},
    )
    assert get.status_code == 200
    data = get.json()['data']
    assert 'results' in data and data['count'] >= 2


def test_filter_output_invalid_format():
    create = client.post("/tools/call", json={"tool": "ons_data.create_filter"})
    fid = create.json()['filterId']
    # CSV is now valid; expect success
    get_csv = client.post(
        "/tools/call",
        json={
            "tool": "ons_data.get_filter_output",
            "filterId": fid,
            "format": "CSV",
        },
    )
    assert get_csv.status_code == 200
    # Unsupported format triggers INVALID_INPUT
    get_bad = client.post(
        "/tools/call",
        json={
            "tool": "ons_data.get_filter_output",
            "filterId": fid,
            "format": "PDF",
        },
    )
    assert get_bad.status_code == 400
    err = get_bad.json()
    assert err['isError'] and err['code'] == 'INVALID_INPUT'


def test_search_query(monkeypatch):
    from tools import ons_search
    def fake_get_json(url, params):
        return 200, {
            "items": [
                {
                    "id": "population-estimates",
                    "title": "Population estimates",
                    "description": "Annual population estimates",
                    "keywords": ["population"],
                    "state": "published",
                    "links": {
                        "self": {
                            "href": "https://api.beta.ons.gov.uk/v1/datasets/population-estimates"
                        }
                    },
                }
            ],
            "count": 1,
            "offset": params.get("offset", 0),
            "limit": params.get("limit", 20),
            "total_count": 1,
        }
    monkeypatch.setattr(settings, "ONS_SEARCH_LIVE_ENABLED", True, raising=False)
    fake_client = type(
        "C",
        (),
        {
            "base_api": "https://api.beta.ons.gov.uk/v1",
            "get_json": staticmethod(fake_get_json),
        },
    )()
    monkeypatch.setattr(ons_search, "_SEARCH_CLIENT", fake_client)
    resp = client.post(
        "/tools/call",
        json={"tool": "ons_search.query", "term": "population"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body['count'] == 1
    assert body['results'][0]['id'] == "population-estimates"
    assert body.get('live') is True


def test_search_query_missing_term():
    resp = client.post("/tools/call", json={"tool": "ons_search.query"})
    assert resp.status_code == 400
    err = resp.json()
    assert err['isError'] and err['code'] == 'INVALID_INPUT'


def test_codes_list_and_options():
    lst = client.post("/tools/call", json={"tool": "ons_codes.list"})
    assert lst.status_code == 200
    dims = lst.json()['dimensions']
    assert 'geography' in dims
    opts = client.post(
        "/tools/call",
        json={"tool": "ons_codes.options", "dimension": "geography"},
    )
    assert opts.status_code == 200
    body = opts.json()
    assert body['dimension'] == 'geography' and len(body['options']) >= 1


def test_codes_options_unknown_dimension():
    opts = client.post(
        "/tools/call",
        json={"tool": "ons_codes.options", "dimension": "unknown_dim"},
    )
    assert opts.status_code in (400,404)
    err = opts.json()
    assert err['isError'] and err['code'] == 'INVALID_INPUT'
