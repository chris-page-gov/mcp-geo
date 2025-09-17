import json, subprocess, sys
from pathlib import Path

CLIENT = Path(__file__).resolve().parent.parent / "scripts" / "mcp_client.py"

def test_client_if_none_match_flag():
    # First fetch to capture ETag
    p1 = subprocess.Popen([sys.executable, str(CLIENT), "resources/get", '{"name":"admin_boundaries","limit":1}'], stdout=subprocess.PIPE)
    out1, _ = p1.communicate(timeout=10)
    data1 = json.loads(out1.decode())
    etag = data1["response"]["result"].get("etag")
    assert etag
    # Second fetch with flag
    p2 = subprocess.Popen([sys.executable, str(CLIENT), "resources/get", "--if-none-match", etag, '{"name":"admin_boundaries","limit":1}'], stdout=subprocess.PIPE)
    out2, _ = p2.communicate(timeout=10)
    data2 = json.loads(out2.decode())
    # Response may be compacted if notModified
    r2 = data2["response"]
    assert r2.get("notModified") is True