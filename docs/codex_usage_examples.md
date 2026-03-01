# Codex Usage Examples for `mcp-geo`

Generated: `2026-03-01`

This document captures practical examples of how Codex has been used on the
`mcp-geo` repository, with evidence from:

- local Codex session summaries (`docs/reports/mcp_geo_codex_long_horizon_summary_2026-03-01.md`)
- git history (`git log`, `git show`)
- merged pull requests on `main`

## 1) High-level usage profile (from logs)

From `docs/reports/mcp_geo_codex_long_horizon_summary_2026-03-01.md`:

- Sessions included: `54`
- Date range: `2026-01-20` to `2026-03-01`
- Active runtime: `608.8h`
- Tool calls: `14,615` (`5,562` shell, `2,184` patches)
- Patch volume: `66.5k` added lines via `apply_patch`

Interpretation:
- Usage has been implementation-heavy (high patch volume, high shell/tool usage), not chat-only.
- The workload includes both iterative debugging (interactive sessions) and repeatable report-style automations.

## 2) Timeline of representative Codex deliveries

- `2026-02-21` - Safe-by-design hardening stream merged via PR #11.
- `2026-02-22` - ONS geo cache and startup-context mitigations landed (PR #15 branch lineage).
- `2026-02-23` - Host-runtime map behavior + boundary harness hardening landed.
- `2026-02-25` - Long-horizon reporting + repo complexity reporting released in `v0.4.0`.
- `2026-02-27` - Simple map auth + PMTiles lab stream merged via PR #18.
- `2026-03-01` - Updated long-horizon summary generated with latest session coverage.

## 3) Concrete examples (problem -> Codex change -> evidence)

### Example A: Browser-first auth fallback for map delivery

- Problem:
  - Need the simplest browser map flow using OAuth bearer when available, with deterministic fallback to API key and then server environment key.
- Codex change:
  - Updated vector proxy auth resolution order in `server/maps_proxy.py`.
  - Added/expanded proxy auth tests in `tests/test_maps_proxy.py`.
- Evidence:
  - Commit `ee06e5e` (`feat(simple-map): add auth-first map lab and proxy diagnostics`).
  - PR merge: `c63dc12` (PR #18).

### Example B: Build a novice-usable map test UI (not just developer tooling)

- Problem:
  - Existing diagnostics were too technical for first-time users.
- Codex change:
  - Added `ui/simple_map.html` (OS Vector + PMTiles lab UI).
  - Added user-facing runbook `docs/simple_map_lab.md`.
  - Added onboarding links and troubleshooting guidance in `docs/getting_started.md` and `docs/troubleshooting.md`.
- Evidence:
  - Commit `ee06e5e` touched 13 files with `1647` insertions.

### Example C: Close test coverage gaps quickly with targeted tests

- Problem:
  - Need full-suite confidence and better coverage around ONS helpers.
- Codex change:
  - Added targeted tests:
    - `tests/test_ons_codes_unit.py`
    - `tests/test_ons_data_internal.py`
    - updates to `tests/test_ons_catalog_validator.py`
- Evidence:
  - Commit `0793640` added `1000` lines across 3 test files.

### Example D: Harden startup path for constrained MCP clients

- Problem:
  - Startup payload/tooling constraints for clients that do not defer full schema loads.
- Codex change:
  - Included `os_mcp.select_toolsets` in starter toolset for scoped expansion.
  - Added regression assertion in `tests/test_tool_search.py`.
- Evidence:
  - Commit `765090c`.

### Example E: Implement dual-derivation ONS geography cache workflow

- Problem:
  - Need reliable postcode/UPRN geography mapping with exact and best-fit derivations.
- Codex change:
  - Added cache core (`server/ons_geo_cache.py`), tools (`tools/ons_geo.py`), refresh pipeline (`scripts/ons_geo_cache_refresh.py`), resource metadata, and tests.
- Evidence:
  - Commit `81f5f8e`: `15` files changed, `1733` insertions.

### Example F: Improve host-runtime robustness for map widgets

- Problem:
  - UI behavior varied across host runtimes; boundary explorer needed deterministic behavior and harness checks.
- Codex change:
  - Hardened widget host behavior in `ui/boundary_explorer.html`.
  - Added deterministic harness test `playground/tests/boundary_explorer_host_harness.spec.js`.
  - Synced config/docs and map-tool compatibility updates.
- Evidence:
  - Commit `9fd5ffd`: `11` files changed, `906` insertions.

### Example G: Security hardening - path containment in resources

- Problem:
  - Path traversal and containment checks needed stronger guarantees.
- Codex change:
  - Hardened path containment in `server/mcp/resource_catalog.py`.
  - Added regression coverage in `tests/test_resource_catalog.py`.
- Evidence:
  - Commit `a6dae84`: `92` insertions, `23` deletions.

### Example H: Reliability hardening from live evaluation feedback

- Problem:
  - Residual OS/ONS live-evaluation score gaps.
- Codex change:
  - Adjusted evaluation scoring + tool behavior for deterministic error handling and routing.
  - Added/updated focused tests across evaluation, NOMIS, maps, MCP routing, and postcode behavior.
- Evidence:
  - Commit `2814114`: `11` files changed, `184` insertions.

## 4) Example prompt patterns you have used effectively

Based on the top-token sessions in the long-horizon summary:

- "Create branch X and implement workstreams from `PROGRESS.MD`, committing as you go."
- "Catch up on context and progress, then pull outstanding mapping items and validate."
- "Run full test suite; fill coverage gaps; update PR; request review; fix comments."

What these prompts have in common:

- clear artifact targets (`PROGRESS.MD`, docs, tests, PR)
- explicit end-state (`commit/sync`, `full suite`, `fix comments`)
- tight feedback loops (run, verify, patch, re-run)

## 5) Recommended report set for ongoing tracking

To maintain a reusable "Codex usage portfolio", keep these files updated:

- Session metrics (logs):
  - `docs/reports/mcp_geo_codex_long_horizon_summary_<date>.md`
  - `docs/reports/mcp_geo_codex_long_horizon_summary_<date>.json`
- Delivery examples (narrative + evidence):
  - `docs/codex_usage_examples.md` (this file)
- Complexity/risk snapshots:
  - `docs/reports/repo_extent_complexity_<date>.md`
  - `docs/reports/repo_extent_complexity_report_card_<date>.md`

## 6) How to regenerate evidence quickly

### Refresh Codex session summary

```bash
./.venv/bin/python scripts/codex_long_horizon_summary.py \
  --repo-filter mcp-geo \
  --output docs/reports/mcp_geo_codex_long_horizon_summary_$(date +%F).md \
  --json-output docs/reports/mcp_geo_codex_long_horizon_summary_$(date +%F).json \
  --summary-svg-output docs/reports/mcp_geo_codex_long_horizon_summary_$(date +%F).svg
```

### Pull latest merged delivery timeline

```bash
git log --merges --oneline -n 20
```

### Inspect a delivery example in detail

```bash
git show --stat <commit_sha>
```

