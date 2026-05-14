---
exchange_id: "EX-0023"
title: "Cache Diagnosis Finds Single-Shard Ingestion"
source_id: "CONV-004"
global_sequence: 23
session_sequence: 2
user_timestamp: "2026-04-15"
timestamp_precision: "date"
publication_status: "public-safe-curated-derivative"
tags:
  - "exchange"
  - "mcp-geo"
  - "llm-wiki"
  - "ons-geo"
  - "cache"
  - "diagnosis"
---

# 0023. Cache Diagnosis Finds Single-Shard Ingestion

Conversation reader: [start-to-finish](../readers/conv-004-ons-uprn-shard-ingestion-incident.md) | Previous: [EX-0022](0022-20260415-uprn-lookup-false-not-found.md) | Next: [EX-0024](0024-20260415-refresh-logic-streams-all-uprn-shards.md)

## Publication Boundary

This is a curated public derivative. It preserves sequence and contribution
evidence, but it is not the raw Claude or Codex transcript.

## User Prompt

```text
Check whether the ONS geography cache contents match the advertised ingested products.
```

## Curated Outcome

The diagnosis found that ONSUD/NSUL source ZIPs were region-sharded under data
members, while the refresh process had selected only one best-scoring CSV
member from each archive. The affected cache therefore contained only one
regional shard while product status still said `ingested`.

## Why It Matters

Cache status needs coverage evidence, not just product-level ingestion status.
For sharded products, loading one valid member can make health look green while
large parts of the country are absent.
