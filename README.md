# MCP Geo Server

Production-focused Model Context Protocol (MCP) server for geospatial (Ordnance Survey) tooling built with FastAPI & Python 3.11+. Provides a uniform tool abstraction, typed schemas, structured error model, correlation IDs, and high test coverage (≥90%).

## Key Features
- MCP endpoints: `/tools/list`, `/tools/call`, `/tools/describe`, `/resources/list`
- Uniform error envelope and pagination (`nextPageToken`)
- Dynamic tool registration with schema introspection
- Structured logging & correlation IDs
- OS API client with retries and explicit upstream error codes
- High coverage test suite exercising success + failure paths

## Quickstart
```bash
git clone <repo-url>
cd mcp-geo
pip install -e .[test]
uvicorn server.main:app --reload
```
Then visit:
- `GET /healthz`
- `GET /tools/list`
- `GET /tools/describe`
- `POST /tools/call` with `{ "tool": "os_places.by_postcode", "postcode": "SW1A1AA" }`

Set `OS_API_KEY` in environment (or `.env`) for live Ordnance Survey calls; otherwise tools return graceful `501 NO_API_KEY` responses.

## Tool Catalog (Epic B Implemented)
Tools are discoverable via `/tools/list` and rich metadata via `/tools/describe`.

| Tool | Purpose |
|------|---------|
| os_places.search | Free text address search |
| os_places.by_postcode | UPRNs + addresses for a postcode |
| os_places.by_uprn | Single address lookup |
| os_places.nearest | Nearest addresses to a coordinate |
| os_places.within | Addresses within bbox |
| os_names.find | Gazetteer name search |
| os_names.nearest | Nearest named features |
| os_features.query | NGD features by bbox & collection |
| os_linked_ids.get | Relationship lookup between UPRN/USRN/TOID |
| os_maps.render | Static map render metadata (stub/descriptor) |
| os_vector_tiles.descriptor | Vector tiles style/source descriptor |

## Error Model
All errors conform to:
```json
{ "isError": true, "code": "<CODE>", "message": "..." }
```
Primary codes: `INVALID_INPUT`, `UNKNOWN_TOOL`, `NO_API_KEY`, `OS_API_ERROR`, `UPSTREAM_TLS_ERROR`, `UPSTREAM_CONNECT_ERROR`, `INTEGRATION_ERROR`.

## Project Structure
```text
server/        FastAPI app & routers
tools/         Tool implementations (one module per domain)
resources/     Static datasets (future expansion)
playground/    Transcript / UI stubs
tests/         Pytest suite (≥90% coverage)
docs/          Backlog & design notes
.devcontainer/ Dev environment setup
```

## Dynamic Tool Registration
`server/mcp/tools.py` explicitly imports each `tools.*` module at startup to guarantee registration in environments where implicit side-effect imports are skipped (e.g. selective packaging or lazy loaders). This ensures `/tools/describe` always reflects the full catalog without relying on import order.

## Testing & Coverage
Run tests with:
```bash
pytest -q
```
Coverage gate (configured) requires ≥90%. Add tests for both success and error branches (retry paths, validation failures, upstream errors). Avoid broad mocks that skip normalization logic.

## Contributing
- Use Conventional Commits (e.g. `feat(tools): add os_places.within pagination`).
- Every PR: update `CHANGELOG.md`, add/adjust tests, keep coverage ≥90%.
- Include JSON schemas (input/output) when adding a tool.
- Prefer incremental refactors; avoid unrelated changes in feature PRs.

## Examples & Golden Tests
See `docs/examples.md` for sample payloads, conversation flows, and guidance on chaining tools. Golden scenario tests (`test_golden_scenarios.py`) ensure transformation stability with deterministic mocked upstream responses.

## Configuration
Copy `.env.example` → `.env` and set `OS_API_KEY`. Optional flags:
- `DEBUG_ERRORS` (if present / truthy) enables traceback in error responses; otherwise stack traces are suppressed.

## SSL & Certificates
Container and dev setup ensure current CA bundle (certifi) for stable TLS to OS APIs.

## License
MIT
