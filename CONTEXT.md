# MCP Geo Context

Last updated: 2026-02-07
Owner: @chris-page-gov

## Purpose

This file is the durable, repo-scoped context for Codex across environments.
Read it at the start of a session and update it whenever priorities or key
assumptions change.

## Project Snapshot

- FastAPI MCP server for Ordnance Survey and ONS geospatial tooling.
- Primary entrypoints: `server/main.py` (HTTP) and `server/stdio_adapter.py` (JSON-RPC).
- Tooling and resources live under `tools/` and `resources/`.

## Spec Package Map

- The spec package is the end-to-end prototype specification for test readiness and demos.
- Primary entry: `docs/spec_package/README.md`; roadmap: `docs/spec_package/12_backlog_and_plan.md`.
- Use chapter references for detail: aims (`01_aims_objectives.md`), personas
  (`02_personas_user_stories.md`), architecture (`03_architecture.md`),
  system design (`04_system_design.md`), data flow/cache (`05_data_flow_and_cache.md`),
  API contracts (`06_api_contracts.md`), security (`07_security_privacy.md`),
  observability (`08_observability_ops.md`), testing (`09_testing_quality.md`),
  MCP-Apps UI (`10_mcp_apps_ui.md`), walkthroughs (`11_walkthroughs.md`),
  backlog/plan (`12_backlog_and_plan.md`), screenshots (`screenshots.md`),
  sequence diagrams (`13_sequence_diagrams.md`), export instructions (`export.md`).
- Quick guidance: use `03_architecture.md`/`04_system_design.md` for system understanding,
  `06_api_contracts.md` for interface details, `10_mcp_apps_ui.md` for UI behaviors, and
  `12_backlog_and_plan.md` for delivery sequencing.
- Current scope snapshot: HTTP and STDIO MCP server; OS Places/Names/NGD/linked IDs/maps/
  admin lookup/ONS tools; boundary cache pipeline; MCP-Apps UI resources via `ui://`.

## Codex Usage (Mac App + Devcontainer)

- `CONTEXT.md` is the durable, cross-surface source of truth; read and update it at session start.
- Devcontainer persistence: `CODEX_HOME` is mounted to the named volume `mcp-geo-codex`
  in `.devcontainer/devcontainer.json`, so Codex local state survives rebuilds.
- Spec package exports are ignored in git: `docs/spec_package/build/`.
- External ref (Codex app overview/install): `https://developers.openai.com/codex/app/`.
- External ref (Codex app features): `https://developers.openai.com/codex/app/features`.
- External ref (Codex app announcement): `https://openai.com/index/introducing-the-codex-app/`.
- External ref (VS Code devcontainer mounts): `https://code.visualstudio.com/remote/advancedcontainers/add-local-file-mount`.
- External ref (Docker volumes reference): `https://docs.docker.com/engine/storage/volumes/`.

## Current Focus

- Ensuring reliable MCP-Apps performance and client compatibility.
- Improving ONS dataset selection (ranking, elicitation, comparability guardrails).

## Active Work

- Documentation pack and preparation for workshop/demo.
- ONS dataset selection research pack integrated at `research/ons_dataset_selection/`.
- Track delivery work in `docs/spec_package/12_backlog_and_plan.md` and `PROGRESS.MD`.

## Status Snapshot (from PROGRESS.MD)

- Done: core server, stdio adapter, tool registry, OS Places/Names/Linked IDs/Vector Tiles,
  route_query tool, baseline tests, boundary cache ingestion pipeline.
- Partial: OS Features, OS Maps render, ONS data tooling, admin lookup caching, resources
  population, playground UI, observability.
- Done: ONS dataset selection research pack (taxonomy, datapack schema, linking rules,
  evaluation plan).
- Not started: CI pipeline.

## Backlog Priorities (from spec package)

- High: CI pipeline; MCP-Apps client compatibility validation and docs.
- Medium: pagination for large tool results; structured JSON logging; expanded ONS caching;
  admin cache staleness policy; performance regression tests.
- Low: UI polish; CLI/Playground UX; documentation cross-links.

## Completion Plan (phased)

- Phase 1 (Reliability and CI, 2-3 weeks): GitHub Actions pipeline; release automation;
  structured JSON logging option.
- Phase 2 (Data correctness, 2-4 weeks): pagination; dataset caching with TTL/invalidation;
  boundary pipeline validation rules.
