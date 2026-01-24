from typing import Any, Dict, Tuple

from fastapi.testclient import TestClient
from server.main import app

client = TestClient(app)


def _mock_live(monkeypatch) -> None:
    from tools import ons_common

    def fake_get_json(url: str, params: Dict[str, Any] | None = None, use_cache: bool = True) -> Tuple[int, Dict[str, Any]]:  # noqa: ARG001
        return 200, {"observations": [{"geography": "K02000001", "measure": "GDPV", "time": "2023 Q1", "value": 1}, {"geography": "K02000001", "measure": "GDPV", "time": "2023 Q2", "value": 2}], "total": 2}

    monkeypatch.setattr(ons_common.client, "get_json", fake_get_json)


def _create_filter(monkeypatch):
    _mock_live(monkeypatch)
    resp = client.post("/tools/call", json={"tool": "ons_data.create_filter", "dataset": "gdp", "edition": "time-series", "version": "1", "geography": "K02000001", "measure": "GDPV", "timeRange": "2023 Q1"})
    assert resp.status_code in (200, 201)
    return resp.json()["filterId"]


def test_filter_output_csv(monkeypatch):
    fid = _create_filter(monkeypatch)
    resp = client.post("/tools/call", json={"tool": "ons_data.get_filter_output", "filterId": fid, "format": "CSV"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["format"] == "CSV"
    assert data["contentType"] == "text/csv"
    assert data.get("dataBase64") not in (None, "")
    assert data["rows"] == 2
    assert data["columns"] >= 4


def test_filter_output_xlsx(monkeypatch):
    fid = _create_filter(monkeypatch)
    resp = client.post("/tools/call", json={"tool": "ons_data.get_filter_output", "filterId": fid, "format": "XLSX"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["format"] == "XLSX"
    assert data["contentType"].startswith("application/vnd.openxmlformats-officedocument")
    assert data.get("dataHex") not in (None, "")
    assert data["rows"] == 2
    assert data["columns"] >= 4
