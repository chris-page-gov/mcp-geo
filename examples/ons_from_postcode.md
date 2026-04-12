# Claude Code with MCP-Geo

```text
➜  AI-Lab-Hackathons git:(main) claude
 ▐▛███▜▌   Claude Code v2.1.101
▝▜█████▛▘  Sonnet 4.6 with high effort · API Usage Billing
  ▘▘ ▝▝    ~/repos/AI-Lab-Hackathons

❯ What geographies are in the  CV3 1HB postcode

⏺ mcp-geo - ons_geo_by_postcode (MCP)(postcode: "CV3 1HB")
  ⎿  {
       "query": {
         "postcode": "CV31HB",
     … +70 lines (ctrl+o to expand)

⏺ Here are the key geographies for CV3 1HB (source: ONS Postcode Directory,
  February 2026):

  ┌─────────────────┬───────────┬───────────────┐
  │      Level      │   Code    │     Name      │
  ├─────────────────┼───────────┼───────────────┤
  │ Country         │ E92000001 │ England       │
  ├─────────────────┼───────────┼───────────────┤
  │ Region          │ E12000005 │ West Midlands │
  ├─────────────────┼───────────┼───────────────┤
  │ Local Authority │ E08000026 │ Coventry      │
  ├─────────────────┼───────────┼───────────────┤
  │ Ward            │ E05001226 │ Lower Stoke   │
  ├─────────────────┼───────────┼───────────────┤
  │ MSOA            │ E02001984 │ Coventry 027  │
  ├─────────────────┼───────────┼───────────────┤
  │ LSOA            │ E01009617 │ Coventry 027C │
  ├─────────────────┼───────────┼───────────────┤
  │ Output Area     │ E00048678 │ —             │
  └─────────────────┴───────────┴───────────────┘

  Additional geographies include:
  - Parliamentary Constituency (2024): E14001182
  - ICB: E54000018
  - NHS England Region: E40000011
  - Police Force Area: E23000014
  - Travel to Work Area: E30000195
  - Built-up Area: E63010120

❯ What do you know about that OA

⏺ mcp-geo - admin_lookup_find_by_name (MCP)(text: "E00048678")
  ⎿  {
       "results": [
         {
     … +14 lines (ctrl+o to expand)

⏺ mcp-geo - ons_geo_cache_status (MCP)
  ⎿  {
       "available": true,
       "status": "degraded",
     … +172 lines (ctrl+o to expand)

⏺ mcp-geo - admin_lookup_area_geometry (MCP)(id: "E00048678", includeGeometry:
                                            false)
  ⎿  {
       "id": "E00048678",
       "bbox": [
     … +15 lines (ctrl+o to expand)

⏺ mcp-geo - os_map_inventory (MCP)(bbox: [-1.476787542296484,52.40388683184649,-
                                  1.4723475591622988,52.407743321377566],
                                  layers: "[\"buildings\", \"uprns\"]")
  ⎿  Error: result (133,188 characters) exceeds maximum allowed tokens. Out
     put has been saved to /Users/crpage/.claude/projects/-Users-crpage-rep
     os-AI-Lab-Hackathons/a09dc89e-d3f8-4af4-a496-e4576e89da53/tool-results
     … +16 lines (ctrl+o to expand)

  Read 2 files (ctrl+o to expand)

⏺ mcp-geo - nomis_query (MCP)(dataset: "NM_2021_1", params: {"geography":"E00048
                             678","variable":"1","measures":"20100"})
  ⎿  {
       "live": true,
       "dataset": "NM_2021_1",
     … +79 lines (ctrl+o to expand)

⏺ Here's what is known about Output Area E00048678:

  Location
  - Bounding box: approximately -1.477 to -1.472 longitude, 52.404 to 52.408
  latitude
  - Sits within Lower Stoke ward, Coventry, West Midlands

  Census 2021 (ONS)
  - Usual residents: 292 (as at 21 March 2021)

  Built environment (OS)
  - ~100 UPRNs and buildings within the OA boundary

  Output Areas are the smallest geography for census data release in England &
  Wales — this one is a fairly typical-sized OA. Note that Census figures at OA
  level are subject to small-count perturbation for disclosure protection, so
  the 292 figure may be slightly adjusted.

  Would you like to dig into more demographic detail (age, tenure, ethnicity
  etc.) for this OA?

✻ Cooked for 40s

❯ yes

⏺ mcp-geo - nomis_query (MCP)(dataset: "NM_2041_1", params:
                             {"geography":"E00048678","measures":"20100"})
  ⎿  {
       "live": true,
       "dataset": "NM_2041_1",
     … +144 lines (ctrl+o to expand)

⏺ mcp-geo - nomis_query (MCP)(dataset: "NM_2072_1", params:
                             {"geography":"E00048678","measures":"20100"})
  ⎿  {
       "live": true,
       "dataset": "NM_2072_1",
     … +115 lines (ctrl+o to expand)

⏺ mcp-geo - nomis_query (MCP)(dataset: "NM_2028_1", params:
                             {"geography":"E00048678","measures":"20100"})
  ⎿  {
       "live": true,
       "dataset": "NM_2028_1",
     … +72 lines (ctrl+o to expand)

⏺ mcp-geo - nomis_query (MCP)(dataset: "NM_2024_1", params:
                             {"geography":"E00048678","measures":"20100"})
  ⎿  {
       "live": true,
       "dataset": "NM_2024_1",
     … +104 lines (ctrl+o to expand)

⏺ Here's the Census 2021 demographic profile for OA E00048678 (all data as at 21
   March 2021):

  ---
  Sex (290 residents)

  ┌────────┬───────┬─────┐
  │        │ Count │  %  │
  ├────────┼───────┼─────┤
  │ Female │ 145   │ 50% │
  ├────────┼───────┼─────┤
  │ Male   │ 145   │ 50% │
  └────────┴───────┴─────┘

  ---
  Ethnicity (288 residents)

  ┌───────────────────────┬───────┬───────┐
  │         Group         │ Count │   %   │
  ├───────────────────────┼───────┼───────┤
  │ White                 │ 166   │ 57.6% │
  ├───────────────────────┼───────┼───────┤
  │ — White British       │ 130   │ 45.1% │
  ├───────────────────────┼───────┼───────┤
  │ — Other White         │ 27    │ 9.4%  │
  ├───────────────────────┼───────┼───────┤
  │ — White Irish         │ 9     │ 3.1%  │
  ├───────────────────────┼───────┼───────┤
  │ Asian / Asian British │ 88    │ 30.6% │
  ├───────────────────────┼───────┼───────┤
  │ — Indian              │ 59    │ 20.5% │
  ├───────────────────────┼───────┼───────┤
  │ — Pakistani           │ 20    │ 6.9%  │
  ├───────────────────────┼───────┼───────┤
  │ — Other Asian         │ 7     │ 2.4%  │
  ├───────────────────────┼───────┼───────┤
  │ Black / Black British │ 16    │ 5.6%  │
  ├───────────────────────┼───────┼───────┤
  │ — African             │ 11    │ 3.8%  │
  ├───────────────────────┼───────┼───────┤
  │ Other                 │ 11    │ 3.8%  │
  ├───────────────────────┼───────┼───────┤
  │ Mixed                 │ 7     │ 2.4%  │
  └───────────────────────┴───────┴───────┘

  ---
  Country of Birth (290 residents)

  ┌───────────────────────┬───────┬───────┐
  │                       │ Count │   %   │
  ├───────────────────────┼───────┼───────┤
  │ UK                    │ 202   │ 69.7% │
  ├───────────────────────┼───────┼───────┤
  │ Middle East & Asia    │ 39    │ 13.4% │
  ├───────────────────────┼───────┼───────┤
  │ EU countries          │ 31    │ 10.7% │
  ├───────────────────────┼───────┼───────┤
  │ Africa                │ 15    │ 5.2%  │
  ├───────────────────────┼───────┼───────┤
  │ Other Europe (non-EU) │ 3     │ 1.0%  │
  └───────────────────────┴───────┴───────┘

  ---
  Tenure (110 households)

  ┌─────────────────────┬───────┬─────┐
  │                     │ Count │  %  │
  ├─────────────────────┼───────┼─────┤
  │ Owned outright      │ 40    │ 36% │
  ├─────────────────────┼───────┼─────┤
  │ Owned with mortgage │ 37    │ 34% │
  ├─────────────────────┼───────┼─────┤
  │ Private rented      │ 33    │ 30% │
  ├─────────────────────┼───────┼─────┤
  │ Social rented       │ 0     │ 0%  │
  └─────────────────────┴───────┴─────┘

  Notable characteristics: This OA has a significantly above-average South Asian
   population (particularly Indian at ~20%), is predominantly owner-occupied
  (70%) with no social housing, and has a substantial share of residents born in
   the Middle East & Asia (13%).

✻ Cogitated for 1m 5s

❯ can you see the OA Classification?

⏺ mcp-geo - ons_geo_by_postcode (MCP)(postcode: "CV3 1HB", includeRaw: true)
  ⎿  {
       "query": {
         "postcode": "CV31HB",
     … +130 lines (ctrl+o to expand)

⏺ Yes — the raw ONSPD data contains the OAC codes:

  ┌─────────────────────┬──────┐
  │       Version       │ Code │
  ├─────────────────────┼──────┤
  │ 2001 OAC (oac01ind) │ 6C1  │
  ├─────────────────────┼──────┤
  │ 2011 OAC (oac11ind) │ 4C1  │
  └─────────────────────┴──────┘

  Decoding those:

  2011 OAC — 4C1
  - Supergroup 4: Multicultural Metropolitans
  - Group 4C: Ethnic Family Life
  - Subgroup 4C1: Striving Families

  This describes areas characterised by high ethnic diversity, working-age
  families, lower incomes, private renting alongside some owner-occupation, and
  high population density — which aligns well with the Census data we saw (30%
  South Asian, 30% private rented, 70% working-age population).

  2001 OAC — 6C1
  - Supergroup 6: Typical Traits
  - Group 6C: Settled Households
  - Subgroup 6C1: Established Home Owning Communities

  The shift from Established Home Owning Communities (2001) to Striving Families
   (2011) suggests the area became more ethnically diverse and experienced some
  socioeconomic change in that decade.

  Note: A 2021 OAC was published (based on Census 2021) but it doesn't appear to
   be included in the February 2026 ONSPD release yet.

────────────────────────────────────────────────────────────────────────────────
❯
────────────────────────────────────────────────────────────────────────────────
 
```
