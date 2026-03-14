from __future__ import annotations
import base64
import csv
import io
import json
import re
import time
from pathlib import Path
from typing import Any, cast
from urllib.parse import urljoin
from tools.registry import Tool, register, ToolResult
from server.config import settings
from server.mcp.resource_handoff import build_resource_stream_hint
from tools.ons_common import client as ons_client
from tools.typing_utils import is_strict_int


def _require_live() -> ToolResult | None:
    if not settings.ONS_LIVE_ENABLED:
        return 501, {
            "isError": True,
            "code": "LIVE_DISABLED",
            "message": "ONS live mode is disabled. Set ONS_LIVE_ENABLED=true.",
        }
    return None


_MONTH_INDEX = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}

_TIME_TOKEN_PATTERNS = [
    (re.compile(r"^(?P<year>\d{4})$"), lambda m: int(m.group("year")) * 100 + 12),
    (
        re.compile(r"^(?P<year>\d{4})\s*Q(?P<q>[1-4])$", re.IGNORECASE),
        lambda m: int(m.group("year")) * 100 + (int(m.group("q")) * 3),
    ),
    (
        re.compile(r"^(?P<year>\d{4})[-\s]?(?P<month>0[1-9]|1[0-2])$"),
        lambda m: int(m.group("year")) * 100 + int(m.group("month")),
    ),
    (
        re.compile(
            r"^(?P<year>\d{4})\s*(?P<month>Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)$",
            re.IGNORECASE,
        ),
        lambda m: int(m.group("year")) * 100 + _MONTH_INDEX[m.group("month")[:3].lower()],
    ),
    (
        re.compile(
            r"^(?P<month>Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)-(?P<yy>\d{2})$",
            re.IGNORECASE,
        ),
        lambda m: (2000 + int(m.group("yy"))) * 100 + _MONTH_INDEX[m.group("month")[:3].lower()],
    ),
]

_VERSION_PATTERN = re.compile(
    r"/datasets/(?P<dataset>[^/]+)/editions/(?P<edition>[^/]+)/versions/(?P<version>[^/]+)"
)
_YEAR_PATTERN = re.compile(r"^(?P<year>\d{4})$")
_QUARTER_PATTERN = re.compile(r"^(?P<year>\d{4})\s*Q(?P<q>[1-4])$", re.IGNORECASE)
_QUARTER_SHORT_PATTERN = re.compile(r"^Q(?P<q>[1-4])$", re.IGNORECASE)

_MAX_TIME_RANGE_OPTIONS = 48
_DEFAULT_TIME_WILDCARD = "*"
_OBSERVATIONS_FETCH_PAGE_LIMIT = 500

_DATASET_ALIASES = {
    # Backward-compatible alias used by legacy prompts and widget defaults.
    "gdp": "gdp-to-four-decimal-places",
}

_DIMENSION_VALUE_ALIASES = {
    "gdp-to-four-decimal-places": {
        "unofficialstandardindustrialclassification": {
            "gdpv": "A--T",
            "gdp": "A--T",
            "chained_volume_measure": "A--T",
        }
    }
}


def _normalize_dataset_id(dataset: str) -> str:
    normalized = dataset.strip()
    if not normalized:
        return normalized
    return _DATASET_ALIASES.get(normalized.lower(), normalized)


def _parse_time_token(value: str) -> int | None:
    for pattern, builder in _TIME_TOKEN_PATTERNS:
        match = pattern.match(value.strip())
        if match:
            return builder(match)
    return None


def _parse_range_bound(value: str, *, is_end: bool) -> int | None:
    text = value.strip()
    quarter_match = _QUARTER_PATTERN.match(text)
    if quarter_match:
        year = int(quarter_match.group("year"))
        quarter = int(quarter_match.group("q"))
        month = quarter * 3 if is_end else (quarter - 1) * 3 + 1
        return year * 100 + month
    year_match = _YEAR_PATTERN.match(text)
    if year_match:
        year = int(year_match.group("year"))
        month = 12 if is_end else 1
        return year * 100 + month
    return _parse_time_token(text)


def _expand_range_end_token(start_text: str, end_text: str) -> str:
    """Expand shorthand end-bounds such as `2024 Q1-Q2` -> `2024 Q1-2024 Q2`."""
    end = end_text.strip()
    short_quarter = _QUARTER_SHORT_PATTERN.match(end)
    if short_quarter:
        start = start_text.strip()
        quarter_start = _QUARTER_PATTERN.match(start)
        if quarter_start:
            return f"{quarter_start.group('year')} Q{short_quarter.group('q')}"
        year_start = _YEAR_PATTERN.match(start)
        if year_start:
            return f"{year_start.group('year')} Q{short_quarter.group('q')}"
    return end_text


def _resolve_time_values(
    dataset: str,
    edition: str,
    version: str,
    *,
    start_text: str,
    end_text: str | None = None,
) -> tuple[list[str] | None, dict[str, Any] | None]:
    """Resolve one token/range token into concrete ONS time options when possible."""
    range_start = start_text.strip()
    range_end = range_start if end_text is None else _expand_range_end_token(range_start, end_text)
    start_val = _parse_range_bound(range_start, is_end=False)
    end_val = _parse_range_bound(range_end, is_end=True)
    if start_val is None or end_val is None:
        return None, None
    if start_val > end_val:
        start_val, end_val = end_val, start_val
    options, err = _resolve_time_options(dataset, edition, version)
    if err is not None:
        return None, err
    if not options:
        return [], None
    option_values: list[tuple[str, int]] = []
    for opt in options:
        parsed = _parse_time_token(opt)
        if parsed is not None:
            option_values.append((opt, parsed))
    in_range = [opt for opt, parsed in option_values if start_val <= parsed <= end_val]
    if len(in_range) > _MAX_TIME_RANGE_OPTIONS:
        return None, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": f"timeRange expands to {len(in_range)} values; narrow the range.",
        }
    return in_range, None


def _is_stale_version_error(err: dict[str, Any]) -> bool:
    message = str(err.get("message", "")).lower()
    return (
        "not found" in message
        or "invalid version requested" in message
        or "invalid edition requested" in message
    )


