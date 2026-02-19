# Peatland Survey Reliability Implementation Plan (2026-02-19)

## Objective

Translate Section F ("Prioritised implementation roadmap") from:

- `/Users/crpage/repos/mcp-geo/troubleshooting/Forensic and Methodological Deep Research Study for an MCP Geospatial Server.md`

into a dependency-aware, implementation-ready program for MCP Geo so the
question:

- "Do a peatland site survey on the forrest of Bowland"

is answerable reliably in production and demos.

## Scope and constraints

- Scope: implementation planning and tracking for server/tool/resource changes,
  tests, and documentation.
- Scope includes: HTTP and STDIO transport behavior, tool contracts, routing,
  payload delivery behavior, and data-source integration planning.
- Constraint: maintain backward compatibility for existing clients where
  feasible; if behavior changes, include explicit migration notes and tests.
- Constraint: no silent contract regressions for `os_features.query`.
- Constraint: all new behavior must be covered by tests in `tests/`.

## Inputs reviewed

- `/Users/crpage/repos/mcp-geo/troubleshooting/Forensic and Methodological Deep Research Study for an MCP Geospatial Server.md`
- `/Users/crpage/repos/mcp-geo/troubleshooting/claude-stopped-after-ngd-features.md`
- `/Users/crpage/repos/mcp-geo/troubleshooting/claude-floor-questions-harness-report-2026-02-18.md`

## Completion criteria

The program is complete when all are true:

1. `os_features.query` count semantics are correct and test-covered for empty,
   partial, and paged responses.
2. Request guardrails prevent high-risk defaults (oversized limits, geometry
   overuse, oversized bboxes) unless explicitly requested.
3. Large results are delivered with `inline|resource|auto` behavior that avoids
   host truncation/context overload.
4. Polygon input validation is deterministic and returns explicit error codes.
5. Filter provenance (`upstream` vs `local`) and scan-budget behavior are
   transparent to users.
6. Protected-landscape boundary lookup for Forest of Bowland is available via
   first-class tools/resources.
7. Peatland-specific evidence layers are discoverable and queryable (or have an
   explicit phased fallback where licensing/format blocks live query).
8. Survey-intent routing produces safe default tool plans for peatland queries.
9. Golden tests reproduce the floor-question scenario with stable, bounded
   payload behavior.
10. `PROGRESS.MD`, `CONTEXT.md`, and docs remain synchronized.

## Program board

Legend: pending, in_progress, done

| ID | Status | Dependencies | Primary outcome |
| --- | --- | --- | --- |
| PSR-INT-0 | pending | none | Shared contract freeze and integration scaffolding for survey-hardening workstreams. |
| PSR-COR-1 | pending | PSR-INT-0 | Correct `numberReturned`/`count` behavior and pagination semantics. |
| PSR-GRD-2 | pending | PSR-INT-0 | Safe request defaults and hard caps (`limit`, geometry, bbox complexity). |
| PSR-REL-3 | pending | PSR-INT-0 | Configurable timeout/retry/degrade policy for upstream failures. |
| PSR-RES-4 | pending | PSR-INT-0 | Resource-backed delivery for oversized tool payloads. |
| PSR-GEO-5 | pending | PSR-INT-0 | Polygon validation/normalization with deterministic errors. |
| PSR-CQL-6 | pending | PSR-COR-1, PSR-GRD-2 | Explicit filter provenance and scan-budget reporting. |
| PSR-BND-7 | pending | PSR-INT-0 | Protected-landscape boundary lookup tools/resources (AONB and related). |
| PSR-ROU-8 | pending | PSR-GRD-2, PSR-BND-7 | Survey-intent routing and safe-by-default execution plans. |
| PSR-PEA-9 | pending | PSR-BND-7 | Peat-specific evidence-layer integration (extent/depth/condition/erosion proxies). |
| PSR-E2E-10 | pending | all above | Golden scenario tests, docs alignment, demo-readiness sign-off. |

## Shared contract deltas (target)

These are the intended behavioral contracts for implementation streams.

### `os_features.query` response semantics

- `numberReturned` MUST equal `len(features)` for every response.
- `count` MUST be documented and stable. Preferred: alias to returned count.
- `numberMatched` SHOULD be present when upstream provides reliable total
  matches; omit or set null otherwise.
- `nextPageToken` behavior MUST remain backward compatible.

Proposed response shape extension:

