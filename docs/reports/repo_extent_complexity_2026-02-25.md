# MCP Geo Repository Extent and Complexity

Generated: `2026-02-25T06:34:25.969900Z`
Repo root: `/Users/crpage/repos/mcp-geo`
Scope mode: `both`
Lookback window: `180` days

## Method Summary

- Uses two inventory scopes:
  - `git_tracked`: files in `git ls-files`.
  - `workspace`: tracked + untracked non-ignored files.
- Excludes generated/output surfaces from functional complexity via:
  - GitHub Linguist attributes (`linguist-generated`, `linguist-vendored`).
  - Deterministic policy globs (for example `docs/reports/**`, `logs/**`).
- Complexity model:
  - Python: AST-based cyclomatic complexity per function.
  - Non-Python code: branch-keyword complexity proxy.
- Hotspot score: `complexity_points * log2(1 + churn_lines)`.

## Change Dynamics

- Commits in lookback: `263`
- Active authors: `4`
- Additions: `214,030`
- Deletions: `15,513`

## Scope: `git_tracked`

- Files (total/text/binary): `661` / `564` / `97`
- Functional files: `265`
- Functional non-blank LOC: `60.2k`
- Excluded as generated/output policy: `34`
- Hotspot concentration (top 5 share): `23.4%`

### Language Footprint

- `Python`: `48.3k` LOC in `230` files
- `HTML`: `9.1k` LOC in `9` files
- `JavaScript`: `1.9k` LOC in `12` files
- `Shell`: `693` LOC in `13` files
- `SQL`: `40` LOC in `1` files

### Top Directories by Functional LOC

- `tests`: `20.1k` LOC
- `tools`: `14.5k` LOC
- `scripts`: `9.7k` LOC
- `server`: `6.9k` LOC
- `ui`: `6.8k` LOC
- `playground`: `2.0k` LOC
- `troubleshooting`: `125` LOC
- `.`: `17` LOC

### Python Complexity

- Functions analyzed: `2,227`
- Mean cyclomatic complexity: `4.06`
- P90 cyclomatic complexity: `9.00`
- Max cyclomatic complexity: `138`
- Functions with CC >= 15: `120`

### Top Hotspots (`complexity x churn`)

- `scripts/boundary_pipeline.py` | `Python` | `score=5127.13` | `complexity=460.00` | `churn=2,265`
- `tools/ons_data.py` | `Python` | `score=4674.18` | `complexity=416.00` | `churn=2,411`
- `server/stdio_adapter.py` | `Python` | `score=3500.19` | `complexity=312.00` | `churn=2,382`
- `tools/os_features.py` | `Python` | `score=3199.71` | `complexity=301.00` | `churn=1,584`
- `tools/nomis_data.py` | `Python` | `score=3196.98` | `complexity=312.00` | `churn=1,214`
- `tools/os_mcp.py` | `Python` | `score=3035.51` | `complexity=275.00` | `churn=2,102`
- `tools/ons_select.py` | `Python` | `score=2697.13` | `complexity=273.00` | `churn=941`
- `tools/admin_lookup.py` | `Python` | `score=2511.52` | `complexity=236.00` | `churn=1,597`
- `server/mcp/resource_catalog.py` | `Python` | `score=2185.79` | `complexity=207.00` | `churn=1,508`
- `server/maps_proxy.py` | `Python` | `score=1727.65` | `complexity=180.00` | `churn=774`
- `tools/os_apps.py` | `Python` | `score=1682.79` | `complexity=164.00` | `churn=1,226`
- `server/mcp/http_transport.py` | `Python` | `score=1552.09` | `complexity=158.00` | `churn=905`
- `scripts/check_lmr_host4.py` | `Python` | `score=1450.99` | `complexity=151.00` | `churn=780`
- `tools/ons_codes.py` | `Python` | `score=1390.59` | `complexity=155.00` | `churn=501`
- `tests/test_os_catalog_snapshot.py` | `Python` | `score=1255.73` | `complexity=143.00` | `churn=439`
- `tools/os_maps.py` | `Python` | `score=1209.23` | `complexity=128.00` | `churn=697`
- `tests/evaluation/harness.py` | `Python` | `score=1093.80` | `complexity=117.00` | `churn=651`
- `tests/test_ons_data.py` | `Python` | `score=1038.69` | `complexity=107.00` | `churn=835`
- `tests/test_tool_upstream_endpoint_contracts.py` | `Python` | `score=1035.62` | `complexity=116.00` | `churn=486`
- `scripts/trace_report.py` | `Python` | `score=970.10` | `complexity=113.00` | `churn=383`

