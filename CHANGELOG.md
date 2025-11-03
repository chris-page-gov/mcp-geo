# Changelog

All notable changes to this project will be documented in this file.


## [Unreleased]
### Added
- Place enrichment: `os_places.by_postcode` now returns `classificationDescription` and `localCustodianName` derived from static code list resources.
- Resource headers: `Cache-Control` added with differentiated TTL (300s for dynamic admin boundaries sample, 86400s for static code lists).
- Standardized resource provenance field `retrievedAt` across all `/resources/get` responses.

### Tests
- Added `test_os_places_enrichment.py` covering enrichment fields.
- Added `test_resources_provenance_headers.py` validating cache headers and provenance presence.

### Internal
- Minor refactor in `server/mcp/resources.py` for provenance normalization.
### Added
- STDIO adapter branch tests for parse errors (-32700), invalid version (-32600), invalid params (-32602), and ETag not-modified flow.

### Changed
- Refactor(server): move STDIO adapter implementation to `server/stdio_adapter.py` with type hints; legacy wrapper preserved.

### Fixed
- Correct handling of non-dict `params` triggering JSON-RPC -32602 Invalid params error.

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
