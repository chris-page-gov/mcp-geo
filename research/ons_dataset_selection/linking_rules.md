# MCP Geo linking rules (Phase 3)

Version: 1.0.0  
Generated at (UTC): 2026-02-07T08:04:56Z

## Purpose
Define deterministic and auditable link creation rules for tile → data card → graph navigation across ONS statistical and derived indicator datasets.

## Link types
1. `same_measure_different_geography`  
2. `same_measure_different_time_granularity`  
3. `derived_from`  
4. `complementary_context`  
5. `quality_or_revision_context`  
6. `methodological_dependency`  
7. `leading_or_lagging_indicator`

## Rule engine order (apply in sequence)

### Rule 1 — Core intent fit
Create candidate links only if:
- intent tags overlap by at least one tag, and
- geography coverage intersects, and
- time windows overlap or can be aligned.

### Rule 2 — Comparability safety gate (mandatory)
Reject or demote links where:
- geography definitions are incompatible without mapping,
- time basis differs without transformation rule,
- revision status mismatch is material and unlabelled,
- denominator definitions differ and are not disclosed.

### Rule 3 — Methodological dependency
Create `methodological_dependency` when one series is an input or denominator for another.

### Rule 4 — Derived indicators
Create `derived_from` links where the target is explicitly computed from the source series.

### Rule 5 — Context enrichment
Create `complementary_context` links for non-equivalent but decision-relevant context (e.g., wages with inflation).

### Rule 6 — Revision and quality context
Create `quality_or_revision_context` links to benchmark/final series when a faster series is provisional.

### Rule 7 — Directional economic dynamics
Create `leading_or_lagging_indicator` only with explicit rationale text; never imply causality.

## Link scoring (0–100)
`link_score = 30*intent_fit + 20*geography_fit + 15*time_fit + 15*quality_alignment + 10*method_dependency + 10*release_alignment`

Where each term is normalised to [0,1].

## Minimum fields per link edge
- `edge_id` (kebab-case)
- `from_dataset_id`
- `to_dataset_id`
- `link_type`
- `link_reason`
- `provenance`:
  - `source_name`
  - `source_url`
  - `retrieved_at`
  - `licence`
  - `method_note`
  - `quality_note`

## AI-safe output requirements
Every surfaced link must be accompanied by:
- explicit `link_reason`,
- comparability warning if present,
- revision status note for both nodes,
- latest release date for both nodes.

## Explainability templates

### Why this link
“Linked because both series address **{intent}** for **{geography}** and can be compared for **{time_window}**.”

### Why not linked
“Not linked because **{constraint}** (e.g., mismatched geography definition, non-aligned vintages, incompatible denominator).”

## Accessibility requirements
- Do not encode link semantics with colour alone.
- Provide text labels for link types.
- Provide keyboard-navigable list of related datasets.
- Offer non-graph fallback (ordered related-datasets list).

## Governance and change control
- Recompute links on each dataset refresh.
- Keep previous link set for audit (versioned snapshots).
- Record rule version and timestamp in DataPack metadata.
- Any manual override must include justification and reviewer.

## Recommended defaults for MCP Geo
- Maximum related datasets shown initially: 6
- Always show one benchmark/final series if primary is provisional
- Show at least one complementary context series
- Show zero links rather than unsafe links
