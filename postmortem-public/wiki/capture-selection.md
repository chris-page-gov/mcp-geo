---
title: "Selected Conversation Capture Queue"
tags:
  - "capture-selection"
  - "llm-wiki"
  - "mcp-geo"
  - "conversation-record"
---

# Selected Conversation Capture Queue

This page records the first Stage 2 capture selection after reviewing the
existing conversation examples in `docs/`. It is a public-safe selection plan:
the raw Codex JSONL paths and private inventories remain under gitignored
`postmortem/`, while this page records which sessions should be curated next
and why.

## Reviewed Example Documents

| Source document | Lines | Theme | Selection signal |
|---|---:|---|---|
| [Claude failed conversation](../../docs/Claude_failed_conversation.md) | 764 | CV1 3HB map failure, repeated browser-library errors, OS mapping fallback confusion | Shows why raw map-generation output and oversized tool responses need a curated diagnostic record. |
| [Claude success conversation](../../docs/Claude_success_conversation.md) | 479 | CV1 3HB postcode lookup, surrounding UPRNs, road-name workbook request | Provides the success contrast for bounded OS Places calls and structured extraction. |
| [Claude Opus failed conversation 1](../../docs/Claude_opus_4-6_failed_convo_1.md) | 517 | Leamington Spa vs Warwick stats routing, NOMIS querying, dashboard/rendering friction | Shows client/tool confusion around statistical routing and multi-step analysis. |
| [Claude Opus failed conversation 2](../../docs/claude_opus_4-6_failed_convo_2.md) | 264 | Leamington/Warwick comparison with admin lookup and NOMIS/ONS fallback attempts | Second independent example of the same comparison intent, useful for triangulating failure modes. |

## Selected Capture Batch

| Capture ID | Priority | Session | Date | Effort | Est. tokens | Tool calls | Public source signal | Why capture |
|---|---:|---|---|---|---:|---:|---|---|
| CAP-001 | 1 | `019c2ffd-c59f-7bd2-b989-db8a21019ca0` | 2026-02-05 | `large` | 138,487 | 869 | Opus 4.6 / Claude comprehension examples | Overarching diagnostic session for the earliest "best model, poor MCP understanding" problem. This should become the main reader for the Claude-client failure family. |
| CAP-002 | 2 | `019c5742-38dd-7361-9ebc-675c1c6768d9` | 2026-02-13 | `small` | 4,883 | 70 | [Claude failed conversation](../../docs/Claude_failed_conversation.md) | Focused follow-up on the CV1 3HB map failure and oversized/fragile map handoff behaviour. |
| CAP-003 | 3 | `019c5d1f-c361-7110-9db2-3da81253f3e9` | 2026-02-14 | `small` | 4,384 | 24 | [Claude success conversation](../../docs/Claude_success_conversation.md) | Minimal constrained `os_places.by_postcode` probe for CV1 3HB; useful as the success/control case. |
| CAP-004 | 4 | `019c5d25-3c0f-76c3-95c7-b070f940db9e` | 2026-02-14 | `small` | 4,020 | 1 | [Claude success conversation](../../docs/Claude_success_conversation.md) | Second exact-tool-call sanity check for CV1 3HB, useful to show the impact of narrowing task scope. |
| CAP-005 | 5 | `019c3a1d-530b-71e3-b8ab-e21009305395` | 2026-02-07 | `small` | 5,270 | 75 | [Claude Opus failed conversation 2](../../docs/claude_opus_4-6_failed_convo_2.md) | Compact record of the Warwick/Leamington "Claude choked on OS data" failure family. |
| CAP-006 | 6 | `019c48f1-6a2c-7361-ae37-726cce23e500` | 2026-02-10 | `medium` | 16,018 | 433 | [Claude Opus failed conversation 1](../../docs/Claude_opus_4-6_failed_convo_1.md) | NOMIS/statistics-routing follow-up that connects the Leamington/Warwick examples to query-normalization fixes. |
| CAP-007 | 7 | `019d90c0-d4cf-75b0-adb4-7253ce356054` | 2026-04-15 | `small` | 6,634 | 97 | ONS UPRN / Claude failure incident | Companion client-failure capture: Welsh UPRNs returning `NOT_FOUND` because ONSUD/NSUL shard ingestion was incomplete. |

