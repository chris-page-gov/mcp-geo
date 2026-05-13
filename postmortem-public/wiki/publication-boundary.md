---
title: "MCP-Geo Conversation Wiki Publication Boundary"
tags:
  - "publication-boundary"
  - "mcp-geo"
  - "llm-wiki"
---

# Publication Boundary

This wiki is a public-safe derivative of MCP-Geo conversation work. It is designed for durable project memory, audit, and future agent reuse without exposing raw local transcripts or credentials.

## Included

- User prompts that are already visible in the working thread.
- Curated summaries of Codex actions and outcomes.
- Repository-relative links to reports, research metadata, changelog fragments, and context notes.
- Operational facts needed for future work, such as dataset availability, table coverage, and decision points.

## Excluded

- API keys, access tokens, browser session tokens, and secret file paths.
- Raw terminal output where it would expose local-only details without adding durable project value.
- Full raw transcript JSONL/session paths, because no raw export was available for this record.
- Any claim that LEACS data was downloaded; the evidence supports the opposite conclusion.

## Redaction Style

- External local data roots are generalized as `[EXTSSD_DATA_ROOT]`.
- Local secret files are generalized as `[LOCAL_SECRET_FILE]`.
- The repository root is generalized as `[LOCAL_REPO]` where needed.
- Authenticated portal access is described by route and result, not by token or credential value.
