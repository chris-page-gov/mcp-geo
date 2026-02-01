# Authoritative sources (by nation and purpose), and how you fetch them:

## UK-wide statistical + many administrative/electoral boundaries (GSS-coded)

ONS Geography (Open Geography Portal). These are usually published as downloadable boundary packages (GeoPackage / Shapefile / etc) and in multiple boundary variants (for example BFC/BFE/BGC/BUC). Many are also exposed as ArcGIS services, so you can query features, but for a PostGIS “local mirror” you normally ingest the download bundle.

## Great Britain legal/admin + electoral boundary framework: 

Ordnance Survey Boundary-Line. This is provided as a bulk download product (single ZIP per format) and OS state it is updated twice a year (May and October); OS also provide a simple downloads API which returns a redirect to the ZIP.

## Scotland Census 2022 small-area geographies: 

National Records of Scotland (NRS) (for example Output Areas + related census geographies), typically as ZIP downloads (often with both “extent” and “clipped” coast representations).

## Scotland Data Zones / Intermediate Zones (post-Census 2022): 

Scottish Government / SpatialData (maps.gov.scot ATOM downloads) (ZIP shapefiles).

## Northern Ireland statistical geographies: 

NISRA (for example Data Zones / Super Data Zones (Census 2021) and Small Areas / SOAs (Census 2011)), published as download bundles; NISRA also describe nesting relationships (DZ→SDZ→LGD/PC).

## JSON Manifest identifies sources for ingestion

[Boundaries.json](Boundaries.json) is a single JSON manifest designed so Codex can discover (latest vintages), download, ingest into PostGIS, and validate. It includes a completion statement Codex can treat as the definition of “done”.

Pipeline entrypoint:

```bash
pip install -e .[boundaries]
python scripts/boundary_pipeline.py --mode resolve
# For a full download + ingest + validation pass:
python scripts/boundary_pipeline.py --mode all
```

Run reports are written under `data/boundary_runs/<timestamp>/run_report.json`.
To summarize effectiveness, run:

```bash
python scripts/boundary_run_tracker.py
```

## Size summary (downloads + ingest)

The pipeline report now captures byte sizes for downloads, extracted archives, and
PostGIS tables. After a run, check `run_tracker.json`:

```bash
cat data/boundary_runs/<timestamp>/run_tracker.json | jq '.summary | {download_bytes, archive_uncompressed_bytes, extracted_bytes, ingested_table_bytes}'
```

This helps estimate storage needs and monitor growth over time.

## Status ticker (progress + error counts)

For a quick progress readout (families ok, downloads/ingest/validation coverage,
and error counts), run:

```bash
python scripts/boundary_status_ticker.py
```

To emit a ticker update every minute while a run is finishing:

```bash
python scripts/boundary_status_ticker.py --watch --interval 60
```

## Validation triage (cause + fix mapping)

To list validation failures that occurred after successful download + ingest,
along with generic fix guidance:

```bash
python scripts/boundary_triage.py > data/boundary_runs/<timestamp>/triage_report.json
```

## Auto-fix loop (full run + targeted reruns)

To run the pipeline end-to-end, then rerun only failing families until the
error set stops changing:

```bash
python scripts/boundary_autofix.py
```

Optional flags:

```bash
python scripts/boundary_autofix.py --max-iterations 5 --sleep 2
```

Selective retries:

```bash
python scripts/boundary_pipeline.py --family oa_2021_ew --variant BFC --mode all
```

Compare tracker output to a baseline run:

```bash
python scripts/boundary_run_tracker.py \
  --compare data/boundary_runs/<previous>/run_report.json
```

## Completion / Done Definition (for Codex)

This step is complete when, for every boundary_family in the JSON manifest:

Source resolution succeeds

A concrete download_url (or OS Boundary-Line redirect target) is resolved for each required_variant listed in completion_definition.required_variants, or the run records an explicit "not_published" outcome with a captured evidence record (CKAN package_show JSON or source page metadata).

Download + integrity checks succeed

The archive is downloaded successfully and, where supported, its checksum (e.g., SHA-256) is computed and stored.

