# MCP Geo Server

A production-ready Model Context Protocol (MCP) server for geospatial and ONS tools, built with FastAPI and Python. Implements the MCP handshake, tool/resource registry, error model, logging, and a minimal playground transcript panel.

## Features
- MCP protocol handshake and endpoints (`/tools/list`, `/tools/call`, `/resources/list`)
- Health check (`/healthz`)
- Uniform error model and pagination
- Structured logging, correlation IDs, and request tracing
- Tool call transcript endpoint for playground UI
- Docker and devcontainer support

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
	- `POST /tools/call` — call a tool (stub)
	- `GET /resources/list` — list available resources
	- `GET /playground/transcript` — tool call transcript

## Configuration
- Copy `.env.example` to `.env` and set your API keys and config.

## Project Structure
- `server/` — FastAPI app, config, endpoints
- `tools/` — Tool implementations (stubs)
- `resources/` — Static resources (code lists, boundaries)
- `playground/` — Playground UI (stub)
- `infra/` — Dockerfile, devcontainer, infra
- `tests/` — Unit and contract tests
- `docs/` — Documentation, backlog, examples

## Development
- Lint, type-check, and test with `pytest`
- See `CHANGELOG.md` for release notes

## License
MIT
