---
source_id: "CONV-003"
title: "Claude Opus Leamington/Warwick Stats-Routing Failures"
source_type: "curated_conversation_summary"
publication_status: "public-safe-curated-derivative"
conversation_date: "2026-02-07/2026-02-10"
exchange_count: 6
raw_transcript_status: "not-exported"
capture_ids:
  - "CAP-005"
  - "CAP-006"
tags:
  - "source"
  - "conversation"
  - "mcp-geo"
  - "llm-wiki"
  - "client-interop"
  - "statistics"
  - "nomis"
---

# Claude Opus Leamington/Warwick Stats-Routing Failures

This source note summarizes the second selected Stage 2
client-interoperability capture. It uses existing public repository example
documents, not raw Codex JSONL paths.

- Conversation source ID: `CONV-003`
- Date range: `2026-02-07` to `2026-02-10`
- Start-to-finish reader: [conversation reader](../readers/conv-003-claude-leamington-warwick-stats-routing.md)
- User-visible exchange groups: 6
- Raw Codex transcript: not exported into this repository
- Evidence basis: [Claude Opus failed conversation 1](../../../docs/Claude_opus_4-6_failed_convo_1.md), [Claude Opus failed conversation 2](../../../docs/claude_opus_4-6_failed_convo_2.md), and the selected capture register

## Public Exchange Notes

- [EX-0016: Broad Leamington/Warwick Comparison Overloads Search](../exchanges/0016-20260207-leamington-warwick-broad-comparison-overload.md)
- [EX-0017: Stats Routing Creates a Ward-Level Comparison Contract](../exchanges/0017-20260210-stats-routing-ward-comparison-contract.md)
- [EX-0018: Dashboard Render Fallback to Direct Queries](../exchanges/0018-20260210-dashboard-render-fallback-to-direct-queries.md)
- [EX-0019: NOMIS Dataset Discovery Drift](../exchanges/0019-20260210-nomis-dataset-discovery-drift.md)
- [EX-0020: Census Query Parameter Failures](../exchanges/0020-20260210-census-query-parameter-failures.md)
- [EX-0021: Comparison Output Contract Needed](../exchanges/0021-20260210-comparison-output-contract-needed.md)

## Durable Findings

- A broad "compare life" request needed decomposition into boundary selection,
  metric selection, data-provider routing, query construction, and a final
  comparison contract.
- Current ward lookup was the strongest part of the flow. The useful working
  set was five Leamington wards and four Warwick wards, while generic or
  legacy ward matches needed to be excluded.
- Stats routing correctly recommended NOMIS and ward-level comparison for
  labour/census-style indicators, but the handoff still left too much query
  construction to the client.
- The statistics dashboard did not render in the example context. The client
  then fell back to direct NOMIS queries, which is a reasonable fallback only
  if the tool contract exposes complete query templates.
- Dataset discovery eventually identified relevant Census 2021 topic-summary
  datasets, including population, deprivation, health, tenure, economic
  activity, and qualifications. Broad searches such as "census 2021" or
  "population census 2021" were not sufficient.
- Direct NOMIS queries repeatedly failed with incomplete-query and upstream
  response errors. The reusable design lesson is that MCP-Geo should provide
  stricter parameter guidance, codelist support, or curated query templates
  for common Census 2021 comparison tasks.
