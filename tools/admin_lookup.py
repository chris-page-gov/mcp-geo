from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any

try:
    import requests
    from requests import exceptions as req_exc
except ImportError:  # pragma: no cover - optional dependency fallback
    requests = None  # type: ignore[assignment]

    class _ReqExc:
        SSLError = Exception
        ConnectionError = Exception
        Timeout = Exception

    req_exc = _ReqExc()

from server.config import settings
from server.boundary_cache import get_boundary_cache, reset_boundary_cache
from server.error_taxonomy import classify_error
from server.logging import log_upstream_error
from tools.ons_common import TTLCache
from tools.registry import Tool, register, ToolResult

DEFAULT_TIMEOUT = 5
DEFAULT_RETRIES = 3

_DEFAULT_ARCGIS_BASE = "https://services1.arcgis.com/ESMARspQHYMw9BZ9/ArcGIS/rest/services"


@dataclass(frozen=True)
class AdminSource:
    level: str
    service: str
    id_field: str
    name_field: str
    lat_field: str | None = None
    lon_field: str | None = None


ADMIN_SOURCES: list[AdminSource] = [
    AdminSource(
        level="OA",
        service="Output_Areas_2021_EW_BGC_V2",
        id_field="OA21CD",
        name_field="OA21CD",
        lat_field="LAT",
        lon_field="LONG",
    ),
    AdminSource(
        level="LSOA",
        service="Lower_layer_Super_Output_Areas_December_2021_Boundaries_EW_BGC_V5",
        id_field="LSOA21CD",
        name_field="LSOA21NM",
        lat_field="LAT",
        lon_field="LONG",
    ),
    AdminSource(
        level="MSOA",
        service="Middle_layer_Super_Output_Areas_December_2021_Boundaries_EW_BGC_V3",
        id_field="MSOA21CD",
        name_field="MSOA21NM",
        lat_field="LAT",
        lon_field="LONG",
    ),
    AdminSource(
        level="WARD",
        service="Wards_December_2019_Boundaries_UK_BGC_2022",
        id_field="WD19CD",
        name_field="WD19NM",
        lat_field="LAT",
        lon_field="LONG",
    ),
    AdminSource(
        level="DISTRICT",
        service="Local_Authority_Districts_December_2017_Boundaries_GB_BGC_2022",
        id_field="LAD17CD",
        name_field="LAD17NM",
        lat_field="LAT",
        lon_field="LONG",
    ),
    AdminSource(
        level="COUNTY",
        service="Counties_and_Unitary_Authorities_April_2019_Generalised_Boundaries_EW_2022",
        id_field="ctyua19cd",
        name_field="ctyua19nm",
        lat_field="lat",
        lon_field="long",
    ),
    AdminSource(
        level="REGION",
        service="Regions_December_2019_General_Clipped_Boundaries_EN_2022",
        id_field="rgn19cd",
        name_field="rgn19nm",
        lat_field="lat",
        lon_field="long",
    ),
    AdminSource(
        level="NATION",
        service="Countries_Dec_2021_GB_BFC_2022",
        id_field="CTRY21CD",
        name_field="CTRY21NM",
        lat_field="LAT",
        lon_field="LONG",
    ),
]

LEVEL_ORDER = [source.level for source in ADMIN_SOURCES]
LEVEL_INDEX = {level: idx for idx, level in enumerate(LEVEL_ORDER)}

SEARCH_PRIORITY_LEVELS = [
    "WARD",
    "DISTRICT",
    "COUNTY",
    "REGION",
    "NATION",
    "MSOA",
    "LSOA",
    "OA",
]
SEARCH_PRIORITY_INDEX = {level: idx for idx, level in enumerate(SEARCH_PRIORITY_LEVELS)}
_MATCH_TYPES = {"contains", "starts_with", "exact"}


def _normalize_levels(value: Any) -> list[str] | None:
    if value is None:
        return None
    raw: list[str] = []
    if isinstance(value, str):
        raw = [part.strip() for part in value.split(",") if part.strip()]
    elif isinstance(value, list):
        raw = [str(item).strip() for item in value if item is not None]
    else:
        return None
    levels: list[str] = []
    for item in raw:
        upper = item.upper()
        if upper in LEVEL_INDEX:
            levels.append(upper)
    return levels or None


