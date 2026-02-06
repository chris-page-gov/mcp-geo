from typing import Any, Dict, Tuple

from fastapi.testclient import TestClient

from server.main import app


client = TestClient(app)


def test_nomis_live_disabled(monkeypatch):
    from server import config

    monkeypatch.setattr(config.settings, "NOMIS_LIVE_ENABLED", False)
    resp = client.post("/tools/call", json={"tool": "nomis.datasets"})
    assert resp.status_code == 501
    assert resp.json()["code"] == "LIVE_DISABLED"
    resp = client.post("/tools/call", json={"tool": "nomis.concepts"})
    assert resp.status_code == 501
    resp = client.post("/tools/call", json={"tool": "nomis.codelists"})
    assert resp.status_code == 501
    resp = client.post("/tools/call", json={"tool": "nomis.query", "dataset": "NM_1"})
    assert resp.status_code == 501


def test_nomis_query_success(monkeypatch):
    from tools import nomis_common

    def fake_get_json(  # noqa: ARG001
        url: str,
        params: Dict[str, Any] | None = None,
        use_cache: bool = True,
    ) -> Tuple[int, Dict[str, Any]]:
        return 200, {"dataset": "NM_1_1", "value": 123}

    monkeypatch.setattr(nomis_common.client, "get_json", fake_get_json)
    resp = client.post(
        "/tools/call",
        json={"tool": "nomis.query", "dataset": "NM_1_1", "params": {"geography": "TYPE499"}},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["live"] is True
    assert body["data"]["value"] == 123


def test_nomis_query_error_surface(monkeypatch):
    from tools import nomis_common

    def fake_get_json(  # noqa: ARG001
        url: str,
        params: Dict[str, Any] | None = None,
        use_cache: bool = True,
    ) -> Tuple[int, Dict[str, Any]]:
        return 200, {"error": "Cannot create query"}

    monkeypatch.setattr(nomis_common.client, "get_json", fake_get_json)
    resp = client.post(
        "/tools/call",
        json={"tool": "nomis.query", "dataset": "NM_1_1", "params": {"geography": "TYPE499"}},
    )
    assert resp.status_code == 400
    body = resp.json()
    assert body["code"] == "NOMIS_QUERY_ERROR"


def test_nomis_datasets_and_concepts(monkeypatch):
    from tools import nomis_common
    from server.config import settings

    def fake_get_json(url: str, params=None, use_cache=True):  # noqa: ARG001
        return 200, {"items": []}

    monkeypatch.setattr(settings, "NOMIS_LIVE_ENABLED", True, raising=False)
    monkeypatch.setattr(nomis_common.client, "get_json", fake_get_json)
    resp = client.post("/tools/call", json={"tool": "nomis.datasets"})
    assert resp.status_code == 200
    resp = client.post("/tools/call", json={"tool": "nomis.concepts"})
    assert resp.status_code == 200
    resp = client.post("/tools/call", json={"tool": "nomis.codelists"})
    assert resp.status_code == 200


def test_nomis_invalid_inputs(monkeypatch):
    from server.config import settings

    monkeypatch.setattr(settings, "NOMIS_LIVE_ENABLED", True, raising=False)
    resp = client.post("/tools/call", json={"tool": "nomis.datasets", "dataset": 123})
    assert resp.status_code == 400
    resp = client.post("/tools/call", json={"tool": "nomis.datasets", "format": "xml"})
    assert resp.status_code == 400
    resp = client.post("/tools/call", json={"tool": "nomis.concepts", "concept": 123})
    assert resp.status_code == 400
    resp = client.post("/tools/call", json={"tool": "nomis.concepts", "format": "xml"})
    assert resp.status_code == 400
    resp = client.post("/tools/call", json={"tool": "nomis.codelists", "codelist": 123})
    assert resp.status_code == 400
    resp = client.post("/tools/call", json={"tool": "nomis.codelists", "format": "xml"})
    assert resp.status_code == 400
    resp = client.post("/tools/call", json={"tool": "nomis.query", "dataset": "NM_1", "format": "xml"})
    assert resp.status_code == 400
    resp = client.post("/tools/call", json={"tool": "nomis.query", "dataset": "NM_1", "params": "bad"})
    assert resp.status_code == 400


def test_nomis_extract_error_list():
    from tools import nomis_data

    assert nomis_data._extract_nomis_error({"errors": ["a", "b"]}) == "a; b"
    assert nomis_data._extract_nomis_error({"error": "boom"}) == "boom"
    assert nomis_data._extract_nomis_error("bad") is None


def test_nomis_upstream_error_passthrough(monkeypatch):
    from tools import nomis_common
    from server.config import settings

    def fake_get_json(url: str, params=None, use_cache=True):  # noqa: ARG001
        return 503, {"isError": True, "code": "NOMIS_API_ERROR", "message": "boom"}

    monkeypatch.setattr(settings, "NOMIS_LIVE_ENABLED", True, raising=False)
    monkeypatch.setattr(nomis_common.client, "get_json", fake_get_json)

    resp = client.post("/tools/call", json={"tool": "nomis.datasets"})
    assert resp.status_code == 503
    resp = client.post("/tools/call", json={"tool": "nomis.concepts"})
    assert resp.status_code == 503
    resp = client.post("/tools/call", json={"tool": "nomis.codelists"})
    assert resp.status_code == 503
    resp = client.post("/tools/call", json={"tool": "nomis.query", "dataset": "NM_1"})
    assert resp.status_code == 503


def test_nomis_error_payloads(monkeypatch):
    from tools import nomis_common
    from server.config import settings

    def fake_get_json(url: str, params=None, use_cache=True):  # noqa: ARG001
        return 200, {"error": "boom"}

    monkeypatch.setattr(settings, "NOMIS_LIVE_ENABLED", True, raising=False)
    monkeypatch.setattr(nomis_common.client, "get_json", fake_get_json)

    resp = client.post("/tools/call", json={"tool": "nomis.datasets"})
    assert resp.status_code == 502
    resp = client.post("/tools/call", json={"tool": "nomis.concepts"})
    assert resp.status_code == 502
    resp = client.post("/tools/call", json={"tool": "nomis.codelists"})
    assert resp.status_code == 502


def test_nomis_query_requires_dataset(monkeypatch):
    from server.config import settings

    monkeypatch.setattr(settings, "NOMIS_LIVE_ENABLED", True, raising=False)
    resp = client.post("/tools/call", json={"tool": "nomis.query", "dataset": ""})
    assert resp.status_code == 400
