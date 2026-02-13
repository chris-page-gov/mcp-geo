from __future__ import annotations

import json
import re
from datetime import datetime, timezone
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
_DEFAULT_RELATED_LIMIT = 5
_MAX_RELATED_LIMIT = 10

_GEO_LEVEL_ALIASES: dict[str, str] = {
    "oa": "oa",
    "output_area": "oa",
    "lsoa": "lsoa",
    "msoa": "msoa",
    "ward": "ward",
    "local_authority": "local_authority",
    "lad": "local_authority",
    "region": "region",
    "nation": "nation",
    "country": "nation",
    "uk": "nation",
}

_TIME_ALIASES: dict[str, str] = {
    "month": "month",
    "monthly": "month",
    "quarter": "quarter",
    "quarterly": "quarter",
    "year": "year",
    "annual": "year",
    "yearly": "year",
    "latest": "latest",
}

_REVISION_STABLE = {"published", "final", "revised"}
_REVISION_PROVISIONAL = {"provisional", "experimental", "preliminary"}


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


def _entry_tokens(entry: dict[str, Any]) -> set[str]:
    parts: list[str] = []
    for key in ("title", "description", "id"):
        value = entry.get(key)
        if isinstance(value, str) and value:
            parts.append(value)
    keywords = entry.get("keywords") or []
    if isinstance(keywords, list):
        parts.extend(str(k) for k in keywords if isinstance(k, str))
    themes = entry.get("themes") or []
    if isinstance(themes, list):
        parts.extend(str(t) for t in themes if isinstance(t, str))
    return set(_tokenize(" ".join(parts)))


def _extract_geo_levels(entry: dict[str, Any]) -> list[str]:
    geo = entry.get("geography")
    if isinstance(geo, dict):
        levels = geo.get("levels")
        if isinstance(levels, list):
            return [str(x).lower() for x in levels if isinstance(x, str)]
    return []


def _extract_time_granularity(entry: dict[str, Any]) -> str | None:
    time_meta = entry.get("time")
    if isinstance(time_meta, dict):
        gran = time_meta.get("granularity")
        if isinstance(gran, str) and gran.strip():
            return _normalize_time_granularity(gran)
    return None


def _normalize_geo_level(value: str) -> str:
    return _GEO_LEVEL_ALIASES.get(value.strip().lower(), value.strip().lower())


def _normalize_time_granularity(value: str) -> str:
    return _TIME_ALIASES.get(value.strip().lower(), value.strip().lower())


def _extract_release_date(entry: dict[str, Any]) -> str | None:
    for key in ("releaseDate", "release_date", "release", "lastUpdated", "last_updated"):
        value = entry.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.strip()
    if not normalized:
        return None
    if normalized.endswith("Z"):
        normalized = f"{normalized[:-1]}+00:00"
    try:
        dt = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _extract_revision_status(entry: dict[str, Any]) -> str | None:
    quality = entry.get("quality")
    if isinstance(quality, dict):
        for key in ("revisionStatus", "revision_status", "status"):
            value = quality.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip().lower()
    state = entry.get("state")
    if isinstance(state, str) and state.strip():
        return state.strip().lower()
    return None


def _has_revision_note(entry: dict[str, Any]) -> bool:
    quality = entry.get("quality")
    if isinstance(quality, dict):
        for key in ("revisionNote", "revision_note", "note", "qualityNote"):
            value = quality.get(key)
            if isinstance(value, str) and value.strip():
                return True
    return False


def _extract_denominator(entry: dict[str, Any]) -> str | None:
    comparability = entry.get("comparability")
    if isinstance(comparability, dict):
        value = comparability.get("denominator")
        if isinstance(value, str) and value.strip():
            return value.strip().lower()
    metadata = entry.get("metadata")
    if isinstance(metadata, dict):
        value = metadata.get("denominator")
        if isinstance(value, str) and value.strip():
            return value.strip().lower()
    return None


def _extract_intent_tags(entry: dict[str, Any]) -> set[str]:
    tags: set[str] = set()
    for key in ("intentTags", "intent_tags", "themes", "keywords"):
        value = entry.get(key)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, str) and item.strip():
                    tags.update(_tokenize(item))
        elif isinstance(value, str) and value.strip():
            tags.update(_tokenize(value))
    return tags


