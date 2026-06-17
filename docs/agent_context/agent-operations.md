# Agent Operations Notes

This file holds operational learnings that do not need to live in `AGENTS.md`.

## MCP Client Interop

- Claude uses `tools/call` with `params.name` and `params.arguments`; support
  `args` only as compatibility input.
- Claude expects tool names matching `^[a-zA-Z0-9_-]{1,64}$`; STDIO should
  expose sanitized aliases and accept both sanitized and original names.
- `resources/read` should accept both `params.uri` and `params.name`.
- STDIO framing can be JSON lines or `Content-Length`; auto-detect and allow
  `MCP_STDIO_FRAMING=line`.
- Do not respond to JSON-RPC notifications without `id`.
- Some clients do not advertise MCP-Apps UI support; STDIO adds `data.fallback`
  static map metadata for `os_apps.render_geography_selector` unless
  `MCP_STDIO_UI_SUPPORTED=1`.
- MCP-Apps payloads may arrive as `structuredContent`, JSON/text content blocks,
  or `result.data`; widget clients should normalize all three.
- MapLibre style swaps clear custom sources/layers; widgets must rehydrate
  overlays and replay in-memory selected state on `style.load`.

## GitHub / Codex Review Workflow

- When PR comments or descriptions include backticks, write markdown to a temp
  file and use `gh ... --body-file` where possible.
- Codex review is triggered by PR comment `@codex review`, not reviewer
  assignment.
- Before asking for another review, cluster unresolved comments by behavior area,
  scan for sibling implementations, fix transport variants together, add
  regression coverage, and rerun the narrowest meaningful validation slice.
- Do not stop at the exact line cited by a reviewer. Check shared helpers,
  HTTP/STDIO variants, cache/live variants, CSV/Parquet variants, and widget
  fallback paths.
- GitHub Advanced Security discussion markers may not be normal review
  conversations; `resolveReviewThread` can fail for those markers.
- For deterministic Playwright suites, prefer component-scoped selectors and an
  explicit rendered-ready indicator. Add a non-default port smoke when hard-coded
  port assumptions are plausible.

## Backlog Snapshot

- Add playground/browser coverage and release automation to CI.
- Improve metrics with structured JSON logging and request/response size or tool
  latency histograms.
- Add circuit-breaker behavior beyond current rate limiting.
- Expand static resource catalog and boundary sets with paging and metadata.
- Continue phased Ruff/mypy expansion only when each new slice is green and
  documented.
