from __future__ import annotations

import re
from enum import Enum
from typing import Any

from server import __version__ as SERVER_VERSION
from server.protocol import PROTOCOL_VERSION
from server.mcp.resource_catalog import MCP_APPS_MIME, SKILLS_RESOURCE
from server.mcp.tool_search import get_tool_search_config
from tools.registry import Tool, ToolResult, register


class QueryIntent(str, Enum):
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
        r"\b(buildings?|roads?|streets?|railway|station|cinema|school|hospital|park|shop|"
        r"restaurant|pub|church|museum|library|hotel)\b"
    ),
    r"\bfeatures?\b",
    r"\bngd\b",
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
]

LINKED_ID_PATTERNS = [
    r"\buprn\b",
    r"\busrn\b",
    r"\btoid\b",
    r"\blinked id\b",
]

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
    stop_words = {"find", "search", "get", "show", "where", "what", "the"}
    for word in words:
        tokens = word.split()
        if tokens and tokens[0].lower() in stop_words:
            if len(tokens) > 1:
                return " ".join(tokens[1:])
            continue
        if word.lower() not in stop_words:
            return word
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


def _detect_feature_collection(query_lower: str) -> str | None:
    for key, collection in FEATURE_COLLECTIONS.items():
        if re.search(rf"\b{re.escape(key)}\b", query_lower):
            return collection
    return None


def _classify_query(query: str) -> tuple[QueryIntent, float, dict[str, Any], dict[str, Any]]:
    query_lower = query.lower()
    context: dict[str, Any] = {}
    level_mentions = _find_level_mentions(query_lower)
    if level_mentions:
        context["levels"] = level_mentions

    postcode = _extract_postcode(query)
    if postcode:
        context["address_mode"] = "postcode"
        return QueryIntent.ADDRESS_LOOKUP, 0.95, {"postcode": postcode}, context

    uprn = _extract_uprn(query)
    if uprn and "uprn" in query_lower:
        context["address_mode"] = "uprn"
        return QueryIntent.ADDRESS_LOOKUP, 0.95, {"uprn": uprn}, context

    if any(re.search(pattern, query_lower) for pattern in LINKED_ID_PATTERNS):
        identifier = uprn or _extract_uprn(query) or ""
        context["linked_id"] = identifier
        return QueryIntent.LINKED_IDS, 0.9, {"identifier": identifier} if identifier else {}, context

    if any(re.search(pattern, query_lower) for pattern in VECTOR_TILE_PATTERNS):
        return QueryIntent.VECTOR_TILES, 0.9, {}, context

    if any(re.search(pattern, query_lower) for pattern in MAP_RENDER_PATTERNS):
        return QueryIntent.MAP_RENDER, 0.85, {}, context

    place_name = _extract_place_name(query)
    if re.search(r"\baddress(es)?\b", query_lower):
        context["address_mode"] = "search"
        return QueryIntent.ADDRESS_LOOKUP, 0.8, {"text": query}, context
    if any(re.search(pattern, query_lower) for pattern in INTERACTIVE_PATTERNS):
        params = _build_interactive_params(query, place_name)
        return QueryIntent.INTERACTIVE_SELECTION, 0.9, params, context
    if re.search(r"\b(select|choose|pick)\b", query_lower) and _find_level_mentions(query_lower):
        params = _build_interactive_params(query, place_name)
        return QueryIntent.INTERACTIVE_SELECTION, 0.9, params, context

    if _should_route_nomis(query_lower, level_mentions):
        context["nomis_preferred"] = True

    scores = {
        QueryIntent.PLACE_LOOKUP: _match_patterns(query, PLACE_LOOKUP_PATTERNS),
        QueryIntent.STATISTICS: _match_patterns(query, STATISTICS_PATTERNS),
        QueryIntent.AREA_COMPARISON: _match_patterns(query, COMPARISON_PATTERNS),
        QueryIntent.FEATURE_SEARCH: _match_patterns(query, FEATURE_SEARCH_PATTERNS),
        QueryIntent.BOUNDARY_FETCH: _match_patterns(query, BOUNDARY_PATTERNS),
        QueryIntent.ROUTE_PLANNING: _match_patterns(query, ROUTE_PATTERNS),
        QueryIntent.DATASET_DISCOVERY: _match_patterns(query, DATASET_PATTERNS),
    }

    if re.search(r"\bcompare\b|\bvs\.?\b|\bversus\b", query_lower):
        scores[QueryIntent.AREA_COMPARISON] = max(scores[QueryIntent.AREA_COMPARISON], 0.9)
        scores[QueryIntent.STATISTICS] = min(scores[QueryIntent.STATISTICS], 0.4)

    feature_collection = _detect_feature_collection(query_lower)
    if feature_collection:
        scores[QueryIntent.FEATURE_SEARCH] = max(scores[QueryIntent.FEATURE_SEARCH], 0.9)
        context["feature_collection"] = feature_collection

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

    params: dict[str, Any] = {}
    if best_intent == QueryIntent.PLACE_LOOKUP and place_name:
        params = {"text": place_name}
        admin_level = _pick_admin_level(level_mentions)
        if admin_level:
            params["level"] = admin_level
    elif best_intent == QueryIntent.INTERACTIVE_SELECTION:
        params = _build_interactive_params(query, place_name)
    elif best_intent == QueryIntent.FEATURE_SEARCH and feature_collection:
        params = {"collection": feature_collection}
    return best_intent, best_score, params, context


