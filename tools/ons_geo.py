from __future__ import annotations

from typing import Any

from server.config import settings
from server.geography_levels import (
    AREA_SUMMARY_LEVEL_RANK,
    AREA_SUMMARY_LEVELS,
    geography_identity_from_normalized,
)
from server.ons_geo_cache import (
    AREA_LEVEL_COLUMN_MAP,
    ONSGeoCache,
    ONSGeoCacheReadError,
    extract_geography_fields,
    infer_area_level_from_code,
    normalize_area_level,
    normalize_derivation_mode,
    normalize_postcode,
    normalize_uprn,
)
from server.ons_geo_catalog import build_release_audit
from server.ons_geo_freshness import summarize_uprn_dataset_freshness
from tools.nomis_data import curated_profile_dataset_specs
from tools.registry import Tool, ToolResult, register
from tools.registry import get as get_tool

_DEFAULT_PROFILE_CATEGORIES = ["population", "sex", "ethnicity", "country_of_birth", "tenure"]
_AREA_SUMMARY_WORKFLOW_URI = "resource://mcp-geo/area-summary-workflows"


def _error(message: str, *, code: str = "INVALID_INPUT", status: int = 400) -> ToolResult:
    return status, {"isError": True, "code": code, "message": message}


def _parse_derivation_mode(payload: dict[str, Any]) -> tuple[str | None, ToolResult | None]:
    default_mode = str(getattr(settings, "ONS_GEO_PRIMARY_DERIVATION", "exact") or "exact")
    raw_mode = payload.get("derivationMode", default_mode)
    if not isinstance(raw_mode, str):
        return None, _error("derivationMode must be a string")
    mode = normalize_derivation_mode(raw_mode)
    if mode is None:
        return None, _error("derivationMode must be one of: exact, best_fit")
    return mode, None


def _build_lookup_response(
    *,
    lookup_key: str,
    normalized_key: str,
    derivation_mode: str,
    cache_result: Any,
    include_raw: bool,
) -> ToolResult:
    geographies = extract_geography_fields(cache_result.row)
    normalized = cache_result.normalized if isinstance(cache_result.normalized, dict) else {}
    normalized_geographies = normalized.get("geographies", {})
    semantic_fields = normalized.get("semanticFields", {})
    code_status_summary = normalized.get("codeStatusSummary", {})
    freshness = summarize_uprn_dataset_freshness(
        dataset_id=cache_result.product_id,
        resolved_release=cache_result.resolved_release,
        resolved_source_url=cache_result.resolved_source_url,
    )
    payload: dict[str, Any] = {
        "query": {
            lookup_key: normalized_key,
            "derivationMode": derivation_mode,
        },
        "lookup": {
            "keyType": cache_result.key_type,
            "product": cache_result.product_id,
            "derivationMode": cache_result.derivation_mode,
            "release": cache_result.release,
            "resolvedRelease": cache_result.resolved_release,
            "sourceName": cache_result.source_name,
            "sourceFormat": cache_result.source_format,
            "schemaFingerprint": cache_result.schema_fingerprint,
            "resolvedSourceUrl": cache_result.resolved_source_url,
            "cachedAt": cache_result.cached_at,
            "freshness": freshness,
        },
        "geographies": geographies,
        "normalizedGeographies": (
            normalized_geographies if isinstance(normalized_geographies, dict) else {}
        ),
        "semanticFields": semantic_fields if isinstance(semantic_fields, dict) else {},
        "codeStatusSummary": code_status_summary if isinstance(code_status_summary, dict) else {},
        "geographyCount": len(geographies),
        "provenance": {
            "source": "ons_geo_cache",
            "product": cache_result.product_id,
            "derivationMode": cache_result.derivation_mode,
            "release": cache_result.release,
            "resolvedRelease": cache_result.resolved_release,
            "schemaFingerprint": cache_result.schema_fingerprint,
            "resolvedSourceUrl": cache_result.resolved_source_url,
            "freshness": freshness,
        },
    }
    if include_raw:
        payload["raw"] = cache_result.row
        payload["normalizedRaw"] = normalized
    return 200, payload


