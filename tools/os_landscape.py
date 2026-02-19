from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tools.registry import Tool, ToolResult, register

_RESOURCE_PATH = Path(__file__).resolve().parents[1] / "resources" / "protected_landscapes_england.json"
_CACHE: dict[str, Any] | None = None


def _load_catalog() -> dict[str, Any]:
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    try:
        payload = json.loads(_RESOURCE_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        payload = {
            "version": "missing",
            "scope": "england",
            "source": {},
            "landscapes": [],
        }
    except Exception:
        payload = {
            "version": "invalid",
            "scope": "england",
            "source": {},
            "landscapes": [],
        }
    if not isinstance(payload, dict):
        payload = {
            "version": "invalid",
            "scope": "england",
            "source": {},
            "landscapes": [],
        }
    _CACHE = payload
    return payload


def _normalize(text: str) -> str:
    return " ".join(text.lower().strip().split())


def _landscapes() -> list[dict[str, Any]]:
    catalog = _load_catalog()
    values = catalog.get("landscapes")
    if not isinstance(values, list):
        return []
    return [entry for entry in values if isinstance(entry, dict)]


def _match_score(query: str, entry: dict[str, Any]) -> tuple[int, str | None]:
    name = str(entry.get("name") or "")
    aliases = entry.get("aliases")
    alias_list = [item for item in aliases if isinstance(item, str)] if isinstance(aliases, list) else []
    candidates = [name, *alias_list]
    query_norm = _normalize(query)
    best_score = 0
    best_alias: str | None = None
    for candidate in candidates:
        candidate_norm = _normalize(candidate)
        if not candidate_norm:
            continue
        score = 0
        if query_norm == candidate_norm:
            score = 100
        elif query_norm in candidate_norm:
            score = 70
        elif candidate_norm in query_norm:
            score = 60
        else:
            query_words = set(query_norm.split())
            candidate_words = set(candidate_norm.split())
            overlap = len(query_words & candidate_words)
            if overlap:
                score = 30 + overlap * 10
        if score > best_score:
            best_score = score
            best_alias = candidate
    return best_score, best_alias


def _summary(entry: dict[str, Any], *, score: int | None = None, alias: str | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id": entry.get("id"),
        "name": entry.get("name"),
        "designation": entry.get("designation"),
        "authority": entry.get("authority"),
        "reference": entry.get("reference"),
        "bbox": entry.get("bbox"),
        "centroid": entry.get("centroid"),
    }
    if score is not None:
        payload["score"] = score
    if alias:
        payload["matchedOn"] = alias
    return payload


def _find(payload: dict[str, Any]) -> ToolResult:
    text = payload.get("text")
    if not isinstance(text, str) or not text.strip():
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "text must be a non-empty string",
        }
    limit_raw = payload.get("limit", 5)
    if not isinstance(limit_raw, int) or limit_raw < 1 or limit_raw > 25:
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "limit must be an integer between 1 and 25",
        }

    matches: list[tuple[int, str | None, dict[str, Any]]] = []
    for entry in _landscapes():
        score, alias = _match_score(text, entry)
        if score <= 0:
            continue
        matches.append((score, alias, entry))
    matches.sort(key=lambda item: (-item[0], str(item[2].get("name") or "")))

    catalog = _load_catalog()
    results = [_summary(entry, score=score, alias=alias) for score, alias, entry in matches[:limit_raw]]
    return 200, {
        "query": text,
        "count": len(results),
        "results": results,
        "scope": catalog.get("scope"),
        "source": catalog.get("source"),
        "hints": [
            "Use os_landscape.get with an id from results to fetch authoritative AOI geometry.",
            "For survey planning, resolve AOI first before running os_features.query calls.",
        ],
    }


def _resolve_landscape(payload: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    landscape_id = payload.get("id")
    name = payload.get("name")
    if landscape_id is not None and not isinstance(landscape_id, str):
        return None, "id must be a string when provided"
    if name is not None and not isinstance(name, str):
        return None, "name must be a string when provided"
    if not (isinstance(landscape_id, str) and landscape_id.strip()) and not (
        isinstance(name, str) and name.strip()
    ):
        return None, "provide id or name"

    entries = _landscapes()
    if isinstance(landscape_id, str) and landscape_id.strip():
        target = _normalize(landscape_id)
        for entry in entries:
            current = str(entry.get("id") or "")
            if _normalize(current) == target:
                return entry, None

    if isinstance(name, str) and name.strip():
        scored: list[tuple[int, dict[str, Any]]] = []
        for entry in entries:
            score, _ = _match_score(name, entry)
            if score > 0:
                scored.append((score, entry))
        scored.sort(key=lambda item: (-item[0], str(item[1].get("name") or "")))
        if scored and scored[0][0] >= 60:
            return scored[0][1], None

    return None, "landscape not found"


def _get(payload: dict[str, Any]) -> ToolResult:
    include_geometry = payload.get("includeGeometry", True)
    if not isinstance(include_geometry, bool):
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "includeGeometry must be a boolean",
        }

    entry, err = _resolve_landscape(payload)
    if err:
        status = 404 if err == "landscape not found" else 400
        return status, {
            "isError": True,
            "code": "NOT_FOUND" if status == 404 else "INVALID_INPUT",
            "message": err,
        }
    assert isinstance(entry, dict)

    catalog = _load_catalog()
    response: dict[str, Any] = {
        "landscape": _summary(entry),
        "scope": catalog.get("scope"),
        "source": catalog.get("source"),
        "provenance": entry.get("provenance"),
    }
    if include_geometry:
        response["geometry"] = entry.get("geometry")
    return 200, response


register(
    Tool(
        name="os_landscape.find",
        description=(
            "Find protected landscapes (AONB/National Landscape) by name "
            "for AOI-first environmental survey routing."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "os_landscape.find"},
                "text": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 25},
            },
            "required": ["text"],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "count": {"type": "integer"},
                "results": {"type": "array"},
            },
            "required": ["count", "results"],
            "additionalProperties": True,
        },
        handler=_find,
    )
)

register(
    Tool(
        name="os_landscape.get",
        description="Retrieve a protected-landscape record and boundary geometry by id or name.",
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "os_landscape.get"},
                "id": {"type": "string"},
                "name": {"type": "string"},
                "includeGeometry": {"type": "boolean", "default": True},
            },
            "required": [],
            "additionalProperties": False,
            "anyOf": [{"required": ["id"]}, {"required": ["name"]}],
        },
        output_schema={
            "type": "object",
            "properties": {
                "landscape": {"type": "object"},
                "geometry": {"type": "object"},
                "source": {"type": "object"},
            },
            "required": ["landscape"],
            "additionalProperties": True,
        },
        handler=_get,
    )
)
