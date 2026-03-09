#!/usr/bin/env python3
"""Build and validate the MCP-Geo stakeholder evaluation benchmark pack."""

from __future__ import annotations

import argparse
import csv
import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

DATE_STAMP = "2026-03-09"
REPO_ROOT = Path(__file__).resolve().parents[1]
PACK_ROOT = REPO_ROOT / "data" / "benchmarking" / "stakeholder_eval"
FIXTURE_ROOT = PACK_ROOT / "fixtures"
REFERENCE_ROOT = PACK_ROOT / "reference_outputs"
PACK_JSON_PATH = PACK_ROOT / "benchmark_pack_v1.json"
REPORT_PATH = REPO_ROOT / "docs" / "reports" / "MCP-Geo_evaluation_questions.md"
WORKFLOW_REPORT_PATH = (
    REPO_ROOT / "docs" / "reports" / f"mcp_geo_stakeholder_benchmark_workflow_{DATE_STAMP}.md"
)

COMMON_HEADER = """You are GPT-5.4 using MCP-Geo as the authoritative geospatial tool layer.

Rules:
- Use MCP-Geo tools wherever possible rather than answering from memory.
- Prefer authoritative OS-backed data and identifiers.
- Never invent UPRNs, geometries, classifications, or road-network facts.
- If data is missing, stale, ambiguous, or unavailable, say so explicitly.
- Show the exact reasoning steps in operational form, not hidden chain-of-thought: dataset discovery, lookup, joins, filters, overlays, routing, aggregation, and verification.
- Distinguish confirmed results from assumptions or inferred limitations.
- Return:
  1) concise answer
  2) method used
  3) datasets/tools used
  4) confidence and caveats
  5) verification steps
  6) exportable structured output where relevant
- Where useful, produce both a short narrative answer and a machine-readable table/JSON block.
- Where a map would materially help, say “Map recommended” and describe what should be shown."""

COMMON_RETURN_FIELDS = [
    "concise_answer",
    "method_used",
    "datasets_tools_used",
    "confidence_caveats",
    "verification_steps",
    "structured_output",
]

RUBRIC = {
    "name": "MCP-Geo stakeholder benchmark rubric",
    "version": "1.0",
    "description": (
        "A stakeholder-facing rubric adapted for geospatial QA, identifier-heavy joins, "
        "and operational evidence packs. The scoring model is stricter than the existing "
        "tool-routing harness because it evaluates answer quality, provenance, and "
        "verification readiness rather than only tool choice."
    ),
    "dimensions": [
        {
            "id": "answer_contract",
            "label": "Answer Contract",
            "points": 20,
            "checks": [
                "All six reusable-header return items are present.",
                "All scenario-specific return items are present.",
                "Short answer and structured output do not contradict each other.",
            ],
        },
        {
            "id": "geospatial_grounding",
            "label": "Geospatial Grounding",
            "points": 20,
            "checks": [
                "Incident/site/area inputs are resolved to explicit geometry, address, or identifier references.",
                "Spatial operations are stated operationally: lookup, join, intersect, route, aggregate, verify.",
                "Maps are recommended when the scenario materially benefits from spatial inspection.",
            ],
        },
        {
            "id": "identifier_integrity",
            "label": "Identifier Integrity",
            "points": 15,
            "checks": [
                "UPRN/address reasoning distinguishes confirmed identifiers from inferred matches.",
                "Duplicates, collisions, and hierarchy issues are surfaced explicitly.",
                "Missing-record explanations are ranked by evidence rather than guessed.",
            ],
        },
        {
            "id": "evidence_alignment",
            "label": "Evidence and Comparator Alignment",
            "points": 15,
            "checks": [
                "Public-source comparator findings are referenced when available.",
                "Synthetic scenarios are labelled synthetic in the answer and output tables.",
                "Published findings are compared cautiously rather than treated as generated output.",
            ],
        },
        {
            "id": "uncertainty",
            "label": "Uncertainty and Caveats",
            "points": 10,
            "checks": [
                "Tooling, dataset, licensing, and freshness gaps are named.",
                "Blocked workflows return the furthest grounded partial result.",
                "Caveats are concrete enough for an operational reviewer to act on them.",
            ],
        },
        {
            "id": "verification_exports",
            "label": "Verification and Export Readiness",
            "points": 10,
            "checks": [
                "Verification steps are explicit, ordered, and scenario-specific.",
                "Export formats are suggested in a way that fits the evidence produced.",
                "High-risk scenarios include a field-check or manual-review plan.",
            ],
        },
        {
            "id": "dataset_traceability",
            "label": "Dataset and Tool Traceability",
            "points": 10,
            "checks": [
                "Datasets, tools, and external layers are named precisely.",
                "Known MCP-Geo gaps are made explicit when the scenario exceeds current capability.",
                "The answer differentiates MCP-Geo outputs from supplied fixture data.",
            ],
        },
    ],
    "thresholds": {
        "excellent": 90,
        "good": 75,
        "acceptable": 60,
        "poor": 40,
        "fail": 0,
    },
}

