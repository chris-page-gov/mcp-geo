# MCP Geo Full Code Review

Date: 2026-03-24
Reviewer: Codex GPT-5
Scope: architecture, system design, documentation, software engineering, security, test and delivery posture

## Executive Summary

MCP-Geo is a substantial and unusually well-documented MCP server with strong
transport coverage, rich domain capability, and a mature evidence culture.
The core architecture is coherent: FastAPI owns HTTP routing and middleware,
`server/stdio_adapter.py` handles JSON-RPC over STDIO, tools are registered
through explicit imports into a central registry, and the repo maintains a
large regression suite that currently passes at the documented coverage gate.

The highest-risk problems are not in the geospatial logic itself. They are in
security boundaries and engineering guardrails around the core:

1. HTTP auth coverage is inconsistent. Under authenticated deployment mode,
   `/metrics`, `/tools/list`, `/tools/describe`, `/tools/search`, and the full
   `/playground/*` surface remain reachable without credentials, while
   `/resources/*` and `/tools/call` are protected.
2. The central redaction helper does not include the newer MCP HTTP auth
   secrets, so the repo's current masking path can still expose
   `MCP_HTTP_AUTH_TOKEN` or `MCP_HTTP_JWT_HS256_SECRET` if they appear in log or
   exception text.
3. The repo-supported `scripts/ruff-local` and `scripts/mypy-local` wrappers are
   currently broken when invoked without extra arguments, which prevents the
   documented local static-analysis workflow from running.
4. CI and repo guidance are out of sync on static-analysis scope. The
   documented standard says Ruff is enforced and mypy is clean, but CI only
   checks a small curated subset of files.

The result is a codebase with strong feature breadth and good test discipline,
but with operational trust boundaries that are weaker than the documentation
implies. The near-term priority should be tightening auth coverage and secret
handling before further expanding surface area.

## Method

Review inputs:

- Runtime code under `server/` and `tools/`
- Process and design docs in `README.md`, `AGENTS.md`, `docs/spec_package/`
- CI workflow in `.github/workflows/ci.yml`
- Validation and regression tests in `tests/`
- Existing report index in `docs/reports/README.md`

Validation performed:

- `./scripts/pytest-local -q`
  - Result: `1202 passed`, `6 skipped`, coverage `90.26%`
- `./scripts/ruff-local`
  - Failed before invoking Ruff: `scripts/run-local-tool: line 249: TOOL_ARGS[@]: unbound variable`
- `./scripts/mypy-local`
  - Failed before invoking mypy: `scripts/run-local-tool: line 249: TOOL_ARGS[@]: unbound variable`
- Direct authenticated-surface probe using `uv run python` + `fastapi.testclient`
  with `MCP_HTTP_AUTH_MODE=static_bearer`
  - `/metrics` returned `200`
  - `/playground/transcript` returned `200`
  - `/playground/evaluation/latest` returned `200`
  - `/tools/list` returned `200`
  - `/tools/describe` returned `200`
  - `/tools/search` returned `200`
  - `/resources/list` returned `401`

## Priority Findings

### P1. MCP HTTP auth does not cover several non-`/mcp` HTTP surfaces

Severity: High

Evidence:

