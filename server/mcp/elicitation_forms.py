from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Optional, Tuple


def client_supports_elicitation_form(capabilities: Dict[str, Any]) -> bool:
    """Return True if a client capability object indicates form elicitation support."""
    if not isinstance(capabilities, dict):
        return False
    elicitation = capabilities.get("elicitation")
    if elicitation is None:
        return False
    if not isinstance(elicitation, dict):
        return False
    # Spec compatibility: empty object implies form support.
    if not elicitation:
        return True
    return isinstance(elicitation.get("form"), dict)


_GEO_LEVEL_ALIASES: dict[str, str] = {
    "nation": "nation",
    "national": "nation",
    "country": "nation",
    "region": "region",
    "regional": "region",
    "local_authority": "local_authority",
    "local-authority": "local_authority",
    "local authority": "local_authority",
    "la": "local_authority",
    "ward": "ward",
    "wards": "ward",
}

_TIME_GRANULARITY_ALIASES: dict[str, str] = {
    "latest": "latest",
    "current": "latest",
    "annual": "year",
    "year": "year",
    "yearly": "year",
    "quarter": "quarter",
    "quarterly": "quarter",
    "qtr": "quarter",
    "month": "month",
    "monthly": "month",
}


def normalize_ons_select_geography_level(value: str) -> Optional[str]:
    raw = value.strip().lower()
    if not raw:
        return None
    return _GEO_LEVEL_ALIASES.get(raw, raw)


def normalize_ons_select_time_granularity(value: str) -> Optional[str]:
    raw = value.strip().lower()
    if not raw:
        return None
    return _TIME_GRANULARITY_ALIASES.get(raw, raw)


def _coerce_string_list(value: Any) -> Optional[List[str]]:
    if value is None:
        return None
    if isinstance(value, list):
        out = [str(x).strip() for x in value if isinstance(x, str) and x.strip()]
        return out or None
    if isinstance(value, str) and value.strip():
        # Accept comma/semicolon separated lists.
        parts = [p.strip() for p in re.split(r"[,\n;]+", value) if p.strip()]
        return parts or None
    return None


def build_ons_select_elicitation_params(
    query: str,
    payload: Dict[str, Any],
    questions: Optional[Iterable[str]] = None,
) -> Dict[str, Any]:
    geo_default = ""
    if isinstance(payload.get("geographyLevel"), str):
        normalized = normalize_ons_select_geography_level(str(payload.get("geographyLevel")))
        if normalized:
            geo_default = normalized
    time_default = ""
    if isinstance(payload.get("timeGranularity"), str):
        normalized = normalize_ons_select_time_granularity(str(payload.get("timeGranularity")))
        if normalized:
            time_default = normalized
    intent_default = ""
    intent_tags = payload.get("intentTags")
    if isinstance(intent_tags, list) and all(isinstance(x, str) for x in intent_tags):
        intent_default = ", ".join([x.strip() for x in intent_tags if x.strip()])
    elif isinstance(intent_tags, str) and intent_tags.strip():
        intent_default = intent_tags.strip()

    message = "Provide optional context to improve ONS dataset ranking."
    if questions:
        cleaned = [q.strip() for q in questions if isinstance(q, str) and q.strip()]
        if cleaned:
            joined = " ".join(cleaned[:3])
            message = f"{message} {joined}"

    return {
        "mode": "form",
        "message": message,
        "requestedSchema": {
            "type": "object",
            "properties": {
                "geographyLevel": {
                    "type": "string",
                    "title": "Geography level",
                    "description": "Choose the area level you care about (optional).",
                    "oneOf": [
                        {"const": "", "title": "No preference"},
                        {"const": "nation", "title": "Nation"},
                        {"const": "region", "title": "Region"},
                        {"const": "local_authority", "title": "Local authority"},
                        {"const": "ward", "title": "Ward"},
                    ],
                    "default": geo_default,
                },
                "timeGranularity": {
                    "type": "string",
                    "title": "Time granularity",
                    "description": "Choose a time basis (optional).",
                    "oneOf": [
                        {"const": "", "title": "No preference"},
                        {"const": "latest", "title": "Latest available"},
                        {"const": "year", "title": "Annual"},
                        {"const": "quarter", "title": "Quarterly"},
                        {"const": "month", "title": "Monthly"},
                    ],
                    "default": time_default,
                },
                "intentTags": {
                    "type": "string",
                    "title": "Topic focus (optional)",
                    "description": "Optional comma-separated keywords/tags to prioritise.",
                    "default": intent_default,
                },
            },
            "required": [],
        },
        "_meta": {"reason": "ons_select_search", "query": query},
    }