def _cache_performance(*, available: bool, product_count: int) -> dict[str, Any]:
    if not available:
        return {
            "degraded": True,
            "reason": "cache_unavailable",
            "impact": (
                "ons_geo.by_postcode and ons_geo.by_uprn return CACHE_UNAVAILABLE until "
                "scripts/ons_geo_cache_refresh.py populates the cache."
            ),
        }
    if product_count < 1:
        return {
            "degraded": True,
            "reason": "index_empty",
            "impact": (
                "Cache file exists but the index has no products; lookups may return NOT_FOUND "
                "for most keys until products are ingested."
            ),
        }
    return {
        "degraded": False,
        "reason": None,
        "impact": "Cached ONS geography lookup is available.",
    }


def _cache_performance_from_index(*, available: bool, index: dict[str, Any]) -> dict[str, Any]:
    products = index.get("products")
    health = index.get("health")
    if not available:
        product_count = len(products) if isinstance(products, list) else 0
        payload = _cache_performance(available=False, product_count=product_count)
        if isinstance(health, dict):
            payload["exactReady"] = bool(health.get("exactReady"))
            payload["bestFitReady"] = bool(health.get("bestFitReady"))
            payload["supportReady"] = bool(health.get("supportReady"))
            payload["freshnessReady"] = bool(health.get("freshnessReady", True))
            payload["laggingProducts"] = health.get("laggingProducts", [])
        return payload
    if isinstance(health, dict):
        status = str(health.get("status") or "degraded")
        reasons = health.get("degradedReasons")
        return {
            "degraded": status != "ready",
            "reason": (
                None
                if status == "ready"
                else ",".join(reasons)
                if isinstance(reasons, list)
                else "cache_degraded"
            ),
            "impact": (
                "Cached ONS geography lookup is available."
                if status == "ready"
                else "Cache is present but one or more primary/support datasets are degraded."
            ),
            "exactReady": bool(health.get("exactReady")),
            "bestFitReady": bool(health.get("bestFitReady")),
            "supportReady": bool(health.get("supportReady")),
            "freshnessReady": bool(health.get("freshnessReady", True)),
            "laggingProducts": health.get("laggingProducts", []),
        }
    product_count = len(products) if isinstance(products, list) else 0
    return _cache_performance(available=available, product_count=product_count)


def _parse_area_summary_level(value: Any) -> tuple[str | None, ToolResult | None]:
    if value is None:
        return None, None
    if not isinstance(value, str) or not value.strip():
        return None, _error("targetLevel must be a non-empty string")
    normalized = normalize_area_level(value)
    if normalized is None or normalized not in AREA_LEVEL_COLUMN_MAP:
        supported = ", ".join(sorted(AREA_LEVEL_COLUMN_MAP.keys()))
        return None, _error(f"targetLevel must be one of: {supported}")
    return normalized, None


def _parse_response_mode(value: Any) -> tuple[str, ToolResult | None]:
    if value is None:
        return "summary", None
    if not isinstance(value, str):
        return "summary", _error("inventoryResponseMode must be a string")
    normalized = value.strip().lower()
    if normalized not in {"full", "summary", "counts"}:
        return "summary", _error("inventoryResponseMode must be one of: full, summary, counts")
    return normalized, None


def _parse_profile_categories(value: Any) -> tuple[list[str], ToolResult | None]:
    if value is None:
        return list(_DEFAULT_PROFILE_CATEGORIES), None
    if isinstance(value, str):
        raw_values = [part.strip() for part in value.split(",") if part.strip()]
    elif isinstance(value, list):
        raw_values = [str(item).strip() for item in value if str(item).strip()]
    else:
        return [], _error("profileCategories must be a string or array of strings")

    categories: list[str] = []
    for raw in raw_values:
        specs = curated_profile_dataset_specs("DUMMY", [raw])
        if not specs:
            return [], _error(
                "profileCategories must use supported categories: "
                "population, sex, ethnicity, country_of_birth, tenure"
            )
        category = str(specs[0]["category"])
        if category not in categories:
            categories.append(category)
    return categories or list(_DEFAULT_PROFILE_CATEGORIES), None


def _extract_numeric_value(value: Any) -> int | float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(value) if float(value).is_integer() else float(value)
    if isinstance(value, list):
        numeric = [_extract_numeric_value(item) for item in value]
        numeric = [item for item in numeric if item is not None]
        if len(numeric) == 1:
            return numeric[0]
        return None
    if isinstance(value, dict):
        if "value" in value:
            return _extract_numeric_value(value.get("value"))
        numeric = [_extract_numeric_value(item) for item in value.values()]
        numeric = [item for item in numeric if item is not None]
        if len(numeric) == 1:
            return numeric[0]
    return None


