---
exchange_id: "EX-0016"
title: "Broad Leamington/Warwick Comparison Overloads Search"
source_id: "CONV-003"
global_sequence: 16
session_sequence: 1
user_timestamp: "2026-02-07"
timestamp_precision: "date"
publication_status: "public-safe-curated-derivative"
tags:
  - "exchange"
  - "mcp-geo"
  - "llm-wiki"
  - "client-interop"
  - "statistics"
  - "admin-boundaries"
---

# 0016. Broad Leamington/Warwick Comparison Overloads Search

Conversation reader: [start-to-finish](../readers/conv-003-claude-leamington-warwick-stats-routing.md) | Previous: [EX-0015](0015-20260214-surrounding-postcodes-road-workbook-request.md) | Next: [EX-0017](0017-20260210-stats-routing-ward-comparison-contract.md)

## Publication Boundary

This is a curated public derivative. It preserves sequence and contribution
evidence, but it is not the raw Claude or Codex transcript.

## User Prompt

```text
use mcp-geo to compare life in Leamington and Warwick
```

## Curated Outcome

The client began by using OS name search and administrative-area lookup. It
found the relevant towns and established that both sit in Warwick district, but
the initial search path produced broad transport, road, place, and facility
matches before the comparison narrowed to ward-level geography.

## Why It Matters

A "compare life" request needs an explicit decomposition step. Without it, a
client can spend context on broad name-search output before selecting the
comparison unit. For this task, the durable comparison unit was ward sets, not
raw place-name search results.
