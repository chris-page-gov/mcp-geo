---
aliases: [climate, carbon, GHG, peat, net zero, carbon stocks]
tags: [use-case, climate, carbon, net-zero, GHG, peat, landis]
confidence: high
key_dataset: NATMAP Carbon
---

# Climate and Carbon

> [!success] Directly Evidenced
> NATMAP Carbon is explicitly used for the **UK Greenhouse Gas Inventory** and provides multi-depth carbon stock summaries. NSI supports national carbon trend studies, including the landmark *Nature* (2005) paper on carbon losses across England and Wales.

## Core Climate and Carbon Applications

### UK Greenhouse Gas Inventory
NATMAP Carbon is a **statutory input** to national climate accounting. It provides:
- Organic carbon stock estimates at 0–30, 30–100, 100–150 cm depth layers
- National totals for land-use category reporting under UNFCCC
- The evidence base for quantifying soil carbon emissions from land-use change

**This makes LandIS a component of UK net zero monitoring infrastructure.**

**MCP access:** `landis_natmap_thematic_area_summary(geometry, "carbon")`

---

### Soil Carbon Trend Monitoring (NSI)
The NSI dataset is the primary evidence base for detecting **national-scale changes in soil carbon** over time. The two sampling periods (Topsoil83, Topsoil95) enable trend analysis.

Most notably, NSI data underpins the *Nature* (2005) paper documenting **carbon losses across England and Wales between 1978 and 2003** — one of the most cited findings in UK soil science, showing that soils were losing carbon at ~4 million tonnes per year.

**MCP access:** `landis_nsi_within_area(geometry)` + `landis_nsi_profile_summary(site_id, year)`

---

### High-Carbon Soil Screening
A key climate policy tool: identifying where the highest carbon-density soils are, to prioritise:
- Protection from development or drainage
- Incentivised management under agri-environment schemes
- Peatland restoration targeting

**Proposed MCP tool:** High-Carbon Soil Screening → see [[Derived Semantic Tools]]

**Output:** High/medium/low carbon stock classification by area + depth breakdown + "peat flag" for wet organic soils + "verify with peat depth survey" caveat

---

### Land-Use Change Impact Screening
When a land-use change is proposed (e.g. development, intensification, rewetting), what is the likely carbon stock at risk?

LandIS carbon data enables a rapid screening before a detailed carbon impact assessment:
- How much carbon is stored in this soil profile?
- Is it high-risk (high carbon + poor drainage = peat likely)?
- What depth does the carbon extend to?

> [!note] Confidence Level for Carbon Accounting
> Medium-high for screening and inventory-level estimates. Lower for site-specific accounting without additional local measurements (bulk density, depth to mineral, lateral variability).

---

### Peatland and Organic Soil Targeting
Peat soils store enormous quantities of carbon — many times more per hectare than mineral soils. Identifying peat requires:

1. LandIS wetness + carbon screening (high carbon + very wet = peat candidate)
2. Soilscapes class check (peat soilscape classes)
3. Soil Alerts (acid sulphate peat alerts, groundwater-affected soils)
4. **Field verification** — peat depth surveys are still required

LandIS provides the screening layer; Natural England's peat depth maps (under development) complement it.

---

### Rewetting and Restoration Planning
Rewetting drained organic soils is one of the most cost-effective nature-based climate solutions. LandIS data helps identify:
- Historically wet soils now artificially drained (high carbon + poor HOST drainage)
- Locations where rewetting is likely to succeed
- Carbon uplift potential from restoration

---

## Carbon Screening Workflow

```
Input: Land parcel polygon
          │
          ▼
1. landis_natmap_thematic_area_summary(parcel, "carbon")
   → Carbon stock by depth layer
          │
          ▼
2. landis_natmap_thematic_area_summary(parcel, "wetness")
   → Drainage class (wet + high carbon = peat candidate)
          │
          ▼
3. landis_soilscapes_area_summary(parcel)
   → Check for peat soilscape classes
          │
          ▼
4. Soil Alerts check (proposed)
   → Acid sulphate peat flags, organic soil alerts
          │
          ▼
Output: Carbon screening report
        → Carbon stock estimates by zone
        → Peat risk flag
        → "Verify with peat depth survey" caveat
        → Provenance: NATMAP Carbon + dataset version
```

---

## Key Questions

| Question | Dataset | Tool |
|---|---|---|
| What is the total carbon stock in this ELMS proposal area? | NATMAP Carbon | `landis_natmap_thematic_area_summary(…, "carbon")` |
| Are there high-carbon soils at risk from this development? | NATMAP Carbon + Wetness | High-carbon screening tool |
| What does NSI tell us about baseline soil chemistry here? | NSI | `landis_nsi_within_area` |
| Is there peat here that should be protected? | Carbon + Wetness + Alerts | Multi-layer screening |

---

## Key Stakeholders
→ [[Stakeholders#🏛️ Government and Policy Teams]]

---
*← [[00 - Home|Home]]  |  See also: [[Interpreted Layers]], [[NSI - National Soil Inventory]], [[Government and Policy]]*
