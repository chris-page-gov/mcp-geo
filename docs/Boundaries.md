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
python scripts/boundary_pipeline.py --mode resolve
```

Run reports are written under `data/boundary_runs/<timestamp>/run_report.json`.

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

------------------- Other notes --------------------

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