def _infer_levels_from_text(text: str) -> list[str] | None:
    lowered = text.lower()
    if "lsoa" in lowered:
        return ["LSOA"]
    if "msoa" in lowered:
        return ["MSOA"]
    if "oa" in lowered or "output area" in lowered:
        return ["OA"]
    if "ward" in lowered:
        return ["WARD"]
    if "district" in lowered or "borough" in lowered or "council" in lowered:
        return ["DISTRICT"]
    if "county" in lowered:
        return ["COUNTY"]
    if "region" in lowered:
        return ["REGION"]
    if "nation" in lowered or "country" in lowered:
        return ["NATION"]
    return None


def _ordered_sources(levels: list[str] | None) -> list[AdminSource]:
    sources = [source for source in ADMIN_SOURCES if not levels or source.level in levels]
    if not sources:
        return []
    if levels:
        order = {level: idx for idx, level in enumerate(levels)}
        return sorted(sources, key=lambda source: order.get(source.level, 999))
    return sorted(sources, key=lambda source: SEARCH_PRIORITY_INDEX.get(source.level, 999))


class _ArcGisClient:
    def __init__(self) -> None:
        ttl = float(getattr(settings, "ONS_CACHE_TTL", 60.0))
        size = int(getattr(settings, "ONS_CACHE_SIZE", 256))
        self.cache = TTLCache(maxsize=size, ttl=ttl)

    def _cache_key(self, url: str, params: dict[str, Any]) -> str:
        return json.dumps([url, params], sort_keys=True)

    def get_json(self, url: str, params: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        if requests is None:
            return 501, {
                "isError": True,
                "code": "MISSING_DEPENDENCY",
                "message": "requests is not installed",
            }
        key = self._cache_key(url, params)
        cached = self.cache.get(key)
        if cached is not None:
            return 200, cached
        last_exc: Exception | None = None
        for attempt in range(1, DEFAULT_RETRIES + 1):
            try:
                resp = requests.get(url, params=params, timeout=DEFAULT_TIMEOUT)
                if resp.status_code != 200:
                    resp_url = getattr(resp, "url", url)
                    log_upstream_error(
                        service="admin_lookup",
                        code="ADMIN_LOOKUP_API_ERROR",
                        status_code=resp.status_code,
                        url=resp_url,
                        params=params,
                        detail=resp.text[:200],
                        attempt=attempt,
                        error_category=classify_error("ADMIN_LOOKUP_API_ERROR"),
                    )
                    return resp.status_code, {
                        "isError": True,
                        "code": "ADMIN_LOOKUP_API_ERROR",
                        "message": f"Admin lookup API error: {resp.text[:200]}",
                    }
                data = resp.json()
                self.cache.set(key, data)
                return 200, data
            except req_exc.SSLError as exc:
                log_upstream_error(
                    service="admin_lookup",
                    code="UPSTREAM_TLS_ERROR",
                    url=url,
                    params=params,
                    detail=str(exc),
                    attempt=attempt,
                    error_category=classify_error("UPSTREAM_TLS_ERROR"),
                )
                return 501, {
                    "isError": True,
                    "code": "UPSTREAM_TLS_ERROR",
                    "message": str(exc),
                }
            except (req_exc.ConnectionError, req_exc.Timeout) as exc:
                last_exc = exc
                if attempt == DEFAULT_RETRIES:
                    log_upstream_error(
                        service="admin_lookup",
                        code="UPSTREAM_CONNECT_ERROR",
                        url=url,
                        params=params,
                        detail=str(exc),
                        attempt=attempt,
                        error_category=classify_error("UPSTREAM_CONNECT_ERROR"),
                    )
                    return 501, {
                        "isError": True,
                        "code": "UPSTREAM_CONNECT_ERROR",
                        "message": str(exc),
                    }
                time.sleep(min(0.1 * (2 ** (attempt - 1)), 1.0))
            except Exception as exc:  # pragma: no cover
                log_upstream_error(
                    service="admin_lookup",
                    code="INTEGRATION_ERROR",
                    url=url,
                    params=params,
                    detail=str(exc),
                    attempt=attempt,
                    error_category=classify_error("INTEGRATION_ERROR"),
                )
                return 500, {
                    "isError": True,
                    "code": "INTEGRATION_ERROR",
                    "message": str(exc),
                }
        return 501, {
            "isError": True,
            "code": "UPSTREAM_CONNECT_ERROR",
            "message": f"Failed after retries: {last_exc}",
        }


_ARCGIS_CLIENT = _ArcGisClient()


def _arcgis_base() -> str:
    base = getattr(settings, "ADMIN_LOOKUP_ARCGIS_BASE", "")
    return base or _DEFAULT_ARCGIS_BASE


def _service_query_url(service: str) -> str:
    return f"{_arcgis_base().rstrip('/')}/{service}/FeatureServer/0/query"


def _live_enabled() -> bool:
    return bool(getattr(settings, "ADMIN_LOOKUP_LIVE_ENABLED", True))


def _escape_like(text: str) -> str:
    return text.replace("'", "''")


def _bbox_from_geometry(geometry: dict[str, Any] | None) -> list[float] | None:
    if not geometry or not isinstance(geometry, dict):
        return None
    minx = miny = maxx = maxy = None

    def _update(x: Any, y: Any) -> None:
        nonlocal minx, miny, maxx, maxy
        try:
            xf = float(x)
            yf = float(y)
        except (TypeError, ValueError):
            return
        if minx is None or xf < minx:
            minx = xf
        if maxx is None or xf > maxx:
            maxx = xf
        if miny is None or yf < miny:
            miny = yf
        if maxy is None or yf > maxy:
            maxy = yf

    rings = geometry.get("rings")
    if isinstance(rings, list):
        for ring in rings:
            if not isinstance(ring, list):
                continue
            for coord in ring:
                if isinstance(coord, (list, tuple)) and len(coord) >= 2:
                    _update(coord[0], coord[1])

    paths = geometry.get("paths")
    if isinstance(paths, list):
        for path in paths:
            if not isinstance(path, list):
                continue
            for coord in path:
                if isinstance(coord, (list, tuple)) and len(coord) >= 2:
                    _update(coord[0], coord[1])

    points = geometry.get("points")
    if isinstance(points, list):
        for coord in points:
            if isinstance(coord, (list, tuple)) and len(coord) >= 2:
                _update(coord[0], coord[1])

    if "x" in geometry and "y" in geometry:
        _update(geometry.get("x"), geometry.get("y"))

    if minx is None or miny is None or maxx is None or maxy is None:
        return None
    return [minx, miny, maxx, maxy]


def _fetch_arcgis(url: str, params: dict[str, Any]) -> dict[str, Any] | None:
    status, data = _ARCGIS_CLIENT.get_json(url, params)
    if status != 200:
        return None
    if isinstance(data, dict) and data.get("error"):
        return None
    return data


def _extract_attrs(feature: dict[str, Any]) -> dict[str, Any]:
    attrs = feature.get("attributes")
    if isinstance(attrs, dict):
        return attrs
    return {}


def _build_match_clause(field: str, needle: str, match: str) -> str:
    if match == "exact":
        return f"UPPER({field}) = '{needle}'"
    if match == "starts_with":
        return f"UPPER({field}) LIKE '{needle}%'"
    return f"UPPER({field}) LIKE '%{needle}%'"


def _score_match(name: str, needle: str, level: str) -> tuple[int, int, int, str]:
    name_upper = name.upper()
    idx = name_upper.find(needle)
    if idx < 0:
        idx = 999
    level_rank = SEARCH_PRIORITY_INDEX.get(level, 999)
    return (idx, level_rank, len(name_upper), name_upper)


def _live_find_by_name(
    text: str,
    limit: int,
    *,
    levels: list[str] | None = None,
    match: str = "contains",
    limit_per_level: int | None = None,
) -> list[dict[str, Any]] | None:
    results: list[dict[str, Any]] = []
    failures = 0
    needle = _escape_like(text.upper())
    match = match if match in _MATCH_TYPES else "contains"
    sources = _ordered_sources(levels)
    if not sources:
        return []
    per_level = limit_per_level or min(limit, 10)
    if per_level < 1:
        per_level = 1
    seen_ids: set[str] = set()
    for source in sources:
        url = _service_query_url(source.service)
        where = _build_match_clause(source.name_field, needle, match)
        params = {
            "where": where,
            "outFields": f"{source.id_field},{source.name_field}",
            "returnGeometry": "false",
            "resultRecordCount": str(per_level),
            "f": "json",
        }
        data = _fetch_arcgis(url, params)
        if data is None:
            failures += 1
            continue
        for feat in data.get("features", []) or []:
            attrs = _extract_attrs(feat)
            area_id = attrs.get(source.id_field)
            if area_id is None:
                continue
            area_id_str = str(area_id)
            if area_id_str in seen_ids:
                continue
            name = attrs.get(source.name_field) or area_id_str
            seen_ids.add(area_id_str)
            results.append({
                "id": area_id_str,
                "level": source.level,
                "name": str(name),
            })
    if not results and failures == len(sources):
        return None
    results.sort(key=lambda item: _score_match(item.get("name", ""), needle, item.get("level", "")))
    return results[:limit]


def _live_containing_areas(
    lat: float, lon: float
) -> tuple[list[dict[str, Any]] | None, dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    failures: list[str] = []
    for source in ADMIN_SOURCES:
        url = _service_query_url(source.service)
        params = {
            "geometry": f"{lon},{lat}",
            "geometryType": "esriGeometryPoint",
            "inSR": "4326",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": f"{source.id_field},{source.name_field}",
            "returnGeometry": "false",
            "f": "json",
        }
        data = _fetch_arcgis(url, params)
        if data is None:
            failures.append(source.service)
            continue
        for feat in data.get("features", []) or []:
            attrs = _extract_attrs(feat)
            area_id = attrs.get(source.id_field)
            if area_id is None:
                continue
            name = attrs.get(source.name_field) or area_id
            matches.append({
                "id": str(area_id),
                "level": source.level,
                "name": str(name),
            })
    matches.sort(key=lambda item: LEVEL_INDEX.get(item.get("level", ""), 999))
    all_failed = len(failures) == len(ADMIN_SOURCES)
    meta: dict[str, Any] = {
        "source": "arcgis",
        "partial": bool(failures) and not all_failed,
        "failedSources": failures or None,
        "allFailed": all_failed,
    }
    if not matches and all_failed:
        return None, meta
    return matches, meta


def _live_area_geometry(
    area_id: str, include_geometry: bool = False
) -> tuple[list[float] | None, dict[str, Any] | None, dict[str, Any] | None]:
    failures: list[str] = []
    for source in ADMIN_SOURCES:
        url = _service_query_url(source.service)
        where = f"{source.id_field}='{_escape_like(area_id)}'"
        if include_geometry:
            params = {
                "where": where,
                "outFields": source.id_field,
                "returnGeometry": "true",
                "outSR": "4326",
                "f": "json",
            }
            data = _fetch_arcgis(url, params)
            if data is None:
                failures.append(source.service)
                continue
            features = data.get("features", []) or []
            if not features:
                continue
            geometry = features[0].get("geometry")
            extent = data.get("extent") or {}
            bbox = [
                extent.get("xmin"),
                extent.get("ymin"),
                extent.get("xmax"),
                extent.get("ymax"),
            ]
            meta = {
                "level": source.level,
                "source": "arcgis",
                "partial": bool(failures),
                "failedSources": failures or None,
                "allFailed": False,
            }
            geometry_missing = include_geometry and not geometry
            if any(v is None for v in bbox):
                bbox = _bbox_from_geometry(geometry)
            if geometry_missing:
                meta["geometryMissing"] = True
            return ([float(v) for v in bbox] if bbox else None), meta, geometry
        params = {
            "where": where,
            "returnExtentOnly": "true",
            "outSR": "4326",
            "f": "json",
        }
        data = _fetch_arcgis(url, params)
        if data is None:
            failures.append(source.service)
            continue
        extent = data.get("extent")
        if not extent:
            continue
        bbox = [extent.get("xmin"), extent.get("ymin"), extent.get("xmax"), extent.get("ymax")]
        if any(v is None for v in bbox):
            continue
        meta = {
            "level": source.level,
            "source": "arcgis",
            "partial": bool(failures),
            "failedSources": failures or None,
            "allFailed": False,
        }
        if include_geometry:
            meta["geometryMissing"] = True
        return [float(v) for v in bbox], meta, None
    if len(failures) == len(ADMIN_SOURCES):
        return None, {"code": "ERROR", "allFailed": True, "failedSources": failures}, None
    return None, {"code": "NOT_FOUND"}, None


def _live_find_by_id(area_id: str) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    for source in ADMIN_SOURCES:
        url = _service_query_url(source.service)
        fields = [source.id_field, source.name_field]
        if source.lat_field:
            fields.append(source.lat_field)
        if source.lon_field:
            fields.append(source.lon_field)
        params = {
            "where": f"{source.id_field}='{_escape_like(area_id)}'",
            "outFields": ",".join(fields),
            "returnGeometry": "false",
            "f": "json",
        }
        data = _fetch_arcgis(url, params)
        if data is None:
            return None, {"code": "ERROR"}
        features = data.get("features", []) or []
        if not features:
            continue
        attrs = _extract_attrs(features[0])
        name = attrs.get(source.name_field) or area_id
        return {
            "id": area_id,
            "level": source.level,
            "name": str(name),
            "lat": attrs.get(source.lat_field) if source.lat_field else None,
            "lon": attrs.get(source.lon_field) if source.lon_field else None,
        }, None
    return None, {"code": "NOT_FOUND"}


def _containing_areas(payload: dict[str, Any]) -> ToolResult:
    raw_lat = payload.get("lat")
    raw_lon = payload.get("lon")
    try:
        lat = float(raw_lat)
        lon = float(raw_lon)
    except Exception:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "lat/lon must be numeric"}
    cache = get_boundary_cache()
    if cache:
        cached = cache.containing_areas(lat, lon)
        if cached is not None:
            cached.sort(key=lambda item: LEVEL_INDEX.get(item.get("level", ""), 999))
            return 200, {
                "results": cached,
                "live": False,
                "meta": {"source": "cache", "fallback": True},
            }
    if not _live_enabled():
        return 501, {
            "isError": True,
            "code": "LIVE_DISABLED",
            "message": "Admin lookup live mode is disabled. Set ADMIN_LOOKUP_LIVE_ENABLED=true.",
        }
    live, meta = _live_containing_areas(lat, lon)
    if live is None:
        return 502, {
            "isError": True,
            "code": "ADMIN_LOOKUP_API_ERROR",
            "message": "Admin lookup live query failed (all sources failed).",
            "meta": meta,
        }
    return 200, {"results": live, "live": True, "meta": meta}


register(Tool(
    name="admin_lookup.containing_areas",
    description="Return containing administrative areas for a point (lat/lon)",
    input_schema={
        "type": "object",
        "properties": {
            "tool": {"type": "string", "const": "admin_lookup.containing_areas"},
            "lat": {"type": "number"},
            "lon": {"type": "number"},
        },
        "required": ["lat", "lon"],
        "additionalProperties": False,
    },
    output_schema={
        "type": "object",
        "properties": {
            "results": {"type": "array", "items": {"type": "object"}},
            "live": {"type": "boolean"},
            "meta": {"type": "object"},
        },
        "required": ["results"],
    },
    handler=_containing_areas,
))


def _reverse_hierarchy(payload: dict[str, Any]) -> ToolResult:
    area_id = str(payload.get("id", "")).strip()
    if not area_id:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "Missing id"}
    cache = get_boundary_cache()
    if cache:
        hit = cache.find_by_id(area_id)
        if hit:
            lat = hit.get("lat")
            lon = hit.get("lon")
            if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
                cached_chain = cache.containing_areas(float(lat), float(lon))
                if cached_chain is not None:
                    cached_chain.sort(
                        key=lambda item: LEVEL_INDEX.get(item.get("level", ""), 999)
                    )
                    return 200, {
                        "chain": cached_chain,
                        "live": False,
                        "meta": {"source": "cache", "fallback": True},
                    }
            return 200, {"chain": [hit], "live": False, "meta": {"source": "cache", "fallback": True}}
    if not _live_enabled():
        return 501, {
            "isError": True,
            "code": "LIVE_DISABLED",
            "message": "Admin lookup live mode is disabled. Set ADMIN_LOOKUP_LIVE_ENABLED=true.",
        }
    hit, err = _live_find_by_id(area_id)
    if err is None and hit:
        lat = hit.get("lat")
        lon = hit.get("lon")
        if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
            live, meta = _live_containing_areas(float(lat), float(lon))
            if live is not None:
                return 200, {"chain": live, "live": True, "meta": meta}
        return 200, {"chain": [hit], "live": True}
    if err and err.get("code") == "NOT_FOUND":
        return 404, {"isError": True, "code": "NOT_FOUND", "message": "Area not found"}
    return 502, {
        "isError": True,
        "code": "ADMIN_LOOKUP_API_ERROR",
        "message": "Admin lookup live query failed.",
    }


