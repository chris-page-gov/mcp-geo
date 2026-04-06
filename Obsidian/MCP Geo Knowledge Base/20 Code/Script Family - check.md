---
title: "Script Family - check"
kb_kind: "code_family"
source_paths:
  - "scripts/check_claude_startup_scope.sh"
  - "scripts/check_codex_startup_scope.sh"
  - "scripts/check_lmr_host4.py"
  - "scripts/check_non_runtime_quality.sh"
  - "scripts/check_shared_benchmark_cache.sh"
source_commit: "bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851"
source_commit_dirty: true
source_urls:
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/scripts/check_claude_startup_scope.sh"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/scripts/check_codex_startup_scope.sh"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/scripts/check_lmr_host4.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/scripts/check_non_runtime_quality.sh"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/scripts/check_shared_benchmark_cache.sh"
source_hashes:
  scripts/check_claude_startup_scope.sh: "c8b0e44d6d640049815e987ac22781933b1a4cbbba368e05c08a27d8ec0ca51d"
  scripts/check_codex_startup_scope.sh: "07aea4e791e1e9c3c02086aa3d84799f1d0706b7ffaf73bd36ac6ee4c999369d"
  scripts/check_lmr_host4.py: "09d10f54a510a24f31ef1cfb2bbeaddfe4ab0f3708a0f026133fc733260a896a"
  scripts/check_non_runtime_quality.sh: "419d0bef3c801a4579a41dd5a1cf6ecc99485f53934dc6fafd26a0e2d8f64f66"
  scripts/check_shared_benchmark_cache.sh: "0da247115a9610d55c5c3bc93356630c249565437d470c356471378a46c3de6f"
generated_at: "2026-04-06T09:00:35Z"
evidence_scope: "canon"
first_seen_date: "2026-02-22"
last_validated_at: "2026-04-06T09:00:35Z"
---
# Script Family - check

## Evidence Scope

- Categories: `code_runtime`
- Source file count: 5

## Source Inventory

| Path | Summary | First Seen | Last Commit | Related Tests |
| --- | --- | --- | --- | --- |
| `scripts/check_claude_startup_scope.sh` | set -euo pipefail | 2026-03-03 | 2026-03-03 | - |
| `scripts/check_codex_startup_scope.sh` | set -euo pipefail | 2026-03-03 | 2026-03-06 | - |
| `scripts/check_lmr_host4.py` | Automate LMR-HOST-4 evidence checks for Claude Desktop sessions. This script focuses on the known host-runtime gap: - Wi | 2026-02-22 | 2026-02-22 | `tests/test_check_lmr_host4.py` |
| `scripts/check_non_runtime_quality.sh` | set -euo pipefail | 2026-02-22 | 2026-03-24 | - |
| `scripts/check_shared_benchmark_cache.sh` | set -euo pipefail | 2026-03-10 | 2026-04-05 | - |

## Pinned Sources

- [`scripts/check_claude_startup_scope.sh`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/scripts/check_claude_startup_scope.sh)
- [`scripts/check_codex_startup_scope.sh`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/scripts/check_codex_startup_scope.sh)
- [`scripts/check_lmr_host4.py`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/scripts/check_lmr_host4.py)
- [`scripts/check_non_runtime_quality.sh`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/scripts/check_non_runtime_quality.sh)
- [`scripts/check_shared_benchmark_cache.sh`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/scripts/check_shared_benchmark_cache.sh)
