---
exchange_id: "EX-0003"
title: "Explain LandIS Warehouse Unavailability"
source_id: "CONV-001"
global_sequence: 3
session_sequence: 3
user_timestamp: "2026-05-13"
timestamp_precision: "date"
publication_status: "public-safe-curated-derivative"
tags:
  - "exchange"
  - "mcp-geo"
  - "llm-wiki"
---

# 0003. Explain LandIS Warehouse Unavailability

Conversation reader: [start-to-finish](../readers/conv-001-mcp-geo-landis-nottinghamshire-leacs.md) | Previous: [EX-0002](0002-20260513-assess-nottinghamshire-geotechnical-earthworks-collapse-risk.md) | Next: [EX-0004](0004-20260513-troubleshoot-missing-postgres.md)

## Publication Boundary

This is a curated public derivative. It preserves sequence and contribution evidence, but it is not the raw Codex transcript.

## User Prompt

```text
Why was The LandIS warehouse unavailable
```

## Curated Codex Outcome

Explained that the failure was a local runtime/data state issue: the MCP server could run, but the configured LandIS warehouse path did not yet expose the needed pipe-risk tables for the requested Nottinghamshire workflow. The diagnosis separated server availability, DSN configuration, Docker/PostGIS availability, and data-table coverage.
