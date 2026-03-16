# Road Stat USRN Integration Task Brief (2026-03-16)

## 1. Objective

This brief defines the first `mcp-geo` implementation for USRN-level street-data
access using the published Road Stat API documentation and the GeoPlace blog
post from 9 March 2026 as the business context for the work.

This is a runtime-tools task, not just research packaging. The goal is to add a
small, explicit `road_stat` capability surface that fits the repo's existing MCP
tooling patterns and can later support richer street-data workflows.

## 2. Background and Why This Matters

GeoPlace's March 2026 argument is that Local Street Gazetteer quality is no
longer an administrative overhead. It is becoming an operational and financial
control because street-data quality now affects reporting burden, funding
assurance, and the ability to move from reactive to proactive highways
management.

The immediate policy backdrop is the shift away from periodic, manual `R199B`
road-length collection toward more data-driven national workflows. GeoPlace's
position is that the Department for Transport will increasingly rely on current,
maintained street data, including maintenance responsibility captured by local
street custodians, rather than on intermittent manual returns. That makes data
quality directly relevant to statistics, planning, and funding credibility.

The current repo already reflects this use case in its stakeholder and
evaluation material. It describes maintainable-road and road-length questions as
important public-sector scenarios, and it already cites GeoPlace's streets work
as evidence that spreadsheet-heavy and manually collected highways processes are
being displaced by better data products. The runtime, however, has no dedicated
streetworks or permit-history tools today. There is no first-class MCP surface
for USRN-level promoter activity or permit history.

Road Stat is relevant because it narrows that gap in a practical way. Its
published documentation presents a small research API that aggregates Street
Manager activity at USRN level and exposes two immediately useful views:
street-level permit history over fiscal years and street-level promoter
activity. That is a good fit for `mcp-geo` because it complements the repo's
existing OS, ONS, NOMIS, route, and admin tooling rather than duplicating it.

Version 1 should remain intentionally narrow. The public Road Stat docs only
publish two USRN-level endpoint contracts. They do not publish a broader
analytics model, a public base URL contract, or a robust street-name lookup
story. The first implementation should therefore be explicit, bounded, and
honest about what it does and does not cover.

## 3. Inputs Reviewed

