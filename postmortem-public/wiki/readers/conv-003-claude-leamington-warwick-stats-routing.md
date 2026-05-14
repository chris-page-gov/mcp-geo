---
source_id: "CONV-003"
title: "Claude Opus Leamington/Warwick Stats-Routing Failures Reader"
reader_type: "curated_start_to_finish_conversation"
publication_status: "public-safe-curated-derivative"
exchange_count: 6
tags:
  - "reader"
  - "conversation"
  - "mcp-geo"
  - "llm-wiki"
  - "client-interop"
  - "statistics"
---

# CONV-003: Claude Opus Leamington/Warwick Stats-Routing Failures

This public reader inlines the curated prompt-response exchanges for the
Leamington/Warwick statistics-routing capture. It shows how a plausible
provider and ward-selection path still failed because the query and dashboard
contracts were not executable enough for the client.

## Navigation

- Index: [MCP-Geo Public Conversation Wiki](../index.md)
- Conversation source note: [CONV-003](../sources/conv-003-claude-leamington-warwick-stats-routing.md)
- Raw Codex transcript: not exported into this repository.
- Public example sources: [failed statistics conversation 1](../../../docs/Claude_opus_4-6_failed_convo_1.md), [failed statistics conversation 2](../../../docs/claude_opus_4-6_failed_convo_2.md)

## Exchange Map

| Exchange | Prompt Theme | Standalone Note |
|---|---|---|
| [EX-0016](#ex-0016) | Broad Leamington/Warwick Comparison Overloads Search | [note](../exchanges/0016-20260207-leamington-warwick-broad-comparison-overload.md) |
| [EX-0017](#ex-0017) | Stats Routing Creates a Ward-Level Comparison Contract | [note](../exchanges/0017-20260210-stats-routing-ward-comparison-contract.md) |
| [EX-0018](#ex-0018) | Dashboard Render Fallback to Direct Queries | [note](../exchanges/0018-20260210-dashboard-render-fallback-to-direct-queries.md) |
| [EX-0019](#ex-0019) | NOMIS Dataset Discovery Drift | [note](../exchanges/0019-20260210-nomis-dataset-discovery-drift.md) |
| [EX-0020](#ex-0020) | Census Query Parameter Failures | [note](../exchanges/0020-20260210-census-query-parameter-failures.md) |
| [EX-0021](#ex-0021) | Comparison Output Contract Needed | [note](../exchanges/0021-20260210-comparison-output-contract-needed.md) |

## Conversation

<a id="ex-0016"></a>

### EX-0016: Broad Leamington/Warwick Comparison Overloads Search

- User timestamp precision: date only (`2026-02-07`)
- Standalone note: [EX-0016](../exchanges/0016-20260207-leamington-warwick-broad-comparison-overload.md)

#### User Prompt

```text
use mcp-geo to compare life in Leamington and Warwick
```

#### Curated Outcome

```text
The client began with broad OS name and administrative searches. It found the towns and same-district context, but produced a wide result stream before narrowing to ward-level geography.
```

<a id="ex-0017"></a>

### EX-0017: Stats Routing Creates a Ward-Level Comparison Contract

- User timestamp precision: date only (`2026-02-10`)
- Standalone note: [EX-0017](../exchanges/0017-20260210-stats-routing-ward-comparison-contract.md)

#### User Prompt

```text
Use stats routing to allow me to compare life in Leamington Spa and Warwick.
```

#### Curated Outcome

```text
Stats routing selected NOMIS for labour/census indicators and recommended ward-level comparisons, admin lookup, a statistics dashboard, and direct NOMIS queries after area selection.
```

<a id="ex-0018"></a>

### EX-0018: Dashboard Render Fallback to Direct Queries

- User timestamp precision: date only (`2026-02-10`)
- Standalone note: [EX-0018](../exchanges/0018-20260210-dashboard-render-fallback-to-direct-queries.md)

#### User Prompt

```text
Continue the statistics-routing comparison for Leamington Spa and Warwick.
```

#### Curated Outcome

```text
The client attempted the dashboard path after identifying wards, but the widget did not render in the conversation context. It then pivoted to direct NOMIS dataset discovery and query construction.
```

<a id="ex-0019"></a>

### EX-0019: NOMIS Dataset Discovery Drift

- User timestamp precision: date only (`2026-02-10`)
- Standalone note: [EX-0019](../exchanges/0019-20260210-nomis-dataset-discovery-drift.md)

#### User Prompt

```text
Continue the statistics-routing comparison for Leamington Spa and Warwick.
```

#### Curated Outcome

```text
Broad dataset searches failed or returned misleading historical/workplace datasets. More specific Census 2021 topic-summary searches eventually found useful TS datasets for population, health, tenure, economic activity, and qualifications.
```

<a id="ex-0020"></a>

### EX-0020: Census Query Parameter Failures

- User timestamp precision: date only (`2026-02-10`)
- Standalone note: [EX-0020](../exchanges/0020-20260210-census-query-parameter-failures.md)

#### User Prompt

```text
Continue the statistics-routing comparison for Leamington Spa and Warwick.
```

#### Curated Outcome

```text
After selecting wards and datasets, direct NOMIS queries repeatedly failed with incomplete-query, invalid-response, and SDMX conversion errors. The client did not reach a reliable comparison table.
```

<a id="ex-0021"></a>

### EX-0021: Comparison Output Contract Needed

- User timestamp precision: date only (`2026-02-10`)
- Standalone note: [EX-0021](../exchanges/0021-20260210-comparison-output-contract-needed.md)

#### User Prompt

```text
Continue the statistics-routing comparison for Leamington Spa and Warwick.
```

#### Curated Outcome

```text
The example shows that a successful "compare life" workflow needs a bounded output contract: selected geography, selected indicators, executable query templates, and a tabular comparison fallback if dashboard rendering is unavailable.
```

## Summary

CONV-003 preserves the main statistics-routing lesson from the
Leamington/Warwick examples: choosing the right provider is only the first
step. MCP-Geo needs to turn route recommendations into executable comparison
plans, including current-area disambiguation, query parameter templates,
dashboard fallback metadata, and compact result tables.
