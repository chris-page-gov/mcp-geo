from __future__ import annotations

import re
from enum import StrEnum
from typing import Any

from server import __version__ as SERVER_VERSION
from server.mcp.resource_catalog import MCP_APPS_MIME, SKILLS_RESOURCE
from server.mcp.tool_search import (
    apply_default_toolset_filters,
    filter_tool_names_by_toolsets,
    get_tool_search_config,
    get_toolset_catalog,
    parse_toolset_list,
)
from server.protocol import (
    MCP_APPS_PROTOCOL_VERSION,
    PROTOCOL_VERSION,
    SUPPORTED_PROTOCOL_VERSIONS,
)
from tools.registry import Tool, ToolResult, all_tools, register


class QueryIntent(StrEnum):
    ADDRESS_LOOKUP = "address_lookup"
    POI_LOOKUP = "poi_lookup"
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
    ENVIRONMENTAL_SURVEY = "environmental_survey"
    UNKNOWN = "unknown"


POSTCODE_REGEX = re.compile(
    r"\b[A-Z]{1,2}[0-9][0-9A-Z]?\s*[0-9][A-Z]{2}\b",
    re.IGNORECASE,
)
UPRN_REGEX = re.compile(r"\b\d{8,13}\b")

PLACE_LOOKUP_PATTERNS = [
    (
        r"\b(find|search|locate|where is|look up|get|show me)\b.*"
        r"\b(city|town|borough|district|county|region|ward|area)\b"
    ),
    r"\barea code\b",
    r"\bgss code\b",
    r"\bwhat is the code for\b",
    r"\blocal authority\b",
    r"\bparliamentary constituency\b",
    r"\bhierarchy\b",
]

STATISTICS_PATTERNS = [
    (
        r"\b(statistics|stats|data|wellbeing|population|house prices?|gdp|life expectancy|"
        r"census|employment|unemployment|health)\b"
    ),
    r"\bhow (many|much)\b.*\b(in|for)\b",
    r"\bfilter output\b",
    r"\bfilter ?id\b",
]

NOMIS_PATTERNS = [
    r"\bcensus\b",
    r"\blabou?r\b",
    r"\bemployment\b",
    r"\bunemployment\b",
    r"\bclaimant\b",
    r"\bjobseeker\b",
    r"\bearnings?\b",
    r"\baps\b",
    r"\bashe\b",
    r"\bqualification(s)?\b",
    r"\beconomic activity\b",
]


def _build_stats_routing_explanation(query_lower: str, level_mentions: list[str]) -> dict[str, Any]:
    matched = [pattern for pattern in NOMIS_PATTERNS if re.search(pattern, query_lower)]
    matched_levels = [level for level in level_mentions if level in {"oa", "lsoa", "msoa"}]
    nomis_preferred = bool(matched or matched_levels)
    reasons: list[str] = []
    if matched:
        reasons.append("Matched labour/census keyword(s).")
    if matched_levels:
        reasons.append("Detected deep local geography (OA/LSOA/MSOA).")
    if not reasons:
        reasons.append("Defaulted to ONS (no labour/census keywords or deep local geographies).")
    return {
        "provider": "nomis" if nomis_preferred else "ons",
        "nomisPreferred": nomis_preferred,
        "reasons": reasons,
        "matchedPatterns": matched,
        "matchedLevels": matched_levels,
    }

COMPARISON_PATTERNS = [
    r"\bcompare\b",
    r"\bcomparison\b",
    r"\bvs\.?\b",
    r"\bversus\b",
    r"\bbetter than\b",
]

FEATURE_SEARCH_PATTERNS = [
    (
        r"\b(buildings?|roads?|streets?|railway|station|bridges?|path links?|road links?|"
        r"parcels?|topograph(y|ic))\b"
    ),
    r"\bfeatures?\b",
    r"\bngd\b",
]

SURVEY_PATTERNS = [
    r"\bpeatland\b",
    r"\bpeat\b",
    r"\bsite survey\b",
    r"\benvironmental survey\b",
    r"\bhabitat survey\b",
    r"\bhydrolog(y|ical)\b",
]

POI_PATTERNS = [
    r"\bpoi\b",
    r"\bpoints? of interest\b",
    r"\bamenit(y|ies)\b",
    (
        r"\bnearby\b.*\b(caf(e|es)|restaurants?|pubs?|shops?|hospitals?|schools?|"
        r"pharmacies?|atms?|hotels?|museums?|cinemas?)\b"
    ),
    (
        r"\b(caf(e|es)|restaurants?|pubs?|shops?|hospitals?|schools?|pharmacies?|atms?|"
        r"hotels?|museums?|cinemas?)\b"
    ),
]

BOUNDARY_PATTERNS = [
    r"\bboundary\b",
    r"\bboundaries\b",
    r"\bgeojson\b",
    r"\bpolygon\b",
    r"\bshape\b",
    r"\boutline\b",
]

INTERACTIVE_PATTERNS = [
    r"\bselect\b.*\bmap\b",
    r"\bmap\b.*\bselect\b",
    r"\bopen\b.*\bmap\b",
    r"\binteractive\b",
    r"\blet me (choose|pick|select)\b",
    r"\bpick\b.*\bareas?\b",
]

BOUNDARY_EXPLORER_HINT_PATTERNS = [
    r"\buprn(s)?\b",
    r"\bbuilding(s)?\b",
    r"\broad links?\b",
    r"\bpath links?\b",
    r"\broadlink\b",
    r"\bpathlink\b",
    r"\blayer(s)?\b",
    r"\bshapefile(s)?\b",
    r"\binventory\b",
    r"\bexport\b",
]

ROUTE_PATTERNS = [
    r"\broute\b",
    r"\bdirections?\b",
    r"\bhow (do i|to|can i) get\b",
    r"\bfrom\b.*\bto\b",
]

DATASET_PATTERNS = [
    r"\bwhat (datasets?|data) (are|is) available\b",
    r"\blist.*datasets?\b",
    r"\bavailable.*data\b",
    r"\bdatasets?\b",
    r"\b(list|search|find|show)\b.*\b(dimensions?|codes?|editions?|versions?|codelists?|concepts?)\b",
    r"\bons\b.*\b(dimensions?|codes?|editions?|versions?)\b",
    r"\bnomis\b.*\b(datasets?|codelists?|concepts?|workflow)\b",
    r"\bworkflow profiles?\b",
]

VECTOR_TILE_PATTERNS = [
    r"\bvector tiles?\b",
    r"\btiles? descriptor\b",
    r"\bmap tiles?\b",
]

MAP_RENDER_PATTERNS = [
    r"\bstatic map\b",
    r"\brender map\b",
    r"\brender (a )?map\b",
    r"\bmap render\b",
    r"\bmap descriptor\b",
    r"\bmap image\b",
    r"\bmap stack\b",
    r"\btiles?\b.*\bstatic\b",
    r"\bstatic\b.*\btiles?\b",
]

LINKED_ID_PATTERNS = [
    r"\buprn(s)?\b",
    r"\busrn(s)?\b",
    r"\btoid(s)?\b",
    r"\blinked id\b",
    r"\blinked ids\b",
    r"\blinked identifiers?\b",
]

CORRELATION_METHOD_REGEX = re.compile(r"\b[A-Z0-9_]+_[0-9]+\b")
LAT_LON_REGEX = re.compile(r"\b(-?\d{1,2}\.\d+)\s*,\s*(-?\d{1,3}\.\d+)\b")
AREA_CODE_REGEX = re.compile(r"\b([EKNSW]\d{8})\b", re.IGNORECASE)

_PLACE_NAME_STOP_WORDS = {
    "a",
    "an",
    "and",
    "build",
    "cache",
    "capabilities",
    "code",
    "codes",
    "config",
    "configuration",
    "create",
    "describe",
    "edition",
    "editions",
    "event",
    "fetch",
    "filter",
    "find",
    "for",
    "from",
    "get",
    "guide",
    "hierarchy",
    "in",
    "list",
    "log",
    "map",
    "mcp",
    "mode",
    "nomis",
    "observation",
    "observations",
    "of",
    "ons",
    "open",
    "probe",
    "render",
    "search",
    "server",
    "show",
    "skills",
    "stack",
    "static",
    "status",
    "the",
    "to",
    "tool",
    "tools",
    "ui",
    "version",
    "versions",
    "widget",
    "workflow",
}

