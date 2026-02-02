# Testing and Quality

## Test suite

- Pytest with >=90% coverage gate.
- Success, validation, and upstream error paths covered.
- STDIO adapter behaviors tested (notification handling, framing).

## Quality standards

- Typed schemas for all tools.
- Max line length: 100.
- Ruff + mypy enforced.

## Recommended additional tests (backlog)

- MCP-Apps UI rendering in a real client (Inspector + Claude).
- Boundary cache regression tests for freshness metadata.
- ONS dataset cache snapshot tests.

