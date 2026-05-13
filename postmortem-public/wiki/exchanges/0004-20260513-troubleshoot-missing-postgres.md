---
exchange_id: "EX-0004"
title: "Troubleshoot Missing Postgres"
source_id: "CONV-001"
global_sequence: 4
session_sequence: 4
user_timestamp: "2026-05-13"
timestamp_precision: "date"
publication_status: "public-safe-curated-derivative"
tags:
  - "exchange"
  - "mcp-geo"
  - "llm-wiki"
---

# 0004. Troubleshoot Missing Postgres

Conversation reader: [start-to-finish](../readers/conv-001-mcp-geo-landis-nottinghamshire-leacs.md) | Previous: [EX-0003](0003-20260513-explain-landis-warehouse-unavailability.md) | Next: [EX-0005](0005-20260513-extend-landis-coverage-to-nottinghamshire.md)

## Publication Boundary

This is a curated public derivative. It preserves sequence and contribution evidence, but it is not the raw Codex transcript.

## User Prompt

```text
Troubleshoot the missing Postgress
```

## Curated Codex Outcome

Recovered the local PostGIS path, verified PostGIS capability, and loaded/validated the phase-2 LandIS archive tables needed for NATMAP, Soilscapes, and NSI-style results. This showed that LandIS soil context was recoverable locally while LEACS-derived pipe risk remained a separate missing-data problem.