The archive contents are readable by GDAL/OGR (no corrupt ZIP, missing layers, or unreadable geometries).

Ingestion succeeds

Each dataset/variant is ingested into PostGIS using the manifest’s postgis_defaults.table_naming convention (or the family’s override), into the declared schema.

All ingested tables have a geometry column named geom in the manifest’s target SRID (EPSG:27700).

Validation succeeds

Schema validation: the expected code field(s) and name field(s) (where applicable) are present and match the family’s regex rules.

Uniqueness validation: the geography code column is unique within each {family_id, variant, vintage} table.

Geometry validation: ST_IsValid(geom) is true for all rows (or all invalid rows are repaired and the repair count is logged).

Row-count sanity: each table meets its row_count_sanity.min threshold.

Variant coverage: for each family, all required variants are present unless recorded as "not_published" with evidence.

Run is reproducible

A single run produces a machine-readable run report containing: manifest version, resolved URLs, download timestamps, checksums, row counts, validation results, and any "not_published"/exceptions with evidence references.

If all five conditions hold, mark the pipeline status as: COMPLETE_BOUNDARIES_INGESTED_AND_VALIDATED.

Here’s a JSON completion_checklist object Codex can execute and emit as a structured pass/fail report (you can paste this into the manifest under completion_definition.completion_checklist, or keep it as a separate file like completion_checklist.json): [Boundaries Completion Checklist](boundaries_completion_checklist.json)

## Post-run checklist (validation error -> next action)

Use this section after a full pipeline run to resolve any errors emitted in
`run_report.json` under `errors[].errors[]`.

| Validation error | Recommended next action |
| --- | --- |
| `missing_resolved:<variant>` | Confirm the family exists in `docs/Boundaries.json`, then rerun `--mode resolve` for that family. If the source does not publish the variant, record a `not_published` evidence entry in the run report. |
| `invalid_resolved_status:<variant>` | Inspect the `resolved_resources` entry for the variant and fix the resolution logic (bad status string or malformed payload). Re-run `--mode resolve`. |
| `missing_not_published_evidence:<variant>` | Add a CKAN package_show JSON or source page metadata file under `evidence/source_page_metadata/` and set `evidence_ref`. Re-run `--mode resolve`. |
| `download_failed:<variant>` | Re-run `--mode download` for the family/variant. If the download is still failing, capture the failing URL + HTTP status in evidence and verify required headers (user-agent, redirects). |
| `ingest_failed:<variant>` | Check `ingestions` for the variant to see the error string (missing deps, bad layer, unsupported geometry). Ensure GDAL/pyogrio + psycopg are installed and re-run `--mode ingest`. |
| `code_field_missing:<variant>:<table>` | Update the manifest `validation.must_be_unique` and/or `code_field_regex` to the correct code column name, then re-run `--mode validate`. |
| `name_field_missing:<variant>:<table>` | Update the manifest `validation.name_field_regex` (or mark name as optional for that family) and re-run `--mode validate`. |
| `row_count_low:<variant>:<table>` | Verify the correct layer is being ingested (GPKG layer index or layer name). Update `ingest.layer_selection` or minimum row count if the dataset changed. |
| `invalid_geometry:<variant>:<table>` | Inspect invalid geometries using `ST_IsValidReason`. If failures persist after `ST_MakeValid`, switch to a different variant or source, or exclude the problematic layer. |
| `duplicate_codes:<variant>:<table>` | Check for multi-part rows or stale code columns. If duplicates are legit, update validation rules; otherwise, fix the ingest selection or de-duplicate upstream. |

------------------- Other notes --------------------

## Glossary (pipeline terms and acronyms)

