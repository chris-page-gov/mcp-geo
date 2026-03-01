# Compact Windows Test Suite

This directory is the dedicated unattended test harness for compact-host MCP UI behavior.

Current status:

- Scaffolded suite and matrix configs are in place.
- Smoke tests ensure all six UI pages load under a deterministic MCP bridge.
- Matrix tests are currently scaffold-level and will be expanded during CW-1..CW-7.

Entry points:

- `npm --prefix playground run test:compact`
- `npm --prefix playground run test:compact-matrix`
