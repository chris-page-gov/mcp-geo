# LandIS Phase 2 Surfacing Plan

Date: 2026-04-04
Updated: 2026-04-05

## Objective

Turn the completed authenticated LandIS archive into a deliberate phase-2 MCP
surface without destabilizing the validated Warwickshire MVP. The immediate
goal is not to expose every downloaded dataset; it is to define which LandIS
families should become first-class MCP tools, which should become warehouse
tables or resources, and which should remain archive-only until a clear user
contract exists.

## Current State

The current LandIS MVP is complete and validated for Claude-hosted use:

- `landis_catalog.list_products`
- `landis_metadata.get`
- `landis_soilscapes.point`
- `landis_soilscapes.area_summary`
- `landis_derive.pipe_risk`

These tools are intentionally narrow. They support offline-safe product
catalog/metadata plus warehouse-backed Soilscapes lookup, area summaries, and
area-based pipe corrosion / shrink-swell screening.

The authenticated Atlas route is also complete:

- inventory complete: `106` portal items
- archive complete: `106` manifest results, `0` errors
- feature services mirrored: `33`
- non-feature payloads mirrored: `73`
- archive root: `/Users/crpage/Data/landis_portal_archive_2026-04-04`

The local release surface is now also complete beyond the portal itself:

- supplementary public/data.gov archive complete: `13` public items, `59`
  packages, `165` verification checks, `0` failures
- local backup roots:
  - `/Users/crpage/Data/landis_portal_archive_2026-04-04`
  - `/Users/crpage/Data/landis_full_release_archive_2026-04-05`

That means the remaining problem is no longer data acquisition. The remaining
problem is product design, normalization scope, and making the local archive
the default source of truth for follow-on LandIS work.

## 2026-04-05 Implementation Update

The first phase-2 tranche is now implemented against local data.

New runtime surfaces:

- `landis_archive.list_items`
- `landis_archive.get_item`
- `landis_natmap.point`
- `landis_natmap.area_summary`
- `landis_natmap.thematic_area_summary`
- `landis_nsi.nearest_sites`
- `landis_nsi.within_area`
- `landis_nsi.profile_summary`

New checked-in resources:

- `resource://mcp-geo/landis-portal-inventory`
- `resource://mcp-geo/landis-archive-triage`
- `resource://mcp-geo/landis-full-release-manifest`

New local-data tooling:

- `scripts/landis_archive_triage.py` creates the machine-readable archive
  triage manifest from the local portal and full-release archives
- `scripts/landis_phase2_ingest.py` loads the locally mirrored NATMAP and NSI
  datasets into the LandIS warehouse schema without going back to the portal

What this tranche does:

- makes the local archive discoverable through MCP as archive inventory and
  manifest resources
- adds a first NATMAP analytical family for point lookup and area summaries
- adds a first NSI evidence family with explicit sampling caveats
- switches phase-2 ingestion assumptions from remote portal access to local
  archive inputs under `~/Data` by default

What this tranche does not do yet:

- it does not surface NATMAP join-table enrichment (`NATMAPassociations`,
  `SOILSERIES`, `HORIZON*`) through a first-class MCP contract
- it does not add AUGER or Soil Catalogue analytical tools
- it does not assume an always-on local PostGIS sidecar; the local archive is
  the durable source, and the warehouse remains an operator-started runtime
  dependency for live spatial queries

## What The Archive Contains

The captured `33` feature services fall into five clear families.

### 1. NATMAP polygon products

These are the strongest candidates for new user-facing analytical tools because
they are generalized polygon layers suitable for point lookup, area summary,
and map-overlay workflows.

| Dataset | Records | Geometry | Likely role |
| --- | ---: | --- | --- |
| `NationalSoilMap` | 42,603 | polygon | canonical polygon map-unit surface |
| `NATMAPsoilscapes` | 34,178 | polygon | generalized screening/product surface |
| `NATMAPtopsoiltexture` | 38,102 | polygon | thematic texture summary |
| `NATMAPsubsoiltexture` | 19,973 | polygon | thematic texture summary |
| `NATMAPsubstratetexture` | 19,751 | polygon | thematic texture summary |
| `NATMAPavailablewater` | 38,097 | polygon | thematic water-capacity screening |
| `NATMAPcarbon` | 165,982 | polygon | thematic carbon screening |
| `NATMAPwrb2006` | 143 | polygon | classification crosswalk |
| `NATMAPregions` | 8 | polygon | high-level region context |
| `NATMAP1000` | 154,765 | polygon | detailed polygon coverage |
| `NATMAP2000` | 39,308 | polygon | medium-detail polygon coverage |
| `NATMAP5000` | 6,277 | polygon | coarser polygon coverage |

### 2. NATMAP join and lookup tables

These should usually not be exposed directly to end users first. They are
better treated as warehouse support tables for richer derived outputs and
provenance.

