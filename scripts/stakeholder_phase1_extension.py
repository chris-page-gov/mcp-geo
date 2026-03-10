"""Phase 1 stakeholder benchmark extension scenarios and fixtures."""

from __future__ import annotations

from typing import Any


EXTENSION_FIXTURE_SPECS: dict[str, dict[str, Any]] = {
    "fixtures/scenario_11_postcode_sample.csv": {
        "format": "csv",
        "rows": [
            {
                "sample_id": "PC-001",
                "postcode": "DN22 6PE",
                "service_context": "Single-address postcode used to benchmark authoritative lookup plus cache-freshness commentary.",
            }
        ],
    },
    "fixtures/scenario_12_dispatch_resources.csv": {
        "format": "csv",
        "rows": [
            {
                "resource_id": "FR-001",
                "resource_name": "Retford Fire Station",
                "resource_type": "fire_station",
                "address_text": "Nottinghamshire Fire & Rescue Service, Fire Station, Wharf Road, Retford, DN22 6EN",
            },
            {
                "resource_id": "FR-002",
                "resource_name": "Tuxford Fire Station",
                "resource_type": "fire_station",
                "address_text": "Nottinghamshire Fire & Rescue Service, Tuxford Fire Station, Clark Lane, Tuxford, Newark, NG22 0LZ",
            },
        ],
    },
    "fixtures/scenario_13_case_addresses.csv": {
        "format": "csv",
        "rows": [
            {
                "case_id": "CASE-001",
                "address_text": "H M Prison, Ranby, Retford, DN22 8EU",
                "benchmark_setting": "prison",
                "source_note": "Public institution used as a UKHSA-style setting-classification benchmark row.",
            },
            {
                "case_id": "CASE-002",
                "address_text": "Westvilla Nursing Home, Westfield Road, Retford, DN22 7BT",
                "benchmark_setting": "care_home",
                "source_note": "Public care home used as a UKHSA-style setting-classification benchmark row.",
            },
            {
                "case_id": "CASE-003",
                "address_text": "6 Mill Bridge Close, Retford, DN22 6FE",
                "benchmark_setting": "residential",
                "source_note": "Public residential address from HM Land Registry benchmark subsets.",
            },
            {
                "case_id": "CASE-004",
                "address_text": "Retford Library, 17 Churchgate, Retford, DN22 6PE",
                "benchmark_setting": "community_facility",
                "source_note": "Public civic building included as a negative-control non-residential record.",
            },
        ],
    },
    "fixtures/scenario_14_building_candidates.csv": {
        "format": "csv",
        "rows": [
            {
                "building_id": "BLD-001",
                "building_name": "York Minster",
                "address_text": "York Minster, Deangate, York, YO1 7HH",
                "height_m": "23.0",
                "floors": "5",
                "synthetic_note": "Synthetic height benchmark attached to a real public building.",
            },
            {
                "building_id": "BLD-002",
                "building_name": "Hudson House",
                "address_text": "Hudson House, Toft Green, York, YO1 6JT",
                "height_m": "22.0",
                "floors": "7",
                "synthetic_note": "Synthetic height benchmark attached to a real public building.",
            },
            {
                "building_id": "BLD-003",
                "building_name": "County Hall",
                "address_text": "County Hall, Racecourse Lane, Northallerton, DL7 8AD",
                "height_m": "15.0",
                "floors": "4",
                "synthetic_note": "Synthetic height benchmark attached to a real public building.",
            },
            {
                "building_id": "BLD-004",
                "building_name": "The Grand Hotel York",
                "address_text": "The Grand, Station Rise, York, YO1 6GD",
                "height_m": "18.5",
                "floors": "6",
                "synthetic_note": "Synthetic height benchmark attached to a real public building.",
            },
            {
                "building_id": "BLD-005",
                "building_name": "York Hospital South Block",
                "address_text": "York Hospital, Wigginton Road, York, YO31 8HE",
                "height_m": "21.0",
                "floors": "8",
                "synthetic_note": "Synthetic height benchmark attached to a real public building.",
            },
            {
                "building_id": "BLD-006",
                "building_name": "Scarborough Town Hall",
                "address_text": "Town Hall, St Nicholas Street, Scarborough, YO11 2HG",
                "height_m": "14.0",
                "floors": "3",
                "synthetic_note": "Synthetic height benchmark attached to a real public building.",
            },
        ],
    },
    "fixtures/scenario_15_uprn_geography_sample.csv": {
        "format": "csv",
        "rows": [
            {
                "sample_id": "UG-001",
                "uprn": "100023336959",
                "label": "Foreign, Commonwealth & Development Office, King Charles Street",
            },
            {
                "sample_id": "UG-002",
                "uprn": "100120786206",
                "label": "3 The Magnolias, Bicester",
            },
            {
                "sample_id": "UG-003",
                "uprn": "100032031210",
                "label": "Retford Library",
            },
        ],
    },
    "fixtures/scenario_16_patient_sample.csv": {
        "format": "csv",
        "rows": [
            {
                "patient_id": "PT-001",
                "address_text": "50 Canal Road, Worksop, S80 2EH",
                "synthetic_note": "Synthetic patient row anchored to a public address.",
            },
            {
                "patient_id": "PT-002",
                "address_text": "Church Lane 1 The Close, Carlton in Lindrick, Worksop, S81 9EH",
                "synthetic_note": "Synthetic patient row anchored to a public address.",
            },
            {
                "patient_id": "PT-003",
                "address_text": "The Old Farm House, 1 Corner Farm Drive, Everton, DN10 5AN",
                "synthetic_note": "Synthetic patient row anchored to a public address.",
            },
            {
                "patient_id": "PT-004",
                "address_text": "Ragnall Stable, Main Street, Ragnall, NG22 0RU",
                "synthetic_note": "Synthetic patient row anchored to a public address.",
            },
            {
                "patient_id": "PT-005",
                "address_text": "81 Cobwell Road, Retford, DN22 7DD",
                "synthetic_note": "Synthetic patient row anchored to a public address.",
            },
        ],
    },
    "fixtures/scenario_16_pharmacy_sites.csv": {
        "format": "csv",
        "rows": [
            {
                "site_id": "PH-001",
                "site_name": "Worksop Pharmacy",
                "address_text": "Worksop Pharmacy, 95-97 Bridge Street, Worksop, S80 1DL",
            },
            {
                "site_id": "PH-002",
                "site_name": "Newgate Pharmacy",
                "address_text": "Newgate Pharmacy, 6 Newgate Street, Worksop, S80 2HD",
            },
            {
                "site_id": "PH-003",
                "site_name": "Manton Pharmacy",
                "address_text": "Manton Pharmacy, 1 Richmond Road, Worksop, S80 2TP",
            },
        ],
    },
    "fixtures/scenario_17_street_segments.csv": {
        "format": "csv",
        "rows": [
            {
                "segment_id": "SEG-001",
                "street_name": "Corporation Street",
                "place_name": "Birmingham",
                "width_m": "4.2",
                "gradient_pct": "1.5",
                "synthetic_note": "Synthetic street-width/gradient benchmark row attached to a real public street.",
            },
            {
                "segment_id": "SEG-002",
                "street_name": "Digbeth High Street",
                "place_name": "Birmingham",
                "width_m": "2.9",
                "gradient_pct": "3.4",
                "synthetic_note": "Synthetic street-width/gradient benchmark row attached to a real public street.",
            },
            {
                "segment_id": "SEG-003",
                "street_name": "Summer Lane",
                "place_name": "Birmingham",
                "width_m": "3.1",
                "gradient_pct": "6.8",
                "synthetic_note": "Synthetic street-width/gradient benchmark row attached to a real public street.",
            },
            {
                "segment_id": "SEG-004",
                "street_name": "Broad Street",
                "place_name": "Birmingham",
                "width_m": "5.6",
                "gradient_pct": "1.2",
                "synthetic_note": "Synthetic street-width/gradient benchmark row attached to a real public street.",
            },
            {
                "segment_id": "SEG-005",
                "street_name": "Hockley Hill",
                "place_name": "Birmingham",
                "width_m": "3.8",
                "gradient_pct": "7.4",
                "synthetic_note": "Synthetic street-width/gradient benchmark row attached to a real public street.",
            },
        ],
    },
    "fixtures/scenario_18_referral_wards.csv": {
        "format": "csv",
        "rows": [
            {"ward_name": "Small Heath", "synthetic_referrals": "12", "synthetic_need_index": "92", "synthetic_population": "35000"},
            {"ward_name": "Erdington", "synthetic_referrals": "18", "synthetic_need_index": "70", "synthetic_population": "33000"},
            {"ward_name": "Ladywood", "synthetic_referrals": "16", "synthetic_need_index": "85", "synthetic_population": "28000"},
            {"ward_name": "Sparkbrook", "synthetic_referrals": "10", "synthetic_need_index": "95", "synthetic_population": "31000"},
            {"ward_name": "Selly Oak", "synthetic_referrals": "22", "synthetic_need_index": "60", "synthetic_population": "27000"},
        ],
    },
    "fixtures/scenario_18_service_sites.csv": {
        "format": "csv",
        "rows": [
            {
                "site_id": "BSMH-001",
                "site_name": "Small Heath Health Centre",
                "address_text": "Birmingham & Solihull Mental Health NHS Trust, Small Heath Health Centre, 42 Chapman Road, Small Heath, Birmingham, B10 0PG",
            },
            {
                "site_id": "BSMH-002",
                "site_name": "Northcroft Hospital",
                "address_text": "Birmingham & Solihull Mental Health NHS Trust, Northcroft Hospital, Reservoir Road, Erdington, Birmingham, B23 6DW",
            },
            {
                "site_id": "BSMH-003",
                "site_name": "The Barberry",
                "address_text": "Birmingham & Solihull Mental Health NHS Trust, The Barberry, 25 Vincent Drive, Birmingham, B15 2FG",
            },
        ],
    },
    "fixtures/scenario_19_service_coverage_towns.csv": {
        "format": "csv",
        "rows": [
            {"town_name": "Chester", "synthetic_clients": "84", "synthetic_need_index": "72", "synthetic_note": "Synthetic client cluster."},
            {"town_name": "Macclesfield", "synthetic_clients": "91", "synthetic_need_index": "76", "synthetic_note": "Synthetic client cluster."},
            {"town_name": "Crewe", "synthetic_clients": "67", "synthetic_need_index": "81", "synthetic_note": "Synthetic client cluster."},
            {"town_name": "Ellesmere Port", "synthetic_clients": "73", "synthetic_need_index": "88", "synthetic_note": "Synthetic client cluster."},
            {"town_name": "Tarvin", "synthetic_clients": "24", "synthetic_need_index": "55", "synthetic_note": "Synthetic client cluster."},
        ],
    },
    "fixtures/scenario_19_service_sites.csv": {
        "format": "csv",
        "rows": [
            {
                "site_id": "CWP-001",
                "site_name": "Countess of Chester Health Park",
                "address_text": "Cheshire & Wirral Partnership NHS Foundation Trust, The Countess of Chester Health Park, Chester, CH2 1BQ",
            },
            {
                "site_id": "CWP-002",
                "site_name": "Delamere Resource Centre",
                "address_text": "Cheshire & Wirral Partnership NHS Foundation Trust, Delamere Resource Centre, 45 Delamere Street, Crewe, CW1 2ER",
            },
            {
                "site_id": "CWP-003",
                "site_name": "York House",
                "address_text": "Cheshire & Wirral Partnership NHS Foundation Trust, York House, Soss Moss, Nether Alderley, Macclesfield, SK10 4UJ",
            },
        ],
    },
    "fixtures/scenario_20_patrol_demand_cells.csv": {
        "format": "csv",
        "rows": [
            {"cell_id": "PAT-001", "place_name": "Retford", "synthetic_incidents": "38", "synthetic_vulnerability_index": "77"},
            {"cell_id": "PAT-002", "place_name": "Worksop", "synthetic_incidents": "52", "synthetic_vulnerability_index": "73"},
            {"cell_id": "PAT-003", "place_name": "Tuxford", "synthetic_incidents": "17", "synthetic_vulnerability_index": "64"},
            {"cell_id": "PAT-004", "place_name": "Newark-on-Trent", "synthetic_incidents": "29", "synthetic_vulnerability_index": "69"},
        ],
    },
    "fixtures/scenario_20_patrol_resources.csv": {
        "format": "csv",
        "rows": [
            {
                "resource_id": "POL-001",
                "resource_name": "Crown House",
                "address_text": "Nottinghamshire Police Authority, Crown House, Newcastle Avenue, Worksop, S80 1ET",
            },
            {
                "resource_id": "POL-002",
                "resource_name": "Newark Police Station",
                "address_text": "Nottinghamshire Police, Police Station, Queens Road, Newark, NG24 1LJ",
            },
        ],
    },
}


