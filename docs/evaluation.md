# MCP Geo Evaluation

This document describes the evaluation framework for the MCP Geo server. The
framework is built around a question suite, a scoring rubric, and a harness
that exercises tools through HTTP endpoints.

## Overview

The evaluation framework includes:

1. Question suite (41 questions across basic, intermediate, advanced, edge, and ambiguous)
2. Scoring rubric (5 dimensions, 100 points total)
3. Test harness (runs the suite and emits JSON + audit logs)
4. Audit logs (LLM-readable traces per question)

The harness calls `os_mcp.route_query` first (unless disabled) and then executes
question-specific tool calls to validate outputs.

## Requirements

- `OS_API_KEY` is required for OS-backed questions (Places, Names, NGD Features, Linked IDs).
  Use `--include-os-api` to include these questions.
- `ONS_LIVE_ENABLED=true` is required only for live ONS dataset checks. The bundled
  live data covers default `ons_data.*` questions (requires `ONS_LIVE_ENABLED=true`).
- Live API capture requires a PostgreSQL + PostGIS database and `MCP_GEO_LIVE_DB_DSN`.

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

## Live API capture (PostgreSQL + PostGIS)

The live evaluation test stores upstream API responses in PostgreSQL (jsonb) so
changes can be audited over time. The test is skipped unless explicitly enabled.

## Live Run Reports

- ONS catalog live validation run report (v2): `docs/reports/ons_catalog_live_run_2026-02-07_v2.md`
- Previous run report (v1): `docs/reports/ons_catalog_live_run_2026-02-07.md`
- Reports index: `docs/reports/README.md`

If you are using the devcontainer, a PostGIS service is started automatically
and the DSN defaults to `postgresql://mcp_geo:mcp_geo@postgis:5432/mcp_geo`.

Environment variables:
- `RUN_LIVE_API_TESTS=1`
- `MCP_GEO_LIVE_DB_DSN=postgresql://mcp_geo:mcp_geo@localhost:5432/mcp_geo`
- `OS_API_KEY=...` (required for OS-backed calls)

Optional PostGIS container (uses repo-local `data/` for storage):

```bash
mkdir -p data/postgres
docker run --rm -p 5432:5432 \\
  -e POSTGRES_DB=mcp_geo \\
  -e POSTGRES_USER=mcp_geo \\
  -e POSTGRES_PASSWORD=mcp_geo \\
  -v "$PWD/data/postgres:/var/lib/postgresql/data" \\
  postgis/postgis:16-3.4
```

Run the live capture test:

```bash
pytest -q tests/test_evaluation_harness_live_api.py
```

Live outputs:
- Results JSON: `data/evaluation_results_live.json`
- Audit summary: `data/evaluation_results_live.audit.txt`
- Per-question audit logs: `data/audit/`

## Question suite

Counts by difficulty:
- Basic: 14
- Intermediate: 12
- Advanced: 8
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