def _build_anchor_summary(
    *,
    anchor_type: str,
    anchor_value: str,
    derivation_mode: str,
    cache_result: Any | None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "type": anchor_type,
        "value": anchor_value,
        "derivationMode": derivation_mode,
    }
    if cache_result is not None:
        payload["lookup"] = {
            "product": cache_result.product_id,
            "release": cache_result.release,
            "resolvedRelease": cache_result.resolved_release,
            "resolvedSourceUrl": cache_result.resolved_source_url,
        }
        oac: dict[str, str] = {}
        for key in ("oac01ind", "oac11ind"):
            raw = cache_result.row.get(key)
            if raw is not None and str(raw).strip():
                oac[key] = str(raw).strip()
        if oac:
            payload["classifications"] = oac
    return payload


def _resolve_area_from_lookup(
    *,
    target_level: str,
    cache_result: Any,
) -> tuple[dict[str, Any] | None, ToolResult | None]:
    config = AREA_SUMMARY_LEVELS.get(target_level)
    if config is None:
        return None, _error("Unsupported targetLevel")
    normalized = cache_result.normalized if isinstance(cache_result.normalized, dict) else {}
    semantic_fields = normalized.get("semanticFields", {})
    geographies = normalized.get("geographies", {})
    if not isinstance(semantic_fields, dict):
        semantic_fields = {}
    if not isinstance(geographies, dict):
        geographies = {}

    code = semantic_fields.get(config["semanticKey"])
    geography = geographies.get(config["normalizedKey"])
    if not isinstance(code, str) or not code.strip():
        code = None
        if isinstance(geography, dict):
            raw_code = geography.get("currentCode") or geography.get("code")
            if isinstance(raw_code, str) and raw_code.strip():
                code = raw_code.strip()
    if code is None:
        anchor_key = cache_result.row.get("pcds") or cache_result.row.get("postcode") or ""
        if cache_result.key_type == "uprn":
            anchor_key = cache_result.row.get("uprn") or cache_result.row.get("UPRN") or anchor_key
        return None, _error(
            f"No {target_level} mapping found for anchor {anchor_key}.",
            code="NOT_FOUND",
            status=404,
        )

    area = geography_identity_from_normalized(
        target_level=target_level,
        geography=geography if isinstance(geography, dict) else {},
        fallback_code=code,
    )
    area["hierarchy"] = geographies if isinstance(geographies, dict) else {}
    return area, None


def _best_effort_call(
    tool_name: str,
    arguments: dict[str, Any],
) -> tuple[int | None, dict[str, Any] | None]:
    tool = get_tool(tool_name)
    if tool is None:
        return None, None
    try:
        status, payload = tool.call(arguments)
    except Exception:
        return None, None
    return status, payload if isinstance(payload, dict) else None


def _area_summary_level_rank(level: str | None) -> int | None:
    if not isinstance(level, str):
        return None
    return AREA_SUMMARY_LEVEL_RANK.get(level)


def _resolve_area_from_hierarchy_chain(
    *,
    target_level: str,
    chain: list[dict[str, Any]] | None,
) -> dict[str, Any] | None:
    if not isinstance(chain, list):
        return None
    for entry in chain:
        if not isinstance(entry, dict):
            continue
        raw_level = entry.get("level")
        if not isinstance(raw_level, str):
            continue
        normalized_level = normalize_area_level(raw_level)
        if normalized_level != target_level:
            continue
        area_id = entry.get("id")
        if not isinstance(area_id, str) or not area_id.strip():
            continue
        area_name = entry.get("name")
        return {
            "id": area_id.strip().upper(),
            "level": target_level,
            "name": (
                area_name.strip()
                if isinstance(area_name, str) and area_name.strip()
                else area_id
            ),
            "hierarchy": chain,
        }
    return None


def _best_effort_area_geometry(area_id: str) -> dict[str, Any] | None:
    status, payload = _best_effort_call(
        "admin_lookup.area_geometry",
        {"tool": "admin_lookup.area_geometry", "id": area_id, "includeGeometry": False},
    )
    if status != 200 or not isinstance(payload, dict):
        return None
    return payload


def _best_effort_reverse_hierarchy(area_id: str) -> list[dict[str, Any]] | None:
    status, payload = _best_effort_call(
        "admin_lookup.reverse_hierarchy",
        {"tool": "admin_lookup.reverse_hierarchy", "id": area_id},
    )
    if status != 200 or not isinstance(payload, dict):
        return None
    chain = payload.get("chain")
    return chain if isinstance(chain, list) else None