def _extract_dim_ids(meta_doc: dict[str, Any]) -> list[str]:
    raw_any = meta_doc.get("dimensions")
    if not isinstance(raw_any, list):
        return []
    ids: list[str] = []
    for entry in raw_any:  # type: ignore[assignment]
        if isinstance(entry, dict):
            entry_dict = cast(dict[str, Any], entry)
            ident: Any = entry_dict.get("name") or entry_dict.get("id")
            if isinstance(ident, str):
                ids.append(ident)
    return ids


def _extract_dim_entries(meta_doc: dict[str, Any]) -> list[dict[str, str]]:
    raw_any = meta_doc.get("dimensions")
    if not isinstance(raw_any, list):
        return []
    entries: list[dict[str, str]] = []
    for entry in raw_any:
        if not isinstance(entry, dict):
            continue
        entry_dict = cast(dict[str, Any], entry)
        name_any: Any = entry_dict.get("name")
        id_any: Any = entry_dict.get("id")
        name = name_any if isinstance(name_any, str) and name_any.strip() else ""
        dim_id = id_any if isinstance(id_any, str) and id_any.strip() else ""
        key = name or dim_id
        if not key:
            continue
        entries.append({"key": key, "name": name, "id": dim_id})
    return entries


def _dimension_matches(entry: dict[str, str], value: str) -> bool:
    needle = value.strip().lower()
    if not needle:
        return False
    for candidate in (entry.get("key"), entry.get("name"), entry.get("id")):
        if candidate and candidate.strip().lower() == needle:
            return True
    return False


def _find_dimension(entries: list[dict[str, str]], value: str) -> dict[str, str] | None:
    for entry in entries:
        if _dimension_matches(entry, value):
            return entry
    return None


def _extract_codes_from_entries(raw_entries: list[dict[str, Any]]) -> list[str]:
    options: list[str] = []
    for entry in raw_entries:
        val: Any = entry.get("option") or entry.get("id") or entry.get("value") or entry.get("code")
        if not isinstance(val, str):
            links = entry.get("links")
            if isinstance(links, dict):
                code_ref = links.get("code")
                if isinstance(code_ref, dict):
                    nested_id = code_ref.get("id")
                    if isinstance(nested_id, str):
                        val = nested_id
        if isinstance(val, str):
            options.append(val)
    return options


def _load_dimension_options(
    dataset: str,
    edition: str,
    version: str,
    entry: dict[str, str],
) -> tuple[list[str] | None, dict[str, Any] | None]:
    # ONS versions can expose both "id" and "name" for dimensions; only one is
    # accepted for options/observations on some datasets. Try both.
    tried: list[str] = []
    last_error: dict[str, Any] | None = None
    for candidate in (entry.get("name"), entry.get("id"), entry.get("key")):
        if not candidate:
            continue
        token = candidate.strip()
        if not token or token in tried:
            continue
        tried.append(token)
        opt_url = (
            f"{ons_client.base_api}/datasets/{dataset}/editions/{edition}/versions/{version}"
            f"/dimensions/{token}/options"
        )
        status_opt, opt_data = ons_client.get_all_pages(opt_url, params={"limit": 1000, "page": 1})
        if status_opt != 200:
            if isinstance(opt_data, dict):
                last_error = cast(dict[str, Any], opt_data)
            continue
        if not isinstance(opt_data, list):
            last_error = {
                "isError": True,
                "code": "INTEGRATION_ERROR",
                "message": "Expected option list from ONS API",
            }
            continue
        options = _extract_codes_from_entries(
            [item for item in opt_data if isinstance(item, dict)]
        )
        if options:
            return options, None
        # Keep searching if this token resolves but returns no options.
    return [], last_error


