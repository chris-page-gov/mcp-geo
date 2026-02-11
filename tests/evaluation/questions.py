"""Evaluation Question Suite for MCP Geo Server."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class Difficulty(str, Enum):
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EDGE = "edge"
    AMBIGUOUS = "ambiguous"


class Intent(str, Enum):
    ADDRESS_LOOKUP = "address_lookup"
    PLACE_LOOKUP = "place_lookup"
    STATISTICS = "statistics"
    AREA_COMPARISON = "area_comparison"
    FEATURE_SEARCH = "feature_search"
    BOUNDARY_FETCH = "boundary_fetch"
    INTERACTIVE_SELECTION = "interactive_selection"
    ROUTE_PLANNING = "route_planning"
    DATASET_DISCOVERY = "dataset_discovery"
    MAP_RENDER = "map_render"
    VECTOR_TILES = "vector_tiles"
    LINKED_IDS = "linked_ids"
    UNKNOWN = "unknown"


@dataclass
class ToolCallSpec:
    name: str
    payload: Dict[str, Any]
    call_type: str = "tool"  # tool | tools_search | resource
    expect_error: bool = False


@dataclass
class ExpectedOutcome:
    required_fields: List[str] = field(default_factory=list)
    expected_values: Dict[str, Any] = field(default_factory=dict)
    required_tools: List[str] = field(default_factory=list)
    forbidden_tools: List[str] = field(default_factory=list)
    max_tool_calls: Optional[int] = None
    required_keywords: List[str] = field(default_factory=list)
    forbidden_keywords: List[str] = field(default_factory=list)


@dataclass
class EvaluationQuestion:
    id: str
    question: str
    intent: Intent
    difficulty: Difficulty
    description: str
    expected: ExpectedOutcome
    tool_calls: List[ToolCallSpec] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    requires_os_api: bool = False
    requires_ons_live: bool = False


BASIC_QUESTIONS = [
    EvaluationQuestion(
        id="B001",
        question="Find Westminster",
        intent=Intent.PLACE_LOOKUP,
        difficulty=Difficulty.BASIC,
        description="Basic administrative area lookup (live).",
        expected=ExpectedOutcome(
            required_tools=["admin_lookup.find_by_name"],
            max_tool_calls=2,
            required_keywords=["Westminster"],
        ),
        tool_calls=[ToolCallSpec("admin_lookup.find_by_name", {"text": "Westminster"})],
        tags=["place", "admin"],
    ),
    EvaluationQuestion(
        id="B002",
        question="UPRNs for SW1A 1AA",
        intent=Intent.ADDRESS_LOOKUP,
        difficulty=Difficulty.BASIC,
        description="Postcode lookup via OS Places.",
        expected=ExpectedOutcome(
            required_tools=["os_places.by_postcode"],
            max_tool_calls=2,
            required_keywords=["uprns"],
        ),
        tool_calls=[ToolCallSpec("os_places.by_postcode", {"postcode": "SW1A1AA"})],
        tags=["postcode", "uprn"],
        requires_os_api=True,
    ),
    EvaluationQuestion(
        id="B003",
        question="Lookup UPRN 100023336959",
        intent=Intent.ADDRESS_LOOKUP,
        difficulty=Difficulty.BASIC,
        description="UPRN lookup via OS Places.",
        expected=ExpectedOutcome(
            required_tools=["os_places.by_uprn"],
            max_tool_calls=2,
            required_keywords=["uprn"],
        ),
        tool_calls=[ToolCallSpec("os_places.by_uprn", {"uprn": "100023336959"})],
        tags=["uprn"],
        requires_os_api=True,
    ),
    EvaluationQuestion(
        id="B004",
        question="Find named features for Oxford",
        intent=Intent.FEATURE_SEARCH,
        difficulty=Difficulty.BASIC,
        description="Named feature search via OS Names.",
        expected=ExpectedOutcome(
            required_tools=["os_names.find"],
            max_tool_calls=2,
            required_keywords=["results"],
        ),
        tool_calls=[ToolCallSpec("os_names.find", {"text": "Oxford"})],
        tags=["names"],
        requires_os_api=True,
    ),
    EvaluationQuestion(
        id="B005",
        question="Vector tiles descriptor",
        intent=Intent.VECTOR_TILES,
        difficulty=Difficulty.BASIC,
        description="Vector tiles descriptor output for OS base map.",
        expected=ExpectedOutcome(
            required_tools=["os_vector_tiles.descriptor"],
            max_tool_calls=2,
            required_keywords=["vectorTiles"],
        ),
        tool_calls=[ToolCallSpec("os_vector_tiles.descriptor", {})],
        tags=["tiles"],
    ),
    EvaluationQuestion(
        id="B006",
        question="Static map descriptor for Westminster bbox",
        intent=Intent.MAP_RENDER,
        difficulty=Difficulty.BASIC,
        description="Static map descriptor with bbox.",
        expected=ExpectedOutcome(
            required_tools=["os_maps.render"],
            max_tool_calls=2,
            required_keywords=["urlTemplate"],
        ),
        tool_calls=[
            ToolCallSpec(
                "os_maps.render",
                {"bbox": [-0.1500, 51.4900, -0.1200, 51.5100]},
            )
        ],
        tags=["map"],
    ),
    EvaluationQuestion(
        id="B007",
        question="List available ONS observation dimensions",
        intent=Intent.DATASET_DISCOVERY,
        difficulty=Difficulty.BASIC,
        description="ONS dimensions listing (live mode).",
        expected=ExpectedOutcome(
            required_tools=["ons_data.dimensions"],
            max_tool_calls=2,
            required_keywords=["dimensions"],
        ),
        tool_calls=[
            ToolCallSpec(
                "ons_data.dimensions",
                {"dataset": "gdp", "edition": "time-series", "version": "1"},
            )
        ],
        tags=["ons"],
        requires_ons_live=True,
    ),
    EvaluationQuestion(
        id="B008",
        question="Search ONS codes for GDP",
        intent=Intent.DATASET_DISCOVERY,
        difficulty=Difficulty.BASIC,
        description="ONS code search using ons_search.query.",
        expected=ExpectedOutcome(
            required_tools=["ons_search.query"],
            max_tool_calls=2,
            required_keywords=["results"],
        ),
        tool_calls=[ToolCallSpec("ons_search.query", {"term": "GDP"})],
        tags=["ons", "search"],
        requires_ons_live=True,
    ),
    EvaluationQuestion(
        id="B008A",
        question="Rank ONS datasets for housing affordability",
        intent=Intent.DATASET_DISCOVERY,
        difficulty=Difficulty.BASIC,
        description="Ranked dataset selection using ons_select.search.",
        expected=ExpectedOutcome(
            required_tools=["ons_select.search"],
            max_tool_calls=2,
            required_keywords=["candidates"],
        ),
        tool_calls=[ToolCallSpec("ons_select.search", {"query": "housing affordability"})],
        tags=["ons", "search", "selection"],
    ),
    EvaluationQuestion(
        id="B008B",
        question="Find an ONS dataset for inflation and prices",
        intent=Intent.DATASET_DISCOVERY,
        difficulty=Difficulty.BASIC,
        description="Ranked dataset selection for inflation topics with related datasets.",
        expected=ExpectedOutcome(
            required_tools=["ons_select.search"],
            max_tool_calls=2,
            required_keywords=["candidates", "relatedDatasets", "catalogMeta"],
        ),
        tool_calls=[
            ToolCallSpec(
                "ons_select.search",
                {"query": "inflation prices dataset", "includeRelated": True, "relatedLimit": 3},
            )
        ],
        tags=["ons", "search", "selection", "inflation"],
    ),
    EvaluationQuestion(
        id="B008C",
        question="Find an ONS dataset for local population change",
        intent=Intent.DATASET_DISCOVERY,
        difficulty=Difficulty.BASIC,
        description="Ranked dataset selection with geography/time hints.",
        expected=ExpectedOutcome(
            required_tools=["ons_select.search"],
            max_tool_calls=2,
            required_keywords=["candidates", "whyThis"],
        ),
        tool_calls=[
            ToolCallSpec(
                "ons_select.search",
                {
                    "query": "population change dataset",
                    "geographyLevel": "local_authority",
                    "timeGranularity": "year",
                },
            )
        ],
        tags=["ons", "search", "selection", "population"],
    ),
    EvaluationQuestion(
        id="B008D",
        question="Find an ONS dataset for net migration",
        intent=Intent.DATASET_DISCOVERY,
        difficulty=Difficulty.BASIC,
        description="Ranked dataset selection for migration topics.",
        expected=ExpectedOutcome(
            required_tools=["ons_select.search"],
            max_tool_calls=2,
            required_keywords=["candidates"],
        ),
        tool_calls=[ToolCallSpec("ons_select.search", {"query": "net migration dataset"})],
        tags=["ons", "search", "selection", "migration"],
    ),
    EvaluationQuestion(
        id="B008E",
        question="Find an ONS dataset for productivity performance",
        intent=Intent.DATASET_DISCOVERY,
        difficulty=Difficulty.BASIC,
        description="Ranked dataset selection with explicit intent tags.",
        expected=ExpectedOutcome(
            required_tools=["ons_select.search"],
            max_tool_calls=2,
            required_keywords=["candidates"],
        ),
        tool_calls=[
            ToolCallSpec(
                "ons_select.search",
                {"query": "productivity dataset", "intentTags": ["productivity"]},
            )
        ],
        tags=["ons", "search", "selection", "productivity"],
    ),
    EvaluationQuestion(
        id="B008F",
        question="Read the ONS dataset catalog resource metadata",
        intent=Intent.DATASET_DISCOVERY,
        difficulty=Difficulty.BASIC,
        description="Validate catalog resource accessibility and metadata fields.",
        expected=ExpectedOutcome(
            required_tools=["resources/read"],
            max_tool_calls=2,
            required_keywords=["generatedAt", "items", "placeholder"],
        ),
        tool_calls=[
            ToolCallSpec(
                "resources/read",
                {"uri": "resource://mcp-geo/ons-catalog"},
                call_type="resource",
            )
        ],
        tags=["ons", "resources", "catalog"],
    ),
    EvaluationQuestion(
        id="B009",
        question="Open a map so I can select wards",
        intent=Intent.INTERACTIVE_SELECTION,
        difficulty=Difficulty.BASIC,
        description="Launch geography selector widget.",
        expected=ExpectedOutcome(
            required_tools=["os_apps.render_geography_selector"],
            max_tool_calls=2,
            required_keywords=["instructions"],
        ),
        tool_calls=[
            ToolCallSpec(
                "os_apps.render_geography_selector",
                {"level": "ward", "focusName": "Westminster", "focusLevel": "local_auth"},
            )
        ],
        tags=["apps", "ui"],
    ),
    EvaluationQuestion(
        id="B010",
        question="Open the statistics dashboard for Westminster",
        intent=Intent.AREA_COMPARISON,
        difficulty=Difficulty.BASIC,
        description="Launch statistics dashboard widget for comparisons.",
        expected=ExpectedOutcome(
            required_tools=["os_apps.render_statistics_dashboard"],
            max_tool_calls=2,
            required_keywords=["instructions"],
        ),
        tool_calls=[
            ToolCallSpec(
                "os_apps.render_statistics_dashboard",
                {"areaCodes": ["E09000033"], "dataset": "gdp", "measure": "GDPV"},
            )
        ],
        tags=["apps", "ui", "ons"],
    ),
    EvaluationQuestion(
        id="B011",
        question="Search for Downing Street addresses",
        intent=Intent.ADDRESS_LOOKUP,
        difficulty=Difficulty.BASIC,
        description="Free text address lookup via OS Places.",
        expected=ExpectedOutcome(
            required_tools=["os_places.search"],
            max_tool_calls=2,
            required_keywords=["results"],
        ),
        tool_calls=[ToolCallSpec("os_places.search", {"text": "Downing Street"})],
        tags=["places", "search"],
        requires_os_api=True,
    ),
    EvaluationQuestion(
        id="B011A",
        question="Search points of interest for cafes in Westminster",
        intent=Intent.PLACE_LOOKUP,
        difficulty=Difficulty.BASIC,
        description="POI text search via os_poi.search.",
        expected=ExpectedOutcome(
            required_tools=["os_poi.search"],
            max_tool_calls=2,
            required_keywords=["results"],
        ),
        tool_calls=[ToolCallSpec("os_poi.search", {"text": "cafes in Westminster", "limit": 5})],
        tags=["poi", "search"],
        requires_os_api=True,
    ),
    EvaluationQuestion(
        id="B011B",
        question="Find nearest POIs to 51.5034,-0.1276",
        intent=Intent.PLACE_LOOKUP,
        difficulty=Difficulty.BASIC,
        description="POI nearest lookup via os_poi.nearest.",
        expected=ExpectedOutcome(
            required_tools=["os_poi.nearest"],
            max_tool_calls=2,
            required_keywords=["results"],
        ),
        tool_calls=[ToolCallSpec("os_poi.nearest", {"lat": 51.5034, "lon": -0.1276, "limit": 5})],
        tags=["poi", "nearest"],
        requires_os_api=True,
    ),
    EvaluationQuestion(
        id="B011C",
        question="Find POIs within a Westminster bbox",
        intent=Intent.PLACE_LOOKUP,
        difficulty=Difficulty.BASIC,
        description="POI bbox lookup via os_poi.within.",
        expected=ExpectedOutcome(
            required_tools=["os_poi.within"],
            max_tool_calls=2,
            required_keywords=["results"],
        ),
        tool_calls=[
            ToolCallSpec(
                "os_poi.within",
                {"bbox": [-0.1310, 51.5020, -0.1250, 51.5060], "limit": 10},
            )
        ],
        tags=["poi", "bbox"],
        requires_os_api=True,
    ),
    EvaluationQuestion(
        id="B012",
        question="Nearest named feature to 51.5034,-0.1276",
        intent=Intent.FEATURE_SEARCH,
        difficulty=Difficulty.BASIC,
        description="OS Names nearest lookup.",
        expected=ExpectedOutcome(
            required_tools=["os_names.nearest"],
            max_tool_calls=2,
            required_keywords=["results"],
        ),
        tool_calls=[ToolCallSpec("os_names.nearest", {"lat": 51.5034, "lon": -0.1276})],
        tags=["names", "nearest"],
        requires_os_api=True,
    ),
    EvaluationQuestion(
        id="B013",
        question="List datasets and dimensions available",
        intent=Intent.DATASET_DISCOVERY,
        difficulty=Difficulty.BASIC,
        description="ONS live code dimensions list.",
        expected=ExpectedOutcome(
            required_tools=["ons_codes.list"],
            max_tool_calls=2,
            required_keywords=["dimensions"],
        ),
        tool_calls=[ToolCallSpec("ons_codes.list", {"dataset": "gdp", "edition": "time-series", "version": "1"})],
        tags=["ons", "codes"],
        requires_ons_live=True,
    ),
    EvaluationQuestion(
        id="B014",
        question="List dataset dimension options for time",
        intent=Intent.DATASET_DISCOVERY,
        difficulty=Difficulty.BASIC,
        description="ONS live code options for a dimension.",
        expected=ExpectedOutcome(
            required_tools=["ons_codes.options"],
            max_tool_calls=2,
            required_keywords=["options"],
        ),
        tool_calls=[ToolCallSpec("ons_codes.options", {"dataset": "gdp", "edition": "time-series", "version": "1", "dimension": "time"})],
        tags=["ons", "codes", "options"],
        requires_ons_live=True,
    ),
    EvaluationQuestion(
        id="B015",
        question="List available editions for the GDP dataset",
        intent=Intent.DATASET_DISCOVERY,
        difficulty=Difficulty.BASIC,
        description="ONS live editions listing.",
        expected=ExpectedOutcome(
            required_tools=["ons_data.editions"],
            max_tool_calls=2,
            required_keywords=["editions"],
        ),
        tool_calls=[ToolCallSpec("ons_data.editions", {"dataset": "gdp"})],
        tags=["ons", "editions"],
        requires_ons_live=True,
    ),
    EvaluationQuestion(
        id="B016",
        question="List versions for the GDP time-series edition",
        intent=Intent.DATASET_DISCOVERY,
        difficulty=Difficulty.BASIC,
        description="ONS live versions listing.",
        expected=ExpectedOutcome(
            required_tools=["ons_data.versions"],
            max_tool_calls=2,
            required_keywords=["versions"],
        ),
        tool_calls=[ToolCallSpec("ons_data.versions", {"dataset": "gdp", "edition": "time-series"})],
        tags=["ons", "versions"],
        requires_ons_live=True,
    ),
    EvaluationQuestion(
        id="B017",
        question="List NOMIS datasets",
        intent=Intent.DATASET_DISCOVERY,
        difficulty=Difficulty.BASIC,
        description="NOMIS dataset list for labour/census stats.",
        expected=ExpectedOutcome(
            required_tools=["nomis.datasets"],
            max_tool_calls=2,
            required_keywords=["dataset"],
        ),
        tool_calls=[ToolCallSpec("nomis.datasets", {})],
        tags=["nomis", "datasets"],
        requires_ons_live=True,
    ),
    EvaluationQuestion(
        id="B018",
        question="List NOMIS codelists",
        intent=Intent.DATASET_DISCOVERY,
        difficulty=Difficulty.BASIC,
        description="NOMIS codelist discovery.",
        expected=ExpectedOutcome(
            required_tools=["nomis.codelists"],
            max_tool_calls=2,
            required_keywords=["codelist"],
        ),
        tool_calls=[ToolCallSpec("nomis.codelists", {})],
        tags=["nomis", "codelists"],
        requires_ons_live=True,
    ),
    EvaluationQuestion(
        id="B018A",
        question="Show NOMIS workflow profiles",
        intent=Intent.DATASET_DISCOVERY,
        difficulty=Difficulty.BASIC,
        description="Read NOMIS workflow profile resource for dataset-specific guidance.",
        expected=ExpectedOutcome(
            required_tools=["resources/read"],
            max_tool_calls=2,
            required_keywords=["profiles", "labour_market_area_compare"],
        ),
        tool_calls=[
            ToolCallSpec(
                "resources/read",
                {"uri": "resource://mcp-geo/nomis-workflows"},
                call_type="resource",
            )
        ],
        tags=["nomis", "resource", "workflow"],
        requires_ons_live=True,
    ),
    EvaluationQuestion(
        id="B019",
        question="Probe MCP-Apps UI rendering mode support",
        intent=Intent.INTERACTIVE_SELECTION,
        difficulty=Difficulty.BASIC,
        description="Verify UI probe tool returns render instructions.",
        expected=ExpectedOutcome(
            required_tools=["os_apps.render_ui_probe"],
            max_tool_calls=2,
            required_keywords=["instructions"],
        ),
        tool_calls=[
            ToolCallSpec(
                "os_apps.render_ui_probe",
                {"resourceUri": "ui://mcp-geo/statistics-dashboard", "contentMode": "text"},
            )
        ],
        tags=["apps", "ui", "probe"],
    ),
    EvaluationQuestion(
        id="B020",
        question="Open a 3D view of Warwick and Leamington wards with premises types",
        intent=Intent.INTERACTIVE_SELECTION,
        difficulty=Difficulty.BASIC,
        description="Launch the Warwick + Leamington 3D UI widget.",
        expected=ExpectedOutcome(
            required_tools=["os_apps.render_warwick_leamington_3d"],
            max_tool_calls=2,
            required_keywords=["instructions"],
        ),
        tool_calls=[ToolCallSpec("os_apps.render_warwick_leamington_3d", {})],
        tags=["apps", "ui", "3d"],
    ),
]


INTERMEDIATE_QUESTIONS = [
    EvaluationQuestion(
        id="I001",
        question="Which administrative areas contain 51.5010,-0.1416?",
        intent=Intent.PLACE_LOOKUP,
        difficulty=Difficulty.INTERMEDIATE,
        description="Containment lookup for a point.",
        expected=ExpectedOutcome(
            required_tools=["admin_lookup.containing_areas"],
            max_tool_calls=2,
            required_keywords=["Westminster"],
        ),
        tool_calls=[ToolCallSpec("admin_lookup.containing_areas", {"lat": 51.5010, "lon": -0.1416})],
        tags=["containment"],
    ),
    EvaluationQuestion(
        id="I002",
        question="Show the hierarchy for ward E05000644",
        intent=Intent.PLACE_LOOKUP,
        difficulty=Difficulty.INTERMEDIATE,
        description="Reverse hierarchy lookup.",
        expected=ExpectedOutcome(
            required_tools=["admin_lookup.reverse_hierarchy"],
            max_tool_calls=2,
            required_keywords=["E05000644"],
        ),
        tool_calls=[ToolCallSpec("admin_lookup.reverse_hierarchy", {"id": "E05000644"})],
        tags=["hierarchy"],
    ),
    EvaluationQuestion(
        id="I003",
        question="Get the boundary bbox for Westminster",
        intent=Intent.BOUNDARY_FETCH,
        difficulty=Difficulty.INTERMEDIATE,
        description="Two-step boundary bbox lookup.",
        expected=ExpectedOutcome(
            required_tools=["admin_lookup.find_by_name", "admin_lookup.area_geometry"],
            max_tool_calls=3,
            required_keywords=["bbox"],
        ),
        tool_calls=[
            ToolCallSpec("admin_lookup.find_by_name", {"text": "Westminster"}),
            ToolCallSpec("admin_lookup.area_geometry", {"id": "E09000033"}),
        ],
        tags=["boundary"],
    ),
    EvaluationQuestion(
        id="I004",
        question="Addresses within a small Westminster bbox",
        intent=Intent.ADDRESS_LOOKUP,
        difficulty=Difficulty.INTERMEDIATE,
        description="OS Places bbox query.",
        expected=ExpectedOutcome(
            required_tools=["os_places.within"],
            max_tool_calls=2,
            required_keywords=["results"],
        ),
        tool_calls=[
            ToolCallSpec("os_places.within", {"bbox": [-0.1310, 51.5020, -0.1250, 51.5060]}),
        ],
        tags=["places", "bbox"],
        requires_os_api=True,
    ),
    EvaluationQuestion(
        id="I005",
        question="Nearest addresses to 51.5034,-0.1276",
        intent=Intent.ADDRESS_LOOKUP,
        difficulty=Difficulty.INTERMEDIATE,
        description="OS Places nearest lookup.",
        expected=ExpectedOutcome(
            required_tools=["os_places.nearest"],
            max_tool_calls=2,
            required_keywords=["results"],
        ),
        tool_calls=[ToolCallSpec("os_places.nearest", {"lat": 51.5034, "lon": -0.1276})],
        tags=["places", "nearest"],
        requires_os_api=True,
    ),
    EvaluationQuestion(
        id="I006",
        question="Resolve linked IDs for UPRN 100021892956",
        intent=Intent.LINKED_IDS,
        difficulty=Difficulty.INTERMEDIATE,
        description="Linked identifiers lookup.",
        expected=ExpectedOutcome(
            required_tools=["os_linked_ids.get"],
            max_tool_calls=2,
            required_keywords=["identifiers"],
        ),
        tool_calls=[ToolCallSpec("os_linked_ids.get", {"identifier": "100021892956"})],
        tags=["linked", "ids"],
        requires_os_api=True,
    ),
    EvaluationQuestion(
        id="I007",
        question="Find building features in a Westminster bbox",
        intent=Intent.FEATURE_SEARCH,
        difficulty=Difficulty.INTERMEDIATE,
        description="OS NGD feature query.",
        expected=ExpectedOutcome(
            required_tools=["os_features.query"],
            max_tool_calls=2,
            required_keywords=["features"],
        ),
        tool_calls=[
            ToolCallSpec(
                "os_features.query",
                {"collection": "buildings", "bbox": [-0.1500, 51.4900, -0.1200, 51.5100]},
            )
        ],
        tags=["features", "ngd"],
        requires_os_api=True,
    ),
    EvaluationQuestion(
        id="I008",
        question="Show two ONS observations for UK GDPV",
        intent=Intent.STATISTICS,
        difficulty=Difficulty.INTERMEDIATE,
        description="ONS query over live observations.",
        expected=ExpectedOutcome(
            required_tools=["ons_data.query"],
            max_tool_calls=2,
            required_keywords=["results"],
        ),
        tool_calls=[
            ToolCallSpec(
                "ons_data.query",
                {
                    "geography": "K02000001",
                    "limit": 2,
                    "dataset": "gdp",
                    "edition": "time-series",
                    "version": "1",
                },
            )
        ],
        tags=["ons", "query"],
        requires_ons_live=True,
    ),
    EvaluationQuestion(
        id="I009",
        question="Create an ONS filter for UK GDPV 2024 Q1-Q2",
        intent=Intent.STATISTICS,
        difficulty=Difficulty.INTERMEDIATE,
        description="ONS filter workflow (create + fetch).",
        expected=ExpectedOutcome(
            required_tools=["ons_data.create_filter", "ons_data.get_filter_output"],
            max_tool_calls=3,
            required_keywords=["filterId"],
        ),
        tool_calls=[
            ToolCallSpec(
                "ons_data.create_filter",
                {
                    "geography": "K02000001",
                    "measure": "GDPV",
                    "timeRange": "2024 Q1-2024 Q2",
                    "dataset": "gdp",
                    "edition": "time-series",
                    "version": "1",
                },
            ),
            ToolCallSpec("ons_data.get_filter_output", {"filterId": "$filterId"}),
        ],
        tags=["ons", "filter"],
        requires_ons_live=True,
    ),
    EvaluationQuestion(
        id="I010",
        question="Plan a route from Coventry to London",
        intent=Intent.ROUTE_PLANNING,
        difficulty=Difficulty.INTERMEDIATE,
        description="Route planner widget.",
        expected=ExpectedOutcome(
            required_tools=["os_apps.render_route_planner"],
            max_tool_calls=2,
            required_keywords=["instructions"],
        ),
        tool_calls=[
            ToolCallSpec(
                "os_apps.render_route_planner",
                {"startLat": 52.4081, "startLng": -1.5106, "endLat": 51.5074, "endLng": -0.1278},
            )
        ],
        tags=["apps", "routing"],
    ),
    EvaluationQuestion(
        id="I011",
        question="Get GDP observation for 2023 Q1",
        intent=Intent.STATISTICS,
        difficulty=Difficulty.INTERMEDIATE,
        description="ONS single observation lookup.",
        expected=ExpectedOutcome(
            required_tools=["ons_data.get_observation"],
            max_tool_calls=2,
            required_keywords=["observation"],
        ),
        tool_calls=[
            ToolCallSpec(
                "ons_data.get_observation",
                {
                    "geography": "K02000001",
                    "measure": "chained_volume_measure",
                    "time": "2023 Q1",
                    "dataset": "gdp",
                    "edition": "time-series",
                    "version": "1",
                },
            )
        ],
        tags=["ons", "observation"],
        requires_ons_live=True,
    ),
    EvaluationQuestion(
        id="I012",
        question="Export a GDP filter output as CSV",
        intent=Intent.STATISTICS,
        difficulty=Difficulty.INTERMEDIATE,
        description="ONS filter output export using CSV format.",
        expected=ExpectedOutcome(
            required_tools=["ons_data.create_filter", "ons_data.get_filter_output"],
            max_tool_calls=3,
            required_keywords=["CSV"],
        ),
        tool_calls=[
            ToolCallSpec(
                "ons_data.create_filter",
                {
                    "geography": "K02000001",
                    "measure": "GDPV",
                    "timeRange": "2024 Q1-2024 Q2",
                    "dataset": "gdp",
                    "edition": "time-series",
                    "version": "1",
                },
            ),
            ToolCallSpec("ons_data.get_filter_output", {"filterId": "$filterId", "format": "CSV"}),
        ],
        tags=["ons", "filter", "csv"],
        requires_ons_live=True,
    ),
    EvaluationQuestion(
        id="I013",
        question="List NOMIS concepts",
        intent=Intent.DATASET_DISCOVERY,
        difficulty=Difficulty.INTERMEDIATE,
        description="NOMIS concept discovery.",
        expected=ExpectedOutcome(
            required_tools=["nomis.concepts"],
            max_tool_calls=2,
            required_keywords=["concept"],
        ),
        tool_calls=[ToolCallSpec("nomis.concepts", {})],
        tags=["nomis", "concepts"],
        requires_ons_live=True,
    ),
    EvaluationQuestion(
        id="I014",
        question="Should LSOA unemployment rate use NOMIS or ONS?",
        intent=Intent.STATISTICS,
        difficulty=Difficulty.INTERMEDIATE,
        description="Stats routing explanation tool.",
        expected=ExpectedOutcome(
            required_tools=["os_mcp.stats_routing"],
            max_tool_calls=2,
            required_keywords=["provider", "recommendedTool"],
        ),
        tool_calls=[
            ToolCallSpec(
                "os_mcp.stats_routing",
                {"query": "Unemployment rate for LSOA in Leeds"},
            )
        ],
        tags=["routing", "stats"],
    ),
    EvaluationQuestion(
        id="I015",
        question="Find an ONS dataset for housing affordability by local authority",
        intent=Intent.DATASET_DISCOVERY,
        difficulty=Difficulty.INTERMEDIATE,
        description="Ranked dataset selection with related datasets and geography/time hints.",
        expected=ExpectedOutcome(
            required_tools=["ons_select.search"],
            max_tool_calls=2,
            required_keywords=["candidates", "relatedDatasets"],
        ),
        tool_calls=[
            ToolCallSpec(
                "ons_select.search",
                {
                    "query": "housing affordability dataset",
                    "geographyLevel": "local_authority",
                    "timeGranularity": "year",
                    "includeRelated": True,
                    "relatedLimit": 5,
                },
            )
        ],
        tags=["ons", "search", "selection", "housing"],
    ),
    EvaluationQuestion(
        id="I016",
        question="Find an ONS dataset for weekly deaths by region",
        intent=Intent.DATASET_DISCOVERY,
        difficulty=Difficulty.INTERMEDIATE,
        description="Ranked dataset selection for mortality topics.",
        expected=ExpectedOutcome(
            required_tools=["ons_select.search"],
            max_tool_calls=2,
            required_keywords=["candidates", "catalogMeta"],
        ),
        tool_calls=[
            ToolCallSpec(
                "ons_select.search",
                {"query": "weekly deaths dataset region", "includeRelated": True},
            )
        ],
        tags=["ons", "search", "selection", "mortality"],
    ),
    EvaluationQuestion(
        id="I017",
        question="Find comparable weekly deaths datasets and explain why they relate",
        intent=Intent.DATASET_DISCOVERY,
        difficulty=Difficulty.INTERMEDIATE,
        description="Validate related dataset explainability fields for comparability gating.",
        expected=ExpectedOutcome(
            required_tools=["ons_select.search"],
            max_tool_calls=2,
            required_keywords=["relatedDatasets", "linkReason", "provenance"],
        ),
        tool_calls=[
            ToolCallSpec(
                "ons_select.search",
                {
                    "query": "weekly deaths dataset region",
                    "includeRelated": True,
                    "relatedLimit": 5,
                },
            )
        ],
        tags=["ons", "search", "selection", "comparability"],
    ),
]


ADVANCED_QUESTIONS = [
    EvaluationQuestion(
        id="A001",
        question="Compare wellbeing between Westminster and Greater London",
        intent=Intent.AREA_COMPARISON,
        difficulty=Difficulty.ADVANCED,
        description="Multi-area comparison workflow.",
        expected=ExpectedOutcome(
            required_tools=["os_apps.render_statistics_dashboard"],
            max_tool_calls=3,
            required_keywords=["instructions"],
        ),
        tool_calls=[
            ToolCallSpec(
                "os_apps.render_statistics_dashboard",
                {"areaCodes": ["E09000033", "E10000014"], "dataset": "wellbeing", "measure": "life-satisfaction"},
            )
        ],
        tags=["comparison"],
    ),
    EvaluationQuestion(
        id="A002",
        question="Select an OA in Westminster and fetch its boundary",
        intent=Intent.INTERACTIVE_SELECTION,
        difficulty=Difficulty.ADVANCED,
        description="Interactive selection + boundary lookup.",
        expected=ExpectedOutcome(
            required_tools=["os_apps.render_geography_selector", "admin_lookup.area_geometry"],
            max_tool_calls=4,
            required_keywords=["instructions"],
        ),
        tool_calls=[
            ToolCallSpec(
                "os_apps.render_geography_selector",
                {"level": "oa", "focusName": "Westminster", "focusLevel": "local_auth"},
            ),
            ToolCallSpec("admin_lookup.area_geometry", {"id": "E00023939"}),
        ],
        tags=["apps", "boundary"],
    ),
    EvaluationQuestion(
        id="A003",
        question="Inspect an NGD feature id",
        intent=Intent.FEATURE_SEARCH,
        difficulty=Difficulty.ADVANCED,
        description="Feature inspector widget.",
        expected=ExpectedOutcome(
            required_tools=["os_apps.render_feature_inspector"],
            max_tool_calls=2,
            required_keywords=["instructions"],
        ),
        tool_calls=[
            ToolCallSpec(
                "os_apps.render_feature_inspector",
                {"collectionId": "buildings", "featureId": "osgb1000000123456"},
            )
        ],
        tags=["apps", "features"],
    ),
    EvaluationQuestion(
        id="A004",
        question="Build a map stack for Westminster (tiles + static)",
        intent=Intent.MAP_RENDER,
        difficulty=Difficulty.ADVANCED,
        description="Vector tiles + static map descriptors.",
        expected=ExpectedOutcome(
            required_tools=["os_vector_tiles.descriptor", "os_maps.render"],
            max_tool_calls=3,
            required_keywords=["vectorTiles"],
        ),
        tool_calls=[
            ToolCallSpec("os_vector_tiles.descriptor", {}),
            ToolCallSpec("os_maps.render", {"bbox": [-0.1500, 51.4900, -0.1200, 51.5100]}),
        ],
        tags=["map", "tiles"],
    ),
    EvaluationQuestion(
        id="A005",
        question="Find tools related to postcode search",
        intent=Intent.UNKNOWN,
        difficulty=Difficulty.ADVANCED,
        description="Tool search endpoint validation.",
        expected=ExpectedOutcome(
            required_tools=["tools/search"],
            max_tool_calls=2,
            required_keywords=["os_places.by_postcode"],
        ),
        tool_calls=[ToolCallSpec("tools/search", {"query": "postcode"}, call_type="tools_search")],
        tags=["tool-search"],
    ),
    EvaluationQuestion(
        id="A006",
        question="Fetch the MCP Geo skills guide",
        intent=Intent.UNKNOWN,
        difficulty=Difficulty.ADVANCED,
        description="Skills resource fetch.",
        expected=ExpectedOutcome(
            required_tools=["resources/read"],
            max_tool_calls=2,
            required_keywords=["MCP Geo Skills"],
        ),
        tool_calls=[
            ToolCallSpec(
                "resources/read",
                {"uri": "skills://mcp-geo/getting-started"},
                call_type="resource",
            )
        ],
        tags=["resources", "skills"],
    ),
    EvaluationQuestion(
        id="A007",
        question="Describe server capabilities and tool search config",
        intent=Intent.UNKNOWN,
        difficulty=Difficulty.ADVANCED,
        description="Server descriptor output.",
        expected=ExpectedOutcome(
            required_tools=["os_mcp.descriptor"],
            max_tool_calls=2,
            required_keywords=["toolSearch"],
        ),
        tool_calls=[ToolCallSpec("os_mcp.descriptor", {})],
        tags=["descriptor", "mcp"],
    ),
    EvaluationQuestion(
        id="A008",
        question="Log a UI event for analytics",
        intent=Intent.UNKNOWN,
        difficulty=Difficulty.ADVANCED,
        description="UI event logging for MCP-Apps widgets.",
        expected=ExpectedOutcome(
            required_tools=["os_apps.log_event"],
            max_tool_calls=2,
            required_keywords=["eventId"],
        ),
        tool_calls=[
            ToolCallSpec(
                "os_apps.log_event",
                {
                    "eventType": "ui_test",
                    "source": "evaluation",
                    "payload": {"action": "click"},
                    "context": {"screen": "dashboard"},
                    "timestamp": 1710000000,
                    "sessionId": "session-eval",
                },
            )
        ],
        tags=["apps", "log"],
    ),
    EvaluationQuestion(
        id="A009",
        question="Query NOMIS for unemployment count in Westminster",
        intent=Intent.STATISTICS,
        difficulty=Difficulty.ADVANCED,
        description="NOMIS query workflow.",
        expected=ExpectedOutcome(
            required_tools=["nomis.query"],
            max_tool_calls=2,
            required_keywords=["dataset"],
        ),
        tool_calls=[
            ToolCallSpec(
                "nomis.query",
                {
                    "dataset": "NM_1",
                    "params": {"geography": "E09000033", "measures": "20100"},
                },
            )
        ],
        tags=["nomis", "query"],
        requires_ons_live=True,
    ),
    EvaluationQuestion(
        id="A010",
        question="Build a boundary inventory and export it for Westminster ward",
        intent=Intent.INTERACTIVE_SELECTION,
        difficulty=Difficulty.ADVANCED,
        description="Boundary explorer + layer inventory + export workflow (coverage for helper tools).",
        expected=ExpectedOutcome(
            required_tools=[
                "os_apps.render_boundary_explorer",
                "os_features.collections",
                "os_map.inventory",
                "os_map.export",
            ],
            max_tool_calls=6,
            required_keywords=["boundary-explorer", "latestByBaseId", "requestedLayers", "exports/"],
        ),
        tool_calls=[
            ToolCallSpec(
                "os_apps.render_boundary_explorer",
                {"level": "WARD", "searchTerm": "Westminster", "detailLevel": "postcode"},
            ),
            ToolCallSpec("os_features.collections", {}),
            ToolCallSpec(
                "os_map.inventory",
                {
                    "bbox": [-0.1500, 51.4900, -0.1200, 51.5100],
                    "layers": ["uprns", "buildings", "road_links", "path_links"],
                    "limits": {"uprns": 50, "buildings": 10, "road_links": 10, "path_links": 10},
                },
            ),
            ToolCallSpec(
                "os_map.export",
                {
                    "bbox": [-0.1500, 51.4900, -0.1200, 51.5100],
                    "name": "evaluation-export",
                    "layers": ["uprns", "buildings", "road_links", "path_links"],
                    "limits": {"uprns": 50, "buildings": 10, "road_links": 10, "path_links": 10},
                },
            ),
        ],
        tags=["maps", "inventory", "export", "ui"],
    ),
]


EDGE_CASE_QUESTIONS = [
    EvaluationQuestion(
        id="E001",
        question="Lookup postcode ZZ99ZZ",
        intent=Intent.ADDRESS_LOOKUP,
        difficulty=Difficulty.EDGE,
        description="Invalid postcode should trigger validation error.",
        expected=ExpectedOutcome(
            required_tools=["os_places.by_postcode"],
            max_tool_calls=2,
            required_keywords=["INVALID_INPUT"],
        ),
        tool_calls=[
            ToolCallSpec("os_places.by_postcode", {"postcode": "ZZ99ZZ"}, expect_error=True),
        ],
        tags=["edge", "validation"],
    ),
    EvaluationQuestion(
        id="E002",
        question="Render a map with invalid bbox values",
        intent=Intent.MAP_RENDER,
        difficulty=Difficulty.EDGE,
        description="Invalid bbox should error.",
        expected=ExpectedOutcome(
            required_tools=["os_maps.render"],
            max_tool_calls=2,
            required_keywords=["INVALID_INPUT"],
        ),
        tool_calls=[ToolCallSpec("os_maps.render", {"bbox": ["x", 1, 2, 3]}, expect_error=True)],
        tags=["edge", "validation"],
    ),
    EvaluationQuestion(
        id="E003",
        question="Fetch boundary for unknown area id",
        intent=Intent.BOUNDARY_FETCH,
        difficulty=Difficulty.EDGE,
        description="Unknown id should return NOT_FOUND.",
        expected=ExpectedOutcome(
            required_tools=["admin_lookup.area_geometry"],
            max_tool_calls=2,
            required_keywords=["NOT_FOUND"],
        ),
        tool_calls=[ToolCallSpec("admin_lookup.area_geometry", {"id": "E99999999"}, expect_error=True)],
        tags=["edge", "not-found"],
    ),
    EvaluationQuestion(
        id="E004",
        question="Fetch an unknown ONS filter output",
        intent=Intent.STATISTICS,
        difficulty=Difficulty.EDGE,
        description="Unknown filter id should return UNKNOWN_FILTER.",
        expected=ExpectedOutcome(
            required_tools=["ons_data.get_filter_output"],
            max_tool_calls=2,
            required_keywords=["UNKNOWN_FILTER"],
        ),
        tool_calls=[ToolCallSpec("ons_data.get_filter_output", {"filterId": "unknown"}, expect_error=True)],
        tags=["edge", "ons"],
        requires_ons_live=True,
    ),
    EvaluationQuestion(
        id="E005",
        question="Run dataset selection with invalid relatedLimit",
        intent=Intent.DATASET_DISCOVERY,
        difficulty=Difficulty.EDGE,
        description="ons_select.search should reject invalid relatedLimit.",
        expected=ExpectedOutcome(
            required_tools=["ons_select.search"],
            max_tool_calls=2,
            required_keywords=["INVALID_INPUT"],
        ),
        tool_calls=[
            ToolCallSpec(
                "ons_select.search",
                {"query": "inflation dataset", "includeRelated": True, "relatedLimit": 0},
                expect_error=True,
            )
        ],
        tags=["edge", "ons", "selection"],
    ),
    EvaluationQuestion(
        id="E006",
        question="Run dataset selection with invalid includeRelated type",
        intent=Intent.DATASET_DISCOVERY,
        difficulty=Difficulty.EDGE,
        description="ons_select.search should reject non-boolean includeRelated.",
        expected=ExpectedOutcome(
            required_tools=["ons_select.search"],
            max_tool_calls=2,
            required_keywords=["INVALID_INPUT"],
        ),
        tool_calls=[
            ToolCallSpec(
                "ons_select.search",
                {"query": "migration dataset", "includeRelated": "yes"},
                expect_error=True,
            )
        ],
        tags=["edge", "ons", "selection"],
    ),
]


AMBIGUOUS_QUESTIONS = [
    EvaluationQuestion(
        id="M001",
        question="St James's",
        intent=Intent.PLACE_LOOKUP,
        difficulty=Difficulty.AMBIGUOUS,
        description="Ambiguous ward name lookup.",
        expected=ExpectedOutcome(
            required_tools=["admin_lookup.find_by_name"],
            max_tool_calls=2,
            required_keywords=["St James"],
        ),
        tool_calls=[ToolCallSpec("admin_lookup.find_by_name", {"text": "St James"})],
        tags=["ambiguous"],
    ),
    EvaluationQuestion(
        id="M002",
        question="Westminster data",
        intent=Intent.STATISTICS,
        difficulty=Difficulty.AMBIGUOUS,
        description="Ambiguous request leaning toward statistics.",
        expected=ExpectedOutcome(
            required_tools=["ons_data.query"],
            max_tool_calls=2,
            required_keywords=["results"],
        ),
        tool_calls=[ToolCallSpec("ons_data.query", {"dataset": "gdp", "edition": "time-series", "version": "1", "geography": "K02000001", "limit": 2})],
        tags=["ambiguous", "ons"],
        requires_ons_live=True,
    ),
    EvaluationQuestion(
        id="M003",
        question="Select Westminster ward",
        intent=Intent.INTERACTIVE_SELECTION,
        difficulty=Difficulty.AMBIGUOUS,
        description="Selection phrasing should trigger geography selector.",
        expected=ExpectedOutcome(
            required_tools=["os_apps.render_geography_selector"],
            max_tool_calls=2,
            required_keywords=["instructions"],
        ),
        tool_calls=[
            ToolCallSpec(
                "os_apps.render_geography_selector",
                {"level": "ward", "focusName": "Westminster", "focusLevel": "local_auth"},
            )
        ],
        tags=["ambiguous", "ui"],
    ),
    EvaluationQuestion(
        id="M004",
        question="Find a dataset for cost of living",
        intent=Intent.DATASET_DISCOVERY,
        difficulty=Difficulty.AMBIGUOUS,
        description="Ambiguous dataset selection should return elicitation prompts.",
        expected=ExpectedOutcome(
            required_tools=["ons_select.search"],
            max_tool_calls=2,
            required_keywords=["elicitationQuestions"],
        ),
        tool_calls=[ToolCallSpec("ons_select.search", {"query": "cost of living dataset"})],
        tags=["ambiguous", "ons", "selection"],
    ),
]


CACHE_QUESTIONS = [
    EvaluationQuestion(
        id="C001",
        question="Show boundary cache status",
        intent=Intent.UNKNOWN,
        difficulty=Difficulty.BASIC,
        description="Audit cache status for local PostGIS boundaries.",
        expected=ExpectedOutcome(
            required_tools=["admin_lookup.get_cache_status"],
            max_tool_calls=1,
        ),
        tool_calls=[ToolCallSpec("admin_lookup.get_cache_status", {})],
        tags=["cache", "admin"],
    ),
    EvaluationQuestion(
        id="C002",
        question="Search the boundary cache for Westminster",
        intent=Intent.UNKNOWN,
        difficulty=Difficulty.BASIC,
        description="Search cache entries by name.",
        expected=ExpectedOutcome(
            required_tools=["admin_lookup.search_cache"],
            max_tool_calls=1,
        ),
        tool_calls=[ToolCallSpec("admin_lookup.search_cache", {"query": "Westminster", "limit": 5})],
        tags=["cache", "admin"],
    ),
]


ALL_QUESTIONS = (
    BASIC_QUESTIONS
    + INTERMEDIATE_QUESTIONS
    + ADVANCED_QUESTIONS
    + EDGE_CASE_QUESTIONS
    + AMBIGUOUS_QUESTIONS
    + CACHE_QUESTIONS
)

QUESTIONS_BY_ID = {q.id: q for q in ALL_QUESTIONS}


def get_questions(
    *,
    intent: Optional[Intent] = None,
    difficulty: Optional[Difficulty] = None,
) -> List[EvaluationQuestion]:
    questions = ALL_QUESTIONS
    if intent:
        questions = [q for q in questions if q.intent == intent]
    if difficulty:
        questions = [q for q in questions if q.difficulty == difficulty]
    return questions


def get_question_summary() -> Dict[str, int]:
    summary: Dict[str, int] = {}
    for q in ALL_QUESTIONS:
        key = f"{q.intent.value}:{q.difficulty.value}"
        summary[key] = summary.get(key, 0) + 1
    return summary