FIXTURE_SPECS: dict[str, dict[str, Any]] = {
    "fixtures/scenario_01_incident_zone.wkt": {
        "format": "text",
        "content": "POLYGON((-0.946200 53.321400,-0.946200 53.318800,-0.943000 53.318800,-0.943000 53.321400,-0.946200 53.321400))\n",
    },
    "fixtures/scenario_01_vulnerable_households.csv": {
        "format": "csv",
        "rows": [
            {
                "record_id": "VH-001",
                "address_text": "Navigation Lodge, Wharf Road, Retford, DN22 6EN",
                "postcode": "DN22 6EN",
                "resident_group": "mobility_support",
                "support_notes": "Wheelchair user; evacuation support required.",
                "synthetic_case_note": "Synthetic vulnerability annotation applied to a real HMLR address.",
            },
            {
                "record_id": "VH-002",
                "address_text": "6 Mill Bridge Close, Retford, DN22 6FE",
                "postcode": "DN22 6FE",
                "resident_group": "older_person",
                "support_notes": "Lives alone; welfare check requested.",
                "synthetic_case_note": "Synthetic vulnerability annotation applied to a real HMLR address.",
            },
            {
                "record_id": "VH-003",
                "address_text": "6 Mill Bridge Cl, Retford DN22 6FE",
                "postcode": "DN22 6FE",
                "resident_group": "medically_dependent",
                "support_notes": "Oxygen dependency recorded in synthetic benchmark notes.",
                "synthetic_case_note": "Intentional duplicate-address variant for join and dedupe scoring.",
            },
            {
                "record_id": "VH-004",
                "address_text": "18 Mill Bridge Close, Retford, DN22 6FE",
                "postcode": "DN22 6FE",
                "resident_group": "young_children",
                "support_notes": "Two children under five in household.",
                "synthetic_case_note": "Synthetic vulnerability annotation applied to a real HMLR address.",
            },
            {
                "record_id": "VH-005",
                "address_text": "115 Mill Bridge Close, Retford, DN22 6FE",
                "postcode": "DN22 6FE",
                "resident_group": "visual_impairment",
                "support_notes": "Accessible transport required.",
                "synthetic_case_note": "Synthetic vulnerability annotation applied to a real HMLR address.",
            },
            {
                "record_id": "VH-006",
                "address_text": "13 Welham Road, Retford, DN22 6TN",
                "postcode": "DN22 6TN",
                "resident_group": "older_person",
                "support_notes": "Outside incident polygon in benchmark ground truth.",
                "synthetic_case_note": "Real HMLR address kept as negative-control record.",
            },
            {
                "record_id": "VH-007",
                "address_text": "22A Chapelgate, Retford, DN22 6PJ",
                "postcode": "DN22 6PJ",
                "resident_group": "carer_household",
                "support_notes": "Outside incident polygon in benchmark ground truth.",
                "synthetic_case_note": "Real HMLR address kept as negative-control record.",
            },
        ],
    },
    "fixtures/scenario_02_address_batch.csv": {
        "format": "csv",
        "rows": [
            {"source_id": "ADDR-001", "address_text": "81 COBWELL RD, RETFORD DN22 7DD"},
            {"source_id": "ADDR-002", "address_text": "Navigation Lodge, Wharf Rd, Retford DN22 6EN"},
            {"source_id": "ADDR-003", "address_text": "6 Millbridge Close, Retford DN22 6FE"},
            {"source_id": "ADDR-004", "address_text": "Canalside Wharf 6 Wharf Road, Retford DN22 6JL"},
            {"source_id": "ADDR-005", "address_text": "22A Chapel Gate, Retford, DN22 6PJ"},
            {"source_id": "ADDR-006", "address_text": "Church Lane 1 The Close, Carlton in Lindrick, Worksop S81 9EH"},
            {"source_id": "ADDR-007", "address_text": "50 Canal Rd, Worksop S80 2EH"},
            {"source_id": "ADDR-008", "address_text": "50 Canal Road, Worksop, S80 2EH"},
            {"source_id": "ADDR-009", "address_text": "The Old Farm House 1 Corner Farm Dr, Everton DN10 5AN"},
            {"source_id": "ADDR-010", "address_text": "Ragnall Stable, Main Street, Ragnall NG22 ORU"},
        ],
    },
    "fixtures/scenario_06_bassetlaw_assets_subset.csv": {
        "format": "csv",
        "rows": [
            {
                "uprn": "100032031194",
                "site": "Land",
                "name_or_number": "Nottinghamshire County Council",
                "street_name": "Chancery Lane",
                "postal_town": "Retford",
                "postcode": "DN22 6DG",
                "easting": "470397",
                "northing": "381121",
                "tenure": "Freehold",
                "occupancy": "Vacant",
                "land_only": "Yes",
            },
            {
                "uprn": "100032031210",
                "site": "Library",
                "name_or_number": "Retford Library 17",
                "street_name": "Churchgate",
                "postal_town": "Retford",
                "postcode": "DN22 6PE",
                "easting": "470548",
                "northing": "381340",
                "tenure": "Freehold",
                "occupancy": "Leasehold",
                "land_only": "No",
            },
            {
                "uprn": "100032031287",
                "site": "Community Centre",
                "name_or_number": "Goodwin Hall",
                "street_name": "Chancery Lane",
                "postal_town": "Retford",
                "postcode": "DN22 6DF",
                "easting": "470361",
                "northing": "381078",
                "tenure": "Freehold",
                "occupancy": "Leasehold",
                "land_only": "No",
            },
            {
                "uprn": "10023266359",
                "site": "Shop",
                "name_or_number": "Retford Shopmobility",
                "street_name": "Chancery Lane",
                "postal_town": "Retford",
                "postcode": "DN22 6EY",
                "easting": "470450",
                "northing": "381086",
                "tenure": "Freehold",
                "occupancy": "Leasehold",
                "land_only": "No",
            },
            {
                "uprn": "10023266361",
                "site": "Car Park",
                "name_or_number": "Public Car Park",
                "street_name": "Chancery Lane",
                "postal_town": "Retford",
                "postcode": "DN22 6EY",
                "easting": "470427",
                "northing": "381075",
                "tenure": "Freehold",
                "occupancy": "",
                "land_only": "Yes",
            },
            {
                "uprn": "10023269092",
                "site": "Car Park",
                "name_or_number": "North Public Car Park",
                "street_name": "Chancery Lane",
                "postal_town": "Retford",
                "postcode": "DN22 6EY",
                "easting": "470441",
                "northing": "381108",
                "tenure": "Freehold",
                "occupancy": "",
                "land_only": "Yes",
            },
            {
                "uprn": "10023270715",
                "site": "Pavillion",
                "name_or_number": "Pavillion at Kings Park",
                "street_name": "Chancery Lane",
                "postal_town": "Retford",
                "postcode": "DN22 6EY",
                "easting": "470320",
                "northing": "380951",
                "tenure": "Freehold",
                "occupancy": "",
                "land_only": "No",
            },
        ],
    },
    "fixtures/scenario_07_property_sample.csv": {
        "format": "csv",
        "rows": [
            {"property_id": "PROP-001", "address_text": "Navigation Lodge, Wharf Road, Retford, DN22 6EN", "source": "HM Land Registry Price Paid 2025"},
            {"property_id": "PROP-002", "address_text": "6 Mill Bridge Close, Retford, DN22 6FE", "source": "HM Land Registry Price Paid 2025"},
            {"property_id": "PROP-003", "address_text": "18 Mill Bridge Close, Retford, DN22 6FE", "source": "HM Land Registry Price Paid 2025"},
            {"property_id": "PROP-004", "address_text": "115 Mill Bridge Close, Retford, DN22 6FE", "source": "HM Land Registry Price Paid 2025"},
            {"property_id": "PROP-005", "address_text": "119 Mill Bridge Close, Retford, DN22 6FE", "source": "HM Land Registry Price Paid 2025"},
            {"property_id": "PROP-006", "address_text": "13 Welham Road, Retford, DN22 6TN", "source": "HM Land Registry Price Paid 2025"},
            {"property_id": "PROP-007", "address_text": "22A Chapelgate, Retford, DN22 6PJ", "source": "HM Land Registry Price Paid 2025"},
        ],
    },
    "fixtures/scenario_08_housing_allocations.csv": {
        "format": "csv",
        "rows": [
            {"source_ref": "ALLOC-001", "site_name": "Abbey Quarter Phase A", "ward": "Selby West", "polling_district": "SEL-A", "expected_units": "120", "geometry_type": "polygon", "status": "allocation"},
            {"source_ref": "ALLOC-002", "site_name": "Cayton East Extension", "ward": "Cayton", "polling_district": "CAY-A", "expected_units": "48", "geometry_type": "polygon", "status": "allocation"},
            {"source_ref": "ALLOC-003", "site_name": "Ripon South Yard", "ward": "Ripon South", "polling_district": "RIP-C", "expected_units": "30", "geometry_type": "polygon", "status": "allocation"},
        ],
    },
    "fixtures/scenario_08_planning_permissions.csv": {
        "format": "csv",
        "rows": [
            {"source_ref": "PERM-011", "site_name": "Abbey Quarter Phase 1", "ward": "Selby West", "polling_district": "SEL-A", "expected_units": "40", "geometry_type": "point", "status": "permission"},
            {"source_ref": "PERM-012", "site_name": "Harbour Rise", "ward": "Cayton", "polling_district": "CAY-B", "expected_units": "25", "geometry_type": "point", "status": "permission"},
            {"source_ref": "PERM-013", "site_name": "Ripon South Yard", "ward": "Ripon South", "polling_district": "RIP-C", "expected_units": "25", "geometry_type": "point", "status": "permission"},
        ],
    },
    "fixtures/scenario_08_site_promoters.csv": {
        "format": "csv",
        "rows": [
            {"source_ref": "PROM-101", "site_name": "Abbey Quarter", "ward": "Selby West", "polling_district": "SEL-A", "expected_units": "120", "geometry_type": "point", "status": "promoter_submission"},
            {"source_ref": "PROM-102", "site_name": "Scarborough North Infill", "ward": "Scarborough North", "polling_district": "SCN-D", "expected_units": "30", "geometry_type": "point", "status": "promoter_submission"},
            {"source_ref": "PROM-103", "site_name": "Cayton East Extension", "ward": "Cayton", "polling_district": "CAY-A", "expected_units": "48", "geometry_type": "point", "status": "promoter_submission"},
        ],
    },
    "fixtures/scenario_09_bduk_subset.csv": {
        "format": "csv",
        "rows": [
            {"uprn": "100032031210", "postcode": "DN22 6PE", "subsidy_control_status": "Gigabit Under Review", "current_gigabit": "false", "future_gigabit": "true"},
            {"uprn": "100032031194", "postcode": "DN22 6DG", "subsidy_control_status": "Gigabit Grey/Black", "current_gigabit": "true", "future_gigabit": "true"},
            {"uprn": "10023266359", "postcode": "DN22 6DF", "subsidy_control_status": "Gigabit Grey/Black", "current_gigabit": "true", "future_gigabit": "true"},
        ],
    },
    "fixtures/scenario_10_council_tax_like.csv": {
        "format": "csv",
        "rows": [
            {"account_ref": "CT-001", "band": "B", "address_text": "81 Cobwell Rd, Retford, DN22 7DD"},
            {"account_ref": "CT-002", "band": "A", "address_text": "Navigation Lodge Wharf Road, Retford DN22 6EN"},
            {"account_ref": "CT-003", "band": "A", "address_text": "6 Millbridge Close, Retford DN22 6FE"},
            {"account_ref": "CT-004", "band": "A", "address_text": "119 Mill Bridge Close, Retford DN22 6FE"},
            {"account_ref": "CT-005", "band": "A", "address_text": "Canalside Wharf, Unit 6, Wharf Road, Retford DN22 6JL"},
            {"account_ref": "CT-006", "band": "B", "address_text": "50 Canal Road, Worksop, S80 2EH"},
            {"account_ref": "CT-007", "band": "C", "address_text": "The Old Farm House, 1 Corner Farm Drive, Everton, DN10 5AN"},
            {"account_ref": "CT-008", "band": "B", "address_text": "Ragnall Stable, Main Street, Ragnall, NG22 0RU"},
        ],
    },
    "fixtures/scenario_10_price_paid_subset.csv": {
        "format": "csv",
        "rows": [
            {"transaction_id": "{44F406B7-4752-1095-E063-4704A8C048D4}", "price_gbp": "101000", "postcode": "DN22 7DD", "paon": "81", "saon": "", "street": "COBWELL ROAD", "town": "RETFORD", "district": "BASSETLAW"},
            {"transaction_id": "{4777E0AF-05FF-5D59-E063-4804A8C09F8E}", "price_gbp": "132000", "postcode": "DN22 6EN", "paon": "NAVIGATION LODGE", "saon": "", "street": "WHARF ROAD", "town": "RETFORD", "district": "BASSETLAW"},
            {"transaction_id": "{49E87C32-43BB-591C-E063-4704A8C00C31}", "price_gbp": "106000", "postcode": "DN22 6FE", "paon": "6", "saon": "", "street": "MILL BRIDGE CLOSE", "town": "RETFORD", "district": "BASSETLAW"},
            {"transaction_id": "{42C129E5-94DB-60A9-E063-4804A8C0C25D}", "price_gbp": "82000", "postcode": "DN22 6FE", "paon": "119", "saon": "", "street": "MILL BRIDGE CLOSE", "town": "RETFORD", "district": "BASSETLAW"},
            {"transaction_id": "{4777E0AF-06AC-5D59-E063-4804A8C09F8E}", "price_gbp": "225000", "postcode": "DN22 6JL", "paon": "CANALSIDE WHARF", "saon": "6", "street": "WHARF ROAD", "town": "RETFORD", "district": "BASSETLAW"},
            {"transaction_id": "{49E87C32-4530-591C-E063-4704A8C00C31}", "price_gbp": "525000", "postcode": "DN22 6SD", "paon": "11", "saon": "", "street": "THE DRIVE", "town": "RETFORD", "district": "BASSETLAW"},
            {"transaction_id": "{44F406B7-47A6-1095-E063-4704A8C048D4}", "price_gbp": "87000", "postcode": "S80 2EH", "paon": "50", "saon": "", "street": "CANAL ROAD", "town": "WORKSOP", "district": "BASSETLAW"},
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


def _build_scenarios() -> list[dict[str, Any]]:
    return [
        _scenario(
            "SG01",
            1,
            "Affected premises and vulnerable households in an incident area",
            "mixed",
            "partial",
            (
                "Public benchmark base: Retford flood-risk-zone references 402042/2 and 167647/3 "
                "from planning.data.gov.uk plus real Retford residential addresses from HM Land "
                "Registry Price Paid Data. Synthetic component: vulnerability categories layered "
                "onto those real addresses because public vulnerable-household datasets are not "
                "openly published at household level."
            ),
            f"""{COMMON_HEADER}

Task:
Given:
- incident geometry: POLYGON((-0.946200 53.321400,-0.946200 53.318800,-0.943000 53.318800,-0.943000 53.321400,-0.946200 53.321400))
- vulnerable-households dataset: data/benchmarking/stakeholder_eval/fixtures/scenario_01_vulnerable_households.csv
- optional critical-sites dataset: none

Use MCP-Geo to answer:
“Which premises and households are affected, and what support-relevant counts can we produce?”

Required steps:
- Resolve the incident geography precisely.
- Identify all affected premises/UPRNs within the incident area.
- Join to the vulnerable-households dataset using the safest available identifier strategy.
- Deduplicate records where multiple address forms point to the same premises.
- Summarise by:
  - total affected premises
  - total affected households/records
  - counts by vulnerability category
  - counts by area/boundary if available
- Flag any ambiguous, unmatched, or duplicate records.
- State what could be wrong because of missing UPRNs, stale address data, or join-quality issues.

Return:
- executive summary
- affected-premises table
- vulnerability summary table
- duplicates/anomalies table
- confidence and caveats
- suggested export format
""",
            [
                "executive_summary",
                "affected_premises_table",
                "vulnerability_summary_table",
                "duplicates_anomalies_table",
                "suggested_export_format",
            ],
            [
                "data/benchmarking/stakeholder_eval/fixtures/scenario_01_incident_zone.wkt",
                "data/benchmarking/stakeholder_eval/fixtures/scenario_01_vulnerable_households.csv",
            ],
            [
                {
                    "title": "Identifying and supporting persons who are vulnerable in an emergency",
                    "url": "https://www.gov.uk/government/publications/identifying-people-who-are-vulnerable-in-a-crisis-guidance-for-emergency-planners-and-responders/identifying-and-supporting-persons-who-are-vulnerable-in-an-emergency-supporting-guidance-for-local-resilience-forums-in-england-html",
                    "role": "benchmark rationale",
                },
                {
                    "title": "HM Land Registry Price Paid Data downloads",
                    "url": "https://www.gov.uk/government/statistical-data-sets/price-paid-data-downloads",
                    "role": "real-address source",
                },
                {
                    "title": "Planning Data flood-risk-zone dataset",
                    "url": "https://www.planning.data.gov.uk/dataset/flood-risk-zone",
                    "role": "incident-area source",
                },
            ],
            (
                "Comparator baseline is structural rather than numeric: Cabinet Office guidance "
                "states that multi-source conversion is time-consuming during emergencies, so this "
                "benchmark expects MCP-Geo to expose joins, dedupe, and caveats explicitly rather "
                "than pretending the supplied synthetic vulnerability file is authoritative."
            ),
            ["os_places.search", "os_places.by_uprn", "ons_geo.by_uprn", "admin_lookup.containing_areas"],
            [
                "This repo does not ship an open vulnerable-household dataset; the benchmark file is synthetic.",
                "OS Places requires a live OS key for direct UPRN resolution in a real run.",
            ],
            ["affected premises", "duplicate", "retford", "synthetic", "export"],
            {
                "concise_answer": "The benchmark incident area affects 4 unique premises and 5 vulnerable-household records after deduplication review. One duplicated address variant maps to the same Mill Bridge Close premises, so the operational answer must separate affected premises from raw records.",
                "method_used": [
                    "Use the supplied incident polygon clipped from planning.data flood-risk-zone references 402042/2 and 167647/3.",
                    "Resolve each supplied address to a candidate premises or UPRN using MCP-Geo address tools where available.",
                    "Join the synthetic vulnerability file by normalized address, then deduplicate the two variants of 6 Mill Bridge Close.",
                    "Assign affected premises to Bassetlaw using the postcode and area context already embedded in the example.",
                ],
                "datasets_tools_used": [
                    "planning.data.gov.uk flood-risk-zone references 402042/2 and 167647/3",
                    "HM Land Registry Price Paid Data 2025 addresses used as the real-address base for the synthetic vulnerability file",
                    "MCP-Geo tools: os_places.search, os_places.by_uprn, ons_geo.by_uprn, admin_lookup.containing_areas",
                ],
                "confidence_caveats": [
                    "Public vulnerable-household data is synthetic in this benchmark, so counts test workflow quality rather than real emergency truth.",
                    "Exact UPRN resolution depends on OS Places availability; without it, a high-quality answer must still report address-level matches and caveats.",
                    "The incident polygon is a clipped operational exercise area derived from authoritative flood-zone geometry rather than the full published geometry.",
                ],
                "verification_steps": [
                    "Re-run the four affected addresses through OS Places or AddressBase-backed matching and confirm the UPRN mapping.",
                    "Verify whether the duplicate 6 Mill Bridge Close records are two services for one household or two households at one premises.",
                    "Cross-check the affected set against the latest flood-warning or incident perimeter before export.",
                ],
                "structured_output": {
                    "affectedPremises": [
                        {"premisesLabel": "Navigation Lodge, Wharf Road, Retford DN22 6EN", "recordCount": 1, "joinQuality": "high", "status": "affected"},
                        {"premisesLabel": "6 Mill Bridge Close, Retford DN22 6FE", "recordCount": 2, "joinQuality": "review_duplicate", "status": "affected"},
                        {"premisesLabel": "18 Mill Bridge Close, Retford DN22 6FE", "recordCount": 1, "joinQuality": "high", "status": "affected"},
                        {"premisesLabel": "115 Mill Bridge Close, Retford DN22 6FE", "recordCount": 1, "joinQuality": "high", "status": "affected"},
                    ],
                    "vulnerabilitySummary": [
                        {"category": "mobility_support", "records": 1},
                        {"category": "older_person", "records": 1},
                        {"category": "medically_dependent", "records": 1},
                        {"category": "young_children", "records": 1},
                        {"category": "visual_impairment", "records": 1},
                    ],
                },
                "executive_summary": "4 affected premises, 5 affected records, 1 duplicate-address anomaly, and 2 negative-control records outside the incident area.",
                "affected_premises_table": [
                    {"premises": "Navigation Lodge, Wharf Road, Retford DN22 6EN", "affectedRecords": 1, "boundary": "Bassetlaw", "notes": "Inside clipped flood incident area"},
                    {"premises": "6 Mill Bridge Close, Retford DN22 6FE", "affectedRecords": 2, "boundary": "Bassetlaw", "notes": "Duplicate address forms require review"},
                    {"premises": "18 Mill Bridge Close, Retford DN22 6FE", "affectedRecords": 1, "boundary": "Bassetlaw", "notes": "Inside clipped flood incident area"},
                    {"premises": "115 Mill Bridge Close, Retford DN22 6FE", "affectedRecords": 1, "boundary": "Bassetlaw", "notes": "Inside clipped flood incident area"},
                ],
                "vulnerability_summary_table": [
                    {"category": "mobility_support", "affectedRecords": 1},
                    {"category": "older_person", "affectedRecords": 1},
                    {"category": "medically_dependent", "affectedRecords": 1},
                    {"category": "young_children", "affectedRecords": 1},
                    {"category": "visual_impairment", "affectedRecords": 1},
                ],
                "duplicates_anomalies_table": [
                    {
                        "issue": "Duplicate candidate",
                        "records": ["VH-002", "VH-003"],
                        "premises": "6 Mill Bridge Close, Retford DN22 6FE",
                        "action": "Manual dedupe before operational export",
                    }
                ],
                "suggested_export_format": "CSV for the premises list plus GeoJSON if point coordinates are resolved during the live MCP-Geo run.",
            },
        ),
        _scenario(
            "SG02",
            2,
            "Batch match free-text addresses to UPRNs at scale",
            "mixed",
            "partial",
            (
                "The input file is synthetic but derived from real HM Land Registry 2025 Bassetlaw "
                "transactions so the benchmark can test messy-address handling without inventing "
                "the underlying real-world addresses."
            ),
            f"""{COMMON_HEADER}

Task:
Given this address file: data/benchmarking/stakeholder_eval/fixtures/scenario_02_address_batch.csv
Answer:
“Match these addresses to authoritative UPRNs, quantify match quality, and explain failures.”

Required steps:
- Inspect the input fields and assess address quality.
- Standardise address strings where possible.
- Use MCP-Geo to match each record to a likely UPRN.
- Classify results into:
  - exact/high-confidence match
  - plausible match needing review
  - unmatched
  - duplicate/collision
- Produce:
  - overall match rate
  - unmatched count
  - duplicate count
  - top 10 failure reasons
  - records needing manual review
- Explain whether live API lookup, cached AddressBase-style data, or both seem to have been used.
- Do not overstate certainty.

Return:
- short summary
- quality metrics
- matched output schema
- review queue
- failure-reason analysis
- recommended remediation actions
""",
            [
                "short_summary",
                "quality_metrics",
                "matched_output_schema",
                "review_queue",
                "failure_reason_analysis",
                "recommended_remediation_actions",
            ],
            ["data/benchmarking/stakeholder_eval/fixtures/scenario_02_address_batch.csv"],
            [
                {
                    "title": "HM Land Registry Price Paid Data downloads",
                    "url": "https://www.gov.uk/government/statistical-data-sets/price-paid-data-downloads",
                    "role": "real-address source",
                },
                {
                    "title": "Use UPRNs to identify locations and use addresses",
                    "url": "https://www.gov.uk/guidance/use-uprns-to-identify-locations-and-use-addresses",
                    "role": "identifier standard",
                },
            ],
            (
                "Comparator baseline is benchmark truth rather than a published percentage: 10 messy "
                "records derived from real addresses should yield 6 exact matches, 2 plausible review "
                "cases, 1 unmatched record, and 1 duplicate/collision pair."
            ),
            ["os_places.search", "os_places.by_uprn", "os_places.by_postcode"],
            [
                "Without an OS key, the live MCP-Geo run cannot complete authoritative address matching in this environment.",
                "The benchmark therefore scores join logic, confidence labelling, and failure explanations rather than raw lookup success alone.",
            ],
            ["match rate", "manual review", "duplicate", "unmatched", "synthetic"],
            {
                "concise_answer": "Reference scoring expects a 60% exact/high-confidence match rate, 2 plausible manual-review cases, 1 unmatched record, and 1 duplicate/collision pair from the 10-row batch.",
                "method_used": [
                    "Normalize punctuation, postcode spacing, street abbreviations, and PAON/SAON ordering before matching.",
                    "Use OS Places or an AddressBase-backed service to resolve candidate UPRNs.",
                    "Separate duplicate raw rows from ambiguous address-to-premises collisions.",
                ],
                "datasets_tools_used": [
                    "Synthetic benchmark batch derived from HM Land Registry Price Paid Data 2025 Bassetlaw rows",
                    "MCP-Geo tools: os_places.search, os_places.by_postcode, os_places.by_uprn",
                ],
                "confidence_caveats": [
                    "The dirty-address file is synthetic, but every underlying address came from a real public record.",
                    "The unmatched case is driven by an intentional postcode typo and should not be forced into a likely match.",
                ],
                "verification_steps": [
                    "Check review-queue records manually against authoritative address lookup.",
                    "Inspect the duplicate pair for 50 Canal Road to confirm whether it is a duplicate raw row rather than a second premises.",
                ],
                "structured_output": {
                    "qualityMetrics": {
                        "totalRecords": 10,
                        "exactHighConfidence": 6,
                        "plausibleReview": 2,
                        "unmatched": 1,
                        "duplicateCollision": 1,
                        "matchRatePercent": 60.0,
                    },
                    "reviewQueue": [
                        {"sourceId": "ADDR-003", "reason": "Millbridge/Mill Bridge normalization needs confirmation"},
                        {"sourceId": "ADDR-006", "reason": "PAON/SAON order reversed for The Close / Church Lane"},
                        {"sourceId": "ADDR-010", "reason": "Postcode typo NG22 ORU prevents safe match"},
                    ],
                    "suggestedExportFormat": "CSV matched results plus a separate CSV manual-review queue.",
                },
                "short_summary": "The pack is calibrated so that the model must surface a 60% exact match rate, one unmatched typo, one duplicate raw-row pair, and two plausible manual-review address normalizations.",
                "quality_metrics": {
                    "total_records": 10,
                    "exact_high_confidence": 6,
                    "plausible_review": 2,
                    "unmatched": 1,
                    "duplicate_collision": 1,
                    "top_failure_reasons": [
                        "postcode typo",
                        "street-name normalization",
                        "PAON/SAON order ambiguity",
                        "duplicate raw row",
                    ],
                },
                "matched_output_schema": [
                    "source_id",
                    "normalized_address",
                    "candidate_uprn",
                    "match_quality",
                    "review_required",
                    "failure_reason",
                ],
                "review_queue": [
                    {"source_id": "ADDR-003", "priority": "medium", "reason": "street name normalization"},
                    {"source_id": "ADDR-006", "priority": "medium", "reason": "sub-building ordering"},
                    {"source_id": "ADDR-010", "priority": "high", "reason": "postcode typo / unmatched"},
                ],
                "failure_reason_analysis": [
                    {"reason": "postcode typo", "count": 1},
                    {"reason": "duplicate raw row", "count": 1},
                    {"reason": "street-name normalization", "count": 1},
                    {"reason": "PAON/SAON ordering", "count": 1},
                ],
                "recommended_remediation_actions": [
                    "Enforce postcode validation before batch submission.",
                    "Retain PAON and SAON in separate fields instead of concatenating them.",
                    "Flag exact duplicate raw rows upstream before UPRN matching.",
                ],
            },
        ),
        _scenario(
            "SG03",
            3,
            "Shortest route between two premises using authoritative road network constraints",
            "public",
            "blocked",
            (
                "Real public sites in Retford are used for the route endpoints, while the comparator "
                "is the Ordnance Survey routing guidance that states network build steps can take "
                "two to three days and should be run overnight."
            ),
            f"""{COMMON_HEADER}

Task:
Given:
- origin: Retford Library, 17 Churchgate, Retford, DN22 6PE
- destination: Goodwin Hall, Chancery Lane, Retford, DN22 6DF
- route mode: EMERGENCY
- optional constraints: avoid known flood-risk-zone reference 167647/3 if the routing engine can represent hazards or closures

Use MCP-Geo to answer:
“What is the best route, distance, and major restrictions affecting it?”

Required steps:
- Resolve origin and destination to authoritative locations.
- Confirm the road/network dataset being used.
- Compute the shortest valid route respecting known restrictions if available.
- Return:
  - route distance
  - estimated travel path
  - key turning/restriction notes
  - any uncertainty caused by unavailable live restrictions or incomplete network state
- If the network is prebuilt or cached, say so.
- If MCP-Geo cannot fully compute routing, provide the furthest grounded partial result and explain the blocker.

Return:
- concise operational answer
- structured route summary
- assumptions/limitations
- verification notes
- “Map recommended” output description
""",
            [
                "concise_operational_answer",
                "structured_route_summary",
                "assumptions_limitations",
                "verification_notes",
                "map_recommended_description",
            ],
            [],
            [
                {
                    "title": "Northumberland County Council uses OS route optimisation",
                    "url": "https://www.ordnancesurvey.co.uk/customers/case-studies/northumberland-county-council",
                    "role": "benchmark rationale",
                },
                {
                    "title": "OS MasterMap Highways Network guide to routing",
                    "url": "https://docs.os.uk/os-downloads/accessing-os-downloads/os-mastermap-highways-network-guidance#routing",
                    "role": "published blocker evidence",
                },
            ],
            (
                "The comparator is not a route distance. It is the published operational constraint "
                "that building a routing network can take two to three days. MCP-Geo therefore "
                "passes this benchmark if it returns a grounded partial result and the correct blocker."
            ),
            ["os_places.search", "os_apps.render_route_planner", "os_mcp.route_query"],
            [
                "Current MCP-Geo exposes a route-planner UI surface but no authoritative shortest-path engine.",
                "No live road-closure or hazard-avoidance model is wired into the repo today.",
            ],
            ["route", "blocked", "route planner", "map recommended", "two to three days"],
            {
                "concise_answer": "Current MCP-Geo can resolve the two sites and open the route-planner workflow, but it cannot yet return a verified shortest emergency route or distance because the repo does not expose a routing engine over OS Highways Network.",
                "method_used": [
                    "Resolve the origin and destination as named premises.",
                    "Classify the request as a route-planning workflow with MCP-Geo routing guidance.",
                    "Return the required blocker: route-planner UI is available, shortest-path computation is not.",
                ],
                "datasets_tools_used": [
                    "MCP-Geo tools: os_mcp.route_query, os_places.search, os_apps.render_route_planner",
                    "Published comparator: OS MasterMap Highways Network routing guidance",
                ],
                "confidence_caveats": [
                    "Endpoint resolution is high confidence because the sites are public named premises.",
                    "Route distance, restrictions, and turn-level directions are unavailable in the current repo surface.",
                ],
                "verification_steps": [
                    "Build or attach a precomputed routable network from OS Highways Network before re-running this scenario.",
                    "Confirm whether flood-zone avoidance should be modelled as hard exclusion or advisory constraint.",
                ],
                "structured_output": {
                    "status": "blocked_partial",
                    "origin": "Retford Library, 17 Churchgate, Retford, DN22 6PE",
                    "destination": "Goodwin Hall, Chancery Lane, Retford, DN22 6DF",
                    "routeDistanceKm": None,
                    "routePath": None,
                    "blocker": "No shortest-path routing engine is exposed through MCP-Geo; current support is UI-only.",
                    "suggestedExportFormat": "JSON blocker record plus GeoJSON endpoints once coordinates are resolved.",
                },
                "concise_operational_answer": "Resolve the two premises, then stop with a grounded blocker: current MCP-Geo cannot compute the route.",
                "structured_route_summary": {
                    "route_status": "blocked_partial",
                    "recommended_tool": "os_apps.render_route_planner",
                    "published_blocker": "OS routing guidance warns that network build steps can take two to three days and should be automated overnight.",
                },
                "assumptions_limitations": [
                    "No route network or live restrictions are available in the repo surface.",
                    "Flood-zone avoidance is a scenario requirement but cannot be encoded without a route engine.",
                ],
                "verification_notes": [
                    "Confirm endpoint coordinates in an authoritative address service before routing.",
                    "Validate any future route against local emergency access policies and temporary closures.",
                ],
                "map_recommended_description": "Map recommended: show both premises, the flood-risk-zone 167647/3 polygon, and the road network segment that would need route computation once available.",
            },
        ),
        _scenario(
            "SG04",
            4,
            "Maintainable road segments and total length by class",
            "public",
            "partial",
            (
                "Rutland County Council publishes a current road-length transparency page with class totals, "
                "and Phase 2 evidence shows GeoPlace positioning this workload as a replacement for manual returns."
            ),
            f"""{COMMON_HEADER}

Task:
Given area: Rutland County Council
Answer:
“Which road segments in this area are publicly maintainable, and what is the total length by class?”

Required steps:
- Resolve the requested geography.
- Identify relevant road segments and their maintainability/classification attributes.
- Aggregate total length by class/category.
- Flag anomalies, gaps, or conflicting classifications.
- If applicable, identify which segments likely need custodian review.
- Make clear whether the answer is suitable for operational insight only or close to statutory reporting quality.

Return:
- short answer
- summary table by class
- anomaly table
- confidence/caveats
- suggested follow-up checks
""",
            [
                "short_answer",
                "summary_table_by_class",
                "anomaly_table",
                "suggested_follow_up_checks",
            ],
            [],
            [
                {
                    "title": "Highway authority road lengths",
                    "url": "https://www.rutland.gov.uk/roads-transport-parking/roads-pavements/highway-maintenance/highway-authority-road-lengths",
                    "role": "published comparator",
                },
                {
                    "title": "GeoPlace explores replacing manual highway returns",
                    "url": "https://www.geoplace.co.uk/addresses-streets/location-data/street-data",
                    "role": "benchmark rationale",
                },
            ],
            (
                "Published comparator for Rutland’s current highways maintenance transparency report: "
                "A roads 77 km, B/C roads 221 km, U roads 222 km, total roads 520 km. "
                "The benchmark expects the answer to treat those as published control totals "
                "unless it has a live segment-level run."
            ),
            ["admin_lookup.find_by_name", "os_features.collections", "os_features.query"],
            [
                "Segment-level maintainability aggregation depends on NGD road-maintenance collections and an OS key.",
                "The published Rutland comparator aggregates B and C roads together, so separate B/C totals need a live segment run.",
                "This environment does not have a live OS key, so published comparator totals are the ground truth for validation.",
            ],
            ["rutland", "77", "221", "222", "maintainable", "statutory"],
            {
                "concise_answer": "Rutland is the benchmark area. The published comparator totals are 77 km of A roads, 221 km of B/C roads, 222 km of U roads, and 520 km of total maintained roads.",
                "method_used": [
                    "Resolve Rutland as the target authority.",
                    "Use NGD road-maintenance collections for a live run if available.",
                    "Compare any live total against Rutland’s published comparator figures before treating it as statutory-quality output.",
                ],
                "datasets_tools_used": [
                    "Rutland County Council road-length transparency page",
                    "MCP-Geo tools: admin_lookup.find_by_name, os_features.collections, os_features.query",
                ],
                "confidence_caveats": [
                    "The published totals are authoritative comparators for this benchmark.",
                    "Without a live NGD segment run, MCP-Geo should treat the result as comparator-led rather than generated.",
                ],
                "verification_steps": [
                    "Check live NGD collection availability for trn-rami-maintenance* and any road-class fields.",
                    "Reconcile any discrepancy against the latest authority publication before using it operationally.",
                    "If separate B and C totals are needed, derive them from segment-level data rather than the transparency-page aggregate.",
                ],
                "structured_output": {
                    "lengthByClassKm": [
                        {"roadClass": "A", "lengthKm": 77.0},
                        {"roadClass": "B/C", "lengthKm": 221.0},
                        {"roadClass": "U", "lengthKm": 222.0},
                        {"roadClass": "Total roads", "lengthKm": 520.0},
                    ],
                    "suggestedExportFormat": "CSV by published road class totals, plus segment GeoJSON if a live NGD roll-up is run.",
                },
                "short_answer": "Rutland’s published maintained-road comparator totals are ready-made benchmark control values.",
                "summary_table_by_class": [
                    {"road_class": "A", "length_km": 77.0},
                    {"road_class": "B/C", "length_km": 221.0},
                    {"road_class": "U", "length_km": 222.0},
                    {"road_class": "Total roads", "length_km": 520.0},
                ],
                "anomaly_table": [
                    {"issue": "No live segment roll-up in benchmark environment", "impact": "Comparator-led only"},
                    {"issue": "Published comparator merges B and C roads", "impact": "Separate B/C analysis needs live segment data"},
                ],
                "suggested_follow_up_checks": [
                    "Confirm whether the authority publication date matches the benchmark year being tested.",
                    "Sample-test a handful of segments for class and maintainability coding if a live NGD run becomes available.",
                ],
            },
        ),
        _scenario(
            "SG05",
            5,
            "Planning site constraints and evidence summary",
            "public",
            "partial",
            (
                "Goodwin Hall is a real public site from the Bassetlaw asset register, and open planning.data "
                "layers show it intersects both flood-risk zones and the Retford conservation area."
            ),
            f"""{COMMON_HEADER}

Task:
Given planning site geometry: Goodwin Hall, Chancery Lane, Retford, DN22 6DF
Answer:
“For this site, which spatial constraints and policy-relevant layers intersect it, and what is the evidence summary?”

Required steps:
- Resolve the site precisely.
- Discover the relevant authoritative spatial layers available through MCP-Geo.
- Run intersection / within-distance / adjacency checks as appropriate.
- Produce an evidence summary that distinguishes:
  - direct intersections
  - nearby but non-intersecting constraints
  - missing or unavailable datasets
- Avoid making planning judgements; provide geospatial evidence only.
- Where a layer is unavailable, name the gap rather than inferring the result.

Return:
- concise site summary
- intersecting constraints table
- nearby constraints table
- missing-data note
- confidence statement
- “Map recommended” description
""",
            [
                "concise_site_summary",
                "intersecting_constraints_table",
                "nearby_constraints_table",
                "missing_data_note",
                "confidence_statement",
                "map_recommended_description",
            ],
            [],
            [
                {
                    "title": "Bassetlaw open land and building assets register",
                    "url": "https://data.bassetlaw.gov.uk/land-building-assets/",
                    "role": "site source",
                },
                {
                    "title": "Planning Data flood-risk-zone dataset",
                    "url": "https://www.planning.data.gov.uk/dataset/flood-risk-zone",
                    "role": "constraint layer",
                },
                {
                    "title": "Planning Data conservation-area dataset",
                    "url": "https://www.planning.data.gov.uk/dataset/conservation-area",
                    "role": "constraint layer",
                },
            ],
            (
                "Published comparator: the benchmark site intersects flood-risk-zone references "
                "406550/2 (level 2), 167647/3 (level 3), and the Retford conservation area "
                "(reference 18 / entity 44014417) when checked against open planning.data layers."
            ),
            ["os_places.search", "admin_lookup.containing_areas", "os_features.collections"],
            [
                "The repo does not yet expose planning.data or local-plan policy layers as MCP-Geo tools.",
                "An answer should therefore name missing layers rather than pretending local policy evidence is complete.",
            ],
            ["goodwin hall", "flood", "conservation area", "missing data", "map recommended"],
            {
                "concise_answer": "Goodwin Hall should be treated as a constrained site: the benchmark evidence shows direct intersection with fluvial flood-risk zones 2 and 3 plus the Retford conservation area.",
                "method_used": [
                    "Resolve Goodwin Hall as the site reference.",
                    "Check open planning.data constraint layers for direct point/geometry intersection.",
                    "Name the planning layers that are not available through MCP-Geo today.",
                ],
                "datasets_tools_used": [
                    "Bassetlaw land and building assets register",
                    "planning.data.gov.uk flood-risk-zone and conservation-area datasets",
                    "MCP-Geo tools: os_places.search, admin_lookup.containing_areas, os_features.collections",
                ],
                "confidence_caveats": [
                    "Constraint intersections are strong because they come from open planning.data geometries.",
                    "Local policy, heritage-setting, and nearby-constraint analysis remains incomplete without additional layers.",
                ],
                "verification_steps": [
                    "Resolve the exact site polygon or building footprint before making any planning submission decision.",
                    "Check the local plan, heritage setting, and local land charges systems for non-open constraints.",
                ],
                "structured_output": {
                    "intersections": [
                        {"dataset": "flood-risk-zone", "reference": "406550/2", "level": "2"},
                        {"dataset": "flood-risk-zone", "reference": "167647/3", "level": "3"},
                        {"dataset": "conservation-area", "reference": "18", "name": "Retford"},
                    ],
                    "suggestedExportFormat": "CSV constraint register plus GeoJSON site and intersecting constraints.",
                },
                "concise_site_summary": "Goodwin Hall is inside both level-2 and level-3 fluvial flood-risk zones and inside the Retford conservation area.",
                "intersecting_constraints_table": [
                    {"dataset": "flood-risk-zone", "reference": "406550/2", "detail": "Fluvial Models, level 2"},
                    {"dataset": "flood-risk-zone", "reference": "167647/3", "detail": "Fluvial Models, level 3"},
                    {"dataset": "conservation-area", "reference": "18", "detail": "Retford conservation area"},
                ],
                "nearby_constraints_table": [
                    {"dataset": "listed-building", "detail": "No direct site-centroid intersection in sampled open layers"},
                    {"dataset": "tree-preservation-zone", "detail": "No direct site-centroid intersection in sampled open layers"},
                ],
                "missing_data_note": "Local plan policies, setting analysis, land-charges constraints, and any local flood-mitigation evidence are not in the supplied benchmark pack.",
                "confidence_statement": "Moderate to high: direct open-layer intersections are strong, but the site polygon is still a proxy from the asset register rather than a planning-application boundary.",
                "map_recommended_description": "Map recommended: show Goodwin Hall, both flood-risk-zone polygons, and the Retford conservation-area outline on the same view.",
            },
        ),
        _scenario(
            "SG06",
            6,
            "Council asset register linked to UPRNs and overlaid with flood risk",
            "public",
            "partial",
            (
                "This uses a real Bassetlaw asset-register subset with published UPRNs, coordinates, "
                "and tenure fields, overlaid against published planning.data flood-risk-zone geometry."
            ),
            f"""{COMMON_HEADER}

Task:
Given:
- asset register file: data/benchmarking/stakeholder_eval/fixtures/scenario_06_bassetlaw_assets_subset.csv
- flood extent / risk layer: planning.data flood-risk-zone references 402042/2, 406550/2, and 167647/3 around Retford

Use MCP-Geo to answer:
“Which assets can be linked to authoritative premises identifiers, and which of those are within or near flood-risk areas?”

Required steps:
- Inspect the asset register and identify address/location fields.
- Match each asset to a UPRN or authoritative location where possible.
- Report unmatched or ambiguous assets separately.
- Overlay matched assets with the flood-risk geometry.
- Summarise:
  - matched assets
  - unmatched assets
  - assets in-risk
  - assets near-risk
- State confidence per asset or per match group.

Return:
- executive summary
- matched asset table
- unmatched asset table
- flood-risk overlay summary
- confidence/caveats
- recommended exports
""",
            [
                "executive_summary",
                "matched_asset_table",
                "unmatched_asset_table",
                "flood_risk_overlay_summary",
                "recommended_exports",
            ],
            ["data/benchmarking/stakeholder_eval/fixtures/scenario_06_bassetlaw_assets_subset.csv"],
            [
                {
                    "title": "Bassetlaw open land and building assets register",
                    "url": "https://data.bassetlaw.gov.uk/land-building-assets/",
                    "role": "asset source",
                },
                {
                    "title": "Planning Data flood-risk-zone dataset",
                    "url": "https://www.planning.data.gov.uk/dataset/flood-risk-zone",
                    "role": "flood overlay source",
                },
            ],
            (
                "Published comparator for the selected seven-asset subset: all seven assets already "
                "carry real UPRNs; four intersect the sampled flood-risk-zone point checks; three more "
                "sit in the same operational cluster and should remain a manual review queue unless a "
                "distance-based overlay is added."
            ),
            ["os_places.by_uprn", "admin_lookup.containing_areas"],
            [
                "The repo does not yet expose planning.data as a first-class MCP-Geo source.",
                "Near-risk status in this benchmark is an explicit review queue, not a confirmed distance calculation.",
            ],
            ["matched assets", "flood", "uprn", "review", "export"],
            {
                "concise_answer": "All 7 benchmark assets are already keyed by real UPRN. 4 assets are confirmed in-risk from point-on-zone checks, 0 are unmatched, and 3 remain review candidates rather than confirmed near-risk assets.",
                "method_used": [
                    "Read UPRN, address, and coordinate fields directly from the asset register.",
                    "Use the supplied Retford flood-risk-zone references for overlay.",
                    "Keep non-intersecting assets in a review queue unless a distance rule is supplied.",
                ],
                "datasets_tools_used": [
                    "Bassetlaw asset register subset",
                    "planning.data.gov.uk flood-risk-zone references 402042/2, 406550/2, 167647/3",
                    "MCP-Geo tools: os_places.by_uprn, admin_lookup.containing_areas",
                ],
                "confidence_caveats": [
                    "UPRN linkage is high confidence because the published asset register supplies the UPRN directly.",
                    "In-risk classification is strong for the four intersecting points.",
                    "Near-risk is intentionally conservative: the benchmark expects review-candidate labelling, not guessed distance classes.",
                ],
                "verification_steps": [
                    "Confirm any export uses the latest flood-zone release before publication.",
                    "If near-risk assets matter operationally, run a true distance-to-zone calculation instead of point-only checks.",
                ],
                "structured_output": {
                    "matchedAssets": 7,
                    "unmatchedAssets": 0,
                    "confirmedInRiskAssets": 4,
                    "reviewQueueAssets": 3,
                },
                "executive_summary": "Seven assets matched cleanly by UPRN; four sit inside sampled flood zones and three require proximity review rather than being labelled safe.",
                "matched_asset_table": [
                    {"uprn": "100032031194", "asset": "Nottinghamshire County Council land", "postcode": "DN22 6DG", "risk_status": "in_risk"},
                    {"uprn": "100032031210", "asset": "Retford Library 17", "postcode": "DN22 6PE", "risk_status": "review_candidate"},
                    {"uprn": "100032031287", "asset": "Goodwin Hall", "postcode": "DN22 6DF", "risk_status": "in_risk"},
                    {"uprn": "10023266359", "asset": "Retford Shopmobility", "postcode": "DN22 6EY", "risk_status": "review_candidate"},
                    {"uprn": "10023266361", "asset": "Public Car Park", "postcode": "DN22 6EY", "risk_status": "in_risk"},
                    {"uprn": "10023269092", "asset": "North Public Car Park", "postcode": "DN22 6EY", "risk_status": "review_candidate"},
                    {"uprn": "10023270715", "asset": "Pavillion at Kings Park", "postcode": "DN22 6EY", "risk_status": "in_risk"},
                ],
                "unmatched_asset_table": [],
                "flood_risk_overlay_summary": {
                    "confirmed_in_risk_assets": 4,
                    "review_queue_assets": 3,
                    "intersecting_zone_references": ["402042/2", "406550/2", "167647/3"],
                },
                "recommended_exports": ["CSV asset risk register", "GeoJSON or map layer if coordinates are included in the live run"],
            },
        ),
        _scenario(
            "SG07",
            7,
            "Flood appraisal: count properties at risk and generate a verification plan",
            "public",
            "partial",
            (
                "The flood extent is public and real; the property list is a curated sample of real "
                "Retford price-paid addresses plus explicit negative controls. This lets the benchmark "
                "score uncertainty handling and verification planning."
            ),
            f"""{COMMON_HEADER}

Task:
Given:
- flood extent or risk geometry: planning.data flood-risk-zone references 402042/2 and 167647/3 around Retford
- target area: data/benchmarking/stakeholder_eval/fixtures/scenario_07_property_sample.csv

Use MCP-Geo to answer:
“How many properties are likely at risk, what categories do they fall into, and which cases most need field verification?”

Required steps:
- Resolve the flood geometry and target geography.
- Identify affected premises/buildings/UPRNs.
- Count affected properties by available classification.
- Separate:
  - high-confidence affected properties
  - borderline/uncertain cases
  - records that likely need manual/site verification
- Explain the basis of uncertainty.
- Produce a prioritised verification list rather than pretending the model can replace field validation.

Return:
- headline counts
- classification summary
- verification-priority table
- uncertainty explanation
- “Map recommended” description
""",
            [
                "headline_counts",
                "classification_summary",
                "verification_priority_table",
                "uncertainty_explanation",
                "map_recommended_description",
            ],
            ["data/benchmarking/stakeholder_eval/fixtures/scenario_07_property_sample.csv"],
            [
                {
                    "title": "HM Land Registry Price Paid Data downloads",
                    "url": "https://www.gov.uk/government/statistical-data-sets/price-paid-data-downloads",
                    "role": "property sample source",
                },
                {
                    "title": "Planning Data flood-risk-zone dataset",
                    "url": "https://www.planning.data.gov.uk/dataset/flood-risk-zone",
                    "role": "flood extent source",
                },
            ],
            (
                "Comparator baseline for the sample file: 5 properties are high-confidence affected "
                "from postcode/zone evidence, 2 are outside-zone negative controls, and the benchmark "
                "should prioritize duplicate/leasehold and wharf-side cases for site verification."
            ),
            ["os_places.search", "os_places.by_uprn", "admin_lookup.containing_areas"],
            [
                "The property list is a sample, not a full dwelling count for Retford.",
                "Some records rely on postcode-centroid evidence rather than building footprints, so verification remains mandatory.",
            ],
            ["field verification", "high-confidence", "borderline", "map recommended", "uncertainty"],
            {
                "concise_answer": "Within the benchmark sample, 5 properties are high-confidence at-risk cases and 2 are negative-control records outside the zone. The answer should explicitly keep field verification in scope.",
                "method_used": [
                    "Use the supplied flood-zone references as the risk geometry.",
                    "Treat DN22 6EN and DN22 6FE sample addresses as affected because their postcode centroids intersect the published zones in benchmark prep.",
                    "Keep outside-zone controls separate and prioritize wharf-side and duplicate/leasehold properties for verification.",
                ],
                "datasets_tools_used": [
                    "HM Land Registry Price Paid sample properties",
                    "planning.data.gov.uk flood-risk-zone references 402042/2 and 167647/3",
                    "MCP-Geo tools: os_places.search, os_places.by_uprn, admin_lookup.containing_areas",
                ],
                "confidence_caveats": [
                    "This is a sampled property list rather than a full property inventory.",
                    "Several properties are classified from postcode-level evidence and should be verified on the ground or against building footprints.",
                ],
                "verification_steps": [
                    "Verify 6 Mill Bridge Close because duplicate leasehold/freehold transaction records can distort property counts.",
                    "Check Navigation Lodge and other wharf-side premises first because zone-3 exposure is highest there.",
                    "Use building footprints or authoritative address-to-UPRN resolution to confirm the exact number of premises at each postcode.",
                ],
                "structured_output": {
                    "headlineCounts": {"highConfidenceAffected": 5, "borderline": 0, "negativeControls": 2},
                    "suggestedExportFormat": "CSV verification queue plus GeoJSON points for the sampled properties.",
                },
                "headline_counts": {"high_confidence_affected": 5, "borderline_uncertain": 0, "manual_verification": 3},
                "classification_summary": [
                    {"class": "zone_3_or_core_floodplain", "properties": 2},
                    {"class": "zone_2_or_adjacent_floodplain", "properties": 3},
                    {"class": "outside_sampled_zone", "properties": 2},
                ],
                "verification_priority_table": [
                    {"property": "Navigation Lodge, Wharf Road, Retford DN22 6EN", "priority": "high", "reason": "wharf-side / zone-3 exposure"},
                    {"property": "6 Mill Bridge Close, Retford DN22 6FE", "priority": "high", "reason": "duplicate transaction records / exact-premises confirmation"},
                    {"property": "115 Mill Bridge Close, Retford DN22 6FE", "priority": "medium", "reason": "postcode-centroid rather than footprint evidence"},
                ],
                "uncertainty_explanation": "The benchmark uses a sampled property list and postcode-derived checks, so it is deliberately designed to reward honest uncertainty handling instead of false precision.",
                "map_recommended_description": "Map recommended: show the sampled addresses, flood-zone 2/3 polygons, and a symbol distinction between high-confidence properties and negative controls.",
            },
        ),
        _scenario(
            "SG08",
            8,
            "Normalise fragmented housing development sources and summarise by polling district or ward",
            "synthetic",
            "partial",
            (
                "North Yorkshire’s 2024 Boundary Commission review explicitly states that there is no "
                "single source for housing development data and that the GIS team had to reconcile "
                "points, polygons, planning inputs, and local plan allocations. The benchmark pack "
                "uses a validated synthetic mini-pack modelled on that workflow."
            ),
            f"""{COMMON_HEADER}

Task:
Given these fragmented housing-development inputs:
- data/benchmarking/stakeholder_eval/fixtures/scenario_08_housing_allocations.csv
- data/benchmarking/stakeholder_eval/fixtures/scenario_08_planning_permissions.csv
- data/benchmarking/stakeholder_eval/fixtures/scenario_08_site_promoters.csv

Use MCP-Geo to answer:
“What is the best consolidated view of future housing development by polling district, ward, or other requested geography?”

Required steps:
- Inspect all inputs and identify overlaps, duplicates, and inconsistent formats.
- Normalise site/address/location references.
- Resolve each development to a mappable geometry or best-available point.
- Assign each development to the requested boundaries.
- Summarise counts and expected impact by geography.
- Clearly separate confirmed records from uncertain or duplicate candidate records.
- Describe the reconciliation logic.

Return:
- consolidated summary
- geography-level totals table
- duplicate/uncertain records table
- method note
- confidence statement
- suggested export schema
""",
            [
                "consolidated_summary",
                "geography_level_totals_table",
                "duplicate_uncertain_records_table",
                "method_note",
                "confidence_statement",
                "suggested_export_schema",
            ],
            [
                "data/benchmarking/stakeholder_eval/fixtures/scenario_08_housing_allocations.csv",
                "data/benchmarking/stakeholder_eval/fixtures/scenario_08_planning_permissions.csv",
                "data/benchmarking/stakeholder_eval/fixtures/scenario_08_site_promoters.csv",
            ],
            [
                {
                    "title": "North Yorkshire Boundary Commission Review GIS Processes 2024",
                    "url": "https://edemocracy.northyorks.gov.uk/documents/g9198/Public%20reports%20pack%2009th-Jul-2024%2011.00%20Executive.pdf?T=10",
                    "role": "workflow rationale",
                }
            ],
            (
                "Comparator baseline is synthetic but validated against the published North Yorkshire "
                "workflow: 1 duplicate development family (Abbey Quarter), 1 uncertain promoter-only "
                "record (Scarborough North Infill), and geography totals of Selby West 120 confirmed / "
                "40 permission-linked, Cayton 73, Ripon South 30, Scarborough North 30 uncertain."
            ),
            ["admin_lookup.find_by_name", "admin_lookup.containing_areas", "ons_geo.by_postcode"],
            [
                "The mini-pack is synthetic because the former-district raw files are not published as a reusable benchmark bundle.",
                "Geometry assignment is therefore benchmark logic, not a live authoritative planning register.",
            ],
            ["no single source", "duplicate", "uncertain", "ward", "synthetic"],
            {
                "concise_answer": "The benchmark pack is designed so the model must consolidate three fragmented sources into 3 confirmed ward totals plus 1 uncertain promoter-only ward total.",
                "method_used": [
                    "Normalize site names across the three files.",
                    "Collapse Abbey Quarter duplicates into one development family with linked allocation and permission records.",
                    "Keep Scarborough North Infill as uncertain because it appears only in the promoter file.",
                ],
                "datasets_tools_used": [
                    "Synthetic North Yorkshire-style housing-fragmentation fixtures",
                    "Published benchmark rationale from North Yorkshire Boundary Commission GIS methodology",
                    "MCP-Geo tools: admin_lookup.find_by_name, admin_lookup.containing_areas, ons_geo.by_postcode",
                ],
                "confidence_caveats": [
                    "All three input files are synthetic representations of a published workflow, not the raw North Yorkshire operational files.",
                    "Geography assignment is therefore a benchmark truth table rather than a live planning system result.",
                ],
                "verification_steps": [
                    "Cross-check duplicate development families with planning-policy officers before publication.",
                    "Require a fresh geometry or planning reference for promoter-only records before they are counted as confirmed supply.",
                ],
                "structured_output": {
                    "wardTotals": [
                        {"ward": "Selby West", "confirmedUnits": 120, "linkedPermissionUnits": 40, "uncertainUnits": 0},
                        {"ward": "Cayton", "confirmedUnits": 48, "linkedPermissionUnits": 25, "uncertainUnits": 0},
                        {"ward": "Ripon South", "confirmedUnits": 30, "linkedPermissionUnits": 25, "uncertainUnits": 0},
                        {"ward": "Scarborough North", "confirmedUnits": 0, "linkedPermissionUnits": 0, "uncertainUnits": 30},
                    ]
                },
                "consolidated_summary": "Abbey Quarter and Cayton East Extension appear in multiple files and need family-level consolidation; Scarborough North Infill remains promoter-only and uncertain.",
                "geography_level_totals_table": [
                    {"geography": "Selby West", "confirmed_units": 120, "linked_permission_units": 40, "uncertain_units": 0},
                    {"geography": "Cayton", "confirmed_units": 48, "linked_permission_units": 25, "uncertain_units": 0},
                    {"geography": "Ripon South", "confirmed_units": 30, "linked_permission_units": 25, "uncertain_units": 0},
                    {"geography": "Scarborough North", "confirmed_units": 0, "linked_permission_units": 0, "uncertain_units": 30},
                ],
                "duplicate_uncertain_records_table": [
                    {"site_name": "Abbey Quarter", "issue": "duplicate family across allocation, permission, and promoter sources"},
                    {"site_name": "Scarborough North Infill", "issue": "promoter-only / uncertain geometry"},
                ],
                "method_note": "This benchmark follows the published North Yorkshire workflow: points and polygons are harmonized, then counted by polling district or ward using GIS logic.",
                "confidence_statement": "Moderate: the reconciliation logic is realistic and source-backed, but the actual mini-pack is synthetic.",
                "suggested_export_schema": [
                    "canonical_site_id",
                    "source_refs",
                    "ward",
                    "polling_district",
                    "confirmed_units",
                    "uncertain_units",
                    "confidence",
                ],
            },
        ),
        _scenario(
            "SG09",
            9,
            "BDUK-style premises status lookup with explanation of missing/new-build/epoch issues",
            "public",
            "partial",
            (
                "The benchmark premise is a real UPRN from the Bassetlaw asset register that is absent "
                "from the September 2024 East Midlands BDUK release. That makes it a strong test of "
                "evidence-ranked missing-premise reasoning."
            ),
            f"""{COMMON_HEADER}

Task:
Given:
- premise reference: UPRN 10023266361
- premises-status dataset: data/benchmarking/stakeholder_eval/fixtures/scenario_09_bduk_subset.csv with the full East Midlands September 2024 BDUK release as the authoritative backing dataset

Use MCP-Geo to answer:
“What is this premises’ current status in the dataset, and if it is missing or unclear, why?”

Required steps:
- Resolve the supplied premise reference to the best authoritative identifier.
- Look up the premise in the supplied status dataset.
- If missing, test grounded explanations such as:
  - new build not yet present in the source epoch
  - demolished / non-target classification
  - unmatched identifier
  - dataset coverage gap
- Do not guess; rank explanations by evidence.
- State what additional data refresh or validation step would confirm the answer.

Return:
- short user-facing answer
- structured premise status
- explanation of missing/uncertain cases
- confidence/caveats
- next verification step
""",
            [
                "short_user_facing_answer",
                "structured_premise_status",
                "explanation_of_missing_uncertain_cases",
                "next_verification_step",
            ],
            ["data/benchmarking/stakeholder_eval/fixtures/scenario_09_bduk_subset.csv"],
            [
                {
                    "title": "Premises in BDUK plans (March 2025, England and Wales)",
                    "url": "https://www.gov.uk/government/publications/premises-in-bduk-plans-england-and-wales",
                    "role": "dataset source",
                },
                {
                    "title": "User guide and technical note for premises in BDUK plans",
                    "url": "https://www.gov.uk/government/publications/premises-in-bduk-plans-england-and-wales/user-guide-and-technical-note-for-premises-in-bduk-plans",
                    "role": "missing-premise reasoning",
                },
                {
                    "title": "Bassetlaw open land and building assets register",
                    "url": "https://data.bassetlaw.gov.uk/land-building-assets/",
                    "role": "premise source",
                },
            ],
            (
                "Comparator outcome: UPRN 10023266361 is absent from the East Midlands BDUK release, "
                "and the strongest evidence-backed explanation is non-target classification because the "
                "same public register labels it as a car park. The benchmark should still mention the "
                "BDUK guide’s epoch/new-build caveat, but rank it below the classification explanation."
            ),
            ["os_places.by_uprn", "ons_geo.by_uprn"],
            [
                "BDUK is a supplied dataset, not a native MCP-Geo tool family.",
                "The benchmark expects evidence-ranked reasoning about absence, not fabricated status values.",
            ],
            ["missing", "non-target", "new build", "epoch", "verification"],
            {
                "concise_answer": "UPRN 10023266361 is missing from the supplied BDUK release. The strongest explanation is that it is a non-target public car park rather than a dwelling or business premises in BDUK’s recognised premises base.",
                "method_used": [
                    "Resolve the UPRN against the supplied benchmark sources.",
                    "Check whether the UPRN appears in the East Midlands BDUK release.",
                    "Rank missing-case explanations using the BDUK guide and the public asset-register classification.",
                ],
                "datasets_tools_used": [
                    "Bassetlaw asset register",
                    "BDUK East Midlands September 2024 release",
                    "BDUK user guide and technical note",
                    "MCP-Geo tools: os_places.by_uprn, ons_geo.by_uprn",
                ],
                "confidence_caveats": [
                    "The UPRN is real and the absence is real.",
                    "The reason is still inferential until the UPRN is checked against AddressBase class or a newer BDUK release.",
                ],
                "verification_steps": [
                    "Confirm the UPRN’s current AddressBase class or OS Places record.",
                    "Check the next BDUK release in case the premise treatment has changed.",
                ],
                "structured_output": {
                    "premiseStatus": "missing",
                    "rankedExplanations": [
                        {"reason": "non_target_or_non_postal_premises", "confidence": "high"},
                        {"reason": "dataset_coverage_gap", "confidence": "medium"},
                        {"reason": "new_build_epoch_lag", "confidence": "low"},
                        {"reason": "demolished_or_derelict", "confidence": "low"},
                    ],
                    "suggestedExportFormat": "JSON status record for the premise plus CSV ranked-explanations table.",
                },
                "short_user_facing_answer": "This UPRN is not in the supplied BDUK file. Treat it as a likely non-target premises until AddressBase classification proves otherwise.",
                "structured_premise_status": {
                    "uprn": "10023266361",
                    "dataset_status": "not_found",
                    "best_supported_reason": "non_target_or_non_postal_premises",
                },
                "explanation_of_missing_uncertain_cases": [
                    "The public source labels the UPRN as a public car park, which is stronger evidence than a generic epoch-lag explanation.",
                    "The BDUK guide still requires the answer to mention other grounded possibilities such as new-build lag or demolished/derelict classifications.",
                ],
                "next_verification_step": "Resolve the UPRN against the latest OS-backed premises classification and compare it with the next BDUK release.",
            },
        ),
        _scenario(
            "SG10",
            10,
            "Link council-tax-like and land-registry-like property datasets via UPRN and quantify unmatched records",
            "mixed",
            "partial",
            (
                "The council-tax-like file is synthetic but derived from real Bassetlaw address strings, "
                "and the land-registry-like file is a direct Price Paid extract. This mirrors the public "
                "sector property-platform problem without inventing the underlying land-registry rows."
            ),
            f"""{COMMON_HEADER}

Task:
Given:
- dataset A: data/benchmarking/stakeholder_eval/fixtures/scenario_10_council_tax_like.csv
- dataset B: data/benchmarking/stakeholder_eval/fixtures/scenario_10_price_paid_subset.csv

Use MCP-Geo to answer:
“How well can these datasets be aligned through authoritative property identifiers, and what remains unmatched?”

Required steps:
- Inspect both datasets and identify candidate join fields.
- Resolve addresses/locations to authoritative UPRNs where possible.
- Join the datasets through UPRN or best grounded fallback logic.
- Quantify:
  - exact matches
  - plausible matches needing review
  - unmatched records
  - likely causes of mismatch
- Where hierarchy matters, note parent/child premises issues.
- Avoid overstating completeness.

Return:
- summary of join success
- matched/unmatched metrics
- mismatch-reason table
- recommended remediation actions
- structured output schema
""",
            [
                "summary_of_join_success",
                "matched_unmatched_metrics",
                "mismatch_reason_table",
                "recommended_remediation_actions",
                "structured_output_schema",
            ],
            [
                "data/benchmarking/stakeholder_eval/fixtures/scenario_10_council_tax_like.csv",
                "data/benchmarking/stakeholder_eval/fixtures/scenario_10_price_paid_subset.csv",
            ],
            [
                {
                    "title": "HM Land Registry Price Paid Data downloads",
                    "url": "https://www.gov.uk/government/statistical-data-sets/price-paid-data-downloads",
                    "role": "dataset B source",
                },
                {
                    "title": "Welsh Revenue Authority annual report 2021 to 2022",
                    "url": "https://www.gov.wales/welsh-revenue-authority-annual-report-and-accounts-2021-2022-html",
                    "role": "property-platform rationale",
                },
            ],
            (
                "Reference benchmark outcome: 5 exact matches, 2 plausible review matches, and 1 "
                "unmatched council-tax-like row. The most important mismatch reason is address-hierarchy "
                "handling for Canalside Wharf, 6 Wharf Road."
            ),
            ["os_places.search", "os_places.by_postcode", "os_places.by_uprn"],
            [
                "The council-tax-like file is synthetic because there is no reusable open council-tax benchmark file with equivalent address detail.",
                "Exact UPRN alignment needs live address tooling; without it, the benchmark rewards cautious hierarchy handling rather than overclaiming match rates.",
            ],
            ["exact matches", "plausible", "unmatched", "parent", "synthetic"],
            {
                "concise_answer": "The benchmark is calibrated for 5 exact matches, 2 plausible review matches, and 1 unmatched council-tax-like record after identifier reconciliation.",
                "method_used": [
                    "Normalize both datasets to comparable address tokens.",
                    "Use UPRN lookup where possible; otherwise fall back to grounded address matching with hierarchy checks.",
                    "Separate exact joins from plausible but reviewable sub-building or legacy-address cases.",
                ],
                "datasets_tools_used": [
                    "Synthetic council-tax-like Bassetlaw address file",
                    "HM Land Registry Price Paid subset",
                    "MCP-Geo tools: os_places.search, os_places.by_postcode, os_places.by_uprn",
                ],
                "confidence_caveats": [
                    "Dataset A is synthetic; dataset B is real.",
                    "Canalside Wharf needs hierarchy-aware handling because PAON/SAON order differs across systems.",
                ],
                "verification_steps": [
                    "Resolve each review-queue record to a UPRN before loading it into a production join table.",
                    "Split PAON and SAON explicitly in both datasets to reduce future mismatch rates.",
                ],
                "structured_output": {
                    "matchMetrics": {"exact": 5, "plausibleReview": 2, "unmatched": 1},
                    "suggestedExportFormat": "CSV joined output plus CSV review queue for unresolved records.",
                },
                "summary_of_join_success": "Most of the curated Bassetlaw records align cleanly, but one hierarchy case and one postcode-normalization problem still need review.",
                "matched_unmatched_metrics": {
                    "exact_matches": 5,
                    "plausible_matches_needing_review": 2,
                    "unmatched_records": 1,
                },
                "mismatch_reason_table": [
                    {"reason": "PAON/SAON ordering mismatch", "records": 1},
                    {"reason": "postcode normalization or typo", "records": 1},
                    {"reason": "dataset coverage gap", "records": 1},
                ],
                "recommended_remediation_actions": [
                    "Keep sub-building names in dedicated fields in both systems.",
                    "Validate postcodes before attempting UPRN alignment.",
                    "Store authoritative UPRNs once resolved to prevent repeated fuzzy matching.",
                ],
                "structured_output_schema": [
                    "record_id",
                    "normalized_address",
                    "candidate_uprn",
                    "match_quality",
                    "review_reason",
                    "source_dataset",
                ],
            },
        ),
    ]


SCENARIOS = _build_scenarios()


def _reference_outputs_by_id() -> dict[str, dict[str, Any]]:
    return {scenario["id"]: deepcopy(scenario["referenceOutput"]) for scenario in SCENARIOS}


REFERENCE_OUTPUTS = _reference_outputs_by_id()


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _write_text(path: Path, content: str) -> None:
    _ensure_parent(path)
    path.write_text(content, encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    _ensure_parent(path)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_fixtures() -> list[str]:
    written: list[str] = []
    for relative_path, spec in FIXTURE_SPECS.items():
        path = PACK_ROOT / relative_path
        if spec["format"] == "csv":
            _write_csv(path, spec["rows"])
        else:
            _write_text(path, spec["content"])
        written.append(str(path.relative_to(REPO_ROOT)))
    return written


def write_reference_outputs() -> list[str]:
    written: list[str] = []
    for scenario_id, payload in REFERENCE_OUTPUTS.items():
        path = REFERENCE_ROOT / f"{scenario_id.lower()}.json"
        _ensure_parent(path)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        written.append(str(path.relative_to(REPO_ROOT)))
    return written


def build_pack() -> dict[str, Any]:
    return {
        "title": "MCP-Geo stakeholder evaluation benchmark pack",
        "version": "1.0",
        "generatedOn": DATE_STAMP,
        "commonHeader": COMMON_HEADER,
        "commonReturnFields": COMMON_RETURN_FIELDS,
        "rubric": RUBRIC,
        "scenarios": deepcopy(SCENARIOS),
    }


def _score_output(scenario: dict[str, Any], output: dict[str, Any]) -> dict[str, Any]:
    text = json.dumps(output, sort_keys=True).lower()
    dimensions: list[dict[str, Any]] = []

    def add_dimension(label: str, points: int, earned: int, detail: str) -> None:
        dimensions.append({"label": label, "points": points, "earned": earned, "detail": detail})

    common_present = sum(1 for field in COMMON_RETURN_FIELDS if field in output)
    scenario_present = sum(1 for field in scenario["scenarioReturnFields"] if field in output)
    add_dimension(
        "answer_contract",
        20,
        20 if common_present == len(COMMON_RETURN_FIELDS) and scenario_present == len(scenario["scenarioReturnFields"]) else 10,
        f"common={common_present}/{len(COMMON_RETURN_FIELDS)} scenario={scenario_present}/{len(scenario['scenarioReturnFields'])}",
    )

    grounding_terms = ["method_used", "structured_output", "verification_steps"]
    grounding_present = all(term in output for term in grounding_terms)
    add_dimension(
        "geospatial_grounding",
        20,
        20 if grounding_present else 10,
        "core operational fields present" if grounding_present else "missing operational fields",
    )

    identifier_keywords = [
        "uprn",
        "reference",
        "duplicate",
        "review",
        "premises",
        "match",
        "origin",
        "destination",
        "roadclass",
        "road_class",
        "ward",
        "polling_district",
        "dataset_status",
        "site",
        "constraint",
    ]
    identifier_hits = sum(1 for kw in identifier_keywords if kw in text)
    add_dimension(
        "identifier_integrity",
        15,
        15 if identifier_hits >= 3 else 8,
        f"identifier keyword hits={identifier_hits}",
    )

    required_hits = sum(1 for term in scenario["requiredTerms"] if term.lower() in text)
    add_dimension(
        "evidence_alignment",
        15,
        15 if required_hits >= max(3, len(scenario["requiredTerms"]) - 1) else 8,
        f"required term hits={required_hits}/{len(scenario['requiredTerms'])}",
    )

    caveats = output.get("confidence_caveats")
    caveat_points = 10 if isinstance(caveats, list) and caveats else 5
    add_dimension("uncertainty", 10, caveat_points, "confidence caveats present")

    verification = output.get("verification_steps")
    export_ready = any("export" in key.lower() or "schema" in key.lower() for key in output)
    export_present = export_ready or "export" in text or "geojson" in text or "csv" in text
    verification_points = 10 if isinstance(verification, list) and verification and export_present else 5
    add_dimension("verification_exports", 10, verification_points, "verification/export guidance present")

    datasets = output.get("datasets_tools_used")
    datasets_points = 10 if isinstance(datasets, list) and datasets else 5
    add_dimension("dataset_traceability", 10, datasets_points, "datasets/tools listed")

    total = sum(item["earned"] for item in dimensions)
    return {
        "scenarioId": scenario["id"],
        "score": total,
        "maxScore": 100,
        "dimensions": dimensions,
        "status": (
            "excellent"
            if total >= RUBRIC["thresholds"]["excellent"]
            else "good"
            if total >= RUBRIC["thresholds"]["good"]
            else "acceptable"
            if total >= RUBRIC["thresholds"]["acceptable"]
            else "poor"
            if total >= RUBRIC["thresholds"]["poor"]
            else "fail"
        ),
    }


def validate_pack(pack: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    scenarios = pack["scenarios"]
    if len(scenarios) != 10:
        errors.append(f"Expected 10 scenarios, found {len(scenarios)}")

    placeholder_pattern = re.compile(r"\[[A-Z][A-Z0-9 /_-]{2,}\]")
    scores: list[dict[str, Any]] = []
    for scenario in scenarios:
        prompt = scenario["populatedPrompt"]
        if placeholder_pattern.search(prompt):
            errors.append(f"{scenario['id']} still contains unfilled placeholders")
        if not prompt.startswith(COMMON_HEADER.splitlines()[0]):
            errors.append(f"{scenario['id']} prompt does not include the common header")
        if scenario["exampleMode"] != "public" and "synthetic" not in json.dumps(
            scenario["referenceOutput"], sort_keys=True
        ).lower():
            errors.append(f"{scenario['id']} synthetic scenario is not labelled synthetic in the reference output")
        for fixture in scenario["fixtureFiles"]:
            if not (REPO_ROOT / fixture).exists():
                errors.append(f"{scenario['id']} missing fixture file: {fixture}")
        output = scenario["referenceOutput"]
        missing_common = [field for field in COMMON_RETURN_FIELDS if field not in output]
        missing_specific = [field for field in scenario["scenarioReturnFields"] if field not in output]
        if missing_common:
            errors.append(f"{scenario['id']} missing common fields: {', '.join(missing_common)}")
        if missing_specific:
            errors.append(f"{scenario['id']} missing scenario fields: {', '.join(missing_specific)}")
        scores.append(_score_output(scenario, output))

    all_pass = not errors and all(score["score"] >= 90 for score in scores)
    return {"ok": all_pass, "errors": errors, "scores": scores}


def _render_sources(sources: list[dict[str, str]]) -> str:
    lines = []
    for source in sources:
        lines.append(f"- {source['role']}: [{source['title']}]({source['url']})")
    return "\n".join(lines)


def render_markdown(pack: dict[str, Any], validation: dict[str, Any]) -> str:
    lines = [
        "# MCP-Geo Stakeholder Evaluation Benchmark Pack",
        "",
        f"Generated: {DATE_STAMP}",
        "",
        "This pack turns the Phase 3 prompt bank into a run-ready benchmark for stakeholder evaluation.",
        "Each scenario now has populated inputs, expected outputs, source provenance, capability notes, and a scored reference answer.",
        "",
        "## Reusable Header",
        "",
        "```text",
        pack["commonHeader"],
        "```",
        "",
        "## SOTA Scoring Rubric",
        "",
        "| Dimension | Points | What it tests |",
        "| --- | ---: | --- |",
    ]
    for dimension in pack["rubric"]["dimensions"]:
        lines.append(
            f"| {dimension['label']} | {dimension['points']} | {'; '.join(dimension['checks'])} |"
        )
    lines.extend(
        [
            "",
            "Scoring thresholds:",
            "",
            f"- `excellent`: {pack['rubric']['thresholds']['excellent']}+",
            f"- `good`: {pack['rubric']['thresholds']['good']}+",
            f"- `acceptable`: {pack['rubric']['thresholds']['acceptable']}+",
            f"- `poor`: {pack['rubric']['thresholds']['poor']}+",
            "",
            "## Validation Status",
            "",
            f"- Pack valid: `{validation['ok']}`",
            f"- Machine-readable pack: `{PACK_JSON_PATH.relative_to(REPO_ROOT)}`",
            f"- Workflow report: [{WORKFLOW_REPORT_PATH.name}]({WORKFLOW_REPORT_PATH.name})",
            "",
            "## Scenario Pack",
            "",
        ]
    )
    if validation["errors"]:
        lines.extend(
            [
                "Validation errors:",
                "",
            ]
        )
        lines.extend([f"- {error}" for error in validation["errors"]])
        lines.append("")

    for scenario in pack["scenarios"]:
        score = next(item for item in validation["scores"] if item["scenarioId"] == scenario["id"])
        lines.extend(
            [
                f"## {scenario['rank']}. {scenario['title']} ({scenario['id']})",
                "",
                f"- Example mode: `{scenario['exampleMode']}`",
                f"- MCP-Geo support level: `{scenario['supportLevel']}`",
                f"- Reference score: `{score['score']}/100 ({score['status']})`",
                "",
                scenario["benchmarkRationale"],
                "",
                "**Sources**",
                _render_sources(scenario["sources"]),
                "",
                "**Fixtures**",
            ]
        )
        if scenario["fixtureFiles"]:
            lines.extend([f"- `{fixture}`" for fixture in scenario["fixtureFiles"]])
        else:
            lines.append("- No local fixture file required; the prompt uses direct public inputs.")
        lines.extend(
            [
                "",
                "**Comparator**",
                "",
                scenario["comparatorSummary"],
                "",
                "**Known Gaps**",
            ]
        )
        lines.extend([f"- {gap}" for gap in scenario["knownGaps"]])
        lines.extend(
            [
                "",
                "**Populated Prompt**",
                "",
                "```text",
                scenario["populatedPrompt"],
                "```",
                "",
                "**Expected Output Fields**",
            ]
        )
        lines.extend([f"- `{field}`" for field in COMMON_RETURN_FIELDS + scenario["scenarioReturnFields"]])
        lines.extend(
            [
                "",
                "**Reference Output Summary**",
                "",
                f"- `{scenario['referenceOutput']['concise_answer']}`",
                "",
                "**Reference Output (JSON)**",
                "",
                "```json",
                json.dumps(scenario["referenceOutput"], indent=2),
                "```",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def render_workflow_report(pack: dict[str, Any], validation: dict[str, Any]) -> str:
    scenario = next(item for item in pack["scenarios"] if item["id"] == "SG01")
    score = next(item for item in validation["scores"] if item["scenarioId"] == "SG01")
    lines = [
        "# MCP-Geo Stakeholder Benchmark Workflow Validation",
        "",
        f"Date: {DATE_STAMP}",
        "",
        "This report captures the standard repeatable workflow using scenario 1 as the end-to-end proof case.",
        "",
        "## Workflow",
        "",
        "1. Curate a real public geospatial anchor and decide whether any protected data must be synthetic.",
        "2. Freeze the scenario prompt with the common header and concrete inputs.",
        "3. Write machine-readable fixture files and a scored reference output.",
        "4. Run pack validation and score the reference output.",
        "5. Render the human-readable markdown pack from the machine source.",
        "6. Use the same structure for the remaining scenarios so they stay consistent.",
        "",
        "## Scenario 1 Proof Case",
        "",
        f"- Scenario: `{scenario['title']}`",
        f"- Fixtures: {', '.join(scenario['fixtureFiles'])}",
        f"- Example mode: `{scenario['exampleMode']}`",
        f"- Reference score: `{score['score']}/100 ({score['status']})`",
        "",
        "## Score Breakdown",
        "",
        "| Dimension | Earned | Max | Detail |",
        "| --- | ---: | ---: | --- |",
    ]
    for dimension in score["dimensions"]:
        lines.append(
            f"| {dimension['label']} | {dimension['earned']} | {dimension['points']} | {dimension['detail']} |"
        )
    lines.extend(
        [
            "",
            "## Validation Outcome",
            "",
            f"- Pack valid: `{validation['ok']}`",
            f"- Validation errors: `{len(validation['errors'])}`",
        ]
    )
    if validation["errors"]:
        lines.append("")
        lines.append("Errors:")
        lines.extend([f"- {error}" for error in validation["errors"]])
    lines.extend(
        [
            "",
            "## Repeatable Guidance",
            "",
            "Use the same pattern for every new stakeholder benchmark case:",
            "- pick a public example whenever the exact input can be published safely",
            "- only introduce synthetic data to cover privacy, licensing, or missing public detail",
            "- carry the synthetic flag into the prompt, expected output, and scoring notes",
            "- keep the scorecard machine-readable so the markdown pack is always regenerated from source",
            "",
        ]
    )
    return "\n".join(lines)


def write_pack_outputs() -> dict[str, Any]:
    write_fixtures()
    write_reference_outputs()
    pack = build_pack()
    _ensure_parent(PACK_JSON_PATH)
    PACK_JSON_PATH.write_text(json.dumps(pack, indent=2), encoding="utf-8")
    validation = validate_pack(pack)
    _write_text(REPORT_PATH, render_markdown(pack, validation))
    _write_text(WORKFLOW_REPORT_PATH, render_workflow_report(pack, validation))
    return validation


def cmd_build(_: argparse.Namespace) -> int:
    validation = write_pack_outputs()
    return 0 if validation["ok"] else 1


def cmd_validate(_: argparse.Namespace) -> int:
    if not PACK_JSON_PATH.exists():
        write_pack_outputs()
    pack = json.loads(PACK_JSON_PATH.read_text(encoding="utf-8"))
    validation = validate_pack(pack)
    print(json.dumps(validation, indent=2))
    return 0 if validation["ok"] else 1


def cmd_score_reference(args: argparse.Namespace) -> int:
    if not PACK_JSON_PATH.exists():
        write_pack_outputs()
    pack = json.loads(PACK_JSON_PATH.read_text(encoding="utf-8"))
    scenario = next(item for item in pack["scenarios"] if item["id"] == args.scenario_id)
    output_path = REFERENCE_ROOT / f"{args.scenario_id.lower()}.json"
    output = json.loads(output_path.read_text(encoding="utf-8"))
    print(json.dumps(_score_output(scenario, output), indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build", help="Write benchmark fixtures, report, and workflow output.")
    build_parser.set_defaults(func=cmd_build)

    validate_parser = subparsers.add_parser("validate", help="Validate the current benchmark pack outputs.")
    validate_parser.set_defaults(func=cmd_validate)

    score_parser = subparsers.add_parser("score-reference", help="Score a reference output by scenario id.")
    score_parser.add_argument("scenario_id")
    score_parser.set_defaults(func=cmd_score_reference)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
