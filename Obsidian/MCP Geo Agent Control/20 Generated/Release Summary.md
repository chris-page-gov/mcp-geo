---
type: "agent_control_generated"
title: "Release Summary"
vault_role: "agent_control"
generated: true
protected: true
updated: "2026-04-14"
source_paths:
  - "CHANGELOG.md"
  - "RELEASE_NOTES/"
---
# Release Summary

## Unreleased highlights
- Added the switchable Obsidian agent-control implementation plan at `Plans/PLAN-Obsidian-agent-control-plane.md`, plus the tracked rollout baseline in `PROGRESS.MD` and `CONTEXT.md`. The new workstream will build a dedicated control vault under `Obsidian/MCP Geo Agent Control/`, keep `AGENTS.md` as the root entrypoint, and compare `classic` versus `obsidian` instruction profiles with a dedicated smoke pack.
- Added the checked-in unattended multi-client remediation implementation plan at `Plans/PLAN-Unattended-multiclient-eval-remediation.md`, plus lockstep tracking updates in `CONTEXT.md` and `PROGRESS.MD` so the repo records the readiness-first redesign before the harness changes land.
- Added a built-in readiness probe to `scripts/unattended_client_eval.py` together with `--readiness-only`, per-track readiness artifact files, and structured attempt records labelled as `readiness`, `recovery`, or `capability`.
- Added unattended multi-client host evaluation tooling via `scripts/unattended_client_eval.py`, focused regression coverage in `tests/test_unattended_client_eval.py`, and the first captured aggregate report at `docs/reports/client_interop_unattended/client_interop_unattended_eval_2026-04-12.{md,json}`.
- Added the first full remediation-era four-client rerun artifacts at `docs/reports/client_interop_unattended/client_interop_unattended_eval_2026-04-13.{md,json}` plus the per-track readiness JSON outputs. That run confirmed Codex CLI, Gemini CLI, and Claude Code CLI now complete the full eight-scenario pack while VS Code Agent still needs additional remediation before closure.
- Added the VS Code closure evidence at `docs/reports/client_interop_unattended/client_interop_unattended_eval_2026-04-13_vscode_canary_v17_no_primer.{md,json}` and `docs/reports/client_interop_unattended/client_interop_unattended_eval_2026-04-13_vscode_full_v18_no_primer.{md,json}`, plus the final rewritten canonical four-client rerun at `docs/reports/client_interop_unattended/client_interop_unattended_eval_2026-04-13.{md,json}` showing all four clients ready and all four completing the full eight-scenario pack.

## Recent tagged releases
- `0.7.0 (2026-03-16)`
- `0.6.0 (2026-03-08)`
- `0.5.0 (2026-03-04)`
- `0.4.0 (2026-02-25)`
