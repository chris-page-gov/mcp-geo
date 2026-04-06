---
title: "Script Family - boundary"
kb_kind: "code_family"
source_paths:
  - "scripts/boundary_autofix.py"
  - "scripts/boundary_cache_ingest.py"
  - "scripts/boundary_cache_schema.sql"
  - "scripts/boundary_pipeline.py"
  - "scripts/boundary_run_tracker.py"
  - "scripts/boundary_status_ticker.py"
  - "scripts/boundary_triage.py"
source_commit: "bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851"
source_commit_dirty: true
source_urls:
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/scripts/boundary_autofix.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/scripts/boundary_cache_ingest.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/scripts/boundary_cache_schema.sql"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/scripts/boundary_pipeline.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/scripts/boundary_run_tracker.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/scripts/boundary_status_ticker.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/scripts/boundary_triage.py"
source_hashes:
  scripts/boundary_autofix.py: "c92ce606ceaf38611529240aafbb0eb7ec5271f246160d200578e311898d7026"
  scripts/boundary_cache_ingest.py: "30bb50508dab71812f757520c50ebe4a3f642ba1d1f50c3ff73991c297453e65"
  scripts/boundary_cache_schema.sql: "c68af9338b0e6c9d28eff06ed5620b8b3cd49bee716137f43be9501d2ee2ff55"
  scripts/boundary_pipeline.py: "b775fb35f21c11bcf36601ac68bc24e2cc3930ce1604e85b2c44f1f17e1e6616"
  scripts/boundary_run_tracker.py: "47d8bbbf7f866eb28b36dfa8dbb043e3013dc8671e8406157717702654751e68"
  scripts/boundary_status_ticker.py: "a760772d0e942dc0996bf94a10ded00f95d0cacf3a0796216f8c99341e2a5cc8"
  scripts/boundary_triage.py: "d0e6d105ac53d2052a104714236c74c98d703b55942ac64e610acf0c76fc7803"
generated_at: "2026-04-06T09:00:35Z"
evidence_scope: "canon"
first_seen_date: "2026-01-30"
last_validated_at: "2026-04-06T09:00:35Z"
---
# Script Family - boundary

## Evidence Scope

- Categories: `code_runtime`
- Source file count: 7

## Source Inventory

| Path | Summary | First Seen | Last Commit | Related Tests |
| --- | --- | --- | --- | --- |
| `scripts/boundary_autofix.py` | from __future__ import annotations | 2026-02-01 | 2026-02-01 | - |
| `scripts/boundary_cache_ingest.py` | from __future__ import annotations | 2026-01-30 | 2026-01-30 | - |
| `scripts/boundary_cache_schema.sql` | -- PostGIS boundary cache schema for MCP Geo | 2026-01-30 | 2026-01-30 | - |
| `scripts/boundary_pipeline.py` | from __future__ import annotations | 2026-01-30 | 2026-02-23 | `tests/test_boundary_pipeline_variant_policy.py` |
| `scripts/boundary_run_tracker.py` | from __future__ import annotations | 2026-02-01 | 2026-02-02 | - |
| `scripts/boundary_status_ticker.py` | from __future__ import annotations | 2026-02-01 | 2026-02-01 | - |
| `scripts/boundary_triage.py` | from __future__ import annotations | 2026-02-01 | 2026-02-01 | - |

## Pinned Sources

- [`scripts/boundary_autofix.py`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/scripts/boundary_autofix.py)
- [`scripts/boundary_cache_ingest.py`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/scripts/boundary_cache_ingest.py)
- [`scripts/boundary_cache_schema.sql`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/scripts/boundary_cache_schema.sql)
- [`scripts/boundary_pipeline.py`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/scripts/boundary_pipeline.py)
- [`scripts/boundary_run_tracker.py`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/scripts/boundary_run_tracker.py)
- [`scripts/boundary_status_ticker.py`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/scripts/boundary_status_ticker.py)
- [`scripts/boundary_triage.py`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/scripts/boundary_triage.py)
