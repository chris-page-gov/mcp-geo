# MCP Geo Repository Guidelines

This document defines how agents (and humans) should work within the `mcp-geo` repository. It replaces a template from a different project—details below are specific to this codebase.

## Current Tech & Scope

- FastAPI-based Model Context Protocol (MCP) server providing geospatial / Ordnance Survey tooling.
- Python >=3.11 runtime (bump `requires-python` in `pyproject.toml` if upgraded).
- Endpoints: `/healthz`, `/tools/list`, `/tools/call`, `/tools/describe`, `/resources/list`, playground transcript endpoints.
- Epic A (core) and Epic B (OS tools) implemented with real handlers (OS calls if `OS_API_KEY` set; graceful 501 otherwise).

## Repository Layout

- `server/`: FastAPI app (`main.py`), config (`config.py`), MCP routers (`mcp/`).
- `server/mcp/tools.py`: Tool metadata/dispatch + explicit dynamic imports guaranteeing registration.
- `server/mcp/resources.py`: Resource listing (placeholder; expand with metadata + retrieval endpoints).
- `server/mcp/playground.py`: Transcript stub (synchronous; should become async and validated).
- `resources/`: Static data (currently minimal / placeholder folders expected).
- `tools/`: Concrete tool modules (os_places, os_places_extra, os_names, os_features, os_linked_ids, os_maps, os_vector_tiles, etc.).
- `playground/`: Placeholder for a web or CLI UI (not yet populated with frontend assets here).
- `tests/`: Pytest suite (currently missing critical coverage—see gaps section).
- `.devcontainer/`: Development container configuration.
- `CHANGELOG.md`: Unreleased section tracks epics.
- `pyproject.toml`: Project metadata & dependencies.
- `.env.example`: Example environment; currently only OS_API_KEY stub.

## Build & Run

- Devcontainer: open in VS Code, auto installs deps via `postCreateCommand`.
- Local manual run:

  ```bash
  pip install -e .[test]
  uvicorn server.main:app --reload
  ```

- Alternate entrypoint: `python run.py` (ensure it points to uvicorn).

## Coding Standards

- 4-space indent, LF, max line length 100.
- Universal type hints; `mypy` clean (no unused ignores) & Ruff enforced.
- Error model: `{ "isError": true, "code": str, "message": str, "correlationId"?: str }`.
- `nextPageToken` for pagination (never snake case).
- Logging via `loguru`; sensitive tokens masked (`server/security.py`).
- Dynamic tool registration: Explicit import loop in `server/mcp/tools.py` ensures consistent registry population across agent/test environments.

## Tools & Resources Conventions

- Namespace: `os_<domain>.<verb>` — allowed verbs: `search|get|query|find|nearest|within|render|descriptor`.
- Each tool supplies: name, version, description, `input_schema`, `output_schema`, handler.
- Discovery endpoints: `/tools/list` (names + paging), `/tools/describe` (full metadata).
- Keep handlers small; shared concerns (HTTP, retries) live in `os_common.py`.

## Testing Strategy

- Pytest with coverage gate (≥90%). Current suite covers success + validation + upstream error paths.
- When adding a tool: include validation tests, success path (mocked upstream), and at least one upstream error normalization test.
- Prefer monkeypatching minimal surface (e.g., `client.get_json` / `requests.get`) to reach normalization logic.
- Future: introduce golden fixtures for canonical postcodes & feature queries.

## Commits & PRs

- Use Conventional Commits: `feat(server): implement os_places.by_postcode parsing`.
- Each PR must: update `CHANGELOG.md`, add/adjust docs, include/adjust tests.
- Avoid bundling unrelated refactors with feature delivery.

## Release Process (Future)

- When stable: introduce GitHub Actions workflow for tagging & publishing (not present yet—add `.github/workflows/release.yml`).
- Version bump: update `pyproject.toml`; optionally add `__version__` in `server/__init__.py`.

## Security & Configuration

- Never log full secrets (centralise redaction helper: e.g., `server/security.py`).
- Validate all external inputs (postcode regex OK; add length and normalization utilities module).
- Timeouts on all outbound HTTP calls (already set for OS API: `timeout=5`). Add retry strategy (e.g., `tenacity`) for transient errors.

## Observability Enhancements (Backlog)

- Add structured JSON logging sink.
- Add request/response size metrics and tool latency histograms (Prometheus or OTLP exporter).
- Correlation ID should also propagate to outbound requests via header injection.

## Agent Execution Rules

- Do not introduce new dependencies without updating `pyproject.toml` and rationale in PR.
- Prefer incremental refactors (extract functions before rewriting blocks).
- If adding a tool: include JSON schema for request/response in docstring.

## Gaps & Immediate Action Items

1. CI pipeline not yet committed (lint, type, test, coverage badge, build image).
2. Observability: metrics (latency histograms, request counts) & structured JSON log sink pending.
3. Retry/backoff sophistication (currently simple exponential) – consider `tenacity` or custom jitter.
4. Resource catalog still minimal (code lists / boundaries not populated).
5. Pagination not implemented for tools returning large collections (future: token-based for OS features).
6. Map render tool currently descriptor/stub – add real static map generation or proxy.
7. Security hardening: rate limiting & circuit breaker not yet implemented.
8. Add `/resources/get` endpoint for retrieval + caching headers.
9. Add admin/ONS tools (future epics) with consistent schemas.

Resolved (removed from gaps): baseline tests, dynamic tool registration reliability, redaction helper, README duplication, type + lint config, modular tool structure.

## Roadmap (Suggested)

- Phase 1 (DONE): Core server + dynamic tool dispatch + baseline tests.
- Phase 2 (DONE): Implement Epic B OS tools with schemas & describe endpoint.
- Phase 3 (NEXT): CI pipeline, metrics, richer retries, resource population.
- Phase 4: ONS data & admin geography tools, golden scenario tests.
- Phase 5: Performance & scaling (caching, rate limiting, async upstream calls).

---

Last updated: 2025-09-16