| Dataset | Records | Shape | Likely role |
| --- | ---: | --- | --- |
| `NATMAPassociations` | 1,073 | table | association-to-series join |
| `NATMAPlegend` | 306 | table | symbology and class labeling |
| `SOILSERIES` | 1,343 | table | soil-series definitions |
| `HORIZONfundamentals` | 6,591 | table | per-horizon physical properties |
| `HORIZONhydraulics` | 6,591 | table | per-horizon hydraulic properties |

### 3. NSI point evidence products

These are strong candidates for evidence-oriented and research-grade tools, but
not for generalized public screening by default. They are point-based and
should be surfaced with explicit sampling and representativeness caveats.

| Dataset | Records | Geometry | Likely role |
| --- | ---: | --- | --- |
| `NSIfeatures` | 6,124 | point | site observations |
| `NSImagnetic` | 1,955 | point | specialist evidence |
| `NSIprofile` | 20,590 | point | profile-level evidence |
| `NSIsite` | 5,706 | multipoint | site catalog/index |
| `NSItexture` | 5,686 | point | texture observations |
| `NSItopsoil1` | 5,686 | point | topsoil evidence |
| `NSItopsoil2` | 2,361 | point | topsoil evidence |

### 4. AUGER survey products

These are very large point datasets. They have clear research value, but they
need careful indexing, paging, and summary design before they become an MCP
surface.

| Dataset | Records | Geometry | Likely role |
| --- | ---: | --- | --- |
| `AUGERprofile` | 421,233 | point | detailed profile evidence |
| `AUGERsite` | 140,902 | point | site-level survey inventory |

### 5. Catalogue and reference coverage layers

These are useful for discovery and operator context, but they are weak
candidates for first-wave analytical tools.

| Dataset | Records | Geometry | Likely role |
| --- | ---: | --- | --- |
| `SoilCatalogue_100k` | 3 | polygon | coverage/reference |
| `SoilCatalogue_25k` | 134 | polygon | coverage/reference |
| `SoilCatalogue_50k` | 5 | polygon | coverage/reference |
| `SoilCatalogue_63k` | 34 | polygon | coverage/reference |
| `SoilCatalogue_FarmSurveys` | 422 | polygon | survey-coverage reference |
| `SoilCatalogue_RabbitSurveys_sites` | 45 | polygon | survey-coverage reference |
| `Portal User Survey_form` | 0 | point | operational artifact, not analytical |

## Review Of The Current Tool Design

The current MVP tool design is still correct for phase 1. It should not be
stretched to absorb the whole archive.

What should remain unchanged:

- `landis_catalog.*` stays the offline-safe entry point for inventory and
  metadata.
- `landis_soilscapes.*` stays the generalized screening layer.
- `landis_derive.pipe_risk` stays a derived screening tool with explicit
  caveats and provenance.

What should not happen next:

- do not add more unrelated NATMAP or NSI attributes to the current
  `landis_soilscapes` response shape
- do not overload `landis_metadata.get` into a full portal-browser interface
- do not surface raw archive dumps directly as tool outputs
- do not promote point-evidence datasets into generalized area-screening tools
  without sampling caveats and paging

The current design is narrow by intent. Phase 2 should add new namespaces,
rather than distort the MVP ones.

## Proposed Phase 2 Tool Surface

### A. Keep the MVP screening layer stable

No breaking changes to the current five public tools. Only additive provenance,
metadata, or implementation hardening should happen on that surface.

### B. Add a NATMAP analytical family

This should be the first new family because it builds naturally on the existing
Soilscapes and pipe-risk pattern.

Recommended phase-2 namespace:

- `landis_natmap.point`
- `landis_natmap.area_summary`
- `landis_natmap.classification_lookup`
- `landis_natmap.thematic_area_summary`

Recommended initial scope:

- polygon point lookup against `NationalSoilMap`
- area summaries across selected polygon products
- explicit thematic summaries for topsoil texture, subsoil texture,
  substrate texture, available water, and carbon
- join-backed class enrichment using `NATMAPassociations`, `SOILSERIES`,
  `HORIZONfundamentals`, and `HORIZONhydraulics`

### C. Add an NSI evidence family

Recommended namespace:

- `landis_nsi.nearest_sites`
- `landis_nsi.within_area`
- `landis_nsi.profile_summary`

Rules for this family:

- every output must state that these are sample observations, not complete
  area coverage
- pagination is mandatory
- provenance must include survey/product identity and observation counts
- geometry inputs should match existing bbox/polygon conventions

### D. Add an AUGER research family later, not immediately

Recommended namespace:

- `landis_auger.nearest_sites`
- `landis_auger.within_area`
- `landis_auger.profile_summary`

This should be deferred behind NATMAP and NSI because the volume is much
larger, and the user contract is closer to research/data-mining than to
general screening.

### E. Add an archive/catalogue family as resources first

Recommended namespace and resources:

- `landis_archive.list_items`
- `landis_archive.get_item`
- `resource://mcp-geo/landis-portal-inventory`
- `resource://mcp-geo/landis-portal-documentation-index`

The first step here should be resource-backed discovery, not analytical tools.
The full archive is useful, but most of it should remain browseable reference
material unless a stronger use case emerges.