register(Tool(
    name="admin_lookup.reverse_hierarchy",
    description="Return ancestor chain for a given area id",
    input_schema={
        "type": "object",
        "properties": {
            "tool": {"type": "string", "const": "admin_lookup.reverse_hierarchy"},
            "id": {"type": "string"},
        },
        "required": ["id"],
        "additionalProperties": False,
    },
    output_schema={
        "type": "object",
        "properties": {"chain": {"type": "array"}},
        "required": ["chain"],
    },
    handler=_reverse_hierarchy,
))


def _area_geometry(payload: dict[str, Any]) -> ToolResult:
    area_id = str(payload.get("id", "")).strip()
    include_geometry = bool(payload.get("includeGeometry"))
    zoom_raw = payload.get("zoom")
    zoom: float | None = None
    if zoom_raw is not None:
        try:
            zoom = float(zoom_raw)
        except Exception:
            return 400, {
                "isError": True,
                "code": "INVALID_INPUT",
                "message": "zoom must be numeric",
            }
    if not area_id:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "Missing id"}
    cache = get_boundary_cache()
    if cache:
        cached = cache.area_geometry(area_id, include_geometry=include_geometry, zoom=zoom)
        if cached and cached.bbox is not None:
            payload: dict[str, Any] = {
                "id": area_id,
                "bbox": cached.bbox,
                "live": False,
                "meta": {**(cached.meta or {}), "geometryFormat": "geojson", "fallback": True},
            }
            if cached.name:
                payload["name"] = cached.name
            if cached.level:
                payload["level"] = cached.level
            if cached.geometry:
                payload["geometry"] = cached.geometry
            elif include_geometry:
                payload["meta"]["geometryMissing"] = True
            return 200, payload
        if not bool(getattr(settings, "BOUNDARY_CACHE_FALLBACK_LIVE", True)):
            return 404, {"isError": True, "code": "NOT_FOUND", "message": "Area not found"}
    if not _live_enabled():
        return 501, {
            "isError": True,
            "code": "LIVE_DISABLED",
            "message": "Admin lookup live mode is disabled. Set ADMIN_LOOKUP_LIVE_ENABLED=true.",
        }
    bbox, meta, geometry = _live_area_geometry(area_id, include_geometry=include_geometry)
    if bbox is not None:
        payload: dict[str, Any] = {"id": area_id, "bbox": bbox, "live": True, "meta": meta}
        payload["meta"]["geometryFormat"] = "arcgis"
        if geometry:
            payload["geometry"] = geometry
        elif include_geometry:
            payload["meta"]["geometryMissing"] = True
            log_upstream_error(
                service="admin_lookup",
                code="ADMIN_LOOKUP_GEOMETRY_MISSING",
                detail=f"Live geometry missing for {area_id}",
                error_category=classify_error("INTEGRATION_ERROR"),
            )
        return 200, payload
    if meta and meta.get("code") == "NOT_FOUND":
        return 404, {"isError": True, "code": "NOT_FOUND", "message": "Area not found"}
    if meta and meta.get("code") == "ERROR":
        return 502, {
            "isError": True,
            "code": "ADMIN_LOOKUP_API_ERROR",
            "message": "Admin lookup live query failed (all sources failed).",
            "meta": meta,
        }
    return 502, {
        "isError": True,
        "code": "ADMIN_LOOKUP_API_ERROR",
        "message": "Admin lookup live query failed.",
    }


