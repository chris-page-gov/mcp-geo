---
title: "Topic Threads"
kb_kind: "timeline_note"
source_paths:
  - "CHANGELOG.md"
  - "CONTEXT.md"
  - "PROGRESS.MD"
source_commit: "bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851"
source_commit_dirty: true
source_urls:
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/CHANGELOG.md"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/CONTEXT.md"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/PROGRESS.MD"
source_hashes:
  CHANGELOG.md: "9f8a72a8b1f9f4d8480398e9ea1002aa504c97bce87633cdf88c3f9b61132334"
  CONTEXT.md: "84fc74b172fc3fdd6b3cceb4ee7e5b77f3785b252ad0b3670de07b61671ce055"
  PROGRESS.MD: "4f33a28d5b0311dd173afe1b2a33d1b58a5f3c49eab1fea8a251ee3d3c3afe5b"
generated_at: "2026-04-06T09:00:35Z"
evidence_scope: "canon"
first_seen_date: "2025-08-20"
last_validated_at: "2026-04-06T09:00:35Z"
---
# Topic Threads

The groupings below are keyword-based evidence threads. They connect explicit traces without
guessing why the work happened.

## Authentication and Security

- `2026-04-06` `tests/test_config_secret_file.py`: from server.config import (
- `2026-04-06` `scripts/landis_release_reconciliation.py`: Generate a LandIS release-surface reconciliation manifest. This compares three public-facing surfaces: 1. The authenticated ArcGIS portal inventory already captured in-repo. 2. Public LandIS website dataset/service pages that are linked from the current navigation but are not present in the mirrored ArcGIS portal slice. 3. Matching `data.gov.uk` package metadata where it exists. The output is a machine-readable JSON manifest that records: - public page reachability and page size - whether each item appears in the current portal inventory - likely related portal datasets, where known - candidate `data.gov.uk` package matches - a conservative approximate size estimate when a public page is dataset-like and there is a defensible analogue in the portal inventory
- `2026-04-05` `scripts/landis_full_release_archive.py`: Create and verify a full LandIS release archive on local storage. This script treats the existing authenticated ArcGIS portal archive as one verified component and then mirrors the remaining public LandIS release surfaces: 1. Public LandIS website dataset/service pages that are linked from the current official navigation but absent from the mirrored portal slice. 2. Relevant `data.gov.uk` Cranfield/LandIS package metadata and their published resource URLs. The script writes a machine-readable release manifest plus a completion verification manifest. It is designed to be rerunnable and resumable.
- `2026-04-05` `docs/reports/landis_release_surface_reconciliation_2026-04-05.md`: Date: 2026-04-05 Check whether the completed authenticated LandIS portal mirror is the full released LandIS data surface, or whether the current release still includes additional public/open or separately distributed dat
- `2026-04-05` `docs/reports/landis_phase_2_surfacing_plan_2026-04-04.md`: Date: 2026-04-04 Updated: 2026-04-05 Turn the completed authenticated LandIS archive into a deliberate phase-2 MCP surface without destabilizing the validated Warwickshire MVP. The immediate goal is not to expose every d
- `2026-04-04` `scripts/landis_portal_inventory.py`: Build an authenticated LandIS portal inventory from an Atlas browser session. This script is intended for local operator use after signing into the LandIS portal in ChatGPT Atlas on macOS. It discovers an ArcGIS access token from the Atlas Chromium history database, enumerates the protected LandIS portal catalog, enriches key item types, and writes both JSON and Markdown inventories.
- `2026-04-04` `scripts/landis_portal_download.py`: Download authenticated LandIS portal items to local storage. The script reuses the Atlas-authenticated LandIS portal route. It expects the user to have an active LandIS portal session in ChatGPT Atlas, then mirrors the catalog metadata and item payloads to a destination directory. Feature services are exported as raw service metadata plus per-layer GeoJSON/JSON batches.
- `2026-04-04` `docs/reports/landis_portal_inventory_2026-04-04.md`: Generated: `2026-04-04T19:38:31.702172+00:00` This inventory was generated from an authenticated LandIS portal session in ChatGPT Atlas. It records the accessible ArcGIS catalog items without storing the session token. -
- `2026-03-24` `tests/test_security.py`: from server.security import configured_secrets, mask_in_text, mask_in_value, redact
- `2026-03-24` `tests/test_owasp_mcp_validation.py`: from __future__ import annotations
- `2026-03-24` `server/security.py`: REDACTION_TOKEN = "[REDACTED]"
- `2026-03-24` `server/owasp_mcp_validation.py`: from __future__ import annotations
- `2026-03-24` `docs/troubleshooting.md`: This guide lists common error codes emitted by the MCP Geo server and suggested remediation steps. Need OS credentials or trial access before troubleshooting auth errors? - OS API authentication overview: <https://docs.o
- `2026-03-24` `docs/spec_package/08_observability_ops.md`: - Structured logs via `loguru`. - Correlation IDs included in error payloads when available. - Prometheus endpoint at `/metrics`. - When MCP HTTP auth is enabled, `/metrics` shares the same auth boundary as `/mcp`, raw `
- `2026-03-24` `docs/spec_package/07_security_privacy.md`: - OS and ONS credentials can be injected via `*_FILE` environment variables. - Remote `/mcp` can require HS256 JWT bearer tokens with issuer, audience, scope, and subject checks. - Logs and generic exception responses re
- `2026-03-24` `docs/reports/mcp_geo_full_code_review_2026-03-24.md`: Date: 2026-03-24 Reviewer: Codex GPT-5 Scope: architecture, system design, documentation, software engineering, security, test and delivery posture MCP-Geo is a substantial and unusually well-documented MCP server with s

## LandIS

- `2026-04-06` `tests/test_server_landis.py`: from __future__ import annotations
- `2026-04-06` `tests/test_landis_release_reconciliation.py`: from scripts.landis_release_reconciliation import strip_html
- `2026-04-06` `server/landis.py`: from __future__ import annotations
- `2026-04-06` `scripts/landis_release_reconciliation.py`: Generate a LandIS release-surface reconciliation manifest. This compares three public-facing surfaces: 1. The authenticated ArcGIS portal inventory already captured in-repo. 2. Public LandIS website dataset/service pages that are linked from the current navigation but are not present in the mirrored ArcGIS portal slice. 3. Matching `data.gov.uk` package metadata where it exists. The output is a machine-readable JSON manifest that records: - public page reachability and page size - whether each item appears in the current portal inventory - likely related portal datasets, where known - candidate `data.gov.uk` package matches - a conservative approximate size estimate when a public page is dataset-like and there is a defensible analogue in the portal inventory
- `2026-04-05` `tools/landis_nsi.py`: from __future__ import annotations
- `2026-04-05` `tools/landis_natmap.py`: from __future__ import annotations
- `2026-04-05` `tools/landis_common.py`: from __future__ import annotations
- `2026-04-05` `tools/landis_archive.py`: from __future__ import annotations
- `2026-04-05` `tests/test_landis_tools.py`: from __future__ import annotations
- `2026-04-05` `tests/test_landis_resources.py`: from __future__ import annotations
- `2026-04-05` `tests/test_landis_ingest.py`: from __future__ import annotations
- `2026-04-05` `scripts/landis_schema.sql`: CREATE SCHEMA IF NOT EXISTS landis;
- `2026-04-05` `scripts/landis_phase2_ingest.py`: from __future__ import annotations
- `2026-04-05` `scripts/landis_full_release_archive.py`: Create and verify a full LandIS release archive on local storage. This script treats the existing authenticated ArcGIS portal archive as one verified component and then mirrors the remaining public LandIS release surfaces: 1. Public LandIS website dataset/service pages that are linked from the current official navigation but absent from the mirrored portal slice. 2. Relevant `data.gov.uk` Cranfield/LandIS package metadata and their published resource URLs. The script writes a machine-readable release manifest plus a completion verification manifest. It is designed to be rerunnable and resumable.
- `2026-04-05` `scripts/landis_archive_triage.py`: from __future__ import annotations
- `2026-04-05` `resources/landis_products.json`: JSON object keys: products, sources, updatedAt, version

## Map Delivery

- `2026-04-05` `tools/landis_natmap.py`: from __future__ import annotations
- `2026-04-05` `docs/benchmarking/codex_vs_claude_host_benchmark.md`: This runbook adds Codex as a first-class MCP host benchmark target for `mcp-geo` alongside Claude Desktop. For any cross-client benchmark or comparison, all clients must hit the same PostGIS-backed cache and route-graph
- `2026-04-04` `troubleshooting/Meeth North Devon/meeth_3d_buildings.html`: OS MasterMap · 3D Buildings
- `2026-04-04` `troubleshooting/Meeth North Devon/Start Meeth 3D Map.command`: ── Meeth 3D Buildings Viewer ──────────────────────────────────────
- `2026-04-04` `tests/test_route_graph_integration.py`: from __future__ import annotations
- `2026-04-04` `scripts/landis_portal_download.py`: Download authenticated LandIS portal items to local storage. The script reuses the Atlas-authenticated LandIS portal route. It expects the user to have an active LandIS portal session in ChatGPT Atlas, then mirrors the catalog metadata and item payloads to a destination directory. Feature services are exported as raw service metadata plus per-layer GeoJSON/JSON batches.
- `2026-04-04` `resources/landis/soil_data_structures.md`: This MCP resource is a concise operational summary of the LandIS soil data structures paper for implementation and tool-output interpretation. - NATMAP association polygons identify mapping units using association keys s
- `2026-04-04` `resources/landis/soil_classification.md`: This MCP resource is a concise operational summary of the LandIS national soil map and soil-classification guidance for non-specialist callers. - Soilscapes classes are generalized landscape-scale classes intended for sc
- `2026-03-16` `tests/test_os_mcp_route_query.py`: from fastapi.testclient import TestClient
- `2026-03-16` `docs/reports/MCP-Geo Stakeholder Mapping and Value Propositions.docx`: Mcp Geo Stakeholder Mapping And Value Propositions
- `2026-03-16` `docs/Mapping Ordnance Survey & ONS APIs to the Model Context Protocol (MCP).docx`: Mapping Ordnance Survey & Ons Apis To The Model Context Protocol (mcp)
- `2026-03-15` `tests/test_os_map_tools.py`: from __future__ import annotations
- `2026-03-15` `docs/Boundaries.json`: JSON object keys: boundary_families, catalogue_sources, completion_definition, generated_at_utc, legacy_field_mappings, manifest_version, optional_dynamic_harvest_rules, postgis_defaults
- `2026-03-14` `tools/os_route.py`: from __future__ import annotations
- `2026-03-14` `tools/os_map.py`: from __future__ import annotations
- `2026-03-14` `server/mcp/http_route_auth.py`: from __future__ import annotations

## Evaluation and Evidence

- `2026-04-05` `tests/test_evaluation_harness_full.py`: import json
- `2026-04-05` `scripts/check_shared_benchmark_cache.sh`: set -euo pipefail
- `2026-04-05` `docs/reports/landis_release_surface_reconciliation_2026-04-05.md`: Date: 2026-04-05 Check whether the completed authenticated LandIS portal mirror is the full released LandIS data surface, or whether the current release still includes additional public/open or separately distributed dat
- `2026-04-05` `docs/reports/landis_phase_2_surfacing_plan_2026-04-04.md`: Date: 2026-04-04 Updated: 2026-04-05 Turn the completed authenticated LandIS archive into a deliberate phase-2 MCP surface without destabilizing the validated Warwickshire MVP. The immediate goal is not to expose every d
- `2026-04-05` `docs/reports/README.md`: This folder contains human-readable run reports and investigation summaries. - 2026-03-11: [MCP-Geo Analytical Index](mcp_geo_analytical_index_2026-03-11.md) - 2026-03-11: [MCP-Geo Analytical Index (PDF)](mcp_geo_analyti
- `2026-04-05` `docs/evaluation.md`: This document describes the evaluation framework for the MCP Geo server. The framework is built around a question suite, a scoring rubric, and a harness that exercises tools through HTTP endpoints. The evaluation framewo
- `2026-04-05` `docs/benchmarking/codex_vs_claude_host_benchmark.md`: This runbook adds Codex as a first-class MCP host benchmark target for `mcp-geo` alongside Claude Desktop. For any cross-client benchmark or comparison, all clients must hit the same PostGIS-backed cache and route-graph
- `2026-04-04` `troubleshooting/Meeth North Devon/meeth_openreach_report.html`: Meeth, North Devon — Openreach First Rural Intervention
- `2026-04-04` `troubleshooting/Meeth North Devon/Meeth-N-Devon-Cowork-failed.md`: Meeth, North Devon Troubleshooting Report ========================================= Date ---- 2026-03-25 Scope ----- This write-up replaces the rough transcript dump that was previously stored in this folder. It diagnose
- `2026-04-04` `troubleshooting/Meeth North Devon/Meeth, North Devon report.docx`: Meeth, North Devon Report
- `2026-04-04` `resources/prompts/evaluation_prompts.json`: JSON object keys: prompts
- `2026-04-04` `docs/reports/landis_portal_inventory_2026-04-04.md`: Generated: `2026-04-04T19:38:31.702172+00:00` This inventory was generated from an authenticated LandIS portal session in ChatGPT Atlas. It records the accessible ArcGIS catalog items without storing the session token. -
- `2026-03-24` `docs/reports/mcp_geo_full_code_review_2026-03-24.md`: Date: 2026-03-24 Reviewer: Codex GPT-5 Scope: architecture, system design, documentation, software engineering, security, test and delivery posture MCP-Geo is a substantial and unusually well-documented MCP server with s
- `2026-03-24` `Gemini-Code-Review.md`: This report provides a comprehensive code review of the **MCP Geo Server** repository, an advanced Model Context Protocol (MCP) implementation for UK geospatial and statistical data. The project demonstrates state-of-the
- `2026-03-17` `tests/test_trace_session.py`: from __future__ import annotations
- `2026-03-17` `tests/test_host_benchmark.py`: from __future__ import annotations

## CI and Release

- `2026-04-06` `tests/test_mcp_docker_local.py`: from __future__ import annotations
- `2026-04-06` `tests/test_landis_release_reconciliation.py`: from scripts.landis_release_reconciliation import strip_html
- `2026-04-06` `scripts/mcp-docker-local`: set -euo pipefail
- `2026-04-06` `scripts/landis_release_reconciliation.py`: Generate a LandIS release-surface reconciliation manifest. This compares three public-facing surfaces: 1. The authenticated ArcGIS portal inventory already captured in-repo. 2. Public LandIS website dataset/service pages that are linked from the current navigation but are not present in the mirrored ArcGIS portal slice. 3. Matching `data.gov.uk` package metadata where it exists. The output is a machine-readable JSON manifest that records: - public page reachability and page size - whether each item appears in the current portal inventory - likely related portal datasets, where known - candidate `data.gov.uk` package matches - a conservative approximate size estimate when a public page is dataset-like and there is a defensible analogue in the portal inventory
- `2026-04-06` `README.md`: A research Model Context Protocol (MCP) server for geospatial (Ordnance Survey) and statistical (Office of National Statistics) data. If you have Docker installed and Internet access, have this running in 3 minutes. This
- `2026-04-06` `PROGRESS.MD`: This file tracks how the implementation compares to the original proposal and later documentation as the MCP specification evolved. Last updated: 2026-04-06 Legend: pending, in_progress, done, blocked | Workstream | Stat
- `2026-04-05` `scripts/landis_full_release_archive.py`: Create and verify a full LandIS release archive on local storage. This script treats the existing authenticated ArcGIS portal archive as one verified component and then mirrors the remaining public LandIS release surfaces: 1. Public LandIS website dataset/service pages that are linked from the current official navigation but absent from the mirrored portal slice. 2. Relevant `data.gov.uk` Cranfield/LandIS package metadata and their published resource URLs. The script writes a machine-readable release manifest plus a completion verification manifest. It is designed to be rerunnable and resumable.
- `2026-04-05` `research/landis-data-source/landis_release_reconciliation_2026-04-05.json`: JSON object keys: archiveManifestPath, entries, generatedAt, portalInventoryPath, portalSummary, scopeNote
- `2026-04-05` `research/landis-data-source/landis_full_release_manifest_2026-04-05.json`: JSON object keys: dataGovPackages, destination, generatedAt, portalComponent, publicItems, repoPublicReconciliationGeneratedAt, repoPublicReconciliationManifest, summary
- `2026-04-05` `research/landis-data-source/landis_archive_triage_2026-04-05.json`: JSON object keys: fullReleaseArchiveDir, generatedAt, portalArchiveDir, portalItems, summary, supplementaryDataGovPackages, supplementaryPublicItems, version
- `2026-04-05` `docs/reports/landis_release_surface_reconciliation_2026-04-05.md`: Date: 2026-04-05 Check whether the completed authenticated LandIS portal mirror is the full released LandIS data surface, or whether the current release still includes additional public/open or separately distributed dat
- `2026-04-05` `docs/reports/landis_phase_2_surfacing_plan_2026-04-04.md`: Date: 2026-04-04 Updated: 2026-04-05 Turn the completed authenticated LandIS archive into a deliberate phase-2 MCP surface without destabilizing the validated Warwickshire MVP. The immediate goal is not to expose every d
- `2026-04-05` `docs/evaluation.md`: This document describes the evaluation framework for the MCP Geo server. The framework is built around a question suite, a scoring rubric, and a harness that exercises tools through HTTP endpoints. The evaluation framewo
- `2026-04-04` `tools/council_tax.py`: from __future__ import annotations
- `2026-04-04` `tests/test_council_tax_gold_eval.py`: from __future__ import annotations
- `2026-04-04` `tests/test_council_tax_band.py`: from __future__ import annotations

## Knowledge Base

- `2026-04-06` `CHANGELOG.md`: All notable changes to this project will be documented in this file. - Added a repo-wide generated Obsidian knowledge base under `Obsidian/MCP Geo Knowledge Base/`, backed by `scripts/obsidian_kb_common.py`, `scripts/bui
