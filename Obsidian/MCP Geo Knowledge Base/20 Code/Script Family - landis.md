---
title: "Script Family - landis"
kb_kind: "code_family"
source_paths:
  - "scripts/landis_archive_triage.py"
  - "scripts/landis_full_release_archive.py"
  - "scripts/landis_ingest.py"
  - "scripts/landis_phase2_ingest.py"
  - "scripts/landis_portal_download.py"
  - "scripts/landis_portal_inventory.py"
  - "scripts/landis_release_reconciliation.py"
  - "scripts/landis_schema.sql"
source_commit: "004e7d4748422b44133399279803c8cb2b766a1c"
source_commit_dirty: true
source_urls:
  - "https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/scripts/landis_archive_triage.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/scripts/landis_full_release_archive.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/scripts/landis_ingest.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/scripts/landis_phase2_ingest.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/scripts/landis_portal_download.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/scripts/landis_portal_inventory.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/scripts/landis_release_reconciliation.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/scripts/landis_schema.sql"
source_hashes:
  scripts/landis_archive_triage.py: "sha256:b46f57b4-709c3dbf-a2524062-5027cfc9-af535a75-5f183029-e72c9a2d-4f235894"
  scripts/landis_full_release_archive.py: "sha256:fc2a1d35-245ca4e5-a4054cda-7fd3d36d-621c7017-08427ba9-29fd9b56-5c1a4f23"
  scripts/landis_ingest.py: "sha256:fd201343-49f7c35c-6617b1b1-ddfa6eb0-f26a6436-aa1272f2-013a9bd5-4f5f633f"
  scripts/landis_phase2_ingest.py: "sha256:c0ef2b1f-69a267fb-f23e0fdf-8907f7f9-11832cce-a3febbed-26f366ab-74868e72"
  scripts/landis_portal_download.py: "sha256:ce92c8db-dcda89b3-e6edfee3-6a0e976b-ac5c839c-bbb5f943-115c97a0-38b18316"
  scripts/landis_portal_inventory.py: "sha256:d38a0a5c-4df6303a-db37e660-5246abfb-1e029f3e-88100dfc-f9ddb191-2ed3eed2"
  scripts/landis_release_reconciliation.py: "sha256:52f1b7bc-207fe51a-35e6f855-1a18419a-2989a7cc-a4b0ed21-56b924de-befb7b88"
  scripts/landis_schema.sql: "sha256:aa0b2da3-00b94895-0543dc17-d50339ee-a511a830-41dbf7cc-366c4a29-d0bcfddd"
generated_at: "2026-04-06T14:09:00Z"
evidence_scope: "canon"
first_seen_date: "2026-04-04"
last_validated_at: "2026-04-06T14:09:00Z"
---
# Script Family - landis

## Evidence Scope

- Categories: `code_runtime`
- Source file count: 8

## Source Inventory

| Path | Summary | First Seen | Last Commit | Related Tests |
| --- | --- | --- | --- | --- |
| `scripts/landis_archive_triage.py` | from __future__ import annotations | 2026-04-05 | 2026-04-05 | `tests/test_landis_ingest.py`, `tests/test_landis_tools.py`, `tests/test_server_landis.py` |
| `scripts/landis_full_release_archive.py` | Create and verify a full LandIS release archive on local storage. This script treats the existing authenticated ArcGIS p | 2026-04-05 | 2026-04-05 | `tests/test_server_landis.py` |
| `scripts/landis_ingest.py` | from __future__ import annotations | 2026-04-04 | 2026-04-06 | `tests/test_landis_ingest.py` |
| `scripts/landis_phase2_ingest.py` | from __future__ import annotations | 2026-04-05 | 2026-04-06 | `tests/test_landis_ingest.py` |
| `scripts/landis_portal_download.py` | Download authenticated LandIS portal items to local storage. The script reuses the Atlas-authenticated LandIS portal rou | 2026-04-04 | 2026-04-04 | - |
| `scripts/landis_portal_inventory.py` | Build an authenticated LandIS portal inventory from an Atlas browser session. This script is intended for local operator | 2026-04-04 | 2026-04-04 | - |
| `scripts/landis_release_reconciliation.py` | Generate a LandIS release-surface reconciliation manifest. This compares three public-facing surfaces: 1. The authentica | 2026-04-05 | 2026-04-06 | `tests/test_landis_release_reconciliation.py` |
| `scripts/landis_schema.sql` | CREATE SCHEMA IF NOT EXISTS landis; | 2026-04-04 | 2026-04-05 | - |

## Pinned Sources

- [`scripts/landis_archive_triage.py`](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/scripts/landis_archive_triage.py)
- [`scripts/landis_full_release_archive.py`](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/scripts/landis_full_release_archive.py)
- [`scripts/landis_ingest.py`](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/scripts/landis_ingest.py)
- [`scripts/landis_phase2_ingest.py`](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/scripts/landis_phase2_ingest.py)
- [`scripts/landis_portal_download.py`](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/scripts/landis_portal_download.py)
- [`scripts/landis_portal_inventory.py`](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/scripts/landis_portal_inventory.py)
- [`scripts/landis_release_reconciliation.py`](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/scripts/landis_release_reconciliation.py)
- [`scripts/landis_schema.sql`](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/scripts/landis_schema.sql)
