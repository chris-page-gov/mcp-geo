# MCP Geo Repository Guidelines

This document defines how agents (and humans) should work within the `mcp-geo` repository. It replaces a template from a different project—details below are specific to this codebase.

## Current Tech & Scope

- FastAPI-based Model Context Protocol (MCP) server providing geospatial / Ordnance Survey tooling.
- Python >=3.11 runtime (bump `requires-python` in `pyproject.toml` if upgraded).
- Endpoints: `/health`, `/tools/list`, `/tools/call`, `/tools/describe`, `/resources/list`, playground transcript endpoints.
- Epic A (core) and Epic B (OS tools) implemented with real handlers (OS calls if `OS_API_KEY` set; graceful 501 otherwise).

## Repository Layout

- `server/`: FastAPI app (`main.py`), config (`config.py`), MCP routers (`mcp/`).
- `server/mcp/tools.py`: Tool metadata/dispatch + explicit dynamic imports guaranteeing registration.
- `server/mcp/resources.py`: Resource listing + retrieval with filtering, paging, and ETag/`If-None-Match` support.
- `server/mcp/playground.py`: Transcript stub (synchronous; should become async and validated).
- `server/stdio_adapter.py`: JSON-RPC 2.0 STDIO adapter (relocated from legacy `scripts/os_mcp.py`; console script `mcp-geo-stdio` + wrapper `scripts/os-mcp` retained for compatibility).
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

- Run tests:

  ```bash
  pytest -q
  ```

- Alternate entrypoint: `python run.py` (ensure it points to uvicorn).

## Coding Standards

- 4-space indent, LF, max line length 100.
- Universal type hints; `mypy` clean (no unused ignores) & Ruff enforced.
- Error model: `{ "isError": true, "code": str, "message": str, "correlationId"?: str }`.
- `nextPageToken` for pagination (never snake case).
- Logging via `loguru`; sensitive tokens masked (`server/security.py`).
- Dynamic tool registration: Explicit import loop in `server/mcp/tools.py` ensures consistent registry population across agent/test environments.
- Rate limiting: middleware in `server/main.py` (defaults: `RATE_LIMIT_PER_MIN=120`, `RATE_LIMIT_BYPASS=True` in `server/config.py`; over-limit returns `429` + `{code:"RATE_LIMITED"}`).
- Metrics: `GET /metrics` enabled by default (`METRICS_ENABLED=True` in `server/config.py`).

## Tools & Resources Conventions

- Namespace: `os_<domain>.<verb>` — allowed verbs: `search|get|query|find|nearest|within|render|descriptor`.
- Each tool supplies: name, version, description, `input_schema`, `output_schema`, handler.
- Discovery endpoints: `/tools/list` (names + paging), `/tools/describe` (full metadata).
- Keep handlers small; shared concerns (HTTP, retries) live in `os_common.py`.
- Tools register via side effects into `tools/registry.py`; ensure modules are explicitly imported in `server/mcp/tools.py` (don’t rely on import order).
- OS-backed tools must return `501` with `{code:"NO_API_KEY"}` when `OS_API_KEY` is unset (see `tools/os_common.py`).
- Resources support filtering, paging, and weak ETags; use `If-None-Match` and return `304` with `ETag` header when appropriate (see `server/mcp/resources.py`).

## STDIO adapter notes

- `server/stdio_adapter.py` speaks JSON-RPC 2.0 with `Content-Length` framing; methods map to `tools/*` and `resources/*`.
- Keep responses compatible with existing tests under `tests/test_stdio_*.py` when modifying adapter behavior.

## Testing Strategy

- Pytest with coverage gate (≥90%). Current suite covers success + validation + upstream error paths.
- When adding a tool: include validation tests, success path (mocked upstream), and at least one upstream error normalization test.
- Prefer monkeypatching minimal surface (e.g., `client.get_json` / `requests.get`) to reach normalization logic.
- Future: introduce golden fixtures for canonical postcodes & feature queries.

## Commits & PRs

- Use Conventional Commits: `feat(server): implement os_places.by_postcode parsing`.
- Each PR must: update `CHANGELOG.md`, add/adjust docs, include/adjust tests.
- Avoid bundling unrelated refactors with feature delivery.

## Release Process (Publish a Version)

