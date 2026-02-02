# Aims and Objectives

## Aim

Deliver a production-grade MCP server for UK geospatial workflows that provides
consistent tool interfaces, structured errors, and optional MCP-Apps UIs for
interactive discovery and decision-making.

## Objectives (prototype targets)

1. **Interoperability**: Support MCP clients over both STDIO and HTTP transports,
   with protocol-compliant tool, resource, and prompt endpoints.
2. **Consistency**: Normalize all external APIs into a consistent tool schema and
   error model (`{isError, code, message, correlationId?}`).
3. **Discoverability**: Provide rich tool metadata, searchable categories, and
   intent routing via `os_mcp.route_query`.
4. **Geospatial capability**: Offer a core set of OS and ONS tools for addresses,
   boundaries, features, linked identifiers, and datasets.
5. **Caching & performance**: Maintain a PostGIS boundary cache for fast admin
   lookups; instrument freshness and cache coverage.
6. **UI acceleration**: Provide MCP-Apps UI resources for common visual tasks
   (selection, routing, inspection, statistics).
7. **Quality**: Maintain high test coverage (>=90%) and consistent logging.

## Non-goals (current prototype)

- Full offline ONS dataset mirroring (only on-disk cache for codes).
- Multi-tenant auth and role-based access control.
- Full static map rendering pipeline (maps tool is a descriptor/stub).
- CI/CD pipeline and release automation (still backlog).

## Success criteria

- All tools discoverable via `/tools/list` and `/tools/describe`.
- Boundary cache is populated; admin lookup reads from cache by default.
- MCP-Apps UI resources are served and can be opened by a UI-capable client.
- No unhandled exceptions in pipeline runs; validation covers schema and geometry.
- Observability and error taxonomy available to support diagnosis.