```json
{
  "count": 0,
  "numberReturned": 0,
  "numberMatched": null,
  "nextPageToken": null,
  "hints": {
    "warnings": ["RESULT_LIMIT_CLAMPED"],
    "filterApplied": "upstream",
    "scan": {
      "mode": "none",
      "pagesScanned": 0,
      "pageBudget": 0,
      "partial": false
    }
  }
}
```

### Guardrail defaults

- Clamp `limit` to upstream max (`<=100` for OS NGD Features).
- Default `includeGeometry=false` unless explicitly requested.
- Default minimal `includeFields` where tool supports field projection.
- Add warnings when clamps/degradation are applied.

### Large payload delivery

- Honor `delivery=inline|resource|auto` for large results.
- For payloads above threshold:
  - return compact summary inline, and
  - emit retrievable `resource://mcp-geo/...` artifact reference.

## Workstreams

### PSR-INT-0: Contract freeze and scaffolding

Dependencies: none

Scope:
- Freeze shared response conventions for counts/paging/warnings.
- Define common guardrail utilities and warning code taxonomy.
- Define shared resource-export helper use for feature-heavy outputs.

Deliverables:
- `/Users/crpage/repos/mcp-geo/tools/os_common.py` (shared guardrail and warning helpers)
- `/Users/crpage/repos/mcp-geo/tools/os_delivery.py` (reuse/extend resource delivery helpers)
- `/Users/crpage/repos/mcp-geo/server/config.py` (new config keys)
- `/Users/crpage/repos/mcp-geo/docs/spec_package/06_api_contracts.md` (contract updates)

Acceptance:
- Shared helper APIs are stable enough for downstream streams.
- New config keys documented with defaults and bounds.

Verification:
- Unit tests for clamp/warning helper behavior.
- Contract-shape tests for warning payload inclusion.

---

### PSR-COR-1: Count and pagination correctness

Dependencies: PSR-INT-0

Scope:
- Fix mismatched `numberReturned` behavior in empty-result paths.
- Ensure consistency across `resultType=hits` and full-feature responses.
- Add explicit behavior docs for `count`, `numberReturned`, and `numberMatched`.

Deliverables:
- `/Users/crpage/repos/mcp-geo/tools/os_features.py`
- `/Users/crpage/repos/mcp-geo/tests/test_os_features.py`
- `/Users/crpage/repos/mcp-geo/tests/test_tool_upstream_endpoint_contracts.py`

Acceptance:
- Empty result sets report `numberReturned=0`.
- Partial pages report `numberReturned` equal to actual returned features.
- No regressions in existing NGD query behavior.

Verification:
- New/updated pytest cases for:
  - empty filtered result
  - limit-clamped result
  - multi-page result with next token

---

### PSR-GRD-2: Query guardrails and thin defaults

Dependencies: PSR-INT-0

Scope:
- Enforce hard max `limit` and sanitize invalid limit values.
- Add optional bbox-area guardrail with warning/degrade path.
- Default to thin mode: no geometry + minimal fields unless requested.

Deliverables:
- `/Users/crpage/repos/mcp-geo/tools/os_features.py`
- `/Users/crpage/repos/mcp-geo/server/config.py`
- `/Users/crpage/repos/mcp-geo/docs/troubleshooting.md`
- `/Users/crpage/repos/mcp-geo/docs/examples.md`

Acceptance:
- Requests over max limit no longer pass through unchecked.
- Large-area queries degrade predictably with warnings.

Verification:
- Unit tests for limit clamp and warning injection.
- Regression test proving explicit `includeGeometry=true` still honored.

---

### PSR-REL-3: Timeout/retry/degrade policy

Dependencies: PSR-INT-0

Scope:
- Separate connect and read timeout settings.
- Retry idempotent upstream requests with bounded backoff.
- Add degrade sequence on repeated timeout:
  1. reduce bbox,
  2. lower limit,
  3. disable geometry.

Deliverables:
- `/Users/crpage/repos/mcp-geo/tools/os_common.py`
- `/Users/crpage/repos/mcp-geo/tools/os_features.py`
- `/Users/crpage/repos/mcp-geo/server/config.py`
- `/Users/crpage/repos/mcp-geo/tests/test_os_common.py`
- `/Users/crpage/repos/mcp-geo/tests/test_os_features.py`

Acceptance:
- Timeout failures return normalized errors with degrade hints.
- Retry policy is bounded and deterministic.

Verification:
- Mocked upstream timeout tests covering retry/exhaustion/degrade signals.

---

### PSR-RES-4: Large payload resource delivery

Dependencies: PSR-INT-0

