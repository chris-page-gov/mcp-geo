---
title: "MCP Surface Overview"
kb_kind: "code_family"
source_paths:
  - "server/mcp/__init__.py"
  - "server/mcp/client_capabilities.py"
  - "server/mcp/elicitation_forms.py"
  - "server/mcp/http_route_auth.py"
  - "server/mcp/http_transport.py"
  - "server/mcp/prompts.py"
  - "server/mcp/rc2026.py"
  - "server/mcp/resource_access.py"
  - "server/mcp/resource_catalog.py"
  - "server/mcp/resource_handoff.py"
  - "server/mcp/tool_search.py"
source_commit: "923807292e3a134ad8214be3de523caa7fdce7c5"
source_commit_dirty: true
source_urls:
  - "https://github.com/chris-page-gov/mcp-geo/blob/923807292e3a134ad8214be3de523caa7fdce7c5/server/mcp/__init__.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/923807292e3a134ad8214be3de523caa7fdce7c5/server/mcp/client_capabilities.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/923807292e3a134ad8214be3de523caa7fdce7c5/server/mcp/elicitation_forms.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/923807292e3a134ad8214be3de523caa7fdce7c5/server/mcp/http_route_auth.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/923807292e3a134ad8214be3de523caa7fdce7c5/server/mcp/http_transport.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/923807292e3a134ad8214be3de523caa7fdce7c5/server/mcp/prompts.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/923807292e3a134ad8214be3de523caa7fdce7c5/server/mcp/rc2026.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/923807292e3a134ad8214be3de523caa7fdce7c5/server/mcp/resource_access.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/923807292e3a134ad8214be3de523caa7fdce7c5/server/mcp/resource_catalog.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/923807292e3a134ad8214be3de523caa7fdce7c5/server/mcp/resource_handoff.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/923807292e3a134ad8214be3de523caa7fdce7c5/server/mcp/tool_search.py"
source_hashes:
  server/mcp/__init__.py: "sha256:7aa7f241-ce31acfd-1f1aab2a-7d0c35ef-cdc8b75e-0d80ae7a-5ef51be8-3545d725"
  server/mcp/client_capabilities.py: "sha256:567e95af-24d447ac-d5925249-c82520db-574af3ca-4ce9066f-e4e803da-0f0b4281"
  server/mcp/elicitation_forms.py: "sha256:f7042747-11a2fb4c-2406cd13-451b6f56-f86c27b0-aa7e05f9-778f033e-fcbf759d"
  server/mcp/http_route_auth.py: "sha256:3a90448b-bf0c58e7-74d58850-3f9c0559-78b55624-e9159f58-5781cc32-4776236c"
  server/mcp/http_transport.py: "sha256:7a4679d3-cc0aa745-7b4b4dbb-2b6c0d90-769538f1-a5fa5bdc-caad9f1a-2a4b471e"
  server/mcp/prompts.py: "sha256:b4bcc27f-2cdc9c02-6dfe9b53-c474211f-c5389180-de37ac57-a9713d0c-c7caae83"
  server/mcp/rc2026.py: "sha256:56b50cd9-ef834fff-dcfcc485-11a44be4-a993d49a-6af0b0ef-c7481c99-dcdd623c"
  server/mcp/resource_access.py: "sha256:09fa97eb-220b767d-f107be40-1d87c84b-8dde1534-8f8352e3-8230ef45-199d4d72"
  server/mcp/resource_catalog.py: "sha256:2980ab34-ff4e6bd0-1c31fcd6-6f477cff-fe31c323-86a6e9d2-1abc0d62-5d8289e7"
  server/mcp/resource_handoff.py: "sha256:2d7d9348-46c49e1e-d3cede8c-1bcc94f5-e9cee75e-65994333-938b5b2c-6998d26a"
  server/mcp/tool_search.py: "sha256:0a9b952b-e51d4187-748fadd3-72a6ecfb-3930fb7b-1e97b39b-ade4a4ff-cb00d1ea"
generated_at: "2026-06-01T02:28:24Z"
evidence_scope: "canon"
first_seen_date: "2025-08-20"
last_validated_at: "2026-06-01T02:28:24Z"
---
# MCP Surface Overview

## Evidence Scope

- Categories: `code_runtime`
- Source file count: 11

## Source Inventory

