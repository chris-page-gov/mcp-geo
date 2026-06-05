---
exchange_id: "EX-0014"
title: "Constrained CV1 Postcode Tool Probes"
source_id: "CONV-002"
global_sequence: 14
session_sequence: 4
user_timestamp: "2026-02-14"
timestamp_precision: "date"
publication_status: "public-safe-curated-derivative"
tags:
  - "exchange"
  - "mcp-geo"
  - "llm-wiki"
  - "client-interop"
  - "os-places"
  - "cv1-3hb"
---

# 0014. Constrained CV1 Postcode Tool Probes

Conversation reader: [start-to-finish](../readers/conv-002-claude-cv1-map-failure-success.md) | Previous: [EX-0013](0013-20260213-vector-tile-runtime-csp-failures.md) | Next: [EX-0015](0015-20260214-surrounding-postcodes-road-workbook-request.md)

## Publication Boundary

This is a curated public derivative. It preserves sequence and contribution
evidence, but it is not the raw Claude or Codex transcript.

## User Prompt

```text
Use MCP server mcp-geo and perform exactly one MCP tool call:
os_places_by_postcode with postcode CV1 3HB.
Do not run shell commands. Return only the first address string from the tool result.
```

## Curated Outcome

The constrained probes changed the problem from "build and display a map" to
"prove the postcode lookup works." The tool call returned stable OS Places
data for `CV1 3HB`, including Spon End addresses and coordinates around
Coventry. Because the task was narrow, the result was auditable and did not
trigger the generated-map failure loop.

## Why It Matters

This exchange provides the control case for CONV-002. The underlying data path
was healthy; the failures were caused by client rendering, task breadth, and
presentation choices. Narrow MCP calls are easier for clients to execute,
verify, and recover from.
