---
title: "Topic Threads"
kb_kind: "timeline_note"
source_paths:
  - "CHANGELOG.md"
  - "CONTEXT.md"
  - "PROGRESS.MD"
source_commit: "2d7d7ba76db4643934aa2bd1b294e0e352285702"
source_commit_dirty: true
source_urls:
  - "https://github.com/chris-page-gov/mcp-geo/blob/2d7d7ba76db4643934aa2bd1b294e0e352285702/CHANGELOG.md"
  - "https://github.com/chris-page-gov/mcp-geo/blob/2d7d7ba76db4643934aa2bd1b294e0e352285702/CONTEXT.md"
  - "https://github.com/chris-page-gov/mcp-geo/blob/2d7d7ba76db4643934aa2bd1b294e0e352285702/PROGRESS.MD"
source_hashes:
  CHANGELOG.md: "sha256:7609427d-3636dc27-ba969ca5-4ed0c777-8469c7a8-5fb9d2db-63dad5eb-34168c23"
  CONTEXT.md: "sha256:320e381f-5f7471c2-97d5ed69-8c72003e-d5f4c724-3426eb51-ca99076b-eede3adb"
  PROGRESS.MD: "sha256:cb45234f-a9a2e553-76fab9f1-837fe7ab-f8cfdc22-083df4d5-88ada35f-40ecefaa"
generated_at: "2026-06-01T01:38:32Z"
evidence_scope: "canon"
first_seen_date: "2025-08-20"
last_validated_at: "2026-06-01T01:38:32Z"
---
# Topic Threads

The groupings below are keyword-based evidence threads. They connect explicit traces without
guessing why the work happened.

## Authentication and Security

- `2026-05-13` `docs/troubleshooting.md`: This guide lists common error codes emitted by the MCP Geo server and suggested remediation steps. Need OS credentials or trial access before troubleshooting auth errors? - OS API authentication overview: <https://docs.o
- `2026-05-13` `docs/reports/landis_leacs_access_probe_2026-05-13.md`: This probe checked whether the LandIS LEACS data needed for wider pipe-risk coverage can be downloaded from the available public and authenticated routes. Result: LEACS is not currently available as a downloadable payloa
- `2026-04-22` `tests/test_security.py`: from server.security import configured_secrets, mask_in_text, mask_in_value, redact
- `2026-04-22` `tests/test_config_secret_file.py`: from typing import ClassVar
- `2026-04-22` `server/security.py`: REDACTION_TOKEN = "[REDACTED]"
- `2026-04-12` `scripts/landis_release_reconciliation.py`: Generate a LandIS release-surface reconciliation manifest. This compares three public-facing surfaces: 1. The authenticated ArcGIS portal inventory already captured in-repo. 2. Public LandIS website dataset/service pages that are linked from the current navigation but are not present in the mirrored ArcGIS portal slice. 3. Matching `data.gov.uk` package metadata where it exists. The output is a machine-readable JSON manifest that records: - public page reachability and page size - whether each item appears in the current portal inventory - likely related portal datasets, where known - candidate `data.gov.uk` package matches - a conservative approximate size estimate when a public page is dataset-like and there is a defensible analogue in the portal inventory
- `2026-04-12` `scripts/landis_portal_download.py`: Download authenticated LandIS portal items to local storage. The script reuses the Atlas-authenticated LandIS portal route. It expects the user to have an active LandIS portal session in ChatGPT Atlas, then mirrors the catalog metadata and item payloads to a destination directory. Feature services are exported as raw service metadata plus per-layer GeoJSON/JSON batches.
- `2026-04-12` `scripts/landis_full_release_archive.py`: Create and verify a full LandIS release archive on local storage. This script treats the existing authenticated ArcGIS portal archive as one verified component and then mirrors the remaining public LandIS release surfaces: 1. Public LandIS website dataset/service pages that are linked from the current official navigation but absent from the mirrored portal slice. 2. Relevant `data.gov.uk` Cranfield/LandIS package metadata and their published resource URLs. The script writes a machine-readable release manifest plus a completion verification manifest. It is designed to be rerunnable and resumable.
- `2026-04-10` `scripts/validate_owasp_mcp_server.py`: from __future__ import annotations
- `2026-04-10` `scripts/generate_owasp_mcp_tool_manifest.py`: from __future__ import annotations
- `2026-04-05` `docs/reports/landis_release_surface_reconciliation_2026-04-05.md`: Date: 2026-04-05 Check whether the completed authenticated LandIS portal mirror is the full released LandIS data surface, or whether the current release still includes additional public/open or separately distributed dat
- `2026-04-05` `docs/reports/landis_phase_2_surfacing_plan_2026-04-04.md`: Date: 2026-04-04 Updated: 2026-04-05 Turn the completed authenticated LandIS archive into a deliberate phase-2 MCP surface without destabilizing the validated Warwickshire MVP. The immediate goal is not to expose every d
- `2026-04-04` `scripts/landis_portal_inventory.py`: Build an authenticated LandIS portal inventory from an Atlas browser session. This script is intended for local operator use after signing into the LandIS portal in ChatGPT Atlas on macOS. It discovers an ArcGIS access token from the Atlas Chromium history database, enumerates the protected LandIS portal catalog, enriches key item types, and writes both JSON and Markdown inventories.
- `2026-04-04` `docs/reports/landis_portal_inventory_2026-04-04.md`: Generated: `2026-04-04T19:38:31.702172+00:00` This inventory was generated from an authenticated LandIS portal session in ChatGPT Atlas. It records the accessible ArcGIS catalog items without storing the session token. -
- `2026-03-24` `tests/test_owasp_mcp_validation.py`: from __future__ import annotations
- `2026-03-24` `server/owasp_mcp_validation.py`: from __future__ import annotations

