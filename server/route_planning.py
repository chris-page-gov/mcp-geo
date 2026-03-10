from __future__ import annotations

import re
from typing import Any

SUPPORTED_ROUTE_PROFILES = ("drive", "walk", "cycle", "emergency", "multimodal")
DEFAULT_ROUTE_PROFILE = "drive"
POSTCODE_REGEX = re.compile(
    r"\b[A-Z]{1,2}[0-9][0-9A-Z]?\s*[0-9][A-Z]{2}\b",
    re.IGNORECASE,
)
UPRN_REGEX = re.compile(r"\b\d{8,13}\b")
LAT_LON_REGEX = re.compile(r"\b(-?\d{1,2}\.\d+)\s*,\s*(-?\d{1,3}\.\d+)\b")
AVOID_REFERENCE_REGEX = re.compile(r"\b[A-Z0-9]+(?:/[A-Z0-9]+)+\b", re.IGNORECASE)
AVOID_TOKEN_REGEX = re.compile(r"[A-Z0-9/_-]+", re.IGNORECASE)
AVOID_COMPACT_ID_REGEX = re.compile(r"^[A-Z0-9_-]+$", re.IGNORECASE)
ROUTE_VERB_REGEX = re.compile(
    r"\b(route|directions?|journey|travel|drive|walk|cycle|emergency route|best route)\b",
    re.IGNORECASE,
)

_PROFILE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("emergency", re.compile(r"\b(emergency|blue light|ambulance|fire|police|urgent)\b", re.I)),
    ("walk", re.compile(r"\b(walk|walking|on foot|pedestrian)\b", re.I)),
    ("cycle", re.compile(r"\b(cycle|cycling|bike|bicycle)\b", re.I)),
    (
        "multimodal",
        re.compile(r"\b(multimodal|multi[- ]modal|rail|train|tram|ferry|interchange)\b", re.I),
    ),
    ("drive", re.compile(r"\b(drive|driving|car|road)\b", re.I)),
)

_PROFILE_ALIASES = {
    "car": "drive",
    "driving": "drive",
    "road": "drive",
    "walk": "walk",
    "walking": "walk",
    "cycle": "cycle",
    "cycling": "cycle",
    "bike": "cycle",
    "bicycle": "cycle",
    "emergency": "emergency",
    "multimodal": "multimodal",
    "multi_modal": "multimodal",
}

_TAIL_NOISE_REGEX = re.compile(
    r"\b(?:if possible|please|thanks|major restrictions?.*|restrictions?.*|distance.*|"
    r"travel path.*|turn(?:ing)? notes?.*|uncertainty.*|verification.*|map recommended.*)"
    r"[ \t,.;:!?]*$",
    re.IGNORECASE,
)
_SOFT_AVOID_HINTS = (
    "if possible",
    "where possible",
    "when possible",
    "if feasible",
    "where feasible",
    "when feasible",
    "preferably",
)


def normalize_route_profile(value: Any) -> str:
    if isinstance(value, str):
        normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
        if normalized in _PROFILE_ALIASES:
            return _PROFILE_ALIASES[normalized]
        if normalized in SUPPORTED_ROUTE_PROFILES:
            return normalized
    return DEFAULT_ROUTE_PROFILE


def detect_route_profile(text: str) -> str:
    for profile, pattern in _PROFILE_PATTERNS:
        if pattern.search(text):
            return profile
    return DEFAULT_ROUTE_PROFILE


def normalize_coordinates(value: Any) -> list[float] | None:
    if isinstance(value, list) and len(value) == 2:
        try:
            lon = float(value[0])
            lat = float(value[1])
        except (TypeError, ValueError):
            return None
        if not (-180.0 <= lon <= 180.0 and -90.0 <= lat <= 90.0):
            return None
        return [lon, lat]
    if isinstance(value, dict):
        lat = value.get("lat")
        lon = value.get("lon")
        try:
            lat_f = float(lat)
            lon_f = float(lon)
        except (TypeError, ValueError):
            return None
        if not (-180.0 <= lon_f <= 180.0 and -90.0 <= lat_f <= 90.0):
            return None
        return [lon_f, lat_f]
    if isinstance(value, str):
        match = LAT_LON_REGEX.search(value)
        if not match:
            return None
        lat = float(match.group(1))
        lon = float(match.group(2))
        if not (-180.0 <= lon <= 180.0 and -90.0 <= lat <= 90.0):
            return None
        return [lon, lat]
    return None