- Phase 3 (UI fidelity, 2-4 weeks): fix MCP-Apps init flow for Claude/Inspector; produce
  screenshots.
- Phase 4 (Resources and observability, 4-6 weeks): populate resources; add latency/cache
  metrics; alerting guidance.

## Verification Status

- Latest full test run: `pytest -q` (90.20% coverage, 464 passed, 1 skipped) on 2026-02-06.
- Latest container test run: `devcontainer exec --workspace-folder /Users/crpage/repos/mcp-geo bash -lc "pytest -q"` succeeded on 2026-02-06.

## Key Conventions

- Follow `AGENTS.md` for repo rules.
- Track plan status in `PROGRESS.MD`.
- Track release notes in `CHANGELOG.md`.

## Decisions Log

- 2026-02-02: Added persistent Codex context file and devcontainer Codex home mount.
- 2026-02-02: Expanded CONTEXT.md with PROGRESS and spec package summary to preserve context.
- 2026-02-06: Added legacy `uiResourceUris` fields in MCP-Apps tool responses to improve Claude Desktop compatibility.
- 2026-02-06: Added `resource_link` content blocks in MCP-Apps tool responses for UI host compatibility.
- 2026-02-06: Defaulted `resource_link` content to opt-in (`MCP_APPS_RESOURCE_LINK=0` by default; set `1` to opt in) to avoid unsupported format warnings in Claude.
- 2026-02-06: Bounded `nomis.datasets` responses with `q`/`limit` discovery controls and updated stats routing guidance to avoid unfiltered dataset listing loops.
- 2026-02-06: Added STDIO form elicitation for comparison-style `os_mcp.stats_routing` calls when client capability negotiation includes `elicitation.form`.
- 2026-02-06: Extended `os_mcp.stats_routing` with `comparisonLevel`/`providerPreference` overrides and returned `userSelections` for traceable routing behavior.
- 2026-02-06: Claude Desktop reports “unsupported format” when tool responses include `content` blocks of type `resource_link` (MCP-Apps UI), so treat `resource_link` as unsupported in Claude until proven otherwise.
- 2026-02-06: Claude transcript captured at `docs/Claude_opus_4-6_failed_convo_1.md` shows MCP-Apps UI still failing to render; follow up with raw stdio trace for capabilities and content blocks.
- 2026-02-06: Claude stdio trace (`logs/claude-trace.jsonl`) confirms `os_apps.render_statistics_dashboard` returns a `resource_link` content block, which aligns with the “unsupported format” error in Claude.
- 2026-02-06: Added `MCP_APPS_CONTENT_MODE` and `os_apps.render_ui_probe` to control UI content blocks and test client rendering without `resource_link`.
- 2026-02-06: Updated `scripts/claude-mcp-local` to default `MCP_APPS_RESOURCE_LINK=0` so Claude sessions do not emit `resource_link` unless explicitly enabled.
- 2026-02-06: Updated `nomis.datasets` dataset-definition path to return a compact summary by default and require `includeRaw=true` for full upstream definition payloads.
- 2026-02-06: Claude `parent_message_uuid` UUID validation errors were confirmed as host/session-state failures (not MCP tool payload failures); troubleshooting docs updated with recovery steps.
- 2026-02-06: Updated `scripts/claude-mcp-local` to default `MCP_APPS_CONTENT_MODE=embedded` so Claude receives embedded UI resources instead of `resource_link` by default.
- 2026-02-06: Added flat `ui/resourceUri` metadata alongside nested `ui.resourceUri` in UI tool metadata for broader MCP-Apps host compatibility.
- 2026-02-06: `nomis.datasets` query filtering now applies multi-token scoring for better dataset ranking on compound prompts (for example `population census 2021`).
- 2026-02-06: `scripts/mcp_stdio_trace_proxy.py` now avoids JSON parse attempts for stderr/non-RPC lines to reduce noisy parse-error entries in trace logs.
- 2026-02-07: Added ONS dataset selection research pack under `research/ons_dataset_selection/` to guide dataset ranking, elicitation, and explainability.
- 2026-02-07: Added Agent Skills vendor submodule and tracking entry to align Codex skill usage with the Agent Skills spec.

## Open Questions

- Does Claude Desktop actually render MCP-Apps UI from `_meta.ui.resourceUri` or `uiResourceUris` without `resource_link`, or is it currently ignoring MCP-Apps UI entirely?

## Run and Test Notes

- `uvicorn server.main:app --reload`
- `pytest -q`