## Completion Status

CONV-002, CONV-003, and CONV-004 are now curated under the public wiki.
CAP-002 through CAP-007 are complete; CAP-001 has been used as context for
CONV-002 and CONV-003. The selected Stage 2 batch is complete.

## Batch Cost

| Scope | Sessions | Est. tokens | Tool calls | Curation estimate |
|---|---:|---:|---:|---:|
| Example-doc batch only, CAP-001 to CAP-006 | 6 | 173,062 | 1,472 | 5-10 h |
| With ONS/UPRN companion, CAP-001 to CAP-007 | 7 | 179,696 | 1,569 | 5.5-11 h |

This is the recommended next Stage 2 batch. It is much smaller than the full
non-repeated queue (`88` rows, about `1.79M` tokens), but it covers the highest
value client-interoperability examples already present in repository documents.

## Capture Shape

The selected batch should be curated as three public conversations rather than
seven separate readers:

| Planned conversation | Selected sessions | Source documents | Suggested shape |
|---|---|---|---|
| CONV-002: Claude CV1 map failure and constrained success path | CAP-002, CAP-003, CAP-004, with CAP-001 context | `Claude_failed_conversation.md`, `Claude_success_conversation.md` | One reader contrasting fragile map generation with bounded tool calls. |
| CONV-003: Claude Opus Leamington/Warwick stats-routing failures | CAP-005, CAP-006, with CAP-001 context | `Claude_opus_4-6_failed_convo_1.md`, `claude_opus_4-6_failed_convo_2.md` | One reader focused on admin lookup, NOMIS routing, over-broad data returns, and query repair. |
| CONV-004: ONS UPRN shard-ingestion incident | CAP-007 | Context and repo fixes | Short diagnostic reader focused on Welsh/non-Yorkshire UPRN `NOT_FOUND` behaviour and cache refresh remediation. |

## Selection Rules Applied

- Prefer source-backed sessions already linked to repository documents.
- Prefer compact diagnostics that explain reusable MCP/client design lessons.
- Include one large umbrella analysis only where it connects several small
  examples into one causal narrative.
- Keep raw logs private; publish only redacted source notes, readers, exchange
  summaries, decisions, and durable repo evidence.

## Restartable Execution Contract

Run Stage 2 as a sequence of small, idempotent slices. A run should be safe to
stop after any completed slice and safe to restart from the repository state.

Private resume state lives in gitignored `postmortem/stage2/`. Public progress
is reflected by the status values in
`postmortem-public/wiki/data/capture-selection-public.json` and by the presence
of completed readers/source notes/exchange pages.

Each restartable run should:

1. Read this page and `data/capture-selection-public.json`.
2. Read private checkpoint state from `postmortem/stage2/capture-progress.json`
   if it exists.
3. Select the first planned conversation with incomplete captures.
4. Curate one planned conversation, or one capture if the conversation is too
   large for a single reliable run.
5. Write only public-safe pages under `postmortem-public/wiki/`.
6. Update `data/capture-selection-public.json` and the private checkpoint.
7. Run JSON, link, private-path, and `git diff --check` publication checks.
8. Stop with a clear status summary rather than starting an unbounded next
   conversation.

Default order:

| Step | Planned conversation | Captures | Restart boundary |
|---:|---|---|---|
| 1 | CONV-002: Claude CV1 map failure and constrained success path | CAP-002, CAP-003, CAP-004, CAP-001 context | Complete reader/source/exchanges for CV1 before moving on. |
| 2 | CONV-003: Claude Opus Leamington/Warwick stats-routing failures | CAP-005, CAP-006, CAP-001 context | Complete stats-routing reader/source/exchanges before moving on. |
| 3 | CONV-004: ONS UPRN shard-ingestion incident | CAP-007 | Complete short diagnostic reader/source/exchanges. |
