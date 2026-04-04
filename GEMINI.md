# GEMINI.md - MCP Geo Server Context

This document provides essential context and instructions for AI agents (like Gemini) interacting with the MCP Geo Server repository.

## Project Overview

**MCP Geo Server** is a research-oriented Model Context Protocol (MCP) server designed to provide AI assistants with access to UK geospatial data (via Ordnance Survey) and statistical data (via Office of National Statistics and NOMIS). It enables tools for address lookups, administrative boundary analysis, demographic statistics, and map rendering.

### Main Technologies
- **Language:** Python 3.11+
- **Framework:** FastAPI / Uvicorn (HTTP transport)
- **Protocol:** Model Context Protocol (MCP) - supports both STDIO and HTTP transports.
- **Data Sources:** Ordnance Survey (OS) APIs, ONS Open Geography, NOMIS.
- **Database:** PostGIS / pgRouting (for boundary and routing features).
- **Frontend:** Svelte + Vite (for the playground UI).
- **DevOps:** Docker, Devcontainers, GitHub Actions.

### Architecture
- `server/`: Core FastAPI application, routers, and MCP transport logic.
  - `server/mcp/`: MCP-specific implementations (tools, resources, http transport).
  - `server/stdio_adapter.py`: JSON-RPC 2.0 adapter for STDIO communication.
- `tools/`: Individual Python modules implementing specific domain tools (e.g., `os_places`, `ons_data`, `admin_lookup`).
- `playground/`: Svelte-based interactive UI for testing tools and exploring resources.
- `scripts/`: Utility scripts for running the server, trace proxies, and maintenance tasks.
- `docs/`: Extensive documentation covering specifications, research, and usage.

## Building and Running

### Prerequisites
- Python 3.11+
- `OS_API_KEY` (required for OS tools)
- Docker (optional, but recommended for PostGIS features)

### Development Setup
```bash
# Install dependencies with test and dev extras
pip install -e .[test,dev]

# Set up environment variables
cp .env.example .env
# Edit .env and add your OS_API_KEY
```

### Running the Server
- **HTTP Transport (Default):**
  ```bash
  python run.py
  # or
  uvicorn server.main:app --reload
  ```
  The server will be available at `http://localhost:8000`.

- **STDIO Transport (for Claude Desktop/IDE integration):**
  ```bash
  python3 scripts/os-mcp
  ```

- **Docker:**
  ```bash
  docker build -t mcp-geo-server .
  docker run -i --env-file .env mcp-geo-server
  ```

### Testing
```bash
# Run all tests
pytest

# Run tests with coverage (gate is 90%)
pytest --cov=server --cov=tools
```

## Development Conventions

- **Coding Style:** Adheres to PEP 8. Uses `ruff` for linting and formatting.
- **Type Safety:** Uses `mypy` for static type checking.
- **Tool Registration:** New tools must be defined in `tools/` and registered using the `tools.registry.register` function.
- **Commits:** Follows [Conventional Commits](https://www.conventionalcommits.org/) (e.g., `feat(tools): add new lookup tool`).
- **Error Model:** All tool errors should return a standard envelope: `{ "isError": true, "code": "CODE", "message": "..." }`.
- **Documentation:** Maintain `CHANGELOG.md` and update relevant files in `docs/` for any significant changes.

## Key Files
- `server/main.py`: FastAPI entry point.
- `server/stdio_adapter.py`: Core logic for STDIO MCP transport.
- `tools/registry.py`: Central registry for MCP tools.
- `mcp.json`: Configuration for various MCP client integrations.
- `pyproject.toml`: Python project metadata and dependencies.