def _load_version_metadata(
    dataset: str,
    edition: str,
    version: str,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    version_url = f"{ons_client.base_api}/datasets/{dataset}/editions/{edition}/versions/{version}"
    status_meta, meta = ons_client.get_json(version_url, params=None)
    if status_meta != 200:
        return None, meta
    return meta, None


def _pick_latest(items: list[dict[str, Any]], key: str) -> str | None:
    if not items:
        return None
    published = [item for item in items if item.get("state") == "published"]
    candidates = published or items
    values: list[str] = []
    for item in candidates:
        val = item.get(key) or item.get("id")
        if isinstance(val, int):
            val = str(val)
        if isinstance(val, str):
            values.append(val)
    if not values:
        return None
    if all(v.isdigit() for v in values):
        return str(max(int(v) for v in values))
    return values[0]


def _resolve_latest_version(dataset: str) -> tuple[str | None, str | None] | tuple[int, dict[str, Any]]:
    dataset = _normalize_dataset_id(dataset)
    editions_url = f"{ons_client.base_api}/datasets/{dataset}/editions"
    status, items = ons_client.get_all_pages(editions_url, params={"limit": 1000, "page": 1})
    if status != 200:
        return status, cast(dict[str, Any], items)
    if not isinstance(items, list):
        return None, None
    edition_id = _pick_latest(items, "edition")
    if not edition_id:
        return None, None
    versions_url = f"{ons_client.base_api}/datasets/{dataset}/editions/{edition_id}/versions"
    status_v, versions = ons_client.get_all_pages(versions_url, params={"limit": 1000, "page": 1})
    if status_v != 200:
        return status_v, cast(dict[str, Any], versions)
    if not isinstance(versions, list):
        return edition_id, None
    version_id = _pick_latest(versions, "version")
    return edition_id, version_id


def _resolve_from_term(term: str) -> tuple[str | None, str | None, str | None, list[dict[str, Any]] | None] | tuple[int, dict[str, Any]]:
    url = f"{ons_client.base_api}/datasets"
    status, data = ons_client.get_json(url, params={"search": term, "limit": 5, "offset": 0})
    if status != 200:
        return status, data
    items = data.get("items", []) or []
    if not items:
        return None, None, None, []
    chosen = None
    for item in items:
        if isinstance(item, dict) and item.get("state") == "published":
            chosen = item
            break
    if chosen is None:
        chosen = items[0] if isinstance(items[0], dict) else None
    if not chosen:
        return None, None, None, []
    dataset_id = chosen.get("id")
    if not isinstance(dataset_id, str):
        return None, None, None, items
    dataset_id = _normalize_dataset_id(dataset_id)
    latest = chosen.get("links", {}).get("latest_version", {}).get("href")
    if isinstance(latest, str):
        match = _VERSION_PATTERN.search(latest)
        if match:
            return (
                dataset_id,
                match.group("edition"),
                match.group("version"),
                items,
            )
    resolved = _resolve_latest_version(dataset_id)
    if isinstance(resolved, tuple) and len(resolved) == 2 and not isinstance(resolved[0], int):
        return dataset_id, resolved[0], resolved[1], items
    return dataset_id, None, None, items


def _resolve_time_options(dataset: str, edition: str, version: str) -> tuple[list[str] | None, dict[str, Any] | None]:
    meta, err = _load_version_metadata(dataset, edition, version)
    if err is not None:
        return None, err
    if meta is None:
        return None, {"isError": True, "code": "INTEGRATION_ERROR", "message": "Missing version metadata"}
    entries = _extract_dim_entries(meta)
    time_entry: dict[str, str] | None = None
    for entry in entries:
        key = (entry.get("name") or entry.get("key") or "").lower()
        if key in {"time", "date"}:
            time_entry = entry
            break
    if time_entry is None:
        for entry in entries:
            key = (entry.get("name") or entry.get("key") or "").lower()
            if "time" in key or "date" in key:
                time_entry = entry
                break
    if time_entry is None:
        return None, {"isError": True, "code": "INVALID_INPUT", "message": "No time dimension found"}
    options, opt_err = _load_dimension_options(dataset, edition, version, time_entry)
    if opt_err is not None:
        return None, opt_err
    return options or [], None


def _fetch_observations_paged(
    *,
    url: str,
    filters: dict[str, Any],
) -> ToolResult:
    base_filters = dict(filters)
    params = ons_client.build_paged_params(
        _OBSERVATIONS_FETCH_PAGE_LIMIT,
        1,
        base_filters,
    )
    current_url = url
    current_params: dict[str, Any] | None = base_filters
    page = int(params.get("page", 1))
    limit = int(params.get("limit", _OBSERVATIONS_FETCH_PAGE_LIMIT))
    explicit_paging = False
    retried_without_paging = False
    paging_unsupported = False
    observations: list[dict[str, Any]] = []
    dimensions: dict[str, Any] | None = None

    while True:
        status, data = ons_client.get_json(current_url, params=current_params)
        if status != 200:
            uses_paging = isinstance(current_params, dict) and any(
                key in current_params for key in ("limit", "page")
            )
            message = str(data.get("message", "")).lower() if isinstance(data, dict) else ""
            invalid_paging = (
                "incorrect selection of query parameters" in message
                and "limit" in message
                and "page" in message
            )
            if uses_paging and invalid_paging and not retried_without_paging:
                retried_without_paging = True
                paging_unsupported = True
                explicit_paging = False
                current_url = url
                current_params = dict(base_filters)
                page = 1
                limit = _OBSERVATIONS_FETCH_PAGE_LIMIT
                observations = []
                dimensions = None
                continue
            return status, data
        if dimensions is None and isinstance(data.get("dimensions"), dict):
            dimensions = cast(dict[str, Any], data.get("dimensions"))

        batch_raw = data.get("observations", [])
        if batch_raw is None:
            batch_raw = []
        if not isinstance(batch_raw, list):
            return 500, {
                "isError": True,
                "code": "INTEGRATION_ERROR",
                "message": "Expected observations list from ONS API.",
            }
        for item in batch_raw:
            if isinstance(item, dict):
                observations.append(item)

        next_url = None
        links = data.get("links")
        if isinstance(links, list):
            for link in links:
                if isinstance(link, dict) and link.get("rel") == "next":
                    href = link.get("href")
                    if isinstance(href, str) and href:
                        next_url = urljoin(current_url, href)
                    break
        if next_url:
            page += 1
            current_url = next_url
            current_params = None
            continue

        total = data.get("total") or data.get("count")
        if explicit_paging:
            if isinstance(total, int) and page * limit >= total:
                break
            if len(batch_raw) < limit:
                break
            page += 1
            current_url = url
            current_params = ons_client.build_paged_params(limit, page, base_filters)
            continue

        # Start with implicit ONS filtering (dimension params only). If that looks
        # truncated without an advertised next link, retry with explicit paging.
        if (
            not paging_unsupported
            and len(batch_raw) >= limit
            and (not isinstance(total, int) or len(observations) < total)
        ):
            explicit_paging = True
            current_url = url
            page = 1
            current_params = ons_client.build_paged_params(limit, page, base_filters)
            observations = []
            dimensions = None
            continue
        break

    return 200, {"observations": observations, "dimensions": dimensions}


def _query(payload: dict[str, Any]) -> ToolResult:
    dataset_input = payload.get("dataset")
    dataset = dataset_input
    edition = payload.get("edition")
    version = payload.get("version")
    geography = payload.get("geography")
    measure = payload.get("measure")
    time_range = payload.get("timeRange")  # format: "YYYY Qn-YYYY Qn" or single period
    filters = payload.get("filters")
    limit = payload.get("limit", 50)
    page = payload.get("page", 1)
    live_check = _require_live()
    if live_check:
        return live_check
    if filters is not None and not isinstance(filters, dict):
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "filters must be an object"}
    if not is_strict_int(limit) or not 1 <= limit <= 500:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "limit must be 1-500"}
    if not is_strict_int(page) or page < 1:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "page must be >=1"}
    alias_retry_used = bool(payload.get("_aliasRetried"))
    term = payload.get("term") or payload.get("query") or payload.get("datasetQuery")
    if not (isinstance(dataset, str) and dataset):
        if isinstance(term, str) and term.strip():
            resolved = _resolve_from_term(term.strip())
            if isinstance(resolved[0], int):
                return resolved  # type: ignore[return-value]
            dataset, edition, version, candidates = resolved  # type: ignore[misc]
            if not dataset or not edition or not version:
                return 400, {
                    "isError": True,
                    "code": "INVALID_INPUT",
                    "message": "Unable to resolve dataset edition/version from term.",
                    "candidates": candidates or [],
                }
        else:
            return 400, {
                "isError": True,
                "code": "INVALID_INPUT",
                    "message": "dataset, edition, and version are required (or provide term for auto-resolution).",
                }
    if not isinstance(dataset, str) or not dataset:
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "dataset is required for live ONS queries.",
        }
    raw_dataset_text = str(dataset_input).strip() if isinstance(dataset_input, str) else ""
    edition_supplied = isinstance(payload.get("edition"), str) and bool(str(payload.get("edition")).strip())
    version_supplied = isinstance(payload.get("version"), str) and bool(str(payload.get("version")).strip())
    dataset = _normalize_dataset_id(dataset)
    alias_applied = raw_dataset_text.lower() in _DATASET_ALIASES
    if alias_applied and not (edition_supplied and version_supplied):
        resolved_latest = _resolve_latest_version(dataset)
        if isinstance(resolved_latest[0], int):
            return resolved_latest  # type: ignore[return-value]
        latest_edition, latest_version = resolved_latest
        if (
            isinstance(latest_edition, str)
            and latest_edition
            and isinstance(latest_version, str)
            and latest_version
        ):
            edition, version = latest_edition, latest_version
    if not (isinstance(edition, str) and edition) or not (isinstance(version, str) and version):
        resolved = _resolve_latest_version(dataset)
        if isinstance(resolved[0], int):
            return resolved  # type: ignore[return-value]
        edition, version = resolved
    if not (isinstance(edition, str) and edition) or not (isinstance(version, str) and version):
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "dataset, edition, and version are required for live ONS queries.",
        }
    meta, meta_err = _load_version_metadata(dataset, edition, version)
    if meta_err is not None:
        # If caller passed stale version metadata, auto-upgrade to the latest published version.
        if _is_stale_version_error(meta_err):
            resolved = _resolve_latest_version(dataset)
            if not isinstance(resolved[0], int):
                latest_edition, latest_version = resolved
                if (
                    isinstance(latest_edition, str)
                    and latest_edition
                    and isinstance(latest_version, str)
                    and latest_version
                    and (latest_edition != edition or latest_version != version)
                ):
                    edition, version = latest_edition, latest_version
                    meta, meta_err = _load_version_metadata(dataset, edition, version)
        if meta_err is not None:
            return 400, meta_err
    if meta is None:
        return 500, {
            "isError": True,
            "code": "INTEGRATION_ERROR",
            "message": "ONS version metadata missing.",
        }
    dim_entries = _extract_dim_entries(meta)
    if not dim_entries:
        # Compatibility fallback for legacy/mocked responses that omit dimensions.
        params = ons_client.build_paged_params(limit, page, {})
        if geography:
            params["geography"] = geography
        if measure:
            params["measure"] = measure
        if isinstance(time_range, str) and time_range.strip():
            params["time"] = time_range.strip()
        url = (
            f"{ons_client.base_api}/datasets/{dataset}/editions/{edition}/versions/{version}"
            "/observations"
        )
        status, data = ons_client.get_json(url, params=params)
        if status != 200:
            return status, data
        observations = data.get("observations", [])
        if not isinstance(observations, list):
            observations = []
        start = (page - 1) * limit
        end = start + limit
        paged_results = [row for row in observations[start:end] if isinstance(row, dict)]
        next_token = str(page + 1) if end < len(observations) else None
        return 200, {
            "results": paged_results,
            "count": len(observations),
            "limit": limit,
            "page": page,
            "nextPageToken": next_token,
            "live": True,
            "dataset": dataset,
            "edition": edition,
            "version": version,
        }

    def _key(entry: dict[str, str]) -> str:
        return entry.get("name") or entry.get("key") or entry.get("id") or ""

    time_entry = None
    geography_entry = _find_dimension(dim_entries, "geography")
    measure_entry = _find_dimension(dim_entries, "measure")
    for entry in dim_entries:
        token = _key(entry).lower()
        if token in {"time", "date"} or "time" in token or "date" in token:
            time_entry = entry
            break
    extra_measure_entry = None
    for entry in dim_entries:
        key_lower = _key(entry).lower()
        if entry is geography_entry or entry is time_entry or entry is measure_entry:
            continue
        if key_lower:
            extra_measure_entry = entry
            break

    base_filters: dict[str, Any] = {}
    if isinstance(filters, dict):
        for key, value in filters.items():
            if isinstance(key, str) and key.strip():
                base_filters[key.strip()] = value

    if geography and geography_entry is not None:
        base_filters[_key(geography_entry)] = geography

    if measure:
        if measure_entry is not None:
            base_filters[_key(measure_entry)] = measure
        elif extra_measure_entry is not None:
            dim_key = _key(extra_measure_entry)
            mapped = measure
            alias_map = _DIMENSION_VALUE_ALIASES.get(dataset, {}).get(dim_key, {})
            if isinstance(alias_map, dict):
                mapped_alias = alias_map.get(str(measure).strip().lower())
                if isinstance(mapped_alias, str) and mapped_alias:
                    mapped = mapped_alias
            base_filters[dim_key] = mapped

    explicit_time_values: list[str] | None = None
    resolved_time_range: str | None = None
    if isinstance(time_range, str) and time_range.strip():
        resolved_time_range = time_range.strip()
        parts = [part.strip() for part in resolved_time_range.split("-", 1)]
        if len(parts) == 2 and parts[0] and parts[1]:
            in_range, err = _resolve_time_values(
                dataset,
                edition,
                version,
                start_text=parts[0],
                end_text=parts[1],
            )
            if err is not None:
                return 400, err
            if in_range is None:
                explicit_time_values = [resolved_time_range]
            elif not in_range:
                if alias_applied and not alias_retry_used:
                    resolved = _resolve_latest_version(dataset)
                    if not isinstance(resolved[0], int):
                        latest_edition, latest_version = resolved
                        if (
                            isinstance(latest_edition, str)
                            and latest_edition
                            and isinstance(latest_version, str)
                            and latest_version
                            and (latest_edition != edition or latest_version != version)
                        ):
                            retry_payload = dict(payload)
                            retry_payload["dataset"] = dataset
                            retry_payload["edition"] = latest_edition
                            retry_payload["version"] = latest_version
                            retry_payload["_aliasRetried"] = True
                            return _query(retry_payload)
                return 404, {
                    "isError": True,
                    "code": "NOT_FOUND",
                    "message": "No time options in range.",
                }
            else:
                explicit_time_values = in_range
        else:
            expanded_values, err = _resolve_time_values(
                dataset,
                edition,
                version,
                start_text=resolved_time_range,
            )
            if err is not None:
                return 400, err
            if expanded_values:
                explicit_time_values = expanded_values
            else:
                if alias_applied and not alias_retry_used:
                    resolved = _resolve_latest_version(dataset)
                    if not isinstance(resolved[0], int):
                        latest_edition, latest_version = resolved
                        if (
                            isinstance(latest_edition, str)
                            and latest_edition
                            and isinstance(latest_version, str)
                            and latest_version
                            and (latest_edition != edition or latest_version != version)
                        ):
                            retry_payload = dict(payload)
                            retry_payload["dataset"] = dataset
                            retry_payload["edition"] = latest_edition
                            retry_payload["version"] = latest_version
                            retry_payload["_aliasRetried"] = True
                            return _query(retry_payload)
                explicit_time_values = [resolved_time_range]

    for entry in dim_entries:
        dim_key = _key(entry)
        if not dim_key:
            continue
        if entry is time_entry:
            continue
        if dim_key in base_filters:
            continue
        options, err = _load_dimension_options(dataset, edition, version, entry)
        if err is not None:
            return 400, err
        if options:
            base_filters[dim_key] = options[0]

    time_values: list[str] | None = explicit_time_values
    if time_entry is not None:
        time_key = _key(time_entry)
        if time_values is None:
            time_values = [_DEFAULT_TIME_WILDCARD]
        if time_values and len(time_values) == 1:
            base_filters[time_key] = time_values[0]

    url = f"{ons_client.base_api}/datasets/{dataset}/editions/{edition}/versions/{version}/observations"
    results: list[dict[str, Any]] = []
    observation_dimensions: dict[str, Any] | None = None

    if time_entry is not None and time_values and len(time_values) > 1:
        time_key = _key(time_entry)
        for time_value in time_values:
            params = dict(base_filters)
            params[time_key] = time_value
            status, data = _fetch_observations_paged(url=url, filters=params)
            if status != 200:
                return status, data
            if observation_dimensions is None and isinstance(data.get("dimensions"), dict):
                observation_dimensions = cast(dict[str, Any], data.get("dimensions"))
            batch_raw = data.get("observations", [])
            if isinstance(batch_raw, list):
                for item in batch_raw:
                    if isinstance(item, dict):
                        results.append(item)
    else:
        status, data = _fetch_observations_paged(url=url, filters=base_filters)
        if status != 200:
            return status, data
        if isinstance(data.get("dimensions"), dict):
            observation_dimensions = cast(dict[str, Any], data.get("dimensions"))
        batch_raw = data.get("observations", [])
        if isinstance(batch_raw, list):
            for item in batch_raw:
                if isinstance(item, dict):
                    results.append(item)

    total_count = len(results)
    start = (page - 1) * limit
    end = start + limit
    if start >= total_count:
        paged_results: list[dict[str, Any]] = []
    else:
        paged_results = results[start:end]
    next_token = str(page + 1) if end < total_count else None
    return 200, {
        "results": paged_results,
        "count": total_count,
        "limit": limit,
        "page": page,
        "nextPageToken": next_token,
        "live": True,
        "dataset": dataset,
        "edition": edition,
        "version": version,
        "timeRange": resolved_time_range,
        "timeValues": explicit_time_values,
        "filters": base_filters,
        "dimensions": observation_dimensions,
    }