def _best_effort_inventory(
    *,
    bbox: list[float] | None,
    response_mode: str,
) -> dict[str, Any] | None:
    if not isinstance(bbox, list) or len(bbox) != 4:
        return None
    status, payload = _best_effort_call(
        "os_map.inventory",
        {
            "tool": "os_map.inventory",
            "bbox": bbox,
            "layers": ["uprns", "buildings"],
            "responseMode": response_mode,
        },
    )
    if status != 200 or not isinstance(payload, dict):
        return None
    return payload


def _best_effort_population_summary(area_id: str) -> dict[str, Any] | None:
    population_specs = curated_profile_dataset_specs(area_id, ["population"])
    if not population_specs:
        return None
    spec = population_specs[0]
    status, payload = _best_effort_call(
        "nomis.query",
        {
            "tool": "nomis.query",
            "dataset": spec["dataset"],
            "params": spec["params"],
        },
    )
    if status != 200 or not isinstance(payload, dict):
        return None
    value = _extract_numeric_value(payload.get("data"))
    result = {
        "category": "population",
        "dataset": spec["dataset"],
        "datasetLabel": spec["datasetLabel"],
        "params": spec["params"],
    }
    if value is not None:
        result["value"] = value
    dataset_summary = payload.get("datasetSummary")
    if isinstance(dataset_summary, dict):
        result["datasetSummary"] = dataset_summary
    if isinstance(payload.get("hints"), list):
        result["hints"] = payload.get("hints")
    if isinstance(payload.get("queryAdjusted"), dict):
        result["queryAdjusted"] = payload.get("queryAdjusted")
    return result


