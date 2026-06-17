# MCP Geo Progress

Last updated: 2026-06-17

This file tracks active workstreams only. Historical summaries live in
`docs/agent_context/historical-workstreams.md`; full detail remains available in
git history and referenced plans/reports.

Legend: pending, in_progress, done, blocked

## Parish, PARNCP, OS Names, and MSOA Display Names

| Workstream | Status | Dependencies | Notes |
| --- | --- | --- | --- |
| PARISH-NAMES-1 ONS cache semantics | done | none | Added normalized `PARISH`/PARNCP aliases, code inference, parish semantic fields, migration-safe UPRN index columns, `PARISH` area summaries, and House of Commons Library 2021 MSOA display-name sidecar ingestion with provenance. |
| PARISH-NAMES-2 Admin boundary and routing support | done | PARISH-NAMES-1 | Added the `PARNCP_MAY_2025_EW_BGC` live boundary source, cache-first parish name lookup, cached parish geometry coverage, and OS Names gazetteer routing for named-place wording while preserving admin/boundary routing for generic area phrases. |
| PARISH-NAMES-3 Cross-surface parish/MSOA parity hardening | in_progress | PARISH-NAMES-1, PARISH-NAMES-2 | Centralizing geography-level metadata in `server/geography_levels.py`, aligning selector/widget/STDIO/export/NOMIS/admin/cache consumers, preserving MSOA display labels through area summaries, and adding sibling-path regressions. |
| PARISH-NAMES-4 Documentation and validation | in_progress | PARISH-NAMES-3 | Agent guidance has been split into `docs/agent_context/`; final validation must rerun Ruff, mypy, full pytest, and OWASP manifest validation before PR review is requested again. |

## MCP 2026-07-28 RC Alignment

| Workstream | Status | Dependencies | Notes |
| --- | --- | --- | --- |
| MCP-RC-0 Clean worktree and source review | done | none | Separate worktree at `/Users/crpage/tmp/mcp-geo-rc-align`; original checkout dirty edits were not touched. |
| MCP-RC-1 Submodule refresh ledger | done | MCP-RC-0 | Ledger lives in `Plans/PLAN-MCP-2026-07-28-RC-alignment.md`. |
| MCP-RC-2 Feature-gated runtime alignment | done | MCP-RC-1 | Stable runtime remains `2025-11-25`; RC behavior is opt-in. |
| MCP-RC-3 Documentation and wiki lockstep | done | MCP-RC-1, MCP-RC-2 | Spec tracking and docs were updated with final validation in that worktree. |

## Backlog Watchlist

| Workstream | Status | Notes |
| --- | --- | --- |
| MCP-Apps postcode picker | pending | Build `os_apps.render_postcode_picker` / `ui://mcp-geo/postcode-picker` with seed-postcode discovery, multi-select, structured postcode output, and optional UPRN payload mode. |
| Welsh PARNCP alternate-name lookup | pending | Extend parish/admin lookup so Welsh community names from `PARNCP25NW` are searchable alongside `PARNCP25NM`, returned as `nameWelsh` or equivalent metadata, and covered across live fallback, cache-backed lookup, and future geography display-name changes. Origin: PR #86 review comment on `tools/admin_lookup.py`. |
| ONS geo refresh external storage | pending | Continue optional mirror/search-root design for bulky ONS raw artifacts and boundary runs. |
| LandIS family expansion | pending | Normalize and surface NATMAP join model before deciding whether scale-specific NATMAP products, AUGER, or Soil Catalogue layers need first-class MCP contracts. |
| Ruff/mypy scope expansion | pending | Widen only after each next slice is green under local wrappers and documented. |
