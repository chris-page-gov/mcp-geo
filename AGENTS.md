# MCP Geo Repository Guidelines

This document defines how agents (and humans) should work within the `mcp-geo` repository. It replaces a template from a different project—details below are specific to this codebase.

## Current Tech & Scope

- FastAPI-based Model Context Protocol (MCP) server providing geospatial/Ordnance Survey (OS) tooling.
- Python >=3.11 runtime (update `pyproject.toml` requires-python if bumped).
- Endpoints implemented so far: `/healthz`, `/tools/list`, `/tools/call`, `/resources/list`, playground transcript endpoints.
- Epic B OS tools scaffolded (all 501 except `os_places.by_postcode`).

## Repository Layout

- `server/`: FastAPI app (`main.py`), config (`config.py`), MCP routers (`mcp/`).
- `server/mcp/tools.py`: Tool registry + dispatcher (needs refactor to per-tool modules when implementations grow).
- `server/mcp/resources.py`: Resource listing (placeholder; expand with metadata + retrieval endpoints).
- `server/mcp/playground.py`: Transcript stub (synchronous; should become async and validated).
- `resources/`: Static data (currently minimal / placeholder folders expected).
- `tools/`: Future concrete tool implementation modules (currently unused; align with `server/mcp/tools.py`).
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

- 4-space indent, LF endings, max line length 100 (enforce via editorconfig/formatter—NOTE: no formatter config committed yet).
- Use type hints everywhere; introduce `mypy` (not currently configured) for stricter checking.
- Consistent error model: `{ "isError": bool, "code": str, "message": str, ... }`. Add `correlationId` where available; do NOT expose stack traces in production responses—current implementation leaks `traceback` (needs gating behind an env flag like `DEBUG_ERRORS`).
- Pagination fields: `nextPageToken` not `next_page` (already consistent).
- Logging: uses `loguru`; ensure secrets redaction is centralised (currently only OS_API_KEY redacted ad‑hoc in one handler).

## Tools & Resources Conventions

- Tool namespace: `os_<domain>.<action>` (keep consistent; document allowed verbs: `search|get|query|find|nearest|within|render|descriptor`).
- Each tool should provide: name, version, description, input schema, output schema (currently missing—add a `/tools/describe` or embed metadata in `/tools/list`).
- Move one-off logic in `call_tool` into per-tool functions under `tools/` or `server/mcp/tools/` sub-package.

## Testing Strategy (To Be Implemented)

- Add tests: `tests/test_healthz.py`, `tests/test_tools_list.py`, `tests/test_postcode_validations.py`, `tests/test_error_model.py`.
- Use `httpx.AsyncClient` with FastAPI lifespan context.
- Mock external OS API with `responses` or `pytest_httpx` fixture.
- Add golden test fixtures for known postcode payloads.

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

1. Missing test suite (only implied tests; create baseline).
2. Error handler exposes traceback—add config flag gating.
3. Tool architecture monolithic—refactor to modular soon.
4. No lint/type tooling configured (add ruff + mypy config sections in `pyproject.toml`).
5. Duplicate/verbose sections in `README.md` (project structure repeated).
6. `CHANGELOG.md` repeats Completed Epic sections under both bullet lists and Fixed; normalise categories.
7. No CI workflow defined (add lint/test pipeline).
8. Security: OS API key redaction only; create general `redact()` helper.
9. Playground transcript endpoint synchronous & unvalidated (should parse body, not call `request.json()` incorrectly—it is async in FastAPI; current code likely broken).
10. `tools` vs `server/mcp/tools.py` duplication of concept; unify.

## Roadmap (Suggested)

- Phase 1: Tests + refactor tool dispatch.
- Phase 2: Add schemas + describe endpoint.
- Phase 3: Observability + retries + CI pipeline.
- Phase 4: Implement Epic B tool functionality incrementally with contract tests.

---

Last updated: (keep current when editing)
