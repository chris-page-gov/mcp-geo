import json, subprocess, sys
from pathlib import Path

CLIENT = Path(__file__).resolve().parent.parent / "scripts" / "mcp_client.py"

def test_client_resources_read_twice():
    p1 = subprocess.Popen([sys.executable, str(CLIENT), "resources/read", '{"name":"admin_boundaries","limit":1}'], stdout=subprocess.PIPE)
    out1, _ = p1.communicate(timeout=10)
    data1 = json.loads(out1.decode())
    contents1 = data1["response"]["result"]["contents"]
    payload1 = json.loads(contents1[0]["text"])
    assert payload1["name"] == "admin_boundaries"
    p2 = subprocess.Popen([sys.executable, str(CLIENT), "resources/read", '{"name":"admin_boundaries","limit":1}'], stdout=subprocess.PIPE)
    out2, _ = p2.communicate(timeout=10)
    data2 = json.loads(out2.decode())
    contents2 = data2["response"]["result"]["contents"]
    payload2 = json.loads(contents2[0]["text"])
    assert payload2["name"] == "admin_boundaries"