LEVEL_KEYWORDS = {
    "oa": [r"\boa\b", r"\boutput areas?\b"],
    "lsoa": [r"\blsoa\b", r"\blower (layer )?super output areas?\b"],
    "msoa": [r"\bmsoa\b", r"\bmiddle (layer )?super output areas?\b"],
    "ward": [r"\bwards?\b"],
    "parl_const": [r"\bconstituenc(y|ies)\b", r"\bparliamentary\b", r"\bmp\b"],
    "local_auth": [r"\blocal authority\b", r"\bcouncil\b", r"\bdistrict\b", r"\bborough\b"],
    "built_up_area": [r"\bbuilt[- ]?up area\b", r"\bbua\b"],
    "postcode": [r"\bpostcode\b"],
}

LEVEL_RANK = {
    "oa": 0,
    "lsoa": 1,
    "msoa": 2,
    "ward": 3,
    "parl_const": 4,
    "local_auth": 5,
    "built_up_area": 6,
    "postcode": 7,
}

ADMIN_LEVEL_MAP = {
    "oa": "OA",
    "lsoa": "LSOA",
    "msoa": "MSOA",
    "ward": "WARD",
    "local_auth": "DISTRICT",
    "parl_const": None,
    "built_up_area": None,
    "postcode": None,
}

FEATURE_COLLECTIONS = {
    "building": "buildings",
    "buildings": "buildings",
    "road": "roads",
    "roads": "roads",
    "school": "schools",
    "schools": "schools",
    "hospital": "hospitals",
    "hospitals": "hospitals",
    "cinema": "cinemas",
    "cinemas": "cinemas",
    "park": "parks",
    "parks": "parks",
}

NOMIS_WORKFLOW_URI = "resource://mcp-geo/nomis-workflows"

INTENT_TOOLSET_MAP: dict[QueryIntent, list[str]] = {
    QueryIntent.ADDRESS_LOOKUP: ["core_router", "places_names", "ons_geo_lookup"],
    QueryIntent.POI_LOOKUP: ["core_router", "places_names"],
    QueryIntent.PLACE_LOOKUP: ["core_router", "admin_boundaries"],
    QueryIntent.STATISTICS: ["core_router", "ons_data"],
    QueryIntent.AREA_COMPARISON: ["core_router", "apps_ui", "ons_data"],
    QueryIntent.FEATURE_SEARCH: ["core_router", "features_layers"],
    QueryIntent.BOUNDARY_FETCH: ["core_router", "admin_boundaries"],
    QueryIntent.INTERACTIVE_SELECTION: ["core_router", "apps_ui", "admin_boundaries"],
    QueryIntent.ROUTE_PLANNING: ["core_router", "apps_ui", "maps_tiles"],
    QueryIntent.DATASET_DISCOVERY: ["core_router", "ons_selection", "ons_data"],
    QueryIntent.MAP_RENDER: ["core_router", "maps_tiles"],
    QueryIntent.VECTOR_TILES: ["core_router", "maps_tiles"],
    QueryIntent.LINKED_IDS: ["core_router", "places_names"],
    QueryIntent.ENVIRONMENTAL_SURVEY: [
        "core_router",
        "features_layers",
        "admin_boundaries",
        "protected_landscapes",
    ],
    QueryIntent.UNKNOWN: ["starter"],
}


def _match_patterns(query: str, patterns: list[str]) -> float:
    query_lower = query.lower()
    matches = sum(1 for pattern in patterns if re.search(pattern, query_lower, re.IGNORECASE))
    return min(matches / max(len(patterns) * 0.3, 1), 1.0)


def _normalize_postcode(postcode: str) -> str:
    return re.sub(r"\s+", "", postcode).upper()


def _extract_postcode(query: str) -> str | None:
    match = POSTCODE_REGEX.search(query)
    if not match:
        return None
    return _normalize_postcode(match.group(0))


def _extract_uprn(query: str) -> str | None:
    match = UPRN_REGEX.search(query)
    if not match:
        return None
    return match.group(0)


def _is_geography_lookup_query(query_lower: str) -> bool:
    patterns = [
        r"\bgeograph(y|ies)\b",
        r"\bonspd\b|\bonsud\b|\bnspl\b|\bnsul\b",
        r"\bexact\b.*\bmode\b",
        r"\bbest[- ]?fit\b",
        (
            r"\bwhich\b.*\b(ward|lsoa|msoa|oa|local authority|district|borough|region|"
            r"constituenc(y|ies))\b"
        ),
    ]
    return any(re.search(pattern, query_lower) for pattern in patterns)


def _extract_derivation_mode(query_lower: str) -> str | None:
    if re.search(r"\bnspl\b|\bnsul\b|\bbest[- ]?fit\b", query_lower):
        return "best_fit"
    if re.search(r"\bonspd\b|\bonsud\b|\bexact\b", query_lower):
        return "exact"
    return None


def _extract_correlation_method(query: str) -> str | None:
    match = CORRELATION_METHOD_REGEX.search(query.strip())
    if not match:
        return None
    return match.group(0)


def _extract_area_code(query: str) -> str | None:
    match = AREA_CODE_REGEX.search(query)
    if not match:
        return None
    return match.group(1).upper()


def _extract_place_name(query: str) -> str | None:
    directional_pattern = re.compile(
        r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+"
        r"(North East|North West|South East|South West|North|South|East|West|Central)\b"
    )
    directional_match = directional_pattern.search(query)
    if directional_match:
        candidate = directional_match.group(0)
        return candidate.title() if candidate.islower() else candidate
    known_places = [
        "birmingham",
        "manchester",
        "london",
        "coventry",
        "leeds",
        "liverpool",
        "sheffield",
        "bristol",
        "edinburgh",
        "glasgow",
        "cardiff",
        "belfast",
        "westminster",
        "oxford",
        "cambridge",
        "york",
    ]
    query_lower = query.lower()
    for place in known_places:
        if place in query_lower:
            return place.title()
    words = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", query)
    for word in words:
        tokens = word.split()
        if tokens and tokens[0].lower() in _PLACE_NAME_STOP_WORDS:
            if len(tokens) > 1:
                candidate = " ".join(tokens[1:])
                if candidate.lower() not in _PLACE_NAME_STOP_WORDS:
                    return candidate
            continue
        if word.lower() not in _PLACE_NAME_STOP_WORDS:
            return str(word)
    return None


def _extract_lat_lon(query: str) -> tuple[float, float] | None:
    match = LAT_LON_REGEX.search(query)
    if not match:
        return None
    lat = float(match.group(1))
    lon = float(match.group(2))
    if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
        return None
    return lat, lon


def _extract_landscape_focus(query: str) -> str | None:
    query_norm = query.strip()
    if not query_norm:
        return None
    if re.search(r"\bforrest of bowland\b", query_norm, re.IGNORECASE):
        return "Forest of Bowland"
    if re.search(r"\bforest of bowland\b", query_norm, re.IGNORECASE):
        return "Forest of Bowland"
    match = re.search(
        r"\b(?:survey|on|for)\s+(?:the\s+)?([A-Za-z][A-Za-z\s-]{3,80})$",
        query_norm,
        re.IGNORECASE,
    )
    if match:
        candidate = match.group(1).strip(" .")
        if candidate:
            return candidate
    return None


def _find_level_mentions(query_lower: str) -> list[str]:
    hits: list[str] = []
    for level, patterns in LEVEL_KEYWORDS.items():
        for pattern in patterns:
            if re.search(pattern, query_lower, re.IGNORECASE):
                hits.append(level)
                break
    return hits


def _pick_smallest_level(levels: list[str]) -> str | None:
    if not levels:
        return None
    return min(levels, key=lambda level: LEVEL_RANK.get(level, 99))


def _pick_largest_level(levels: list[str]) -> str | None:
    if not levels:
        return None
    return max(levels, key=lambda level: LEVEL_RANK.get(level, -1))