def normalize_stop(stop: Any) -> dict[str, Any] | None:
    if isinstance(stop, str):
        return stop_from_text(stop)
    if not isinstance(stop, dict):
        return None
    if isinstance(stop.get("query"), str) and stop["query"].strip():
        return {"query": stop["query"].strip()}
    if isinstance(stop.get("uprn"), str) and stop["uprn"].strip():
        return {"uprn": stop["uprn"].strip()}
    coordinates = normalize_coordinates(stop.get("coordinates"))
    if coordinates is not None:
        return {"coordinates": coordinates}
    return None


def stop_from_text(text: str) -> dict[str, Any] | None:
    cleaned = clean_stop_text(text)
    if not cleaned:
        return None
    coordinates = normalize_coordinates(cleaned)
    if coordinates is not None and cleaned == cleaned.strip():
        return {"coordinates": coordinates}
    uprn = _extract_uprn(cleaned)
    if uprn and re.search(r"\buprn\b", cleaned, re.IGNORECASE):
        return {"uprn": uprn}
    return {"query": cleaned}


def clean_stop_text(text: str) -> str:
    value = re.sub(r"^(origin|destination|start|end|from|to)\s*:\s*", "", text.strip(), flags=re.I)
    value = _TAIL_NOISE_REGEX.sub("", value).strip(" ,.;:")
    value = re.sub(r"\b(?:and|via)\b[ \t,.;:!?]*$", "", value, flags=re.I).strip(" ,.;:")
    return re.sub(r"\s+", " ", value)


def looks_like_route_query(query: str) -> bool:
    normalized_query = _normalize_query_text(query)
    query_lower = normalized_query.lower()
    if re.search(r"\borigin\s*:\s*.+\bdestination\s*:\s*.+", query_lower, re.S) and re.search(
        r"\b(route mode|mode|profile|via|optional constraints)\b",
        query_lower,
    ):
        return True
    if not ROUTE_VERB_REGEX.search(query):
        return False
    if re.search(r"\bfrom\b.+\bto\b", query_lower):
        return True
    if re.search(r"\borigin\b.+\bdestination\b", query_lower):
        return True
    if re.search(r"\bbetween\b.+\band\b", query_lower):
        return True
    return bool(POSTCODE_REGEX.search(normalized_query) and re.search(r"\bto\b", query_lower))


def extract_route_request(query: str) -> dict[str, Any] | None:
    normalized_query = _normalize_query_text(query)
    if not looks_like_route_query(normalized_query):
        return None

    profile = detect_route_profile(normalized_query)
    constraints, unresolved_avoid_texts = _extract_route_constraints_with_hints(normalized_query)
    base_text = strip_constraints_text(normalized_query)
    start_text, end_text, via_texts = _extract_route_segments(base_text)
    if not start_text or not end_text:
        return None

    start_stop = stop_from_text(start_text)
    end_stop = stop_from_text(end_text)
    via_stops = [stop for stop in (stop_from_text(text) for text in via_texts) if stop]
    if not start_stop or not end_stop:
        return None

    extracted = {
        "startText": clean_stop_text(start_text),
        "endText": clean_stop_text(end_text),
        "viaText": [clean_stop_text(text) for text in via_texts if clean_stop_text(text)],
    }
    if unresolved_avoid_texts:
        extracted["unresolvedAvoidTexts"] = unresolved_avoid_texts

    return {
        "stops": [start_stop, end_stop],
        "via": via_stops,
        "profile": profile,
        "constraints": constraints,
        "extracted": extracted,
    }


def extract_route_constraints(query: str) -> dict[str, Any]:
    constraints, _ = _extract_route_constraints_with_hints(query)
    return constraints