def _dimensions(payload: dict[str, Any]) -> ToolResult:
    dataset_input = payload.get("dataset")
    dataset = dataset_input
    edition = payload.get("edition")
    version = payload.get("version")
    only = payload.get("dimension")
    live_check = _require_live()
    if live_check:
        return live_check
    if not all(isinstance(val, str) and val for val in (dataset, edition, version)):
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "dataset, edition, and version are required for live ONS dimensions.",
        }
    raw_dataset_text = str(dataset_input).strip() if isinstance(dataset_input, str) else ""
    edition_supplied = isinstance(payload.get("edition"), str) and bool(str(payload.get("edition")).strip())
    version_supplied = isinstance(payload.get("version"), str) and bool(str(payload.get("version")).strip())
    dataset = _normalize_dataset_id(dataset)
    if raw_dataset_text.lower() in _DATASET_ALIASES and not (edition_supplied and version_supplied):
        resolved_latest = _resolve_latest_version(dataset)
        if isinstance(resolved_latest[0], int):
            return resolved_latest  # type: ignore[return-value]
        latest_edition, latest_version = resolved_latest
        if (
            isinstance(latest_edition, str)
            and latest_edition
            and isinstance(latest_version, str)
            and latest_version
        ):
            edition, version = latest_edition, latest_version

    meta, meta_err = _load_version_metadata(dataset, edition, version)
    if meta_err is not None:
        if _is_stale_version_error(meta_err):
            resolved = _resolve_latest_version(dataset)
            if not isinstance(resolved[0], int):
                latest_edition, latest_version = resolved
                if (
                    isinstance(latest_edition, str)
                    and latest_edition
                    and isinstance(latest_version, str)
                    and latest_version
                ):
                    edition, version = latest_edition, latest_version
                    meta, meta_err = _load_version_metadata(dataset, edition, version)
        if meta_err is not None:
            return 400, meta_err
    if meta is None:
        return 500, {
            "isError": True,
            "code": "INTEGRATION_ERROR",
            "message": "ONS version metadata missing.",
        }

    dim_entries = _extract_dim_entries(meta)
    if only:
        selected = _find_dimension(dim_entries, only)
        if selected is None:
            return 400, {
                "isError": True,
                "code": "INVALID_INPUT",
                "message": f"Unknown dimension '{only}'",
            }
        dim_entries = [selected]
    result_map: dict[str, list[str]] = {}
    aliases: dict[str, dict[str, str]] = {}
    for entry in dim_entries:
        dim_key = entry.get("name") or entry.get("key") or entry.get("id") or ""
        if not dim_key:
            continue
        options, err = _load_dimension_options(dataset, edition, version, entry)
        if err is not None:
            return 400, err
        result_map[dim_key] = options or []
        aliases[dim_key] = {
            "id": entry.get("id", ""),
            "name": entry.get("name", ""),
        }
    return 200, {
        "dimensions": result_map,
        "dimensionAliases": aliases,
        "live": True,
        "dataset": dataset,
        "edition": edition,
        "version": version,
    }