def _pick_admin_level(levels: list[str]) -> str | None:
    if not levels:
        return None
    ordered = sorted(levels, key=lambda level: LEVEL_RANK.get(level, 99))
    for level in ordered:
        mapped = ADMIN_LEVEL_MAP.get(level)
        if mapped:
            return mapped
    return None


def _should_route_nomis(query_lower: str, level_mentions: list[str]) -> bool:
    if any(re.search(pattern, query_lower) for pattern in NOMIS_PATTERNS):
        return True
    if any(level in {"oa", "lsoa", "msoa"} for level in level_mentions):
        return True
    return False


def _build_interactive_params(query: str, place_name: str | None) -> dict[str, Any]:
    query_lower = query.lower()
    level_mentions = _find_level_mentions(query_lower)
    selection_level = _pick_smallest_level(level_mentions) or "local_auth"
    params: dict[str, Any] = {"level": selection_level}

    focus_level = _pick_largest_level(level_mentions)
    if focus_level == selection_level:
        focus_level = None

    if selection_level in {"oa", "lsoa", "msoa", "ward"} and not focus_level:
        focus_level = "local_auth"

    if place_name:
        if focus_level:
            params["focusName"] = place_name
            params["focusLevel"] = focus_level
        else:
            params["searchTerm"] = place_name

    if re.search(r"\b(compare|multiple|several|list)\b", query_lower):
        params["multiSelect"] = True

    return params


def _should_offer_boundary_explorer(
    query_lower: str, *, level_mentions: list[str], place_name: str | None
) -> bool:
    if not any(re.search(pattern, query_lower) for pattern in BOUNDARY_EXPLORER_HINT_PATTERNS):
        return False
    if level_mentions or place_name:
        return True
    if re.search(r"\bwithin\b|\bin\b", query_lower):
        return True
    return False


def _build_boundary_explorer_params(query: str, place_name: str | None) -> dict[str, Any]:
    query_lower = query.lower()
    level_mentions = _find_level_mentions(query_lower)
    admin_level = _pick_admin_level(level_mentions) or "WARD"
    params: dict[str, Any] = {"level": admin_level}
    if place_name:
        params["searchTerm"] = place_name
    if re.search(r"\buprn(s)?\b", query_lower):
        params["detailLevel"] = "uprn"
    elif re.search(r"\bpostcode(s)?\b", query_lower):
        params["detailLevel"] = "postcode"
    return params


def _detect_feature_collection(query_lower: str) -> str | None:
    for key, collection in FEATURE_COLLECTIONS.items():
        if re.search(rf"\b{re.escape(key)}\b", query_lower):
            return collection
    return None


def _classify_linked_identifier_query(
    query: str,
    query_lower: str,
    identifier: str | None,
    context: dict[str, Any],
) -> tuple[QueryIntent, float, dict[str, Any], dict[str, Any]]:
    resolved_identifier = identifier or _extract_uprn(query) or ""
    context["linked_id"] = resolved_identifier
    if re.search(r"\bproduct version\b|\bcorrelation method\b", query_lower):
        context["linked_mode"] = "product_version_info"
        corr = _extract_correlation_method(query)
        params = {"correlationMethod": corr} if corr else {}
        return QueryIntent.LINKED_IDS, 0.92, params, context
    if re.search(r"\bfeature type\b|\broadlink\b|\broad link\b", query_lower):
        context["linked_mode"] = "feature_types"
        linked_params: dict[str, Any] = {"featureType": "RoadLink"}
        if resolved_identifier:
            linked_params["identifier"] = resolved_identifier
        return QueryIntent.LINKED_IDS, 0.9, linked_params, context
    linked_params = {"identifier": resolved_identifier} if resolved_identifier else {}
    return QueryIntent.LINKED_IDS, 0.9, linked_params, context


