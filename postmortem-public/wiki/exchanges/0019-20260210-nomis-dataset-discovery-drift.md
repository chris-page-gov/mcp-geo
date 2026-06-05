---
exchange_id: "EX-0019"
title: "NOMIS Dataset Discovery Drift"
source_id: "CONV-003"
global_sequence: 19
session_sequence: 4
user_timestamp: "2026-02-10"
timestamp_precision: "date"
publication_status: "public-safe-curated-derivative"
tags:
  - "exchange"
  - "mcp-geo"
  - "llm-wiki"
  - "client-interop"
  - "nomis"
  - "census-2021"
---

# 0019. NOMIS Dataset Discovery Drift

Conversation reader: [start-to-finish](../readers/conv-003-claude-leamington-warwick-stats-routing.md) | Previous: [EX-0018](0018-20260210-dashboard-render-fallback-to-direct-queries.md) | Next: [EX-0020](0020-20260210-census-query-parameter-failures.md)

## Publication Boundary

This is a curated public derivative. It preserves sequence and contribution
evidence, but it is not the raw Claude or Codex transcript.

## User Prompt

```text
Continue the statistics-routing comparison for Leamington Spa and Warwick.
```

## Curated Outcome

Broad dataset searches such as "population census 2021" and "census 2021" did
not produce the expected ward-level Census 2021 path. The client eventually
found useful topic-summary datasets with narrower searches, including `TS001`
population, `TS011` deprivation dimensions, `TS037` general health, `TS054`
tenure, `TS066` economic activity, and `TS067` qualifications.

## Why It Matters

Dataset discovery is not enough if clients have to rediscover naming
conventions every time. For common tasks, MCP-Geo should expose curated dataset
shortlists or search hints that map natural-language indicators to stable
dataset IDs and expected dimensions.