## Warehouse Strategy

The archive should not be treated as the runtime. The MCP server should
continue to read normalized tables from PostGIS and checked-in resources from
the repo.

Recommended warehouse layers:

### Priority 1: normalized NATMAP core

- `NationalSoilMap`
- `NATMAPsoilscapes`
- `NATMAPassociations`
- `SOILSERIES`
- `HORIZONfundamentals`
- `HORIZONhydraulics`

Reason: this creates a joinable soil-map core that can support classification,
explanation, and derived summaries without inventing new ad hoc tables.

### Priority 2: thematic NATMAP layers

- `NATMAPtopsoiltexture`
- `NATMAPsubsoiltexture`
- `NATMAPsubstratetexture`
- `NATMAPavailablewater`
- `NATMAPcarbon`
- `NATMAPwrb2006`
- `NATMAPregions`

Reason: these are the most natural additive thematic summaries once the core is
stable.

### Priority 3: NSI evidence tables

- `NSIsite`
- `NSIprofile`
- `NSIfeatures`
- `NSItexture`
- `NSItopsoil1`
- `NSItopsoil2`
- `NSImagnetic`

Reason: useful, but they need a separate evidence-oriented contract rather than
screening semantics.

### Leave as archive-only until justified

- `AUGERprofile`
- `AUGERsite`
- Soil catalogue coverage layers
- operational portal artifacts such as the user-survey form

## Resource Strategy

The non-feature archive content should become a curated resource layer instead
of a raw dump surface.

Recommended new resources:

- `resource://mcp-geo/landis-portal-inventory`
- `resource://mcp-geo/landis-portal-docs`
- `resource://mcp-geo/landis-natmap-dataset-guide`
- `resource://mcp-geo/landis-nsi-dataset-guide`

Recommended curation principles:

- expose stable summaries, not arbitrary portal JSON blobs
- keep operator-only paths and local archive paths out of normal client-facing
  payloads unless explicitly requested
- preserve source URLs, item IDs, item types, and licence/provenance notes

## Recommended Delivery Sequence

### Phase 2A: archive triage to runnable ingestion plan

Status: done

- define one normalized schema plan for NATMAP core tables
- define one schema plan for NSI evidence tables
- pin archive-to-warehouse mappings for the selected services
- add a machine-readable triage manifest checked into the repo

### Phase 2B: NATMAP core surfacing

Status: done for the first analytical slice; join-backed enrichment remains next

- ingest `NationalSoilMap` plus join tables
- ship `landis_natmap.point`
- ship `landis_natmap.area_summary`
- add regression fixtures and one live validation run

### Phase 2C: thematic NATMAP summaries

Status: done for the selected polygon thematics already mirrored locally

- ingest selected thematic polygon layers
- ship `landis_natmap.thematic_area_summary`
- expand metadata/resources and operator docs

### Phase 2D: NSI evidence surfacing

Status: done for the first evidence slice

- ingest NSI evidence tables
- ship bounded paged NSI search/summary tools
- add explicit sampling caveats and evidence-only positioning

### Phase 2E: archive browsing resources

Status: done

- expose curated archive inventory/docs resources
- keep raw archive mirroring as an operator workflow, not a default MCP result

### Phase 2F: join enrichment and deferred families

Status: next

- normalize and surface the NATMAP join model using `NATMAPassociations`,
  `SOILSERIES`, `HORIZONfundamentals`, and `HORIZONhydraulics`
- decide whether `NATMAP1000`, `NATMAP2000`, and `NATMAP5000` should become a
  separate scale-aware family or remain archive-only
- define whether any AUGER or Soil Catalogue surfaces deserve first-class MCP
  contracts

## Acceptance Criteria For Phase 2 Planning

This plan should be treated as complete when the repo has:

- a committed family-level surfacing decision for all `33` feature services
- a committed warehouse-priority order, not just a download archive
- a committed rule that MVP tools stay stable and additive only
- a committed phase-2 namespace plan for NATMAP, NSI, archive resources, and
  deferred AUGER work

## Immediate Next Steps

1. Run `scripts/landis_phase2_ingest.py` against the operator’s chosen local
   PostGIS warehouse whenever a live NATMAP/NSI deployment is needed.
2. Add the NATMAP join-table enrichment contract so callers can move from map
   units to series and horizon evidence without using raw archive dumps.
3. Decide whether scale-specific NATMAP products and AUGER belong in the next
   MCP tranche or should remain archive-only.
4. Expand the evaluation harness from the MVP screening cases to the new
   archive, NATMAP, and NSI families.

## Bottom Line

The right next move is still not “surface everything.” The right next move is:

- keep the validated MVP screening tools stable
- use the local archives as the default LandIS source of truth
- keep extending NATMAP and NSI deliberately, not by dumping raw portal fields
- keep AUGER and catalogue layers out of the first analytical expansion until a
  clear user contract exists
- treat the local archive as a governed source of warehouse and resource inputs,
  not a direct substitute for the MCP runtime