| Path | Summary | First Seen | Last Commit | Related Tests |
| --- | --- | --- | --- | --- |
| `server/mcp/__init__.py` | Makes this directory a Python package | 2025-08-20 | 2025-08-20 | `tests/evaluation/audit_logger.py`, `tests/evaluation/harness.py`, `tests/evaluation/live_capture.py`, `tests/test_admin_lookup_live_internals.py` |
| `server/mcp/client_capabilities.py` | from __future__ import annotations | 2026-02-11 | 2026-02-13 | `tests/test_client_capabilities.py` |
| `server/mcp/elicitation_forms.py` | from __future__ import annotations | 2026-02-07 | 2026-04-12 | `tests/test_elicitation_forms.py` |
| `server/mcp/http_route_auth.py` | from __future__ import annotations | 2026-03-14 | 2026-03-14 | `tests/test_resource_fallback.py` |
| `server/mcp/http_transport.py` | from __future__ import annotations | 2026-01-21 | 2026-06-01 | `tests/test_http_transport_coverage_more.py`, `tests/test_main_observability_branches.py`, `tests/test_mcp_2026_rc.py`, `tests/test_mcp_http.py` |
| `server/mcp/prompts.py` | from __future__ import annotations | 2026-01-28 | 2026-01-28 | `tests/evaluation/questions.py`, `tests/test_client_capabilities.py`, `tests/test_landis_resources.py`, `tests/test_prompts.py` |
| `server/mcp/rc2026.py` | from __future__ import annotations | 2026-06-01 | 2026-06-01 | `tests/test_mcp_2026_rc.py` |
| `server/mcp/resource_access.py` | from __future__ import annotations | 2026-03-14 | 2026-04-04 | `tests/test_resource_fallback.py` |
| `server/mcp/resource_catalog.py` | from __future__ import annotations | 2026-01-20 | 2026-04-23 | `tests/test_evaluation_harness_full.py`, `tests/test_landis_resources.py`, `tests/test_mcp_http.py`, `tests/test_ons_data.py` |
| `server/mcp/resource_handoff.py` | from __future__ import annotations | 2026-03-14 | 2026-03-14 | `tests/test_ons_data.py`, `tests/test_os_apps_tools.py`, `tests/test_os_downloads_tools.py`, `tests/test_resource_fallback.py` |
| `server/mcp/tool_search.py` | from __future__ import annotations | 2026-01-20 | 2026-04-12 | `tests/test_host_benchmark.py`, `tests/test_landis_resources.py`, `tests/test_os_mcp_descriptor.py`, `tests/test_tool_search.py` |

## Pinned Sources

- [`server/mcp/__init__.py`](https://github.com/chris-page-gov/mcp-geo/blob/923807292e3a134ad8214be3de523caa7fdce7c5/server/mcp/__init__.py)
- [`server/mcp/client_capabilities.py`](https://github.com/chris-page-gov/mcp-geo/blob/923807292e3a134ad8214be3de523caa7fdce7c5/server/mcp/client_capabilities.py)
- [`server/mcp/elicitation_forms.py`](https://github.com/chris-page-gov/mcp-geo/blob/923807292e3a134ad8214be3de523caa7fdce7c5/server/mcp/elicitation_forms.py)
- [`server/mcp/http_route_auth.py`](https://github.com/chris-page-gov/mcp-geo/blob/923807292e3a134ad8214be3de523caa7fdce7c5/server/mcp/http_route_auth.py)
- [`server/mcp/http_transport.py`](https://github.com/chris-page-gov/mcp-geo/blob/923807292e3a134ad8214be3de523caa7fdce7c5/server/mcp/http_transport.py)
- [`server/mcp/prompts.py`](https://github.com/chris-page-gov/mcp-geo/blob/923807292e3a134ad8214be3de523caa7fdce7c5/server/mcp/prompts.py)
- [`server/mcp/rc2026.py`](https://github.com/chris-page-gov/mcp-geo/blob/923807292e3a134ad8214be3de523caa7fdce7c5/server/mcp/rc2026.py)
- [`server/mcp/resource_access.py`](https://github.com/chris-page-gov/mcp-geo/blob/923807292e3a134ad8214be3de523caa7fdce7c5/server/mcp/resource_access.py)
- [`server/mcp/resource_catalog.py`](https://github.com/chris-page-gov/mcp-geo/blob/923807292e3a134ad8214be3de523caa7fdce7c5/server/mcp/resource_catalog.py)
- [`server/mcp/resource_handoff.py`](https://github.com/chris-page-gov/mcp-geo/blob/923807292e3a134ad8214be3de523caa7fdce7c5/server/mcp/resource_handoff.py)
- [`server/mcp/tool_search.py`](https://github.com/chris-page-gov/mcp-geo/blob/923807292e3a134ad8214be3de523caa7fdce7c5/server/mcp/tool_search.py)
