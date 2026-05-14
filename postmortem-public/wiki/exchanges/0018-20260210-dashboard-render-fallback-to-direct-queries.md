---
exchange_id: "EX-0018"
title: "Dashboard Render Fallback to Direct Queries"
source_id: "CONV-003"
global_sequence: 18
session_sequence: 3
user_timestamp: "2026-02-10"
timestamp_precision: "date"
publication_status: "public-safe-curated-derivative"
tags:
  - "exchange"
  - "mcp-geo"
  - "llm-wiki"
  - "client-interop"
  - "mcp-apps"
  - "dashboard"
---

# 0018. Dashboard Render Fallback to Direct Queries

Conversation reader: [start-to-finish](../readers/conv-003-claude-leamington-warwick-stats-routing.md) | Previous: [EX-0017](0017-20260210-stats-routing-ward-comparison-contract.md) | Next: [EX-0019](0019-20260210-nomis-dataset-discovery-drift.md)

## Publication Boundary

This is a curated public derivative. It preserves sequence and contribution
evidence, but it is not the raw Claude or Codex transcript.

## User Prompt

```text
Continue the statistics-routing comparison for Leamington Spa and Warwick.
```

## Curated Outcome

After finding the ward sets, the client tried to use a statistics dashboard for
the multi-area comparison. The dashboard path did not render in the example
context, so the client switched to direct NOMIS dataset discovery and query
construction.

## Why It Matters

Dashboard tools need a visible fallback contract. If the host cannot render the
dashboard, the response should still expose the selected areas, intended
indicators, and direct-query plan. Otherwise the client loses the structured
comparison state and starts reconstructing it through broad dataset searches.
