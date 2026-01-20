# MCP Geo Evaluation

This document describes the evaluation framework for the MCP Geo server. The
framework is built around a question suite, a scoring rubric, and a harness
that exercises tools through HTTP endpoints.

## Overview

The evaluation framework includes:

1. Question suite (33 questions across basic, intermediate, advanced, edge, and ambiguous)
2. Scoring rubric (5 dimensions, 100 points total)
3. Test harness (runs the suite and emits JSON + audit logs)
4. Audit logs (LLM-readable traces per question)

The harness calls `os_mcp.route_query` first (unless disabled) and then executes
question-specific tool calls to validate outputs.

## Requirements

- `OS_API_KEY` is required for OS-backed questions (Places, Names, NGD Features, Linked IDs).
  Use `--include-os-api` to include these questions.
- `ONS_LIVE_ENABLED=true` is required only for live ONS dataset checks. The bundled
  sample data covers default `ons_data.*` questions.

## Running evaluations

Basic-only run:

```bash
python -m tests.evaluation.harness --difficulty=basic
```

Include OS API questions:

```bash
python -m tests.evaluation.harness --include-os-api
```

Specific intent:

```bash
python -m tests.evaluation.harness --intent=statistics
```

Specific questions:

```bash
python -m tests.evaluation.harness --questions=B001,I003,A004
```

Skip routing (useful for isolating tool outputs):

```bash
python -m tests.evaluation.harness --no-routing
```

Default outputs:
- Results JSON: `tests/evaluation/evaluation_results.json`
- Audit summary: `tests/evaluation/evaluation_results.audit.txt`
- Per-question audit logs: `tests/evaluation/logs/audit/`

## Question suite

Counts by difficulty:
- Basic: 10
- Intermediate: 10
- Advanced: 6
- Edge: 4
- Ambiguous: 3

Intent coverage includes: address lookup, place lookup, statistics, comparisons,
feature search, boundary fetch, interactive selection, routing, dataset discovery,
map rendering, vector tiles, and linked IDs.

For the full question definitions and tool call payloads see:
- `tests/evaluation/questions.py`

## Scoring rubric

The rubric scores five dimensions:

1. Intent recognition (0-25)
2. Tool selection (0-25)
3. Efficiency (0-20)
4. Response quality (0-20)
5. Error handling (0-10)

Detailed criteria live in:
- `tests/evaluation/rubric.py`

## Audit logs

Each question produces an audit log with:

- QUERY
- ROUTING DECISION
- TOOL CALLS
- RESPONSE
- METRICS

Example excerpt:

```
AUDIT LOG: 12ab34cd
Timestamp: 2025-01-20T15:45:12

## 1. QUERY
User Question: "Find Westminster"

## 2. ROUTING DECISION
Intent Detected: place_lookup
Confidence: 0.92
Recommended Tool: admin_lookup.find_by_name
Workflow Steps: ['admin_lookup.find_by_name']

## 3. TOOL CALLS
### Tool Call 1: admin_lookup.find_by_name
...
```
