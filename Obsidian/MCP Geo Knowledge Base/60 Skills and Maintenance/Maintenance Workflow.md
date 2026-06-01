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
source_commit: "2d7d7ba76db4643934aa2bd1b294e0e352285702"
source_commit_dirty: true
source_urls:
  - "https://github.com/chris-page-gov/mcp-geo/blob/2d7d7ba76db4643934aa2bd1b294e0e352285702/AGENTS.md"
  - "https://github.com/chris-page-gov/mcp-geo/blob/2d7d7ba76db4643934aa2bd1b294e0e352285702/CHANGELOG.md"
  - "https://github.com/chris-page-gov/mcp-geo/blob/2d7d7ba76db4643934aa2bd1b294e0e352285702/CONTEXT.md"
  - "https://github.com/chris-page-gov/mcp-geo/blob/2d7d7ba76db4643934aa2bd1b294e0e352285702/PROGRESS.MD"
  - "https://github.com/chris-page-gov/mcp-geo/blob/2d7d7ba76db4643934aa2bd1b294e0e352285702/README.md"
  - "https://github.com/chris-page-gov/mcp-geo/blob/2d7d7ba76db4643934aa2bd1b294e0e352285702/scripts/build_obsidian_kb.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/2d7d7ba76db4643934aa2bd1b294e0e352285702/scripts/validate_obsidian_kb.py"
source_hashes:
  AGENTS.md: "sha256:48bfd2dd-ca8e9bf2-91c51fb0-550894d3-a351736c-61502efc-b8591312-eb1e46c9"
  CHANGELOG.md: "sha256:7609427d-3636dc27-ba969ca5-4ed0c777-8469c7a8-5fb9d2db-63dad5eb-34168c23"
  CONTEXT.md: "sha256:320e381f-5f7471c2-97d5ed69-8c72003e-d5f4c724-3426eb51-ca99076b-eede3adb"
  PROGRESS.MD: "sha256:cb45234f-a9a2e553-76fab9f1-837fe7ab-f8cfdc22-083df4d5-88ada35f-40ecefaa"
  README.md: "sha256:a62356fd-fa1a2081-4365a154-0c0f9f7a-fe2f3009-5ae1b98e-8676a29e-6ed3ea31"
  scripts/build_obsidian_kb.py: "sha256:4d03f023-c72e23f8-992bcd8c-bac2fc36-016c9551-bcb968fb-74be77f7-ace0ed5b"
  scripts/validate_obsidian_kb.py: "sha256:8c97e6a6-82ff6a37-cadd7fa5-4d6f9993-66c38ad8-d8dee9e6-53ff2cd8-a104f378"
generated_at: "2026-06-01T01:38:32Z"
evidence_scope: "canon"
first_seen_date: "2025-08-20"
last_validated_at: "2026-06-01T01:38:32Z"
---
# Maintenance Workflow

1. Refresh the canonical vault with `scripts/build_obsidian_kb.py --mode canon`.
2. Refresh the local overlay only when local traces are needed.
3. Run `scripts/validate_obsidian_kb.py` against the canonical manifest.
4. Update repo tracking docs when the KB work introduces a new maintained surface.
