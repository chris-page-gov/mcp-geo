# GitHub Copilot / Agent Instructions

These instructions tailor agent behaviour for the `mcp-geo` repository. Follow them to produce minimal, correct, test‑backed changes aligned with project governance.

## Runtime & Stack

- Python >=3.11, FastAPI for HTTP surface.
- Do not downgrade runtime or introduce frameworks without approval.
- Use `uvicorn server.main:app --reload` for local run.

## Core Conventions

- JSON responses: success payloads are structured objects; errors use `{ "isError": true, "code": str, "message": str, "correlationId"?: str }`.
- Pagination fields: always `nextPageToken` when partial pages returned.
- Correlation ID: propagate `x-correlation-id` header from request to response; include in logs.
- Avoid leaking stack traces unless `DEBUG_ERRORS=true` env flag is set.
- Redact secrets via central helper (implement `server/security.py#redact`).

## Tools Architecture

- Each tool gets its own module under `server/mcp/tools/` (create package if missing) or `tools/` if pure logic.
- Provide metadata: `name`, `version`, `description`, `input_schema`, `output_schema` (JSON Schema dicts) exposed via `/tools/describe`.
- Dispatcher should import lightweight registry only (no heavy imports at import time—lazy load where possible).
- Network calls: enforce timeout (<=5s) and apply retry (2–3 attempts, exponential backoff) for transient 5xx/timeout.

## When Adding a Tool

1. Create module with pure function `run(input: dict) -> dict` plus `SCHEMA_IN`, `SCHEMA_OUT` constants.
2. Register in registry map: `{ name: ToolSpec }`.
3. Add contract tests (success + validation failure + not found path) in `tests/`.
4. Update `/tools/list` expected list and ensure describe output includes new tool.
5. Update `CHANGELOG.md` under `[Unreleased]` (Added section).

## Testing Requirements

- Use `pytest` + `httpx.AsyncClient` for API tests.
- Create/maintain: `test_healthz.py`, `test_tools_list.py`, `test_postcode.py`, `test_error_model.py`, `test_describe.py`.
- Mock external OS endpoints (`pytest_httpx` or `responses`).
- Golden fixtures: postcode → expected normalised outputs.
- Do not add a feature without at least one test asserting its success path and one error case.

## Linting & Types

- Add and keep clean: `ruff` (style + import order), `mypy` (strict mode gradually adopted—start with modules touched by change).
- Run locally (or in CI) before PR: `ruff check . && mypy server`.

## Error Handling

- Wrap unexpected exceptions in generic error model; do not expose full trace unless `DEBUG_ERRORS`.
- Prefer raising domain exceptions (e.g., `InvalidPostcodeError`) and mapping them in a dedicated exception handler rather than inline JSONResponse duplication.

## Logging

- Use `loguru`; add optional JSON serialised sink when `LOG_JSON=true`.
- Include: timestamp, level, correlationId, path, tool (if applicable), latency_ms.

## Pull Request Rules

- Conventional Commits subject lines: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `ci`, `build`.
- Every PR updates tests and `CHANGELOG.md` if user-visible.
- Split large refactors: first extraction, then behaviour change.

## Changelog Discipline

- Only list user-visible behaviour changes. Remove duplicates between epic summaries and Fixed section.
- Sections: Added / Changed / Fixed / Removed / Security.

## Playground Endpoint

- Use async handlers; `await request.json()`; validate with Pydantic model; cap transcript length; never store secrets.

## Secrets & Config

- All secrets come from environment; do not bake into code/tests.
- Use central `redact(value: str) -> str` to mask values in logs (keep first 3 + last 3 chars).

## Versioning

- Expose `__version__` in `server/__init__.py` synced with `pyproject.toml`.
- Automate release via future GitHub Actions (not implemented yet).

## Agent DO / DO NOT

DO:
- Add tests with each behavioural change.
- Keep patches narrow and documented in PR body.
- Prefer composition over large rewrites.

DO NOT:
- Add dependencies without justification.
- Expose stack traces in production responses.
- Duplicate error response structure inline.

## Minimal Example Tool Skeleton

```python
# server/mcp/tools/os_places_by_postcode.py
SCHEMA_IN = {"type": "object", "properties": {"postcode": {"type": "string"}}, "required": ["postcode"]}
SCHEMA_OUT = {"type": "object", "properties": {"uprns": {"type": "array"}}, "required": ["uprns"]}

def run(input: dict) -> dict:
    # validate input (pydantic model preferred in full impl)
    postcode = input["postcode"].strip().upper().replace(" ", "")
    # call external service (omitted)
    return {"uprns": []}
```

## Contact

Open an issue or tag maintainers for architectural questions.