## Scope: `workspace`

- Files (total/text/binary): `677` / `580` / `97`
- Functional files: `271`
- Functional non-blank LOC: `62.2k`
- Excluded as generated/output policy: `39`
- Hotspot concentration (top 5 share): `23.4%`

### Language Footprint

- `Python`: `50.4k` LOC in `234` files
- `HTML`: `9.1k` LOC in `9` files
- `JavaScript`: `1.9k` LOC in `12` files
- `Shell`: `726` LOC in `15` files
- `SQL`: `40` LOC in `1` files

### Top Directories by Functional LOC

- `tests`: `20.4k` LOC
- `tools`: `14.5k` LOC
- `scripts`: `11.4k` LOC
- `server`: `6.9k` LOC
- `ui`: `6.8k` LOC
- `playground`: `2.0k` LOC
- `troubleshooting`: `125` LOC
- `skills`: `33` LOC
- `.`: `17` LOC

### Python Complexity

- Functions analyzed: `2,294`
- Mean cyclomatic complexity: `4.10`
- P90 cyclomatic complexity: `9.00`
- Max cyclomatic complexity: `138`
- Functions with CC >= 15: `126`

### Top Hotspots (`complexity x churn`)

- `scripts/boundary_pipeline.py` | `Python` | `score=5127.13` | `complexity=460.00` | `churn=2,265`
- `tools/ons_data.py` | `Python` | `score=4674.18` | `complexity=416.00` | `churn=2,411`
- `server/stdio_adapter.py` | `Python` | `score=3500.19` | `complexity=312.00` | `churn=2,382`
- `tools/os_features.py` | `Python` | `score=3199.71` | `complexity=301.00` | `churn=1,584`
- `tools/nomis_data.py` | `Python` | `score=3196.98` | `complexity=312.00` | `churn=1,214`
- `tools/os_mcp.py` | `Python` | `score=3035.51` | `complexity=275.00` | `churn=2,102`
- `tools/ons_select.py` | `Python` | `score=2697.13` | `complexity=273.00` | `churn=941`
- `tools/admin_lookup.py` | `Python` | `score=2511.52` | `complexity=236.00` | `churn=1,597`
- `server/mcp/resource_catalog.py` | `Python` | `score=2185.79` | `complexity=207.00` | `churn=1,508`
- `server/maps_proxy.py` | `Python` | `score=1727.65` | `complexity=180.00` | `churn=774`
- `tools/os_apps.py` | `Python` | `score=1682.79` | `complexity=164.00` | `churn=1,226`
- `server/mcp/http_transport.py` | `Python` | `score=1552.09` | `complexity=158.00` | `churn=905`
- `scripts/check_lmr_host4.py` | `Python` | `score=1450.99` | `complexity=151.00` | `churn=780`
- `tools/ons_codes.py` | `Python` | `score=1390.59` | `complexity=155.00` | `churn=501`
- `tests/test_os_catalog_snapshot.py` | `Python` | `score=1255.73` | `complexity=143.00` | `churn=439`
- `tools/os_maps.py` | `Python` | `score=1209.23` | `complexity=128.00` | `churn=697`
- `tests/evaluation/harness.py` | `Python` | `score=1093.80` | `complexity=117.00` | `churn=651`
- `tests/test_ons_data.py` | `Python` | `score=1038.69` | `complexity=107.00` | `churn=835`
- `tests/test_tool_upstream_endpoint_contracts.py` | `Python` | `score=1035.62` | `complexity=116.00` | `churn=486`
- `scripts/trace_report.py` | `Python` | `score=970.10` | `complexity=113.00` | `churn=383`

## Notes

- This report prioritizes functional complexity and excludes known output/generated
  areas by default to avoid inflating system size with build/report artifacts.
- Customize inclusion/exclusion with `--exclude-glob` and scope flags.
- Use JSON output for dashboarding or longitudinal snapshots.
