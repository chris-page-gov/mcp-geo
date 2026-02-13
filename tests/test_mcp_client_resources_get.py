import json, subprocess, sys
from pathlib import Path

CLIENT = Path(__file__).resolve().parent.parent / "scripts" / "mcp_client.py"


def test_client_resources_get_skills():
    proc = subprocess.Popen([sys.executable, str(CLIENT), "resources/read", '{"name":"skills_getting_started"}'], stdout=subprocess.PIPE)
    out, _ = proc.communicate(timeout=10)
    decoded = out.decode()
    payload = json.loads(decoded)
    contents = payload["response"]["result"]["contents"]
    assert contents[0]["uri"] == "skills://mcp-geo/getting-started"
