# Deep Analysis Report: NOMIS Failure During Coventry Isochrone Enrichment

Date: 2026-03-03  
Scope: Failure chain in `troubleshooting/Validating-NOMIS.docx` when Claude attempted to answer:

> "Estimate it's income, median age, and education levels and show this on the map - which I'd rather be a light OS map using primary hierarchy as highlighting"

## Artifacts Reviewed

- Source conversation document: `troubleshooting/Validating-NOMIS.docx`
- Markdown conversion: `troubleshooting/Validating-NOMIS.md`
- Extracted trace evidence: `troubleshooting/validating-nomis-trace-evidence-2026-03-03.md`
- Full trace log: `logs/claude-trace.jsonl`
- Server/tool logic: `tools/nomis_data.py`, `tools/os_mcp.py`, `server/mcp/tool_search.py`
- Regression tests: `tests/test_nomis_data.py`, `tests/test_tool_search.py`, `tests/test_os_mcp_descriptor.py`

## Symptom Timeline (UTC)

Evidence references are line-numbered from `logs/claude-trace.jsonl`.

1. `2026-03-03T19:27:25` (`line 4769`) Claude calls `nomis_query` with `dataset=NM_2028_1` and params containing an unknown dimension key `c2021_age_92`.
2. `2026-03-03T19:27:26` (`line 4771`) Server returns `400 NOMIS_QUERY_ERROR` with message `Cannot create query`.
3. `2026-03-03T19:27:49` (`line 4772`) Claude retries with a larger ward list, still omitting required dimensions (`time`, `c_sex`) and still including invalid age key.
4. `2026-03-03T19:27:49` (`line 4774`) Same `400` error.
5. `2026-03-03T19:28:00` (`line 4775`) Claude retries with `geography="645922049...645922066"` (range syntax not supported as sent).
6. `2026-03-03T19:28:01` (`line 4776`) Same `400` error.
7. `2026-03-03T19:28:17` (`line 4777`) Claude retries with valid LA code `E08000026` but still with missing required dimensions and invalid age key.
8. `2026-03-03T19:28:17` (`line 4778`) Same `400` error.
9. `2026-03-03T19:33:45` (`line 4779`) Claude calls `os_mcp_descriptor` with `category="stats"`.
10. `2026-03-03T19:33:45` (`line 4780`) Descriptor responds `200` but includes `toolSearch.error`: `Invalid category 'stats'... valid includes 'statistics'`.

## Root Cause Analysis

### RC1: Query shape drift for `nomis.query` was not auto-recovered

Observed bad payload characteristics:

- Wrong/unsupported dimension key: `c2021_age_92`
- Missing required dimensions for `NM_2028_1`: `time`, `c_sex`
- Repeated retries without correcting dimensions

Pre-existing behavior in this failure trace was opaque (`Cannot create query` only), so the model continued low-quality retries.

### RC2: Category alias mismatch (`stats` vs `statistics`) disrupted discovery follow-up

`os_mcp_descriptor` accepted the request but returned a category-validation error in `toolSearch` for `stats`. This blocked consistent narrowing of tools and increased chance of model derailment after NOMIS failures.

### RC3: Progressive-disclosure expectations were conflated with non-standard search semantics

Validation against MCP `2025-11-25` standard docs confirms:

- Standard discovery method is `tools/list` with optional `cursor` pagination.
- Tool invocation is `tools/call`.
- Core spec does not define a mandatory `tools/search` RPC requirement.

Evidence:

- `docs/vendor/mcp/repos/modelcontextprotocol/docs/specification/2025-11-25/server/tools.mdx`
- `docs/vendor/mcp/repos/modelcontextprotocol/schema/2025-11-25/schema.json` (`ListToolsRequest`, `ListToolsResult`)

Conclusion: client-side "tool search first" behavior is implementation policy, not a core MCP transport requirement.

## Reproduction Validation (Post-change)

Live local verification performed:

- `_fetch_dataset_overview("NM_2028_1")` confirms required dimensions include `time`, `geography`, `c_sex`, `measures`.
- `nomis.query` with `dataset=NM_2028_1`, `geography=E08000026`, invalid `c2021_age_92`, missing `time/c_sex` now auto-adjusts and succeeds after retry.

## Implementation Plan and Execution

### Workstream A: Descriptor/category resilience

Status: done

1. Add category alias normalization (`stats -> statistics`) in `server/mcp/tool_search.py`.
2. Apply alias handling to both:
   - `get_tool_search_config(...)`
   - `search_tools(...)`
3. Preserve current behavior for unknown categories (no breaking exception).

Delivered:

- `normalize_category_alias(...)`
- `get_tool_search_config("stats")` now returns filtered statistics tools instead of an error.

### Workstream B: NOMIS auto-correction/retry

Status: done

1. Derive required dimensions from dataset overview.
2. On `Cannot create query`/`Query is incomplete`:
   - auto-fill missing required dimensions from query template
   - drop unknown dimension keys
   - retry once with adjusted params
3. Return successful payload with `queryAdjusted.dimensionAutoAdjust` metadata.

Delivered in `tools/nomis_data.py`:

- `_required_dimension_concepts(...)`
- `_build_retry_params_from_overview(...)`
- `_query(...)` retry path now applies dimension auto-adjustments before final erroring.

### Workstream C: Regression tests

Status: done

Added tests:

- `tests/test_tool_search.py`
  - `test_get_tool_search_config_stats_alias`
  - `test_search_tools_accepts_stats_alias_category`
- `tests/test_os_mcp_descriptor.py`
  - `test_os_mcp_descriptor_accepts_stats_category_alias`
- `tests/test_nomis_data.py`
  - `test_nomis_query_autoretries_with_dimension_autoadjustments`

Validation command:

```bash
uv run --with pytest --with pytest-cov pytest -q --no-cov \
  tests/test_nomis_data.py tests/test_tool_search.py tests/test_os_mcp_descriptor.py
```

Result:

- `39 passed`

## What This Fixes for the Reported Prompt

For the failing conversation class:

- `category: "stats"` no longer causes descriptor-side category mismatch.
- NOMIS calls with missing required dimensions and extraneous dimension keys now have an automatic correction path instead of only returning terminal `NOMIS_QUERY_ERROR`.
- The model receives structured adjustment evidence (`queryAdjusted`) that supports better self-correction on subsequent turns.

## Residual Risks

- If geography codes are semantically invalid for the chosen dataset (even after dimension auto-correction), NOMIS can still legitimately fail.
- Query success still depends on the model selecting a dataset that actually contains the requested concept (for example, income vs age vs qualifications often require different datasets).

## Commit Scope (User-added files included)

This change set includes user-added troubleshooting sources and conversions:

- `troubleshooting/Validating-NOMIS.docx`
- `troubleshooting/Validating-NOMIS.md`
- `docs/Claude Conversations on MCP-Geo.docx`

Along with implementation, tests, and analysis artifacts listed above.
