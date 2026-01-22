from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
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
from tools.ons_common import TTLCache
from tools.registry import Tool, register, ToolResult

_RESOURCE_PATH = Path(__file__).parent.parent / "resources" / "admin_boundaries.json"

DEFAULT_TIMEOUT = 5
DEFAULT_RETRIES = 3

# Lazy cache (sample fallback)
_BOUNDARIES_CACHE: list[dict[str, Any]] | None = None

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
                    return resp.status_code, {
                        "isError": True,
                        "code": "ADMIN_LOOKUP_API_ERROR",
                        "message": f"Admin lookup API error: {resp.text[:200]}",
                    }
                data = resp.json()
                self.cache.set(key, data)
                return 200, data
            except req_exc.SSLError as exc:
                return 501, {
                    "isError": True,
                    "code": "UPSTREAM_TLS_ERROR",
                    "message": str(exc),
                }
            except (req_exc.ConnectionError, req_exc.Timeout) as exc:
                last_exc = exc
                if attempt == DEFAULT_RETRIES:
                    return 501, {
                        "isError": True,
                        "code": "UPSTREAM_CONNECT_ERROR",
                        "message": str(exc),
                    }
                time.sleep(min(0.1 * (2 ** (attempt - 1)), 1.0))
            except Exception as exc:  # pragma: no cover
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


def _load_sample() -> list[dict[str, Any]]:
    global _BOUNDARIES_CACHE
    if _BOUNDARIES_CACHE is None:
        data = json.loads(_RESOURCE_PATH.read_text())
        _BOUNDARIES_CACHE = data.get("features", [])
    return _BOUNDARIES_CACHE or []


def _point_in_bbox(lat: float, lon: float, bbox: list[float]) -> bool:
    min_lon, min_lat, max_lon, max_lat = bbox
    return (min_lon <= lon <= max_lon) and (min_lat <= lat <= max_lat)


def _live_enabled() -> bool:
    return bool(getattr(settings, "ADMIN_LOOKUP_LIVE_ENABLED", True))


def _escape_like(text: str) -> str:
    return text.replace("'", "''")


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


def _live_find_by_name(text: str, limit: int) -> list[dict[str, Any]] | None:
    results: list[dict[str, Any]] = []
    needle = _escape_like(text.upper())
    for source in ADMIN_SOURCES:
        url = _service_query_url(source.service)
        where = f"UPPER({source.name_field}) LIKE '%{needle}%'"
        params = {
            "where": where,
            "outFields": f"{source.id_field},{source.name_field}",
            "returnGeometry": "false",
            "resultRecordCount": str(limit),
            "f": "json",
        }
        data = _fetch_arcgis(url, params)
        if data is None:
            return None
        for feat in data.get("features", []) or []:
            attrs = _extract_attrs(feat)
            area_id = attrs.get(source.id_field)
            if area_id is None:
                continue
            name = attrs.get(source.name_field) or area_id
            results.append({
                "id": str(area_id),
                "level": source.level,
                "name": str(name),
            })
            if len(results) >= limit:
                return results
    return results


def _live_containing_areas(lat: float, lon: float) -> list[dict[str, Any]] | None:
    matches: list[dict[str, Any]] = []
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
            return None
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
    return matches


def _live_area_geometry(area_id: str) -> tuple[list[float] | None, dict[str, Any] | None]:
    for source in ADMIN_SOURCES:
        url = _service_query_url(source.service)
        where = f"{source.id_field}='{_escape_like(area_id)}'"
        params = {
            "where": where,
            "returnExtentOnly": "true",
            "outSR": "4326",
            "f": "json",
        }
        data = _fetch_arcgis(url, params)
        if data is None:
            return None, {"code": "ERROR"}
        extent = data.get("extent")
        if not extent:
            continue
        bbox = [extent.get("xmin"), extent.get("ymin"), extent.get("xmax"), extent.get("ymax")]
        if any(v is None for v in bbox):
            continue
        meta = {"level": source.level, "source": "arcgis"}
        return [float(v) for v in bbox], meta
    return None, {"code": "NOT_FOUND"}


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