def _classify_query(query: str) -> tuple[QueryIntent, float, dict[str, Any], dict[str, Any]]:
    query_lower = query.lower()
    context: dict[str, Any] = {}
    level_mentions = _find_level_mentions(query_lower)
    if level_mentions:
        context["levels"] = level_mentions
    place_name = _extract_place_name(query)

    if re.search(r"\bfetch\b.*\b(mcp geo )?skills guide\b|\bskills guide\b", query_lower):
        context["unknown_mode"] = "skills_resource"
        return QueryIntent.UNKNOWN, 0.92, {"uri": SKILLS_RESOURCE["uri"]}, context
    if re.search(r"\bdescribe\b.*\b(server capabilities|tool search config)\b", query_lower):
        context["unknown_mode"] = "descriptor"
        return QueryIntent.UNKNOWN, 0.92, {}, context
    if re.search(r"\blog\b.*\bui event\b", query_lower):
        context["unknown_mode"] = "log_event"
        return (
            QueryIntent.UNKNOWN,
            0.9,
            {
                "eventType": "ui_event",
                "source": "route_query",
                "payload": {"query": query},
            },
            context,
        )
    if re.search(r"\bboundary cache status\b", query_lower):
        context["unknown_mode"] = "boundary_cache_status"
        return QueryIntent.UNKNOWN, 0.9, {}, context
    if re.search(r"\bsearch\b.*\bboundary cache\b", query_lower):
        context["unknown_mode"] = "boundary_cache_search"
        return QueryIntent.UNKNOWN, 0.9, {"query": place_name or "Westminster", "limit": 5}, context
    if re.search(r"\b(find|search|list|show)\b.*\btools?\b", query_lower):
        context["unknown_mode"] = "descriptor"
        return QueryIntent.UNKNOWN, 0.9, {}, context

    if any(re.search(pattern, query_lower) for pattern in SURVEY_PATTERNS):
        focus = _extract_landscape_focus(query) or place_name
        if focus:
            context["survey_focus"] = focus
        context["survey_intent"] = True
        return (
            QueryIntent.ENVIRONMENTAL_SURVEY,
            0.94,
            {"text": focus or query},
            context,
        )

    if re.search(r"\bstatistics dashboard\b", query_lower):
        return QueryIntent.AREA_COMPARISON, 0.93, {}, context
    if re.search(r"\bboundary explorer\b", query_lower):
        context["interactive_widget"] = "boundary_explorer"
        return (
            QueryIntent.INTERACTIVE_SELECTION,
            0.94,
            _build_boundary_explorer_params(query, place_name),
            context,
        )
    if re.search(
        r"\b(mcp-apps?|ui)\b.*\b(rendering mode|probe)\b|\brendering mode support\b|\bui probe\b",
        query_lower,
    ):
        context["interactive_widget"] = "ui_probe"
        return (
            QueryIntent.INTERACTIVE_SELECTION,
            0.94,
            {"resourceUri": "ui://mcp-geo/statistics-dashboard", "contentMode": "text"},
            context,
        )

    if re.search(r"\bpoints? of interest\b|\bpois?\b", query_lower):
        lat_lon = _extract_lat_lon(query)
        if lat_lon is not None:
            lat, lon = lat_lon
            context["poi_mode"] = "nearest"
            return QueryIntent.POI_LOOKUP, 0.88, {"lat": lat, "lon": lon, "limit": 5}, context
        context["poi_mode"] = "search"
        text_match = re.search(r"\bfor\s+(.+)$", query, re.IGNORECASE)
        poi_text = text_match.group(1).strip() if text_match else query
        return QueryIntent.POI_LOOKUP, 0.88, {"text": poi_text}, context

    if any(re.search(pattern, query_lower) for pattern in DATASET_PATTERNS):
        if "nomis" in query_lower:
            context["nomis_preferred"] = True
        return QueryIntent.DATASET_DISCOVERY, 0.9, {}, context

    area_code = _extract_area_code(query)
    if re.search(r"\bhierarchy\b|\bancestor(s)?\b", query_lower):
        if area_code:
            context["place_mode"] = "reverse_hierarchy"
            return QueryIntent.PLACE_LOOKUP, 0.9, {"id": area_code}, context
        context["place_mode"] = "hierarchy_lookup"
        return QueryIntent.PLACE_LOOKUP, 0.85, {"text": place_name or query}, context

    uprn = _extract_uprn(query)
    if re.search(r"\blinked ids?\b|\blinked identifiers?\b|\bcrosswalk\b", query_lower):
        return _classify_linked_identifier_query(query, query_lower, uprn, context)

    postcode = _extract_postcode(query)
    if postcode:
        if _is_geography_lookup_query(query_lower):
            context["address_mode"] = "postcode_geography"
            params: dict[str, Any] = {"postcode": postcode}
            derivation_mode = _extract_derivation_mode(query_lower)
            if derivation_mode:
                context["derivation_mode"] = derivation_mode
                params["derivationMode"] = derivation_mode
            return QueryIntent.ADDRESS_LOOKUP, 0.95, params, context
        context["address_mode"] = "postcode"
        return QueryIntent.ADDRESS_LOOKUP, 0.95, {"postcode": postcode}, context

    if uprn and "uprn" in query_lower:
        if _is_geography_lookup_query(query_lower):
            context["address_mode"] = "uprn_geography"
            params = {"uprn": uprn}
            derivation_mode = _extract_derivation_mode(query_lower)
            if derivation_mode:
                context["derivation_mode"] = derivation_mode
                params["derivationMode"] = derivation_mode
            return QueryIntent.ADDRESS_LOOKUP, 0.95, params, context
        context["address_mode"] = "uprn"
        return QueryIntent.ADDRESS_LOOKUP, 0.95, {"uprn": uprn}, context

    if any(re.search(pattern, query_lower) for pattern in LINKED_ID_PATTERNS):
        return _classify_linked_identifier_query(query, query_lower, uprn, context)

    if any(re.search(pattern, query_lower) for pattern in VECTOR_TILE_PATTERNS):
        return QueryIntent.VECTOR_TILES, 0.9, {}, context

    if any(re.search(pattern, query_lower) for pattern in MAP_RENDER_PATTERNS):
        return QueryIntent.MAP_RENDER, 0.85, {}, context

    wants_boundary_explorer = _should_offer_boundary_explorer(
        query_lower, level_mentions=level_mentions, place_name=place_name
    )
    if re.search(r"\baddress(es)?\b", query_lower):
        context["address_mode"] = "search"
        return QueryIntent.ADDRESS_LOOKUP, 0.8, {"text": query}, context
    if any(re.search(pattern, query_lower) for pattern in INTERACTIVE_PATTERNS):
        params = (
            _build_boundary_explorer_params(query, place_name)
            if wants_boundary_explorer
            else _build_interactive_params(query, place_name)
        )
        if wants_boundary_explorer:
            context["interactive_widget"] = "boundary_explorer"
        return QueryIntent.INTERACTIVE_SELECTION, 0.9, params, context
    if re.search(r"\b(select|choose|pick)\b", query_lower) and _find_level_mentions(query_lower):
        params = (
            _build_boundary_explorer_params(query, place_name)
            if wants_boundary_explorer
            else _build_interactive_params(query, place_name)
        )
        if wants_boundary_explorer:
            context["interactive_widget"] = "boundary_explorer"
        return QueryIntent.INTERACTIVE_SELECTION, 0.9, params, context

    if _should_route_nomis(query_lower, level_mentions):
        context["nomis_preferred"] = True

    scores = {
        QueryIntent.POI_LOOKUP: _match_patterns(query, POI_PATTERNS),
        QueryIntent.PLACE_LOOKUP: _match_patterns(query, PLACE_LOOKUP_PATTERNS),
        QueryIntent.STATISTICS: _match_patterns(query, STATISTICS_PATTERNS),
        QueryIntent.AREA_COMPARISON: _match_patterns(query, COMPARISON_PATTERNS),
        QueryIntent.FEATURE_SEARCH: _match_patterns(query, FEATURE_SEARCH_PATTERNS),
        QueryIntent.BOUNDARY_FETCH: _match_patterns(query, BOUNDARY_PATTERNS),
        QueryIntent.INTERACTIVE_SELECTION: _match_patterns(query, INTERACTIVE_PATTERNS),
        QueryIntent.ROUTE_PLANNING: _match_patterns(query, ROUTE_PATTERNS),
        QueryIntent.DATASET_DISCOVERY: _match_patterns(query, DATASET_PATTERNS),
    }

    if wants_boundary_explorer:
        context["interactive_widget"] = "boundary_explorer"
        scores[QueryIntent.INTERACTIVE_SELECTION] = max(
            scores[QueryIntent.INTERACTIVE_SELECTION], 0.92
        )
        # If the query looks like "features within a boundary", prefer the boundary explorer UI over
        # raw NGD feature queries to avoid forcing callers to pick collections/bboxes prematurely.
        if (
            scores.get(QueryIntent.FEATURE_SEARCH, 0.0) >= 0.8
            and (level_mentions or scores.get(QueryIntent.BOUNDARY_FETCH, 0.0) >= 0.5)
            and re.search(r"\bwithin\b|\binside\b", query_lower)
        ):
            scores[QueryIntent.FEATURE_SEARCH] = min(scores[QueryIntent.FEATURE_SEARCH], 0.85)

    if re.search(r"\bcompare\b|\bvs\.?\b|\bversus\b", query_lower):
        scores[QueryIntent.AREA_COMPARISON] = max(scores[QueryIntent.AREA_COMPARISON], 0.9)
        scores[QueryIntent.STATISTICS] = min(scores[QueryIntent.STATISTICS], 0.4)

    if re.search(r"\bobservations?\b|\bgdpv\b", query_lower):
        scores[QueryIntent.STATISTICS] = max(scores[QueryIntent.STATISTICS], 0.82)
    if re.search(r"\bcreate\b.*\bfilter\b|\bons\b.*\bfilter\b", query_lower):
        scores[QueryIntent.STATISTICS] = max(scores[QueryIntent.STATISTICS], 0.85)

    feature_collection = _detect_feature_collection(query_lower)
    if feature_collection:
        scores[QueryIntent.FEATURE_SEARCH] = max(scores[QueryIntent.FEATURE_SEARCH], 0.9)
        context["feature_collection"] = feature_collection

    if any(re.search(pattern, query_lower) for pattern in POI_PATTERNS):
        scores[QueryIntent.POI_LOOKUP] = max(scores[QueryIntent.POI_LOOKUP], 0.85)
        lat_lon = _extract_lat_lon(query)
        if re.search(r"\bnearest\b|\bnear\b|\bnearby\b", query_lower):
            scores[QueryIntent.POI_LOOKUP] = max(scores[QueryIntent.POI_LOOKUP], 0.92)
            if lat_lon is not None:
                context["poi_mode"] = "nearest"
        elif "poi_mode" not in context:
            context["poi_mode"] = "search"
        scores[QueryIntent.FEATURE_SEARCH] = min(scores[QueryIntent.FEATURE_SEARCH], 0.75)

    if re.search(r"\broute\b|\bdirections\b|\bfrom\b.*\bto\b", query_lower):
        scores[QueryIntent.ROUTE_PLANNING] = max(scores[QueryIntent.ROUTE_PLANNING], 0.85)

    if re.search(r"\bboundary\b|\bgeojson\b|\bpolygon\b", query_lower):
        scores[QueryIntent.BOUNDARY_FETCH] = max(scores[QueryIntent.BOUNDARY_FETCH], 0.85)

    if re.search(r"\bdatasets?\b", query_lower):
        scores[QueryIntent.DATASET_DISCOVERY] = max(scores[QueryIntent.DATASET_DISCOVERY], 0.85)

    if place_name:
        other_high = any(
            scores[intent] >= 0.5
            for intent in [
                QueryIntent.STATISTICS,
                QueryIntent.AREA_COMPARISON,
                QueryIntent.POI_LOOKUP,
                QueryIntent.FEATURE_SEARCH,
                QueryIntent.BOUNDARY_FETCH,
                QueryIntent.ROUTE_PLANNING,
                QueryIntent.DATASET_DISCOVERY,
            ]
        )
        if not other_high:
            scores[QueryIntent.PLACE_LOOKUP] = max(scores[QueryIntent.PLACE_LOOKUP], 0.8)

    best_intent = max(scores, key=lambda k: scores[k])
    best_score = scores[best_intent]

    if best_score < 0.3:
        return QueryIntent.UNKNOWN, 0.0, {}, context

    recommended_params: dict[str, Any] = {}
    if best_intent == QueryIntent.PLACE_LOOKUP and place_name:
        recommended_params = {"text": place_name}
        admin_level = _pick_admin_level(level_mentions)
        if admin_level:
            recommended_params["level"] = admin_level
    elif best_intent == QueryIntent.POI_LOOKUP:
        recommended_params = {"text": query}
    elif best_intent == QueryIntent.INTERACTIVE_SELECTION:
        recommended_params = (
            _build_boundary_explorer_params(query, place_name)
            if context.get("interactive_widget") == "boundary_explorer"
            else _build_interactive_params(query, place_name)
        )
    elif best_intent == QueryIntent.FEATURE_SEARCH and feature_collection:
        recommended_params = {"collection": feature_collection}
    return best_intent, best_score, recommended_params, context