def _get_tool_for_intent(intent: QueryIntent, context: dict[str, Any]) -> tuple[str, list[str], str]:
    if intent == QueryIntent.ADDRESS_LOOKUP:
        mode = context.get("address_mode")
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
    if intent == QueryIntent.LINKED_IDS:
        return (
            "os_linked_ids.get",
            ["os_linked_ids.get"],
            "Resolve linked identifiers (UPRN/USRN/TOID) for an entity.",
        )
    if intent == QueryIntent.PLACE_LOOKUP:
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
    if intent == QueryIntent.STATISTICS:
        if context.get("nomis_preferred"):
            return (
                "nomis.query",
                ["nomis.query", "nomis.datasets", "nomis.concepts"],
                (
                    "Query NOMIS labour/census statistics directly. "
                    "If dataset id is unknown, use nomis.datasets with q and limit."
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
                "List NOMIS datasets with q+limit, then inspect code lists if needed.",
            )
        return (
            "ons_data.dimensions",
            ["ons_data.dimensions", "ons_search.query"],
            "List ONS dimensions and search available codes.",
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
    return (
        "os_mcp.descriptor",
        ["os_mcp.descriptor"],
        "Use the server descriptor to discover tool search defaults.",
    )


def _get_alternative_tools(intent: QueryIntent) -> list[str]:
    alternatives = {
        QueryIntent.ADDRESS_LOOKUP: ["os_places.search", "os_places.nearest"],
        QueryIntent.LINKED_IDS: ["os_places.by_uprn"],
        QueryIntent.PLACE_LOOKUP: ["admin_lookup.area_geometry", "os_names.find"],
        QueryIntent.BOUNDARY_FETCH: ["resources/read"],
        QueryIntent.FEATURE_SEARCH: ["os_names.find", "os_vector_tiles.descriptor"],
        QueryIntent.STATISTICS: ["ons_data.dimensions", "ons_search.query", "nomis.query"],
        QueryIntent.AREA_COMPARISON: ["ons_data.query"],
        QueryIntent.INTERACTIVE_SELECTION: ["admin_lookup.find_by_name"],
        QueryIntent.ROUTE_PLANNING: ["os_maps.render"],
        QueryIntent.DATASET_DISCOVERY: ["ons_search.query", "nomis.datasets"],
        QueryIntent.MAP_RENDER: ["os_vector_tiles.descriptor"],
        QueryIntent.VECTOR_TILES: ["os_maps.render"],
        QueryIntent.UNKNOWN: ["os_mcp.descriptor", "admin_lookup.find_by_name"],
    }
    return alternatives.get(intent, [])


def _get_guidance_for_intent(intent: QueryIntent) -> str:
    guidance = {
        QueryIntent.ADDRESS_LOOKUP: (
            "Use OS Places for postcodes, UPRNs, or free-text address search. "
            "Postcodes return multiple UPRNs; UPRN returns a single address."
        ),
        QueryIntent.LINKED_IDS: (
            "Use os_linked_ids.get when the query mentions UPRN/USRN/TOID relationships."
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
        QueryIntent.STATISTICS: (
            "Use NOMIS for labour/census or deep local geographies; otherwise use ONS datasets. "
            "Prefer nomis.query directly when dataset is known. If you need discovery, call "
            "nomis.datasets with q and limit to avoid large payloads. ONS flow: "
            "ons_data.dimensions to find filters, then ons_data.query for observations."
        ),
        QueryIntent.AREA_COMPARISON: (
            "Use the statistics dashboard to compare multiple areas, or query per area and compare."
        ),
        QueryIntent.INTERACTIVE_SELECTION: (
            "Open the geography selector widget and choose the right level (OA/LSOA/MSOA/ward, etc.)."
        ),
        QueryIntent.ROUTE_PLANNING: (
            "Use the route planner widget to set start/end coordinates."
        ),
        QueryIntent.DATASET_DISCOVERY: (
            "Use ons_data.dimensions/ons_search.query for ONS datasets or "
            "nomis.datasets with q and limit for labour/census."
        ),
        QueryIntent.MAP_RENDER: (
            "Use os_maps.render with a bbox to obtain a static map URL template."
        ),
        QueryIntent.VECTOR_TILES: (
            "Use os_vector_tiles.descriptor for tile/style templates; inject OS_API_KEY client-side."
        ),
        QueryIntent.UNKNOWN: (
            "Intent unclear. Use os_mcp.descriptor for tool discovery or be more specific."
        ),
    }
    return guidance.get(intent, guidance[QueryIntent.UNKNOWN])


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
        "guidance": {"type": "string"}
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
    return 200, {
        "query": query,
        "intent": intent.value,
        "confidence": round(confidence, 2),
        "recommended_tool": tool,
        "recommended_parameters": params,
        "explanation": explanation,
        "workflow_steps": workflow,
        "alternative_tools": _get_alternative_tools(intent),
        "guidance": _get_guidance_for_intent(intent),
    }


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
