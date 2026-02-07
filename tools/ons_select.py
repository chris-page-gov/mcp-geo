from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable

from server.config import settings
from tools.ons_common import ONSClient
from tools.registry import Tool, ToolResult, register

_CATALOG_CLIENT = ONSClient()

_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")

_SYNONYMS: dict[str, tuple[str, ...]] = {
    "population": ("demography", "census", "residents"),
    "inflation": ("prices", "cpi", "cpih"),
    "employment": ("jobs", "unemployment", "labour", "work"),
    "housing": ("affordability", "rent", "house", "dwelling"),
    "productivity": ("gva", "output"),
    "migration": ("immigration", "emigration"),
    "health": ("mortality", "life", "wellbeing"),
    "crime": ("offending", "violence"),
}

_DEFAULT_LIMIT = 5
_MAX_LIMIT = 25


def _resolve_catalog_path() -> Path:
    raw = getattr(settings, "ONS_CATALOG_PATH", "resources/ons_catalog.json")
    path = Path(raw)
    if not path.is_absolute():
        root = Path(__file__).resolve().parent.parent
        path = root / raw
    return path


def _tokenize(text: str) -> list[str]:
    return _TOKEN_PATTERN.findall(text.lower())


def _expand_tokens(tokens: Iterable[str]) -> list[str]:
    expanded: list[str] = []
    for token in tokens:
        expanded.append(token)
        expanded.extend(_SYNONYMS.get(token, ()))
    # dedupe while preserving order
    seen: set[str] = set()
    out: list[str] = []
    for token in expanded:
        if token in seen:
            continue
        seen.add(token)
        out.append(token)
    return out


def _load_catalog() -> tuple[list[dict[str, Any]] | None, dict[str, Any] | None]:
    path = _resolve_catalog_path()
    if not path.exists():
        return None, {
            "isError": True,
            "code": "CATALOG_NOT_FOUND",
            "message": "ONS catalog index not found. Run scripts/ons_catalog_refresh.py.",
        }
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, {
            "isError": True,
            "code": "CATALOG_INVALID",
            "message": f"ONS catalog index is not valid JSON: {exc}",
        }
    items = data.get("items") if isinstance(data, dict) else None
    if not isinstance(items, list):
        return None, {
            "isError": True,
            "code": "CATALOG_INVALID",
            "message": "ONS catalog index missing 'items' list.",
        }
    return items, data if isinstance(data, dict) else None


def _live_search(term: str, limit: int) -> ToolResult:
    base_api = getattr(settings, "ONS_DATASET_API_BASE", "https://api.beta.ons.gov.uk/v1")
    url = f"{base_api}/datasets"
    status, data = _CATALOG_CLIENT.get_json(url, params={"search": term, "limit": limit, "offset": 0})
    if status != 200 or not isinstance(data, dict):
        return status, data
    items = data.get("items", []) or []
    results: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        results.append({
            "id": item.get("id"),
            "title": item.get("title"),
            "description": item.get("description"),
            "keywords": item.get("keywords") or [],
            "state": item.get("state"),
            "links": item.get("links") or {},
        })
    payload = {
        "items": results,
        "generatedAt": data.get("last_updated") or None,
        "source": base_api,
        "placeholder": False,
    }
    return 200, payload


def _score_entry(
    entry: dict[str, Any],
    tokens: list[str],
    query: str,
    geography_level: str | None,
    time_granularity: str | None,
) -> tuple[float, list[str], list[str]]:
    score = 0.0
    reasons: list[str] = []
    warnings: list[str] = []

    title = str(entry.get("title") or "")
    description = str(entry.get("description") or "")
    keywords = entry.get("keywords") or []
    themes = entry.get("themes") or []
    dataset_id = str(entry.get("id") or "")

    haystack_title = title.lower()
    haystack_desc = description.lower()
    haystack_id = dataset_id.lower()
    keyword_text = " ".join(str(k).lower() for k in keywords)
    theme_text = " ".join(str(t).lower() for t in themes)

    if query and query.lower() in haystack_title:
        score += 12
        reasons.append("Exact phrase match in title")

    token_hits = 0
    for token in tokens:
        if token in haystack_title:
            score += 6
            token_hits += 1
        elif token in haystack_desc:
            score += 3
            token_hits += 1
        elif token in keyword_text:
            score += 5
            token_hits += 1
        elif token in theme_text:
            score += 2
            token_hits += 1
        elif token in haystack_id:
            score += 4
            token_hits += 1

    if token_hits:
        reasons.append(f"Matched {token_hits} query tokens")

    geo_levels = []
    geo = entry.get("geography")
    if isinstance(geo, dict):
        levels = geo.get("levels")
        if isinstance(levels, list):
            geo_levels = [str(x).lower() for x in levels if isinstance(x, str)]
    if geography_level:
        geo_norm = geography_level.strip().lower()
        if geo_levels:
            if geo_norm in geo_levels:
                score += 8
                reasons.append("Geography level matches")
            else:
                score -= 4
                warnings.append("Geography level mismatch")
        else:
            warnings.append("No geography metadata in catalog entry")

    time_meta = entry.get("time") if isinstance(entry.get("time"), dict) else {}
    if time_granularity:
        gran = None
        if isinstance(time_meta, dict):
            gran = time_meta.get("granularity")
        gran_norm = str(gran).lower() if gran else ""
        requested = time_granularity.strip().lower()
        if gran_norm:
            if requested == gran_norm:
                score += 6
                reasons.append("Time granularity matches")
            else:
                score -= 3
                warnings.append("Time granularity mismatch")
        else:
            warnings.append("No time granularity metadata in catalog entry")

    state = str(entry.get("state") or "").lower()
    if state and state not in {"published", "placeholder"}:
        warnings.append(f"Dataset state is {state}")

    return score, reasons, warnings