def _extract_method_dependencies(entry: dict[str, Any]) -> set[str]:
    deps: set[str] = set()
    for key in ("derivedFrom", "dependsOn", "inputs", "dependencies"):
        value = entry.get(key)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, str) and item.strip():
                    deps.add(item.strip())
        elif isinstance(value, str) and value.strip():
            deps.add(value.strip())
    return deps


def _extract_geo_levels_normalized(entry: dict[str, Any]) -> set[str]:
    return {_normalize_geo_level(level) for level in _extract_geo_levels(entry)}


def _time_alignment_rule(primary: dict[str, Any], entry: dict[str, Any]) -> bool:
    primary_time = _extract_time_granularity(primary)
    entry_time = _extract_time_granularity(entry)
    if not primary_time or not entry_time:
        return False
    if primary_time == entry_time:
        return True
    for node in (primary, entry):
        time_meta = node.get("time")
        if isinstance(time_meta, dict):
            alignable = time_meta.get("alignableTo") or time_meta.get("alignable_to")
            if isinstance(alignable, list):
                normalized = {_normalize_time_granularity(str(item)) for item in alignable}
                if entry_time in normalized or primary_time in normalized:
                    return True
    comparability = entry.get("comparability")
    if isinstance(comparability, dict):
        rules = comparability.get("timeTransforms") or comparability.get("time_transforms")
        if isinstance(rules, list):
            normalized_rules = {str(rule).strip().lower() for rule in rules}
            pair = f"{primary_time}->{entry_time}"
            inverse = f"{entry_time}->{primary_time}"
            if pair in normalized_rules or inverse in normalized_rules:
                return True
    return False


def _geography_mapping_available(primary: dict[str, Any], entry: dict[str, Any]) -> bool:
    for node in (primary, entry):
        comparability = node.get("comparability")
        if isinstance(comparability, dict):
            mapping = comparability.get("geographyMapping") or comparability.get("geography_mapping")
            if isinstance(mapping, dict) and mapping:
                return True
            if isinstance(mapping, list) and mapping:
                return True
            if isinstance(mapping, str) and mapping.strip():
                return True
    return False


def _link_type(
    primary: dict[str, Any],
    entry: dict[str, Any],
    geo_intersection: set[str],
    time_matches: bool,
    time_aligned: bool,
    revision_mismatch: bool,
    intent_overlap: set[str],
) -> str:
    primary_deps = _extract_method_dependencies(primary)
    entry_deps = _extract_method_dependencies(entry)
    entry_id = str(entry.get("id") or "")
    primary_id = str(primary.get("id") or "")

    if entry_id and entry_id in primary_deps:
        return "derived_from"
    if primary_id and primary_id in entry_deps:
        return "methodological_dependency"
    if primary_deps and entry_deps and (primary_deps & entry_deps):
        return "methodological_dependency"
    if revision_mismatch:
        return "quality_or_revision_context"
    if not geo_intersection and time_matches and intent_overlap:
        return "same_measure_different_geography"
    if geo_intersection and not time_matches and time_aligned and intent_overlap:
        return "same_measure_different_time_granularity"
    return "complementary_context"


def _compatibility_release_alignment(primary: dict[str, Any], entry: dict[str, Any]) -> float:
    primary_release = _parse_iso_datetime(_extract_release_date(primary))
    entry_release = _parse_iso_datetime(_extract_release_date(entry))
    if not primary_release or not entry_release:
        return 0.5
    delta_days = abs((primary_release - entry_release).days)
    if delta_days <= 365:
        return 1.0
    if delta_days <= 730:
        return 0.5
    return 0.2


def _build_link_reason(
    intent_overlap: set[str],
    geography_context: str,
    time_context: str,
    constraints: list[str],
) -> str:
    intent_text = ", ".join(sorted(intent_overlap)[:4]) if intent_overlap else "shared context"
    reason = (
        f"Linked because both series address {intent_text} for "
        f"{geography_context} and can be compared for {time_context}."
    )
    if constraints:
        reason += f" Constraints: {'; '.join(constraints[:3])}."
    return reason


