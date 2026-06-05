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
source_commit: "923807292e3a134ad8214be3de523caa7fdce7c5"
source_commit_dirty: true
source_urls:
  - "https://github.com/chris-page-gov/mcp-geo/blob/923807292e3a134ad8214be3de523caa7fdce7c5/scripts/boundary_autofix.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/923807292e3a134ad8214be3de523caa7fdce7c5/scripts/boundary_cache_ingest.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/923807292e3a134ad8214be3de523caa7fdce7c5/scripts/boundary_cache_schema.sql"
  - "https://github.com/chris-page-gov/mcp-geo/blob/923807292e3a134ad8214be3de523caa7fdce7c5/scripts/boundary_pipeline.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/923807292e3a134ad8214be3de523caa7fdce7c5/scripts/boundary_run_tracker.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/923807292e3a134ad8214be3de523caa7fdce7c5/scripts/boundary_status_ticker.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/923807292e3a134ad8214be3de523caa7fdce7c5/scripts/boundary_triage.py"
source_hashes:
  scripts/boundary_autofix.py: "sha256:be6ca3e8-7e3ffb11-04c17b4d-91d42065-707421f3-d7b84880-9126b168-539861b8"
  scripts/boundary_cache_ingest.py: "sha256:30bb5050-8dab7181-2f757520-c50ebe4a-3f642ba1-d1f50c3f-f73991c2-97453e65"
  scripts/boundary_cache_schema.sql: "sha256:c68af933-8b0e6c9d-28eff06e-d5620b8b-3cd49bee-716137f4-3be9501d-2ee2ff55"
  scripts/boundary_pipeline.py: "sha256:e9e98738-8969ade6-efb93079-844af82f-408d0b9e-2d14f33d-f69cefe2-d9ca12bb"
  scripts/boundary_run_tracker.py: "sha256:3f5e554b-de96323b-2118c0f9-8edd2188-ad37eec1-7d070d74-e3c81b0d-8e2a16c7"
  scripts/boundary_status_ticker.py: "sha256:ecf95979-8c03a57b-eb6d0744-f4420274-848de6e9-2a2a0d11-e6f251b6-738451f3"
  scripts/boundary_triage.py: "sha256:9b4e481b-d6d43096-19730c57-930673a2-db4a71c2-1284da0d-408915fb-317a8156"
generated_at: "2026-06-01T02:28:24Z"
evidence_scope: "canon"
first_seen_date: "2026-01-30"
last_validated_at: "2026-06-01T02:28:24Z"
---
# Script Family - boundary

## Evidence Scope

- Categories: `code_runtime`
- Source file count: 7

## Source Inventory

| Path | Summary | First Seen | Last Commit | Related Tests |
| --- | --- | --- | --- | --- |
| `scripts/boundary_autofix.py` | from __future__ import annotations | 2026-02-01 | 2026-04-12 | `tests/test_boundary_autofix.py` |
| `scripts/boundary_cache_ingest.py` | from __future__ import annotations | 2026-01-30 | 2026-01-30 | - |
| `scripts/boundary_cache_schema.sql` | -- PostGIS boundary cache schema for MCP Geo | 2026-01-30 | 2026-01-30 | - |
| `scripts/boundary_pipeline.py` | from __future__ import annotations | 2026-01-30 | 2026-04-12 | `tests/test_boundary_autofix.py`, `tests/test_boundary_pipeline_variant_policy.py` |
| `scripts/boundary_run_tracker.py` | from __future__ import annotations | 2026-02-01 | 2026-04-12 | - |
| `scripts/boundary_status_ticker.py` | from __future__ import annotations | 2026-02-01 | 2026-04-12 | - |
| `scripts/boundary_triage.py` | from __future__ import annotations | 2026-02-01 | 2026-04-12 | - |

## Pinned Sources

- [`scripts/boundary_autofix.py`](https://github.com/chris-page-gov/mcp-geo/blob/923807292e3a134ad8214be3de523caa7fdce7c5/scripts/boundary_autofix.py)
- [`scripts/boundary_cache_ingest.py`](https://github.com/chris-page-gov/mcp-geo/blob/923807292e3a134ad8214be3de523caa7fdce7c5/scripts/boundary_cache_ingest.py)
- [`scripts/boundary_cache_schema.sql`](https://github.com/chris-page-gov/mcp-geo/blob/923807292e3a134ad8214be3de523caa7fdce7c5/scripts/boundary_cache_schema.sql)
- [`scripts/boundary_pipeline.py`](https://github.com/chris-page-gov/mcp-geo/blob/923807292e3a134ad8214be3de523caa7fdce7c5/scripts/boundary_pipeline.py)
- [`scripts/boundary_run_tracker.py`](https://github.com/chris-page-gov/mcp-geo/blob/923807292e3a134ad8214be3de523caa7fdce7c5/scripts/boundary_run_tracker.py)
- [`scripts/boundary_status_ticker.py`](https://github.com/chris-page-gov/mcp-geo/blob/923807292e3a134ad8214be3de523caa7fdce7c5/scripts/boundary_status_ticker.py)
- [`scripts/boundary_triage.py`](https://github.com/chris-page-gov/mcp-geo/blob/923807292e3a134ad8214be3de523caa7fdce7c5/scripts/boundary_triage.py)
