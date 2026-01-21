# Changelog

All notable changes to this project will be documented in this file.


## [Unreleased]
### Added
- (none)

### Changed
- (none)

### Fixed
- (none)

## [0.2.3] - 2026-01-21
### Added
- MCP stdio trace proxy `scripts/mcp_stdio_trace_proxy.py` for JSON-RPC traffic capture.
- UI interaction logging tool `os_apps.log_event` with `UI_EVENT_LOG_PATH`.
- Client tracing guide `docs/client_trace_strategy.md` covering MCP + UI logs.
- Dockerfile + `.dockerignore` for containerized STDIO usage, plus Docker client config docs.

### Changed
- Geography selector MCP-App emits UI interaction events for tracing.

### Fixed
- STDIO adapter auto-detects JSON line framing vs Content-Length to avoid client parse errors.
- STDIO initialize response now includes protocol version and server info with spec-style capabilities.
- STDIO tool names normalized to Claude-compatible pattern while still accepting original dotted names.
- `ons_data.create_filter` no longer marked read-only in tool annotations.
- STDIO adapter now accepts `arguments` payloads for `tools/call` (MCP spec compatibility).

## [0.2.2] - 2026-01-20
### Breaking
- Health check endpoint renamed to `/health` (was `/healthz`).

### Added
- Evaluation framework (question suite, rubric, harness, audit logs) and `docs/evaluation.md`.
- Tool search endpoint `/tools/search` and stdio `tools/search` with annotations and `deferLoading`.
- `os_mcp.descriptor` and `os_mcp.route_query` for tool discovery and routing.
- MCP-Apps UI resources with MapLibre geography selector and progressive disclosure UI.
- Skills resource `skills://mcp-geo/getting-started`.
- Tool catalog generator and `docs/tool_catalog.md`.
- Troubleshooting guide and expanded examples.
- ONS filter output CSV/XLSX formats.
- Tutorial expanded with multi-client setup and MCP-Apps/tool search walkthrough.

### Changed
- STDIO adapter moved to `server/stdio_adapter.py` with legacy wrapper retained.
- OS Places tools now request WGS84 output; `os_places.within` supports oversized bbox tiling/clamping.
- `mcp.json` server entries renamed to `mcp-geo-stdio` / `mcp-geo-http`.

### Fixed
- OS Places WGS84 coordinate handling for `nearest`/`within` to avoid BNG coverage errors.
- Non-200 OS API responses normalized to 501 error envelopes for consistency.
- JSON-RPC invalid params handling for non-dict `params`.

### Tests
- Added routing, MCP-Apps, tool search, and STDIO error branch coverage.
- Added OS Places bbox tiling/clamping tests and evaluation harness coverage.

## [0.2.1] - 2025-09-17

### Added
- STDIO adapter: `resources/get` parity enhancements (pagination + filtering retained) now include weak ETag generation and conditional `ifNoneMatch` support returning `{ "notModified": true }` short result.
- STDIO adapter: `resources/describe` method returning resource metadata (name, description, license).
- Client: REPL mode (`--repl`) and generic JSON param parsing for any method.
- Client: Skips initial log notifications automatically.
- Client: `--if-none-match <etag>` convenience flag for conditional `resources/get`.

### Changed
- Resource responses over STDIO now include `etag` field when not modified conditions are not met.
- Internal refactor: centralized ETag computation helper in adapter.

### Fixed
- STDIO tests updated to tolerate initial log frames preventing spurious KeyError on first read.

## [0.2.0] - 2025-09-17

### Added
- Epic A: Core MCP server (health, tools list/call/describe, resources list, transcript endpoint, error handler, logging with correlation IDs, devcontainer & Docker setup).
- Epic B: OS tooling with real handlers (conditional on `OS_API_KEY`):
  - `os_places`: search, by_postcode, by_uprn, nearest, within
  - `os_names`: find, nearest
  - `os_features.query`
  - `os_linked_ids.get`
  - `os_maps.render` (descriptor stub)
  - `os_vector_tiles.descriptor`
- Epic C (partial): `admin_lookup.containing_areas`, `admin_lookup.reverse_hierarchy`, `admin_lookup.area_geometry`, `admin_lookup.find_by_name` using bundled sample boundary resource.
- Dynamic tool import mechanism in `server/mcp/tools.py` ensuring registry population in all execution contexts.
- High coverage (>90%) test suite including validation, success, and upstream error normalization paths.
- Epic D: statistical integration foundations:
  - `ons_data.query` tool with sample observations + filters + pagination.
  - `ons_observations` resource (pagination + ETag + provenance + filters geography/measure with variant ETag).
  - ONS client scaffold (`ONSClient`) with TTL caching and pagination helper.
  - Live ONS integration path for `ons_data.query` (dataset/edition/version) gated by `ONS_LIVE_ENABLED`.
  - `ons_data.dimensions` tool (sample & live modes) including live version metadata fetch + per-dimension options and single-dimension optimization.

### Changed
- Unified retry + error normalization via shared OS client (`os_common.OSClient`).
- Settings migrated to Pydantic v2 style (removed deprecated inner `Config`).
- README overhauled with testing & contributing guidance.

### Fixed
- Upstream TLS / connect / timeout failures for `os_places.by_postcode` mapped to explicit codes (`UPSTREAM_TLS_ERROR`, `UPSTREAM_CONNECT_ERROR`).
- Added certificate bundle assurance in container for reliable SSL.
- Removed duplicate Epic listings & inconsistent changelog categories.

## [0.1.0] - 2025-08-20
- Project bootstrapped with core MCP endpoints and infra
