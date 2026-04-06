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
  - "server/mcp/resource_access.py"
  - "server/mcp/resource_catalog.py"
  - "server/mcp/resource_handoff.py"
  - "server/mcp/tool_search.py"
source_commit: "bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851"
source_commit_dirty: true
source_urls:
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/server/mcp/__init__.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/server/mcp/client_capabilities.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/server/mcp/elicitation_forms.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/server/mcp/http_route_auth.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/server/mcp/http_transport.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/server/mcp/prompts.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/server/mcp/resource_access.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/server/mcp/resource_catalog.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/server/mcp/resource_handoff.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/server/mcp/tool_search.py"
source_hashes:
  server/mcp/__init__.py: "7aa7f241ce31acfd1f1aab2a7d0c35efcdc8b75e0d80ae7a5ef51be83545d725"
  server/mcp/client_capabilities.py: "567e95af24d447acd5925249c82520db574af3ca4ce9066fe4e803da0f0b4281"
  server/mcp/elicitation_forms.py: "6752f14a4c22a152df841bb0819d779eae89e317e9ed5ebad28bd4958355da21"
  server/mcp/http_route_auth.py: "3a90448bbf0c58e774d588503f9c055978b55624e9159f585781cc324776236c"
  server/mcp/http_transport.py: "485ffe97c9d1d6b449de071bebf3595ed4920df5a4151fc38724de81e3f47240"
  server/mcp/prompts.py: "b4bcc27f2cdc9c026dfe9b53c474211fc5389180de37ac57a9713d0cc7caae83"
  server/mcp/resource_access.py: "09fa97eb220b767df107be401d87c84b8dde15348f8352e38230ef45199d4d72"
  server/mcp/resource_catalog.py: "56df19c778d79eab058c77499df6cc03241dc9331a6519091d033c8699d2e06d"
  server/mcp/resource_handoff.py: "2d7d934846c49e1ed3cede8c1bcc94f5e9cee75e65994333938b5b2c6998d26a"
  server/mcp/tool_search.py: "8bf72136914872123db379377166288c2fdc85d6a9965175da2671d75e22c815"
generated_at: "2026-04-06T09:00:35Z"
evidence_scope: "canon"
first_seen_date: "2025-08-20"
last_validated_at: "2026-04-06T09:00:35Z"
---
# MCP Surface Overview

## Evidence Scope

- Categories: `code_runtime`
- Source file count: 10

## Source Inventory

| Path | Summary | First Seen | Last Commit | Related Tests |
| --- | --- | --- | --- | --- |
| `server/mcp/__init__.py` | Makes this directory a Python package | 2025-08-20 | 2025-08-20 | `tests/evaluation/audit_logger.py`, `tests/evaluation/harness.py`, `tests/evaluation/live_capture.py`, `tests/test_admin_lookup_live_internals.py` |
| `server/mcp/client_capabilities.py` | from __future__ import annotations | 2026-02-11 | 2026-02-13 | `tests/test_client_capabilities.py` |
| `server/mcp/elicitation_forms.py` | from __future__ import annotations | 2026-02-07 | 2026-02-13 | `tests/test_elicitation_forms.py` |
| `server/mcp/http_route_auth.py` | from __future__ import annotations | 2026-03-14 | 2026-03-14 | `tests/test_resource_fallback.py` |
| `server/mcp/http_transport.py` | from __future__ import annotations | 2026-01-21 | 2026-03-22 | `tests/test_http_transport_coverage_more.py`, `tests/test_main_observability_branches.py`, `tests/test_mcp_http.py`, `tests/test_owasp_mcp_validation.py` |
| `server/mcp/prompts.py` | from __future__ import annotations | 2026-01-28 | 2026-01-28 | `tests/evaluation/questions.py`, `tests/test_client_capabilities.py`, `tests/test_landis_resources.py`, `tests/test_prompts.py` |
| `server/mcp/resource_access.py` | from __future__ import annotations | 2026-03-14 | 2026-04-04 | `tests/test_resource_fallback.py` |
| `server/mcp/resource_catalog.py` | from __future__ import annotations | 2026-01-20 | 2026-04-05 | `tests/test_evaluation_harness_full.py`, `tests/test_landis_resources.py`, `tests/test_mcp_http.py`, `tests/test_ons_data.py` |
| `server/mcp/resource_handoff.py` | from __future__ import annotations | 2026-03-14 | 2026-03-14 | `tests/test_ons_data.py`, `tests/test_os_downloads_tools.py`, `tests/test_resource_fallback.py`, `tests/test_stdio_adapter_direct.py` |
| `server/mcp/tool_search.py` | from __future__ import annotations | 2026-01-20 | 2026-04-05 | `tests/test_host_benchmark.py`, `tests/test_landis_resources.py`, `tests/test_os_mcp_descriptor.py`, `tests/test_tool_search.py` |

## Pinned Sources

- [`server/mcp/__init__.py`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/server/mcp/__init__.py)
- [`server/mcp/client_capabilities.py`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/server/mcp/client_capabilities.py)
- [`server/mcp/elicitation_forms.py`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/server/mcp/elicitation_forms.py)
- [`server/mcp/http_route_auth.py`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/server/mcp/http_route_auth.py)
- [`server/mcp/http_transport.py`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/server/mcp/http_transport.py)
- [`server/mcp/prompts.py`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/server/mcp/prompts.py)
- [`server/mcp/resource_access.py`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/server/mcp/resource_access.py)
- [`server/mcp/resource_catalog.py`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/server/mcp/resource_catalog.py)
- [`server/mcp/resource_handoff.py`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/server/mcp/resource_handoff.py)
- [`server/mcp/tool_search.py`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/server/mcp/tool_search.py)