def _scenario(
    scenario_id: str,
    rank: int,
    title: str,
    example_mode: str,
    support_level: str,
    benchmark_rationale: str,
    populated_prompt: str,
    scenario_return_fields: list[str],
    fixtures: list[str],
    sources: list[dict[str, str]],
    comparator_summary: str,
    mcp_geo_tools: list[str],
    known_gaps: list[str],
    required_terms: list[str],
    reference_output: dict[str, Any],
) -> dict[str, Any]:
    return {
        "id": scenario_id,
        "rank": rank,
        "title": title,
        "exampleMode": example_mode,
        "supportLevel": support_level,
        "benchmarkRationale": benchmark_rationale,
        "populatedPrompt": populated_prompt,
        "scenarioReturnFields": scenario_return_fields,
        "fixtureFiles": fixtures,
        "sources": sources,
        "comparatorSummary": comparator_summary,
        "mcpGeoTools": mcp_geo_tools,
        "knownGaps": known_gaps,
        "requiredTerms": required_terms,
        "referenceOutput": reference_output,
    }


def build_phase1_extension_scenarios(common_header: str) -> list[dict[str, Any]]:
    return [
        _scenario(
            "SG11",
            11,
            "Authoritative postcode result set with cache-freshness guidance",
            "public",
            "partial",
            (
                "Phase 1 evidence showed GOV.UK's `locations-api` as a mature OS Places pattern: "
                "it answers postcode lookups with cached PostgreSQL records and explicit refresh rules. "
                "This benchmark turns that architecture into a concrete prompt using a public postcode."
            ),
            f"""{common_header}

Task:
Given postcode sample file: data/benchmarking/stakeholder_eval/fixtures/scenario_11_postcode_sample.csv

Use MCP-Geo to answer:
"For postcode DN22 6PE, what is the authoritative result set, and how should a cache-backed service keep it fresh?"

Required steps:
- Resolve the postcode to the authoritative OS-backed result set.
- State how many premises the postcode resolves to.
- Distinguish the authoritative address result from any service-layer caching plan.
- Explain how a cache-backed implementation should treat freshness, stale records, and refresh triggers.
- Do not invent internal service metrics that MCP-Geo cannot observe directly.

Return:
- concise operational answer
- postcode result table
- cache freshness plan
- stale-risk note
- verification note
- structured output schema
""",
            [
                "concise_operational_answer",
                "postcode_result_table",
                "cache_freshness_plan",
                "stale_risk_note",
                "verification_note",
                "structured_output_schema",
            ],
            ["data/benchmarking/stakeholder_eval/fixtures/scenario_11_postcode_sample.csv"],
            [
                {
                    "title": "GOV.UK locations-api",
                    "url": "https://docs.publishing.service.gov.uk/repos/locations-api.html",
                    "role": "published architecture reference",
                },
                {
                    "title": "How postcodes are added, cached and updated",
                    "url": "https://docs.publishing.service.gov.uk/repos/locations-api/postcodes.html",
                    "role": "published comparator",
                },
            ],
            (
                "Published GOV.UK comparator: postcode records are cached when first requested and "
                "refreshed when they have not been updated in the previous 30 days. The benchmark "
                "expects MCP-Geo to separate the live postcode result from that service-layer cache policy."
            ),
            ["os_mcp.route_query", "os_places.by_postcode"],
            [
                "MCP-Geo exposes the postcode lookup but not GOV.UK's internal PostgreSQL cache metadata or refresh workers.",
                "Any cache policy discussion is therefore comparator-led rather than observed live from MCP-Geo.",
            ],
            ["postcode", "cached", "refreshed", "30 days", "os_places.by_postcode"],
            {
                "concise_answer": "DN22 6PE resolves to a single authoritative premises record in the current OS Places result set: Nottinghamshire County Council, Retford Library, 17 Churchgate, Retford, DN22 6PE. MCP-Geo can return that live result, but the cache-freshness rule comes from GOV.UK's published service pattern rather than from MCP-Geo runtime telemetry.",
                "method_used": [
                    "Call os_places.by_postcode for DN22 6PE to obtain the current authoritative result set.",
                    "Treat cache freshness as a separate service-operations concern and compare against GOV.UK's published locations-api rule set.",
                    "Do not claim MCP-Geo can inspect the downstream PostgreSQL cache unless such telemetry is explicitly exposed.",
                ],
                "datasets_tools_used": [
                    "MCP-Geo tools: os_mcp.route_query, os_places.by_postcode",
                    "Published comparator: GOV.UK locations-api postcode cache and refresh documentation",
                ],
                "confidence_caveats": [
                    "High confidence on the live postcode result because it comes directly from OS Places.",
                    "Cache-freshness guidance is comparator-led: MCP-Geo does not expose live cache age, refresh-worker status, or cache hit ratios.",
                ],
                "verification_steps": [
                    "Re-run os_places.by_postcode for DN22 6PE and confirm the premises count remains one.",
                    "If this pattern is implemented in a service, log cache age and last-refresh timestamps separately from the authoritative result payload.",
                    "Compare any local refresh schedule against GOV.UK's published 30-day refresh rule before treating it as aligned.",
                ],
                "structured_output": {
                    "postcode": "DN22 6PE",
                    "resultCount": 1,
                    "addresses": [
                        {
                            "uprn": "100032031210",
                            "address": "NOTTINGHAMSHIRE COUNTY COUNCIL, RETFORD LIBRARY, 17, CHURCHGATE, RETFORD, DN22 6PE",
                            "classification": "Library",
                        }
                    ],
                    "cachePolicyComparator": {
                        "publishedRule": "refresh cached postcode records after 30 days if not updated sooner",
                        "observedByMcpGeo": False,
                    },
                    "suggestedExportFormat": "JSON response plus CSV postcode-address extract.",
                },
                "concise_operational_answer": "DN22 6PE currently resolves to one authoritative record. A cache-backed service should keep the live result separate from the published 30-day refresh policy.",
                "postcode_result_table": [
                    {
                        "postcode": "DN22 6PE",
                        "uprn": "100032031210",
                        "address": "NOTTINGHAMSHIRE COUNTY COUNCIL, RETFORD LIBRARY, 17, CHURCHGATE, RETFORD, DN22 6PE",
                        "classification": "Library",
                    }
                ],
                "cache_freshness_plan": [
                    "Cache the postcode result after first lookup.",
                    "Record the cache timestamp separately from the authoritative OS payload.",
                    "Refresh cached postcode records when they have not been updated in the previous 30 days.",
                ],
                "stale_risk_note": "MCP-Geo can show the current authoritative result, but it cannot prove whether a downstream service cache is stale unless explicit cache telemetry is added.",
                "verification_note": "Confirm the postcode still resolves to one premises record and that any downstream cache refresh schedule matches the published GOV.UK rule.",
                "structured_output_schema": [
                    "postcode",
                    "uprn",
                    "address",
                    "classification",
                    "cache_last_refreshed_at",
                    "cache_policy_reference",
                ],
            },
        ),
        _scenario(
            "SG12",
            12,
            "Coordinate-to-address incident resolution and quickest responder comparison",
            "public",
            "partial",
            (
                "Phase 1 highlighted North West Fire Control using AddressBase Premium and the road network "
                "to turn coordinates into addresses and mobilise the quickest resource. This benchmark uses "
                "public responder sites and a public incident coordinate in Retford."
            ),
            f"""{common_header}

Task:
Given:
- incident coordinates: latitude 53.3219807, longitude -0.9451639
- responder file: data/benchmarking/stakeholder_eval/fixtures/scenario_12_dispatch_resources.csv

Use MCP-Geo to answer:
"What is the incident address, and which responder reaches it fastest?"

Required steps:
- Resolve the incident coordinate to the nearest authoritative premises or address context.
- Resolve each responder site to an authoritative location.
- Compare route distance and duration from each responder if the routing graph is ready.
- If routing is unavailable, provide the furthest grounded partial result without inventing the fastest resource.
- Make the graph-readiness state explicit.

Return:
- concise dispatch answer
- incident resolution table
- responder comparison table
- blocker_or_limitations
- verification notes
- map recommended description
""",
            [
                "concise_dispatch_answer",
                "incident_resolution_table",
                "responder_comparison_table",
                "blocker_or_limitations",
                "verification_notes",
                "map_recommended_description",
            ],
            ["data/benchmarking/stakeholder_eval/fixtures/scenario_12_dispatch_resources.csv"],
            [
                {
                    "title": "North West Fire Control case study",
                    "url": "https://www.ordnancesurvey.co.uk/customers/case-studies/north-west-fire-control-ltd",
                    "role": "benchmark rationale",
                },
                {
                    "title": "OS Places API nearest lookup",
                    "url": "https://www.ordnancesurvey.co.uk/documentation/product-details/places-api",
                    "role": "tooling analogue",
                },
            ],
            (
                "Published comparator: North West Fire Control used AddressBase Premium and the road "
                "network to identify an address from coordinates and mobilise the quickest resource. "
                "The benchmark answer is complete only when it resolves the coordinate and compares "
                "the responder routes without inventing unavailable timings."
            ),
            ["os_places.nearest", "os_places.search", "os_route.descriptor", "os_route.get"],
            [
                "Responder ranking depends on a ready route graph; otherwise MCP-Geo can only resolve the incident and responder locations.",
                "Dispatch logic, appliance availability, and control-room policy remain external to MCP-Geo.",
            ],
            ["incident", "nearest", "route", "quickest", "graph"],
            {
                "concise_answer": "The incident coordinate resolves to Goodwin Hall, Chancery Lane, Retford, DN22 6DF. On the benchmark route graph, Retford Fire Station is the quickest responder and Tuxford Fire Station is slower by design.",
                "method_used": [
                    "Use os_places.nearest to resolve the incident coordinate to the closest authoritative address context.",
                    "Resolve each responder site with os_places.search or os_places.by_uprn.",
                    "Check os_route.descriptor before comparing responder journeys with os_route.get.",
                ],
                "datasets_tools_used": [
                    "MCP-Geo tools: os_places.nearest, os_places.search, os_route.descriptor, os_route.get",
                    "Benchmark public responder sites for Retford and Tuxford fire stations",
                ],
                "confidence_caveats": [
                    "Incident-to-address resolution is high confidence because the benchmark coordinate is anchored to a known public premises.",
                    "Fastest-responder ranking depends on an active benchmark route graph rather than a full live dispatch system.",
                ],
                "verification_steps": [
                    "Confirm the coordinate still resolves nearest to Goodwin Hall.",
                    "Check os_route.descriptor to ensure the benchmark graph is active before using route timings.",
                    "Treat appliance availability and control-room dispatch policy as out of scope unless supplied separately.",
                ],
                "structured_output": {
                    "incidentAddress": "GOODWIN HALL, CHANCERY LANE, RETFORD, DN22 6DF",
                    "quickestResource": "Retford Fire Station",
                    "graphReadyRequired": True,
                    "suggestedExportFormat": "JSON dispatch comparison plus GeoJSON route layers.",
                },
                "concise_dispatch_answer": "Resolve the coordinate first; if the route graph is ready, Retford Fire Station is the benchmark quickest responder.",
                "incident_resolution_table": [
                    {
                        "incident_label": "Benchmark incident",
                        "lat": 53.3219807,
                        "lon": -0.9451639,
                        "resolved_address": "GOODWIN HALL, CHANCERY LANE, RETFORD, DN22 6DF",
                        "uprn": "100032031287",
                    }
                ],
                "responder_comparison_table": [
                    {"resource_name": "Retford Fire Station", "route_status": "benchmark_fastest", "distance_m": 260.0, "duration_s": 120.0},
                    {"resource_name": "Tuxford Fire Station", "route_status": "benchmark_slower", "distance_m": 11100.0, "duration_s": 900.0},
                ],
                "blocker_or_limitations": "If os_route.descriptor reports the graph as not ready, stop after grounded address resolution and return ROUTE_GRAPH_NOT_READY instead of inventing responder timings.",
                "verification_notes": [
                    "Check the incident and responder points on a map before dispatch rehearsal.",
                    "Review any loaded route warnings or restriction rows on the active benchmark graph.",
                ],
                "map_recommended_description": "Map recommended: show the incident point at Goodwin Hall plus both responder sites and their compared routes.",
            },
        ),
        _scenario(
            "SG13",
            13,
            "UKHSA-style property-setting classification from authoritative address records",
            "public",
            "partial",
            (
                "Phase 1 cited UKHSA using AddressBase with UPRN and BLPU to classify case records "
                "into settings such as care homes and prisons. This benchmark uses public addresses "
                "covering prison, care-home, residential, and civic cases."
            ),
            f"""{common_header}

Task:
Given case-address file: data/benchmarking/stakeholder_eval/fixtures/scenario_13_case_addresses.csv

Use MCP-Geo to answer:
"Which setting does each case belong to, using the safest authoritative identifier workflow available?"

Required steps:
- Resolve each case address to an authoritative premises record.
- Capture the authoritative identifier and classification returned by MCP-Geo.
- Translate the authoritative class into an operational setting label only where the mapping is safe.
- Separate uncertain or non-comparable records from high-confidence setting labels.
- Summarise counts by setting without inventing unsupported medical or public-health attributes.

Return:
- concise classification answer
- case classification table
- setting summary counts
- ambiguous_or_review_table
- caveats
- verification steps
""",
            [
                "concise_classification_answer",
                "case_classification_table",
                "setting_summary_counts",
                "ambiguous_or_review_table",
                "caveats",
                "verification_steps_detail",
            ],
            ["data/benchmarking/stakeholder_eval/fixtures/scenario_13_case_addresses.csv"],
            [
                {
                    "title": "UKHSA COVID-19 settings series technical summary",
                    "url": "https://www.gov.uk/government/publications/covid-19-settings-series-metrics-methodology-and-usage/covid-19-settings-series-reporting-summary",
                    "role": "benchmark rationale",
                },
                {
                    "title": "OS Places API",
                    "url": "https://www.ordnancesurvey.co.uk/documentation/product-details/places-api",
                    "role": "tooling analogue",
                },
            ],
            (
                "Published comparator: UKHSA derives property classifications from AddressBase, using "
                "UPRN and BLPU to support settings reporting. The benchmark rewards safe translation of "
                "authoritative premises classes into operational setting labels, not freehand inference."
            ),
            ["os_places.search", "os_places.by_uprn"],
            [
                "MCP-Geo returns authoritative premises classes, but the UKHSA-specific settings taxonomy is still external to the tool surface.",
                "Batch classification remains an orchestrated workflow rather than a native MCP-Geo tool.",
            ],
            ["uprn", "blpu", "care home", "prison", "residential"],
            {
                "concise_answer": "The benchmark case list resolves cleanly enough to classify one prison, one care home, one residential dwelling, and one community facility. The safe workflow is identifier-first: resolve the UPRN, inspect the authoritative class, then translate only where the class is operationally clear.",
                "method_used": [
                    "Resolve each address with os_places.search and capture the returned UPRN and classification description.",
                    "Translate 'HM Prison Service' to the prison setting and 'Care / Nursing Home' to the care-home setting.",
                    "Keep ambiguous civic or mixed-use records in explicit review or 'other setting' buckets instead of forcing them into UKHSA-style categories.",
                ],
                "datasets_tools_used": [
                    "MCP-Geo tools: os_places.search, os_places.by_uprn",
                    "Published comparator: UKHSA AddressBase, UPRN, and BLPU settings workflow",
                ],
                "confidence_caveats": [
                    "High confidence for prison and care-home rows because their authoritative classes are explicit.",
                    "The benchmark setting labels are a controlled translation layer, not raw AddressBase outputs.",
                ],
                "verification_steps": [
                    "Confirm each resolved UPRN before loading the row into a public-health settings pipeline.",
                    "Keep the raw classificationDescription alongside any operational setting label.",
                    "Route non-standard or mixed-use premises to manual review rather than auto-classifying them.",
                ],
                "structured_output": {
                    "settingCounts": {
                        "prison": 1,
                        "care_home": 1,
                        "residential": 1,
                        "community_facility": 1,
                    },
                    "suggestedExportFormat": "CSV case classification register with raw class and mapped setting columns.",
                },
                "concise_classification_answer": "Resolve first, translate second: the benchmark sample contains one prison, one care home, one residential dwelling, and one community facility.",
                "case_classification_table": [
                    {"case_id": "CASE-001", "uprn": "10013978351", "authoritative_class": "HM Prison Service", "setting_label": "prison"},
                    {"case_id": "CASE-002", "uprn": "100031280110", "authoritative_class": "Care / Nursing Home", "setting_label": "care_home"},
                    {"case_id": "CASE-003", "uprn": "100031272122", "authoritative_class": "Terraced", "setting_label": "residential"},
                    {"case_id": "CASE-004", "uprn": "100032031210", "authoritative_class": "Library", "setting_label": "community_facility"},
                ],
                "setting_summary_counts": [
                    {"setting_label": "prison", "cases": 1},
                    {"setting_label": "care_home", "cases": 1},
                    {"setting_label": "residential", "cases": 1},
                    {"setting_label": "community_facility", "cases": 1},
                ],
                "ambiguous_or_review_table": [],
                "caveats": [
                    "The UKHSA-specific settings taxonomy is richer than the MCP-Geo tool output alone.",
                    "Keep raw premises classes and mapped settings side by side for auditability.",
                ],
                "verification_steps_detail": [
                    "Re-check the UPRN and premises class for any record whose address resolves to multiple candidates.",
                    "Document the settings-translation rules used between raw classes and reporting categories.",
                ],
            },
        ),
        _scenario(
            "SG14",
            14,
            "North Yorkshire-style tall-building threshold review",
            "synthetic",
            "partial",
            (
                "Phase 1 cited North Yorkshire Fire and Rescue using OS Select+Build and OS Building "
                "Features to identify buildings over 18 metres or seven floors. Public building-height "
                "lists are not open, so this benchmark uses a validated synthetic candidate pack tied "
                "to real public buildings."
            ),
            f"""{common_header}

Task:
Given building candidate file: data/benchmarking/stakeholder_eval/fixtures/scenario_14_building_candidates.csv

Use MCP-Geo to answer:
"Which buildings exceed 18 metres or seven floors, and which records need review?"

Required steps:
- Resolve each building to a public location where possible.
- Use the supplied height_m and floors values as synthetic benchmark attributes.
- Identify buildings that exceed either threshold.
- Flag borderline records near 18 metres or seven floors for manual review.
- Make it explicit that the height data in this benchmark is synthetic.

Return:
- concise threshold answer
- exceedance table
- review table
- synthetic_data_note
- caveats
- map recommended description
""",
            [
                "concise_threshold_answer",
                "exceedance_table",
                "review_table",
                "synthetic_data_note",
                "caveats",
                "map_recommended_description",
            ],
            ["data/benchmarking/stakeholder_eval/fixtures/scenario_14_building_candidates.csv"],
            [
                {
                    "title": "North Yorkshire Fire and Rescue Service case study",
                    "url": "https://www.ordnancesurvey.co.uk/customers/case-studies/north-yorkshire-fire-and-rescue-service",
                    "role": "benchmark rationale",
                }
            ],
            (
                "Published comparator: North Yorkshire Fire and Rescue used OS Select+Build and "
                "Building Features to identify buildings over 18 metres or seven floors. This "
                "benchmark carries that threshold question into a synthetic but location-validated pack."
            ),
            ["os_places.search", "os_features.collections", "os_features.query"],
            [
                "MCP-Geo lists building collections but does not yet expose a native building-height query workflow.",
                "The supplied height and floor values are synthetic benchmark data and must be labelled as such in every answer.",
            ],
            ["18 metres", "seven floors", "synthetic", "review", "building"],
            {
                "concise_answer": "Using the synthetic benchmark attributes, four of the six candidate buildings exceed the 18 metres or seven floors threshold and one borderline record should remain in review. The heights and floors are synthetic, even though the building anchors are real public sites and every row keeps a building site reference for audit.",
                "method_used": [
                    "Resolve each building anchor to confirm the location exists.",
                    "Use the supplied synthetic height_m and floors values because MCP-Geo does not yet expose native building-height filters.",
                    "Flag records above either threshold as positive and keep near-threshold rows in review.",
                ],
                "datasets_tools_used": [
                    "Synthetic benchmark file with real public building anchors",
                    "MCP-Geo tools: os_places.search, os_features.collections, os_features.query",
                ],
                "confidence_caveats": [
                    "Confidence is high for the threshold logic inside the fixture.",
                    "Confidence is limited for any claim about live building heights because the underlying height attributes are synthetic.",
                ],
                "verification_steps": [
                    "Confirm each building anchor resolves to the intended public site.",
                    "If a live building-height source becomes available, replace the synthetic attributes before operational use.",
                ],
                "structured_output": {
                    "exceedanceCount": 4,
                    "reviewCount": 1,
                    "buildingSiteReferenceCount": 6,
                    "synthetic": True,
                    "suggestedExportFormat": "CSV exceedance list plus GeoJSON building points or polygons.",
                },
                "concise_threshold_answer": "Four benchmark buildings exceed the 18 metres or seven floors question and one is a borderline review case.",
                "exceedance_table": [
                    {"building_id": "BLD-001", "building_name": "York Minster", "height_m": 23.0, "floors": 5, "trigger": "height"},
                    {"building_id": "BLD-002", "building_name": "Hudson House", "height_m": 22.0, "floors": 7, "trigger": "height_and_floors"},
                    {"building_id": "BLD-004", "building_name": "The Grand Hotel York", "height_m": 18.5, "floors": 6, "trigger": "height"},
                    {"building_id": "BLD-005", "building_name": "York Hospital South Block", "height_m": 21.0, "floors": 8, "trigger": "height_and_floors"},
                ],
                "review_table": [
                    {"building_id": "BLD-006", "building_name": "Scarborough Town Hall", "height_m": 14.0, "floors": 3, "reason": "location resolves but synthetic attributes show no exceedance"},
                    {"building_id": "BLD-003", "building_name": "County Hall", "height_m": 15.0, "floors": 4, "reason": "below threshold but keep as control row"},
                ],
                "synthetic_data_note": "Synthetic scenario: the building heights and floor counts are validated benchmark values attached to real public building anchors because no reusable open tall-building list was found, so each building keeps a site reference and review note instead of pretending the height is live.",
                "caveats": [
                    "This benchmark tests threshold logic and location grounding, not a live OS building-height feed.",
                ],
                "map_recommended_description": "Map recommended: show the resolved building locations and symbolise exceedances versus control rows.",
            },
        ),
        _scenario(
            "SG15",
            15,
            "ONS-style address-to-geography allocation by UPRN",
            "public",
            "partial",
            (
                "Phase 1 highlighted ONS using AddressBase-maintained UPRNs to allocate addresses to "
                "geographies. This benchmark probes exact and best-fit UPRN geography lookup using a "
                "mix of cache-covered and uncached public UPRNs."
            ),
            f"""{common_header}

Task:
Given UPRN sample file: data/benchmarking/stakeholder_eval/fixtures/scenario_15_uprn_geography_sample.csv

Use MCP-Geo to answer:
"For each UPRN, what geographies are available in exact and best-fit mode, and what is missing?"

Required steps:
- Resolve each UPRN to its authoritative address where possible.
- Call the ONS geography lookup in both exact and best-fit mode.
- Compare exact and best-fit outputs explicitly.
- Separate covered rows from NOT_FOUND rows.
- Report cache provenance and any coverage limitations.

Return:
- concise geography answer
- geography comparison table
- missing_rows_table
- cache_provenance_note
- caveats
- verification notes
""",
            [
                "concise_geography_answer",
                "geography_comparison_table",
                "missing_rows_table",
                "cache_provenance_note",
                "caveats",
                "verification_notes_detail",
            ],
            ["data/benchmarking/stakeholder_eval/fixtures/scenario_15_uprn_geography_sample.csv"],
            [
                {
                    "title": "Office for National Statistics COVID-19 Infection Survey methodology",
                    "url": "https://www.ons.gov.uk/peoplepopulationandcommunity/healthandsocialcare/conditionsanddiseases/methodologies/covid19infectionsurveyqmi",
                    "role": "benchmark rationale",
                },
                {
                    "title": "ONS geography cache and UPRN lookup tooling in MCP-Geo",
                    "url": "https://github.com/chris-page-gov/mcp-geo",
                    "role": "tooling reference",
                },
            ],
            (
                "Published Phase 1 finding: ONS uses AddressBase-maintained addresses as a sampling "
                "frame and separately publishes UPRN-based geography allocation products. The "
                "benchmark expects exact-versus-best-fit comparison plus explicit NOT_FOUND handling."
            ),
            ["os_places.by_uprn", "ons_geo.by_uprn", "ons_geo.cache_status"],
            [
                "The current ONS geography cache is sparse and does not cover every public UPRN.",
                "Some rows return only LAD and country in the bootstrap cache, not the full OA/LSOA/MSOA chain.",
            ],
            ["exact", "best_fit", "uprn", "not_found", "lad"],
            {
                "concise_answer": "The benchmark pack shows three different UPRN outcomes: one row has the same LAD result in exact and best-fit mode, one row diverges between Westminster and City of London, and one row is missing entirely from the current cache.",
                "method_used": [
                    "Resolve each UPRN to a public address with os_places.by_uprn.",
                    "Query ons_geo.by_uprn in exact mode and best_fit mode for each UPRN.",
                    "Keep missing rows explicit and report the cache provenance rather than guessing absent geographies.",
                ],
                "datasets_tools_used": [
                    "MCP-Geo tools: os_places.by_uprn, ons_geo.by_uprn, ons_geo.cache_status",
                    "Published comparator: ONS AddressBase-backed geography allocation workflow",
                ],
                "confidence_caveats": [
                    "High confidence on rows that are present in the current cache.",
                    "Coverage is intentionally limited in the bootstrap cache, so NOT_FOUND is an expected benchmark outcome for some UPRNs.",
                ],
                "verification_steps": [
                    "Confirm the current cache status and generation timestamp before relying on any lookup.",
                    "Rebuild the ONS geography cache if wider UPRN coverage is needed.",
                ],
                "structured_output": {
                    "coveredRows": 2,
                    "missingRows": 1,
                    "suggestedExportFormat": "CSV exact/best-fit comparison table plus JSON cache-status snapshot.",
                },
                "concise_geography_answer": "Two of the three benchmark UPRNs resolve in the current cache, and one of those shows an exact-versus-best-fit LAD difference.",
                "geography_comparison_table": [
                    {
                        "uprn": "100023336959",
                        "address": "FOREIGN COMMONWEALTH & DEVELOPMENT OFFICE, KING CHARLES STREET, LONDON, SW1A 2AH",
                        "exact_lad": "Coventry",
                        "best_fit_lad": "Coventry",
                        "difference_flag": False,
                    },
                    {
                        "uprn": "100120786206",
                        "address": "3, THE MAGNOLIAS, BICESTER, OX26 3YG",
                        "exact_lad": "Westminster",
                        "best_fit_lad": "City of London",
                        "difference_flag": True,
                    },
                ],
                "missing_rows_table": [
                    {"uprn": "100032031210", "label": "Retford Library", "exact_status": "NOT_FOUND", "best_fit_status": "NOT_FOUND"}
                ],
                "cache_provenance_note": "Cache provenance should be read from ons_geo.cache_status; the current benchmark cache is a small bootstrap rather than a full production UPRN directory.",
                "caveats": [
                    "The bootstrap cache currently exposes only limited geography fields for the covered UPRNs.",
                ],
                "verification_notes_detail": [
                    "Always compare exact and best-fit results before aggregating public-sector metrics by geography.",
                    "Treat unexpected LAD differences as a signal to inspect the underlying ONS reference product.",
                ],
            },
        ),
        _scenario(
            "SG16",
            16,
            "NHS SCW-style patient distance-to-pharmacy validation",
            "synthetic",
            "partial",
            (
                "Phase 1 cited NHS South, Central and West using AddressBase and Code-Point to identify "
                "people beyond 1.6 kilometres from a pharmacy. Patient-level addresses are not public, "
                "so this benchmark uses synthetic patient rows anchored to public addresses and real "
                "public pharmacy sites."
            ),
            f"""{common_header}

Task:
Given:
- patient file: data/benchmarking/stakeholder_eval/fixtures/scenario_16_patient_sample.csv
- pharmacy file: data/benchmarking/stakeholder_eval/fixtures/scenario_16_pharmacy_sites.csv
- distance threshold: 1.6 kilometres

Use MCP-Geo to answer:
"Which patients are beyond 1.6 kilometres from the nearest pharmacy, and which rows need review?"

Required steps:
- Resolve patient and pharmacy addresses to authoritative locations.
- Compare each patient to the nearest resolved pharmacy.
- Identify rows above the 1.6 km threshold.
- Separate high-confidence rows from unresolved or review rows.
- Keep the synthetic-patient status explicit in the answer and exports.

Return:
- concise distance answer
- patient_distance_table
- threshold_breach_table
- review_table
- synthetic_data_note
- verification notes
""",
            [
                "concise_distance_answer",
                "patient_distance_table",
                "threshold_breach_table",
                "review_table",
                "synthetic_data_note",
                "verification_notes_detail",
            ],
            [
                "data/benchmarking/stakeholder_eval/fixtures/scenario_16_patient_sample.csv",
                "data/benchmarking/stakeholder_eval/fixtures/scenario_16_pharmacy_sites.csv",
            ],
            [
                {
                    "title": "NHS South, Central and West case study",
                    "url": "https://www.ordnancesurvey.co.uk/customers/case-studies/nhs-south-central-and-west-commissioning-support-unit",
                    "role": "benchmark rationale",
                }
            ],
            (
                "Published comparator: NHS SCW used AddressBase and Code-Point to identify dispensing-list "
                "patients more than 1.6 km from their nearest pharmacy. The benchmark rewards careful "
                "distance ranking plus explicit synthetic-data labelling."
            ),
            ["os_places.search", "os_places.by_postcode"],
            [
                "MCP-Geo does not yet expose a native nearest-facility-by-category workflow for pharmacies.",
                "The patient rows are synthetic and must be labelled synthetic in every answer and export.",
            ],
            ["1.6", "pharmacy", "nearest", "synthetic", "review"],
            {
                "concise_answer": "In the benchmark pack, three synthetic patient rows are beyond the 1.6 km threshold, one is within range, and one should stay in review until both the patient and nearest pharmacy resolution are confirmed.",
                "method_used": [
                    "Resolve each synthetic patient row and each public pharmacy address to authoritative coordinates.",
                    "Measure each patient against the nearest resolved pharmacy.",
                    "Keep unresolved or low-confidence rows in a review queue instead of forcing a threshold decision.",
                ],
                "datasets_tools_used": [
                    "Synthetic patient benchmark file anchored to public addresses",
                    "Public Worksop pharmacy addresses",
                    "MCP-Geo tools: os_places.search, os_places.by_postcode",
                ],
                "confidence_caveats": [
                    "Distance logic is strong once both patient and pharmacy sites resolve.",
                    "This benchmark uses synthetic patient rows and an external nearest-facility calculation rather than a native MCP-Geo workflow.",
                ],
                "verification_steps": [
                    "Confirm every patient and pharmacy location resolves cleanly before applying the threshold.",
                    "Re-run the nearest-site calculation if the pharmacy list changes.",
                ],
                "structured_output": {
                    "breachCount": 3,
                    "reviewCount": 1,
                    "synthetic": True,
                    "suggestedExportFormat": "CSV patient-to-pharmacy distance table plus CSV review queue.",
                },
                "concise_distance_answer": "Three synthetic benchmark patients are beyond 1.6 km from their nearest pharmacy, one is within range, and one remains in review.",
                "patient_distance_table": [
                    {"patient_id": "PT-001", "nearest_pharmacy": "Worksop Pharmacy", "distance_km": 1.2, "threshold_status": "within"},
                    {"patient_id": "PT-002", "nearest_pharmacy": "Manton Pharmacy", "distance_km": 2.1, "threshold_status": "beyond"},
                    {"patient_id": "PT-003", "nearest_pharmacy": "Worksop Pharmacy", "distance_km": 7.6, "threshold_status": "beyond"},
                    {"patient_id": "PT-004", "nearest_pharmacy": "Worksop Pharmacy", "distance_km": 15.4, "threshold_status": "beyond"},
                    {"patient_id": "PT-005", "nearest_pharmacy": "Worksop Pharmacy", "distance_km": None, "threshold_status": "review"},
                ],
                "threshold_breach_table": [
                    {"patient_id": "PT-002", "distance_km": 2.1},
                    {"patient_id": "PT-003", "distance_km": 7.6},
                    {"patient_id": "PT-004", "distance_km": 15.4},
                ],
                "review_table": [
                    {"patient_id": "PT-005", "reason": "Retford row requires a broader pharmacy site list or confirmation of the nearest resolved site."}
                ],
                "synthetic_data_note": "Synthetic scenario: patient rows are benchmark-only records anchored to public addresses because real dispensing-list patient addresses are not public.",
                "verification_notes_detail": [
                    "Confirm the nearest pharmacy list covers the operational area before using the threshold output.",
                    "Keep the synthetic patient flag in any downstream export or scorecard.",
                ],
            },
        ),
        _scenario(
            "SG17",
            17,
            "Transport for West Midlands-style street width and gradient bottleneck review",
            "synthetic",
            "blocked",
            (
                "Phase 1 described Transport for West Midlands deriving street width and gradient "
                "insights at fine spatial granularity. Public segment-level width and gradient outputs "
                "were not available, so this benchmark uses a synthetic segment pack tied to real public streets."
            ),
            f"""{common_header}

Task:
Given street segment file: data/benchmarking/stakeholder_eval/fixtures/scenario_17_street_segments.csv

Use MCP-Geo to answer:
"Which street segments are the main accessibility bottlenecks if width under 3.2 m or gradient over 5% is a concern?"

Required steps:
- Resolve the named streets and confirm the place context.
- Use the supplied synthetic width_m and gradient_pct attributes.
- Flag segments breaching width, gradient, or both thresholds.
- Rank the worst bottlenecks.
- Make clear that the width and gradient figures are synthetic benchmark data.

Return:
- concise bottleneck answer
- bottleneck_table
- review_or_control_table
- synthetic_data_note
- caveats
- map recommended description
""",
            [
                "concise_bottleneck_answer",
                "bottleneck_table",
                "review_or_control_table",
                "synthetic_data_note",
                "caveats",
                "map_recommended_description",
            ],
            ["data/benchmarking/stakeholder_eval/fixtures/scenario_17_street_segments.csv"],
            [
                {
                    "title": "Transport for West Midlands case study",
                    "url": "https://www.ordnancesurvey.co.uk/customers/case-studies/transport-for-west-midlands",
                    "role": "benchmark rationale",
                }
            ],
            (
                "Published comparator: TfWM described generating street widths at 1 m intervals and "
                "street-gradient insights from OS datasets. This benchmark is synthetic because that "
                "granular derived output is not openly published for reuse."
            ),
            ["os_names.find", "os_features.collections", "os_features.query"],
            [
                "MCP-Geo has no native street-width or gradient derivation tool today.",
                "The width and gradient figures are synthetic benchmark values and must remain clearly labelled as such.",
            ],
            ["width", "gradient", "synthetic", "bottleneck", "3.2"],
            {
                "concise_answer": "Using the synthetic benchmark attributes, three street segments are bottlenecks: Digbeth High Street breaches the width threshold, Summer Lane breaches both thresholds, and Hockley Hill breaches the gradient threshold. The numbers are synthetic even though the streets are real.",
                "method_used": [
                    "Resolve the named streets as real public streets in Birmingham.",
                    "Apply the width and gradient thresholds to the supplied synthetic segment attributes.",
                    "Rank segments breaching both thresholds ahead of single-threshold breaches.",
                ],
                "datasets_tools_used": [
                    "Synthetic street segment benchmark file tied to real public streets",
                    "MCP-Geo tools: os_names.find, os_features.collections, os_features.query",
                ],
                "confidence_caveats": [
                    "Confidence is high for the thresholding inside the fixture.",
                    "There is no live MCP-Geo derivation of street width or gradient yet, so the output remains benchmark-only.",
                ],
                "verification_steps": [
                    "Resolve every street name to the intended place context.",
                    "Replace the synthetic width and gradient fields with a live derivation source before operational use.",
                ],
                "structured_output": {
                    "bottleneckCount": 3,
                    "synthetic": True,
                    "suggestedExportFormat": "CSV bottleneck ranking plus GeoJSON segment overlays when live geometry becomes available.",
                },
                "concise_bottleneck_answer": "Three synthetic benchmark street segments are the main accessibility bottlenecks.",
                "bottleneck_table": [
                    {"segment_id": "SEG-003", "street_name": "Summer Lane", "width_m": 3.1, "gradient_pct": 6.8, "breach_type": "width_and_gradient"},
                    {"segment_id": "SEG-002", "street_name": "Digbeth High Street", "width_m": 2.9, "gradient_pct": 3.4, "breach_type": "width"},
                    {"segment_id": "SEG-005", "street_name": "Hockley Hill", "width_m": 3.8, "gradient_pct": 7.4, "breach_type": "gradient"},
                ],
                "review_or_control_table": [
                    {"segment_id": "SEG-001", "street_name": "Corporation Street", "status": "control"},
                    {"segment_id": "SEG-004", "street_name": "Broad Street", "status": "control"},
                ],
                "synthetic_data_note": "Synthetic scenario: width and gradient values are benchmark-only derived attributes tied to real public streets.",
                "caveats": [
                    "This is a blocked first-class workflow in MCP-Geo today because the derivation layer is not exposed.",
                ],
                "map_recommended_description": "Map recommended: show Birmingham street segments coloured by width/gradient breach type.",
            },
        ),
        _scenario(
            "SG18",
            18,
            "Birmingham and Solihull referral inequity review by ward",
            "synthetic",
            "partial",
            (
                "Phase 1 cited Birmingham and Solihull Mental Health NHS Foundation Trust using OS "
                "boundaries and basemaps to visualise referral patterns and inequities. The referral "
                "counts in this benchmark are synthetic, but the wards and service sites are real."
            ),
            f"""{common_header}

Task:
Given:
- ward file: data/benchmarking/stakeholder_eval/fixtures/scenario_18_referral_wards.csv
- service site file: data/benchmarking/stakeholder_eval/fixtures/scenario_18_service_sites.csv

Use MCP-Geo to answer:
"Which wards look under-referred relative to need, and which service sites should review them first?"

Required steps:
- Resolve the ward geography and service site locations.
- Use the supplied synthetic_referrals and synthetic_need_index values.
- Identify wards with high need but comparatively low referrals.
- Associate those wards with the nearest or most relevant resolved service site where possible.
- Keep the synthetic nature of the referral counts explicit.

Return:
- concise inequity answer
- ward_inequity_table
- priority_review_sites
- synthetic_data_note
- caveats
- map recommended description
""",
            [
                "concise_inequity_answer",
                "ward_inequity_table",
                "priority_review_sites",
                "synthetic_data_note",
                "caveats",
                "map_recommended_description",
            ],
            [
                "data/benchmarking/stakeholder_eval/fixtures/scenario_18_referral_wards.csv",
                "data/benchmarking/stakeholder_eval/fixtures/scenario_18_service_sites.csv",
            ],
            [
                {
                    "title": "Birmingham and Solihull Mental Health NHS Foundation Trust case study",
                    "url": "https://www.ordnancesurvey.co.uk/customers/case-studies/birmingham-and-solihull-mental-health-nhs-foundation-trust",
                    "role": "benchmark rationale",
                }
            ],
            (
                "Published comparator: the trust used OS boundaries and mapping to visualise referrals "
                "and inequities. The benchmark keeps the counts synthetic but expects the geography and "
                "service-site reasoning to stay grounded."
            ),
            ["admin_lookup.find_by_name", "os_places.search"],
            [
                "Referral and need counts are synthetic benchmark values, not live NHS data.",
                "MCP-Geo does not yet expose a native inequity-dashboard workflow; site prioritisation still requires external logic.",
            ],
            ["ward", "inequity", "synthetic", "need", "referrals"],
            {
                "concise_answer": "Small Heath and Sparkbrook are the clearest synthetic under-referral wards in the benchmark because they pair the highest need scores with the lowest referral counts. Small Heath Health Centre should review Small Heath first, and central Birmingham teams should review Sparkbrook next.",
                "method_used": [
                    "Resolve the ward names and service site addresses.",
                    "Compare synthetic_referrals against synthetic_need_index to identify high-need / low-referral wards.",
                    "Assign review priority to the most relevant resolved service sites.",
                ],
                "datasets_tools_used": [
                    "Synthetic ward referral benchmark file",
                    "Public BSMHFT service-site addresses",
                    "MCP-Geo tools: admin_lookup.find_by_name, os_places.search",
                ],
                "confidence_caveats": [
                    "Geography and service-site resolution are grounded.",
                    "Referral counts and need scores are synthetic and should not be treated as live NHS performance data.",
                ],
                "verification_steps": [
                    "Confirm each ward resolves to the intended Birmingham context.",
                    "Replace synthetic counts with approved referral and need data before operational use.",
                ],
                "structured_output": {
                    "priorityWardCount": 2,
                    "synthetic": True,
                    "suggestedExportFormat": "CSV ward inequity table plus map-ready service-site overlay.",
                },
                "concise_inequity_answer": "Two synthetic benchmark wards stand out for review: Small Heath and Sparkbrook.",
                "ward_inequity_table": [
                    {"ward_name": "Small Heath", "synthetic_referrals": 12, "synthetic_need_index": 92, "priority": "high"},
                    {"ward_name": "Sparkbrook", "synthetic_referrals": 10, "synthetic_need_index": 95, "priority": "high"},
                    {"ward_name": "Ladywood", "synthetic_referrals": 16, "synthetic_need_index": 85, "priority": "medium"},
                ],
                "priority_review_sites": [
                    {"site_name": "Small Heath Health Centre", "focus_wards": ["Small Heath", "Sparkbrook"]},
                    {"site_name": "Northcroft Hospital", "focus_wards": ["Erdington"]},
                ],
                "synthetic_data_note": "Synthetic scenario: referral counts and need indices are benchmark-only values attached to real wards and real service sites.",
                "caveats": [
                    "Under-referral signals in this benchmark are illustrative rather than operational.",
                ],
                "map_recommended_description": "Map recommended: show resolved wards shaded by synthetic need-versus-referral gap and overlay the trust service sites.",
            },
        ),
        _scenario(
            "SG19",
            19,
            "Cheshire and Wirral service-location coverage versus client distribution",
            "synthetic",
            "partial",
            (
                "Phase 1 cited Cheshire and Wirral Partnership NHS Foundation Trust using OS mapping "
                "to compare client distribution with service locations. The client counts here are "
                "synthetic, while the towns and trust sites are real public references."
            ),
            f"""{common_header}

Task:
Given:
- client cluster file: data/benchmarking/stakeholder_eval/fixtures/scenario_19_service_coverage_towns.csv
- service site file: data/benchmarking/stakeholder_eval/fixtures/scenario_19_service_sites.csv

Use MCP-Geo to answer:
"Which client clusters look least well served by the current site pattern?"

Required steps:
- Resolve the towns and service sites.
- Use the supplied synthetic_clients and synthetic_need_index values.
- Compare the client clusters with the current service-site distribution.
- Highlight the clusters that look least well served.
- Keep the synthetic client counts explicit in every summary and export.

Return:
- concise coverage answer
- underserved_cluster_table
- service_site_context_table
- synthetic_data_note
- caveats
- verification notes
""",
            [
                "concise_coverage_answer",
                "underserved_cluster_table",
                "service_site_context_table",
                "synthetic_data_note",
                "caveats",
                "verification_notes_detail",
            ],
            [
                "data/benchmarking/stakeholder_eval/fixtures/scenario_19_service_coverage_towns.csv",
                "data/benchmarking/stakeholder_eval/fixtures/scenario_19_service_sites.csv",
            ],
            [
                {
                    "title": "Cheshire and Wirral Partnership NHS Foundation Trust case study",
                    "url": "https://www.ordnancesurvey.co.uk/customers/case-studies/cheshire-and-wirral-partnership-nhs-foundation-trust",
                    "role": "benchmark rationale",
                }
            ],
            (
                "Published comparator: Cheshire and Wirral Partnership used OS mapping to compare "
                "client distribution with service locations. The benchmark reproduces the service-coverage "
                "logic using synthetic client counts and real site anchors."
            ),
            ["os_names.find", "os_places.search"],
            [
                "Client counts and need indices are synthetic benchmark values.",
                "MCP-Geo does not yet expose a native service-network optimisation workflow.",
            ],
            ["service", "clients", "synthetic", "coverage", "underserved"],
            {
                "concise_answer": "In the benchmark client pattern, Ellesmere Port and Tarvin look least well served because they are not colocated with the named trust sites and carry meaningful synthetic demand. Chester and Macclesfield align more closely with the current site pattern.",
                "method_used": [
                    "Resolve the cluster towns and trust service sites.",
                    "Compare synthetic client volume and need against the current service-site pattern.",
                    "Flag clusters without a clearly colocated or nearby service site for review.",
                ],
                "datasets_tools_used": [
                    "Synthetic client-cluster benchmark file",
                    "Public Cheshire and Wirral Partnership service-site addresses",
                    "MCP-Geo tools: os_names.find, os_places.search",
                ],
                "confidence_caveats": [
                    "Town and site locations are grounded.",
                    "The client distribution is synthetic and should be treated as a planning benchmark only.",
                ],
                "verification_steps": [
                    "Confirm the town anchors resolve to the intended Cheshire context.",
                    "Replace synthetic client counts with approved service-planning data before any operational decision.",
                ],
                "structured_output": {
                    "underservedClusterCount": 2,
                    "synthetic": True,
                    "suggestedExportFormat": "CSV underserved cluster table plus map-ready town/service-site overlay.",
                },
                "concise_coverage_answer": "Ellesmere Port and Tarvin are the clearest synthetic underserved clusters in the benchmark.",
                "underserved_cluster_table": [
                    {"town_name": "Ellesmere Port", "synthetic_clients": 73, "synthetic_need_index": 88, "coverage_status": "underserved_review"},
                    {"town_name": "Tarvin", "synthetic_clients": 24, "synthetic_need_index": 55, "coverage_status": "underserved_review"},
                ],
                "service_site_context_table": [
                    {"site_name": "Countess of Chester Health Park", "context": "closest major site for Chester and nearby clusters"},
                    {"site_name": "Delamere Resource Centre", "context": "Crewe-aligned service site"},
                    {"site_name": "York House", "context": "Macclesfield-aligned service site"},
                ],
                "synthetic_data_note": "Synthetic scenario: client counts and need indices are benchmark-only values attached to real towns and real trust sites.",
                "caveats": [
                    "No live service-capacity or appointment data is included in this benchmark.",
                ],
                "verification_notes_detail": [
                    "Validate cluster-to-site travel times before acting on a service-coverage recommendation.",
                ],
            },
        ),
        _scenario(
            "SG20",
            20,
            "Policing patrol-planning hotspot review with live resource locations",
            "synthetic",
            "blocked",
            (
                "Phase 1 included a policing procurement that described map-driven analysis, demand "
                "prediction, patrol planning, and live resource location using Ordnance Survey and "
                "AddressBase data. Incident demand is private, so this benchmark uses synthetic hotspots "
                "anchored to real public places and police resource sites."
            ),
            f"""{common_header}

Task:
Given:
- patrol demand file: data/benchmarking/stakeholder_eval/fixtures/scenario_20_patrol_demand_cells.csv
- patrol resource file: data/benchmarking/stakeholder_eval/fixtures/scenario_20_patrol_resources.csv

Use MCP-Geo to answer:
"Which hotspots appear least well covered by the current police resource pattern, and what should be reviewed first?"

Required steps:
- Resolve the synthetic hotspot place names and the public police resource sites.
- Use the supplied synthetic_incidents and synthetic_vulnerability_index values.
- Highlight hotspots that appear least well covered by the current resource pattern.
- Avoid pretending MCP-Geo can run full patrol optimisation or demand prediction when it cannot.
- Keep the synthetic status explicit in the answer and outputs.

Return:
- concise patrol answer
- hotspot_priority_table
- resource_context_table
- synthetic_data_note
- capability_gap_note
- map recommended description
""",
            [
                "concise_patrol_answer",
                "hotspot_priority_table",
                "resource_context_table",
                "synthetic_data_note",
                "capability_gap_note",
                "map_recommended_description",
            ],
            [
                "data/benchmarking/stakeholder_eval/fixtures/scenario_20_patrol_demand_cells.csv",
                "data/benchmarking/stakeholder_eval/fixtures/scenario_20_patrol_resources.csv",
            ],
            [
                {
                    "title": "Police GIS platform procurement notice",
                    "url": "https://www.contractsfinder.service.gov.uk/Notice/6f72e900-e31d-4055-b1cc-bd6528bab4ef",
                    "role": "benchmark rationale",
                }
            ],
            (
                "Published comparator: the procurement described a system supporting map-driven analysis, "
                "demand prediction, patrol planning, and live resource location using authoritative OS "
                "data. MCP-Geo does not yet provide that end-to-end policing workflow natively."
            ),
            ["os_names.find", "os_places.search", "os_mcp.route_query"],
            [
                "Patrol demand and vulnerability values are synthetic benchmark data.",
                "MCP-Geo does not yet expose live patrol optimisation, demand prediction, or resource-allocation logic as a first-class tool.",
            ],
            ["patrol", "resource", "synthetic", "hotspot", "coverage"],
            {
                "concise_answer": "Worksop and Retford are the highest-priority synthetic hotspots in the benchmark. Worksop is at least colocated with one resource anchor, but Retford and Tuxford still look coverage-sensitive when compared with the current resource pattern.",
                "method_used": [
                    "Resolve the named hotspots and public police resource sites.",
                    "Use the supplied synthetic incident and vulnerability values to rank hotspots.",
                    "Describe coverage sensitivity without claiming a full patrol-optimisation result.",
                ],
                "datasets_tools_used": [
                    "Synthetic policing hotspot benchmark file",
                    "Public police resource-site addresses",
                    "MCP-Geo tools: os_names.find, os_places.search, os_mcp.route_query",
                ],
                "confidence_caveats": [
                    "Place and resource resolution are grounded.",
                    "Patrol demand ranking is synthetic and MCP-Geo does not yet provide live patrol optimisation.",
                ],
                "verification_steps": [
                    "Confirm the hotspot anchors and resource sites resolve to the intended Nottinghamshire context.",
                    "Use an operational policing platform for any real patrol-allocation decision.",
                ],
                "structured_output": {
                    "priorityHotspots": ["Worksop", "Retford", "Tuxford"],
                    "synthetic": True,
                    "suggestedExportFormat": "CSV hotspot priority table plus map-ready hotspot/resource overlay.",
                },
                "concise_patrol_answer": "Worksop and Retford are the highest-priority synthetic patrol hotspots in the benchmark, with Tuxford next.",
                "hotspot_priority_table": [
                    {"place_name": "Worksop", "synthetic_incidents": 52, "synthetic_vulnerability_index": 73, "priority": "high"},
                    {"place_name": "Retford", "synthetic_incidents": 38, "synthetic_vulnerability_index": 77, "priority": "high"},
                    {"place_name": "Tuxford", "synthetic_incidents": 17, "synthetic_vulnerability_index": 64, "priority": "medium"},
                ],
                "resource_context_table": [
                    {"resource_name": "Crown House", "context": "Worksop-aligned public resource anchor"},
                    {"resource_name": "Newark Police Station", "context": "Newark-aligned public resource anchor"},
                ],
                "synthetic_data_note": "Synthetic scenario: hotspot demand and vulnerability values are benchmark-only values attached to real public places and resource sites.",
                "capability_gap_note": "Blocked first-class workflow: MCP-Geo can ground places and resource sites, but it does not yet provide patrol optimisation, demand prediction, or live resource-allocation tooling.",
                "map_recommended_description": "Map recommended: show hotspot places sized by synthetic demand and overlay the resolved police resource sites.",
            },
        ),
    ]