def _build_survey_plan(focus: str | None) -> list[dict[str, Any]]:
    landscape_name = focus or "Forest of Bowland"
    return [
        {
            "step": 1,
            "goal": "Resolve an authoritative protected-landscape AOI.",
            "tool": "os_landscape.find",
            "parameters": {"text": landscape_name, "limit": 3},
        },
        {
            "step": 2,
            "goal": "Fetch the AOI geometry by id.",
            "tool": "os_landscape.get",
            "parameters": {"id": "<id-from-step-1>", "includeGeometry": True},
        },
        {
            "step": 3,
            "goal": "Build peat evidence paths with direct/proxy separation and caveats.",
            "tool": "os_peat.evidence_paths",
            "parameters": {
                "landscapeId": "<id-from-step-1>",
                "limit": 25,
                "resultType": "hits",
            },
        },
        {
            "step": 4,
            "goal": "Profile hydrology context counts first (no geometry).",
            "tool": "os_features.query",
            "parameters": {
                "collection": "wtr-fts-water-3",
                "bbox": "<aoi-bbox>",
                "resultType": "hits",
                "limit": 25,
                "includeGeometry": False,
                "thinMode": True,
            },
        },
        {
            "step": 5,
            "goal": "Profile habitat proxies counts first (no geometry).",
            "tool": "os_features.query",
            "parameters": {
                "collection": "lnd-fts-land-3",
                "bbox": "<aoi-bbox>",
                "resultType": "hits",
                "limit": 25,
                "includeGeometry": False,
                "thinMode": True,
            },
        },
        {
            "step": 6,
            "goal": "Fetch sampled geometry only after counts are stable.",
            "tool": "os_features.query",
            "parameters": {
                "collection": "lnd-fts-land-3",
                "bbox": "<aoi-bbox>",
                "limit": 25,
                "includeGeometry": True,
                "thinMode": True,
                "delivery": "auto",
            },
        },
    ]


def _get_tool_for_intent(
    intent: QueryIntent, context: dict[str, Any]
) -> tuple[str, list[str], str]:
    if intent == QueryIntent.ADDRESS_LOOKUP:
        mode = context.get("address_mode")
        derivation_mode = str(context.get("derivation_mode") or "")
        if mode == "postcode_geography":
            mode_hint = ""
            if derivation_mode in {"exact", "best_fit"}:
                mode_hint = f" using derivationMode={derivation_mode}"
            return (
                "ons_geo.by_postcode",
                ["ons_geo.by_postcode", "ons_geo.cache_status"],
                (
                    "Lookup all ONS geographies for a postcode from local ONSPD/NSPL cache"
                    f"{mode_hint}."
                ),
            )
        if mode == "uprn_geography":
            mode_hint = ""
            if derivation_mode in {"exact", "best_fit"}:
                mode_hint = f" using derivationMode={derivation_mode}"
            return (
                "ons_geo.by_uprn",
                ["ons_geo.by_uprn", "ons_geo.cache_status"],
                (
                    "Lookup all ONS geographies for a UPRN from local ONSUD/NSUL cache"
                    f"{mode_hint}."
                ),
            )
        if mode == "uprn":
            return (
                "os_places.by_uprn",
                ["os_places.by_uprn"],
                "Lookup a specific address by UPRN using OS Places.",
            )
        if mode == "postcode":
            return (
                "os_places.by_postcode",
                ["os_places.by_postcode"],
                "Lookup addresses and UPRNs for a postcode using OS Places.",
            )
        return (
            "os_places.search",
            ["os_places.search"],
            "Free-text address search using OS Places.",
        )
    if intent == QueryIntent.POI_LOOKUP:
        poi_mode = str(context.get("poi_mode") or context.get("place_mode") or "")
        if poi_mode == "nearest":
            return (
                "os_poi.nearest",
                ["os_poi.nearest"],
                "Find nearest OS points of interest to a coordinate.",
            )
        return (
            "os_poi.search",
            ["os_poi.search", "os_poi.nearest", "os_poi.within"],
            "Search OS Points of Interest for amenities and nearby services.",
        )
    if intent == QueryIntent.LINKED_IDS:
        linked_mode = str(context.get("linked_mode") or "")
        if linked_mode == "product_version_info":
            return (
                "os_linked_ids.product_version_info",
                ["os_linked_ids.product_version_info"],
                "Resolve linked-identifiers product version details for a correlation method.",
            )
        if linked_mode == "feature_types":
            return (
                "os_linked_ids.feature_types",
                ["os_linked_ids.feature_types", "os_linked_ids.identifiers"],
                "Resolve linked identifiers for a feature type identifier.",
            )
        return (
            "os_linked_ids.get",
            ["os_linked_ids.get", "os_linked_ids.identifiers"],
            "Resolve linked identifiers (UPRN/USRN/TOID) for an entity.",
        )
    if intent == QueryIntent.PLACE_LOOKUP:
        place_mode = str(context.get("place_mode") or "")
        if place_mode == "reverse_hierarchy":
            return (
                "admin_lookup.reverse_hierarchy",
                ["admin_lookup.reverse_hierarchy"],
                "Resolve the administrative hierarchy for a known area code.",
            )
        if place_mode == "hierarchy_lookup":
            return (
                "admin_lookup.find_by_name",
                ["admin_lookup.find_by_name", "admin_lookup.reverse_hierarchy"],
                "Resolve area code by name, then call reverse hierarchy with the selected id.",
            )
        if place_mode == "poi_nearest":
            return (
                "os_poi.nearest",
                ["os_poi.nearest"],
                "Find nearest OS points of interest to a coordinate.",
            )
        if place_mode == "poi_search":
            return (
                "os_poi.search",
                ["os_poi.search", "os_poi.within"],
                "Search OS points of interest by text.",
            )
        return (
            "admin_lookup.find_by_name",
            ["admin_lookup.find_by_name"],
            "Find administrative areas by name using admin_lookup.find_by_name.",
        )
    if intent == QueryIntent.BOUNDARY_FETCH:
        return (
            "admin_lookup.area_geometry",
            ["admin_lookup.find_by_name", "admin_lookup.area_geometry"],
            "Get a bounding box for an administrative area.",
        )
    if intent == QueryIntent.FEATURE_SEARCH:
        return (
            "os_features.query",
            ["os_features.query"],
            "Query OS NGD feature collections by bbox and collection.",
        )
    if intent == QueryIntent.ENVIRONMENTAL_SURVEY:
        return (
            "os_landscape.find",
            [
                "os_landscape.find",
                "os_landscape.get",
                "os_peat.evidence_paths",
                "os_features.query",
            ],
            (
                "Run an AOI-first environmental survey flow: resolve "
                "protected-landscape boundary, derive peat evidence paths "
                "(direct + proxy), profile counts, then fetch bounded geometry."
            ),
        )
    if intent == QueryIntent.STATISTICS:
        if context.get("nomis_preferred"):
            return (
                "nomis.query",
                ["nomis.query", "nomis.datasets", "nomis.concepts"],
                (
                    "Query NOMIS labour/census statistics directly. "
                    "If dataset id is unknown, use nomis.datasets with q and limit. "
                    "See resource://mcp-geo/nomis-workflows for dataset-specific workflow profiles."
                ),
            )
        return (
            "ons_data.query",
            ["ons_data.dimensions", "ons_data.query"],
            "Query ONS observations; use dimensions to discover valid filters.",
        )
    if intent == QueryIntent.AREA_COMPARISON:
        return (
            "os_apps.render_statistics_dashboard",
            ["os_apps.render_statistics_dashboard", "ons_data.query"],
            "Open the statistics dashboard to compare multiple areas.",
        )
    if intent == QueryIntent.INTERACTIVE_SELECTION:
        if context.get("interactive_widget") == "ui_probe":
            return (
                "os_apps.render_ui_probe",
                ["os_apps.render_ui_probe"],
                "Probe MCP-Apps UI rendering mode support in the current host.",
            )
        if context.get("interactive_widget") == "boundary_explorer":
            return (
                "os_apps.render_boundary_explorer",
                ["os_apps.render_boundary_explorer"],
                (
                    "Open the boundary explorer to select boundaries and build "
                    "map inventories (UPRNs/buildings/links)."
                ),
            )
        return (
            "os_apps.render_geography_selector",
            ["os_apps.render_geography_selector"],
            "Open an interactive map to select geographic areas.",
        )
    if intent == QueryIntent.ROUTE_PLANNING:
        return (
            "os_apps.render_route_planner",
            ["os_apps.render_route_planner"],
            "Open the route planner to choose start/end points.",
        )
    if intent == QueryIntent.DATASET_DISCOVERY:
        if context.get("nomis_preferred"):
            return (
                "nomis.datasets",
                ["nomis.datasets", "nomis.codelists"],
                (
                    "List NOMIS datasets with q+limit, then inspect code lists if needed. "
                    "See resource://mcp-geo/nomis-workflows for workflow templates."
                ),
            )
        return (
            "ons_select.search",
            ["ons_select.search", "ons_data.dimensions"],
            "Rank ONS datasets with explainability, then inspect dimensions before querying.",
        )
    if intent == QueryIntent.MAP_RENDER:
        return (
            "os_maps.render",
            ["os_maps.render"],
            "Return a static map descriptor for a bounding box.",
        )
    if intent == QueryIntent.VECTOR_TILES:
        return (
            "os_vector_tiles.descriptor",
            ["os_vector_tiles.descriptor"],
            "Return OS vector tiles style and template URLs.",
        )
    unknown_mode = str(context.get("unknown_mode") or "")
    if unknown_mode == "skills_resource":
        return (
            "resources/read",
            ["resources/read"],
            "Read the MCP Geo skills guide resource.",
        )
    if unknown_mode == "descriptor":
        return (
            "os_mcp.descriptor",
            ["os_mcp.descriptor"],
            "Describe server capabilities and tool-search configuration.",
        )
    if unknown_mode == "log_event":
        return (
            "os_apps.log_event",
            ["os_apps.log_event"],
            "Record a UI event payload for analytics and host diagnostics.",
        )
    if unknown_mode == "boundary_cache_status":
        return (
            "admin_lookup.get_cache_status",
            ["admin_lookup.get_cache_status"],
            "Return boundary cache maturity and staleness status.",
        )
    if unknown_mode == "boundary_cache_search":
        return (
            "admin_lookup.search_cache",
            ["admin_lookup.search_cache"],
            "Search boundary cache entries by name.",
        )
    return (
        "os_mcp.descriptor",
        ["os_mcp.descriptor"],
        "Use the server descriptor to discover tool search defaults.",
    )