def _area_summary(payload: dict[str, Any]) -> ToolResult:
    area_id_raw = payload.get("id")
    postcode_raw = payload.get("postcode")
    uprn_raw = payload.get("uprn")

    normalized_identifier_values = []
    for value in (area_id_raw, postcode_raw, uprn_raw):
        if isinstance(value, str):
            if value.strip():
                normalized_identifier_values.append(value)
        elif value is not None:
            normalized_identifier_values.append(value)

    if len(normalized_identifier_values) > 1:
        return _error("Provide only one of: id, postcode, uprn")

    derivation_mode, parse_error = _parse_derivation_mode(payload)
    if parse_error is not None:
        return parse_error
    assert derivation_mode is not None

    target_level, target_level_error = _parse_area_summary_level(payload.get("targetLevel"))
    if target_level_error is not None:
        return target_level_error

    inventory_response_mode, inventory_mode_error = _parse_response_mode(
        payload.get("inventoryResponseMode")
    )
    if inventory_mode_error is not None:
        return inventory_mode_error

    profile_categories, profile_categories_error = _parse_profile_categories(
        payload.get("profileCategories")
    )
    if profile_categories_error is not None:
        return profile_categories_error

    include_inventory = payload.get("includeInventory", True)
    if not isinstance(include_inventory, bool):
        return _error("includeInventory must be a boolean")
    include_population = payload.get("includePopulation", True)
    if not isinstance(include_population, bool):
        return _error("includePopulation must be a boolean")
    include_profile_datasets = payload.get("includeProfileDatasets", True)
    if not isinstance(include_profile_datasets, bool):
        return _error("includeProfileDatasets must be a boolean")

    anchor_type: str | None = None
    anchor_value: str | None = None
    cache_result: Any | None = None
    direct_anchor_level: str | None = None
    hierarchy_chain: list[dict[str, Any]] | None = None
    cache = ONSGeoCache.from_settings()

    if isinstance(postcode_raw, str) and postcode_raw.strip():
        normalized_postcode = normalize_postcode(postcode_raw)
        if normalized_postcode is None:
            return _error("Invalid UK postcode")
        if not cache.available():
            return _error(
                "ONS geo cache is unavailable. Run scripts/ons_geo_cache_refresh.py.",
                code="CACHE_UNAVAILABLE",
                status=503,
            )
        try:
            cache_result = cache.lookup(
                key_type="postcode",
                key_value=normalized_postcode,
                derivation_mode=derivation_mode,
            )
        except ONSGeoCacheReadError as exc:
            return _error(
                (
                    "ONS geo cache is unreadable. "
                    f"{exc} Run scripts/ons_geo_cache_refresh.py to rebuild the cache."
                ),
                code="CACHE_READ_ERROR",
                status=503,
            )
        if cache_result is None:
            return _error(
                (
                    "No geography mapping found for postcode "
                    f"{normalized_postcode} in {derivation_mode} mode."
                ),
                code="NOT_FOUND",
                status=404,
            )
        anchor_type = "postcode"
        anchor_value = normalized_postcode
        if target_level is None:
            target_level = "OA"
    elif isinstance(uprn_raw, str) and uprn_raw.strip():
        normalized_uprn = normalize_uprn(uprn_raw)
        if normalized_uprn is None:
            return _error("uprn must be a numeric string")
        if not cache.available():
            return _error(
                "ONS geo cache is unavailable. Run scripts/ons_geo_cache_refresh.py.",
                code="CACHE_UNAVAILABLE",
                status=503,
            )
        try:
            cache_result = cache.lookup(
                key_type="uprn",
                key_value=normalized_uprn,
                derivation_mode=derivation_mode,
            )
        except ONSGeoCacheReadError as exc:
            return _error(
                (
                    "ONS geo cache is unreadable. "
                    f"{exc} Run scripts/ons_geo_cache_refresh.py to rebuild the cache."
                ),
                code="CACHE_READ_ERROR",
                status=503,
            )
        if cache_result is None:
            return _error(
                f"No geography mapping found for uprn {normalized_uprn} in {derivation_mode} mode.",
                code="NOT_FOUND",
                status=404,
            )
        anchor_type = "uprn"
        anchor_value = normalized_uprn
        if target_level is None:
            target_level = "OA"
    elif isinstance(area_id_raw, str) and area_id_raw.strip():
        area_id = area_id_raw.strip().upper()
        inferred_level = infer_area_level_from_code(area_id)
        if inferred_level is not None:
            direct_anchor_level = inferred_level
            if target_level is None:
                target_level = inferred_level
            else:
                inferred_rank = _area_summary_level_rank(inferred_level)
                target_rank = _area_summary_level_rank(target_level)
                if (
                    inferred_rank is not None
                    and target_rank is not None
                    and target_rank < inferred_rank
                ):
                    return _error(
                        f"id {area_id} implies level {inferred_level}, which cannot be "
                        f"narrowed to targetLevel={target_level}"
                    )
        elif target_level is None:
            return _error(
                f"Could not infer targetLevel from id {area_id}. Provide targetLevel explicitly."
            )
        else:
            direct_anchor_level = target_level
        anchor_type = "id"
        anchor_value = area_id
    else:
        if target_level is None:
            return _error("Provide one of: id, postcode, uprn")
        return _error(
            "Provide id, postcode, or uprn so the requested area can be "
            "resolved from the prompt context."
        )

    assert target_level is not None
    assert anchor_type is not None
    assert anchor_value is not None

    if cache_result is not None:
        area, area_error = _resolve_area_from_lookup(
            target_level=target_level,
            cache_result=cache_result,
        )
        if area_error is not None:
            return area_error
        assert area is not None
    else:
        area = {"id": anchor_value, "level": target_level, "name": anchor_value, "hierarchy": {}}
        if anchor_type == "id":
            hierarchy_chain = _best_effort_reverse_hierarchy(anchor_value)
            resolved_from_chain = _resolve_area_from_hierarchy_chain(
                target_level=target_level,
                chain=hierarchy_chain,
            )
            if direct_anchor_level is not None and target_level != direct_anchor_level:
                if resolved_from_chain is None:
                    return _error(
                        f"No {target_level} mapping found for area id {anchor_value}.",
                        code="NOT_FOUND",
                        status=404,
                    )
                area = resolved_from_chain
            elif resolved_from_chain is not None:
                area["name"] = resolved_from_chain["name"]
                area["hierarchy"] = resolved_from_chain["hierarchy"]

    geometry_payload = _best_effort_area_geometry(str(area["id"]))
    bbox = None
    if isinstance(geometry_payload, dict):
        bbox_raw = geometry_payload.get("bbox")
        if isinstance(bbox_raw, list) and len(bbox_raw) == 4:
            bbox = bbox_raw
        area_name = geometry_payload.get("name")
        if isinstance(area_name, str) and area_name.strip():
            area["name"] = area_name.strip()
        area_level = geometry_payload.get("level")
        if not isinstance(area_level, str):
            meta = geometry_payload.get("meta")
            if isinstance(meta, dict):
                area_level = meta.get("level")
        if isinstance(area_level, str) and area_level.strip():
            area["level"] = normalize_area_level(area_level) or area["level"]

    if not area.get("hierarchy") and isinstance(hierarchy_chain, list) and hierarchy_chain:
        area["hierarchy"] = hierarchy_chain
    if not area.get("hierarchy"):
        chain = _best_effort_reverse_hierarchy(str(area["id"]))
        if isinstance(chain, list) and chain:
            area["hierarchy"] = chain

    counts = None
    if cache.available():
        try:
            counts = cache.area_member_counts(
                area_code=str(area["id"]),
                area_level=str(area["level"]),
                derivation_mode=derivation_mode,
            )
        except ONSGeoCacheReadError:
            counts = None

    if anchor_type == "id":
        has_hierarchy = isinstance(area.get("hierarchy"), list) and bool(area["hierarchy"])
        has_nonzero_counts = isinstance(counts, dict) and any(
            int(value or 0) > 0 for value in counts.values()
        )
        if not has_nonzero_counts and geometry_payload is None and not has_hierarchy:
            return _error(
                f"No area found for id {anchor_value} at targetLevel {target_level}.",
                code="NOT_FOUND",
                status=404,
            )

    inventory = (
        _best_effort_inventory(bbox=bbox, response_mode=inventory_response_mode)
        if include_inventory
        else None
    )
    population = _best_effort_population_summary(str(area["id"])) if include_population else None
    profile_datasets = (
        curated_profile_dataset_specs(str(area["id"]), profile_categories)
        if include_profile_datasets
        else []
    )
    response_area = dict(area)
    response_area["bbox"] = bbox
    response_area["hierarchy"] = area.get("hierarchy", {})

    response: dict[str, Any] = {
        "input": {
            anchor_type: anchor_value,
            "targetLevel": target_level,
            "derivationMode": derivation_mode,
            "includeInventory": include_inventory,
            "inventoryResponseMode": inventory_response_mode,
        },
        "anchor": _build_anchor_summary(
            anchor_type=anchor_type,
            anchor_value=anchor_value,
            derivation_mode=derivation_mode,
            cache_result=cache_result,
        ),
        "area": response_area,
        "workflowProfileUri": _AREA_SUMMARY_WORKFLOW_URI,
        "guidance": [
            "Use ons_geo.area_summary for compact OA/LSOA/MSOA/parish/ward summaries.",
            "Prefer inventoryResponseMode='summary' or 'counts' for narrative "
            "summaries instead of raw map inventories.",
            "Use profileDatasets for deeper NOMIS follow-up queries by topic.",
        ],
        "provenance": {
            "source": "ons_geo_cache",
            "derivationMode": derivation_mode,
            "resolvedFrom": anchor_type,
        },
    }
    if counts is not None:
        response["counts"] = counts
    if inventory is not None:
        response["inventory"] = inventory
    if population is not None:
        response["population"] = population
    if profile_datasets:
        response["profileDatasets"] = profile_datasets
    return 200, response


