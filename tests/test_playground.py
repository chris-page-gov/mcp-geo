from fastapi.testclient import TestClient
from server.main import app

client = TestClient(app)

def test_playground_transcript_initial():
    resp = client.get("/playground/transcript")
    assert resp.status_code == 200
    assert "transcript" in resp.json()


def test_playground_invalid_payload():
    # Missing required 'tool'
    resp = client.post("/playground/tool_call", json={"input": {"x": 1}})
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("isError")
    assert body.get("code") == "INVALID_INPUT"


def test_playground_record_and_prune():
    # Add more than MAX_TRANSCRIPT entries to trigger prune branch
    for i in range(25):
        resp = client.post(
            "/playground/tool_call",
            json={"tool": f"tool{i}", "input": {"n": i}, "output": {"ok": True}},
        )
        assert resp.json().get("ok") is True
    resp2 = client.get("/playground/transcript")
    data = resp2.json()["transcript"]
    assert len(data) <= 10  # ensured by prune logic
