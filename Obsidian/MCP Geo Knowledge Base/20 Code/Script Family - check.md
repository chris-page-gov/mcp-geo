---
title: "Script Family - check"
kb_kind: "code_family"
source_paths:
  - "scripts/check_claude_startup_scope.sh"
  - "scripts/check_codex_startup_scope.sh"
  - "scripts/check_lmr_host4.py"
  - "scripts/check_non_runtime_quality.sh"
  - "scripts/check_shared_benchmark_cache.sh"
source_commit: "004e7d4748422b44133399279803c8cb2b766a1c"
source_commit_dirty: true
source_urls:
  - "https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/scripts/check_claude_startup_scope.sh"
  - "https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/scripts/check_codex_startup_scope.sh"
  - "https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/scripts/check_lmr_host4.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/scripts/check_non_runtime_quality.sh"
  - "https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/scripts/check_shared_benchmark_cache.sh"
source_hashes:
  scripts/check_claude_startup_scope.sh: "sha256:c8b0e44d-6d640049-815e987a-c2278193-3b1a4cbb-ba368e05-c08a27d8-ec0ca51d"
  scripts/check_codex_startup_scope.sh: "sha256:07aea4e7-91e1e9c3-c02086aa-3d84799f-1d0706b7-ffaf73bd-36ac6ee4-c999369d"
  scripts/check_lmr_host4.py: "sha256:09d10f54-a510a24f-31ef1cfb-2bbeaddf-e4ab0f37-08a0f026-133fc733-260a896a"
  scripts/check_non_runtime_quality.sh: "sha256:419d0bef-3c801a45-79a41dd5-a1cf6ecc-99485f53-934dc6fa-fd26a0e2-d8f64f66"
  scripts/check_shared_benchmark_cache.sh: "sha256:0da24711-5a9610d5-5c5c3bc9-3356630c-24956543-7d470c35-6471378a-46c3de6f"
generated_at: "2026-04-06T14:09:00Z"
evidence_scope: "canon"
first_seen_date: "2026-02-22"
last_validated_at: "2026-04-06T14:09:00Z"
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

- [`scripts/check_claude_startup_scope.sh`](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/scripts/check_claude_startup_scope.sh)
- [`scripts/check_codex_startup_scope.sh`](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/scripts/check_codex_startup_scope.sh)
- [`scripts/check_lmr_host4.py`](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/scripts/check_lmr_host4.py)
- [`scripts/check_non_runtime_quality.sh`](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/scripts/check_non_runtime_quality.sh)
- [`scripts/check_shared_benchmark_cache.sh`](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/scripts/check_shared_benchmark_cache.sh)