def _by_postcode(payload: dict[str, Any]) -> ToolResult:
    postcode_raw = payload.get("postcode")
    if not isinstance(postcode_raw, str) or not postcode_raw.strip():
        return _error("postcode must be a non-empty string")
    derivation_mode, parse_error = _parse_derivation_mode(payload)
    if parse_error is not None:
        return parse_error
    assert derivation_mode is not None

    normalized_postcode = normalize_postcode(postcode_raw)
    if normalized_postcode is None:
        return _error("Invalid UK postcode")

    include_raw = bool(payload.get("includeRaw", False))
    if payload.get("includeRaw") is not None and not isinstance(payload.get("includeRaw"), bool):
        return _error("includeRaw must be a boolean")

    cache = ONSGeoCache.from_settings()
    if not cache.available():
        return _error(
            "ONS geo cache is unavailable. Run scripts/ons_geo_cache_refresh.py.",
            code="CACHE_UNAVAILABLE",
            status=503,
        )

    try:
        result = cache.lookup(
            key_type="postcode",
            key_value=normalized_postcode,
            derivation_mode=derivation_mode,
        )
    except ONSGeoCacheReadError as exc:
        return _error(
            (
                "ONS geo cache is unreadable. "
                f"{exc} Run scripts/ons_geo_cache_refresh.py to rebuild the cache."
            ),
            code="CACHE_READ_ERROR",
            status=503,
        )
    if result is None:
        return _error(
            (
                f"No geography mapping found for postcode {normalized_postcode} "
                f"in {derivation_mode} mode."
            ),
            code="NOT_FOUND",
            status=404,
        )
    return _build_lookup_response(
        lookup_key="postcode",
        normalized_key=normalized_postcode,
        derivation_mode=derivation_mode,
        cache_result=result,
        include_raw=include_raw,
    )


