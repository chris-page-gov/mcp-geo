---
title: "Script Family - check"
kb_kind: "code_family"
source_paths:
  - "scripts/check_claude_startup_scope.sh"
  - "scripts/check_codex_startup_scope.sh"
  - "scripts/check_gemini_startup_scope.sh"
  - "scripts/check_lmr_host4.py"
  - "scripts/check_non_runtime_quality.sh"
  - "scripts/check_shared_benchmark_cache.sh"
  - "scripts/check_spec_drift.py"
source_commit: "923807292e3a134ad8214be3de523caa7fdce7c5"
source_commit_dirty: true
source_urls:
  - "https://github.com/chris-page-gov/mcp-geo/blob/923807292e3a134ad8214be3de523caa7fdce7c5/scripts/check_claude_startup_scope.sh"
  - "https://github.com/chris-page-gov/mcp-geo/blob/923807292e3a134ad8214be3de523caa7fdce7c5/scripts/check_codex_startup_scope.sh"
  - "https://github.com/chris-page-gov/mcp-geo/blob/923807292e3a134ad8214be3de523caa7fdce7c5/scripts/check_gemini_startup_scope.sh"
  - "https://github.com/chris-page-gov/mcp-geo/blob/923807292e3a134ad8214be3de523caa7fdce7c5/scripts/check_lmr_host4.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/923807292e3a134ad8214be3de523caa7fdce7c5/scripts/check_non_runtime_quality.sh"
  - "https://github.com/chris-page-gov/mcp-geo/blob/923807292e3a134ad8214be3de523caa7fdce7c5/scripts/check_shared_benchmark_cache.sh"
  - "https://github.com/chris-page-gov/mcp-geo/blob/923807292e3a134ad8214be3de523caa7fdce7c5/scripts/check_spec_drift.py"
source_hashes:
  scripts/check_claude_startup_scope.sh: "sha256:5462dfda-47696e0e-df3d46ad-1a2b8fde-f8f36816-ac28701e-882f2588-64cf0cec"
  scripts/check_codex_startup_scope.sh: "sha256:0a04713e-6501ad4e-a2a4d9bc-dae537b4-6a8a15b8-782e9c90-12ad17cc-766f2a1c"
  scripts/check_gemini_startup_scope.sh: "sha256:67fec5a2-084ea006-7b7e6274-e22737a4-85ef548c-14fda633-44d02113-229fe137"
  scripts/check_lmr_host4.py: "sha256:09d10f54-a510a24f-31ef1cfb-2bbeaddf-e4ab0f37-08a0f026-133fc733-260a896a"
  scripts/check_non_runtime_quality.sh: "sha256:419d0bef-3c801a45-79a41dd5-a1cf6ecc-99485f53-934dc6fa-fd26a0e2-d8f64f66"
  scripts/check_shared_benchmark_cache.sh: "sha256:8835d736-1d2289b5-84820eea-495c5b77-2329d06a-78861d21-7486a312-ffd65a6c"
  scripts/check_spec_drift.py: "sha256:3739c940-8f7e31aa-4eb7ade5-2a49fb3f-df94d814-7c2e928f-1201e896-5c8ec934"
generated_at: "2026-06-01T02:28:24Z"
evidence_scope: "canon"
first_seen_date: "2026-02-22"
last_validated_at: "2026-06-01T02:28:24Z"
---
# Script Family - check

## Evidence Scope

- Categories: `code_runtime`
- Source file count: 7

## Source Inventory

| Path | Summary | First Seen | Last Commit | Related Tests |
| --- | --- | --- | --- | --- |
| `scripts/check_claude_startup_scope.sh` | set -euo pipefail | 2026-03-03 | 2026-04-12 | - |
| `scripts/check_codex_startup_scope.sh` | set -euo pipefail | 2026-03-03 | 2026-04-12 | - |
| `scripts/check_gemini_startup_scope.sh` | set -euo pipefail | 2026-03-03 | 2026-04-12 | - |
| `scripts/check_lmr_host4.py` | Automate LMR-HOST-4 evidence checks for Claude Desktop sessions. This script focuses on the known host-runtime gap: - Wi | 2026-02-22 | 2026-02-22 | `tests/test_check_lmr_host4.py` |
| `scripts/check_non_runtime_quality.sh` | set -euo pipefail | 2026-02-22 | 2026-03-24 | - |
| `scripts/check_shared_benchmark_cache.sh` | set -euo pipefail | 2026-03-10 | 2026-04-12 | - |
| `scripts/check_spec_drift.py` | from __future__ import annotations | 2026-04-12 | 2026-04-28 | `tests/test_check_spec_drift.py` |

## Pinned Sources

- [`scripts/check_claude_startup_scope.sh`](https://github.com/chris-page-gov/mcp-geo/blob/923807292e3a134ad8214be3de523caa7fdce7c5/scripts/check_claude_startup_scope.sh)
- [`scripts/check_codex_startup_scope.sh`](https://github.com/chris-page-gov/mcp-geo/blob/923807292e3a134ad8214be3de523caa7fdce7c5/scripts/check_codex_startup_scope.sh)
- [`scripts/check_gemini_startup_scope.sh`](https://github.com/chris-page-gov/mcp-geo/blob/923807292e3a134ad8214be3de523caa7fdce7c5/scripts/check_gemini_startup_scope.sh)
- [`scripts/check_lmr_host4.py`](https://github.com/chris-page-gov/mcp-geo/blob/923807292e3a134ad8214be3de523caa7fdce7c5/scripts/check_lmr_host4.py)
- [`scripts/check_non_runtime_quality.sh`](https://github.com/chris-page-gov/mcp-geo/blob/923807292e3a134ad8214be3de523caa7fdce7c5/scripts/check_non_runtime_quality.sh)
- [`scripts/check_shared_benchmark_cache.sh`](https://github.com/chris-page-gov/mcp-geo/blob/923807292e3a134ad8214be3de523caa7fdce7c5/scripts/check_shared_benchmark_cache.sh)
- [`scripts/check_spec_drift.py`](https://github.com/chris-page-gov/mcp-geo/blob/923807292e3a134ad8214be3de523caa7fdce7c5/scripts/check_spec_drift.py)
