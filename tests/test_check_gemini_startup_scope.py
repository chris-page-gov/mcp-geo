from __future__ import annotations

import os
import subprocess
from pathlib import Path


def test_check_gemini_startup_scope_detects_scoped_discovery(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    wrapper = tmp_path / "fake-wrapper.sh"
    wrapper.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
cat >/dev/null
if [[ -n "${MCP_TOOLS_DEFAULT_TOOLSET:-}" ]]; then
  echo '{"jsonrpc":"2.0","id":1,"result":{"tools":[{"name":"tool.one"}]}}'
else
  cat <<'EOF'
{"jsonrpc":"2.0","id":1,"result":{"tools":[{"name":"tool.one"},{"name":"tool.two"},{"name":"tool.three"}]}}
EOF
fi
""",
        encoding="utf-8",
    )
    wrapper.chmod(0o755)

    env = os.environ.copy()
    env["MCP_GEMINI_WRAPPER"] = str(wrapper)
    proc = subprocess.run(
        ["bash", str(repo_root / "scripts" / "check_gemini_startup_scope.sh")],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "PASS: scoped startup discovery is active" in proc.stdout
