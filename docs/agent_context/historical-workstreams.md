# Historical Workstreams

This summary replaces large historical blocks that previously lived in
`CONTEXT.md` and `PROGRESS.MD`. Use git history or the referenced plans/reports
for full detail.

## 2026-06

- Parish/PARNCP, OS Names routing, and House of Commons Library MSOA display
  names were implemented on `codex/parish-pんarncp-names-support`.
- MCP 2026-07-28 release-candidate alignment was implemented in a separate
  worktree and remains opt-in until the final spec is published.

## 2026-04

- Release `v0.8.1` fixed package contents after the `v0.8.0` stable baseline.
- ONS UPRN multi-shard ingest was fixed after cache refresh selected only one
  region shard; old local caches need rebuild before they contain all UPRNs.
- Unattended multi-client evaluation work added readiness-first scoring,
  blocker taxonomy, benchmark workspaces, and VS Code/Gemini remediation.
- ONS geo source resolution moved to resolver-driven acquisition with CHD/RGC
  sidecars, semantic normalization, and release-audit tooling.
- LandIS MVP and phase-2 surfaces added warehouse-backed Soilscapes, NATMAP,
  NSI, archive discovery, Docker/PostGIS bootstrap, and local archive support.
- AddressBase Premium Parquet runtime support added DuckDB-backed council-tax
  lookup paths and Docker image dependency alignment.

## 2026-03

- Council Tax band lookup pilot added a guarded public-form-backed tool.
- Full code review remediated raw HTTP auth, secret redaction, local wrapper
  quality gates, and OWASP validator compatibility.
- Docker MCP catalog readiness added metadata, secret placeholder handling, and
  external registry submission notes.
- Release `v0.7.0` packaged the merged benchmark, documentation, route-planning,
  playground, and MCP compatibility work.

## 2026-02

- ONS/NOMIS routing and stats comparison work added `comparisonLevel`,
  `providerPreference`, elicitation support, and traceable `userSelections`.
- Boundary, map-lab, and MCP-Apps work introduced the first selector widgets and
  map export workflows that later required geography-level parity hardening.