def _editions(payload: dict[str, Any]) -> ToolResult:
    dataset = payload.get("dataset")
    if not settings.ONS_LIVE_ENABLED:
        return 501, {
            "isError": True,
            "code": "LIVE_DISABLED",
            "message": "ONS live mode is disabled. Set ONS_LIVE_ENABLED=true.",
        }
    if not isinstance(dataset, str) or not dataset:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "dataset is required"}
    dataset = _normalize_dataset_id(dataset)
    url = f"{ons_client.base_api}/datasets/{dataset}/editions"
    status, items = ons_client.get_all_pages(url, params={"limit": 1000, "page": 1})
    if status != 200:
        return status, items
    if not isinstance(items, list):
        return 500, {
            "isError": True,
            "code": "INTEGRATION_ERROR",
            "message": "Expected editions list from ONS API",
        }
    editions: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        edition_id = item.get("edition") or item.get("id")
        if is_strict_int(edition_id):
            edition_id = str(edition_id)
        if not isinstance(edition_id, str):
            continue
        editions.append({
            "id": edition_id,
            "title": item.get("edition") or item.get("title"),
            "state": item.get("state"),
        })
    return 200, {"dataset": dataset, "editions": editions, "count": len(editions), "live": True}


def _versions(payload: dict[str, Any]) -> ToolResult:
    dataset = payload.get("dataset")
    edition = payload.get("edition")
    if not settings.ONS_LIVE_ENABLED:
        return 501, {
            "isError": True,
            "code": "LIVE_DISABLED",
            "message": "ONS live mode is disabled. Set ONS_LIVE_ENABLED=true.",
        }
    if not isinstance(dataset, str) or not dataset:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "dataset is required"}
    dataset = _normalize_dataset_id(dataset)
    if not isinstance(edition, str) or not edition:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "edition is required"}
    url = f"{ons_client.base_api}/datasets/{dataset}/editions/{edition}/versions"
    status, items = ons_client.get_all_pages(url, params={"limit": 1000, "page": 1})
    if status != 200:
        return status, items
    if not isinstance(items, list):
        return 500, {
            "isError": True,
            "code": "INTEGRATION_ERROR",
            "message": "Expected versions list from ONS API",
        }
    versions: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        version_id = item.get("version") or item.get("id")
        if is_strict_int(version_id):
            version_id = str(version_id)
        if not isinstance(version_id, str):
            continue
        versions.append({
            "id": version_id,
            "state": item.get("state"),
            "releaseDate": item.get("release_date"),
        })
    return 200, {
        "dataset": dataset,
        "edition": edition,
        "versions": versions,
        "count": len(versions),
        "live": True,
    }


