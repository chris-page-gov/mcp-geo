# Compact Windows Test Suite

This directory is the dedicated unattended test harness for compact-host MCP UI behavior.

Current status:

- CW-7 complete: strict acceptance coverage is implemented for all six UIs.
- `smoke.spec.js` validates global compact contract plus UI-specific behavior:
  - host handshake + host-context merge + fullscreen fallback
  - style/layer/opacity controls
  - boundary selection/filter/import workflows
  - auth mode and diagnostics contracts
  - deterministic loading/empty/error flows and runtime exception checks
- `compact_matrix.spec.js` validates compact behavior across host profiles and viewports.
- Harness uses deterministic MCP bridge stubs (`support/mcp_bridge.js`) and compact assertions (`support/compact_assertions.js`).

Entry points:

- `npm --prefix playground run test:compact`
- `npm --prefix playground run test:compact-matrix`
