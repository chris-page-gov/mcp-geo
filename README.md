# MCP Geo Server

A production-ready Model Context Protocol (MCP) server for geospatial and ONS tools, built with FastAPI and Python. Implements the MCP handshake, tool/resource registry, error model, logging, and a minimal playground transcript panel.

## Features
- MCP protocol handshake and endpoints (`/tools/list`, `/tools/call`, `/resources/list`)
- Health check (`/healthz`)
- Uniform error model and pagination
- Structured logging, correlation IDs, and request tracing
- Tool call transcript endpoint for playground UI
- Docker and devcontainer support


## SSL & Certificate Reliability

The devcontainer and Dockerfile are configured to ensure CA certificates are present and Python requests use the correct certifi CA bundle. This guarantees reliable SSL connections for all Python and system tools.

## Quickstart

1. **Clone the repo and open in VS Code (with devcontainer support):**
	```sh
	git clone <repo-url>
	cd mcp-geo
	# Open in VS Code and reopen in container
	```
2. **Install dependencies (if not using devcontainer):**
	```sh
	pip install -e .[test]
	```
3. **Run the server:**
	```sh
	npm run dev
	# or
	python run.py
	```
4. **Test endpoints:**
	- `GET /healthz` — health check
	- `GET /tools/list` — list available tools
	- `POST /tools/call` — invoke a tool (Epic B tools perform live OS API calls when `OS_API_KEY` is set, otherwise return 501 with `NO_API_KEY`)
	- `GET /resources/list` — list available resources
	- `GET /playground/transcript` — tool call transcript

## Configuration
- Copy `.env.example` to `.env` and set your API keys and config.

- `server/` — FastAPI app, config, endpoints
- `tools/` — Tool implementations (stubs)
- `resources/` — Static resources (code lists, boundaries)
- `playground/` — Playground UI (stub)
- `.devcontainer/` — Dockerfile, devcontainer config
- `tests/` — Unit and contract tests
- `docs/` — Documentation, backlog, examples

## Available Ordnance Survey (Epic B) Tools

The following OS tools are scaffolded and available via `/tools/list` and `/tools/call`:

- os_places.search
- os_places.by_postcode
- os_places.by_uprn
- os_places.nearest
- os_places.within
- os_linked_ids.get
- os_features.query
- os_names.find
- os_names.nearest
- os_maps.render
- os_vector_tiles.descriptor

Epic B tools now implement real outbound calls (search, addresses, names, features, linked IDs, map metadata, vector tiles descriptor) with graceful degradation (501) if no API key or upstream issues.

## Error Codes

Tools and endpoints return a uniform error envelope:

```
{
	"isError": true,
	"code": "<ERROR_CODE>
	"message": "Human-readable description",
	...
}
```

Current error codes in use:

| Code | Meaning |
|------|---------|
| INVALID_INPUT | Request failed validation (missing/invalid fields) |
| UNKNOWN_TOOL | Tool name not registered |
| NO_API_KEY | Required upstream API key not configured |
| OS_API_ERROR | Non-200 response returned from OS API |
| UPSTREAM_TLS_ERROR | TLS / certificate verification failure calling upstream |
| UPSTREAM_CONNECT_ERROR | Connection or timeout reaching upstream |
| INTEGRATION_ERROR | Unexpected upstream/network error (catch-all) |

Pagination responses also include `nextPageToken` when additional pages exist.

## Project Structure
- `server/` — FastAPI app, config, endpoints
- `tools/` — Tool implementations (stubs)
- `resources/` — Static resources (code lists, boundaries)
- `playground/` — Playground UI (stub)
- `.devcontainer/` — Dockerfile, devcontainer config
- `tests/` — Unit and contract tests
- `docs/` — Documentation, backlog, examples
- `server/` — FastAPI app, config, endpoints
- `tools/` — Tool implementations (stubs)
- `resources/` — Static resources (code lists, boundaries)
- `playground/` — Playground UI (stub)
- `.devcontainer/` — Dockerfile, devcontainer config
- `tests/` — Unit and contract tests
- `docs/` — Documentation, backlog, examples

## Development
- Lint, type-check, and test with `pytest`
- See `CHANGELOG.md` for release notes

## License
MIT
