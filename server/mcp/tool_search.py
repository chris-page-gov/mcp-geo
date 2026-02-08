from __future__ import annotations

import difflib
import re
from enum import Enum
from typing import Any, Dict, Iterable, List, Sequence, Set

from tools.registry import Tool, all_tools


class ToolCategory(str, Enum):
    CORE = "core"
    PLACES = "places"
    NAMES = "names"
    FEATURES = "features"
    LINKED = "linked"
    MAPS = "maps"
    VECTOR = "vector"
    ADMIN = "admin"
    STATISTICS = "statistics"
    CODES = "codes"
    APPS = "apps"
    UTILITY = "utility"


_PREFIX_CATEGORY: dict[str, ToolCategory] = {
    "os_places": ToolCategory.PLACES,
    "os_names": ToolCategory.NAMES,
    "os_features": ToolCategory.FEATURES,
    "os_linked_ids": ToolCategory.LINKED,
    "os_maps": ToolCategory.MAPS,
    "os_vector_tiles": ToolCategory.VECTOR,
    "os_map": ToolCategory.MAPS,
    "admin_lookup": ToolCategory.ADMIN,
    "ons_data": ToolCategory.STATISTICS,
    "ons_search": ToolCategory.STATISTICS,
    "ons_select": ToolCategory.STATISTICS,
    "ons_codes": ToolCategory.CODES,
    "nomis": ToolCategory.STATISTICS,
    "os_apps": ToolCategory.APPS,
    "os_mcp": ToolCategory.CORE,
}

_PREFIX_KEYWORDS: dict[str, list[str]] = {
    "os_places": ["address", "postcode", "uprn", "place", "geocode"],
    "os_names": ["gazetteer", "names", "feature", "nearest"],
    "os_features": ["ngd", "feature", "bbox", "collection"],
    "os_linked_ids": ["uprn", "usrn", "toid", "linked"],
    "os_maps": ["map", "render", "static"],
    "os_vector_tiles": ["vector", "tiles", "style", "descriptor"],
    "os_map": ["map", "inventory", "export", "layers", "aggregation", "boundary"],
    "admin_lookup": ["admin", "boundary", "hierarchy", "areas"],
    "ons_data": ["ons", "statistics", "observations", "dataset"],
    "ons_search": ["ons", "search", "dataset", "discover"],
    "ons_select": ["ons", "dataset", "selection", "ranking", "discover"],
    "ons_codes": ["codes", "dimension", "options"],
    "nomis": ["nomis", "labour", "employment", "census", "dataset", "statistics"],
    "os_apps": ["ui", "widget", "interactive", "mcp-apps", "event", "log", "telemetry"],
    "os_mcp": ["metadata", "tool-search", "skills", "capabilities", "route", "router", "intent"],
}

ALWAYS_LOADED_TOOLS: Set[str] = {
    "os_mcp.route_query",
    "os_mcp.stats_routing",
    "os_places.search",
    "os_places.by_postcode",
    "os_names.find",
    "ons_search.query",
    "ons_select.search",
    "ons_data.query",
    "nomis.query",
    "admin_lookup.find_by_name",
    "os_mcp.descriptor",
    "os_apps.render_geography_selector",
    "os_apps.render_boundary_explorer",
    "os_apps.log_event",
}

EXTERNAL_PREFIXES: Set[str] = {
    "os_places",
    "os_names",
    "os_features",
    "os_linked_ids",
    "os_maps",
    "os_vector_tiles",
    "ons_data",
    "ons_search",
    "ons_select",
    "nomis",
}

STATEFUL_TOOLS: Set[str] = {"os_apps.log_event", "ons_data.create_filter", "os_map.export"}
NON_IDEMPOTENT_TOOLS: Set[str] = {"os_apps.log_event", "ons_data.create_filter", "os_map.export"}


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def infer_category(tool_name: str) -> ToolCategory:
    prefix = tool_name.split(".", 1)[0]
    return _PREFIX_CATEGORY.get(prefix, ToolCategory.UTILITY)


def should_defer_loading(tool_name: str) -> bool:
    return tool_name not in ALWAYS_LOADED_TOOLS


def get_tool_annotations(tool_name: str) -> Dict[str, bool]:
    annotations: Dict[str, bool] = {}
    if tool_name not in STATEFUL_TOOLS:
        annotations["readOnlyHint"] = True
    if tool_name not in NON_IDEMPOTENT_TOOLS:
        annotations["idempotentHint"] = True
    prefix = tool_name.split(".", 1)[0]
    if prefix in EXTERNAL_PREFIXES:
        annotations["openWorldHint"] = True
    return annotations


def build_keywords(tool: Tool) -> list[str]:
    prefix = tool.name.split(".", 1)[0]
    keywords = set(_PREFIX_KEYWORDS.get(prefix, []))
    keywords.update(_tokenize(tool.name))
    keywords.update(_tokenize(tool.description))
    return sorted(keywords)


def get_tool_metadata(tool: Tool) -> Dict[str, Any]:
    return {
        "category": infer_category(tool.name).value,
        "keywords": build_keywords(tool),
        "defer_loading": should_defer_loading(tool.name),
        "annotations": get_tool_annotations(tool.name),
    }