## LandIS

- `2026-05-13` `research/landis-data-source/landis_leacs_access_probe_2026-05-13.json`: JSON object keys: archivedPublicReleaseEvidence, conclusion, futureDecisionRules, generatedAt, localWarehouseState, operatorContext, protectedPortalProbe, publicCkanPackages
- `2026-05-13` `docs/reports/landis_leacs_access_probe_2026-05-13.md`: This probe checked whether the LandIS LEACS data needed for wider pipe-risk coverage can be downloaded from the available public and authenticated routes. Result: LEACS is not currently available as a downloadable payloa
- `2026-04-23` `RELEASE_NOTES/0.8.0.md`: Date: 2026-04-23 `0.8.0` pins the current MCP-Geo strategy baseline before a possible larger direction change. It packages all merged work since `0.7.0` on current `main`, including LandIS phase-2 surfacing, AddressBase/
- `2026-04-22` `tests/test_server_landis.py`: from __future__ import annotations
- `2026-04-22` `server/landis.py`: from __future__ import annotations
- `2026-04-12` `tests/test_landis_ingest.py`: from __future__ import annotations
- `2026-04-12` `scripts/landis_release_reconciliation.py`: Generate a LandIS release-surface reconciliation manifest. This compares three public-facing surfaces: 1. The authenticated ArcGIS portal inventory already captured in-repo. 2. Public LandIS website dataset/service pages that are linked from the current navigation but are not present in the mirrored ArcGIS portal slice. 3. Matching `data.gov.uk` package metadata where it exists. The output is a machine-readable JSON manifest that records: - public page reachability and page size - whether each item appears in the current portal inventory - likely related portal datasets, where known - candidate `data.gov.uk` package matches - a conservative approximate size estimate when a public page is dataset-like and there is a defensible analogue in the portal inventory
- `2026-04-12` `scripts/landis_portal_download.py`: Download authenticated LandIS portal items to local storage. The script reuses the Atlas-authenticated LandIS portal route. It expects the user to have an active LandIS portal session in ChatGPT Atlas, then mirrors the catalog metadata and item payloads to a destination directory. Feature services are exported as raw service metadata plus per-layer GeoJSON/JSON batches.
- `2026-04-12` `scripts/landis_phase2_ingest.py`: from __future__ import annotations
- `2026-04-12` `scripts/landis_full_release_archive.py`: Create and verify a full LandIS release archive on local storage. This script treats the existing authenticated ArcGIS portal archive as one verified component and then mirrors the remaining public LandIS release surfaces: 1. Public LandIS website dataset/service pages that are linked from the current official navigation but absent from the mirrored portal slice. 2. Relevant `data.gov.uk` Cranfield/LandIS package metadata and their published resource URLs. The script writes a machine-readable release manifest plus a completion verification manifest. It is designed to be rerunnable and resumable.
- `2026-04-08` `troubleshooting/Landis/mapping_landis_results.md`: The Schematic at-risk road lines for A444, A5, B4089, B4095, and the Harbury-Southam rural C network don't look right, not on any roads. Can't you use the precise USRN or RoadLink geometries Thought process Thought proce
- `2026-04-08` `troubleshooting/Landis/draw_roads_on_map.md`: Let me resume the work from where it left off. I need to: Read remaining chunks for A444 pages Read remaining chunks for B4101 pages Read Harbury-Southam pages Process all data via Python Update the HTML with static road
- `2026-04-08` `research/landis-data-source/LandIS MVP Implementation PLAN.md`: - Rebase or merge `codex/landis` onto current `main` first, because this branch diverged at `8d93cec` and `main` is now 8 commits ahead through `c39d5dd` on April 4, 2026. - Treat the report added on `main` by commit `f4
- `2026-04-07` `troubleshooting/Landis/draw_roads_on_map_analysis_2026-04-07.md`: What is the best way to stop AI clients from struggling with `mcp-geo` when the real task is "draw the roads on the map" rather than "manually orchestrate paged feature export, byte-chunk reads, JSON reassembly, Python E
- `2026-04-06` `troubleshooting/Landis/failure_data_availability.md`: "The key use case for all of this is the resilience of our buried infrastructure and also the transport infrastructure. So road rail, all the pipes and cables, the pylons Energy System - to future climate change-induced
- `2026-04-06` `troubleshooting/Landis/check_real_sites.md`: Is there an example in the paper that we can construct questions from which would validate our MCP-Geo functionality and function as a demo Thought process Thought process Absolutely — the four study sites are real, name

## Map Delivery

- `2026-05-13` `troubleshooting/mcp-cowork/mcp-cowork-fail2.md`: Claude finished the response Show me a map so I can see postcodes around of CV3 1HB Claude responded: Got the coordinates. Used mcp-geo integration, loaded tools Used mcp-geo integration, loaded tools The user wants to s
- `2026-05-13` `docs/spec_package/10_mcp_apps_ui.md`: MCP Geo exposes UI resources that can be opened by MCP clients that support `text/html;profile=mcp-app` resources. - `ui://mcp-geo/geography-selector` - `ui://mcp-geo/route-planner` - `ui://mcp-geo/feature-inspector` - `
- `2026-05-13` `docs/reports/landis_leacs_access_probe_2026-05-13.md`: This probe checked whether the LandIS LEACS data needed for wider pipe-risk coverage can be downloaded from the available public and authenticated routes. Result: LEACS is not currently available as a downloadable payloa
- `2026-04-28` `docs/spec_package/12_backlog_and_plan.md`: - **Map render tool**: `os_maps.render` now returns a static map proxy URL (OSM tile proxy). - **Resources catalog**: expanded `/resources/*` with boundary manifest, latest report, cache status, and ONS cache index. - **
- `2026-04-22` `tools/os_maps.py`: from __future__ import annotations
- `2026-04-22` `tools/os_map.py`: from __future__ import annotations
- `2026-04-22` `tests/test_os_mcp_route_query.py`: from fastapi.testclient import TestClient
- `2026-04-22` `tests/test_os_maps_helpers.py`: from __future__ import annotations
- `2026-04-22` `tests/test_os_map_tools.py`: from __future__ import annotations
- `2026-04-22` `tests/test_os_map_helpers_extra.py`: from __future__ import annotations
- `2026-04-12` `scripts/landis_portal_download.py`: Download authenticated LandIS portal items to local storage. The script reuses the Atlas-authenticated LandIS portal route. It expects the user to have an active LandIS portal session in ChatGPT Atlas, then mirrors the catalog metadata and item payloads to a destination directory. Feature services are exported as raw service metadata plus per-layer GeoJSON/JSON batches.
- `2026-04-10` `troubleshooting/ABP/after-revision-trace-claude-report.md`: Date: 2026-04-10 Inputs: - `troubleshooting/ABP/after-revision-trace-claude.md` - Current router and tool-discovery code in `tools/os_mcp.py` and `server/mcp/tool_search.py` - Current council-tax tools in `tools/council_
- `2026-04-09` `ui/simple_map.html`: Simple Map Lab
- `2026-04-09` `docs/reports/teignmouth_wheelchair_access_map_2026-03-07.html`: Teignmouth town-centre wheelchair access map
- `2026-04-09` `docs/reports/sidmouth_wheelchair_access_map_2026-03-07.html`: Sidmouth town-centre wheelchair access map
- `2026-04-09` `docs/reports/exmouth_wheelchair_access_map_2026-03-07.html`: Exmouth town-centre wheelchair access map

## Evaluation and Evidence

- `2026-05-13` `troubleshooting/mcp-cowork/cowork-sanity-and-failure-report-2026-04-28.md`: Date: 2026-04-28 This note diagnoses the saved Claude Cowork transcripts in `troubleshooting/mcp-cowork/` and separates: - MCP-Geo server/runtime health - Docker Desktop external-drive mount health - Claude Cowork MCP-Ap
- `2026-05-13` `docs/reports/landis_leacs_access_probe_2026-05-13.md`: This probe checked whether the LandIS LEACS data needed for wider pipe-risk coverage can be downloaded from the available public and authenticated routes. Result: LEACS is not currently available as a downloadable payloa
- `2026-04-28` `docs/spec_package/12_backlog_and_plan.md`: - **Map render tool**: `os_maps.render` now returns a static map proxy URL (OSM tile proxy). - **Resources catalog**: expanded `/resources/*` with boundary manifest, latest report, cache status, and ONS cache index. - **
- `2026-04-23` `CHANGELOG.md`: All notable changes to this project will be documented in this file. - Fixed published package contents so installed wheels include nested server modules, audit schemas, static resources, UI assets, and typed tool metada
- `2026-04-22` `docs/reports/os_ngd_spring_2026_release_impact.md`: Date: 2026-04-22 - [OS NGD product page](https://www.ordnancesurvey.co.uk/products/os-ngd) - [OS NGD What's New](https://docs.os.uk/osngd/os-ngd-news/whats-new) - [OS NGD API Features: data available](https://docs.os.uk/
- `2026-04-14` `tests/test_host_benchmark.py`: from __future__ import annotations
- `2026-04-14` `tests/test_benchmark_env.py`: from __future__ import annotations
- `2026-04-14` `scripts/benchmark_env.py`: from __future__ import annotations
- `2026-04-14` `docs/reports/client_interop_unattended/client_interop_unattended_eval_2026-04-13_vscode_full_v18_no_primer.vscode_ide.readiness.json`: JSON object keys: attemptCount, attempts, blocker, blockerCategory, configVisibility, finalAttemptKind, firstAttemptOutcome, liveOsReady
- `2026-04-14` `docs/reports/client_interop_unattended/client_interop_unattended_eval_2026-04-13_vscode_full_v18_no_primer.md`: Generated: 2026-04-13T12:13:45Z Scenario pack: codex_vs_claude_host_v1 | Track | Outcome | First Attempt | Final Attempt | Recovery | Live OS Ready | Config | Blocker | | --- | --- | --- | --- | --- | --- | --- | --- | |
- `2026-04-14` `docs/reports/client_interop_unattended/client_interop_unattended_eval_2026-04-13_vscode_full_v18_no_primer.json`: JSON object keys: attempts, capability, generatedAt, readiness, scenarioPack, tracks
- `2026-04-14` `docs/reports/client_interop_unattended/client_interop_unattended_eval_2026-04-13_vscode_canary_v17_no_primer.vscode_ide.readiness.json`: JSON object keys: attemptCount, attempts, blocker, blockerCategory, configVisibility, finalAttemptKind, firstAttemptOutcome, liveOsReady
- `2026-04-14` `docs/reports/client_interop_unattended/client_interop_unattended_eval_2026-04-13_vscode_canary_v17_no_primer.md`: Generated: 2026-04-13T12:06:13Z Scenario pack: codex_vs_claude_host_v1 | Track | Outcome | First Attempt | Final Attempt | Recovery | Live OS Ready | Config | Blocker | | --- | --- | --- | --- | --- | --- | --- | --- | |
- `2026-04-14` `docs/reports/client_interop_unattended/client_interop_unattended_eval_2026-04-13_vscode_canary_v17_no_primer.json`: JSON object keys: attempts, capability, generatedAt, readiness, scenarioPack, tracks
- `2026-04-14` `docs/reports/client_interop_unattended/client_interop_unattended_eval_2026-04-13_vscode_canary_v16_useful_wait.vscode_ide.readiness.json`: JSON object keys: attemptCount, attempts, blocker, blockerCategory, configVisibility, finalAttemptKind, firstAttemptOutcome, liveOsReady
- `2026-04-14` `docs/reports/client_interop_unattended/client_interop_unattended_eval_2026-04-13_vscode_canary_v16_useful_wait.md`: Generated: 2026-04-13T12:01:04Z Scenario pack: codex_vs_claude_host_v1 | Track | Outcome | First Attempt | Final Attempt | Recovery | Live OS Ready | Config | Blocker | | --- | --- | --- | --- | --- | --- | --- | --- | |

## CI and Release

- `2026-05-13` `troubleshooting/mcp-cowork/cowork-sanity-and-failure-report-2026-04-28.md`: Date: 2026-04-28 This note diagnoses the saved Claude Cowork transcripts in `troubleshooting/mcp-cowork/` and separates: - MCP-Geo server/runtime health - Docker Desktop external-drive mount health - Claude Cowork MCP-Ap
- `2026-05-13` `research/landis-data-source/landis_leacs_access_probe_2026-05-13.json`: JSON object keys: archivedPublicReleaseEvidence, conclusion, futureDecisionRules, generatedAt, localWarehouseState, operatorContext, protectedPortalProbe, publicCkanPackages
- `2026-04-28` `PROGRESS.MD`: This file tracks how the implementation compares to the original proposal and later documentation as the MCP specification evolved. Last updated: 2026-06-01 Legend: pending, in_progress, done, blocked | Workstream | Stat
- `2026-04-28` `.github/workflows/ci.yml`: name: CI
- `2026-04-23` `docs/Build.md`: This guide describes how to install, run, and validate the current MCP Geo server in this repository. It replaces the original planning backlog with repo-aligned instructions. - Python 3.11+ - Optional: Docker (for conta
- `2026-04-23` `RELEASE_NOTES/0.8.1.md`: Date: 2026-04-23 `0.8.1` is a patch release for the `0.8.0` stable strategy baseline. It fixes the published package contents so installed wheels work outside the source checkout for both HTTP and STDIO runtimes. - Inclu
- `2026-04-23` `RELEASE_NOTES/0.8.0.md`: Date: 2026-04-23 `0.8.0` pins the current MCP-Geo strategy baseline before a possible larger direction change. It packages all merged work since `0.7.0` on current `main`, including LandIS phase-2 surfacing, AddressBase/
- `2026-04-23` `README.md`: A research Model Context Protocol (MCP) server for geospatial (Ordnance Survey) and statistical (Office of National Statistics) data. If you have Docker installed and Internet access, have this running in 3 minutes. This
- `2026-04-22` `docs/reports/os_ngd_spring_2026_release_impact.md`: Date: 2026-04-22 - [OS NGD product page](https://www.ordnancesurvey.co.uk/products/os-ngd) - [OS NGD What's New](https://docs.os.uk/osngd/os-ngd-news/whats-new) - [OS NGD API Features: data available](https://docs.os.uk/
- `2026-04-22` `AGENTS.md`: This document defines how agents (and humans) should work within the `mcp-geo` repository. It replaces a template from a different project—details below are specific to this codebase. - FastAPI-based Model Context Protoc
- `2026-04-13` `tests/test_mcp_docker_local.py`: from __future__ import annotations
- `2026-04-13` `scripts/mcp-docker-local`: set -euo pipefail
- `2026-04-12` `tools/council_tax.py`: from __future__ import annotations
- `2026-04-12` `tests/test_elicitation_forms.py`: from server.mcp import elicitation_forms as forms
- `2026-04-12` `tests/test_council_tax_band.py`: from __future__ import annotations
- `2026-04-12` `server/mcp/elicitation_forms.py`: from __future__ import annotations

## Knowledge Base

- `2026-04-28` `research/llm_wiki_vs_rag/README.md`: Date opened: 2026-04-23 Status: Proposed Owner: TBD Investigate whether Karpathy-style **LLM Wiki** knowledge bases are more effective than retrieval-augmented generation (RAG) for accumulating, maintaining, and using pr
- `2026-04-06` `tests/test_obsidian_kb.py`: from __future__ import annotations
- `2026-04-06` `skills/mcp-geo-obsidian-kb/SKILL.md`: Use this skill when you need to refresh or validate the repo knowledge base under `Obsidian/MCP Geo Knowledge Base/`. - Canonical tier: checked-in markdown generated from tracked repo content. - Local overlay tier: ignor
- `2026-04-06` `scripts/validate_obsidian_kb.py`: from __future__ import annotations
- `2026-04-06` `scripts/obsidian_kb_common.py`: from __future__ import annotations
- `2026-04-06` `scripts/build_obsidian_kb.py`: from __future__ import annotations