def _get_alternative_tools(intent: QueryIntent) -> list[str]:
    alternatives = {
        QueryIntent.ADDRESS_LOOKUP: [
            "ons_geo.by_postcode",
            "ons_geo.by_uprn",
            "os_places.search",
            "os_places.nearest",
        ],
        QueryIntent.POI_LOOKUP: ["os_poi.nearest", "os_poi.within", "os_places.search"],
        QueryIntent.LINKED_IDS: [
            "os_linked_ids.identifiers",
            "os_linked_ids.feature_types",
            "os_linked_ids.product_version_info",
            "os_places.by_uprn",
        ],
        QueryIntent.PLACE_LOOKUP: ["admin_lookup.area_geometry", "os_names.find", "os_poi.search"],
        QueryIntent.BOUNDARY_FETCH: ["resources/read"],
        QueryIntent.FEATURE_SEARCH: ["os_names.find", "os_vector_tiles.descriptor"],
        QueryIntent.ENVIRONMENTAL_SURVEY: [
            "os_landscape.get",
            "os_peat.layers",
            "os_peat.evidence_paths",
            "os_features.collections",
            "admin_lookup.find_by_name",
        ],
        QueryIntent.STATISTICS: ["ons_data.dimensions", "ons_select.search", "nomis.query"],
        QueryIntent.AREA_COMPARISON: ["ons_data.query"],
        QueryIntent.INTERACTIVE_SELECTION: [
            "os_apps.render_boundary_explorer",
            "os_apps.render_ui_probe",
            "admin_lookup.find_by_name",
        ],
        QueryIntent.ROUTE_PLANNING: ["os_maps.render"],
        QueryIntent.DATASET_DISCOVERY: ["ons_select.search", "ons_search.query", "nomis.datasets"],
        QueryIntent.MAP_RENDER: ["os_vector_tiles.descriptor"],
        QueryIntent.VECTOR_TILES: ["os_maps.render"],
        QueryIntent.UNKNOWN: ["os_mcp.descriptor", "admin_lookup.find_by_name"],
    }
    return alternatives.get(intent, [])


def _get_guidance_for_intent(intent: QueryIntent) -> str:
    guidance = {
        QueryIntent.ADDRESS_LOOKUP: (
            "Use OS Places for address retrieval and free-text address search. "
            "Use ons_geo.by_postcode / ons_geo.by_uprn when you need full geography "
            "mappings for postcode/UPRN with exact (ONSPD/ONSUD) or best_fit "
            "(NSPL/NSUL) derivation modes."
        ),
        QueryIntent.POI_LOOKUP: (
            "Use os_poi.search/nearest/within for amenities and points of interest. "
            "Use nearest for a point lookup and within for bbox-constrained queries."
        ),
        QueryIntent.LINKED_IDS: (
            "Use os_linked_ids.get for identifier type lookups, "
            "os_linked_ids.identifiers for generic identifier crosswalks, "
            "os_linked_ids.feature_types for feature-type identifiers, and "
            "os_linked_ids.product_version_info for correlation method "
            "version checks."
        ),
        QueryIntent.PLACE_LOOKUP: (
            "Use admin_lookup.find_by_name for administrative areas, "
            "and pass level/levels (WARD/DISTRICT/etc) to reduce noisy matches."
        ),
        QueryIntent.BOUNDARY_FETCH: (
            "Find the area id first, then call admin_lookup.area_geometry for a bbox summary."
        ),
        QueryIntent.FEATURE_SEARCH: (
            "Use os_features.query with a collection and bbox. Collections map to NGD feature sets."
        ),
        QueryIntent.ENVIRONMENTAL_SURVEY: (
            "Use AOI-first sequencing: os_landscape.find -> os_landscape.get -> "
            "os_peat.evidence_paths -> os_features.query (hits/thin/geometry-last). "
            "This separates direct peat evidence sources from proxy indicators and "
            "reduces large-response risk."
        ),
        QueryIntent.STATISTICS: (
            "Use NOMIS for labour/census or deep local geographies; otherwise use ONS datasets. "
            "Prefer nomis.query directly when dataset is known. If you need discovery, call "
            "nomis.datasets with q and limit to avoid large payloads. ONS flow: "
            "ons_data.dimensions to find filters, then ons_data.query for observations. "
            "NOMIS workflow profiles are available at resource://mcp-geo/nomis-workflows."
        ),
        QueryIntent.AREA_COMPARISON: (
            "Use the statistics dashboard to compare multiple areas, or query per area and compare."
        ),
        QueryIntent.INTERACTIVE_SELECTION: (
            "Use MCP-Apps UI to collect the area of interest and progressive "
            "detail preferences. Prefer the boundary explorer when users ask "
            "for UPRNs/buildings/road/path links inside a boundary."
        ),
        QueryIntent.ROUTE_PLANNING: (
            "Use the route planner widget to set start/end coordinates."
        ),
        QueryIntent.DATASET_DISCOVERY: (
            "Use ons_select.search for ranked ONS dataset discovery (with explanations), or "
            "ons_search.query for raw live search; "
            "nomis.datasets with q and limit for labour/census. "
            "NOMIS workflow profiles are available at resource://mcp-geo/nomis-workflows."
        ),
        QueryIntent.MAP_RENDER: (
            "Use os_maps.render with a bbox to obtain a static map URL template."
        ),
        QueryIntent.VECTOR_TILES: (
            "Use os_vector_tiles.descriptor for tile/style templates; inject "
            "OS_API_KEY client-side."
        ),
        QueryIntent.UNKNOWN: (
            "Intent unclear. Use os_mcp.descriptor for tool discovery or be more specific."
        ),
    }
    return guidance.get(intent, guidance[QueryIntent.UNKNOWN])


