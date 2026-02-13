# Copilot instructions (mcp-geo)

## Big picture
- FastAPI server in `server/main.py` exposing MCP-style HTTP endpoints: `/tools/list`, `/tools/describe`, `/tools/call`, `/resources/list`, `/resources/read`, plus `/healthz` and `/metrics`.
- Tools are implemented as modules under `tools/` and registered via side effects into the in-memory registry in `tools/registry.py`.
- Tool registration is forced by explicit imports in `server/mcp/tools.py` (do not rely on import order).
- There is also a JSON-RPC 2.0 STDIO adapter in `server/stdio_adapter.py` (legacy entrypoint `scripts/os_mcp.py` re-exports it).

## Run / test
- Install: `pip install -e .[test]`
- Run HTTP server: `uvicorn server.main:app --reload` (or `python run.py`)
- Run tests: `pytest -q` (coverage gate configured in `pytest.ini`)

## Project conventions to follow
- **Error envelope**: return `{ "isError": true, "code": str, "message": str, "correlationId"?: str }` for errors.
  - Correlation IDs are created/propagated by middleware in `server/main.py` via `x-correlation-id`.
  - Unhandled exceptions are normalized by the global exception handler in `server/main.py` (traceback only when `DEBUG_ERRORS=true`).
- **Pagination**: when paging, use `nextPageToken` (camel case) like `server/mcp/tools.py` and `server/mcp/resources.py`.
- **Logging/secrets**: use `server/security.py` helpers (`redact`, `mask_in_text`) and avoid leaking `OS_API_KEY`.
- **Rate limiting**: enforced by middleware in `server/main.py` unless bypassed.
  - Defaults in `server/config.py`: `RATE_LIMIT_PER_MIN=120` and `RATE_LIMIT_BYPASS=True` (tests/dev usually bypass; set `RATE_LIMIT_BYPASS=false` to exercise 429 path).
  - Limit keying: per client IP and top-level path segment; over-limit returns `429` with `{code:"RATE_LIMITED"}`.
- **Metrics**: `GET /metrics` is enabled by default (`METRICS_ENABLED=True` in `server/config.py`).

## Adding or changing a tool
- Implement in a `tools/*.py` module and register a `tools.registry.Tool`:
  - Handler signature is `handler(payload: dict[str, Any]) -> tuple[int, dict[str, Any]]` (see `tools/registry.py`).
  - Follow existing error codes and upstream normalization patterns in `tools/os_common.py` and `tools/os_places.py`.
- **No OS key behavior**: OS-backed tools must gracefully return `501` with `{code:"NO_API_KEY"}` when `OS_API_KEY` is unset (see `tools/os_common.py`).
- Update the explicit import list in `server/mcp/tools.py` to guarantee registration.
- Note: `/tools/call` passes the whole request JSON to the handler (including the `tool` field). Validate and extract only what you need.

## Resources API patterns
- Implemented in `server/mcp/resources.py` with:
  - Filtering parameters (e.g., `level`, `nameContains`, `geography`, `measure`).
  - `limit`/`page` pagination and `nextPageToken`.
  - Weak ETags and `If-None-Match` support returning `304` with `ETag` header.

## Config knobs (used in code)
- `server/config.py`: `OS_API_KEY`, `DEBUG_ERRORS`, `RATE_LIMIT_PER_MIN`, `RATE_LIMIT_BYPASS`, `METRICS_ENABLED`, `ONS_LIVE_ENABLED`, `ONS_CACHE_TTL`, `ONS_CACHE_SIZE`.

## STDIO adapter notes
- `server/stdio_adapter.py` speaks JSON-RPC 2.0 with `Content-Length` framing; methods map to `tools/*` and `resources/*`.
- Keep responses compatible with existing tests under `tests/test_stdio_*.py` when modifying adapter behavior.
