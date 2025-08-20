# GitHub Copilot Instructions

This repository is designed for use with GitHub Copilot and other code agents. Please follow these conventions to ensure consistent, testable, and maintainable code:

## Coding Conventions
- Use Python 3.9+ and FastAPI for all server endpoints.
- All endpoints must return structured, typed JSON responses.
- Errors must use the uniform error model: `{ "isError": true, "code": str, "message": str }`.
- Support pagination and `nextPageToken` where applicable.
- Log all requests with a correlation ID and redact secrets in logs.
- Place new tools in the `tools/` directory and register them in the MCP registry.
- Place static resources (code lists, boundaries) in the `resources/` directory.
- Add new endpoints and routers in `server/mcp/` as modular FastAPI routers.

## Testing & Validation
- All new features and epics must include validation tests in the `tests/` directory.
- Use `pytest` and `httpx` for API tests.
- Write contract tests for error models, pagination, and golden scenarios.
- Add a changelog entry for each completed epic or major feature.

## Pull Requests
- Reference the relevant epic or ticket in the PR description.
- Ensure all tests pass before merging.
- Update documentation and changelog as needed.

## Example Test (see `tests/test_healthz.py`):
```python
import httpx

def test_healthz():
    resp = httpx.get("http://localhost:8000/healthz")
    assert resp.status_code == 200
    assert resp.json().get("ok") is True
```

## Contact
For questions, contact the maintainers or open an issue.
