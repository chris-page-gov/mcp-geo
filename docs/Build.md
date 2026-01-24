# Build and Run

This guide describes how to install, run, and validate the current MCP Geo
server in this repository. It replaces the original planning backlog with
repo-aligned instructions.

## Requirements

- Python 3.11+
- Optional: Docker (for container runs)
- Optional: OS API key for live Ordnance Survey tools

## Install

```bash
pip install -e .[test]
```

## Run (local dev)

```bash
uvicorn server.main:app --reload
```

Alternate entrypoint:

```bash
python run.py
```

## Core endpoints

- `GET /health`
- `POST /tools/list`
- `POST /tools/describe`
- `POST /tools/search`
- `POST /tools/call`
- `GET /resources/list`
- `GET /resources/describe`
- `GET /resources/read`
- `POST /mcp` (JSON-RPC)
- `GET /metrics` (if enabled)

## Tests

```bash
pytest -q
```

## Environment variables

- `OS_API_KEY`: enables live Ordnance Survey tools (Places, Names, NGD Features).
  If unset, OS-backed tools return `501` with `{ "code": "NO_API_KEY" }`.
- `ONS_LIVE_ENABLED`: enables live ONS API access for `ons_data.*`. If unset or
  false, the server uses bundled sample data.
- `UI_EVENT_LOG_PATH`: path for MCP-Apps UI event log output
  (default: `logs/ui-events.jsonl`).
- `DEBUG_ERRORS`: include tracebacks in error responses (development only).
- `RATE_LIMIT_PER_MIN`: per-minute in-memory rate limit (default 120).
- `RATE_LIMIT_BYPASS`: set to `true` to disable rate limiting (default true).
- `METRICS_ENABLED`: enable `/metrics` (default true).

You can copy `.env.example` to `.env` for local use.

## STDIO adapter (MCP clients)

Installed entrypoint:

```bash
mcp-geo-stdio
```

Repo-local wrapper:

```bash
./scripts/os-mcp
```

The `mcp.json` file in the repo includes a ready-to-copy client configuration
for STDIO connections.

## Docker

Build the image:

```bash
docker build -t mcp-geo-server .
```

Run HTTP transport:

```bash
docker run --rm -p 8000:8000 \
  -e OS_API_KEY=your-api-key-here \
  -e ONS_LIVE_ENABLED=true \
  mcp-geo-server \
  uvicorn server.main:app --host 0.0.0.0 --port 8000
```

Run STDIO (for MCP desktop clients):

```bash
docker run --rm -i \
  -e OS_API_KEY=your-api-key-here \
  -e ONS_LIVE_ENABLED=true \
  mcp-geo-server
```

## Smoke check

After starting the server, confirm basic health and discovery:

```bash
curl -sS http://127.0.0.1:8000/health
curl -sS http://127.0.0.1:8000/tools/list
```

For a deeper walkthrough (tool search, MCP-Apps, and client setup), see
`docs/tutorial.md`.
3. Contract test snapshot updated.

---

## Bootstrapping Task 0 (for a Builder Agent)

> **Objective:** Generate a production‑ready MCP server scaffold with TypeScript (or Python) including handshake, tool router, resource registry, config, logging, tests, Docker, and a minimal playground UI. Create stubs for tools listed in Epics B–D and resources in C. Include CI workflow and `/docs` with a tool catalog and example conversations. Then iterate through the backlog, turning stubs into full implementations, keeping I/O **strictly typed** and **structured**.

---

## Suggested repo layout

```txt
/server
  /mcp           ## handshake, tool registry, resource registry
  /tools         ## os_places, os_linked_ids, os_features, os_names, os_maps, admin_lookup, ons_data, ons_search, ons_codes
  /resources     ## code lists, boundaries, samples (versioned)
/playground      ## tiny chat UI + call transcript
/tests           ## unit, contract, golden, hammer tests
/infra           ## Dockerfile, compose, k8s manifests (optional)
/docs            ## quickstart, tool catalog, examples
.env.example
```

---

## Definition of Done (project)

* All tools in Epics B–D implemented with typed inputs/outputs, pagination, enrichment (where applicable), and uniform error model.
* Static resources (code lists, boundaries) are versioned, documented, enriched with caching headers and provenance timestamps, and discoverable via `resources/list`.
* Golden scenarios in EPIC E pass, producing both textual answers and (where specified) map images.
* Secrets redaction, rate limiting, retry/backoff, and basic dashboards exist.
* CI green; a newcomer can run the stack locally in <10 minutes, and deploy via Docker.

---

### When to prefer a “builder agent” over plain tickets

* You want the skeleton, CI, docs, and stubs generated **immediately** so you can iterate inside a working shell.
* You’re happy to let the agent make opinionated choices (TypeScript vs Python, test framework, map renderer) that you’ll refine later.
* You expect lots of repetitive wrapper code (tool stubs, schema definitions, error adapters) that an agent can mass‑generate consistently.

If you’d like, I can also produce:

* A **Codex system prompt** that pins coding conventions and enforces strict I/O schemas for all tools.
* The **first three PRs** (A0, B1, D1) in code so you can start running the server straight away.
