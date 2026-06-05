---
exchange_id: "EX-0017"
title: "Stats Routing Creates a Ward-Level Comparison Contract"
source_id: "CONV-003"
global_sequence: 17
session_sequence: 2
user_timestamp: "2026-02-10"
timestamp_precision: "date"
publication_status: "public-safe-curated-derivative"
tags:
  - "exchange"
  - "mcp-geo"
  - "llm-wiki"
  - "client-interop"
  - "stats-routing"
  - "nomis"
---

# 0017. Stats Routing Creates a Ward-Level Comparison Contract

Conversation reader: [start-to-finish](../readers/conv-003-claude-leamington-warwick-stats-routing.md) | Previous: [EX-0016](0016-20260207-leamington-warwick-broad-comparison-overload.md) | Next: [EX-0018](0018-20260210-dashboard-render-fallback-to-direct-queries.md)

## Publication Boundary

This is a curated public derivative. It preserves sequence and contribution
evidence, but it is not the raw Claude or Codex transcript.

## User Prompt

```text
Use stats routing to allow me to compare life in Leamington Spa and Warwick.
```

## Curated Outcome

The stats-routing tool selected NOMIS because the request involved
labour/census indicators such as population, employment, health, housing, and
education. It recommended ward-level targeting, `admin_lookup.find_by_name`,
the statistics dashboard, and direct `nomis.query` calls after selecting area
codes.

The area-selection step identified a useful current-ward working set:
Leamington Willes, Brunswick, Clarendon, Milverton, and Lillington; plus
Warwick Aylesford, Saltisford, Myton & Heathcote, and All Saints & Woodloes.

## Why It Matters

This exchange shows the strongest part of the client/tool flow. Routing
correctly chose the provider and level, and admin lookup supplied usable
geography. The missing piece was an executable query plan that turned those
recommendations into complete NOMIS calls and a final comparison table.
