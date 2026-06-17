# MCP Geo Repository Guidelines

This file is the always-read agent guide for `mcp-geo`. Keep it compact.
Detailed operational history lives under `docs/agent_context/`.

## Current Tech & Scope

- FastAPI-based MCP server for UK geospatial, Ordnance Survey, ONS/NOMIS,
  property, mapping, and LandIS tooling.
- Python >=3.11 runtime.
- Main entrypoints: `server/main.py` for HTTP and `server/stdio_adapter.py` for
  JSON-RPC STDIO.
- Tool modules live in `tools/`; static resources live in `resources/`; tests
  live in `tests/`.

## Required Startup Context

- Read `CONTEXT.md` at the start of each session.
- Use `PROGRESS.MD` for active workstream status only.
- Use `docs/agent_context/` for historical context and operational playbooks:
  - `README.md`
  - `geography-extension-contract.md`
  - `agent-operations.md`
  - `historical-workstreams.md`
- Treat `docs/vendor/openai/` as deprecated fallback. Prefer current OpenAI
  developer docs via the shared documentation MCP server when available.

## Build & Run

Local manual run:

```bash
pip install -e .[test]
uvicorn server.main:app --reload
```

Preferred local validation wrappers:

```bash
./scripts/ruff-local
./scripts/mypy-local
./scripts/pytest-local -q
./scripts/validate-owasp-mcp-local
```

The wrappers prefer the running devcontainer, then `.venv`, then `uv run`.

Timeout guidance:

- Full pytest: 15 minutes.
- Containerized map trials: 5 minutes.
- Full Playwright suites: 5 minutes.
- Unknown long command: start at 5 minutes and extend from evidence.

## Coding Standards

- 4-space indent, LF, max line length 100.
- Use type hints on maintained runtime surfaces.
- Error model: `{ "isError": true, "code": str, "message": str, "correlationId"?: str }`.
- Use `nextPageToken` for pagination.
- Logging via `loguru`; mask secrets through shared redaction helpers.
- Dynamic tool registration depends on explicit imports in `server/mcp/tools.py`.
- OS-backed tools return `501` with `{code:"NO_API_KEY"}` when `OS_API_KEY` is unset.
- Do not add dependencies without updating `pyproject.toml` and documenting why.

## Tool Contracts

- Namespace tools as `os_<domain>.<verb>` where verbs are
  `search|get|query|find|nearest|within|render|descriptor`.
- Each tool must supply metadata, input schema, output schema, and a small
  handler.
- Shared concerns such as HTTP, retries, config, auth, and normalization should
  live in shared helpers rather than per-tool copies.
- If adding or renaming a tool, changing a description, or changing a schema:
  update `security/owasp_mcp/tool_risk_inventory.json`, regenerate signed
  manifest artifacts, and run `./scripts/validate-owasp-mcp-local`.

## Geography-Level Changes

Geography levels must be treated as cross-surface contracts. Start in
`server/geography_levels.py`; do not add one-off alias lists in individual tools.

For parish/PARNCP, public API level is `PARISH`; raw fields remain
`PARNCP25CD`, `PARNCP25NM`, and `PARNCP25NW`. For House of Commons Library MSOA
names, keep official ONS/RGC names in `name` / `currentName` and expose Library
labels through `displayName` fields with provenance.

Before finishing any geography-level or display-name change, review and test:

- ONS cache schema, refresh ingest, semantic extraction, and migrations
- admin lookup cache/live/geometry paths
- route-query, stats routing, and workflow resources
- HTTP and STDIO schemas/elicitation
- MCP-Apps widget config and embedded HTML defaults
- export selectors and CSV audit columns
- docs, examples, changelog fragments, and OWASP manifest artifacts

See `docs/agent_context/geography-extension-contract.md` for the full checklist.

## Testing Strategy

- Pytest has a coverage gate; use targeted `--no-cov` slices during development
  only when the full gate is not needed yet.
- New tools need validation tests, a mocked success path, and upstream error
  normalization tests.
- Bug fixes and PR-comment fixes require a same-pattern sweep. Check shared
  helpers, HTTP/STDIO variants, cache/live variants, file-format variants, and
  widget fallbacks where relevant.
- Add regression coverage for the reported case plus at least one confirmed
  sibling path. If the site is unique, say so in the task summary or PR comment.
- Prefer monkeypatching minimal surfaces such as `client.get_json` or
  `requests.get`.

## Commits & PRs

- Use Conventional Commits, for example
  `feat(server): implement os_places.by_postcode parsing`.
- Keep unrelated refactors out of feature/fix commits.
- Each PR needs tests, docs, and release-note coverage. For parallel work, use a
  `changelog.d/` fragment instead of editing `CHANGELOG.md` directly.
- For high-churn files (`CHANGELOG.md`, `PROGRESS.MD`, `CONTEXT.md`), prefer
  branch-local fragments/plans unless doing release or integration work.
- When creating PRs/comments with markdown, prefer body files rather than
  embedding backticks directly in shell commands.

## Runtime & Security

- When MCP HTTP auth is enabled, only `GET /health` is public. Raw `/tools/*`,
  `/resources/*`, `/playground/*`, and `/metrics` share the bearer-auth boundary
  with `/mcp`.
- Never log full secrets. Include `MCP_HTTP_AUTH_TOKEN` and
  `MCP_HTTP_JWT_HS256_SECRET` in redaction-sensitive reviews.
- Validate external inputs and keep outbound HTTP timeouts.
- Metrics are served at `/metrics` when enabled.

## Client Interop

Keep STDIO and MCP-Apps compatibility in mind:

- Support JSON-RPC `tools/call` with `params.name` and `params.arguments`.
- Accept sanitized and original tool names.
- `resources/read` should accept both `uri` and `name`.
- Do not respond to JSON-RPC notifications without an `id`.
- Widget payload extraction must tolerate `structuredContent`, content blocks,
  and `result.data`.

See `docs/agent_context/agent-operations.md` for detailed client and review
workflow learnings.

## Map UX

- For user-facing maps needing street/building detail, default to MapLibre with
  an OS vector basemap such as `OS_VTS_3857_Light.json`.
- Keep analytical overlays separate from the basemap and label-safe.
- Validate maps in a real browser at desktop width with zoom, pan, and label
  readability checks before closing the task.

## Releases

Publishing a version means:

- update versions in `pyproject.toml` and `server/__init__.py`
- move `CHANGELOG.md` Unreleased content into a dated release
- add `RELEASE_NOTES/<version>.md`
- run tests and confirm the coverage gate
- tag `v<version>` at the release commit
- optionally build the Docker image