Scope:
- Route oversized feature outputs to resource-backed artifacts.
- Return summary-only inline payload plus resource URI in auto/resource modes.
- Track artifact TTL, bytes, and checksum metadata.

Deliverables:
- `/Users/crpage/repos/mcp-geo/tools/os_features.py`
- `/Users/crpage/repos/mcp-geo/tools/os_delivery.py`
- `/Users/crpage/repos/mcp-geo/server/mcp/resource_catalog.py`
- `/Users/crpage/repos/mcp-geo/tests/test_os_features.py`
- `/Users/crpage/repos/mcp-geo/tests/test_resource_catalog.py`

Acceptance:
- No large unbounded inline payloads for configured threshold crossings.
- Resource retrieval path works through both HTTP and STDIO flows.

Verification:
- Tests for `delivery=inline|resource|auto`.
- Artifact lifecycle tests (`bytes`, `sha256`, expiry metadata).

---

### PSR-GEO-5: Polygon validation and normalization

Dependencies: PSR-INT-0

Scope:
- Validate polygon closure, coordinate ranges, and minimum ring length.
- Normalize accepted polygon representations.
- Reject invalid geometry with explicit error codes/messages.

Deliverables:
- `/Users/crpage/repos/mcp-geo/tools/os_features.py`
- `/Users/crpage/repos/mcp-geo/tools/os_common.py` (or new `tools/geo_validation.py`)
- `/Users/crpage/repos/mcp-geo/tests/test_os_features.py`

Acceptance:
- Invalid polygons fail fast with deterministic errors.
- Valid polygon input remains backward compatible.

Verification:
- Unit tests for malformed rings, non-closed rings, and excessive vertex count.

---

### PSR-CQL-6: Filter provenance and scan-budget transparency

Dependencies: PSR-COR-1, PSR-GRD-2

Scope:
- Distinguish upstream CQL filtering from local post-filtering in responses.
- Add scan-budget reporting when local filtering scans multiple pages.
- Expose partial-scan warning states.

Deliverables:
- `/Users/crpage/repos/mcp-geo/tools/os_features.py`
- `/Users/crpage/repos/mcp-geo/docs/spec_package/06_api_contracts.md`
- `/Users/crpage/repos/mcp-geo/tests/test_os_features.py`

Acceptance:
- Response metadata includes `filterApplied` and scan status when relevant.
- Partial scans are explicit; no silent partial behavior.

Verification:
- Mocked tests for upstream filter success and local fallback scan mode.

---

### PSR-BND-7: Protected-landscape boundaries

Dependencies: PSR-INT-0

Scope:
- Add first-class lookup for AONB/National Landscapes and related protected
  boundaries, starting with Forest of Bowland coverage.
- Provide name search and geometry retrieval tools/resources.
- Maintain provenance metadata for source dataset and update timestamp.

Deliverables:
- New tool module(s), for example:
  - `/Users/crpage/repos/mcp-geo/tools/os_landscape.py`
- Resource data/catalog updates, for example:
  - `/Users/crpage/repos/mcp-geo/resources/protected_landscapes*.json`
  - `/Users/crpage/repos/mcp-geo/server/mcp/resource_catalog.py`
- Tool registration:
  - `/Users/crpage/repos/mcp-geo/server/mcp/tools.py`
- Tests:
  - `/Users/crpage/repos/mcp-geo/tests/test_os_landscape.py`

Acceptance:
- Querying "Forest of Bowland" resolves a protected-landscape polygon without
  falling back to an electoral ward.

Verification:
- Golden fixture test for Bowland lookup and geometry retrieval.

---

### PSR-ROU-8: Environmental survey routing

Dependencies: PSR-GRD-2, PSR-BND-7

Scope:
- Extend routing guidance so survey-intent questions produce safe tool plans:
  AOI first, counts first, geometry last.
- Add explicit routing hints for peatland, habitat, and flood-style survey intents.

Deliverables:
- `/Users/crpage/repos/mcp-geo/tools/os_mcp.py`
- `/Users/crpage/repos/mcp-geo/tests/test_os_mcp.py`
- `/Users/crpage/repos/mcp-geo/docs/examples.md`
- `/Users/crpage/repos/mcp-geo/docs/troubleshooting.md`

Acceptance:
- `os_mcp.route_query` (or companion routing tool) returns survey-safe sequence
  and parameter defaults for peatland prompts.

Verification:
- Evaluation questions and route-query tests for survey intent mapping.

---

### PSR-PEA-9: Peat-specific evidence layers