- GeoPlace blog:
  - [Where street data quality is not an overhead but a financial control](https://www.geoplace.co.uk/blog/where-street-data-quality-is-not-an-overhead-but-a-financial-control)
- Road Stat docs:
  - [Overview](https://chriscarlon.github.io/road-stat-docs/)
  - [Endpoints](https://chriscarlon.github.io/road-stat-docs/endpoints)
- Existing repo references:
  - `/Users/crpage/repos/mcp-geo/docs/reports/MCP-Geo_evaluation_questions.md`
  - `/Users/crpage/repos/mcp-geo/docs/reports/MCP-Geo Phase 2 evidence-backed benchmark and positioning framework for blocked and hard-to-answer U.md`
  - `/Users/crpage/repos/mcp-geo/server/mcp/tool_search.py`
  - `/Users/crpage/repos/mcp-geo/tools/os_mcp.py`

## 4. Current Repo State

- No existing `road_stat` or dedicated street-data runtime tool prefix exists.
- The repo already supports OS, ONS, NOMIS, route, admin, resource, and
  discovery patterns that a Road Stat integration should follow rather than
  bypass.
- Existing routing and discovery infrastructure in
  `/Users/crpage/repos/mcp-geo/server/mcp/tool_search.py` and
  `/Users/crpage/repos/mcp-geo/tools/os_mcp.py` can support a new prefix,
  keyword set, toolset, and intent classification path.
- Existing repo evidence already frames street-data and maintainability
  questions as important stakeholder scenarios. In particular, the evaluation
  pack and Phase 2 stakeholder framework already describe road-length,
  maintainability, and spreadsheet-replacement questions as meaningful
  public-sector use cases.

## 5. Scope and Constraints

- Scope includes new MCP runtime tools, config, discovery and routing updates,
  docs, and tests.
- Scope excludes UI widgets, map rendering, exports or resources, and broader
  maintainability or funding analytics in v1.
- Scope excludes best-effort street-name resolution in v1.
- Constraint: inputs are USRN-first only.
- Constraint: live Road Stat access is config-driven and may be unavailable in
  most environments.
- Constraint: do not invent upstream semantics beyond the published contracts.
- Constraint: all new behavior must be test-covered and must not regress HTTP or
  STDIO tool calling.

## 6. Target Deliverables

- `road_stat.descriptor`
- `road_stat.usrn_info`
- `road_stat.usrn_history`
- new Road Stat env and config settings
- discovery and tool-search updates for `road_stat`
- `os_mcp.route_query` support for street-data intent
- pytest coverage for tools, routing, and transport compatibility
- docs updates for configuration and discovery
- report index entry in `docs/reports/README.md`

## 7. Public Interfaces

### `road_stat.descriptor`

Reports enabled and configured state, source links, the USRN-first requirement,
available tools, and missing configuration items.

### `road_stat.usrn_info`

- Input: numeric `usrn`
- Output aligned to published `/usrn-info`:
  - `usrn`
  - `highway_authority_swa_code`
  - `highway_authority`
  - `street_name`
  - `promoters`
  - `live`

### `road_stat.usrn_history`

- Input: numeric `usrn`
- Output aligned to published `/usrn-history`:
  - `usrn`
  - `fiscal_years`
  - `live`

## 8. Configuration Model

Planned settings:

- `ROAD_STAT_LIVE_ENABLED=false`
- `ROAD_STAT_USRN_INFO_URL_TEMPLATE=""`
- `ROAD_STAT_USRN_HISTORY_URL_TEMPLATE=""`
- `ROAD_STAT_API_TOKEN=""`
- `ROAD_STAT_HTTP_TIMEOUT_CONNECT_SECONDS`
- `ROAD_STAT_HTTP_TIMEOUT_READ_SECONDS`
- `ROAD_STAT_HTTP_RETRIES`

Key design choice:

- use URL templates with a required `{usrn}` placeholder because the public docs
  do not publish a canonical base URL or request syntax

This is deliberately more explicit than a plain base URL setting. The public
Road Stat documentation describes response contracts but does not publish a
stable request pattern or operator-ready host contract. Template-driven config
keeps v1 honest and avoids hard-coding guesses about query strings, path
segments, or other request semantics.

## 9. Behavioral Rules

- numeric USRN validation only
- `LIVE_DISABLED` when live mode is off
- `NOT_CONFIGURED` when URL templates are absent or invalid
- `USRN_NOT_FOUND` when upstream has no matching street
- normalized upstream timeout, connection, and invalid-response errors
- optional bearer token header only when configured
- no derived road-length, maintainability, funding, or routing analysis in v1
- no street-name-to-USRN resolver in v1

The first implementation should stay close to the published Road Stat fields and
should not imply that `mcp-geo` can already answer the broader highways
questions described in the stakeholder material. Those broader questions remain
important, but they belong to later tasks once the runtime has a stable USRN
street-data foundation.

## 10. Discovery and Routing

Required discovery work:

- add `road_stat` search keywords around `usrn`, `street works`, `permits`,
  `promoters`, `closures`, and `emergency`
- add a `street_works` toolset containing `road_stat.*`
- classify `road_stat` under the existing utility category in tool search
- do not add it to starter or default toolsets
- add `STREET_DATA` intent handling in `os_mcp.route_query`
- when the query lacks a numeric USRN, `route_query` should return guidance
  rather than fake a street match

This keeps the capability discoverable without pretending that the repo already
has a reliable street-name-to-USRN resolver. The routing layer should be clear
that v1 is authoritative only when the caller already has the street's USRN.

## 11. Tests and Acceptance

- descriptor works in disabled, partially configured, and configured states
- `usrn_info` and `usrn_history` success paths are fixture-tested
- invalid USRN, 404, timeout, non-JSON, and malformed-upstream cases are
  covered
- authenticated MCP HTTP, raw `/tools/call`, and STDIO all handle sanitized
  names correctly
- tool search and toolset filtering expose `road_stat.*`
- `os_mcp.route_query` recommends the new tools for streetworks queries
- no live Road Stat dependency is required in CI

Acceptance for this task is implementation-readiness: another engineer or agent
should be able to build the Road Stat v1 surface from this brief without having
to decide the scope, public contracts, config model, or test expectations from
scratch.

## 12. Recommended Follow-on Work

- street-name-to-USRN resolution
- richer Street Manager analytics and derived aggregates
- maintainability and road-length workflows tied to stakeholder scenarios
- map-assisted inspection or operator UI
- evaluation scenario upgrades once live upstream access exists

## Notes for the Implementer

The business case for this work is broader than the v1 tool surface. The
GeoPlace article and the repo's existing stakeholder material point toward a
future capability area around maintainability, road-length assurance,
spreadsheet-replacement workflows, and upstream data quality feedback. That is
useful context, but it should not be collapsed into the first delivery.

The correct first move is a minimal, well-bounded USRN integration that gives
`mcp-geo` a credible street-data foothold while preserving clear upgrade paths
for later tasks.
