# User Question Patterns and Solution Progress

## Why This Chapter Matters

The system was shaped by real user question patterns, not only by planned API coverage.

## Primary Question Families

From `tests/evaluation/questions.py`, user intent groups include:

- address and postcode lookup
- place and boundary lookup
- map render and interactive selection
- dataset discovery and statistics retrieval
- environmental survey workflows
- linked identifier and infrastructure context

```mermaid
flowchart LR
    A["User question"] --> B["Intent classification"]
    B --> C["Tool routing"]
    C --> D["Tool/resource response"]
    D --> E["Expected outcome checks"]
```

## How the Harness Was Used

The evaluation harness provided:

- fixed question bank with expected outcomes
- pass/fail and score outputs
- error and rate-limit auditing
- live-mode and offline-mode validation paths

References:

- `tests/evaluation/harness.py`
- `tests/evaluation/questions.py`
- `tests/evaluation/rubric.py`
- `docs/evaluation.md`

## Examples of Progress Triggered by Question Failures

- better dataset selection and comparability guidance (`ons_select.search`)
- explicit route/query helper improvements (`os_mcp.route_query`)
- NOMIS query normalization and auto-adjust behavior
- map and UI fallback improvements for non-UI hosts
- improved error payloads for unsupported or aliased collections

Evidence links:

- `PROGRESS.MD` sections `NQR-*`, `PSF-*`, `CT-*`, `LMR-*`
- `CHANGELOG.md`
- `docs/reports/*`
