---
type: "agent_control_generated"
title: "Recent Verification Summary"
vault_role: "agent_control"
generated: true
protected: true
updated: "2026-04-14"
source_paths:
  - "CONTEXT.md"
  - "PROGRESS.MD"
---
# Recent Verification Summary

## Verification status highlights
- Latest OWASP MCP strict validator run: `./scripts/validate-owasp-mcp-local` on 2026-03-13 (`compliant`, score `100.0`, `0` required/minimum-bar failures, empty remediation backlog, baseline outputs committed under `security/owasp_mcp/baseline/`).
- Latest strict test run: `./scripts/pytest-local -q -m "not integration"` on 2026-03-13
- Latest live harness run: `RUN_LIVE_API_TESTS=1 ./.venv/bin/python -m tests.evaluation.harness --include-os-api --include-ons-live`
- Latest full tool operability aggregation:
- Latest playground UI test run: `npm --prefix /Users/crpage/repos/mcp-geo/playground run test` (6 passed) on 2026-02-11.

## Recent recorded validation commands
- `scripts/validate_agent_control.py`
- `./scripts/ruff-local scripts/obsidian_cli.py scripts/validate_agent_control.py tests/test_obsidian_cli.py`
- `./scripts/pytest-local -q --no-cov tests/test_obsidian_cli.py`
- `python3 -m py_compile scripts/obsidian_cli.py scripts/validate_agent_control.py tests/test_obsidian_cli.py`
- `python3 scripts/validate_agent_control.py --skip-cli`
- `./scripts/ruff-local scripts/switch_agent_mode.py scripts/validate_agent_control.py tests/test_switch_agent_mode.py tests/test_obsidian_cli.py`
