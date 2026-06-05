---
exchange_id: "EX-0025"
title: "Rebuild Requirement and Regression Boundary"
source_id: "CONV-004"
global_sequence: 25
session_sequence: 4
user_timestamp: "2026-04-15"
timestamp_precision: "date"
publication_status: "public-safe-curated-derivative"
tags:
  - "exchange"
  - "mcp-geo"
  - "llm-wiki"
  - "ons-geo"
  - "cache"
  - "regression"
---

# 0025. Rebuild Requirement and Regression Boundary

Conversation reader: [start-to-finish](../readers/conv-004-ons-uprn-shard-ingestion-incident.md) | Previous: [EX-0024](0024-20260415-refresh-logic-streams-all-uprn-shards.md)

## Publication Boundary

This is a curated public derivative. It preserves sequence and contribution
evidence, but it is not the raw Claude or Codex transcript.

## User Prompt

```text
Record what remains required after the refresh-code fix.
```

## Curated Outcome

The fix changes future refresh behavior, but existing cache files created
before the patch remain incomplete until they are rebuilt. Regression coverage
now constructs split ONSUD/NSUL ZIP fixtures with `LN`, `WA`, and `YH` members
and asserts that all three UPRNs appear in both the row table and the UPRN
index.

## Why It Matters

This exchange preserves the operational closure condition. A green code change
does not repair already-populated local caches; the rebuild step is part of the
incident response.