register(Tool(
    name="admin_lookup.area_geometry",
    description="Return bbox geometry for a given area id",
    input_schema={
        "type": "object",
        "properties": {
            "tool": {"type": "string", "const": "admin_lookup.area_geometry"},
            "id": {"type": "string"},
            "includeGeometry": {"type": "boolean"},
            "zoom": {"type": "number"},
        },
        "required": ["id"],
        "additionalProperties": False,
    },
    output_schema={
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "bbox": {"type": "array"},
            "geometry": {"type": "object"},
            "name": {"type": "string"},
            "level": {"type": "string"},
            "live": {"type": "boolean"},
            "meta": {"type": "object"},
        },
        "required": ["id", "bbox"],
    },
    handler=_area_geometry,
))


def _find_by_name(payload: dict[str, Any]) -> ToolResult:
    text = str(payload.get("text", "")).strip()
    if not text:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "Missing text"}
    limit = payload.get("limit", 25)
    if not isinstance(limit, int) or limit < 1:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "limit must be >= 1"}
    match = payload.get("match") or payload.get("matchType") or "contains"
    if not isinstance(match, str):
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "match must be a string"}
    levels = _normalize_levels(payload.get("levels")) or _normalize_levels(payload.get("level"))
    if levels is None:
        levels = _infer_levels_from_text(text)
    limit_per_level = payload.get("limitPerLevel")
    if limit_per_level is not None:
        if not isinstance(limit_per_level, int) or limit_per_level < 1:
            return 400, {
                "isError": True,
                "code": "INVALID_INPUT",
                "message": "limitPerLevel must be >= 1",
            }
    if not _live_enabled():
        return 501, {
            "isError": True,
            "code": "LIVE_DISABLED",
            "message": "Admin lookup live mode is disabled. Set ADMIN_LOOKUP_LIVE_ENABLED=true.",
        }
    live = _live_find_by_name(
        text,
        limit,
        levels=levels,
        match=match,
        limit_per_level=limit_per_level,
    )
    if live is None:
        return 502, {
            "isError": True,
            "code": "ADMIN_LOOKUP_API_ERROR",
            "message": "Admin lookup live query failed.",
        }
    return 200, {
        "results": live,
        "count": len(live),
        "live": True,
        "meta": {
            "match": match,
            "levels": levels,
            "limitPerLevel": limit_per_level,
        },
    }