def _by_uprn(payload: dict[str, Any]) -> ToolResult:
    uprn_raw = payload.get("uprn")
    if not isinstance(uprn_raw, str) or not uprn_raw.strip():
        return _error("uprn must be a non-empty string")
    derivation_mode, parse_error = _parse_derivation_mode(payload)
    if parse_error is not None:
        return parse_error
    assert derivation_mode is not None

    normalized_uprn = normalize_uprn(uprn_raw)
    if normalized_uprn is None:
        return _error("uprn must be a numeric string")

    include_raw = bool(payload.get("includeRaw", False))
    if payload.get("includeRaw") is not None and not isinstance(payload.get("includeRaw"), bool):
        return _error("includeRaw must be a boolean")

    cache = ONSGeoCache.from_settings()
    if not cache.available():
        return _error(
            "ONS geo cache is unavailable. Run scripts/ons_geo_cache_refresh.py.",
            code="CACHE_UNAVAILABLE",
            status=503,
        )

    try:
        result = cache.lookup(
            key_type="uprn",
            key_value=normalized_uprn,
            derivation_mode=derivation_mode,
        )
    except ONSGeoCacheReadError as exc:
        return _error(
            (
                "ONS geo cache is unreadable. "
                f"{exc} Run scripts/ons_geo_cache_refresh.py to rebuild the cache."
            ),
            code="CACHE_READ_ERROR",
            status=503,
        )
    if result is None:
        return _error(
            f"No geography mapping found for uprn {normalized_uprn} in {derivation_mode} mode.",
            code="NOT_FOUND",
            status=404,
        )
    return _build_lookup_response(
        lookup_key="uprn",
        normalized_key=normalized_uprn,
        derivation_mode=derivation_mode,
        cache_result=result,
        include_raw=include_raw,
    )


def _cache_status(_payload: dict[str, Any]) -> ToolResult:
    cache = ONSGeoCache.from_settings()
    index = cache.load_index()
    products = index.get("products", [])
    support_products = index.get("supportProducts", [])
    product_count = len(products) if isinstance(products, list) else 0
    available = cache.available()
    performance = _cache_performance_from_index(available=available, index=index)
    status = "degraded" if performance.get("degraded") else "ready"
    return 200, {
        "available": available,
        "status": status,
        "cacheDir": str(cache.cache_dir),
        "dbPath": str(cache.db_path),
        "indexPath": str(cache.index_path),
        "version": index.get("version"),
        "generatedAt": index.get("generatedAt"),
        "productCount": product_count,
        "products": products if isinstance(products, list) else [],
        "supportProducts": support_products if isinstance(support_products, list) else [],
        "health": index.get("health", {}),
        "performance": performance,
        "reloadHint": (
            "Run scripts/ons_geo_cache_refresh.py to populate ONSPD/ONSUD/NSPL/NSUL "
            "plus CHD/RGC support datasets."
        ),
        "primaryDerivationMode": str(
            getattr(settings, "ONS_GEO_PRIMARY_DERIVATION", "exact") or "exact"
        ),
    }


def _release_audit(payload: dict[str, Any]) -> ToolResult:
    if not settings.ONS_LIVE_ENABLED:
        return _error(
            "ONS live mode is disabled. Set ONS_LIVE_ENABLED=true.",
            code="LIVE_DISABLED",
            status=503,
        )
    raw_timeout = payload.get("timeout", 30.0)
    if not isinstance(raw_timeout, (int, float)) or float(raw_timeout) <= 0:
        return _error("timeout must be a positive number")
    try:
        audit = build_release_audit(timeout=float(raw_timeout))
    except Exception as exc:
        return _error(
            f"ONS release audit failed: {exc}",
            code="UPSTREAM_ERROR",
            status=502,
        )
    return 200, audit


register(
    Tool(
        name="ons_geo.by_postcode",
        description=(
            "Lookup all cached geographies for a postcode using derivation mode "
            "(exact via ONSPD, best_fit via NSPL)."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "ons_geo.by_postcode"},
                "postcode": {"type": "string"},
                "derivationMode": {
                    "type": "string",
                    "enum": ["exact", "best_fit"],
                    "default": "exact",
                },
                "includeRaw": {"type": "boolean", "default": False},
            },
            "required": ["postcode"],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "query": {"type": "object"},
                "lookup": {"type": "object"},
                "geographies": {"type": "object"},
                "geographyCount": {"type": "integer"},
                "raw": {"type": "object"},
            },
            "required": ["query", "lookup", "geographies", "geographyCount"],
            "additionalProperties": True,
        },
        handler=_by_postcode,
    )
)

