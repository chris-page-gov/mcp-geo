from __future__ import annotations
from pathlib import Path
from typing import Any, cast

from server.config import settings
from server.dataset_cache import DatasetCache
from tools.ons_common import ONSClient
from tools.registry import Tool, register, ToolResult

_CLIENT = ONSClient()
_CLIENT.base_api = (
    getattr(settings, "ONS_DATASET_API_BASE", "")
    or "https://api.beta.ons.gov.uk/v1"
)

_DATASET_ALIASES = {
    "gdp": "gdp-to-four-decimal-places",
}


def _dataset_cache() -> DatasetCache | None:
    if not settings.ONS_DATASET_CACHE_ENABLED:
        return None
    return DatasetCache(Path(settings.ONS_DATASET_CACHE_DIR))


def _require_live(dataset: Any, edition: Any, version: Any) -> ToolResult | None:
    if not settings.ONS_LIVE_ENABLED:
        return 501, {
            "isError": True,
            "code": "LIVE_DISABLED",
            "message": "ONS live mode is disabled. Set ONS_LIVE_ENABLED=true.",
        }
    if not all(isinstance(val, str) and val for val in (dataset, edition, version)):
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "dataset, edition, and version are required for live ONS codes.",
        }
    return None


def _normalize_dataset_id(dataset: str) -> str:
    normalized = dataset.strip()
    if not normalized:
        return normalized
    return _DATASET_ALIASES.get(normalized.lower(), normalized)


def _pick_latest(items: list[dict[str, Any]], key: str) -> str | None:
    if not items:
        return None
    published = [item for item in items if item.get("state") == "published"]
    candidates = published or items
    values: list[str] = []
    for item in candidates:
        value = item.get(key) or item.get("id")
        if isinstance(value, int):
            value = str(value)
        if isinstance(value, str):
            values.append(value)
    if not values:
        return None
    if all(val.isdigit() for val in values):
        return str(max(int(val) for val in values))
    return values[0]


def _resolve_latest_version(dataset: str) -> tuple[str | None, str | None] | tuple[int, dict[str, Any]]:
    editions_url = f"{_CLIENT.base_api}/datasets/{dataset}/editions"
    status, editions = _CLIENT.get_all_pages(editions_url, params={"limit": 1000, "page": 1})
    if status != 200:
        return status, cast(dict[str, Any], editions)
    if not isinstance(editions, list):
        return None, None
    edition_id = _pick_latest(editions, "edition")
    if not edition_id:
        return None, None
    versions_url = f"{_CLIENT.base_api}/datasets/{dataset}/editions/{edition_id}/versions"
    status_v, versions = _CLIENT.get_all_pages(versions_url, params={"limit": 1000, "page": 1})
    if status_v != 200:
        return status_v, cast(dict[str, Any], versions)
    if not isinstance(versions, list):
        return edition_id, None
    version_id = _pick_latest(versions, "version")
    return edition_id, version_id


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


def _find_dimension(entries: list[dict[str, str]], value: str) -> dict[str, str] | None:
    needle = value.strip().lower()
    if not needle:
        return None
    for entry in entries:
        for candidate in (entry.get("name"), entry.get("id"), entry.get("key")):
            if candidate and candidate.strip().lower() == needle:
                return entry
    return None


def _extract_codes(opt_doc: dict[str, Any]) -> list[str]:
    raw_any = opt_doc.get("items") or opt_doc.get("options") or opt_doc.get("results") or []
    if not isinstance(raw_any, list):
        return []
    codes: list[str] = []
    for entry in raw_any:  # type: ignore[assignment]
        if isinstance(entry, dict):
            entry_dict = cast(dict[str, Any], entry)
            val: Any = (
                entry_dict.get("option")
                or entry_dict.get("id")
                or entry_dict.get("value")
                or entry_dict.get("code")
            )
            if not isinstance(val, str):
                links = entry_dict.get("links")
                if isinstance(links, dict):
                    code_ref = links.get("code")
                    if isinstance(code_ref, dict):
                        nested_id = code_ref.get("id")
                        if isinstance(nested_id, str):
                            val = nested_id
            if isinstance(val, str):
                codes.append(val)
    return codes