def _compact_toolset_catalog() -> dict[str, dict[str, Any]]:
    raw_catalog = get_toolset_catalog()
    compact: dict[str, dict[str, Any]] = {}
    for name, details in raw_catalog.items():
        compact[name] = {
            "count": details.get("count", 0),
            "patterns": details.get("patterns", []),
        }
    return compact


def _infer_toolsets_from_query(query: str) -> tuple[list[str], dict[str, Any]]:
    intent, _confidence, _params, context = _classify_query(query)
    recommended = list(INTENT_TOOLSET_MAP.get(intent, ["starter"]))
    if intent in {QueryIntent.STATISTICS, QueryIntent.DATASET_DISCOVERY}:
        if context.get("nomis_preferred"):
            recommended = ["core_router", "nomis_data"]
        else:
            recommended = ["core_router", "ons_selection", "ons_data"]
    return recommended, {
        "intent": intent.value,
        "nomisPreferred": bool(context.get("nomis_preferred")),
    }


def _select_toolsets(payload: dict[str, Any]) -> ToolResult:
    """Resolve toolset filters and return compact discovery guidance.

    Request schema:
    {
      "type": "object",
      "properties": {
        "query": {"type": "string"},
        "toolset": {"type": "string"},
        "includeToolsets": {"type": ["array", "string"]},
        "excludeToolsets": {"type": ["array", "string"]},
        "maxTools": {"type": "integer"}
      },
      "required": []
    }
    """
    query = payload.get("query")
    if query is not None and not isinstance(query, str):
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "query must be a string when provided",
        }
    query = query.strip() if isinstance(query, str) else ""
    toolset = payload.get("toolset")
    if toolset is not None and not isinstance(toolset, str):
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "toolset must be a string when provided",
        }
    max_tools = payload.get("maxTools", 20)
    if not isinstance(max_tools, int) or max_tools < 1 or max_tools > 200:
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "maxTools must be an integer between 1 and 200",
        }
    try:
        include_toolsets = parse_toolset_list(payload.get("includeToolsets"))
        exclude_toolsets = parse_toolset_list(payload.get("excludeToolsets"))
    except ValueError as exc:
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": str(exc),
        }

    inferred: list[str] = []
    inference_context: dict[str, Any] = {}
    if query and not toolset and not include_toolsets:
        inferred, inference_context = _infer_toolsets_from_query(query)
        include_toolsets = inferred

    toolset, include_toolsets, exclude_toolsets = apply_default_toolset_filters(
        toolset=toolset,
        include_toolsets=include_toolsets,
        exclude_toolsets=exclude_toolsets,
    )
    names = sorted(tool.name for tool in all_tools())
    try:
        filtered_names = filter_tool_names_by_toolsets(
            names,
            toolset=toolset,
            include_toolsets=include_toolsets,
            exclude_toolsets=exclude_toolsets,
        )
    except ValueError as exc:
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": str(exc),
        }
    list_tools_params: dict[str, Any] = {}
    if toolset:
        list_tools_params["toolset"] = toolset
    if include_toolsets:
        list_tools_params["includeToolsets"] = include_toolsets
    if exclude_toolsets:
        list_tools_params["excludeToolsets"] = exclude_toolsets
    notes: list[str] = []
    if inferred:
        notes.append("Applied query-based toolset inference.")
    if not list_tools_params:
        notes.append("No filters selected; all tools remain discoverable.")
    return 200, {
        "query": query or None,
        "inference": inference_context or None,
        "inferredIncludeToolsets": inferred,
        "effectiveFilters": list_tools_params,
        "listToolsParams": list_tools_params,
        "matchedToolCount": len(filtered_names),
        "matchedTools": filtered_names[:max_tools],
        "toolsets": _compact_toolset_catalog(),
        "notes": notes,
    }


def _descriptor(payload: dict[str, Any]) -> ToolResult:
    """Describe server capabilities and tool search configuration.

    Request schema:
    {
      "type": "object",
      "properties": {
        "category": {"type": "string"},
        "includeTools": {"type": "boolean"}
      },
      "required": []
    }

    Response schema:
    {
      "type": "object",
      "properties": {
        "server": {"type": "string"},
        "version": {"type": "string"},
        "protocolVersion": {"type": "string"},
        "supportedProtocolVersions": {"type": "array"},
        "mcpAppsProtocolVersion": {"type": "string"},
        "transport": {"type": "string"},
        "capabilities": {"type": "object"},
        "toolSearch": {"type": "object"},
        "skillsUri": {"type": "string"}
      },
      "required": ["server", "version", "protocolVersion", "toolSearch"]
    }
    """
    category = payload.get("category")
    include_tools = payload.get("includeTools", True)
    if category is not None and not isinstance(category, str):
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "category must be a string when provided",
        }
    if include_tools is not None and not isinstance(include_tools, bool):
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "includeTools must be a boolean when provided",
        }
    tool_search = get_tool_search_config(category if include_tools else None)
    return 200, {
        "server": "mcp-geo",
        "version": SERVER_VERSION,
        "protocolVersion": PROTOCOL_VERSION,
        "supportedProtocolVersions": list(SUPPORTED_PROTOCOL_VERSIONS),
        "mcpAppsProtocolVersion": MCP_APPS_PROTOCOL_VERSION,
        "capabilities": {
            "toolSearch": True,
            "skills": True,
            "extensions": {"io.modelcontextprotocol/ui": {"mimeTypes": [MCP_APPS_MIME]}},
        },
        "toolSearch": tool_search,
        "skillsUri": SKILLS_RESOURCE["uri"],
    }


def _route_query(payload: dict[str, Any]) -> ToolResult:
    """Classify a natural language query and recommend the right tool.

    Request schema:
    {
      "type": "object",
      "properties": {
        "query": {"type": "string"}
      },
      "required": ["query"]
    }

    Response schema:
    {
      "type": "object",
      "properties": {
        "query": {"type": "string"},
        "intent": {"type": "string"},
        "confidence": {"type": "number"},
        "recommended_tool": {"type": "string"},
        "recommended_parameters": {"type": "object"},
        "explanation": {"type": "string"},
        "workflow_steps": {"type": "array"},
        "alternative_tools": {"type": "array"},
        "guidance": {"type": "string"},
        "surveyPlan": {"type": "array"}
      },
      "required": ["intent", "confidence", "recommended_tool", "workflow_steps"]
    }
    """
    query = payload.get("query")
    if not isinstance(query, str) or not query.strip():
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "query must be a non-empty string",
        }
    query = query.strip()
    intent, confidence, params, context = _classify_query(query)
    tool, workflow, explanation = _get_tool_for_intent(intent, context)
    workflow_profile_uri = (
        NOMIS_WORKFLOW_URI
        if (tool.startswith("nomis.") or bool(context.get("nomis_preferred")))
        else None
    )
    response: dict[str, Any] = {
        "query": query,
        "intent": intent.value,
        "confidence": round(confidence, 2),
        "recommended_tool": tool,
        "recommended_parameters": params,
        "explanation": explanation,
        "workflow_steps": workflow,
        "alternative_tools": _get_alternative_tools(intent),
        "guidance": _get_guidance_for_intent(intent),
        "workflow_profile_uri": workflow_profile_uri,
    }
    if intent == QueryIntent.ENVIRONMENTAL_SURVEY:
        focus_raw = context.get("survey_focus")
        focus = focus_raw if isinstance(focus_raw, str) else None
        response["surveyPlan"] = _build_survey_plan(focus)
    return 200, response


