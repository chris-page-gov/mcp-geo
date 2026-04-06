---
aliases: [Soilscapes, soilscapes viewer]
tags: [dataset, polygon, soilscapes, landis, generalised]
layer: 2
scale: "1:250,000"
classes: 27
coverage: "England and Wales"
created_date: 2003
updated_date: 2010
---

# Soilscapes

> [!info] Dataset Identity
> **Type:** Simplified national soil polygon map
> **Scale:** 1:250,000 shapefile
> **Classes:** 27 (generalised from ~300 NATMAP associations)
> **Created:** 2003, updated 2010
> **Metadata:** ISO 19115/19139
> **Access:** Free via viewer; open access 2026

## What It Is

Soilscapes is a simplified, non-specialist-friendly version of [[NATMAP Vector]], collapsing ~300 soil associations into just **27 broad soil classes**. It is explicitly designed to communicate soil variation to **non-soil scientists** and support policy awareness and broad planning — not detailed site assessment.

It is the most accessible entry point to LandIS data, providing a free web viewer at [landis.org.uk/soilscapes](https://www.landis.org.uk/soilscapes/).

## The 27 Classes

The 27 Soilscapes classes aggregate soils by dominant functional characteristics (drainage, parent material, land cover association). Examples include:

- Freely draining slightly acid loamy soils
- Seasonally wet acid and loamy soils
- Shallow soils over chalk and limestone
- Peat soils
- Slowly permeable seasonally wet acid loamy and clayey soils

Each class links to descriptive information on typical drainage, organic matter, habitats, and farming constraints.

## Viewer and Access

The **Soilscapes Viewer** supports location search by:
- Postcode
- Place name
- OS grid reference
- Coordinates (lat/lon)

It returns a soilscape class with class description, typical drainage, habitats, and farming notes.

## MCP Access

**Point lookup:** `landis_soilscapes_point(lat, lon)` → class + key attributes + uncertainty note
**Area summary:** `landis_soilscapes_area_summary(geometry)` → percent area by soilscape class

## Associated Datasets (per class)

| Soilscapes Sub-dataset | Content |
|---|---|
| Drainage | Ease of cultivation, flood response |
| Habitats | Typical habitats associated with class |
| Agriculture | Farming constraints, workdays |
| Hydrology | Drainage behaviour indicators |

## The Generalisation Trap

> [!danger] High-Stakes Misinterpretation Risk
> Soilscapes **collapses 300 associations into 27 classes**, making it a sweeping generalisation. It **must not** be used for:
> - Planning applications
> - Site investigations
> - Engineering design
> - Detailed assessments of any kind
>
> The 1:250k scale and within-polygon variability mean that the class shown at a location is a statistical probability, not a site-specific characterisation. Field validation is always required.

This limitation is [[MCP Overview|hardcoded into MCP tool outputs]] as a mandatory caveat block.

## Use Cases

- [[Government and Policy]] — broad land-use planning awareness
- [[Agriculture and Land Management]] — farm planning, awareness of drainage classes
- [[Biodiversity and Habitat]] — habitat mapping, wildlife trust land purchase
- [[Emerging Opportunities]] — "explain my soil" public education tools
- Local authorities, engineers, agronomists, environmental consultants

## Data Model Note

Soilscapes is a **standalone** dataset — it does not join to the SOILSERIES or HORIZON tables. For attribute-level detail you must use [[NATMAP Vector]] and follow the [[Data Structure and Joins|join model]] to series and horizon data.

## Sources
- [LandIS Soilscapes viewer](https://www.landis.org.uk/soilscapes/)
- [data.gov.uk Soilscapes record](https://www.data.gov.uk/dataset/26d61739-e05b-420d-8fd0-d11edffa8b27/soilscapes1)
- Soilscapes applications and metadata brochure (downloadable from LandIS)

---
*← [[00 - Home|Home]]  |  See also: [[NATMAP Vector]], [[Data Structure and Joins]]*
