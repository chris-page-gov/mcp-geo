---
exchange_id: "EX-0011"
title: "CV1 Map Request Produces Fragile HTML Output"
source_id: "CONV-002"
global_sequence: 11
session_sequence: 1
user_timestamp: "2026-02-13"
timestamp_precision: "date"
publication_status: "public-safe-curated-derivative"
tags:
  - "exchange"
  - "mcp-geo"
  - "llm-wiki"
  - "client-interop"
  - "maps"
---

# 0011. CV1 Map Request Produces Fragile HTML Output

Conversation reader: [start-to-finish](../readers/conv-002-claude-cv1-map-failure-success.md) | Next: [EX-0012](0012-20260213-os-mapping-api-key-handling-drift.md)

## Publication Boundary

This is a curated public derivative. It preserves sequence and contribution
evidence, but it is not the raw Claude or Codex transcript.

## User Prompt

```text
show me cv1 3hb on a map
```

## Curated Outcome

The client correctly identified the task as a postcode-to-map request and
found that `CV1 3HB` refers to addresses on and around Spon End in Coventry.
The failure was in the delivery surface: instead of returning a robust
MCP-Geo map descriptor or host-compatible resource handoff, the client created
standalone HTML that depended on browser libraries loading correctly inside the
client artifact environment.

## Why It Matters

This is the first failure mode in the CV1 sequence: the data lookup was
tractable, but the presentation path was too brittle for the host. Future map
tools need to expose explicit map resources/descriptors and fallback metadata
instead of forcing the model to improvise a complete web application in chat.
