import json, subprocess, sys
from pathlib import Path

CLIENT = Path(__file__).resolve().parent.parent / "scripts" / "mcp_client.py"


def test_client_resources_get_admin_boundaries():
    proc = subprocess.Popen([sys.executable, str(CLIENT), "resources/get", '{"name":"admin_boundaries","limit":1}'], stdout=subprocess.PIPE)
    out, _ = proc.communicate(timeout=10)
    decoded = out.decode()
    payload = json.loads(decoded)
    assert payload["response"]["result"]["name"] == "admin_boundaries"