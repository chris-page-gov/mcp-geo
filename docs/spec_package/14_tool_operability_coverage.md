# Tool Operability Coverage (Measured)

This chapter defines measurable coverage for live tool operability using a
Gherkin requirement set (`14_tool_operability.feature`) and machine-produced
evidence.

## Evidence artifacts

- Live harness report:
  `data/evaluation_results_live_review_2026-02-21_after_patch2_full.json`
- Missing-tool probe report:
  `data/live_missing_tools_probe_report_2026-02-21.json`
- Aggregated spec coverage report:
  `data/spec_tool_operability_coverage_2026-02-21.json`

## Coverage generator

Run:

```bash
./.venv/bin/python scripts/spec_tool_operability_coverage.py \
  --harness data/evaluation_results_live_review_2026-02-21_after_patch2_full.json \
  --probe data/live_missing_tools_probe_report_2026-02-21.json \
  --output data/spec_tool_operability_coverage_2026-02-21.json
```

## Current measured status (2026-02-21)

- Registered tools: `76`
- Functional live tools: `75` (`98.68%`)
- Release-gated functional tools (excluding optional entitlement): `75/75` (`100.0%`)
- Auth/entitlement-blocked tools: `1` (`1.32%`)
- Unresolved tools (no evidence): `0`
- Live harness score: `91.16%` (`6290/6900`)

Blocked tool detail:
- `os_features.wfs_archive_capabilities`: `401 OS_API_KEY_INVALID` (key
  scope/entitlement mismatch for archive capabilities endpoint).

Optional-by-entitlement tools:
- `os_features.wfs_archive_capabilities` (explicitly excluded from release-gated
  functional denominator, but still required to be evidenced as functional or blocked_auth).

## Requirement matrix

| Requirement ID | Statement | Measure | Actual | Status |
| --- | --- | --- | --- | --- |
| `REQ-LIVE-TOOLS-01` | Every registered tool has live execution evidence. | `(functional + blocked_auth) / registered` and unresolved `== 0` | `76/76`, unresolved `0` | Pass |
| `REQ-LIVE-TOOLS-02` | Release-gated functional operability >= 95%. | `functional / (registered - optional entitlement)` | `75/75 = 100.0%` | Pass |
| `REQ-LIVE-TOOLS-03` | Live harness score >= 90%. | `total_score / max_score` | `91.16%` | Pass |
| `REQ-LIVE-TOOLS-04` | Any blocked tool is explicit/actionable. | Blocked entries include tool + code + message | `os_features.wfs_archive_capabilities`, `OS_API_KEY_INVALID` | Pass |
| `REQ-LIVE-TOOLS-05` | Optional entitlement tools are explicit/tracked. | Optional tools listed + evidenced as functional/blocked_auth | `1 listed`, `1 evidenced` | Pass |

## Scope note

The harness score penalties below 80 on individual questions are primarily
intent-classification mismatches in `os_mcp.route_query`, not execution
failures of the called tools. Use this chapter together with
`09_testing_quality.md` for release gating.
