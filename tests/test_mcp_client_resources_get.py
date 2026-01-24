import json, subprocess, sys
from pathlib import Path

CLIENT = Path(__file__).resolve().parent.parent / "scripts" / "mcp_client.py"


def test_client_resources_get_admin_boundaries():
    proc = subprocess.Popen([sys.executable, str(CLIENT), "resources/read", '{"name":"admin_boundaries","limit":1}'], stdout=subprocess.PIPE)
    out, _ = proc.communicate(timeout=10)
    decoded = out.decode()
    payload = json.loads(decoded)
    contents = payload["response"]["result"]["contents"]
    body = json.loads(contents[0]["text"])
    assert body["name"] == "admin_boundaries"