def _build_why_not(warnings: list[str], entry: dict[str, Any]) -> list[str]:
    if warnings:
        return warnings
    if str(entry.get("state") or "").lower() == "placeholder":
        return ["Placeholder catalog entry; refresh catalog for live metadata."]
    return []


def _build_elicitation_questions(
    geography_level: str | None,
    time_granularity: str | None,
    intent_tags: list[str] | None,
    tokens: list[str],
) -> list[str]:
    questions: list[str] = []
    if not geography_level:
        questions.append("Which geography level? (nation, region, local authority, ward)")
    if not time_granularity:
        questions.append("What time granularity or period? (latest, annual, quarterly, monthly)")
    if not intent_tags and len(tokens) < 2:
        questions.append("What topic or measure should be prioritised?")
    return questions


def _search(payload: dict[str, Any]) -> ToolResult:
    query = (payload.get("query") or payload.get("q") or "").strip()
    if not query:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "Missing query"}

    limit = payload.get("limit", _DEFAULT_LIMIT)
    if not isinstance(limit, int) or limit < 1:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "limit must be >= 1"}
    limit = min(limit, _MAX_LIMIT)

    geography_level = payload.get("geographyLevel")
    if geography_level is not None and not isinstance(geography_level, str):
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "geographyLevel must be a string",
        }
    time_granularity = payload.get("timeGranularity")
    if time_granularity is not None and not isinstance(time_granularity, str):
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "timeGranularity must be a string",
        }
    intent_tags = payload.get("intentTags")
    if intent_tags is not None and not isinstance(intent_tags, list):
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "intentTags must be a list of strings",
        }
    if isinstance(intent_tags, list) and not all(isinstance(x, str) for x in intent_tags):
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "intentTags must be a list of strings",
        }

    tokens = _expand_tokens(_tokenize(query))

    catalog_items, catalog_meta = _load_catalog()
    used_live = False
    if catalog_items is None:
        if not getattr(settings, "ONS_SELECT_LIVE_ENABLED", True):
            return 501, catalog_meta or {
                "isError": True,
                "code": "CATALOG_UNAVAILABLE",
                "message": "ONS catalog unavailable and live fallback disabled.",
            }
        status, live_payload = _live_search(query, limit)
        if status != 200 or not isinstance(live_payload, dict):
            return status, live_payload
        catalog_items = live_payload.get("items") if isinstance(live_payload, dict) else []
        catalog_meta = live_payload
        used_live = True

    if not catalog_items:
        return 404, {
            "isError": True,
            "code": "CATALOG_EMPTY",
            "message": "ONS catalog is empty; refresh it with scripts/ons_catalog_refresh.py",
        }

    scored: list[tuple[float, dict[str, Any], list[str], list[str]]] = []
    for entry in catalog_items:
        if not isinstance(entry, dict):
            continue
        score, reasons, warnings = _score_entry(
            entry,
            tokens,
            query,
            geography_level,
            time_granularity,
        )
        scored.append((score, entry, reasons, warnings))

    scored.sort(key=lambda item: (-item[0], str(item[1].get("title", ""))))

    candidates: list[dict[str, Any]] = []
    for score, entry, reasons, warnings in scored[:limit]:
        candidates.append(
            {
                "datasetId": entry.get("id"),
                "title": entry.get("title"),
                "description": entry.get("description"),
                "score": round(score, 2),
                "scoreReasons": reasons,
                "warnings": warnings,
                "whyThis": "; ".join(reasons) if reasons else "Matched query context.",
                "whyNot": _build_why_not(warnings, entry),
                "metadata": {
                    "keywords": entry.get("keywords") or [],
                    "themes": entry.get("themes") or [],
                    "state": entry.get("state"),
                    "links": entry.get("links") or {},
                    "geography": entry.get("geography") or {},
                    "time": entry.get("time") or {},
                },
            }
        )

    questions = _build_elicitation_questions(geography_level, time_granularity, intent_tags, tokens)

    return 200, {
        "query": query,
        "candidates": candidates,
        "candidateCount": len(candidates),
        "needsElicitation": bool(questions),
        "elicitationQuestions": questions,
        "catalogMeta": {
            "generatedAt": catalog_meta.get("generatedAt") if isinstance(catalog_meta, dict) else None,
            "source": catalog_meta.get("source") if isinstance(catalog_meta, dict) else None,
            "placeholder": catalog_meta.get("placeholder") if isinstance(catalog_meta, dict) else None,
            "usedLive": used_live,
            "catalogPath": str(_resolve_catalog_path()),
            "totalEntries": len(catalog_items),
        },
    }


register(
    Tool(
        name="ons_select.search",
        description=(
            "Rank ONS datasets using a cached catalog with explainable scoring and "
            "elicitation prompts for missing context."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "ons_select.search"},
                "query": {"type": "string"},
                "q": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 25},
                "geographyLevel": {"type": "string"},
                "timeGranularity": {"type": "string"},
                "intentTags": {"type": "array", "items": {"type": "string"}},
            },
            "required": [],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "candidates": {"type": "array"},
                "candidateCount": {"type": "integer"},
                "needsElicitation": {"type": "boolean"},
                "elicitationQuestions": {"type": "array", "items": {"type": "string"}},
                "catalogMeta": {"type": "object"},
            },
            "required": ["query", "candidates", "candidateCount"],
        },
        handler=_search,
    )
)