register(Tool(
    name="admin_lookup.find_by_name",
    description="Substring case-insensitive search by area name",
    input_schema={
        "type": "object",
        "properties": {
            "tool": {"type": "string", "const": "admin_lookup.find_by_name"},
            "text": {"type": "string"},
            "limit": {"type": "integer", "minimum": 1, "maximum": 200},
            "level": {"type": "string", "description": "Optional single level (WARD/LSOA/etc)."},
            "levels": {"type": "array", "items": {"type": "string"}},
            "match": {"type": "string", "enum": ["contains", "starts_with", "exact"]},
            "limitPerLevel": {"type": "integer", "minimum": 1, "maximum": 200},
        },
        "required": ["text"],
        "additionalProperties": False,
    },
    output_schema={
        "type": "object",
        "properties": {
            "results": {"type": "array"},
            "count": {"type": "integer"},
            "live": {"type": "boolean"},
            "meta": {"type": "object"},
        },
        "required": ["results"],
    },
    handler=_find_by_name,
))


def _cache_status(payload: dict[str, Any]) -> ToolResult:
    refresh = bool(payload.get("refresh"))
    if refresh:
        reset_boundary_cache()
    cache = get_boundary_cache()
    configured = bool(getattr(settings, "BOUNDARY_CACHE_ENABLED", False))
    dsn_set = bool(getattr(settings, "BOUNDARY_CACHE_DSN", ""))
    if not cache:
        return 200, {
            "enabled": False,
            "configured": configured,
            "dsnSet": dsn_set,
            "reloadHint": "Run scripts/boundary_cache_ingest.py to populate PostGIS.",
        }
    status = cache.status()
    if status is None:
        return 502, {
            "isError": True,
            "code": "BOUNDARY_CACHE_ERROR",
            "message": "Boundary cache status query failed.",
        }
    status["configured"] = configured
    status["dsnSet"] = dsn_set
    status["reloadHint"] = "Run scripts/boundary_cache_ingest.py to populate PostGIS."
    return 200, status