def _load_dimension_options(
    dataset: str,
    edition: str,
    version: str,
    entry: dict[str, str],
) -> tuple[list[str] | None, dict[str, Any] | None]:
    last_error: dict[str, Any] | None = None
    tried: list[str] = []
    for candidate in (entry.get("name"), entry.get("id"), entry.get("key")):
        if not candidate:
            continue
        token = candidate.strip()
        if not token or token in tried:
            continue
        tried.append(token)
        opt_url = (
            f"{_CLIENT.base_api}/datasets/{dataset}/editions/{edition}/versions/{version}"
            f"/dimensions/{token}/options"
        )
        status_opt, opt_data = _CLIENT.get_all_pages(opt_url, params={"limit": 1000, "page": 1})
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
        options = _extract_codes({"items": opt_data})
        if options:
            return options, None
    return [], last_error


def _list(payload: dict[str, Any]) -> ToolResult:
    dataset_input = payload.get("dataset")
    dataset = dataset_input
    edition = payload.get("edition")
    version = payload.get("version")
    live_check = _require_live(dataset, edition, version)
    if live_check:
        return live_check
    raw_dataset_text = str(dataset_input).strip() if isinstance(dataset_input, str) else ""
    alias_requested = raw_dataset_text.lower() in _DATASET_ALIASES
    edition_supplied = isinstance(payload.get("edition"), str) and bool(str(payload.get("edition")).strip())
    version_supplied = isinstance(payload.get("version"), str) and bool(str(payload.get("version")).strip())
    dataset = _normalize_dataset_id(dataset)
    if alias_requested and not (edition_supplied and version_supplied):
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
    cache = _dataset_cache()
    cache_key = f"ons_codes:dimensions:{dataset}:{edition}:{version}"
    if cache:
        cached = cache.read(cache_key)
        if cached and isinstance(cached.get("dimensions"), list):
            return 200, {
                "dimensions": cached.get("dimensions", []),
                "live": True,
                "cached": True,
            }
    version_url = f"{_CLIENT.base_api}/datasets/{dataset}/editions/{edition}/versions/{version}"
    status_meta, meta = _CLIENT.get_json(version_url, params=None)
    if status_meta != 200 and alias_requested and isinstance(meta, dict) and _is_stale_version_error(meta):
        resolved_latest = _resolve_latest_version(dataset)
        if isinstance(resolved_latest[0], int):
            return resolved_latest  # type: ignore[return-value]
        latest_edition, latest_version = resolved_latest
        if (
            isinstance(latest_edition, str)
            and latest_edition
            and isinstance(latest_version, str)
            and latest_version
            and (latest_edition != edition or latest_version != version)
        ):
            edition, version = latest_edition, latest_version
            version_url = (
                f"{_CLIENT.base_api}/datasets/{dataset}/editions/{edition}/versions/{version}"
            )
            status_meta, meta = _CLIENT.get_json(version_url, params=None)
    if status_meta != 200:
        return status_meta, meta
    dimensions = _extract_dim_ids(meta)
    if cache:
        cache.write(
            cache_key,
            {"dimensions": dimensions, "source_url": version_url},
        )
    return 200, {"dimensions": dimensions, "live": True}


