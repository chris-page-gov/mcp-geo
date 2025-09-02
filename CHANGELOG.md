# Changelog

All notable changes to this project will be documented in this file.


## [Unreleased]

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