Dependencies: PSR-BND-7

Scope:
- Integrate peat-oriented layers as discoverable MCP resources/tools.
- Support at minimum metadata discovery + AOI query strategy.
- If full live query is blocked by source/format constraints, ship explicit
  phased fallback plan with stable interfaces.

Deliverables:
- New tool module(s), for example:
  - `/Users/crpage/repos/mcp-geo/tools/os_peat.py`
- Resource and metadata entries:
  - `/Users/crpage/repos/mcp-geo/resources/peat_layers*.json`
  - `/Users/crpage/repos/mcp-geo/server/mcp/resource_catalog.py`
- Tests:
  - `/Users/crpage/repos/mcp-geo/tests/test_os_peat.py`

Acceptance:
- Users can discover peat-related layers and obtain AOI-scoped evidence paths.

Verification:
- Unit tests for layer discovery/query contracts.
- Evidence-path regression using Bowland AOI fixture.

---

### PSR-E2E-10: Golden scenario and release-readiness

Dependencies: all prior workstreams

Scope:
- Add deterministic end-to-end scenario tests for the floor question.
- Validate behavior across STDIO and HTTP flows.
- Publish a concise runbook for demo execution and expected outputs.

Deliverables:
- `/Users/crpage/repos/mcp-geo/tests/evaluation/questions.py`
- `/Users/crpage/repos/mcp-geo/tests/test_evaluation_harness_full.py`
- New scenario fixture(s) under:
  - `/Users/crpage/repos/mcp-geo/tests/fixtures/`
- Documentation updates:
  - `/Users/crpage/repos/mcp-geo/docs/examples.md`
  - `/Users/crpage/repos/mcp-geo/docs/troubleshooting.md`
  - `/Users/crpage/repos/mcp-geo/PROGRESS.MD`

Acceptance:
- Golden question completes without host-breaking payload behavior.
- Output includes AOI provenance, peat evidence/proxy separation, confidence,
  and explicit caveats.

Verification:
- Full regression: `pytest -q`.
- Focused eval run for survey scenarios.

## Integration ownership and conflict control

Integration-owned hot files (to reduce merge conflict risk):

- `/Users/crpage/repos/mcp-geo/server/config.py`
- `/Users/crpage/repos/mcp-geo/server/mcp/tools.py`
- `/Users/crpage/repos/mcp-geo/server/mcp/resource_catalog.py`
- `/Users/crpage/repos/mcp-geo/PROGRESS.MD`
- `/Users/crpage/repos/mcp-geo/CONTEXT.md`
- `/Users/crpage/repos/mcp-geo/CHANGELOG.md`

Feature streams should hand off requested edits to these files through the
integration stream.

## Milestones and execution order

1. Milestone M0: `PSR-INT-0` contract freeze.
2. Milestone M1: correctness + guardrails (`PSR-COR-1`, `PSR-GRD-2`, `PSR-REL-3`).
3. Milestone M2: payload and geometry hardening (`PSR-RES-4`, `PSR-GEO-5`, `PSR-CQL-6`).
4. Milestone M3: survey data/routing enablement (`PSR-BND-7`, `PSR-ROU-8`, `PSR-PEA-9`).
5. Milestone M4: end-to-end scenario readiness (`PSR-E2E-10`).

## Risks and mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Upstream source instability for protected landscape and peat datasets | Delays in `PSR-BND-7`/`PSR-PEA-9` | Ship source adapters behind capability flags and preserve resource-backed fallback contracts. |
| Contract changes break strict clients | Regression in Claude/other hosts | Add transport parity tests and preserve backward-compatible fields during transition. |
| Large payload fallback still too heavy for host | Persistent response truncation | Lower inline threshold, prioritize summary mode, and force resource handoff in auto mode. |
| Ambiguous filter provenance when mixed modes occur | Misleading analytical confidence | Explicit `filterApplied` and scan metadata with warning codes for partial scans. |
| Scope expansion across many tools | Delivery slippage | Keep strict milestone gates and defer non-critical enhancements after `PSR-E2E-10`. |

## Open decisions to resolve before implementation

1. Confirm primary authoritative source(s) for protected landscape boundaries in
   runtime integrations (Planning Data vs Natural England vs cached package).
2. Confirm whether peat-layer access is live-query, cached package, or hybrid
   for initial release.
3. Approve final warning/error code taxonomy for guardrail and degrade states.
4. Set default inline payload threshold for `os_features.query` in STDIO-heavy
   environments.

