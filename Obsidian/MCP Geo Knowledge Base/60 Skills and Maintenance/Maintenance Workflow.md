---
title: "Maintenance Workflow"
kb_kind: "maintenance_note"
source_paths:
  - "AGENTS.md"
  - "CHANGELOG.md"
  - "CONTEXT.md"
  - "PROGRESS.MD"
  - "README.md"
source_commit: "bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851"
source_commit_dirty: true
source_urls:
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/AGENTS.md"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/CHANGELOG.md"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/CONTEXT.md"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/PROGRESS.MD"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/README.md"
source_hashes:
  AGENTS.md: "6a1a5b801f795ef43d36948d16d041efe437fea006cdefadda59c0f03e17de30"
  CHANGELOG.md: "9f8a72a8b1f9f4d8480398e9ea1002aa504c97bce87633cdf88c3f9b61132334"
  CONTEXT.md: "84fc74b172fc3fdd6b3cceb4ee7e5b77f3785b252ad0b3670de07b61671ce055"
  PROGRESS.MD: "4f33a28d5b0311dd173afe1b2a33d1b58a5f3c49eab1fea8a251ee3d3c3afe5b"
  README.md: "74d66e7b6af82310cdc6ee6d4fb941f53d6b16cace80156887dbb5e9cc685e8a"
generated_at: "2026-04-06T09:00:35Z"
evidence_scope: "canon"
first_seen_date: "2025-08-20"
last_validated_at: "2026-04-06T09:00:35Z"
---
# Maintenance Workflow

1. Refresh the canonical vault with `scripts/build_obsidian_kb.py --mode canon`.
2. Refresh the local overlay only when local traces are needed.
3. Run `scripts/validate_obsidian_kb.py` against the canonical manifest.
4. Update repo tracking docs when the KB work introduces a new maintained surface.