def _extract_route_constraints_with_hints(query: str) -> tuple[dict[str, Any], list[str]]:
    query = _normalize_query_text(query)
    query_lower = query.lower()
    avoid_ids: list[str] = []
    unresolved_avoid_texts: list[str] = []

    for match in re.finditer(
        r"\bavoid(?:ing)?\b\s+(.+?)(?=(?:\bfrom\b|\bto\b|\bvia\b|\bwith\b|$))",
        query,
        re.IGNORECASE,
    ):
        value = clean_stop_text(match.group(1))
        if not value:
            continue
        refs = _extract_avoid_id_tokens(value)
        if refs:
            avoid_ids.extend(refs)
            continue
        unresolved_avoid_texts.append(value)

    return (
        {
            "avoidAreas": [],
            "avoidIds": _dedupe_text(avoid_ids),
            "softAvoid": _has_soft_avoid_language(query_lower),
        },
        _dedupe_text(unresolved_avoid_texts),
    )


def strip_constraints_text(query: str) -> str:
    query = _normalize_query_text(query)
    return re.sub(
        r"\bavoid(?:ing)?\b\s+.+?(?=(?:\bwith\b|\bmajor restrictions\b|\btravel path\b|$))",
        "",
        query,
        flags=re.IGNORECASE,
    ).strip()


def _extract_route_segments(query: str) -> tuple[str | None, str | None, list[str]]:
    origin = _labeled_value(query, "origin")
    destination = _labeled_value(query, "destination")
    if origin and destination:
        return origin, destination, _split_via_segments(query)

    match = re.search(r"\bfrom\b(?P<start>.+?)\bto\b(?P<end>.+)", query, re.IGNORECASE | re.S)
    if not match:
        match = re.search(
            r"\bbetween\b(?P<start>.+?)\band\b(?P<end>.+)",
            query,
            re.IGNORECASE | re.S,
        )
    if not match:
        return None, None, []

    start_text = clean_stop_text(match.group("start"))
    end_block = match.group("end")
    via_texts = _split_via_segments(end_block)
    end_text = re.split(r"\bvia\b", end_block, maxsplit=1, flags=re.IGNORECASE)[0]
    return start_text, clean_stop_text(end_text), via_texts


def _labeled_value(text: str, label: str) -> str | None:
    match = re.search(
        rf"\b{label}\s*:\s*(.+?)(?=(?:\borigin\b|\bdestination\b|\broute mode\b|\boptional constraints\b|$))",
        text,
        re.IGNORECASE | re.S,
    )
    if not match:
        return None
    value = clean_stop_text(match.group(1))
    return value or None


def _split_via_segments(text: str) -> list[str]:
    match = re.search(r"\bvia\b(.+)", text, re.IGNORECASE | re.S)
    if not match:
        return []
    raw = match.group(1)
    cleaned = re.split(r"\b(?:avoid(?:ing)?|with|and avoid)\b", raw, maxsplit=1, flags=re.I)[0]
    parts = re.split(r"\band\b|,", cleaned)
    return [clean_stop_text(part) for part in parts if clean_stop_text(part)]


def _extract_uprn(text: str) -> str | None:
    match = UPRN_REGEX.search(text)
    if not match:
        return None
    return match.group(0)


def _dedupe_text(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        key = value.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(value)
    return out


def _has_soft_avoid_language(query_lower: str) -> bool:
    return any(marker in query_lower for marker in _SOFT_AVOID_HINTS)


def _normalize_query_text(query: str) -> str:
    return re.sub(r"\s+", " ", query).strip()


def _extract_avoid_id_tokens(value: str) -> list[str]:
    tokens = AVOID_REFERENCE_REGEX.findall(value)
    tokens.extend(
        token
        for token in AVOID_TOKEN_REGEX.findall(value)
        if _looks_like_avoid_id_token(token)
    )
    return _dedupe_text(tokens)


def _looks_like_avoid_id_token(token: str) -> bool:
    candidate = token.strip(" ,.;:!?")
    if not candidate or " " in candidate:
        return False
    if AVOID_REFERENCE_REGEX.fullmatch(candidate):
        return True
    if candidate.isdigit():
        return len(candidate) >= 3
    if not AVOID_COMPACT_ID_REGEX.fullmatch(candidate):
        return False
    return any(char.isalpha() for char in candidate) and any(char.isdigit() for char in candidate)
