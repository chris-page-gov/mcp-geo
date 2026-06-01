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
source_commit: "2d7d7ba76db4643934aa2bd1b294e0e352285702"
source_commit_dirty: true
source_urls:
  - "https://github.com/chris-page-gov/mcp-geo/blob/2d7d7ba76db4643934aa2bd1b294e0e352285702/scripts/landis_archive_triage.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/2d7d7ba76db4643934aa2bd1b294e0e352285702/scripts/landis_full_release_archive.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/2d7d7ba76db4643934aa2bd1b294e0e352285702/scripts/landis_ingest.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/2d7d7ba76db4643934aa2bd1b294e0e352285702/scripts/landis_phase2_ingest.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/2d7d7ba76db4643934aa2bd1b294e0e352285702/scripts/landis_portal_download.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/2d7d7ba76db4643934aa2bd1b294e0e352285702/scripts/landis_portal_inventory.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/2d7d7ba76db4643934aa2bd1b294e0e352285702/scripts/landis_release_reconciliation.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/2d7d7ba76db4643934aa2bd1b294e0e352285702/scripts/landis_schema.sql"
source_hashes:
  scripts/landis_archive_triage.py: "sha256:b46f57b4-709c3dbf-a2524062-5027cfc9-af535a75-5f183029-e72c9a2d-4f235894"
  scripts/landis_full_release_archive.py: "sha256:186fd0a0-4756d962-8fa9c63c-3303c541-da02c76c-46df71f1-a11a038b-212f5e6f"
  scripts/landis_ingest.py: "sha256:fd201343-49f7c35c-6617b1b1-ddfa6eb0-f26a6436-aa1272f2-013a9bd5-4f5f633f"
  scripts/landis_phase2_ingest.py: "sha256:bf4338e1-3c469194-9132129b-e51fe5a3-24582178-dc536e79-c40eba8f-dd3795c3"
  scripts/landis_portal_download.py: "sha256:840d61a0-50d29a6a-04d7f448-401bd68c-c92024b8-e02a50df-be533e3d-5ee1514f"
  scripts/landis_portal_inventory.py: "sha256:d38a0a5c-4df6303a-db37e660-5246abfb-1e029f3e-88100dfc-f9ddb191-2ed3eed2"
  scripts/landis_release_reconciliation.py: "sha256:01efbd19-87c6f09d-c26db717-460cb54e-f7d59119-012887d7-80693b91-42945742"
  scripts/landis_schema.sql: "sha256:aa0b2da3-00b94895-0543dc17-d50339ee-a511a830-41dbf7cc-366c4a29-d0bcfddd"
generated_at: "2026-06-01T01:38:32Z"
evidence_scope: "canon"
first_seen_date: "2026-04-04"
last_validated_at: "2026-06-01T01:38:32Z"
---
# Script Family - landis

## Evidence Scope

- Categories: `code_runtime`
- Source file count: 8

## Source Inventory

| Path | Summary | First Seen | Last Commit | Related Tests |
| --- | --- | --- | --- | --- |
| `scripts/landis_archive_triage.py` | from __future__ import annotations | 2026-04-05 | 2026-04-05 | `tests/test_landis_ingest.py`, `tests/test_landis_tools.py`, `tests/test_server_landis.py` |
| `scripts/landis_full_release_archive.py` | Create and verify a full LandIS release archive on local storage. This script treats the existing authenticated ArcGIS p | 2026-04-05 | 2026-04-12 | `tests/test_server_landis.py` |
| `scripts/landis_ingest.py` | from __future__ import annotations | 2026-04-04 | 2026-04-06 | `tests/test_landis_ingest.py` |
| `scripts/landis_phase2_ingest.py` | from __future__ import annotations | 2026-04-05 | 2026-04-12 | `tests/test_landis_ingest.py` |
| `scripts/landis_portal_download.py` | Download authenticated LandIS portal items to local storage. The script reuses the Atlas-authenticated LandIS portal rou | 2026-04-04 | 2026-04-12 | - |
| `scripts/landis_portal_inventory.py` | Build an authenticated LandIS portal inventory from an Atlas browser session. This script is intended for local operator | 2026-04-04 | 2026-04-04 | - |
| `scripts/landis_release_reconciliation.py` | Generate a LandIS release-surface reconciliation manifest. This compares three public-facing surfaces: 1. The authentica | 2026-04-05 | 2026-04-12 | `tests/test_landis_release_reconciliation.py` |
| `scripts/landis_schema.sql` | CREATE SCHEMA IF NOT EXISTS landis; | 2026-04-04 | 2026-04-05 | - |

## Pinned Sources

- [`scripts/landis_archive_triage.py`](https://github.com/chris-page-gov/mcp-geo/blob/2d7d7ba76db4643934aa2bd1b294e0e352285702/scripts/landis_archive_triage.py)
- [`scripts/landis_full_release_archive.py`](https://github.com/chris-page-gov/mcp-geo/blob/2d7d7ba76db4643934aa2bd1b294e0e352285702/scripts/landis_full_release_archive.py)
- [`scripts/landis_ingest.py`](https://github.com/chris-page-gov/mcp-geo/blob/2d7d7ba76db4643934aa2bd1b294e0e352285702/scripts/landis_ingest.py)
- [`scripts/landis_phase2_ingest.py`](https://github.com/chris-page-gov/mcp-geo/blob/2d7d7ba76db4643934aa2bd1b294e0e352285702/scripts/landis_phase2_ingest.py)
- [`scripts/landis_portal_download.py`](https://github.com/chris-page-gov/mcp-geo/blob/2d7d7ba76db4643934aa2bd1b294e0e352285702/scripts/landis_portal_download.py)
- [`scripts/landis_portal_inventory.py`](https://github.com/chris-page-gov/mcp-geo/blob/2d7d7ba76db4643934aa2bd1b294e0e352285702/scripts/landis_portal_inventory.py)
- [`scripts/landis_release_reconciliation.py`](https://github.com/chris-page-gov/mcp-geo/blob/2d7d7ba76db4643934aa2bd1b294e0e352285702/scripts/landis_release_reconciliation.py)
- [`scripts/landis_schema.sql`](https://github.com/chris-page-gov/mcp-geo/blob/2d7d7ba76db4643934aa2bd1b294e0e352285702/scripts/landis_schema.sql)