Definition of "publish a version" in this repo:
- Update versions in `pyproject.toml` and `server/__init__.py`.
- Move the `[Unreleased]` section in `CHANGELOG.md` into a new dated release.
- Add `RELEASE_NOTES/<version>.md` (match the changelog summary).
- Run tests (`pytest -q`) and confirm coverage gate passes.
- Create a git tag `v<version>` that points at the release commit.
- Optional but recommended: build the Docker image (`docker build -t mcp-geo-server .`).

If you need CI automation later, add `.github/workflows/release.yml` to formalize the above.

## Security & Configuration

- Never log full secrets (centralise redaction helper: e.g., `server/security.py`).
- Validate all external inputs (postcode regex OK; add length and normalization utilities module).
- Timeouts on all outbound HTTP calls (already set for OS API: `timeout=5`). Add retry strategy (e.g., `tenacity`) for transient errors.
- Config knobs live in `server/config.py`: `OS_API_KEY`, `DEBUG_ERRORS`, `RATE_LIMIT_PER_MIN`, `RATE_LIMIT_BYPASS`, `METRICS_ENABLED`, `ONS_LIVE_ENABLED`, `ONS_CACHE_TTL`, `ONS_CACHE_SIZE`.

## Observability Enhancements (Backlog)

- Add structured JSON logging sink.
- Add request/response size metrics and tool latency histograms (Prometheus or OTLP exporter).
- Correlation ID should also propagate to outbound requests via header injection.

## Agent Execution Rules

- Do not introduce new dependencies without updating `pyproject.toml` and rationale in PR.
- Prefer incremental refactors (extract functions before rewriting blocks).
- If adding a tool: include JSON schema for request/response in docstring.
- Keep the implementation plan in `PROGRESS.MD` updated as plan items move from
  pending to in progress to done. Update `CHANGELOG.md` when a plan item is
  completed and adjust related docs in the same change.

## Preview Spec Tracking

- Any preview/evolving spec or feature must be logged in `docs/spec_tracking.md`.
- Entries must include spec URL, status, owner, last-checked date, and review cadence.
- Update README if a preview spec link changes or new preview features are added.
- Note client-behavior evidence (logs or traces) in the tracking entry when available.

## MCP Client Interop Learnings

- Claude uses `tools/call` with `params.name` + `params.arguments` (not `args`); support both.
- Claude expects tool names matching `^[a-zA-Z0-9_-]{1,64}$`; normalize dotted names for stdio list/search and accept originals for calls.
- STDIO framing can be JSON lines or Content-Length; auto-detect and allow `MCP_STDIO_FRAMING=line` to force.
- Do not respond to JSON-RPC notifications (no `id`) to avoid client disconnects.
- Some clients do not advertise MCP-Apps UI support; stdio adds `data.fallback` static map metadata for `os_apps.render_geography_selector` unless `MCP_STDIO_UI_SUPPORTED=1`. Use `MCP_STDIO_FALLBACK_BBOX_DEG` to control fallback span.

## Gaps & Immediate Action Items

1. CI pipeline not yet committed (lint, type, test, coverage badge, build image).
2. Observability: improve/extend metrics and add structured JSON log sink.
3. Retry/backoff sophistication (currently simple exponential) – consider `tenacity` or custom jitter.
4. Resource catalog still minimal (admin sample only) – add real code lists & full boundary sets.
5. Pagination not implemented for tools returning large collections (future: token-based for OS features).
6. Map render tool currently descriptor/stub – add real static map generation or proxy.
7. Security hardening: circuit breaker not yet implemented (rate limiting is present in `server/main.py`).
8. Enhance resources further (ETag / caching headers are present; expand to more datasets).
9. ONS data tools (Epic D) not yet started.

Resolved (removed from gaps): baseline tests, dynamic tool registration reliability, redaction helper, README duplication, type + lint config, modular tool structure, STDIO adapter relocation with branch tests (+ invalid params fix), ETag support for resources over STDIO.

## Roadmap (Suggested)

- Phase 1 (DONE): Core server + dynamic tool dispatch + baseline tests.
- Phase 2 (DONE): Implement Epic B OS tools with schemas & describe endpoint.
- Phase 3 (NEXT): CI pipeline, metrics, richer retries, resource population.
- Phase 4 (IN PROGRESS): Admin geography tools (started `admin_lookup.containing_areas`), ONS data, golden scenario tests.
- Phase 5: Performance & scaling (caching, rate limiting, async upstream calls).

---

Last updated: 2026-01-21