def _stats_routing(payload: dict[str, Any]) -> ToolResult:
    """Explain whether statistics queries route to ONS or NOMIS.

    Request schema:
    {
      "type": "object",
      "properties": {
        "query": {"type": "string"}
      },
      "required": ["query"]
    }

    Response schema:
    {
      "type": "object",
      "properties": {
        "query": {"type": "string"},
        "provider": {"type": "string"},
        "nomisPreferred": {"type": "boolean"},
        "reasons": {"type": "array"},
        "matchedPatterns": {"type": "array"},
        "matchedLevels": {"type": "array"},
        "recommendedTool": {"type": "string"},
        "comparisonRecommended": {"type": "boolean"},
        "nextSteps": {"type": "array"},
        "notes": {"type": "array"}
      },
      "required": ["provider", "nomisPreferred", "reasons", "recommendedTool"]
    }
    """
    query = payload.get("query")
    if not isinstance(query, str) or not query.strip():
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "query must be a non-empty string",
        }
    comparison_level = payload.get("comparisonLevel")
    if comparison_level is not None:
        if not isinstance(comparison_level, str):
            return 400, {
                "isError": True,
                "code": "INVALID_INPUT",
                "message": "comparisonLevel must be a string",
            }
        comparison_level = comparison_level.strip().upper()
        if comparison_level not in {"WARD", "LSOA", "MSOA"}:
            return 400, {
                "isError": True,
                "code": "INVALID_INPUT",
                "message": "comparisonLevel must be one of WARD, LSOA, MSOA",
            }
    provider_preference = payload.get("providerPreference", "AUTO")
    if not isinstance(provider_preference, str):
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "providerPreference must be a string",
        }
    provider_preference = provider_preference.strip().upper()
    if provider_preference not in {"AUTO", "NOMIS", "ONS"}:
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "providerPreference must be one of AUTO, NOMIS, ONS",
        }
    query = query.strip()
    query_lower = query.lower()
    level_mentions = _find_level_mentions(query_lower)
    details = _build_stats_routing_explanation(query_lower, level_mentions)
    if provider_preference == "NOMIS":
        details["provider"] = "nomis"
        details["nomisPreferred"] = True
        details["reasons"] = [*details["reasons"], "User selected NOMIS provider preference."]
    elif provider_preference == "ONS":
        details["provider"] = "ons"
        details["nomisPreferred"] = False
        details["reasons"] = [*details["reasons"], "User selected ONS provider preference."]
    recommended_tool = "nomis.query" if details["nomisPreferred"] else "ons_data.query"
    comparison = any(re.search(pattern, query_lower) for pattern in COMPARISON_PATTERNS) or (
        " between " in query_lower
    )
    next_steps: list[dict[str, Any]] = []
    notes: list[str] = []
    if comparison:
        selected_level = comparison_level or "WARD"
        next_steps.append({
            "tool": "admin_lookup.find_by_name",
            "note": f"Use level={selected_level} to target specific comparison areas.",
        })
        next_steps.append({
            "tool": "os_apps.render_statistics_dashboard",
            "note": "Use the dashboard for multi-area comparisons.",
        })
        notes.append(
            "If both locations fall under the same local authority, ONS datasets may not "
            "differentiate them."
        )
        next_steps.append({
            "tool": "nomis.query" if details["nomisPreferred"] else "ons_data.query",
            "note": (
                "Run direct area comparison queries after selecting area codes "
                "(avoid unfiltered dataset listing calls)."
            ),
        })
    if details["nomisPreferred"]:
        notes.append("NOMIS is best for labour/census and small-area (OA/LSOA/MSOA) stats.")
        notes.append(
            "If dataset discovery is needed, call nomis.datasets with q and limit "
            "(for example q='employment', limit=10)."
        )
    return 200, {
        "query": query,
        "provider": details["provider"],
        "nomisPreferred": details["nomisPreferred"],
        "userSelections": {
            "comparisonLevel": comparison_level,
            "providerPreference": provider_preference,
        },
        "reasons": details["reasons"],
        "matchedPatterns": details["matchedPatterns"],
        "matchedLevels": details["matchedLevels"],
        "recommendedTool": recommended_tool,
        "comparisonRecommended": comparison,
        "nextSteps": next_steps,
        "notes": notes,
    }


register(
    Tool(
        name="os_mcp.descriptor",
        description="Describe server capabilities and tool search configuration.",
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "os_mcp.descriptor"},
                "category": {
                    "type": "string",
                    "description": "Optional tool category to filter search config.",
                },
                "includeTools": {
                    "type": "boolean",
                    "description": "Include per-tool metadata in toolSearch section.",
                    "default": True,
                },
            },
            "required": [],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "server": {"type": "string"},
                "version": {"type": "string"},
                "protocolVersion": {"type": "string"},
                "supportedProtocolVersions": {"type": "array", "items": {"type": "string"}},
                "mcpAppsProtocolVersion": {"type": "string"},
                "transport": {"type": "string"},
                "capabilities": {"type": "object"},
                "toolSearch": {"type": "object"},
                "skillsUri": {"type": "string"},
            },
            "required": ["server", "version", "protocolVersion", "toolSearch"],
        },
        handler=_descriptor,
    )
)

register(
    Tool(
        name="os_mcp.route_query",
        description="Classify a query and recommend the right tool/workflow.",
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "os_mcp.route_query"},
                "query": {"type": "string"},
            },
            "required": ["query"],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "intent": {"type": "string"},
                "confidence": {"type": "number"},
                "recommended_tool": {"type": "string"},
                "recommended_parameters": {"type": "object"},
                "explanation": {"type": "string"},
                "workflow_steps": {"type": "array"},
                "alternative_tools": {"type": "array"},
                "guidance": {"type": "string"},
                "workflow_profile_uri": {"type": ["string", "null"]},
            },
            "required": ["intent", "confidence", "recommended_tool", "workflow_steps"],
        },
        handler=_route_query,
    )
)

register(
    Tool(
        name="os_mcp.stats_routing",
        description="Explain whether stats queries route to ONS or NOMIS.",
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "os_mcp.stats_routing"},
                "query": {"type": "string"},
                "comparisonLevel": {"type": "string", "enum": ["WARD", "LSOA", "MSOA"]},
                "providerPreference": {"type": "string", "enum": ["AUTO", "NOMIS", "ONS"]},
            },
            "required": ["query"],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "provider": {"type": "string"},
                "nomisPreferred": {"type": "boolean"},
                "userSelections": {"type": "object"},
                "reasons": {"type": "array"},
                "matchedPatterns": {"type": "array"},
                "matchedLevels": {"type": "array"},
                "recommendedTool": {"type": "string"},
                "comparisonRecommended": {"type": "boolean"},
                "nextSteps": {"type": "array"},
                "notes": {"type": "array"},
            },
            "required": ["provider", "nomisPreferred", "reasons", "recommendedTool"],
        },
        handler=_stats_routing,
    )
)

register(
    Tool(
        name="os_mcp.select_toolsets",
        description="Select discovery toolsets and return tools/list filter guidance.",
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "os_mcp.select_toolsets"},
                "query": {
                    "type": "string",
                    "description": "Optional natural-language query used to infer toolsets.",
                },
                "toolset": {
                    "type": "string",
                    "description": "Single named toolset shortcut (for tools/list toolset param).",
                },
                "includeToolsets": {
                    "type": ["array", "string"],
                    "description": "Toolsets to include (array or comma-separated string).",
                },
                "excludeToolsets": {
                    "type": ["array", "string"],
                    "description": "Toolsets to exclude (array or comma-separated string).",
                },
                "maxTools": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 200,
                    "default": 20,
                },
            },
            "required": [],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "query": {"type": ["string", "null"]},
                "inference": {"type": ["object", "null"]},
                "inferredIncludeToolsets": {"type": "array", "items": {"type": "string"}},
                "effectiveFilters": {"type": "object"},
                "listToolsParams": {"type": "object"},
                "matchedToolCount": {"type": "integer"},
                "matchedTools": {"type": "array", "items": {"type": "string"}},
                "toolsets": {"type": "object"},
                "notes": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["effectiveFilters", "matchedToolCount", "matchedTools", "toolsets"],
        },
        handler=_select_toolsets,
    )
)
