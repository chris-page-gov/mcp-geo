from fastapi.testclient import TestClient
from server.main import app

client = TestClient(app)

def _create_filter():
    resp = client.post("/tools/call", json={"tool": "ons_data.create_filter", "geography": "K02000001", "measure": "chained_volume_measure", "timeRange": "2023 Q1-2023 Q2"})
    assert resp.status_code in (200, 201)
    return resp.json()["filterId"]


def test_filter_output_csv():
    fid = _create_filter()
    resp = client.post("/tools/call", json={"tool": "ons_data.get_filter_output", "filterId": fid, "format": "CSV"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["format"] == "CSV"
    assert data["contentType"] == "text/csv"
    assert data.get("dataBase64") not in (None, "")
    assert data["rows"] == 2  # Q1 and Q2
    assert data["columns"] >= 4  # geography, measure, seasonalAdjustment, time, value


def test_filter_output_xlsx():
    fid = _create_filter()
    resp = client.post("/tools/call", json={"tool": "ons_data.get_filter_output", "filterId": fid, "format": "XLSX"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["format"] == "XLSX"
    assert data["contentType"].startswith("application/vnd.openxmlformats-officedocument")
    assert data.get("dataHex") not in (None, "")
    assert data["rows"] == 2
    assert data["columns"] >= 4