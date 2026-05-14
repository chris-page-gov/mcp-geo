---
exchange_id: "EX-0012"
title: "OS Mapping and API-Key Handling Drift"
source_id: "CONV-002"
global_sequence: 12
session_sequence: 2
user_timestamp: "2026-02-13"
timestamp_precision: "date"
publication_status: "public-safe-curated-derivative"
tags:
  - "exchange"
  - "mcp-geo"
  - "llm-wiki"
  - "client-interop"
  - "os-maps"
  - "secrets"
---

# 0012. OS Mapping and API-Key Handling Drift

Conversation reader: [start-to-finish](../readers/conv-002-claude-cv1-map-failure-success.md) | Previous: [EX-0011](0011-20260213-cv1-map-request-fragile-html-output.md) | Next: [EX-0013](0013-20260213-vector-tile-runtime-csp-failures.md)

## Publication Boundary

This is a curated public derivative. It preserves sequence and contribution
evidence, but it is not the raw Claude or Codex transcript.

## User Prompt

```text
Everytime we do this you give me this console error: L is not defined.
Also, make sure you use OS Mapping.

Again, failed as before - do you need to prompt me for the OS_API_KEY?

Open a dialogue on the map so it does not get logged or exposed in a conversation tracking app.
```

## Curated Outcome

The user pushed the client toward two requirements at once: use Ordnance Survey
mapping and avoid leaking the OS API key into conversation logs. The client
responded by attempting script-order fixes and then a browser-side key-entry
dialog. The privacy instinct was sound, but the implementation still depended
on a fragile standalone page and did not resolve the host rendering problem.

## Why It Matters

This exchange records a useful boundary: credentials must be treated as local
runtime configuration, not transcript content. It also shows why asking a model
to repair generated HTML is a weak substitute for a server-owned map delivery
contract that can use `OS_API_KEY` safely and return a host-compatible map
resource.
