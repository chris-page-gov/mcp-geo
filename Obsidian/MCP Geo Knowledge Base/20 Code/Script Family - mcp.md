---
title: "Script Family - mcp"
kb_kind: "code_family"
source_paths:
  - "scripts/mcp_client.py"
  - "scripts/mcp_http_trace_proxy.py"
  - "scripts/mcp_stdio_trace_proxy.py"
  - "scripts/mcp_ui_mode_probe.py"
source_commit: "bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851"
source_commit_dirty: true
source_urls:
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/scripts/mcp_client.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/scripts/mcp_http_trace_proxy.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/scripts/mcp_stdio_trace_proxy.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/scripts/mcp_ui_mode_probe.py"
source_hashes:
  scripts/mcp_client.py: "74c521b5a8f5c3f1175d654b60783ba738e4e5b9a382ce8a41aa0b53f525bd29"
  scripts/mcp_http_trace_proxy.py: "a918fda4ab76ade6a8b11b7d4494e40a966869e37bc78654ae83e68a558ce7fd"
  scripts/mcp_stdio_trace_proxy.py: "f2bf08fd3a389e94cf9ba0da9a88744b3f43bc04e0797d65981ad07fae4bc4c3"
  scripts/mcp_ui_mode_probe.py: "b5c53a6279e811986c6a0182ccbbffc2eeb1c29284c07398c00775d553471e76"
generated_at: "2026-04-06T09:00:35Z"
evidence_scope: "canon"
first_seen_date: "2025-09-17"
last_validated_at: "2026-04-06T09:00:35Z"
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

- [`scripts/mcp_client.py`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/scripts/mcp_client.py)
- [`scripts/mcp_http_trace_proxy.py`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/scripts/mcp_http_trace_proxy.py)
- [`scripts/mcp_stdio_trace_proxy.py`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/scripts/mcp_stdio_trace_proxy.py)
- [`scripts/mcp_ui_mode_probe.py`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/scripts/mcp_ui_mode_probe.py)