- [server/main.py](/Users/crpage/repos/mcp-geo/server/main.py#L150) mounts
  `playground.router`, `http_transport.router`, and the unauthenticated
  `/metrics` route together.
- [server/main.py](/Users/crpage/repos/mcp-geo/server/main.py#L158) exposes
  `/metrics` directly with no call to `authorize_http_route()`.
- [server/mcp/tools.py](/Users/crpage/repos/mcp-geo/server/mcp/tools.py#L161)
  defines `/tools/list` with no auth gate.
- [server/mcp/tools.py](/Users/crpage/repos/mcp-geo/server/mcp/tools.py#L281)
  defines `/tools/search` with no auth gate.
- [server/mcp/tools.py](/Users/crpage/repos/mcp-geo/server/mcp/tools.py#L454)
  defines `/tools/describe` with no auth gate.
- [server/mcp/playground.py](/Users/crpage/repos/mcp-geo/server/mcp/playground.py#L81)
  exposes the full `/playground/*` surface without auth.
- Auth probe confirmed that these endpoints stay public even when
  `MCP_HTTP_AUTH_MODE=static_bearer`, while `/resources/list` correctly returns
  `401`.
- [docs/Build.md](/Users/crpage/repos/mcp-geo/docs/Build.md#L241) says the
  hardened profile exposes `/metrics` only on a private monitoring plane, which
  is stronger than the runtime actually enforces.

Impact:

- Anonymous callers can enumerate available tools, schemas, toolsets, and
  prompt-adjacent discovery surfaces even when authenticated MCP HTTP mode is
  enabled.
- Anonymous callers can read monitoring counters including auth-failure and
  session metrics.
- Anonymous callers can read and reset in-memory playground state, fetch the
  latest evaluation payload, and append arbitrary event data to the server's
  playground log.
- This creates a split trust boundary: operationally sensitive surfaces remain
  outside the same auth contract the repo now applies to `/mcp`,
  `/resources/*`, and `/tools/call`.

Recommendation:

- Decide the intended policy explicitly:
  - Option A: all HTTP surfaces other than `/health` require the same auth mode
    as `/mcp`
  - Option B: keep some discovery endpoints public, but document that policy and
    move `/metrics` and `/playground/*` behind auth or network isolation
- Add regression tests for auth-enabled access to `/metrics`, `/tools/list`,
  `/tools/describe`, `/tools/search`, and `/playground/*`.

### P1. Secret redaction omits MCP HTTP auth credentials

Severity: High

Evidence:

- [server/security.py](/Users/crpage/repos/mcp-geo/server/security.py#L37)
  limits `configured_secrets()` to `OS_API_KEY`, `NOMIS_UID`, and
  `NOMIS_SIGNATURE`.
- [server/config.py](/Users/crpage/repos/mcp-geo/server/config.py#L149) now
  hydrates additional secrets from files, including `MCP_HTTP_AUTH_TOKEN` and
  `MCP_HTTP_JWT_HS256_SECRET`.
- [server/main.py](/Users/crpage/repos/mcp-geo/server/main.py#L201) uses
  `configured_secrets(settings)` when masking exception text.
- [server/logging.py](/Users/crpage/repos/mcp-geo/server/logging.py#L38) also
  relies on `configured_secrets(settings)` for log redaction.

Impact:

- If an exception message, request echo, or logged extra payload includes the
  static bearer token or JWT signing secret, the shared masking path will not
  redact it.
- The repo documents centralized masking as a security control, so this is a
  real regression in the control boundary rather than an isolated missing test.

Recommendation:

- Expand `configured_secrets()` to include all configured secrets used by the
  runtime, at minimum `MCP_HTTP_AUTH_TOKEN` and `MCP_HTTP_JWT_HS256_SECRET`.
- Add regression tests that assert these values are removed from both generic
  exception payloads and structured logs.

### P2. Repo-supported local lint/type wrappers are broken on the default path

Severity: Medium

Evidence:

- [AGENTS.md](/Users/crpage/repos/mcp-geo/AGENTS.md#L45) instructs users and
  agents to prefer `scripts/pytest-local`, `scripts/ruff-local`, and
  `scripts/mypy-local`.
- Running `./scripts/ruff-local` and `./scripts/mypy-local` both failed before
  invoking the underlying tool:
  `scripts/run-local-tool: line 249: TOOL_ARGS[@]: unbound variable`
- [scripts/run-local-tool](/Users/crpage/repos/mcp-geo/scripts/run-local-tool#L249)
  appends `"${TOOL_ARGS[@]}"` under `set -u`; the zero-argument case trips the
  shell on this platform.

Impact:

- The documented local static-analysis workflow is currently not runnable on its
  default path.
- Engineers can still run `pytest`, and CI still runs, but the repo’s preferred
  developer ergonomics are broken and may hide static-analysis drift in routine
  local use.

Recommendation:

- Make the wrapper robust to zero arguments, then add shell-level regression
  coverage for the no-argument path on both wrappers.

### P2. Static-analysis policy and CI enforcement are materially out of sync

Severity: Medium

Evidence:

- [AGENTS.md](/Users/crpage/repos/mcp-geo/AGENTS.md#L64) says `mypy` is clean
  and Ruff is enforced.
- [AGENTS.md](/Users/crpage/repos/mcp-geo/AGENTS.md#L89) says the suite uses a
  coverage gate and emphasizes broad validation hygiene.
- [.github/workflows/ci.yml](/Users/crpage/repos/mcp-geo/.github/workflows/ci.yml#L47)
  runs Ruff only on a handful of files.
- [.github/workflows/ci.yml](/Users/crpage/repos/mcp-geo/.github/workflows/ci.yml#L58)
  runs mypy only on a small curated subset.

Impact:

- Most of the repository can regress on lint and typing without CI noticing.
- The docs currently create stronger expectations than the actual gate surface.
- This weakens confidence in the repo’s engineering claims, especially for a
  public MCP server that emphasizes assurance and governance.

Recommendation:

- Either:
  - widen Ruff/mypy coverage incrementally until the repo matches the documented
    standard, or
  - explicitly document that static gates are intentionally scoped while debt is
    being paid down
- Pair any decision with a tracked plan item in `PROGRESS.MD`.

### P3. Playground HTTP semantics and persistence model are inconsistent with the repo’s error discipline

Severity: Low to Medium

Evidence:

- [server/mcp/playground.py](/Users/crpage/repos/mcp-geo/server/mcp/playground.py#L100)
  returns an error object for invalid tool-call payloads but leaves the HTTP
  status at `200`.
- [server/mcp/playground.py](/Users/crpage/repos/mcp-geo/server/mcp/playground.py#L142)
  does the same for invalid event payloads.
- [tests/test_playground.py](/Users/crpage/repos/mcp-geo/tests/test_playground.py#L19)
  codifies the `200` status on invalid input.
- [AGENTS.md](/Users/crpage/repos/mcp-geo/AGENTS.md#L65) documents a uniform
  structured error model, and the rest of the HTTP surface generally uses `4xx`
  for invalid input.

Impact:

- Clients cannot rely on status code semantics consistently across HTTP
  endpoints.
- Combined with the missing auth gate, the playground becomes an easy place for
  unauthenticated log pollution and noisy operational behavior.

Recommendation:

- Bring `/playground/*` validation failures into line with the rest of the
  server by returning `400` for invalid payloads.
- Consider moving playground state behind an explicit debug or local-only mode
  rather than mounting it unconditionally in all deployments.

## Architecture Review

### Strengths

- Clear runtime split between:
  - HTTP app and middleware in `server/main.py`
  - Streamable MCP HTTP transport in `server/mcp/http_transport.py`
  - STDIO transport in `server/stdio_adapter.py`
  - domain tools under `tools/`
- Explicit module import lists in
  [server/mcp/tools.py](/Users/crpage/repos/mcp-geo/server/mcp/tools.py#L22)
  reduce reliance on import order and make registration behavior deterministic.
- The registry model in
  [tools/registry.py](/Users/crpage/repos/mcp-geo/tools/registry.py#L1) is
  simple and effective for this scale.
- Resource delivery and handoff surfaces show careful evolution for hostile or
  partial MCP hosts.
- The repo has unusually strong historical evidence capture: design docs,
  operational runbooks, benchmark outputs, and troubleshooting traces all
  support maintenance and audits.

### Architectural Risks

- The HTTP and STDIO transports duplicate a large amount of MCP logic. The repo
  history already records fixes that had to be applied in both files, which is a
  concrete sign of transport-divergence risk.
- A large amount of mutable process-global state exists in:
  - HTTP session tracking
  - rate limiting
  - observability counters
  - playground transcripts/events
  - map/proxy caches
  This is acceptable for a single-process research server but should be treated
  as a scaling boundary, not a transparent implementation detail.
- The app mixes product surfaces, benchmark tooling, internal ops endpoints, and
  local-playground conveniences into the same runtime binary. That keeps local
  development simple, but it increases the burden on deployment policy because
  there is no hard separation between external and internal surfaces.

### Architectural Recommendation

- Move toward an explicit deployment profile model:
  - core public runtime
  - authenticated operator/runtime endpoints
  - local-only playground/debug endpoints
- Reduce transport duplication by extracting more shared MCP method handling
  into common helpers with transport-specific wrappers only at the edge.

## Security Review

### Strengths

- The repo has a visible security program: OWASP validation, route auth
  surfaces, masked logging, rate limiting, and documented deployment guidance.
- HTTP auth supports both static bearer and HS256 JWT with subject binding and
  quota enforcement in
  [server/mcp/http_transport.py](/Users/crpage/repos/mcp-geo/server/mcp/http_transport.py).
- Resource access shows careful handling of ETags, safe download paths, and
  chunked retrieval.
- Error envelopes are generally consistent and correlation IDs are propagated.

### Concerns

- Auth coverage inconsistency is the top security concern because it weakens the
  repo’s operational perimeter.
- Redaction coverage lagged behind the addition of new auth modes.
- The playground log path is writable from unauthenticated requests today.
- `/metrics` exposes auth-failure and session counters publicly when enabled,
  which can help an external observer map security posture and usage patterns.

### Security Recommendation

- Treat the runtime as having three trust classes:
  - public health/info
  - authenticated MCP/control-plane
  - local/operator-only observability and playground
- Enforce those classes in code, not only in deployment documentation.

## Software Engineering Review

### Strengths

- The repo is disciplined about schemas, explicit error envelopes, and focused
  regression testing around transport behavior.
- `./scripts/pytest-local -q` currently passes with a healthy total coverage
  outcome.
- The codebase preserves significant institutional memory in markdown reports
  and troubleshooting artifacts, which is valuable for a research-heavy server.

### Concerns

- Developer tooling is brittle where it should be boring. The broken
  `ruff-local` and `mypy-local` wrappers erode confidence in the preferred
  workflow.
- The stated standard for linting and typing is stronger than actual CI
  enforcement.
- Some review/test surfaces focus on branch coverage rather than contract
  realism, which is useful but can create a false sense of gate completeness if
  paired with narrow static analysis.

### Engineering Recommendation

- Fix wrapper reliability first.
- Align CI policy with the repo’s documented standard.
- Add a simple status matrix in docs showing which quality gates are:
  - full-repo
  - scoped
  - optional/manual

## Documentation Review

### Strengths

- The repo is exceptionally well documented relative to most engineering
  projects.
- The spec package, build docs, getting-started docs, and report index make the
  project navigable for new maintainers.
- Historical investigation artifacts are preserved rather than discarded, which
  supports auditability and context continuity.

### Concerns

- Some documentation now overstates enforcement or isolation properties:
  - private metrics exposure
  - full Ruff/mypy enforcement
- The repo contains a lot of historical material, and not all of it is clearly
  marked as normative versus historical reference. That increases the chance of
  a maintainer following an outdated assurance claim.

### Documentation Recommendation

- Mark runtime-security statements as either:
  - enforced in code
  - expected from deployment topology
- Make static-analysis scope explicit in both `README.md` and `AGENTS.md`.

## System Design Review

### What is working well

- The transport model supports both desktop MCP and HTTP MCP clients cleanly.
- Tool metadata, resource handoff, and discovery/toolset mechanisms fit the
  repository’s stated goal of acting as a geospatial MCP platform rather than a
  single-purpose API wrapper.
- The server’s use of explicit schemas and normalized error codes is a good
  foundation for multi-client interoperability.

### System-level weaknesses

- Runtime surface composition is currently too permissive for a server that has
  grown beyond a purely local development tool.
- Observability, playground, and control-plane capabilities are not separated
  strongly enough from the user-facing HTTP surface.
- The repo’s assurance story depends partly on process and documentation where
  stronger runtime enforcement is now warranted.

## Positive Highlights

- Core regression baseline is green: `1202 passed`, `6 skipped`, coverage
  `90.26%`.
- Tool/resource interoperability work appears thoughtful and battle-tested.
- The project has strong evidence of learning loops: reports lead to code
  changes, and code changes lead to targeted regressions.
- The repository is far more maintainable than a typical prototype because the
  author preserved design rationale and investigation history.

## Recommended Remediation Order

1. Close auth gaps on `/metrics`, `/tools/list`, `/tools/describe`,
   `/tools/search`, and `/playground/*`.
2. Extend central redaction coverage to MCP HTTP auth secrets and add tests.
3. Repair `scripts/run-local-tool` zero-argument handling so
   `scripts/ruff-local` and `scripts/mypy-local` work as documented.
4. Align CI and docs on the real Ruff/mypy enforcement scope.
5. Normalize playground HTTP error semantics and decide whether the playground
   should be mounted in production-like profiles at all.

## Appendix: Evidence References

- [AGENTS.md](/Users/crpage/repos/mcp-geo/AGENTS.md)
- [README.md](/Users/crpage/repos/mcp-geo/README.md)
- [server/main.py](/Users/crpage/repos/mcp-geo/server/main.py)
- [server/security.py](/Users/crpage/repos/mcp-geo/server/security.py)
- [server/logging.py](/Users/crpage/repos/mcp-geo/server/logging.py)
- [server/mcp/tools.py](/Users/crpage/repos/mcp-geo/server/mcp/tools.py)
- [server/mcp/playground.py](/Users/crpage/repos/mcp-geo/server/mcp/playground.py)
- [server/mcp/http_transport.py](/Users/crpage/repos/mcp-geo/server/mcp/http_transport.py)
- [scripts/run-local-tool](/Users/crpage/repos/mcp-geo/scripts/run-local-tool)
- [.github/workflows/ci.yml](/Users/crpage/repos/mcp-geo/.github/workflows/ci.yml)
- [docs/Build.md](/Users/crpage/repos/mcp-geo/docs/Build.md)
