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
- Added the first checked-in Obsidian agent-control vault scaffold under `Obsidian/MCP Geo Agent Control/`, including curated control notes, generated digests for repo map / plans / verification / releases, the new build helper `scripts/agent_control_common.py`, the vault builder `scripts/build_agent_control_vault.py`, the manifest `data/agent_control/control_vault_manifest.json`, and focused regression coverage in `tests/test_agent_control_vault.py`.
- Added the official Obsidian CLI wrapper `scripts/obsidian_cli.py`, the control-vault validator `scripts/validate_agent_control.py`, and focused preflight coverage in `tests/test_obsidian_cli.py`. The new preflight checks the installed app version, bundled CLI binary, PATH registration, and vault read/search behavior, and it now fails locally with a clear `OBSIDIAN_VERSION_TOO_OLD` prerequisite message on the current `1.8.7` desktop app.
- Added the switcher `scripts/switch_agent_mode.py --mode classic|obsidian` plus the active-mode validation checks in `scripts/validate_agent_control.py` and focused coverage in `tests/test_switch_agent_mode.py`. The repo now keeps the committed baseline in `classic` mode while the switcher can locally rewrite the root instruction files into `obsidian` mode and restore the tracked baseline from `HEAD` for repeatable evaluation.
- Added the checked-in unattended multi-client remediation implementation plan at `Plans/PLAN-Unattended-multiclient-eval-remediation.md`, plus lockstep tracking updates in `CONTEXT.md` and `PROGRESS.MD` so the repo records the readiness-first redesign before the harness changes land.
- Added a built-in readiness probe to `scripts/unattended_client_eval.py` together with `--readiness-only`, per-track readiness artifact files, and structured attempt records labelled as `readiness`, `recovery`, or `capability`.

## Recent tagged releases
- `0.7.0 (2026-03-16)`
- `0.6.0 (2026-03-08)`
- `0.5.0 (2026-03-04)`
- `0.4.0 (2026-02-25)`
