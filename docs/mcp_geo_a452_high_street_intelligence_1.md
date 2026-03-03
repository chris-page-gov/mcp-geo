# MCP-Geo Intelligence Report: A452 High Street Leamington Resurfacing

## Scheme Overview

**Source:** [Warwickshire County Council News](https://www.warwickshire.gov.uk/news/article/7391/a452-high-street-leamington-carriageway-resurfacing)

| Detail | Value |
|--------|-------|
| Road | A452 High Street, Royal Leamington Spa |
| Works | Carriageway resurfacing (Balfour Beatty) |
| Dates | 16–20 February 2026 |
| Hours | 09:30 – 15:30 (Mon–Fri) |
| Traffic mgmt | Full road closure with signed diversion |
| Permit ref | PC0812073795-02 |

---

## What MCP-Geo Can Provide

The following sections demonstrate the data layers available through the mcp-geo server that could support background research and impact assessment for a highway scheme like this. Each section notes the **tool used**, the **data returned**, and its **relevance** to the resurfacing project.

---

## 1. Precise Location & Address Data

**Tool:** `os_places_search` / `os_places_by_postcode`

High Street Leamington runs roughly east–west at **52.284°N, –1.531°W**, between the junction with Bath Street/Gas Street (west) and the junction with Clemens Street/George Street (east). Postcodes served are CV31 3AN (west end), CV31 1LN (odd/north side), and CV31 1LW (even/south side).

### Directly Affected Premises (50 UPRNs returned on High Street alone)

**Retail / Food & Drink (directly fronting the road):**

- Jordans (No. 14) – Shop/Showroom
- Fades (No. 21) – Shop/Showroom  
- Creations (No. 20 & 26) – Shop/Showroom
- Francesco (No. 35) – Shop/Showroom
- Wah Kee (No. 50) – Shop/Showroom
- Red Fort (No. 46) – Restaurant/Cafeteria
- Pepes Pizza (No. 51) – Restaurant/Cafeteria
- Cake Box (No. 47) – Shop/Showroom
- The Treatment Lounge (No. 24) – Shop/Showroom
- Tear A Bytea (No. 2) – Public House/Bar/Nightclub
- Plus multiple additional shops at Nos. 25, 28, 38B, 40, 43, 44, 51C

**Residential (above shops and adjacent):**

- Self-contained flats at Nos. 12, 20A, 25A, 28A, 39A, 41A/B, 46A, 47A/B, 48A
- 6 flats at 51A High Street
- Crown Terrace flats (No. 10)
- Flats at No. 26
- HMOs at Nos. 14A, 16B, 23A, 29-33, 44B, 52A

**Other:**
- Warehouse/Storage at No. 15
- Workshop/Light Industrial at No. 19A
- Property Shell at Nos. 19B, 27A

**Relevance:** Enables a precise count of affected businesses and residents for notification purposes. The mix of retail, restaurants, and above-shop residential is exactly what you'd need for access management planning during a road closure.

---

## 2. Road Network Intelligence

**Tool:** `os_features_query` on `trn-ntwk-roadlink-5` (Road Link v5)

The NGD Road Link collection provides remarkably detailed data for every road segment in the area. For the streets around High Street, mcp-geo returns:

### Road Characteristics Available Per Link

| Attribute | Example Values (local streets) |
|-----------|-------------------------------|
| Road classification | A Road, B Road, Unclassified |
| Route hierarchy | Local Road, B Road, Restricted Local Access Road |
| Road width (average) | 4.0m – 15.5m |
| Road width (minimum) | 3.2m – 11.1m |
| Directionality | Both Directions, In Direction (one-way) |
| Operational state | Open |
| Road structure | Single Carriageway |
| Street lighting | Fully Lit, Mostly Lit, Unknown |
| Pavement coverage (%) | Left: 0–100%, Right: 0–100%, Overall: 16–100% |
| Pavement average width | 1.06m – 2.16m |
| Bus lane presence | 0% (none in this area) |
| Cycle lane presence | 0% (none in this area) |
| Tram on road | None |
| Elevation gain | Per-link gradient data |

### Connecting Streets Identified

The road network query reveals the full connectivity around High Street, including: Clinton Street, Regent Place, Abbott Street, Spencer Yard, Gas Street, Frances Havergal Close, Church Terrace/New Street, Althorpe Street, and Lower Avenue (B4087). This connectivity data is essential for **diversion route planning** — understanding which side streets can handle redirected traffic, their widths, and whether they are one-way.

**Relevance:** Road width and pavement data directly inform whether diversion routes can accommodate HGVs, whether pedestrian access is maintained during works, and whether temporary traffic management needs to account for narrow pinch points.

---

## 3. Average & Indicative Speed Data

**Tool:** `os_features_query` on `trn-rami-averageandindicativespeed-1`

This is perhaps the most powerful layer for impact assessment. OS provides **historic average speeds by time period** for every road link, plus indicative speed limits.

### Speed Profile Structure

Every road link has speed data broken into **14 time periods**:

- **Mon–Fri:** 04:00–07:00, 07:00–09:00, 09:00–12:00, 12:00–14:00, 14:00–16:00, 16:00–19:00, 19:00–22:00, 22:00–04:00
- **Sat–Sun:** 04:00–07:00, 07:00–10:00, 10:00–14:00, 14:00–19:00, 19:00–22:00, 22:00–04:00

Each period provides speed in **both directions** (in-direction and against-direction) in kph.

### Example: Side Streets During Working Hours (09:30–15:30)

The works are scheduled during Mon–Fri 09:00–16:00 windows. Looking at average speeds for nearby streets in the MF 09:00–12:00 and 12:00–14:00 periods:

| Street | MF 09–12 kph | MF 12–14 kph | Speed limit |
|--------|-------------|-------------|-------------|
| Abbott Street | 4.0 | 9.8 | 30 mph |
| Gas Street | 6.0 | 4.8 | 30 mph |
| Spencer Yard | 12.6 | 13.8 | 30 mph |
| Clinton Street | 19.2 | 21.9 | 30 mph |
| Regent Place | 16.3 | 15.8 | 30 mph |
| Lower Avenue (B4087) | 29.9 | 25.9 | 30 mph |

**Key insight:** Abbott Street and Gas Street already operate at very low speeds during the day (4–10 kph), suggesting existing congestion or constrained conditions. Diverting A452 traffic through these streets would likely cause significant further delays. Lower Avenue (B4087) has the highest capacity with speeds near the limit.

**Relevance:** This data enables before/during/after speed comparisons, helps predict which diversion routes will bottleneck, and supports evidence-based traffic management decisions. For a resurfacing scheme during working hours, this is gold.

---

## 4. Building Footprints

**Tool:** `os_map_inventory` with `bld-fts-buildingpart-2`

The buildings layer returns full polygon geometry for every building in the area. From a sample of 50 buildings in the bounding box, the data includes:

- **Geometry:** Full GeoJSON polygons for mapping
- **Classification:** Residential Dwelling, Commercial Industrial, Commercial Office, Commercial Utility, Mixed, HMO
- **Containing site count:** How many addresses exist within the building

This enables visualisation of the physical built environment along the road — useful for understanding how close buildings are to the carriageway, where there are gaps for temporary access, and the density of the built-up area.

---

## 5. Administrative Geography

**Tool:** `admin_lookup_find_by_name`

High Street Leamington falls within **Leamington Brunswick ward** (E05012621) under Warwick District Council. Adjacent wards include Leamington Clarendon, Leamington Willes, and Leamington Milverton.

This enables linking to ward-level census and statistical data, councillor contact details, and planning area policies. The ward code (E05012621) is the key for querying NOMIS census datasets at ward level.

---

## 6. What Could Be Added (Data Gaps & Opportunities)

The following would enhance the picture but require either additional data sources or extended mcp-geo capabilities:

| Data Need | Current Status | Potential Source |
|-----------|---------------|-----------------|
| Traffic count (AADT) on A452 | Not in mcp-geo | DfT road traffic statistics |
| Bus routes affected | No transit data | Stagecoach/National Express GTFS |
| Parking spaces affected | Not directly available | WCC parking data |
| Census demographics (ward) | NOMIS available but requires numeric geography IDs | Census 2021 via NOMIS |
| Air quality monitoring | Not in mcp-geo | DEFRA AURN / local monitoring |
| Planned developments nearby | Not in mcp-geo | Planning applications data |
| Street-level imagery | Not in mcp-geo | Google Street View / Mapillary |

---

## Summary: The MCP-Geo Data Layers

For a highway resurfacing scheme like this, mcp-geo currently provides **six distinct data layers** that together build a comprehensive background picture:

1. **OS Places** → Every affected address, classified by use (retail, residential, HMO, etc.)
2. **NGD Road Links** → Physical road characteristics including width, pavement, lighting, connectivity
3. **Average Speed Data** → Time-of-day traffic speed profiles for impact modelling
4. **Building Footprints** → Physical environment geometry for mapping
5. **Administrative Geography** → Ward/LSOA codes for linking to statistical datasets
6. **OS Names** → Place and road name search for initial location discovery

The combination of premises-level address data with road network intelligence and time-period speed data provides a genuinely useful evidence base for scheme planning, stakeholder communication, and impact assessment — all accessible programmatically through a single MCP server conversation.