def apply_ons_select_elicitation_result(
    payload: Dict[str, Any],
    response: Dict[str, Any],
) -> Tuple[bool, Optional[Dict[str, Any]]]:
    action = response.get("action")
    if action in {"cancel", "decline"}:
        return False, None
    if action != "accept":
        return False, {
            "isError": True,
            "code": "ELICITATION_INVALID_RESULT",
            "message": "Client returned an invalid elicitation result.",
        }
    content = response.get("content")
    if not isinstance(content, dict):
        return False, None
    changed = False

    geo = content.get("geographyLevel")
    if isinstance(geo, str):
        normalized_geo = normalize_ons_select_geography_level(geo)
        if normalized_geo:
            payload["geographyLevel"] = normalized_geo
            changed = True

    time_gran = content.get("timeGranularity")
    if isinstance(time_gran, str):
        normalized_time = normalize_ons_select_time_granularity(time_gran)
        if normalized_time:
            payload["timeGranularity"] = normalized_time
            changed = True

    intent_tags = _coerce_string_list(content.get("intentTags"))
    if intent_tags:
        payload["intentTags"] = intent_tags
        changed = True

    return changed, None


def _coerce_toolset_list(value: Any) -> Optional[List[str]]:
    if value is None:
        return None
    if isinstance(value, list):
        values = [str(item).strip() for item in value if isinstance(item, str) and item.strip()]
        return values or None
    if isinstance(value, str) and value.strip():
        parts = [part.strip() for part in re.split(r"[,\n;]+", value) if part.strip()]
        return parts or None
    return None


def build_toolset_selection_elicitation_params(
    *,
    query: str,
    toolset_names: List[str],
    default_include: Optional[List[str]] = None,
    default_exclude: Optional[List[str]] = None,
) -> Dict[str, Any]:
    include_default = [item for item in (default_include or []) if item in toolset_names]
    exclude_default = [item for item in (default_exclude or []) if item in toolset_names]
    return {
        "mode": "form",
        "message": "Choose discovery toolsets for this session before listing tools.",
        "requestedSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "title": "Query hint (optional)",
                    "description": "Optional natural-language goal to auto-recommend toolsets.",
                    "default": query,
                },
                "includeToolsets": {
                    "type": "array",
                    "title": "Include toolsets",
                    "description": "Pick toolsets to include when calling tools/list.",
                    "items": {"type": "string", "enum": toolset_names},
                    "default": include_default,
                },
                "excludeToolsets": {
                    "type": "array",
                    "title": "Exclude toolsets",
                    "description": "Optional toolsets to exclude from tools/list.",
                    "items": {"type": "string", "enum": toolset_names},
                    "default": exclude_default,
                },
            },
            "required": [],
        },
        "_meta": {"reason": "os_mcp_select_toolsets"},
    }


def apply_toolset_selection_elicitation_result(
    payload: Dict[str, Any],
    response: Dict[str, Any],
) -> Tuple[bool, Optional[Dict[str, Any]]]:
    action = response.get("action")
    if action in {"cancel", "decline"}:
        return False, {
            "isError": True,
            "code": "ELICITATION_CANCELLED",
            "message": "User cancelled or declined toolset selection.",
            "action": action,
        }
    if action != "accept":
        return False, {
            "isError": True,
            "code": "ELICITATION_INVALID_RESULT",
            "message": "Client returned an invalid elicitation result.",
        }
    content = response.get("content")
    if not isinstance(content, dict):
        return True, None
    query = content.get("query")
    if isinstance(query, str) and query.strip():
        payload["query"] = query.strip()
    include = _coerce_toolset_list(content.get("includeToolsets"))
    if include is not None:
        payload["includeToolsets"] = include
    exclude = _coerce_toolset_list(content.get("excludeToolsets"))
    if exclude is not None:
        payload["excludeToolsets"] = exclude
    return True, None
