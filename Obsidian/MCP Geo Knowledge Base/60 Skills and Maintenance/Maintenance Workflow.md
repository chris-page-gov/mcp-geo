---
title: "Maintenance Workflow"
kb_kind: "maintenance_note"
source_paths:
  - "AGENTS.md"
  - "CHANGELOG.md"
  - "CONTEXT.md"
  - "PROGRESS.MD"
  - "README.md"
  - "scripts/build_obsidian_kb.py"
  - "scripts/validate_obsidian_kb.py"
source_commit: "b279fe5fde6669d57955890996cd6fa6ddca76fb"
source_commit_dirty: true
source_urls:
  - "https://github.com/chris-page-gov/mcp-geo/blob/b279fe5fde6669d57955890996cd6fa6ddca76fb/AGENTS.md"
  - "https://github.com/chris-page-gov/mcp-geo/blob/b279fe5fde6669d57955890996cd6fa6ddca76fb/CHANGELOG.md"
  - "https://github.com/chris-page-gov/mcp-geo/blob/b279fe5fde6669d57955890996cd6fa6ddca76fb/CONTEXT.md"
  - "https://github.com/chris-page-gov/mcp-geo/blob/b279fe5fde6669d57955890996cd6fa6ddca76fb/PROGRESS.MD"
  - "https://github.com/chris-page-gov/mcp-geo/blob/b279fe5fde6669d57955890996cd6fa6ddca76fb/README.md"
  - "https://github.com/chris-page-gov/mcp-geo/blob/b279fe5fde6669d57955890996cd6fa6ddca76fb/scripts/build_obsidian_kb.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/b279fe5fde6669d57955890996cd6fa6ddca76fb/scripts/validate_obsidian_kb.py"
source_hashes:
  AGENTS.md: "sha256:6a1a5b80-1f795ef4-3d36948d-16d041ef-e437fea0-06cdefad-da59c0f0-3e17de30"
  CHANGELOG.md: "sha256:252eed1f-fb15f22a-3e8565c7-6b106cd0-8ff2b9ee-5283fcb5-b57b1589-9c309984"
  CONTEXT.md: "sha256:7491e909-2b856e35-9845b0e1-b1810012-38af25c8-c53f46e6-03d769d6-e84157de"
  PROGRESS.MD: "sha256:36e56707-408a87b1-1d7424ba-f7865265-90fb6b64-77910634-ed261080-5fa6bafd"
  README.md: "sha256:93a5372d-b1622a15-6b0349dc-a4755814-ec389283-39420228-77e83a54-a5de7f5b"
  scripts/build_obsidian_kb.py: "sha256:4d03f023-c72e23f8-992bcd8c-bac2fc36-016c9551-bcb968fb-74be77f7-ace0ed5b"
  scripts/validate_obsidian_kb.py: "sha256:8c97e6a6-82ff6a37-cadd7fa5-4d6f9993-66c38ad8-d8dee9e6-53ff2cd8-a104f378"
generated_at: "2026-04-06T13:09:04Z"
evidence_scope: "canon"
first_seen_date: "2025-08-20"
last_validated_at: "2026-04-06T13:09:04Z"
---
# Maintenance Workflow

1. Refresh the canonical vault with `scripts/build_obsidian_kb.py --mode canon`.
2. Refresh the local overlay only when local traces are needed.
3. Run `scripts/validate_obsidian_kb.py` against the canonical manifest.
4. Update repo tracking docs when the KB work introduces a new maintained surface.