- ArcGIS Hub: ArcGIS-hosted dataset portal used by ONS for downloads.
- BBOX: Bounding box, [minLon, minLat, maxLon, maxLat].
- BFC/BFE/BGC/BUC: ONS boundary variants (Full/Extent/Generalised/Ultra generalised, clipped or extent).
- BNG: British National Grid (EPSG:27700).
- CKAN: Open data catalog API (data.gov.uk uses CKAN).
- EPSG/SRID: Coordinate reference identifiers used by PostGIS.
- FGDB: ESRI File Geodatabase download format.
- GDAL/OGR: Geospatial library used to read shapefiles/GPKG/GeoJSON.
- GPKG: GeoPackage file format.
- ONS: Office for National Statistics (Open Geography Portal).
- OS: Ordnance Survey (Boundary-Line, OS APIs).
- NISRA: Northern Ireland Statistics and Research Agency.
- PostGIS: PostgreSQL geospatial extension used as the boundary cache.
- SHP: ESRI Shapefile format.
- Validation errors:
  - code_field_missing/name_field_missing: expected ID/name columns not found.
  - row_count_low: ingested row count below minimum threshold.
  - invalid_geometry: geometry invalid after ST_MakeValid repair.
  - duplicate_codes: non-unique geography codes.
- Download errors:
  - download_not_ready: ArcGIS Hub export still processing.
  - not_published: variant not available; must include evidence.
  - ingest_status=skipped: unsupported geometry type (e.g., lines) intentionally skipped.

Alternative strategies referenced:
- CKAN discovery (data.gov.uk) for ONS datasets.
- Direct download URLs (NISRA, OS Boundary-Line).
- Fallback to OpenDataNI CKAN if NISRA links change.

1. Facts: authoritative sources and scope
2. Full boundary catalogue (by class)
3. Notes on codes, vintages, and stability
4. Practical guidance for PostGIS + MCP design

No opinion is mixed into the catalogue itself; I’ll separate commentary clearly.

---

## 1. Facts: authoritative scope by source

### Office for National Statistics – Open Geography Portal (UK-wide)

**Authoritative for:**

* Statistical geographies
* Administrative geographies as used in official statistics
* Census hierarchies
* Health, education, and bespoke analytical areas

**Strengths**

* UK-wide (England, Wales, Scotland, Northern Ireland)
* GSS codes are the canonical join keys
* Explicit hierarchies (OA → LSOA → MSOA → LAD → Region → Nation)

**Access**

* Bulk downloads (GeoPackage, SHP, GeoJSON)
* WFS/REST endpoints for some layers
* Versioned by “as at” year (e.g. 2021 Census)

---

### Ordnance Survey – Boundary-Line (Great Britain only)

**Authoritative for:**

* Legal and administrative boundaries
* Electoral boundaries
* Ceremonial boundaries

**Strengths**

* High cartographic precision
* Legal definitions
* Stable identifiers for many admin units

**Limitations**

* Great Britain only (no Northern Ireland)
* Mostly bulk download rather than fine-grained API

---

## 2. Full boundary catalogue you can expect to localise

Below is a **superset** of what your current list implies, grouped logically.
I’ve included **canonical codes**, **names**, and **typical vintages**.

---

### A. Census Statistical Geographies (ONS)

These are **non-negotiable** for any serious analytics MCP.

| Level                        | Code field       | Name field | Notes                     |
| ---------------------------- | ---------------- | ---------- | ------------------------- |
| Output Area                  | `OA21CD`         | —          | Smallest statistical unit |
| Lower Super Output Area      | `LSOA21CD`       | `LSOA21NM` | ~1,500 people             |
| Middle Super Output Area     | `MSOA21CD`       | `MSOA21NM` | ~7,200 people             |
| Upper Tier Super Output Area | *(England only)* | —          | Rarely used post-2011     |

✔ Your current OA / LSOA / MSOA entries are correct.

---

### B. Administrative Areas – Local Government (ONS + OS)

These define **governance**, funding, and accountability.

| Level                        | Code field  | Name field  | Notes                    |
| ---------------------------- | ----------- | ----------- | ------------------------ |
| Local Authority District     | `LAD23CD`   | `LAD23NM`   | England, Wales, Scotland |
| County / Unitary Authority   | `CTYUA23CD` | `CTYUA23NM` | England only             |
| London Borough               | `LAD23CD`   | `LAD23NM`   | Subtype of LAD           |
| Metropolitan District        | `LAD23CD`   | `LAD23NM`   | Subtype of LAD           |
| Civil Parish / Community     | `PAR23CD`   | `PAR23NM`   | England & Wales          |
| Scottish Council Area        | `LAD23CD`   | `LAD23NM`   | Scotland                 |
| NI Local Government District | `LGD2023CD` | `LGD2023NM` | Northern Ireland         |