register(Tool(
    name="admin_lookup.get_cache_status",
    description="Return boundary cache status (levels, datasets, counts).",
    input_schema={
        "type": "object",
        "properties": {
            "tool": {"type": "string", "const": "admin_lookup.get_cache_status"},
            "refresh": {"type": "boolean"},
        },
        "additionalProperties": False,
    },
    output_schema={
        "type": "object",
        "properties": {
            "enabled": {"type": "boolean"},
            "configured": {"type": "boolean"},
            "dsnSet": {"type": "boolean"},
            "total": {"type": "integer"},
            "geomCount": {"type": "integer"},
            "levels": {"type": "array"},
            "datasets": {"type": "array"},
            "reloadHint": {"type": "string"},
        },
        "required": ["enabled"],
    },
    handler=_cache_status,
))


def _cache_search(payload: dict[str, Any]) -> ToolResult:
    query = str(payload.get("query", "")).strip() or None
    level = str(payload.get("level", "")).strip() or None
    limit = payload.get("limit", 25)
    if not isinstance(limit, int) or limit < 1 or limit > 200:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "limit must be 1-200"}
    fallback_live = payload.get("fallbackLive", True)
    if not isinstance(fallback_live, bool):
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "fallbackLive must be a boolean",
        }
    include_geometry = bool(payload.get("includeGeometry"))
    cache = get_boundary_cache()
    if not cache:
        if fallback_live and _live_enabled() and query:
            live = _live_find_by_name(query, limit, levels=_normalize_levels(level), match="contains")
            if live is None:
                return 502, {
                    "isError": True,
                    "code": "ADMIN_LOOKUP_API_ERROR",
                    "message": "Boundary cache unavailable and live lookup failed.",
                }
            return 200, {
                "results": live,
                "count": len(live),
                "live": True,
                "meta": {
                    "source": "arcgis",
                    "fallback": True,
                    "cache": "disabled",
                    "query": query,
                    "level": level,
                    "limit": limit,
                },
            }
        return 501, {
            "isError": True,
            "code": "BOUNDARY_CACHE_DISABLED",
            "message": "Boundary cache is not enabled.",
        }
    results = cache.search(query=query, level=level, limit=limit, include_geometry=include_geometry)
    if results is None:
        if fallback_live and _live_enabled() and query:
            live = _live_find_by_name(query, limit, levels=_normalize_levels(level), match="contains")
            if live is None:
                return 502, {
                    "isError": True,
                    "code": "ADMIN_LOOKUP_API_ERROR",
                    "message": "Boundary cache failed and live lookup failed.",
                }
            return 200, {
                "results": live,
                "count": len(live),
                "live": True,
                "meta": {
                    "source": "arcgis",
                    "fallback": True,
                    "cacheError": True,
                    "query": query,
                    "level": level,
                    "limit": limit,
                },
            }
        return 502, {
            "isError": True,
            "code": "BOUNDARY_CACHE_ERROR",
            "message": "Boundary cache search failed.",
        }
    return 200, {
        "results": results,
        "count": len(results),
        "live": False,
        "meta": {
            "query": query,
            "level": level,
            "limit": limit,
            "includeGeometry": include_geometry,
        },
    }


register(Tool(
    name="admin_lookup.search_cache",
    description="Search the boundary cache by id/name/level.",
    input_schema={
        "type": "object",
        "properties": {
            "tool": {"type": "string", "const": "admin_lookup.search_cache"},
            "query": {"type": "string"},
            "level": {"type": "string"},
            "limit": {"type": "integer", "minimum": 1, "maximum": 200},
            "includeGeometry": {"type": "boolean"},
            "fallbackLive": {
                "type": "boolean",
                "description": "Fallback to live lookup if cache unavailable.",
            },
        },
        "additionalProperties": False,
    },
    output_schema={
        "type": "object",
        "properties": {
            "results": {"type": "array"},
            "count": {"type": "integer"},
            "live": {"type": "boolean"},
            "meta": {"type": "object"},
        },
        "required": ["results"],
    },
    handler=_cache_search,
))