register(Tool(
    name="ons_data.query",
    description="Query live ONS observations (dataset/edition/version or search term).",
    input_schema={
        "type": "object",
        "properties": {
            "tool": {"type": "string", "const": "ons_data.query"},
            "geography": {"type": "string"},
            "measure": {"type": "string"},
            "timeRange": {"type": "string", "description": "Format 'YYYY Qn-YYYY Qn' or single period 'YYYY Qn'"},
            "filters": {
                "type": "object",
                "description": "Explicit dimension-name filters passed through to ONS observations.",
            },
            "limit": {"type": "integer", "minimum": 1, "maximum": 500},
            "page": {"type": "integer", "minimum": 1},
            "dataset": {"type": "string", "description": "ONS dataset ID for live mode"},
            "edition": {"type": "string", "description": "ONS dataset edition for live mode"},
            "version": {"type": "string", "description": "ONS dataset version for live mode"},
            "term": {"type": "string", "description": "Search term for auto-resolving dataset/edition/version"},
            "query": {"type": "string", "description": "Alias for term"},
        },
        "required": [],
        "additionalProperties": False,
    },
    output_schema={
        "type": "object",
        "properties": {
            "results": {"type": "array", "items": {"type": "object"}},
            "count": {"type": "integer"},
            "limit": {"type": "integer"},
            "page": {"type": "integer"},
            "nextPageToken": {"type": ["string", "null"]},
            "timeRange": {"type": ["string", "null"]},
            "timeValues": {"type": ["array", "null"]},
            "filters": {"type": ["object", "null"]},
            "dimensions": {"type": ["object", "null"]},
        },
        "required": ["results", "count", "limit", "page"],
    },
    handler=_query,
))

register(Tool(
    name="ons_data.dimensions",
    description="List available ONS observation dimensions from the live API.",
    input_schema={
        "type": "object",
        "properties": {
            "tool": {"type": "string", "const": "ons_data.dimensions"},
            "dimension": {"type": "string", "description": "Return only this dimension's codes"},
            "dataset": {"type": "string"},
            "edition": {"type": "string"},
            "version": {"type": "string"},
        },
        "required": ["dataset", "edition", "version"],
        "additionalProperties": False,
    },
    output_schema={
        "type": "object",
        "properties": {
            "dimensions": {"type": "object"},
            "live": {"type": "boolean"},
        },
        "required": ["dimensions", "live"],
    },
    handler=_dimensions,
))

register(Tool(
    name="ons_data.editions",
    description="List live editions for an ONS dataset.",
    input_schema={
        "type": "object",
        "properties": {
            "tool": {"type": "string", "const": "ons_data.editions"},
            "dataset": {"type": "string"},
        },
        "required": ["dataset"],
        "additionalProperties": False,
    },
    output_schema={
        "type": "object",
        "properties": {
            "dataset": {"type": "string"},
            "editions": {"type": "array"},
            "count": {"type": "integer"},
            "live": {"type": "boolean"},
        },
        "required": ["dataset", "editions", "count", "live"],
    },
    handler=_editions,
))

register(Tool(
    name="ons_data.versions",
    description="List live versions for an ONS dataset edition.",
    input_schema={
        "type": "object",
        "properties": {
            "tool": {"type": "string", "const": "ons_data.versions"},
            "dataset": {"type": "string"},
            "edition": {"type": "string"},
        },
        "required": ["dataset", "edition"],
        "additionalProperties": False,
    },
    output_schema={
        "type": "object",
        "properties": {
            "dataset": {"type": "string"},
            "edition": {"type": "string"},
            "versions": {"type": "array"},
            "count": {"type": "integer"},
            "live": {"type": "boolean"},
        },
        "required": ["dataset", "edition", "versions", "count", "live"],
    },
    handler=_versions,
))

