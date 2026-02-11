from __future__ import annotations

from pathlib import Path
from typing import Any
import json

REQUIRED_ENTRY_FIELDS = ("id", "title", "description", "keywords", "state", "links")
OPTIONAL_LIST_FIELDS = ("themes", "topics", "taxonomies", "intentTags")
REQUIRED_LINK_KEYS = ("editions", "latest_version", "self")


def _validate_str_or_none(entry: dict[str, Any], field: str, errors: list[str]) -> None:
    value = entry.get(field)
    if value is not None and not isinstance(value, str):
        errors.append(f"{field} must be string or null")


def _validate_optional_string_list(
    entry: dict[str, Any],
    field: str,
    errors: list[str],
) -> None:
    value = entry.get(field)
    if value is None:
        return
    if isinstance(value, list):
        if any(not isinstance(item, str) for item in value):
            errors.append(f"{field} must contain strings only")
        return
    if not isinstance(value, str):
        errors.append(f"{field} must be string or list of strings")


def validate_entry_fields(entry: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = [field for field in REQUIRED_ENTRY_FIELDS if field not in entry]
    if missing:
        errors.append(f"missing fields {missing}")
        return errors

    dataset_id = entry.get("id")
    if not isinstance(dataset_id, str) or not dataset_id.strip():
        errors.append("id must be a non-empty string")

    for field in ("title", "description", "state"):
        _validate_str_or_none(entry, field, errors)

    keywords = entry.get("keywords")
    if not isinstance(keywords, list):
        errors.append("keywords must be a list")
    elif any(not isinstance(keyword, str) for keyword in keywords):
        errors.append("keywords must contain strings only")

    links = entry.get("links")
    if not isinstance(links, dict):
        errors.append("links must be a dict")
    else:
        missing_links = [key for key in REQUIRED_LINK_KEYS if key not in links]
        if missing_links:
            errors.append(f"links missing keys {missing_links}")
        latest = links.get("latest_version")
        if isinstance(latest, dict):
            href = latest.get("href")
            if not isinstance(href, str) or not href.strip():
                errors.append("links.latest_version.href must be a non-empty string")
        else:
            errors.append("links.latest_version must be an object")

    for field in OPTIONAL_LIST_FIELDS:
        _validate_optional_string_list(entry, field, errors)

    geography = entry.get("geography")
    if geography is not None:
        if not isinstance(geography, dict):
            errors.append("geography must be an object")
        else:
            levels = geography.get("levels")
            if levels is not None:
                if not isinstance(levels, list) or any(not isinstance(level, str) for level in levels):
                    errors.append("geography.levels must be a list of strings")

    time_meta = entry.get("time")
    if time_meta is not None:
        if not isinstance(time_meta, dict):
            errors.append("time must be an object")
        else:
            granularity = time_meta.get("granularity")
            if granularity is not None and not isinstance(granularity, str):
                errors.append("time.granularity must be a string")
            alignable = time_meta.get("alignableTo") or time_meta.get("alignable_to")
            if alignable is not None:
                if not isinstance(alignable, list) or any(not isinstance(item, str) for item in alignable):
                    errors.append("time.alignableTo must be a list of strings")

    comparability = entry.get("comparability")
    if comparability is not None:
        if not isinstance(comparability, dict):
            errors.append("comparability must be an object")
        else:
            denominator = comparability.get("denominator")
            if denominator is not None and not isinstance(denominator, str):
                errors.append("comparability.denominator must be a string")
            transforms = comparability.get("timeTransforms") or comparability.get("time_transforms")
            if transforms is not None:
                if not isinstance(transforms, list) or any(not isinstance(item, str) for item in transforms):
                    errors.append("comparability.timeTransforms must be a list of strings")
            mapping = comparability.get("geographyMapping") or comparability.get("geography_mapping")
            if mapping is not None and not isinstance(mapping, (dict, list, str)):
                errors.append("comparability.geographyMapping must be dict/list/string")

    quality = entry.get("quality")
    if quality is not None:
        if not isinstance(quality, dict):
            errors.append("quality must be an object")
        else:
            revision_status = quality.get("revisionStatus") or quality.get("revision_status")
            if revision_status is not None and not isinstance(revision_status, str):
                errors.append("quality.revisionStatus must be a string")
            revision_note = quality.get("revisionNote") or quality.get("revision_note")
            if revision_note is not None and not isinstance(revision_note, str):
                errors.append("quality.revisionNote must be a string")

    for date_key in ("releaseDate", "release_date", "lastUpdated", "last_updated"):
        value = entry.get(date_key)
        if value is not None and not isinstance(value, str):
            errors.append(f"{date_key} must be a string")
    return errors


def validate_catalog_payload(payload: dict[str, Any], *, min_items: int = 0) -> list[str]:
    errors: list[str] = []
    if payload.get("placeholder") not in (True, False):
        errors.append("placeholder must be boolean")
    if payload.get("generatedAt") is not None and not isinstance(payload.get("generatedAt"), str):
        errors.append("generatedAt must be a string")
    if payload.get("source") is not None and not isinstance(payload.get("source"), str):
        errors.append("source must be a string")

    items = payload.get("items")
    if not isinstance(items, list):
        errors.append("items must be a list")
        return errors

    if min_items and len(items) < min_items:
        errors.append(f"items must contain at least {min_items} entries")

    seen_ids: set[str] = set()
    for index, entry in enumerate(items):
        if not isinstance(entry, dict):
            errors.append(f"items[{index}] must be an object")
            continue
        entry_errors = validate_entry_fields(entry)
        if entry_errors:
            item_id = entry.get("id", f"items[{index}]")
            errors.append(f"{item_id}: {', '.join(entry_errors)}")
        item_id = entry.get("id")
        if isinstance(item_id, str) and item_id:
            if item_id in seen_ids:
                errors.append(f"duplicate dataset id '{item_id}'")
            seen_ids.add(item_id)
    return errors


def load_catalog(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_catalog_file(path: Path, *, min_items: int = 0) -> tuple[dict[str, Any] | None, list[str]]:
    if not path.exists():
        return None, [f"catalog file not found: {path}"]
    try:
        payload = load_catalog(path)
    except json.JSONDecodeError as exc:
        return None, [f"invalid JSON: {exc}"]
    if not isinstance(payload, dict):
        return None, ["catalog root must be an object"]
    return payload, validate_catalog_payload(payload, min_items=min_items)