def _sample_containing_areas(lat: float, lon: float) -> ToolResult:
    feats = _load_sample()
    matches: list[dict[str, Any]] = []
    for feat in feats:
        bbox = feat.get("bbox")
        if not (isinstance(bbox, list) and len(bbox) == 4):
            continue
        if _point_in_bbox(lat, lon, bbox):
            matches.append({
                "id": feat.get("id"),
                "level": feat.get("level"),
                "name": feat.get("name"),
                "parent": feat.get("parent"),
            })
    if not matches:
        return 200, {"results": []}
    return 200, {"results": matches}


def _sample_reverse_hierarchy(area_id: str) -> ToolResult:
    feats = {f.get("id"): f for f in _load_sample()}
    if area_id not in feats:
        return 404, {"isError": True, "code": "NOT_FOUND", "message": "Area not found"}
    chain = []
    current = feats[area_id]
    while current:
        chain.append({
            "id": current.get("id"),
            "level": current.get("level"),
            "name": current.get("name"),
        })
        parent_id = current.get("parent")
        current = feats.get(parent_id) if parent_id else None
    return 200, {"chain": chain}


def _sample_area_geometry(area_id: str) -> ToolResult:
    for feat in _load_sample():
        if feat.get("id") == area_id:
            return 200, {"id": area_id, "bbox": feat.get("bbox")}
    return 404, {"isError": True, "code": "NOT_FOUND", "message": "Area not found"}


def _sample_find_by_name(text: str) -> ToolResult:
    matches = []
    for feat in _load_sample():
        name = str(feat.get("name", ""))
        if text in name.lower():
            matches.append({
                "id": feat.get("id"),
                "level": feat.get("level"),
                "name": name,
            })
    return 200, {"results": matches}


def _containing_areas(payload: dict[str, Any]) -> ToolResult:
    raw_lat = payload.get("lat")
    raw_lon = payload.get("lon")
    try:
        lat = float(raw_lat)
        lon = float(raw_lon)
    except Exception:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "lat/lon must be numeric"}
    if _live_enabled():
        live = _live_containing_areas(lat, lon)
        if live is not None:
            return 200, {"results": live, "live": True}
    return _sample_containing_areas(lat, lon)


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
        },
        "required": ["results"],
    },
    handler=_containing_areas,
))


def _reverse_hierarchy(payload: dict[str, Any]) -> ToolResult:
    area_id = str(payload.get("id", "")).strip()
    if not area_id:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "Missing id"}
    if _live_enabled():
        hit, err = _live_find_by_id(area_id)
        if err is None and hit:
            lat = hit.get("lat")
            lon = hit.get("lon")
            if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
                live = _live_containing_areas(float(lat), float(lon))
                if live is not None:
                    return 200, {"chain": live, "live": True}
            return 200, {"chain": [hit], "live": True}
        if err and err.get("code") == "NOT_FOUND":
            return 404, {"isError": True, "code": "NOT_FOUND", "message": "Area not found"}
    return _sample_reverse_hierarchy(area_id)


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
    if not area_id:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "Missing id"}
    if _live_enabled():
        bbox, meta = _live_area_geometry(area_id)
        if bbox is not None:
            return 200, {"id": area_id, "bbox": bbox, "live": True, "meta": meta}
        if meta and meta.get("code") == "NOT_FOUND":
            return 404, {"isError": True, "code": "NOT_FOUND", "message": "Area not found"}
    return _sample_area_geometry(area_id)


register(Tool(
    name="admin_lookup.area_geometry",
    description="Return bbox geometry for a given area id",
    input_schema={
        "type": "object",
        "properties": {
            "tool": {"type": "string", "const": "admin_lookup.area_geometry"},
            "id": {"type": "string"},
        },
        "required": ["id"],
        "additionalProperties": False,
    },
    output_schema={
        "type": "object",
        "properties": {"id": {"type": "string"}, "bbox": {"type": "array"}},
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
    if _live_enabled():
        live = _live_find_by_name(text, limit)
        if live is not None:
            return 200, {"results": live, "count": len(live), "live": True}
    sample = _sample_find_by_name(text.lower())
    if sample[1].get("results"):
        return sample
    return 200, {
        "results": [],
        "hints": {
            "note": (
                "No matches in bundled admin boundary sample. Try os_names.find, "
                "os_places.search, or the geography selector UI."
            ),
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
        },
        "required": ["text"],
        "additionalProperties": False,
    },
    output_schema={
        "type": "object",
        "properties": {"results": {"type": "array"}},
        "required": ["results"],
    },
    handler=_find_by_name,
))