⚠️ Note: **LADxx** is a *container concept* — the subtype matters semantically.

---

### C. Regions and Nations (ONS)

| Level            | Code field | Name field |
| ---------------- | ---------- | ---------- |
| Region (England) | `RGN23CD`  | `RGN23NM`  |
| Country          | `CTRY23CD` | `CTRY23NM` |

✔ Your REGION / NATION entries are correct, but update vintages.

---

### D. Electoral Geographies (ONS + OS Boundary-Line)

Critical for democratic, planning, and FOI-adjacent questions.

| Level                                  | Code field  | Name field  |
| -------------------------------------- | ----------- | ----------- |
| Westminster Parliamentary Constituency | `PCON23CD`  | `PCON23NM`  |
| Electoral Ward / Division              | `WD23CD`    | `WD23NM`    |
| Scottish Parliament Constituency       | `SPC2021CD` | `SPC2021NM` |
| Senedd Cymru Constituency              | `WSC2021CD` | `WSC2021NM` |
| Northern Ireland Assembly Area         | `NIA2022CD` | `NIA2022NM` |

---

### E. Health Geographies (ONS)

These matter for deprivation, outcomes, and funding.

| Level                                 | Code field  | Name field  |
| ------------------------------------- | ----------- | ----------- |
| Integrated Care Board                 | `ICB23CD`   | `ICB23NM`   |
| NHS Trust                             | `NHSER23CD` | `NHSER23NM` |
| Clinical Commissioning Group (legacy) | `CCG21CD`   | `CCG21NM`   |

---

### F. Built-form / Planning / Delivery (OS + ONS hybrids)

Often overlooked but **extremely powerful** for MCP reasoning.

| Level                      | Source | Notes              |
| -------------------------- | ------ | ------------------ |
| Built-up Area              | ONS    | Urban extent       |
| Built-up Area Sub-division | ONS    | Towns / city parts |
| Travel to Work Area        | ONS    | Labour markets     |
| Police Force Area          | ONS    | England & Wales    |
| Fire & Rescue Authority    | ONS    | England            |

---

### G. Ceremonial & Legal Areas (OS Boundary-Line)

| Level                          | Notes                      |
| ------------------------------ | -------------------------- |
| Ceremonial County              | Lieutenancy                |
| Historic County                | Contextual                 |
| Crown Dependency (extent only) | Jersey, Guernsey (non-ONS) |

---

## 3. Codes, vintages, and stability (important facts)

**Facts**

* GSS codes are *immutable identifiers*, but **geometry changes over time**
* ONS publishes multiple vintages concurrently
* Names are **not stable keys**
* Electoral boundaries change most frequently
* Census geographies are fixed per Census cycle

**Implication**
Your MCP server must treat:

```
boundary_type + vintage + code
```

as the *true primary key*, not just the code.

---

## 4. Practical guidance for MCP-geo + PostGIS

### What to localise by default

Minimum “serious MCP” baseline:

* OA21
* LSOA21
* MSOA21
* LAD23
* WD23
* PCON23
* RGN23
* CTRY23

Everything else can be layered incrementally.

---

### Suggested PostGIS schema pattern

```sql
boundary_type
vintage
gss_code
name
geom
source
valid_from
valid_to
```

This lets your MCP agent:

* Answer historical questions
* Explain discrepancies
* Reason about change over time

---

### API reality check (fact)

There is **no authoritative UK API that serves arbitrary per-boundary polygons on demand** at scale.

**Correct architectural pattern**

* Bulk download authoritative data
* Localise into PostGIS
* Serve *your own* per-boundary, per-point, and hierarchical queries

This is exactly the right design choice for MCP-geo.

---

If you want, next we can:

* Turn this into a **machine-readable boundary manifest** (YAML/JSON) for your repo
* Map **which boundaries nest cleanly vs approximately**
* Design **MCP resources vs MCP tools** per boundary class

Just say where you want to go next.
