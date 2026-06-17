# MCP Geo Context

Last updated: 2026-06-17
Owner: @chris-page-gov

Read this file at session start. Keep it to active, cross-branch handoff facts
only. Move history and playbooks to `docs/agent_context/`.

## Project Snapshot

- FastAPI MCP server for UK geospatial tooling.
- Entrypoints: `server/main.py` for HTTP and `server/stdio_adapter.py` for STDIO.
- Runtime tool modules: `tools/`.
- Static MCP resources: `resources/`.
- MCP-Apps widgets: `ui/`.
- Spec package: `docs/spec_package/README.md`.

## Active Workstreams

| Workstream | Branch / Location | Status | Notes |
| --- | --- | --- | --- |
| Parish/PARNCP, OS Names routing, and HoC MSOA display names | `codex/parish-pんarncp-names-support` | PR #86 active | Public parish level is `PARISH`; raw PARNCP fields remain `PARNCP25CD`, `PARNCP25NM`, `PARNCP25NW`. HoC MSOA names are display labels only and must not replace ONS/RGC `currentName`. Geography-level support now needs to be implemented through `server/geography_levels.py` and checked across router, cache, admin lookup, widgets, STDIO, exports, docs, and OWASP manifests. |
| MCP 2026-07-28 RC alignment | `/Users/crpage/tmp/mcp-geo-rc-align`, branch `codex/mcp-2026-rc-alignment` | separate worktree | Stable runtime remains `2025-11-25`; RC behavior is opt-in via `MCP_2026_RC_ENABLED=1` or `MCP_PROTOCOL_2026_07_28_ENABLED=1`. Ledger: `Plans/PLAN-MCP-2026-07-28-RC-alignment.md`. |
| MCP-Apps postcode picker | backlog | pending | Needs a dedicated postcode picker using current OS postcode capability, multi-select, and optional UPRN list return mode. |
| Unattended multi-client eval | historical active caveat | needs fresh rerun | Harness remediation exists, but VS Code memory/cleanup closure needs one fresh live rerun before considering the old incident closed. |

## Current PR #86 Review Focus

The latest review comment exposed a cross-surface geography-level problem:
parish was routed to the geography selector before the selector/runtime fallback
fully understood parish. Fixes should address the class, not only the cited
line.

Required contract for this branch:

- `server/geography_levels.py` is the source of truth for level aliases, code
  inference, admin levels, selector support, stats comparison, and NOMIS
  geography-type hints.
- `PARISH` support covers civil parishes, Welsh communities, and
  non-civil-parished areas.
- MSOA `displayName` fields remain non-official labels; `name` and
  `currentName` preserve official ONS/RGC names.
- Selector-driven exports should preserve parish identity and selected-by audit
  fields when parish/PARNCP selectors are used.

Detailed checklist: `docs/agent_context/geography-extension-contract.md`.

## Validation Expectations

For the parish/MSOA PR, run at least:

```bash
./scripts/ruff-local
./scripts/mypy-local
./scripts/pytest-local -q
./scripts/validate-owasp-mcp-local
```

During development, targeted slices can use `--no-cov`, but final PR updates
should include the full gate unless there is an explicit blocker.

## Context Pointers

- Active progress ledger: `PROGRESS.MD`.
- Historical workstream summary: `docs/agent_context/historical-workstreams.md`.
- Client/review operations: `docs/agent_context/agent-operations.md`.
- Geography extension contract: `docs/agent_context/geography-extension-contract.md`.
- OpenAI Codex best-practice references: `docs/agent_context/README.md`.

## Durable Decisions

- Prefer current OpenAI developer docs via the documentation MCP server when
  current Codex/OpenAI guidance is needed. Treat `docs/vendor/openai/` as a
  deprecated legacy fallback.
- Do not assume Docker-backed host clients share one PostGIS database. Normal
  wrappers use isolated named-volume sidecars unless shared devcontainer reuse
  is explicitly enabled.
- Use branch-local changelog fragments for parallel PR work. Fold fragments into
  canonical `CHANGELOG.md` only during release or integration.
- Do not store machine-specific secrets or API keys in repo files.
