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
./scripts/pytest-local -q
```

Focused host-side lint/type checks:

```bash
./scripts/ruff-local check <paths...>
./scripts/mypy-local <paths...>
```

## Environment variables

- `OS_API_KEY`: required for Ordnance Survey tools (Places, Names, NGD Features).
  Missing or invalid keys return `NO_API_KEY`, `OS_API_KEY_INVALID`, or `OS_API_KEY_EXPIRED`.
- `ONS_LIVE_ENABLED`: enables live ONS API access for `ons_data.*` (default true).
- `UI_EVENT_LOG_PATH`: path for MCP-Apps UI event log output
  (default: `logs/ui-events.jsonl`).
- `PLAYGROUND_EVENT_LOG_PATH`: path for playground prompt/tool event logs
  (default: `logs/playground-events.jsonl`).
- `ONS_DATASET_CACHE_ENABLED`: cache full ONS dataset responses (default true).
- `ONS_DATASET_CACHE_DIR`: cache directory for full ONS dataset snapshots.
- `ONS_GEO_CACHE_DIR`: cache directory for ONS postcode/UPRN geography index.
- `OS_DATA_CACHE_DIR`: cache directory for OS response snapshots.
- `DEBUG_ERRORS`: include tracebacks in error responses (development only).
- `RATE_LIMIT_PER_MIN`: per-minute in-memory rate limit (default 207).
- `RATE_LIMIT_BYPASS`: set to `true` to disable rate limiting (default false; enable explicitly for tests/dev).
- `RATE_LIMIT_EXEMPT_PATH_PREFIXES`: comma-separated path prefixes excluded from rate limiting (default `/maps/vector/vts/tile,/maps/raster/osm,/maps/static/osm`).
- `METRICS_ENABLED`: enable `/metrics` (default true).
- `LOG_JSON`: loguru JSON output (default false).
- `CORS_ALLOWED_ORIGINS`: comma-separated origins for browser clients (default `http://localhost:5173,http://127.0.0.1:5173`).
- `MCP_TOOLS_DEFAULT_TOOLSET`: default toolset for `tools/list`/`tools/describe` when client passes no filters (for example `starter`).
- `MCP_TOOLS_DEFAULT_INCLUDE_TOOLSETS`: default CSV include filters when no per-request filters are provided.
- `MCP_TOOLS_DEFAULT_EXCLUDE_TOOLSETS`: default CSV exclude filters when no per-request filters are provided.

You can copy `.env.example` to `.env` for local use.

Storage recommendation:
- Keep PostGIS data and cache directories outside git worktrees.
- For containerized PostGIS, prefer Docker named volumes over bind mounts.
- For host-run caches/logs, use a host data root (for example
  `$HOME/Library/Application Support/mcp-geo/...`).
- For devcontainer overrides, copy `.devcontainer/.env.example` to
  `.devcontainer/.env` and set per-worktree volume names/port pins
  (`docker compose --env-file .devcontainer/.env ...`), or export the same env
  vars in your host shell before starting VS Code Dev Containers.

Cross-platform build notes:
- The repo now tracks line-ending policy in `.gitattributes` and `.editorconfig`
  so shell, Docker, YAML, JSON, Markdown, and Python files stay on LF across
  macOS and Windows checkouts.
- For TLS-inspected or proxied networks, copy `.devcontainer/.env.example` to
  `.devcontainer/.env`, set `HTTP_PROXY` / `HTTPS_PROXY` / `NO_PROXY` as
  needed, and rebuild the devcontainer.
- If your corporate proxy uses a private root CA, place one or more `.crt`
  files in `.devcontainer/certs/` before rebuilding. Both Dockerfiles now use
  the system CA bundle path (`/etc/ssl/certs/ca-certificates.crt`) so custom
  local roots are visible to `curl`, `pip`, and Python HTTP clients.
- `INSTALL_NGROK` defaults to `false` in the devcontainer build. Set
  `INSTALL_NGROK=true` only when you need the CLI inside the container.

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

## Playground UI (Svelte)

```bash
cd playground
npm install
npx playwright install --with-deps
npm run dev
```

Then open `http://localhost:5173` and connect to `http://localhost:8000/mcp`.

## Docker

Build the image:

```bash
docker build -t mcp-geo-server .
```

Or pull the pre-built multi-arch image published from GitHub Actions:

```bash
docker pull ghcr.io/chris-page-gov/mcp-geo:latest
```

Published tags:
- `latest` for the default branch image
- `<sha>` for a specific commit image
- `<version>` for release tags such as `0.6.0`

For proxied networks, pass the same build args explicitly if you are using the
top-level Dockerfile outside the devcontainer flow:

```bash
docker build \
  --build-arg HTTP_PROXY="$HTTP_PROXY" \
  --build-arg HTTPS_PROXY="$HTTPS_PROXY" \
  --build-arg NO_PROXY="$NO_PROXY" \
  -t mcp-geo-server .
```

Those proxy values are build-scoped only and are not baked into the final
image metadata. If the running container also needs proxy access, pass the same
variables explicitly to `docker run -e ...`.

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

For desktop clients that shell out to `docker run`, keep `--env-file` on an
absolute path because GUI apps do not start from the repo directory. Example:

```json
{
  "mcpServers": {
    "geo": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--env-file",
        "/absolute/path/to/mcp-geo/.env",
        "ghcr.io/chris-page-gov/mcp-geo:latest"
      ]
    }
  }
}
```

When to use STDIO:
- Use STDIO for desktop MCP clients that require it (Claude Desktop / Claude Code).
- Use HTTP `/mcp` for Inspector, ChatGPT connectors, and web clients.

To rebuild the STDIO image:

```bash
docker build -t mcp-geo-server .
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
