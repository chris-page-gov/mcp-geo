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
source_commit: "004e7d4748422b44133399279803c8cb2b766a1c"
source_commit_dirty: true
source_urls:
  - "https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/scripts/boundary_autofix.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/scripts/boundary_cache_ingest.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/scripts/boundary_cache_schema.sql"
  - "https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/scripts/boundary_pipeline.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/scripts/boundary_run_tracker.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/scripts/boundary_status_ticker.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/scripts/boundary_triage.py"
source_hashes:
  scripts/boundary_autofix.py: "sha256:c92ce606-ceaf3861-1529240a-afbb0eb7-ec5271f2-46160d20-0578e311-898d7026"
  scripts/boundary_cache_ingest.py: "sha256:30bb5050-8dab7181-2f757520-c50ebe4a-3f642ba1-d1f50c3f-f73991c2-97453e65"
  scripts/boundary_cache_schema.sql: "sha256:c68af933-8b0e6c9d-28eff06e-d5620b8b-3cd49bee-716137f4-3be9501d-2ee2ff55"
  scripts/boundary_pipeline.py: "sha256:b775fb35-f21c11bc-f36601ac-68bc24e2-cc3930ce-1604e85b-2c44f1f1-7e1e6616"
  scripts/boundary_run_tracker.py: "sha256:47d8bbbf-7f866eb2-8b36dfa8-dbb043e3-013dc867-1e840615-77177026-54751e68"
  scripts/boundary_status_ticker.py: "sha256:a760772d-0e942dc0-996bf94a-10ded00f-95d0cacf-3a079621-6f8c9934-1e2a5cc8"
  scripts/boundary_triage.py: "sha256:d0e6d105-ac53d205-2a104714-236c74c9-8d703b55-942ac64e-610acf0c-76fc7803"
generated_at: "2026-04-06T14:09:00Z"
evidence_scope: "canon"
first_seen_date: "2026-01-30"
last_validated_at: "2026-04-06T14:09:00Z"
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

- [`scripts/boundary_autofix.py`](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/scripts/boundary_autofix.py)
- [`scripts/boundary_cache_ingest.py`](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/scripts/boundary_cache_ingest.py)
- [`scripts/boundary_cache_schema.sql`](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/scripts/boundary_cache_schema.sql)
- [`scripts/boundary_pipeline.py`](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/scripts/boundary_pipeline.py)
- [`scripts/boundary_run_tracker.py`](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/scripts/boundary_run_tracker.py)
- [`scripts/boundary_status_ticker.py`](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/scripts/boundary_status_ticker.py)
- [`scripts/boundary_triage.py`](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/scripts/boundary_triage.py)