register(
    Tool(
        name="ons_geo.by_uprn",
        description=(
            "Lookup all cached geographies for a UPRN using derivation mode "
            "(exact via ONSUD, best_fit via NSUL)."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "ons_geo.by_uprn"},
                "uprn": {"type": "string"},
                "derivationMode": {
                    "type": "string",
                    "enum": ["exact", "best_fit"],
                    "default": "exact",
                },
                "includeRaw": {"type": "boolean", "default": False},
            },
            "required": ["uprn"],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "query": {"type": "object"},
                "lookup": {"type": "object"},
                "geographies": {"type": "object"},
                "geographyCount": {"type": "integer"},
                "raw": {"type": "object"},
            },
            "required": ["query", "lookup", "geographies", "geographyCount"],
            "additionalProperties": True,
        },
        handler=_by_uprn,
    )
)

register(
    Tool(
        name="ons_geo.area_summary",
        description=(
            "Resolve a compact OA/LSOA/MSOA/parish/ward/profile summary from an area code, "
            "postcode, or UPRN using cached ONS geographies, compact inventory counts, "
            "and curated NOMIS follow-up datasets."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "ons_geo.area_summary"},
                "id": {"type": "string"},
                "postcode": {"type": "string"},
                "uprn": {"type": "string"},
                "targetLevel": {
                    "type": "string",
                    "enum": sorted(AREA_LEVEL_COLUMN_MAP.keys()),
                },
                "derivationMode": {
                    "type": "string",
                    "enum": ["exact", "best_fit"],
                    "default": "exact",
                },
                "includeInventory": {"type": "boolean", "default": True},
                "inventoryResponseMode": {
                    "type": "string",
                    "enum": ["full", "summary", "counts"],
                    "default": "summary",
                },
                "includePopulation": {"type": "boolean", "default": True},
                "includeProfileDatasets": {"type": "boolean", "default": True},
                "profileCategories": {
                    "oneOf": [
                        {"type": "array", "items": {"type": "string"}, "minItems": 1},
                        {"type": "string", "minLength": 1},
                        {"type": "null"},
                    ]
                },
            },
            "required": [],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "input": {"type": "object"},
                "anchor": {"type": "object"},
                "area": {"type": "object"},
                "counts": {"type": "object"},
                "inventory": {"type": "object"},
                "population": {"type": "object"},
                "profileDatasets": {"type": "array", "items": {"type": "object"}},
                "workflowProfileUri": {"type": "string"},
                "guidance": {"type": "array", "items": {"type": "string"}},
                "provenance": {"type": "object"},
            },
            "required": ["input", "anchor", "area", "workflowProfileUri", "guidance", "provenance"],
            "additionalProperties": True,
        },
        handler=_area_summary,
    )
)

register(
    Tool(
        name="ons_geo.cache_status",
        description="Return cache/index status for ONS geography lookups (ONSPD/ONSUD/NSPL/NSUL).",
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "ons_geo.cache_status"},
            },
            "required": [],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "available": {"type": "boolean"},
                "cacheDir": {"type": "string"},
                "dbPath": {"type": "string"},
                "indexPath": {"type": "string"},
                "productCount": {"type": "integer"},
                "products": {"type": "array"},
            },
            "required": [
                "available",
                "cacheDir",
                "dbPath",
                "indexPath",
                "productCount",
                "products",
            ],
            "additionalProperties": True,
        },
        handler=_cache_status,
    )
)

register(
    Tool(
        name="ons_geo.release_audit",
        description=(
            "Audit ONS UPRN release freshness by combining AddressBase epoch schedule, "
            "Geoportal notices, Geoportal dataset discovery, and current package resolution."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "ons_geo.release_audit"},
                "timeout": {"type": "number", "minimum": 0.1, "default": 30.0},
            },
            "required": [],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "version": {"type": "string"},
                "addressBaseSchedule": {"type": "object"},
                "publisherNotices": {"type": "object"},
                "datasets": {"type": "array"},
            },
            "required": ["version", "addressBaseSchedule", "publisherNotices", "datasets"],
            "additionalProperties": True,
        },
        handler=_release_audit,
    )
)
