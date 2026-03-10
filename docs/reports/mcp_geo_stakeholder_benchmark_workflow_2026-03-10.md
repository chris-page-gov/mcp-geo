# MCP-Geo Stakeholder Benchmark Workflow Validation

Date: 2026-03-10

This report captures the standard repeatable workflow using scenario 1 as the end-to-end proof case.

## Workflow

1. Curate a real public geospatial anchor and decide whether any protected data must be synthetic.
2. Freeze the scenario prompt with the common header and concrete inputs.
3. Write machine-readable fixture files and a scored reference output.
4. Run pack validation and score the reference output.
5. Render the human-readable markdown pack from the machine source.
6. Use the same structure for the remaining scenarios so they stay consistent.

## Scenario 1 Proof Case

- Scenario: `Affected premises and vulnerable households in an incident area`
- Fixtures: data/benchmarking/stakeholder_eval/fixtures/scenario_01_incident_zone.wkt, data/benchmarking/stakeholder_eval/fixtures/scenario_01_vulnerable_households.csv
- Example mode: `mixed`
- Reference score: `100/100 (excellent)`

## Score Breakdown

| Dimension | Earned | Max | Detail |
| --- | ---: | ---: | --- |
| answer_contract | 20 | 20 | common=6/6 scenario=5/5 |
| geospatial_grounding | 20 | 20 | core operational fields present |
| identifier_integrity | 15 | 15 | identifier keyword hits=6 |
| evidence_alignment | 15 | 15 | required term hits=5/5 |
| uncertainty | 10 | 10 | confidence caveats present |
| verification_exports | 10 | 10 | verification/export guidance present |
| dataset_traceability | 10 | 10 | datasets/tools listed |

## Validation Outcome

- Pack valid: `True`
- Validation errors: `0`

## Repeatable Guidance

Use the same pattern for every new stakeholder benchmark case:
- pick a public example whenever the exact input can be published safely
- only introduce synthetic data to cover privacy, licensing, or missing public detail
- carry the synthetic flag into the prompt, expected output, and scoring notes
- keep the scorecard machine-readable so the markdown pack is always regenerated from source
