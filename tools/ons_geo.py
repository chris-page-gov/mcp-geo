from __future__ import annotations

from typing import Any

from server.config import settings
from server.ons_geo_cache import (
    ONSGeoCache,
    ONSGeoCacheReadError,
    extract_geography_fields,
    normalize_derivation_mode,
    normalize_postcode,
    normalize_uprn,
)
from tools.registry import Tool, ToolResult, register


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
            "sourceName": cache_result.source_name,
            "cachedAt": cache_result.cached_at,
        },
        "geographies": geographies,
        "geographyCount": len(geographies),
        "provenance": {
            "source": "ons_geo_cache",
            "product": cache_result.product_id,
            "derivationMode": cache_result.derivation_mode,
        },
    }
    if include_raw:
        payload["raw"] = cache_result.row
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
    product_count = len(products) if isinstance(products, list) else 0
    available = cache.available()
    performance = _cache_performance(available=available, product_count=product_count)
    status = "degraded" if performance.get("degraded") else "ready"
    return 200, {
        "available": available,
        "status": status,
        "cacheDir": str(cache.cache_dir),
        "dbPath": str(cache.db_path),
        "indexPath": str(cache.index_path),
        "generatedAt": index.get("generatedAt"),
        "productCount": product_count,
        "products": products if isinstance(products, list) else [],
        "performance": performance,
        "reloadHint": "Run scripts/ons_geo_cache_refresh.py to populate ONSPD/ONSUD/NSPL/NSUL.",
        "primaryDerivationMode": str(
            getattr(settings, "ONS_GEO_PRIMARY_DERIVATION", "exact") or "exact"
        ),
    }


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