def _comparability_gate(primary: dict[str, Any], entry: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    reasons: list[str] = []
    warnings: list[str] = []
    constraints: list[str] = []
    rejected_by: list[str] = []

    primary_geo = _extract_geo_levels_normalized(primary)
    entry_geo = _extract_geo_levels_normalized(entry)
    geo_intersection = primary_geo & entry_geo
    has_geo_mapping = _geography_mapping_available(primary, entry)
    if primary_geo and entry_geo:
        if geo_intersection:
            reasons.append("Geography levels intersect")
        elif has_geo_mapping:
            constraints.append("Geography differs but mapping is available")
            warnings.append("Geography differs; mapped comparison required")
        else:
            rejected_by.append("geography")
            warnings.append("Geography mismatch without mapping")
    else:
        warnings.append("Missing geography metadata for comparability check")

    primary_time = _extract_time_granularity(primary)
    entry_time = _extract_time_granularity(entry)
    time_matches = bool(primary_time and entry_time and primary_time == entry_time)
    time_aligned = bool(primary_time and entry_time and _time_alignment_rule(primary, entry))
    if primary_time and entry_time:
        if time_matches:
            reasons.append("Time granularity matches")
        elif time_aligned:
            constraints.append("Time basis differs but transform/align rule exists")
            warnings.append("Time granularity differs; transformed comparison required")
        else:
            rejected_by.append("time")
            warnings.append("Time granularity mismatch without transform rule")
    else:
        warnings.append("Missing time granularity for comparability check")

    primary_denom = _extract_denominator(primary)
    entry_denom = _extract_denominator(entry)
    if primary_denom and entry_denom:
        if primary_denom == entry_denom:
            reasons.append("Denominator definitions align")
        else:
            rejected_by.append("denominator")
            warnings.append("Denominator definitions differ")
    else:
        warnings.append("Missing denominator metadata")

    primary_revision = _extract_revision_status(primary)
    entry_revision = _extract_revision_status(entry)
    revision_mismatch = False
    if primary_revision and entry_revision:
        if primary_revision == entry_revision:
            reasons.append("Revision status aligns")
        else:
            revision_mismatch = True
            note_present = _has_revision_note(primary) or _has_revision_note(entry)
            if note_present:
                constraints.append("Revision mismatch disclosed via quality notes")
                warnings.append("Revision mismatch disclosed by quality notes")
            else:
                rejected_by.append("revision")
                warnings.append("Revision mismatch without quality notes")
            if (
                primary_revision in _REVISION_STABLE
                and entry_revision in _REVISION_PROVISIONAL
                and not note_present
            ):
                rejected_by.append("revision")
    else:
        warnings.append("Missing revision-status metadata")

    is_safe = not rejected_by
    result = {
        "isSafe": is_safe,
        "reasons": reasons,
        "warnings": warnings,
        "constraints": constraints,
        "rejectedBy": sorted(set(rejected_by)),
        "geoIntersection": sorted(geo_intersection),
        "hasGeoMapping": has_geo_mapping,
        "timeMatches": time_matches,
        "timeAligned": time_aligned,
        "revisionMismatch": revision_mismatch,
        "primaryRevisionStatus": primary_revision,
        "entryRevisionStatus": entry_revision,
        "primaryReleaseDate": _extract_release_date(primary),
        "entryReleaseDate": _extract_release_date(entry),
        "primaryDenominator": primary_denom,
        "entryDenominator": entry_denom,
    }
    return is_safe, result


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


def _build_related_datasets(
    primary: dict[str, Any],
    entries: list[dict[str, Any]],
    query_tokens: list[str],
    limit: int,
) -> list[dict[str, Any]]:
    primary_tokens = _entry_tokens(primary) | set(query_tokens)
    primary_intent = _extract_intent_tags(primary) | set(query_tokens)
    related: list[dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        if entry.get("id") == primary.get("id"):
            continue
        entry_tokens = _entry_tokens(entry)
        token_overlap = primary_tokens & entry_tokens
        entry_intent = _extract_intent_tags(entry) | entry_tokens
        intent_overlap = primary_intent & entry_intent
        if not token_overlap and not intent_overlap:
            continue
        is_safe, gate = _comparability_gate(primary, entry)
        if not is_safe:
            continue

        geo_intersection = set(gate.get("geoIntersection") or [])
        time_matches = bool(gate.get("timeMatches"))
        time_aligned = bool(gate.get("timeAligned"))
        revision_mismatch = bool(gate.get("revisionMismatch"))
        link_type = _link_type(
            primary,
            entry,
            geo_intersection,
            time_matches,
            time_aligned,
            revision_mismatch,
            intent_overlap,
        )

        intent_fit = min(len(intent_overlap), 3) / 3
        geography_fit = 1.0 if geo_intersection else (0.6 if gate.get("hasGeoMapping") else 0.0)
        time_fit = 1.0 if time_matches else (0.7 if time_aligned else 0.0)
        quality_alignment = (
            0.4 if revision_mismatch else (1.0 if gate.get("primaryRevisionStatus") else 0.7)
        )
        deps_overlap = _extract_method_dependencies(primary) & _extract_method_dependencies(entry)
        method_dependency = 1.0 if deps_overlap else 0.0
        release_alignment = _compatibility_release_alignment(primary, entry)
        score = (
            (30 * intent_fit)
            + (20 * geography_fit)
            + (15 * time_fit)
            + (15 * quality_alignment)
            + (10 * method_dependency)
            + (10 * release_alignment)
        )
        score -= min(len(gate.get("warnings") or []) * 3, 15)
        final_score = max(int(round(score)), 0)

        geography_context = (
            ", ".join(sorted(geo_intersection))
            if geo_intersection
            else ("mapped geographies" if gate.get("hasGeoMapping") else "unknown geographies")
        )
        if time_matches:
            time_context = str(_extract_time_granularity(primary) or "aligned periods")
        elif time_aligned:
            time_context = "aligned periods via transform rules"
        else:
            time_context = "unknown periods"
        link_reason = _build_link_reason(
            intent_overlap=intent_overlap,
            geography_context=geography_context,
            time_context=time_context,
            constraints=list(gate.get("constraints") or []),
        )
        provenance = {
            "sourceName": "ONS catalog",
            "sourceUrl": ((entry.get("links") or {}).get("self") or {}).get("href"),
            "retrievedAt": datetime.now(timezone.utc).isoformat(),
            "licence": "Open Government Licence v3.0",
            "methodNote": "Rule-based comparability scoring using catalog metadata.",
            "qualityNote": (
                f"primary={gate.get('primaryRevisionStatus')}, "
                f"related={gate.get('entryRevisionStatus')}"
            ),
        }
        related.append(
            {
                "datasetId": entry.get("id"),
                "title": entry.get("title"),
                "linkType": link_type,
                "linkScore": final_score,
                "linkReason": link_reason,
                "warnings": gate.get("warnings") or [],
                "provenance": provenance,
                "releaseDates": {
                    "primary": gate.get("primaryReleaseDate"),
                    "related": gate.get("entryReleaseDate"),
                },
                "revisionStatus": {
                    "primary": gate.get("primaryRevisionStatus"),
                    "related": gate.get("entryRevisionStatus"),
                },
                "comparability": {
                    "geoIntersection": gate.get("geoIntersection") or [],
                    "timeMatches": bool(gate.get("timeMatches")),
                    "timeAligned": bool(gate.get("timeAligned")),
                    "denominator": {
                        "primary": gate.get("primaryDenominator"),
                        "related": gate.get("entryDenominator"),
                    },
                    "constraints": gate.get("constraints") or [],
                },
            }
        )
    related.sort(key=lambda item: (-item.get("linkScore", 0), str(item.get("title", ""))))
    return related[:limit]


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
    include_related = payload.get("includeRelated", False)
    if not isinstance(include_related, bool):
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "includeRelated must be a boolean",
        }
    related_limit = payload.get("relatedLimit", _DEFAULT_RELATED_LIMIT)
    if not isinstance(related_limit, int) or related_limit < 1:
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "relatedLimit must be >= 1",
        }
    related_limit = min(related_limit, _MAX_RELATED_LIMIT)

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
    top_entries: list[dict[str, Any]] = []
    for score, entry, reasons, warnings in scored[:limit]:
        top_entries.append(entry)
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

    related = []
    if include_related and top_entries:
        related = _build_related_datasets(top_entries[0], catalog_items, tokens, related_limit)

    return 200, {
        "query": query,
        "candidates": candidates,
        "candidateCount": len(candidates),
        "needsElicitation": bool(questions),
        "elicitationQuestions": questions,
        "relatedDatasets": related,
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
                "includeRelated": {"type": "boolean"},
                "relatedLimit": {"type": "integer", "minimum": 1, "maximum": 10},
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
                "relatedDatasets": {"type": "array"},
                "catalogMeta": {"type": "object"},
            },
            "required": ["query", "candidates", "candidateCount"],
        },
        handler=_search,
    )
)