def get_tool_search_system_prompt() -> str:
    return (
        "Start with os_mcp.route_query for natural-language requests.\n"
        "Primary tools:\n"
        "- os_places.search: free text address search\n"
        "- os_places.by_postcode: lookup UPRNs and addresses\n"
        "- admin_lookup.find_by_name: find administrative areas by name (use level/levels to reduce noise)\n"
        "- ons_select.search: rank ONS datasets with explainability\n"
        "- ons_search.query: discover ONS datasets (live API search)\n"
        "- ons_data.query: query ONS observations\n"
        "- nomis.query: query NOMIS labour and census statistics\n\n"
        "Use MCP-Apps widgets for interactive workflows (os_apps.* tools).\n"
        "Specialized OS feature tools are for NGD feature collections, not place lookups."
    )


def generate_mcp_toolset_config(server_name: str = "mcp-geo") -> Dict[str, Any]:
    configs = {name: {"defer_loading": False} for name in ALWAYS_LOADED_TOOLS}
    return {
        "type": "mcp_toolset",
        "mcp_server_name": server_name,
        "default_config": {"defer_loading": True},
        "configs": configs,
    }


def get_tool_search_config(category: str | None = None) -> Dict[str, Any]:
    tools = all_tools()
    names = [t.name for t in tools]
    always_loaded = sorted([name for name in names if not should_defer_loading(name)])
    deferred = sorted([name for name in names if should_defer_loading(name)])
    result: Dict[str, Any] = {
        "always_loaded": always_loaded,
        "deferred": deferred,
        "counts": {
            "always_loaded": len(always_loaded),
            "deferred": len(deferred),
            "total": len(names),
        },
        "categories": [c.value for c in ToolCategory],
        "mcp_toolset_config": generate_mcp_toolset_config(),
        "system_prompt": get_tool_search_system_prompt(),
    }
    if category:
        try:
            cat = ToolCategory(category.lower())
        except ValueError:
            result["error"] = (
                f"Invalid category '{category}'. Valid: {[c.value for c in ToolCategory]}"
            )
            return result
        filtered: Dict[str, Any] = {}
        for tool in tools:
            if infer_category(tool.name) != cat:
                continue
            meta = get_tool_metadata(tool)
            filtered[tool.name] = meta
        result["filtered_category"] = category
        result["tools"] = filtered
    return result


def _score_match(query: str, tool: Tool, keywords: Sequence[str]) -> float:
    query_norm = query.strip().lower()
    if not query_norm:
        return 0.0
    name = tool.name.lower()
    desc = tool.description.lower()
    score = 0.0
    if query_norm in name:
        score += 6.0
    elif query_norm in desc:
        score += 3.0
    tokens = _tokenize(query_norm)
    for token in tokens:
        if token in name:
            score += 2.5
        if token in desc:
            score += 1.2
        if token in keywords:
            score += 1.0
    score += difflib.SequenceMatcher(None, query_norm, name).ratio()
    return score


def search_tools(
    query: str,
    *,
    mode: str = "token",
    limit: int = 10,
    category: str | None = None,
    include_schemas: bool = False,
) -> List[Dict[str, Any]]:
    tools = all_tools()
    results: list[dict[str, Any]] = []
    pattern = None
    if mode == "regex":
        try:
            pattern = re.compile(query, re.IGNORECASE)
        except re.error as exc:
            raise ValueError(f"Invalid regex: {exc}") from exc
    normalized_category = category.lower() if isinstance(category, str) else None
    for tool in tools:
        meta = get_tool_metadata(tool)
        if normalized_category and meta["category"] != normalized_category:
            continue
        keywords = meta.get("keywords", [])
        if mode == "regex":
            if not pattern:
                continue
            hay = f"{tool.name} {tool.description} {' '.join(keywords)}"
            if not pattern.search(hay):
                continue
            score = 1.0
        else:
            score = _score_match(query, tool, keywords)
            if score <= 0:
                continue
        result = {
            "name": tool.name,
            "description": tool.description,
            "score": round(score, 4),
            "category": meta["category"],
            "keywords": keywords,
            "annotations": meta["annotations"],
            "deferLoading": meta["defer_loading"],
            "defer_loading": meta["defer_loading"],
        }
        if include_schemas:
            result["inputSchema"] = tool.input_schema
            result["outputSchema"] = tool.output_schema
        results.append(result)
    results.sort(key=lambda item: item["score"], reverse=True)
    return results[: max(1, min(limit, 50))]


__all__ = [
    "ToolCategory",
    "ALWAYS_LOADED_TOOLS",
    "EXTERNAL_PREFIXES",
    "STATEFUL_TOOLS",
    "NON_IDEMPOTENT_TOOLS",
    "infer_category",
    "should_defer_loading",
    "get_tool_annotations",
    "build_keywords",
    "get_tool_metadata",
    "get_tool_search_system_prompt",
    "generate_mcp_toolset_config",
    "get_tool_search_config",
    "search_tools",
]