def _options(payload: dict[str, Any]) -> ToolResult:
    dataset_input = payload.get("dataset")
    dataset = dataset_input
    edition = payload.get("edition")
    version = payload.get("version")
    dim = payload.get("dimension")
    live_check = _require_live(dataset, edition, version)
    if live_check:
        return live_check
    raw_dataset_text = str(dataset_input).strip() if isinstance(dataset_input, str) else ""
    alias_requested = raw_dataset_text.lower() in _DATASET_ALIASES
    edition_supplied = isinstance(payload.get("edition"), str) and bool(str(payload.get("edition")).strip())
    version_supplied = isinstance(payload.get("version"), str) and bool(str(payload.get("version")).strip())
    dataset = _normalize_dataset_id(dataset)
    if alias_requested and not (edition_supplied and version_supplied):
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
    if not isinstance(dim, str) or not dim:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "Missing dimension"}
    cache = _dataset_cache()
    cache_key = f"ons_codes:options:{dataset}:{edition}:{version}:{dim}"
    if cache:
        cached = cache.read(cache_key)
        if cached and isinstance(cached.get("options"), list):
            return 200, {
                "dimension": dim,
                "options": cached.get("options", []),
                "live": True,
                "cached": True,
            }
    direct_url = (
        f"{_CLIENT.base_api}/datasets/{dataset}/editions/{edition}/versions/{version}"
        f"/dimensions/{dim}/options"
    )
    status_direct, direct_data = _CLIENT.get_all_pages(direct_url, params={"limit": 1000, "page": 1})
    options: list[str] | None = None
    source_dim = dim
    source_url = direct_url
    if (
        status_direct != 200
        and alias_requested
        and isinstance(direct_data, dict)
        and _is_stale_version_error(direct_data)
    ):
        resolved_latest = _resolve_latest_version(dataset)
        if isinstance(resolved_latest[0], int):
            return resolved_latest  # type: ignore[return-value]
        latest_edition, latest_version = resolved_latest
        if (
            isinstance(latest_edition, str)
            and latest_edition
            and isinstance(latest_version, str)
            and latest_version
            and (latest_edition != edition or latest_version != version)
        ):
            edition, version = latest_edition, latest_version
            direct_url = (
                f"{_CLIENT.base_api}/datasets/{dataset}/editions/{edition}/versions/{version}"
                f"/dimensions/{dim}/options"
            )
            status_direct, direct_data = _CLIENT.get_all_pages(
                direct_url,
                params={"limit": 1000, "page": 1},
            )
    if status_direct == 200 and isinstance(direct_data, list):
        options = _extract_codes({"items": direct_data})
    else:
        version_url = f"{_CLIENT.base_api}/datasets/{dataset}/editions/{edition}/versions/{version}"
        status_meta, meta = _CLIENT.get_json(version_url, params=None)
        if status_meta != 200 and alias_requested and isinstance(meta, dict) and _is_stale_version_error(meta):
            resolved_latest = _resolve_latest_version(dataset)
            if isinstance(resolved_latest[0], int):
                return resolved_latest  # type: ignore[return-value]
            latest_edition, latest_version = resolved_latest
            if (
                isinstance(latest_edition, str)
                and latest_edition
                and isinstance(latest_version, str)
                and latest_version
                and (latest_edition != edition or latest_version != version)
            ):
                edition, version = latest_edition, latest_version
                version_url = (
                    f"{_CLIENT.base_api}/datasets/{dataset}/editions/{edition}/versions/{version}"
                )
                status_meta, meta = _CLIENT.get_json(version_url, params=None)
        if status_meta != 200:
            return status_meta, meta
        entries = _extract_dim_entries(meta)
        selected = _find_dimension(entries, dim)
        if selected is None:
            return 400, {
                "isError": True,
                "code": "INVALID_INPUT",
                "message": f"Unknown dimension '{dim}'",
            }
        options, err = _load_dimension_options(dataset, edition, version, selected)
        if err is not None:
            return 400, err
        source_dim = selected.get("name") or selected.get("id") or selected.get("key") or dim
        source_url = (
            f"{_CLIENT.base_api}/datasets/{dataset}/editions/{edition}/versions/{version}"
            f"/dimensions/{source_dim}/options"
        )
    if cache:
        cache.write(
            cache_key,
            {"options": options, "source_url": source_url},
        )
    out_dim = source_dim
    return 200, {"dimension": out_dim, "options": options or [], "live": True}

register(Tool(
    name="ons_codes.list",
    description="List available ONS dimensions for a live dataset version.",
    input_schema={"type": "object", "properties": {"tool": {"type": "string", "const": "ons_codes.list"}, "dataset": {"type": "string"}, "edition": {"type": "string"}, "version": {"type": "string"}}, "required": ["dataset", "edition", "version"], "additionalProperties": False},
    output_schema={"type": "object", "properties": {"dimensions": {"type": "array"}, "live": {"type": "boolean"}, "cached": {"type": "boolean"}}, "required": ["dimensions", "live"]},
    handler=_list,
))

register(Tool(
    name="ons_codes.options",
    description="List codes/options for a given ONS live dimension.",
    input_schema={"type": "object", "properties": {"tool": {"type": "string", "const": "ons_codes.options"}, "dimension": {"type": "string"}, "dataset": {"type": "string"}, "edition": {"type": "string"}, "version": {"type": "string"}}, "required": ["dataset", "edition", "version", "dimension"], "additionalProperties": False},
    output_schema={"type": "object", "properties": {"dimension": {"type": "string"}, "options": {"type": "array"}, "live": {"type": "boolean"}, "cached": {"type": "boolean"}}, "required": ["dimension", "options", "live"]},
    handler=_options,
))
