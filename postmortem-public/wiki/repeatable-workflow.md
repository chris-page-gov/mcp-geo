---
title: "Repeatable Conversation Postmortem Workflow"
tags:
  - "llm-wiki"
  - "postmortem"
  - "workflow"
---

# Repeatable Conversation Postmortem Workflow

This workflow turns local Codex conversation logs into a curated, publishable
LLM-wiki record. It keeps raw and operational source material private while
publishing only redacted derivatives.

## Directory Contract

- `postmortem/` is private and gitignored. It can contain candidate
  inventories, raw transcript exports, source hashes, and working notes.
- `postmortem-public/` is tracked and publishable. It contains redacted
  wiki pages, exchange notes, source notes, readers, decisions, repository
  evidence, and machine-readable registers.

## Stage 1: Candidate Discovery

Run this from the repository root:

```bash
python3 scripts/llm_wiki_postmortem_inventory.py
```

The inventory script scans local Codex rollout logs under `$CODEX_HOME/sessions`
or `~/.codex/sessions`, filters sessions for the current repository, and writes
private candidate files under `postmortem/candidates/`.

The generated candidate list is sorted newest first and includes:

- session ID and start timestamp
- inferred title and session kind
- visible user/assistant message counts
- estimated visible tokens
- tool-call counts
- curation effort band
- source log path and SHA-256 hash

It also writes a repeated-session rollup that sums metrics for prompt patterns
that should normally be curated as one batch:

- scheduled automations across their full observed span
- repeated retry prompts inside a time window
- short status/check-monitoring prompts, such as PR check polling

The rollup includes session counts, summed token estimates, summed tool calls,
session ID ranges, and a suggested curation treatment.

## Stage 2: Promotion

Promote only selected candidates into `postmortem-public/`.

For each selected session:

1. Keep raw source evidence and any sensitive operational notes in
   `postmortem/`.
2. Add a redacted source note under `postmortem-public/wiki/sources/`.
3. Split useful prompt/response units into
   `postmortem-public/wiki/exchanges/`.
4. Add or update a start-to-finish reader under
   `postmortem-public/wiki/readers/`.
5. Summarize repeated-session groups compactly instead of publishing every
   repeated run as a standalone exchange.
6. Update the index, summary, decision register, repository evidence, and JSON
   registers.
7. Run publication checks before committing.

## Effort Bands

| Band | Meaning |
|---|---|
| `tiny` | About 15-30 min; one to three exchanges. |
| `small` | About 30-60 min; short focused session. |
| `medium` | About 1-2 h; multiple exchanges or moderate tool use. |
| `large` | About 2-4 h; lengthy curation and redaction. |
| `very_large` | More than 4 h or split first. |

## Publication Boundary

Public pages must not include API keys, tokens, browser session material, raw
private transcript paths, or full local secret-file paths. Use placeholders such
as `[LOCAL_PATH]`, `[EXTSSD_DATA_PATH]`, `[LOCAL_SECRET_FILE]`, and
`[PORTAL_ACCOUNT]` when operational context is useful.

Public pages should cite durable repo artifacts, redacted notes, source hashes,
and decision summaries rather than raw logs.
