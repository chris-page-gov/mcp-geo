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
source_commit: "bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851"
source_commit_dirty: true
source_urls:
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/scripts/landis_archive_triage.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/scripts/landis_full_release_archive.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/scripts/landis_ingest.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/scripts/landis_phase2_ingest.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/scripts/landis_portal_download.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/scripts/landis_portal_inventory.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/scripts/landis_release_reconciliation.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/scripts/landis_schema.sql"
source_hashes:
  scripts/landis_archive_triage.py: "b46f57b4709c3dbfa25240625027cfc9af535a755f183029e72c9a2d4f235894"
  scripts/landis_full_release_archive.py: "fc2a1d35245ca4e5a4054cda7fd3d36d621c701708427ba929fd9b565c1a4f23"
  scripts/landis_ingest.py: "7d80d2ba94792a59fe90d380f8ca4d7197fa650720a10444b6138a95299cb16c"
  scripts/landis_phase2_ingest.py: "24eee6b5d87de890262cb4cfa222e714409d43fefeaa5c440b2e5eba961c2ee2"
  scripts/landis_portal_download.py: "ce92c8dbdcda89b3e6edfee36a0e976bac5c839cbbb5f943115c97a038b18316"
  scripts/landis_portal_inventory.py: "d38a0a5c4df6303adb37e6605246abfb1e029f3e88100dfcf9ddb1912ed3eed2"
  scripts/landis_release_reconciliation.py: "52f1b7bc207fe51a35e6f8551a18419a2989a7cca4b0ed2156b924debefb7b88"
  scripts/landis_schema.sql: "aa0b2da300b948950543dc17d50339eea511a83041dbf7cc366c4a29d0bcfddd"
generated_at: "2026-04-06T09:00:35Z"
evidence_scope: "canon"
first_seen_date: "2026-04-04"
last_validated_at: "2026-04-06T09:00:35Z"
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
| `scripts/landis_ingest.py` | from __future__ import annotations | 2026-04-04 | 2026-04-04 | `tests/test_landis_ingest.py` |
| `scripts/landis_phase2_ingest.py` | from __future__ import annotations | 2026-04-05 | 2026-04-05 | `tests/test_landis_ingest.py` |
| `scripts/landis_portal_download.py` | Download authenticated LandIS portal items to local storage. The script reuses the Atlas-authenticated LandIS portal rou | 2026-04-04 | 2026-04-04 | - |
| `scripts/landis_portal_inventory.py` | Build an authenticated LandIS portal inventory from an Atlas browser session. This script is intended for local operator | 2026-04-04 | 2026-04-04 | - |
| `scripts/landis_release_reconciliation.py` | Generate a LandIS release-surface reconciliation manifest. This compares three public-facing surfaces: 1. The authentica | 2026-04-05 | 2026-04-06 | `tests/test_landis_release_reconciliation.py` |
| `scripts/landis_schema.sql` | CREATE SCHEMA IF NOT EXISTS landis; | 2026-04-04 | 2026-04-05 | - |

## Pinned Sources

- [`scripts/landis_archive_triage.py`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/scripts/landis_archive_triage.py)
- [`scripts/landis_full_release_archive.py`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/scripts/landis_full_release_archive.py)
- [`scripts/landis_ingest.py`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/scripts/landis_ingest.py)
- [`scripts/landis_phase2_ingest.py`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/scripts/landis_phase2_ingest.py)
- [`scripts/landis_portal_download.py`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/scripts/landis_portal_download.py)
- [`scripts/landis_portal_inventory.py`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/scripts/landis_portal_inventory.py)
- [`scripts/landis_release_reconciliation.py`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/scripts/landis_release_reconciliation.py)
- [`scripts/landis_schema.sql`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/scripts/landis_schema.sql)
