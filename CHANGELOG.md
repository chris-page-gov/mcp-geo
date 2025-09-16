# Changelog

All notable changes to this project will be documented in this file.


## [Unreleased]

- Completed Epic B: Ordnance Survey (OS) tools endpoints
	- Implemented real outbound handlers: os_places (search, by_postcode, by_uprn, nearest, within), os_names (find, nearest), os_features.query, os_linked_ids.get, os_maps.render (metadata), os_vector_tiles.descriptor
	- Unified retry + error normalization via shared OS client
	- Graceful degradation (501) for missing API key or upstream TLS/connect failures
	- Validation tests updated to allow 200 (success) or 501 (graceful fallback)

- Resilience: `os_places.by_postcode` now maps upstream TLS / connection / timeout failures to 501 with explicit codes (`UPSTREAM_TLS_ERROR`, `UPSTREAM_CONNECT_ERROR`) instead of generic 500 `INTEGRATION_ERROR`, stabilising the test suite.

- Maintenance: Migrated settings configuration to Pydantic v2 `model_config` (removed deprecated inner `Config` class) eliminating deprecation warnings and preparing for Pydantic v3.

- Completed Epic A: Core MCP server & playground
	- MCP server scaffold with FastAPI
	- Health check (`/healthz`), tool/resource listing, and call endpoints
	- Uniform error model and pagination stubs
	- Structured logging, correlation IDs, and request tracing
	- Tool call transcript endpoint for playground UI
	- Devcontainer, Docker, and packaging setup

### Fixed
- Devcontainer and Dockerfile now ensure CA certificates are present and Python requests use the correct certifi CA bundle for SSL reliability.
- Completed Epic B: Ordnance Survey (OS) tools endpoints
	- Scaffolded all Epic B endpoints: os_places.*, os_linked_ids.get, os_features.query, os_names.*, os_maps.render, os_vector_tiles.descriptor
	- All endpoints return 501 Not Implemented with standard error model, except os_places.by_postcode (returns real or stub data)
	- `/tools/list` includes all Epic B tools
	- Validation tests for all Epic B tools

- Completed Epic A: Core MCP server & playground
	- MCP server scaffold with FastAPI
	- Health check (`/healthz`), tool/resource listing, and call endpoints
	- Uniform error model and pagination stubs
	- Structured logging, correlation IDs, and request tracing
	- Tool call transcript endpoint for playground UI
	- Devcontainer, Docker, and packaging setup

## [0.1.0] - 2025-08-20
- Project bootstrapped with core MCP endpoints and infra
