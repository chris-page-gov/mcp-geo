from __future__ import annotations

import os
import subprocess
from pathlib import Path

FAKE_CODEX = """#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$*" >> "$CODEX_LOG"
if [[ "$1" == "mcp" && "$2" == "get" && "$3" == "os-ngd-api" ]]; then
  exit 1
fi
if [[ "$1" == "mcp" && "$2" == "get" && "$3" == "--json" && "$4" == "mcp-geo" ]]; then
  cat <<'JSON'
{"name":"mcp-geo","transport":{"type":"stdio","command":"python3","args":["/Users/crpage/repos/mcp-geo/scripts/claude-mcp-local"],"env":{}}}
JSON
  exit 0
fi
if [[ "$1" == "mcp" && "$2" == "get" && "$3" == "--json" && "$4" == "openaiDeveloperDocs" ]]; then
  exit 1
fi
if [[ "$1" == "mcp" && ( "$2" == "remove" || "$2" == "rm" ) ]]; then
  exit 0
fi
if [[ "$1" == "mcp" && "$2" == "add" ]]; then
  exit 0
fi
exit 1
"""


def test_devcontainer_setup_registers_codex_launcher(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    log_path = tmp_path / "codex.log"
    codex_path = fake_bin / "codex"
    codex_path.write_text(FAKE_CODEX, encoding="utf-8")
    codex_path.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env['PATH']}"
    env["CODEX_LOG"] = str(log_path)
    env["OS_API_KEY"] = "os-secret"
    env["ONS_API_KEY"] = "unused-ons-secret"

    subprocess.run(
        ["bash", str(repo_root / "scripts" / "devcontainer_mcp_setup.sh")],
        cwd=repo_root,
        env=env,
        check=True,
    )

    log_text = log_path.read_text(encoding="utf-8")
    add_lines = [line for line in log_text.splitlines() if line.startswith("mcp add")]
    expected_launcher = repo_root / "scripts" / "codex-mcp-local"
    expected_variants = {str(expected_launcher), expected_launcher.as_posix()}
    launcher_posix = expected_launcher.as_posix()
    if len(launcher_posix) >= 3 and launcher_posix[1:3] == ":/":
        expected_variants.add(f"/{launcher_posix[0].lower()}{launcher_posix[2:]}")
    assert any(
      any(variant in line for variant in expected_variants)
      for line in add_lines
    )
    assert any("--env OS_API_KEY=os-secret" in line for line in add_lines)
    assert not any("ONS_API_KEY" in line for line in add_lines)
    assert any(
        "openaiDeveloperDocs --url https://developers.openai.com/mcp" in line for line in add_lines
    )
    assert not any("claude-mcp-local" in line for line in add_lines)
