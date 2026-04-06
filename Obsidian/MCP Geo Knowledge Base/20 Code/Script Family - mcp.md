---
title: "Script Family - mcp"
kb_kind: "code_family"
source_paths:
  - "scripts/mcp_client.py"
  - "scripts/mcp_http_trace_proxy.py"
  - "scripts/mcp_stdio_trace_proxy.py"
  - "scripts/mcp_ui_mode_probe.py"
source_commit: "b279fe5fde6669d57955890996cd6fa6ddca76fb"
source_commit_dirty: true
source_urls:
  - "https://github.com/chris-page-gov/mcp-geo/blob/b279fe5fde6669d57955890996cd6fa6ddca76fb/scripts/mcp_client.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/b279fe5fde6669d57955890996cd6fa6ddca76fb/scripts/mcp_http_trace_proxy.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/b279fe5fde6669d57955890996cd6fa6ddca76fb/scripts/mcp_stdio_trace_proxy.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/b279fe5fde6669d57955890996cd6fa6ddca76fb/scripts/mcp_ui_mode_probe.py"
source_hashes:
  scripts/mcp_client.py: "sha256:74c521b5-a8f5c3f1-175d654b-60783ba7-38e4e5b9-a382ce8a-41aa0b53-f525bd29"
  scripts/mcp_http_trace_proxy.py: "sha256:a918fda4-ab76ade6-a8b11b7d-4494e40a-966869e3-7bc78654-ae83e68a-558ce7fd"
  scripts/mcp_stdio_trace_proxy.py: "sha256:f2bf08fd-3a389e94-cf9ba0da-9a88744b-3f43bc04-e0797d65-981ad07f-ae4bc4c3"
  scripts/mcp_ui_mode_probe.py: "sha256:b5c53a62-79e81198-6c6a0182-ccbbffc2-eeb1c292-84c07398-c00775d5-53471e76"
generated_at: "2026-04-06T13:09:04Z"
evidence_scope: "canon"
first_seen_date: "2025-09-17"
last_validated_at: "2026-04-06T13:09:04Z"
---
# Script Family - mcp

## Evidence Scope

- Categories: `code_runtime`
- Source file count: 4

## Source Inventory

| Path | Summary | First Seen | Last Commit | Related Tests |
| --- | --- | --- | --- | --- |
| `scripts/mcp_client.py` | Helper client for the mcp-geo STDIO adapter. Usage examples: python scripts/mcp_client.py initialize python scripts/mcp_ | 2025-09-17 | 2026-01-24 | `tests/test_mcp_client_if_none_match.py`, `tests/test_mcp_client_resources_get.py` |
| `scripts/mcp_http_trace_proxy.py` | HTTP proxy that logs MCP JSON-RPC traffic. Usage: python scripts/mcp_http_trace_proxy.py \\ --upstream http://127.0.0.1: | 2026-01-21 | 2026-01-24 | - |
| `scripts/mcp_stdio_trace_proxy.py` | MCP stdio proxy that logs JSON-RPC traffic. This proxy sits between an MCP client and an MCP stdio server, forwarding by | 2026-01-21 | 2026-02-09 | `tests/test_mcp_stdio_trace_proxy.py` |
| `scripts/mcp_ui_mode_probe.py` | Probe MCP-Apps UI content modes over STDIO. Examples: python3 scripts/mcp_ui_mode_probe.py python3 scripts/mcp_ui_mode_p | 2026-02-06 | 2026-02-06 | - |

## Pinned Sources

- [`scripts/mcp_client.py`](https://github.com/chris-page-gov/mcp-geo/blob/b279fe5fde6669d57955890996cd6fa6ddca76fb/scripts/mcp_client.py)
- [`scripts/mcp_http_trace_proxy.py`](https://github.com/chris-page-gov/mcp-geo/blob/b279fe5fde6669d57955890996cd6fa6ddca76fb/scripts/mcp_http_trace_proxy.py)
- [`scripts/mcp_stdio_trace_proxy.py`](https://github.com/chris-page-gov/mcp-geo/blob/b279fe5fde6669d57955890996cd6fa6ddca76fb/scripts/mcp_stdio_trace_proxy.py)
- [`scripts/mcp_ui_mode_probe.py`](https://github.com/chris-page-gov/mcp-geo/blob/b279fe5fde6669d57955890996cd6fa6ddca76fb/scripts/mcp_ui_mode_probe.py)
