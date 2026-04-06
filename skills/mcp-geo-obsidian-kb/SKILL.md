---
name: mcp-geo-obsidian-kb
description: Refresh, validate, and maintain the checked-in MCP Geo Obsidian knowledge base, including the canonical vault, local overlay, and drift checks.
---

# MCP Geo Obsidian Knowledge Base

Use this skill when you need to refresh or validate the repo knowledge base
under `Obsidian/MCP Geo Knowledge Base/`.

## Scope

- Canonical tier: checked-in markdown generated from tracked repo content.
- Local overlay tier: ignored, machine-local notes generated from `logs/` and
  session traces when explicitly requested.
- Validation: coverage, drift, recursion exclusion, and missing-note checks.

## Default commands

Refresh the canonical vault:

```bash
python3 scripts/build_obsidian_kb.py \
  --mode canon \
  --git-ref WORKTREE \
  --output-root "Obsidian/MCP Geo Knowledge Base" \
  --manifest-out data/knowledge_base/obsidian_kb_manifest.json
```

Refresh the canonical vault plus local overlay:

```bash
python3 scripts/build_obsidian_kb.py \
  --mode all \
  --git-ref WORKTREE \
  --output-root "Obsidian/MCP Geo Knowledge Base" \
  --manifest-out data/knowledge_base/obsidian_kb_manifest.json \
  --overlay-manifest-out data/knowledge_base/obsidian_kb_overlay_manifest.json \
  --include-local-evidence
```

Validate the canonical manifest:

```bash
python3 scripts/validate_obsidian_kb.py \
  --manifest data/knowledge_base/obsidian_kb_manifest.json \
  --fail-on drift coverage recursion orphan
```

## Maintenance rules

1. Never let the generator scan `Obsidian/**`.
2. Treat tracked repo content as the canonical evidence source.
3. Keep local traces in `98 Local Overlay/` only; do not promote them into the
   canonical tier unless they are first captured as tracked repo artifacts.
4. Prefer commit-pinned GitHub links in generated notes.
5. When validator drift or coverage failures appear, refresh the vault after
   the underlying tracked content is updated.

## Promotion workflow

- If a local trace becomes durable evidence, write or generate a tracked report,
  research note, or manifest elsewhere in the repo first.
- Rebuild the canonical vault only after that tracked artifact exists.
- Do not copy speculative interpretation into the knowledge base; keep notes
  descriptive and evidence-backed.