# --- Additional ONS Tools (D1 & D2) -------------------------------------------------

_FILTER_STORE: dict[str, dict[str, Any]] = {}
_FILTER_COUNTER = 0
_REPO_ROOT = Path(__file__).resolve().parents[1]
_ONS_EXPORTS_DIR = _REPO_ROOT / "data" / "ons_exports"
_INLINE_EXPORT_MAX_BYTES = 200_000


def _table_headers(rows: list[dict[str, Any]]) -> list[str]:
    headers: list[str] = []
    for row in rows:
        for key in row.keys():
            if key not in headers:
                headers.append(key)
    return headers


def _csv_payload(rows: list[dict[str, Any]]) -> tuple[str, int, int]:
    headers = _table_headers(rows)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(headers)
    for row in rows:
        writer.writerow([row.get(header, "") for header in headers])
    return buf.getvalue(), len(rows), len(headers)


def _xlsx_payload(rows: list[dict[str, Any]]) -> tuple[str, int, int]:
    from openpyxl import Workbook  # type: ignore

    headers = _table_headers(rows)
    wb = Workbook()
    ws = wb.active
    ws.append(headers)
    for row in rows:
        ws.append([row.get(header, "") for header in headers])
    stream = io.BytesIO()
    wb.save(stream)
    encoded = base64.b64encode(stream.getvalue()).decode("ascii")
    return encoded, len(rows), len(headers)


def _write_export_resource(
    *,
    filter_id: str,
    fmt: str,
    content_type: str,
    encoding: str,
    data: Any,
    rows: int | None,
    columns: int | None,
) -> tuple[str, int]:
    _ONS_EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    file_name = f"{filter_id}-{int(time.time() * 1000)}-{fmt.lower()}.json"
    path = _ONS_EXPORTS_DIR / file_name
    payload: dict[str, Any] = {
        "filterId": filter_id,
        "format": fmt,
        "contentType": content_type,
        "encoding": encoding,
        "createdAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "data": data,
    }
    if rows is not None:
        payload["rows"] = rows
    if columns is not None:
        payload["columns"] = columns
    serialized = json.dumps(payload, ensure_ascii=True, separators=(",", ":"))
    path.write_text(serialized, encoding="utf-8")
    return f"resource://mcp-geo/ons-exports/{file_name}", len(serialized.encode("utf-8"))

def _get_observation(payload: dict[str, Any]) -> ToolResult:
    # Live-only: return first matching observation.
    geography = payload.get("geography")
    measure = payload.get("measure")
    time = payload.get("time")
    live_check = _require_live()
    if live_check:
        return live_check
    dataset = payload.get("dataset")
    edition = payload.get("edition")
    version = payload.get("version")
    if not all(isinstance(val, str) and val for val in (dataset, edition, version)):
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "dataset, edition, and version are required for live ONS queries.",
        }
    if not (geography and measure and time):
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "geography, measure, time required"}
    status, result = _query(
        {
            "dataset": dataset,
            "edition": edition,
            "version": version,
            "geography": geography,
            "measure": measure,
            "timeRange": time,
            "limit": 1,
            "page": 1,
        }
    )
    if status != 200:
        return status, result
    obs = result.get("results", []) if isinstance(result, dict) else []
    first = obs[0] if obs else None
    if not first:
        return 404, {"isError": True, "code": "NO_OBSERVATION", "message": "No matching observation"}
    return 200, {"observation": first, "live": True}

def _create_filter(payload: dict[str, Any]) -> ToolResult:
    global _FILTER_COUNTER
    # Accept same filtering fields as query + dataset metadata
    dataset = payload.get("dataset")
    edition = payload.get("edition")
    version = payload.get("version")
    live_check = _require_live()
    if live_check:
        return live_check
    if not all(isinstance(val, str) and val for val in (dataset, edition, version)):
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "dataset, edition, and version are required for live ONS filters.",
        }
    filter_payload = {
        k: payload.get(k)
        for k in ["geography", "measure", "timeRange", "dataset", "edition", "version"]
        if payload.get(k) is not None
    }
    _FILTER_COUNTER += 1
    filter_id = f"f{_FILTER_COUNTER:04d}"
    # Always store; if no params provided store empty dict (interpreted as unfiltered sample)
    _FILTER_STORE[filter_id] = filter_payload or {}
    return 201, {"filterId": filter_id, "params": filter_payload}

