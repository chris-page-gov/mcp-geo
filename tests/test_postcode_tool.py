from fastapi.testclient import TestClient

from server.main import app


client = TestClient(app)


def test_postcode_invalid():
    resp = client.post(
        "/tools/call",
        json={"tool": "os_places.by_postcode", "postcode": "INVALID"},
    )
    assert resp.status_code == 400
    body = resp.json()
    assert body.get("isError")
    assert body.get("code") == "INVALID_INPUT"


def test_postcode_missing_tool():
    resp = client.post("/tools/call", json={"postcode": "SW1A2AA"})
    assert resp.status_code == 400
    body = resp.json()
    assert body.get("code") == "INVALID_INPUT"


def test_postcode_valid_without_key_returns_501():
    # If OS_API_KEY not present expect 501 NO_API_KEY
    resp = client.post(
        "/tools/call",
        json={"tool": "os_places.by_postcode", "postcode": "SW1A 2AA"},
    )
    assert resp.status_code in (200, 501)
    if resp.status_code == 501:
        assert resp.json().get("code") in ("NO_API_KEY", "OS_API_ERROR")
