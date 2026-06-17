### Added
- Added normalized `PARISH`/PARNCP geography support across ONS geography cache
  lookups, area summaries, admin boundary lookup, and route guidance.
- Added House of Commons Library 2021 MSOA names as display-only sidecar labels
  with source provenance while preserving official ONS/RGC MSOA names.

### Changed
- Routed OS Names gazetteer and named-place wording to `os_names.find` while
  keeping generic boundary/admin phrases on `admin_lookup.*`.
- Centralized geography-level aliases, code-prefix inference, admin routing,
  selector levels, stats comparison levels, NOMIS geography-type hints, and
  export selector columns in `server/geography_levels.py`.
- Slimmed active agent handoff files and moved historical/client-review guidance
  into `docs/agent_context/`.

### Fixed
- Fixed parish/PARNCP geography selector routing so interactive parish prompts
  use a selector level supported by both the tool payload and embedded widget.
- Preserved MSOA display-name fields through `ons_geo.area_summary` responses
  without replacing official `name` / `currentName` values.
- Added parish identity and `selected_by_parish` audit fields to selector-driven
  UPRN exports.