def _get_filter_output(payload: dict[str, Any]) -> ToolResult:
    filter_id = payload.get("filterId")
    fmt = (payload.get("format") or "JSON").upper()
    delivery = str(payload.get("delivery") or "inline").strip().lower()
    inline_max_bytes = payload.get("inlineMaxBytes", _INLINE_EXPORT_MAX_BYTES)
    if not isinstance(filter_id, str):
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "Missing filterId"}
    if delivery not in {"inline", "resource", "auto"}:
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "delivery must be one of inline, resource, auto",
        }
    if not is_strict_int(inline_max_bytes) or inline_max_bytes < 1:
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "inlineMaxBytes must be a positive integer",
        }
    stored = _FILTER_STORE.get(filter_id)
    if stored is None:
        # Treat unknown id as 404
        return 404, {"isError": True, "code": "UNKNOWN_FILTER", "message": "Filter not found"}
    # Re-use _query logic for live queries
    status, result = _query(stored)
    if status != 200:
        return status, result
    rows_raw = result.get("results", [])
    rows = [row for row in rows_raw if isinstance(row, dict)] if isinstance(rows_raw, list) else []

    # Supported formats: JSON (structured object), CSV (text), XLSX (base64 binary)
    if fmt == "JSON":
        content_type = "application/json"
        inline_payload = {"filterId": filter_id, "format": fmt, "data": result}
        payload_bytes = len(json.dumps(result, ensure_ascii=True, separators=(",", ":")).encode("utf-8"))
        if delivery == "resource" or (delivery == "auto" and payload_bytes > inline_max_bytes):
            uri, resource_bytes = _write_export_resource(
                filter_id=filter_id,
                fmt=fmt,
                content_type=content_type,
                encoding="json",
                data=result,
                rows=len(rows),
                columns=None,
            )
            return 200, {
                "filterId": filter_id,
                "format": fmt,
                "delivery": "resource",
                "resourceUri": uri,
                "contentType": content_type,
                "bytes": resource_bytes,
                "rows": len(rows),
                "stream": build_resource_stream_hint(
                    uri,
                    hint="Use os_resources.get or resources/read with resourceUri to fetch large outputs without oversized tool payloads.",
                ),
            }
        inline_payload["delivery"] = "inline"
        inline_payload["bytes"] = payload_bytes
        return 200, inline_payload
    if fmt == "CSV":
        csv_text, row_count, col_count = _csv_payload(rows)
        content_type = "text/csv"
        payload_bytes = len(csv_text.encode("utf-8"))
        if delivery == "resource" or (delivery == "auto" and payload_bytes > inline_max_bytes):
            uri, resource_bytes = _write_export_resource(
                filter_id=filter_id,
                fmt=fmt,
                content_type=content_type,
                encoding="utf-8",
                data=csv_text,
                rows=row_count,
                columns=col_count,
            )
            return 200, {
                "filterId": filter_id,
                "format": fmt,
                "delivery": "resource",
                "resourceUri": uri,
                "contentType": content_type,
                "rows": row_count,
                "columns": col_count,
                "bytes": resource_bytes,
                "stream": build_resource_stream_hint(
                    uri,
                    hint="Use os_resources.get or resources/read with resourceUri to fetch large outputs without oversized tool payloads.",
                ),
            }
        return 200, {
            "filterId": filter_id,
            "format": fmt,
            "delivery": "inline",
            "contentType": content_type,
            # Keep legacy field name for compatibility.
            "dataBase64": csv_text,
            "rows": row_count,
            "columns": col_count,
            "bytes": payload_bytes,
        }
    if fmt == "XLSX":
        try:
            b64, row_count, col_count = _xlsx_payload(rows)
            content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            payload_bytes = len(b64.encode("ascii"))
            if delivery == "resource" or (delivery == "auto" and payload_bytes > inline_max_bytes):
                uri, resource_bytes = _write_export_resource(
                    filter_id=filter_id,
                    fmt=fmt,
                    content_type=content_type,
                    encoding="base64",
                    data=b64,
                    rows=row_count,
                    columns=col_count,
                )
                return 200, {
                    "filterId": filter_id,
                    "format": fmt,
                    "delivery": "resource",
                    "resourceUri": uri,
                    "contentType": content_type,
                    "rows": row_count,
                    "columns": col_count,
                    "bytes": resource_bytes,
                    "stream": build_resource_stream_hint(
                        uri,
                        hint="Use os_resources.get or resources/read with resourceUri to fetch large outputs without oversized tool payloads.",
                    ),
                }
            return 200, {
                "filterId": filter_id,
                "format": fmt,
                "delivery": "inline",
                "contentType": content_type,
                # Keep legacy field name for compatibility.
                "dataHex": b64,
                "rows": row_count,
                "columns": col_count,
                "bytes": payload_bytes,
            }
        except Exception as exc:  # pragma: no cover
            return 500, {"isError": True, "code": "INTEGRATION_ERROR", "message": f"XLSX generation failed: {exc}"}
    return 400, {"isError": True, "code": "INVALID_INPUT", "message": "Unsupported format (use JSON, CSV, XLSX)"}

register(Tool(
    name="ons_data.get_observation",
    description="Fetch a single observation by geography, measure, time from the live ONS API.",
    input_schema={
        "type": "object",
        "properties": {
            "tool": {"type": "string", "const": "ons_data.get_observation"},
            "geography": {"type": "string"},
            "measure": {"type": "string"},
            "time": {"type": "string"},
            "dataset": {"type": "string"},
            "edition": {"type": "string"},
            "version": {"type": "string"},
        },
        "required": ["dataset", "edition", "version", "geography", "measure", "time"],
        "additionalProperties": False,
    },
    output_schema={"type": "object", "properties": {"observation": {"type": "object"}, "live": {"type": "boolean"}}, "required": ["observation", "live"]},
    handler=_get_observation,
))

register(Tool(
    name="ons_data.create_filter",
    description="Create a filter for live ONS observations. Returns filterId.",
    input_schema={"type": "object", "properties": {"tool": {"type": "string", "const": "ons_data.create_filter"}, "geography": {"type": "string"}, "measure": {"type": "string"}, "timeRange": {"type": "string"}, "dataset": {"type": "string"}, "edition": {"type": "string"}, "version": {"type": "string"}}, "required": ["dataset", "edition", "version"], "additionalProperties": False},
    output_schema={"type": "object", "properties": {"filterId": {"type": "string"}, "params": {"type": "object"}}, "required": ["filterId", "params"]},
    handler=_create_filter,
))

register(Tool(
    name="ons_data.get_filter_output",
    description=(
        "Retrieve data for a previously created filter (formats: JSON, CSV, XLSX). "
        "Supports inline or resource delivery for larger outputs."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "tool": {"type": "string", "const": "ons_data.get_filter_output"},
            "filterId": {"type": "string"},
            "format": {"type": "string", "enum": ["JSON", "CSV", "XLSX"]},
            "delivery": {"type": "string", "enum": ["inline", "resource", "auto"]},
            "inlineMaxBytes": {"type": "integer", "minimum": 1},
        },
        "required": ["filterId"],
        "additionalProperties": False,
    },
    output_schema={
        "type": "object",
        "properties": {
            "filterId": {"type": "string"},
            "format": {"type": "string"},
            "delivery": {"type": "string"},
            "data": {"type": "object"},
            "contentType": {"type": ["string", "null"]},
            "dataBase64": {"type": ["string", "null"]},
            "dataHex": {"type": ["string", "null"]},
            "resourceUri": {"type": ["string", "null"]},
            "stream": {"type": ["object", "null"]},
            "bytes": {"type": ["integer", "null"]},
            "rows": {"type": ["integer", "null"]},
            "columns": {"type": ["integer", "null"]},
        },
        "required": ["filterId", "format"],
    },
    handler=_get_filter_output,
))
