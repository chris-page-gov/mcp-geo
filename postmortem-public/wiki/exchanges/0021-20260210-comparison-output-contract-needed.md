---
exchange_id: "EX-0021"
title: "Comparison Output Contract Needed"
source_id: "CONV-003"
global_sequence: 21
session_sequence: 6
user_timestamp: "2026-02-10"
timestamp_precision: "date"
publication_status: "public-safe-curated-derivative"
tags:
  - "exchange"
  - "mcp-geo"
  - "llm-wiki"
  - "client-interop"
  - "statistics"
  - "structured-output"
---

# 0021. Comparison Output Contract Needed

Conversation reader: [start-to-finish](../readers/conv-003-claude-leamington-warwick-stats-routing.md) | Previous: [EX-0020](0020-20260210-census-query-parameter-failures.md) | Next: CONV-004 pending

## Publication Boundary

This is a curated public derivative. It preserves sequence and contribution
evidence, but it is not the raw Claude or Codex transcript.

## User Prompt

```text
Continue the statistics-routing comparison for Leamington Spa and Warwick.
```

## Curated Outcome

The client did not reach a reliable comparative answer. It had the right broad
workflow ingredients: routing, ward lookup, relevant indicator families, and
candidate datasets. It lacked a compact output contract that preserved the
selected wards, indicator list, query templates, and fallback result table when
dashboard rendering or direct queries failed.

## Why It Matters

This exchange turns the failed session into a product requirement. MCP-Geo
comparison tools should return a restartable analysis plan and a stable
machine-readable state object, so another client or later run can continue
without repeating discovery loops.
