### Added
- Added normalized `PARISH`/PARNCP geography support across ONS geography cache
  lookups, area summaries, admin boundary lookup, and route guidance.
- Added House of Commons Library 2021 MSOA names as display-only sidecar labels
  with source provenance while preserving official ONS/RGC MSOA names.

### Changed
- Routed OS Names gazetteer and named-place wording to `os_names.find` while
  keeping generic boundary/admin phrases on `admin_lookup.*`.
