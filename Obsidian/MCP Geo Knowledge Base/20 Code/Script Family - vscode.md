---
title: "Script Family - vscode"
kb_kind: "code_family"
source_paths:
  - "scripts/vscode_mcp_stdio.py"
  - "scripts/vscode_trace_snapshot.py"
source_commit: "923807292e3a134ad8214be3de523caa7fdce7c5"
source_commit_dirty: true
source_urls:
  - "https://github.com/chris-page-gov/mcp-geo/blob/923807292e3a134ad8214be3de523caa7fdce7c5/scripts/vscode_mcp_stdio.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/923807292e3a134ad8214be3de523caa7fdce7c5/scripts/vscode_trace_snapshot.py"
source_hashes:
  scripts/vscode_mcp_stdio.py: "sha256:cdfa829f-550c2bf6-544485e3-5d051a75-a7b7d554-f095f4a6-b7bfe16d-cf12d350"
  scripts/vscode_trace_snapshot.py: "sha256:2542c37b-1260b418-ac80748d-668d2473-2d2c7c0b-50ca56d9-a8006044-d9a83791"
generated_at: "2026-06-01T02:28:24Z"
evidence_scope: "canon"
first_seen_date: "2026-02-09"
last_validated_at: "2026-06-01T02:28:24Z"
---
# Script Family - vscode

## Evidence Scope

- Categories: `code_runtime`
- Source file count: 2

## Source Inventory

| Path | Summary | First Seen | Last Commit | Related Tests |
| --- | --- | --- | --- | --- |
| `scripts/vscode_mcp_stdio.py` | VS Code MCP stdio entrypoint that works on both host macOS and Linux devcontainers. VS Code runs MCP stdio servers by ex | 2026-02-09 | 2026-03-01 | `tests/test_host_benchmark.py` |
| `scripts/vscode_trace_snapshot.py` | Snapshot VS Code MCP trace logs into a trace_session-style directory. VS Code MCP servers can write long-lived trace fil | 2026-02-10 | 2026-02-10 | - |

## Pinned Sources

- [`scripts/vscode_mcp_stdio.py`](https://github.com/chris-page-gov/mcp-geo/blob/923807292e3a134ad8214be3de523caa7fdce7c5/scripts/vscode_mcp_stdio.py)
- [`scripts/vscode_trace_snapshot.py`](https://github.com/chris-page-gov/mcp-geo/blob/923807292e3a134ad8214be3de523caa7fdce7c5/scripts/vscode_trace_snapshot.py)
