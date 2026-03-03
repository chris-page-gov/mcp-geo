# Deep Analysis Report: Peat Survey Failure Chain (Forest of Bowland)

Date: 2026-03-03  
Scope: Failure modes in `docs/MCP-Geo Peatland Site Survey - Forest of Bowland National Landscape.md`, including the Claude trace section where proxy and transport queries diverged/faulted.

## Artifacts Reviewed

- Source conversation markdown:
  - `docs/MCP-Geo Peatland Site Survey - Forest of Bowland National Landscape.md`
- Transport trace:
  - `logs/claude-trace.jsonl`
- Evidence extraction:
  - `troubleshooting/peat-survey-trace-evidence-2026-03-03.md`
- Relevant implementation:
  - `tools/os_features.py`
  - `tools/os_peat.py`
  - `tools/os_common.py`
- Existing troubleshooting guidance:
  - `docs/troubleshooting.md`

## Failure Timeline (Evidence-Linked)

1. `os_peat_evidence_paths` produced valid AOI and proxy query plans (`wtr-fts-water-3`, `lnd-fts-land-3`).
- Conversation evidence: `...Forest of Bowland National Landscape.md:124`
- Transport evidence: `logs/claude-trace.jsonl:4832`

2. Hydrology `hits` query returned `count=0` with `numberMatched=null`.
- Conversation evidence: `...Forest of Bowland National Landscape.md:146`
- Transport evidence: `logs/claude-trace.jsonl:4834`

3. Same collection/AOI in `results` mode immediately returned `count=25`.
- Conversation evidence: `...Forest of Bowland National Landscape.md:160`
- Transport evidence: `logs/claude-trace.jsonl:4836`

4. Claude then attempted `collection=trn-fts-roadlink-1` and received unsupported-collection 404 (`OS_API_ERROR`).
- Conversation evidence: `...Forest of Bowland National Landscape.md:232`, `:236`
- Transport evidence: `logs/claude-trace.jsonl:4839`, `:4841`

5. Recovery was manual by calling `os_features.collections` and selecting path-related collections.
- Conversation evidence: `...Forest of Bowland National Landscape.md:250`
- Transport evidence: `logs/claude-trace.jsonl:4843`

## Root Causes

### RC1: `os_features.query` `resultType="hits"` count semantics were incorrect

Observed behavior:
- Response `count` was computed from `numberReturned` (which is `0` in `hits` mode because feature payloads are intentionally omitted), not from matched features.
- When upstream omitted `numberMatched`, `count` misleadingly reported zero even when upstream returned features in the same request.

Impact:
- Model inferred no hydrology features existed in AOI, then retried with `resultType="results"` to compensate.
- This undermined the intended bounded-proxy query flow emitted by `os_peat.evidence_paths`.

### RC2: Missing compatibility alias for legacy/mistyped transport collection IDs

Observed behavior:
- `trn-fts-roadlink-1` failed as unsupported, while valid modern transport collections exist (`trn-ntwk-roadlink-*`, `trn-fts-roadtrackorpath-*`, `trn-ntwk-pathlink-*`).

Impact:
- Transport layer analysis faulted despite availability of equivalent datasets.
- Recovery depended on an additional discovery call and model self-correction.

### RC3: Unsupported-collection errors were not actionable

Observed behavior:
- Error payload surfaced raw upstream text but did not include structured candidate collections.

Impact:
- Extra recovery turns were needed (`os_features.collections` + human/model interpretation).
- Client could not automatically repair query with deterministic suggestion data.

## Implementation Plan

### Workstream PSF-INT-1: Correct `hits` count semantics

1. Compute `count` in `hits` mode from the best available matched signal, not `numberReturned`.
2. Use `numberMatched` when upstream provides it.
3. Else use observed feature volume as matched estimate (`len(raw_features)` or local-filter total).
4. Add warnings when counts are lower-bound/derived:
- `HITS_COUNT_LOWER_BOUND`
- `HITS_NUMBER_MATCHED_UNAVAILABLE`

Status: done

### Workstream PSF-INT-2: Add transport collection compatibility aliasing

1. Introduce base alias mapping for legacy transport naming:
- `trn-fts-roadlink-*` -> `trn-ntwk-roadlink-*`
2. Keep existing explicit aliases (`buildings`) intact.
3. Preserve `requestedCollection` in responses for transparency.

Status: done

### Workstream PSF-INT-3: Enrich unsupported-collection errors with guidance

1. Detect unsupported-collection text in `OS_API_ERROR` payloads.
2. Query live collection catalog (`/collections`) to derive candidate suggestions.
3. Attach structured fields to error payload:
- `requestedCollection`
- `resolvedCollection` (when alias applied)
- `upstreamUnsupportedCollection` (when upstream reports a different id)
- `suggestedCollections`
- `hint`

Status: done

### Workstream PSF-DOC-4: Keep docs/tracking in lockstep

1. Add deep report and trace-evidence artifact in `troubleshooting/`.
2. Update `docs/troubleshooting.md` with new `os_features.query` remediation guidance.
3. Update `PROGRESS.MD`, `CONTEXT.md`, and `CHANGELOG.md`.

Status: done

## Changes Implemented

### Code

- `tools/os_features.py`
  - Added collection compatibility helpers:
    - `_apply_collection_alias`
    - `_COLLECTION_BASE_ALIASES`
  - Added unsupported-collection guidance helpers:
    - `_extract_unsupported_collection`
    - `_suggest_collections_for_request`
    - `_augment_unsupported_collection_error`
  - Fixed `hits` count semantics:
    - `count` no longer mirrors `numberReturned` in `hits` mode.
    - emits `HITS_NUMBER_MATCHED_UNAVAILABLE` and lower-bound warnings where applicable.

### Tests

- `tests/test_os_features_collections.py`
  - Updated `test_os_features_query_result_type_hits` for corrected behavior.
  - Added `test_os_features_query_hits_without_numbermatched_uses_feature_count`.
  - Added `test_os_features_query_aliases_legacy_transport_collection`.
  - Added `test_os_features_query_unsupported_collection_returns_suggestions`.

### Documentation

- Added:
  - `troubleshooting/peat-survey-trace-evidence-2026-03-03.md`
  - `troubleshooting/peat-survey-failure-deep-analysis-2026-03-03.md` (this report)
- Updated:
  - `docs/troubleshooting.md`
  - `PROGRESS.MD`
  - `CONTEXT.md`
  - `CHANGELOG.md`

## Verification

Commands run:

```bash
uv run --with pytest --with pytest-cov pytest -q --no-cov tests/test_os_features_collections.py tests/test_os_peat.py tests/test_os_tools_normalization.py
```

Result:
- `38 passed` (combined focused suite for `os_features`, peat tooling, and tool normalization)

## Expected Behavior After Fix

1. `resultType="hits"` no longer reports false-zero counts purely due to omitted feature payloads.
2. Legacy `trn-fts-roadlink-*` requests are normalized to supported `trn-ntwk-roadlink-*` IDs.
3. Unsupported collection errors include structured candidate collections and repair hints to reduce recovery turns.

## Residual Risks

- Upstream OS responses may still omit global `numberMatched`; in those cases count can remain estimate/lower-bound and should be treated with the emitted warning metadata.
- Collection availability/entitlement is key-dependent; suggestions improve repairability but cannot bypass entitlement restrictions.
