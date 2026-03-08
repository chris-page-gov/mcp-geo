from __future__ import annotations

import csv
import json
import sqlite3
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Iterable

from server.config import settings
from server.ons_geo_cache import ONSGeoCache, normalize_postcode, normalize_uprn
from tools.registry import Tool, ToolResult, get as get_tool, register

_REPO_ROOT = Path(__file__).resolve().parents[1]
_EXPORTS_DIR = _REPO_ROOT / "data" / "exports"
_OS_EXPORTS_DIR = _REPO_ROOT / "data" / "os_exports"
_OS_EXPORT_JOBS_DIR = _OS_EXPORTS_DIR / "jobs"

# Base collection ids (without numeric suffix). We resolve to the latest available version
# via `os_features.collections` when needed.
_DEFAULT_COLLECTION_BASES: dict[str, str] = {
    "buildings": "bld-fts-buildingpart",
    "road_links": "trn-ntwk-roadlink",
    "path_links": "trn-ntwk-pathlink",
}

_DEFAULT_LIMITS: dict[str, int] = {
    "uprns": 100,
    "buildings": 100,
    "road_links": 100,
    "path_links": 100,
}

_MAX_LIMIT = 500

_NGD_COLLECTION_CACHE_TTL_SECONDS = 3600.0
_NGD_COLLECTION_CACHE: dict[str, Any] = {"stored_at": 0.0, "latest_by_base": {}}

_GSS_LEVEL_TO_COLUMN: dict[str, tuple[str, str | None]] = {
    "OA": ("oa_code", "selected_by_oa"),
    "LSOA": ("lsoa_code", "selected_by_lsoa"),
    "MSOA": ("msoa_code", "selected_by_msoa"),
    "LAD": ("lad_code", None),
}

_MEMBERSHIP_COLUMNS = [
    "selected_by_oa",
    "selected_by_lsoa",
    "selected_by_msoa",
    "selected_by_postcode",
    "selected_by_uprn",
    "selected_by_polygon",
]

_CSV_COLUMNS_CANONICAL_DEFAULT = [
    "uprn",
    "postcode",
    "oa_code",
    "local_authority_name",
    "lsoa_code",
    "msoa_code",
    "lad_code",
]

_CSV_COLUMNS_DEFAULT = [
    *_CSV_COLUMNS_CANONICAL_DEFAULT,
    "selected_by_oa",
    "selected_by_lsoa",
    "selected_by_msoa",
    "selected_by_postcode",
    "selected_by_uprn",
    "selected_by_polygon",
]

_EXPORT_JOB_LOCK = threading.Lock()


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    tmp_path.write_text(text, encoding="utf-8")
    tmp_path.replace(path)


def _normalize_export_id(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    candidate = value.strip()
    if not candidate:
        return None
    try:
        return str(uuid.UUID(candidate))
    except ValueError:
        return None


def _parse_bbox(value: Any) -> list[float] | None:
    if not (isinstance(value, list) and len(value) == 4):
        return None
    try:
        min_lon, min_lat, max_lon, max_lat = [float(x) for x in value]
    except (TypeError, ValueError):
        return None
    if min_lon >= max_lon or min_lat >= max_lat:
        return None
    return [min_lon, min_lat, max_lon, max_lat]


def _parse_layers(value: Any) -> list[str] | None:
    if value is None:
        return None
    if isinstance(value, str):
        parts = [p.strip() for p in value.split(",") if p.strip()]
    elif isinstance(value, list):
        parts = [str(p).strip() for p in value if p is not None and str(p).strip()]
    else:
        return None
    allowed = {"uprns", "buildings", "road_links", "path_links"}
    out = [p for p in parts if p in allowed]
    return out or None


def _parse_limits(value: Any) -> dict[str, int]:
    limits: dict[str, int] = dict(_DEFAULT_LIMITS)
    if not isinstance(value, dict):
        return limits
    for key, raw in value.items():
        if key not in limits:
            continue
        try:
            parsed = int(raw)
        except (TypeError, ValueError):
            continue
        if parsed < 1:
            continue
        limits[key] = min(parsed, _MAX_LIMIT)
    return limits


def _parse_layer_tokens(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    out: dict[str, str] = {}
    for key, raw in value.items():
        if key not in {"buildings", "road_links", "path_links"}:
            continue
        if isinstance(raw, (int, float)):
            raw = str(int(raw))
        if isinstance(raw, str) and raw.strip():
            out[key] = raw.strip()
    return out


def _parse_bool_map(value: Any) -> dict[str, bool]:
    if not isinstance(value, dict):
        return {}
    out: dict[str, bool] = {}
    for key, raw in value.items():
        if key not in {"buildings", "road_links", "path_links"}:
            continue
        if isinstance(raw, bool):
            out[key] = raw
    return out


def _parse_collections_override(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    out: dict[str, str] = {}
    for key, raw in value.items():
        if key not in {"buildings", "road_links", "path_links"}:
            continue
        if isinstance(raw, str) and raw.strip():
            out[key] = raw.strip()
    return out


def _parse_selector_list(value: Any) -> list[dict[str, Any]] | None:
    if not isinstance(value, list):
        return None
    out: list[dict[str, Any]] = []
    for row in value:
        if not isinstance(row, dict):
            return None
        out.append(dict(row))
    return out


def _parse_uprn_list(value: Any) -> set[str] | None:
    if value is None:
        return set()
    if not isinstance(value, list):
        return None
    out: set[str] = set()
    for raw in value:
        if not isinstance(raw, str):
            return None
        normalized = normalize_uprn(raw)
        if normalized is None:
            return None
        out.add(normalized)
    return out


def _parse_selection_spec(value: Any) -> tuple[dict[str, Any] | None, str | None]:
    if not isinstance(value, dict):
        return None, "selectionSpec must be an object"
    selectors = _parse_selector_list(value.get("selectors", []))
    if selectors is None:
        return None, "selectionSpec.selectors must be an array of objects"

    uprn_overrides = value.get("uprnOverrides", {})
    if uprn_overrides is None:
        uprn_overrides = {}
    if not isinstance(uprn_overrides, dict):
        return None, "selectionSpec.uprnOverrides must be an object"

    include = _parse_uprn_list(uprn_overrides.get("include", []))
    if include is None:
        return None, "selectionSpec.uprnOverrides.include must be an array of numeric strings"

    exclude = _parse_uprn_list(uprn_overrides.get("exclude", []))
    if exclude is None:
        return None, "selectionSpec.uprnOverrides.exclude must be an array of numeric strings"

    return {
        "selectors": selectors,
        "uprnOverrides": {"include": sorted(include), "exclude": sorted(exclude)},
    }, None


def _normalize_export_format(value: Any) -> str:
    if not isinstance(value, str):
        return "csv"
    norm = value.strip().lower()
    return "csv" if norm != "json" else "json"


def _normalize_derivation_mode(value: Any) -> str:
    if not isinstance(value, str):
        return "exact"
    norm = value.strip().lower()
    return norm if norm in {"exact", "best_fit"} else "exact"


def _normalize_columns_config(value: Any) -> dict[str, Any]:
    default = {"defaultSet": "maplab_default_v1", "selectorMembership": True}
    if not isinstance(value, dict):
        return default
    default_set_raw = value.get("defaultSet")
    default_set = (
        str(default_set_raw).strip()
        if isinstance(default_set_raw, str) and default_set_raw.strip()
        else "maplab_default_v1"
    )
    if default_set != "maplab_default_v1":
        default_set = "maplab_default_v1"
    selector_membership = value.get("selectorMembership")
    if isinstance(selector_membership, bool):
        include_membership = selector_membership
    else:
        include_membership = True
    return {"defaultSet": default_set, "selectorMembership": include_membership}


def _csv_columns_from_config(value: Any) -> list[str]:
    config = _normalize_columns_config(value)
    if config.get("selectorMembership", True):
        return list(_CSV_COLUMNS_DEFAULT)
    return list(_CSV_COLUMNS_CANONICAL_DEFAULT)


def _sort_uprns(values: Iterable[str]) -> list[str]:
    def _key(value: str) -> tuple[int, str]:
        return (0, f"{int(value):020d}") if value.isdigit() else (1, value)

    return sorted(set(values), key=_key)


def _get_latest_ngd_collection_ids() -> dict[str, str]:
    """Return cached latest-by-base collection ids from `os_features.collections`."""
    now = time.time()
    cached = _NGD_COLLECTION_CACHE.get("latest_by_base")
    stored_at = float(_NGD_COLLECTION_CACHE.get("stored_at", 0.0) or 0.0)
    if isinstance(cached, dict) and cached and now - stored_at < _NGD_COLLECTION_CACHE_TTL_SECONDS:
        return {str(k): str(v) for k, v in cached.items() if isinstance(k, str) and isinstance(v, str)}

    collections_tool = get_tool("os_features.collections")
    if not collections_tool:
        return {}
    status, data = collections_tool.call({"tool": "os_features.collections"})
    if status != 200 or not isinstance(data, dict):
        return {}
    latest = data.get("latestByBaseId")
    if not isinstance(latest, dict):
        return {}
    normalized = {
        str(base): str(coll_id)
        for base, coll_id in latest.items()
        if isinstance(base, str) and isinstance(coll_id, str)
    }
    _NGD_COLLECTION_CACHE["stored_at"] = now
    _NGD_COLLECTION_CACHE["latest_by_base"] = normalized
    return normalized


def _resolve_collection_id(layer_id: str, overrides: dict[str, str]) -> str | None:
    override = overrides.get(layer_id)
    if override:
        return override
    base = _DEFAULT_COLLECTION_BASES.get(layer_id)
    if not base:
        return None
    latest = _get_latest_ngd_collection_ids()
    return latest.get(base) or base


def _inventory(payload: dict[str, Any]) -> ToolResult:
    """Return a bounded inventory for common map layers within a bbox.

    This tool is intended for UI clients to avoid orchestrating multiple OS calls themselves.
    It enforces per-layer limits and returns truncation flags so clients can apply progressive
    disclosure (aggregate at low zoom, drill down at high zoom).
    """
    bbox = _parse_bbox(payload.get("bbox"))
    if bbox is None:
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "bbox must be [minLon,minLat,maxLon,maxLat] with min < max",
        }

    layers = _parse_layers(payload.get("layers")) or ["uprns", "buildings", "road_links", "path_links"]
    limits = _parse_limits(payload.get("limits"))
    page_tokens = _parse_layer_tokens(payload.get("pageTokens"))
    include_geometry = _parse_bool_map(payload.get("includeGeometry"))
    collections_override = _parse_collections_override(payload.get("collections"))

    result_layers: dict[str, Any] = {}
    hints: list[str] = []

    if "uprns" in layers:
        tool = get_tool("os_places.within")
        if not tool:
            result_layers["uprns"] = {
                "isError": True,
                "code": "MISSING_TOOL",
                "message": "os_places.within not registered",
            }
        else:
            status, data = tool.call({"tool": "os_places.within", "bbox": bbox})
            if status != 200:
                result_layers["uprns"] = data
            else:
                raw_results = data.get("results") if isinstance(data, dict) else None
                if not isinstance(raw_results, list):
                    raw_results = []
                limit = limits.get("uprns", _DEFAULT_LIMITS["uprns"])
                truncated = len(raw_results) > limit
                result_layers["uprns"] = {
                    "results": raw_results[:limit],
                    "count": min(len(raw_results), limit),
                    "truncated": truncated,
                    "notes": (
                        ["UPRNs are sourced via OS Places bbox search; results may be truncated upstream."]
                        + (["Increase limits.uprns or zoom in for detail."] if truncated else [])
                    ),
                }
                if isinstance(data, dict) and isinstance(data.get("provenance"), dict):
                    result_layers["uprns"]["provenance"] = data.get("provenance")

    def _fetch_features(layer_id: str) -> None:
        if layer_id not in layers:
            return
        tool = get_tool("os_features.query")
        if not tool:
            result_layers[layer_id] = {
                "isError": True,
                "code": "MISSING_TOOL",
                "message": "os_features.query not registered",
            }
            return
        collection_id = _resolve_collection_id(layer_id, collections_override)
        if not collection_id:
            result_layers[layer_id] = {
                "isError": True,
                "code": "INVALID_INPUT",
                "message": f"No default collection mapping for layer '{layer_id}'.",
            }
            return
        limit = limits.get(layer_id, _DEFAULT_LIMITS[layer_id])
        include_geom = include_geometry.get(layer_id, True)
        req: dict[str, Any] = {
            "tool": "os_features.query",
            "collection": collection_id,
            "bbox": bbox,
            "limit": limit,
            "includeGeometry": include_geom,
        }
        token = page_tokens.get(layer_id)
        if token:
            req["pageToken"] = token
        status, data = tool.call(req)
        if status != 200:
            result_layers[layer_id] = data
            return
        if not isinstance(data, dict):
            result_layers[layer_id] = {
                "isError": True,
                "code": "INTEGRATION_ERROR",
                "message": "Expected object response from os_features.query",
            }
            return
        result_layers[layer_id] = data
        # Cosmetic rename so UIs can treat layers uniformly.
        result_layers[layer_id].setdefault("layer", layer_id)
        if not include_geom:
            hints.append(f"{layer_id}: pass includeGeometry.{layer_id}=true to render on a map.")

    _fetch_features("buildings")
    _fetch_features("road_links")
    _fetch_features("path_links")

    return 200, {
        "bbox": bbox,
        "layers": result_layers,
        "requestedLayers": layers,
        "limits": {k: limits[k] for k in layers if k in limits},
        "hints": hints,
        "live": True,
    }


def _export_inventory_snapshot(payload: dict[str, Any]) -> ToolResult:
    bbox = _parse_bbox(payload.get("bbox"))
    if bbox is None:
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "bbox must be [minLon,minLat,maxLon,maxLat] with min < max",
        }
    name = payload.get("name")
    if name is not None and not isinstance(name, str):
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "name must be a string"}
    recipe = payload.get("recipe")
    if recipe is not None and not isinstance(recipe, dict):
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "recipe must be an object"}
    layers = _parse_layers(payload.get("layers"))
    limits = _parse_limits(payload.get("limits"))
    include_geometry = _parse_bool_map(payload.get("includeGeometry"))
    collections_override = _parse_collections_override(payload.get("collections"))

    inv_status, inv = _inventory(
        {
            "bbox": bbox,
            "layers": layers,
            "limits": limits,
            "includeGeometry": include_geometry,
            "collections": collections_override,
        }
    )
    if inv_status != 200:
        return inv_status, inv

    export_id = str(uuid.uuid4())
    _EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{export_id}.json"
    path = _EXPORTS_DIR / filename
    payload_out = {
        "exportId": export_id,
        "name": name or "",
        "createdAt": _now_iso(),
        "recipe": recipe or {},
        "inventory": inv,
    }
    _atomic_write_text(path, json.dumps(payload_out, ensure_ascii=True, indent=2) + "\n")
    uri = f"resource://mcp-geo/exports/{filename}"
    return 200, {
        "exportId": export_id,
        "uri": uri,
        "path": str(path),
        "notes": [
            "Use resources/read with the returned uri to fetch the exported JSON content.",
        ],
    }


def _os_export_uri(filename: str) -> str:
    return f"resource://mcp-geo/os-exports/{filename}"


def _job_status_uri(export_id: str) -> str:
    return _os_export_uri(f"jobs/{export_id}.json")


def _job_path(export_id: str) -> Path:
    normalized = _normalize_export_id(export_id)
    if not normalized:
        raise ValueError("invalid export id")
    root = _OS_EXPORT_JOBS_DIR.resolve()
    path = (root / f"{normalized}.json").resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError("invalid export id") from exc
    return path


def _read_job(export_id: str) -> dict[str, Any] | None:
    try:
        path = _job_path(export_id)
    except ValueError:
        return None
    if not path.exists() or not path.is_file():
        return None
    for _attempt in range(3):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            time.sleep(0.01)
            continue
        except Exception:
            return None
        return raw if isinstance(raw, dict) else None
    return None


def _write_job(job: dict[str, Any]) -> None:
    normalized = _normalize_export_id(job.get("exportId"))
    if not normalized:
        return
    _OS_EXPORT_JOBS_DIR.mkdir(parents=True, exist_ok=True)
    path = _job_path(normalized)
    _atomic_write_text(path, json.dumps(job, ensure_ascii=True, indent=2) + "\n")


def _membership_value(values: set[str]) -> str:
    if not values:
        return ""
    return "|".join(sorted(values))


def _fetch_index_rows_by_column(
    conn: sqlite3.Connection,
    *,
    derivation_mode: str,
    column: str,
    values: Iterable[str],
) -> dict[str, dict[str, Any]]:
    normalized_values = [str(v).strip() for v in values if str(v).strip()]
    if not normalized_values:
        return {}
    placeholders = ",".join("?" for _ in normalized_values)
    sql = (
        "SELECT uprn, postcode, oa_code, lsoa_code, msoa_code, lad_code, lad_name, postal_delivery "
        "FROM ons_geo_uprn_index "
        f"WHERE derivation_mode = ? AND {column} IN ({placeholders})"
    )
    params: list[Any] = [derivation_mode, *normalized_values]
    rows = conn.execute(sql, params).fetchall()
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        uprn = str(row["uprn"])
        out.setdefault(
            uprn,
            {
                "uprn": uprn,
                "postcode": row["postcode"],
                "oa_code": row["oa_code"],
                "lsoa_code": row["lsoa_code"],
                "msoa_code": row["msoa_code"],
                "lad_code": row["lad_code"],
                "lad_name": row["lad_name"],
                "postal_delivery": row["postal_delivery"],
            },
        )
    return out


def _fetch_index_rows_for_uprns(
    conn: sqlite3.Connection,
    *,
    derivation_mode: str,
    uprns: Iterable[str],
) -> dict[str, dict[str, Any]]:
    uprn_list = _sort_uprns(uprns)
    if not uprn_list:
        return {}

    out: dict[str, dict[str, Any]] = {}
    chunk = 800
    for start in range(0, len(uprn_list), chunk):
        part = uprn_list[start : start + chunk]
        placeholders = ",".join("?" for _ in part)
        sql = (
            "SELECT uprn, postcode, oa_code, lsoa_code, msoa_code, lad_code, lad_name, postal_delivery "
            "FROM ons_geo_uprn_index "
            f"WHERE derivation_mode = ? AND uprn IN ({placeholders})"
        )
        params: list[Any] = [derivation_mode, *part]
        rows = conn.execute(sql, params).fetchall()
        for row in rows:
            uprn = str(row["uprn"])
            out.setdefault(
                uprn,
                {
                    "uprn": uprn,
                    "postcode": row["postcode"],
                    "oa_code": row["oa_code"],
                    "lsoa_code": row["lsoa_code"],
                    "msoa_code": row["msoa_code"],
                    "lad_code": row["lad_code"],
                    "lad_name": row["lad_name"],
                    "postal_delivery": row["postal_delivery"],
                },
            )
    return out


def _selector_membership_label(selector: dict[str, Any], fallback: str) -> str:
    selector_id = selector.get("id")
    if isinstance(selector_id, str) and selector_id.strip():
        return selector_id.strip()
    return fallback


def _resolve_polygon_selector(selector: dict[str, Any]) -> tuple[set[str], str | None]:
    geometry = selector.get("geometry")
    if not isinstance(geometry, dict):
        return set(), "polygon selector requires geometry"

    tool = get_tool("os_places.polygon")
    if not tool:
        return set(), "os_places.polygon not available for polygon selector"

    status, payload = tool.call({"tool": "os_places.polygon", "polygon": geometry, "limit": 50000})
    if status != 200:
        if isinstance(payload, dict):
            msg = str(payload.get("message") or payload.get("code") or "polygon lookup failed")
        else:
            msg = "polygon lookup failed"
        return set(), msg

    results = payload.get("results") if isinstance(payload, dict) else None
    if not isinstance(results, list):
        return set(), None

    uprns: set[str] = set()
    for row in results:
        if not isinstance(row, dict):
            continue
        raw = row.get("uprn")
        if isinstance(raw, str):
            normalized = normalize_uprn(raw)
            if normalized:
                uprns.add(normalized)
    return uprns, None


def _resolve_selection_rows(
    *,
    selection_spec: dict[str, Any],
    derivation_mode: str,
    postal_delivery_only: bool,
) -> tuple[list[dict[str, Any]], dict[str, int], list[str]]:
    cache = ONSGeoCache.from_settings()
    if not cache.available():
        raise RuntimeError("ONS geo cache is unavailable. Run scripts/ons_geo_cache_refresh.py.")

    conn = sqlite3.connect(str(cache.db_path))
    conn.row_factory = sqlite3.Row

    warnings: list[str] = []
    include_uprns: set[str] = set()
    membership: dict[str, dict[str, set[str]]] = {}

    def _mark_membership(uprn: str, column: str, value: str) -> None:
        entry = membership.setdefault(uprn, {name: set() for name in _MEMBERSHIP_COLUMNS})
        if column in entry and value:
            entry[column].add(value)

    selectors = selection_spec.get("selectors", [])
    if not isinstance(selectors, list):
        selectors = []

    for idx, selector in enumerate(selectors):
        if not isinstance(selector, dict):
            warnings.append(f"selectors[{idx}] skipped: expected object")
            continue
        selector_type = str(selector.get("type") or "").strip().lower()
        if not selector_type:
            warnings.append(f"selectors[{idx}] skipped: missing type")
            continue

        if selector_type == "gss_code":
            level = str(selector.get("level") or "").strip().upper()
            code = str(selector.get("code") or "").strip().upper()
            mapping = _GSS_LEVEL_TO_COLUMN.get(level)
            if not mapping or not code:
                warnings.append(
                    f"selectors[{idx}] skipped: gss_code requires supported level and code"
                )
                continue
            db_col, membership_col = mapping
            matches = _fetch_index_rows_by_column(
                conn,
                derivation_mode=derivation_mode,
                column=db_col,
                values=[code],
            )
            include_uprns.update(matches.keys())
            if membership_col:
                for uprn in matches:
                    _mark_membership(uprn, membership_col, code)
            continue

        if selector_type == "postcode":
            postcode_raw = selector.get("postcode")
            if not isinstance(postcode_raw, str):
                warnings.append(f"selectors[{idx}] skipped: postcode selector requires postcode")
                continue
            postcode = normalize_postcode(postcode_raw)
            if postcode is None:
                warnings.append(f"selectors[{idx}] skipped: invalid postcode")
                continue
            matches = _fetch_index_rows_by_column(
                conn,
                derivation_mode=derivation_mode,
                column="postcode",
                values=[postcode],
            )
            include_uprns.update(matches.keys())
            for uprn in matches:
                _mark_membership(uprn, "selected_by_postcode", postcode)
            continue

        if selector_type == "uprn":
            uprn_raw = selector.get("uprn")
            if not isinstance(uprn_raw, str):
                warnings.append(f"selectors[{idx}] skipped: uprn selector requires uprn")
                continue
            uprn = normalize_uprn(uprn_raw)
            if uprn is None:
                warnings.append(f"selectors[{idx}] skipped: invalid uprn")
                continue
            include_uprns.add(uprn)
            _mark_membership(
                uprn,
                "selected_by_uprn",
                _selector_membership_label(selector, uprn),
            )
            continue

        if selector_type == "polygon":
            matched, warning = _resolve_polygon_selector(selector)
            if warning:
                warnings.append(f"selectors[{idx}] polygon: {warning}")
                continue
            include_uprns.update(matched)
            label = _selector_membership_label(selector, f"polygon-{idx + 1}")
            for uprn in matched:
                _mark_membership(uprn, "selected_by_polygon", label)
            continue

        warnings.append(f"selectors[{idx}] skipped: unsupported selector type '{selector_type}'")

    uprn_overrides = selection_spec.get("uprnOverrides", {})
    include_overrides = uprn_overrides.get("include", []) if isinstance(uprn_overrides, dict) else []
    exclude_overrides = uprn_overrides.get("exclude", []) if isinstance(uprn_overrides, dict) else []

    for raw in include_overrides:
        if isinstance(raw, str):
            normalized = normalize_uprn(raw)
            if normalized:
                include_uprns.add(normalized)
                _mark_membership(normalized, "selected_by_uprn", normalized)

    exclusions: set[str] = set()
    for raw in exclude_overrides:
        if isinstance(raw, str):
            normalized = normalize_uprn(raw)
            if normalized:
                exclusions.add(normalized)

    include_uprns.difference_update(exclusions)

    indexed_rows = _fetch_index_rows_for_uprns(
        conn,
        derivation_mode=derivation_mode,
        uprns=include_uprns,
    )

    has_delivery_flags = any(
        row.get("postal_delivery") in {0, 1}
        for row in indexed_rows.values()
    )
    if postal_delivery_only:
        if has_delivery_flags:
            include_uprns = {
                uprn
                for uprn in include_uprns
                if indexed_rows.get(uprn, {}).get("postal_delivery") == 1
            }
            warnings.append("postalDeliveryOnly applied using indexed postal-delivery flags")
        else:
            warnings.append(
                "postalDeliveryOnly requested but delivery flags unavailable; export used best-effort fallback"
            )

    rows: list[dict[str, Any]] = []
    for uprn in _sort_uprns(include_uprns):
        data = indexed_rows.get(uprn, {})
        mem = membership.get(uprn, {name: set() for name in _MEMBERSHIP_COLUMNS})
        rows.append(
            {
                "uprn": uprn,
                "postcode": data.get("postcode") or "",
                "oa_code": data.get("oa_code") or "",
                "local_authority_name": data.get("lad_name") or "",
                "lsoa_code": data.get("lsoa_code") or "",
                "msoa_code": data.get("msoa_code") or "",
                "lad_code": data.get("lad_code") or "",
                "selected_by_oa": _membership_value(mem.get("selected_by_oa", set())),
                "selected_by_lsoa": _membership_value(mem.get("selected_by_lsoa", set())),
                "selected_by_msoa": _membership_value(mem.get("selected_by_msoa", set())),
                "selected_by_postcode": _membership_value(mem.get("selected_by_postcode", set())),
                "selected_by_uprn": _membership_value(mem.get("selected_by_uprn", set())),
                "selected_by_polygon": _membership_value(mem.get("selected_by_polygon", set())),
            }
        )

    conn.close()

    stats = {
        "resolvedUprnCount": len(rows),
        "selectorCount": len(selectors),
        "excludedCount": len(exclusions),
    }
    return rows, stats, warnings


def _write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    with tmp_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in columns})
    tmp_path.replace(path)


def _update_job(export_id: str, **updates: Any) -> dict[str, Any]:
    with _EXPORT_JOB_LOCK:
        current = _read_job(export_id) or {"exportId": export_id}
        current.update(updates)
        current["updatedAt"] = _now_iso()
        _write_job(current)
        return current


def _run_selection_export_job(export_id: str, payload: dict[str, Any]) -> None:
    _update_job(export_id, status="running")
    try:
        selection_spec, parse_error = _parse_selection_spec(payload.get("selectionSpec"))
        if parse_error or selection_spec is None:
            raise ValueError(parse_error or "invalid selectionSpec")

        filters = payload.get("filters", {})
        if filters is None:
            filters = {}
        if not isinstance(filters, dict):
            raise ValueError("filters must be an object")

        derivation_mode = _normalize_derivation_mode(payload.get("derivationMode"))
        columns_config = _normalize_columns_config(payload.get("columns"))
        output_columns = _csv_columns_from_config(columns_config)
        postal_delivery_only = bool(filters.get("postalDeliveryOnly", False))
        rows, stats, warnings = _resolve_selection_rows(
            selection_spec=selection_spec,
            derivation_mode=derivation_mode,
            postal_delivery_only=postal_delivery_only,
        )

        file_stem = f"maplab-selection-{export_id}"
        export_format = _normalize_export_format(payload.get("format"))
        if export_format == "json":
            filename = f"{file_stem}.json"
            out_path = _OS_EXPORTS_DIR / filename
            _atomic_write_text(
                out_path,
                json.dumps(
                    {
                        "exportId": export_id,
                        "createdAt": _now_iso(),
                        "selectionSpec": selection_spec,
                        "columns": columns_config,
                        "rows": rows,
                        "stats": stats,
                        "warnings": warnings,
                    },
                    ensure_ascii=True,
                    indent=2,
                )
                + "\n",
            )
        else:
            filename = f"{file_stem}.csv"
            out_path = _OS_EXPORTS_DIR / filename
            _write_csv(out_path, rows, output_columns)

        result_uri = _os_export_uri(filename)
        _update_job(
            export_id,
            status="completed",
            completedAt=_now_iso(),
            resultUri=result_uri,
            rowCount=len(rows),
            columns=columns_config,
            stats=stats,
            warnings=warnings,
            path=str(out_path),
        )
    except Exception as exc:  # pragma: no cover - guarded by tests via get_export status
        _update_job(
            export_id,
            status="failed",
            failedAt=_now_iso(),
            error={"message": str(exc), "code": "EXPORT_FAILED"},
        )


def _start_selection_export(payload: dict[str, Any]) -> ToolResult:
    selection_spec, parse_error = _parse_selection_spec(payload.get("selectionSpec"))
    if parse_error or selection_spec is None:
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": parse_error or "selectionSpec is required",
        }

    columns = payload.get("columns", {})
    if columns is not None and not isinstance(columns, dict):
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "columns must be an object"}
    filters = payload.get("filters", {})
    if filters is not None and not isinstance(filters, dict):
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "filters must be an object"}

    export_id = str(uuid.uuid4())
    created_at = _now_iso()
    job = {
        "exportId": export_id,
        "status": "queued",
        "exportType": "selection_uprn",
        "createdAt": created_at,
        "updatedAt": created_at,
        "statusUri": _job_status_uri(export_id),
        "resultUri": None,
        "request": {
            "selectionSpec": selection_spec,
            "format": _normalize_export_format(payload.get("format")),
            "columns": _normalize_columns_config(columns),
            "filters": filters or {"postalDeliveryOnly": False},
            "derivationMode": _normalize_derivation_mode(payload.get("derivationMode")),
        },
    }
    _write_job(job)

    worker = threading.Thread(
        target=_run_selection_export_job,
        kwargs={"export_id": export_id, "payload": dict(payload)},
        daemon=True,
        name=f"os-map-export-{export_id[:8]}",
    )
    worker.start()

    return 200, {
        "exportId": export_id,
        "status": "queued",
        "statusUri": _job_status_uri(export_id),
        "resultUri": None,
    }


def _export(payload: dict[str, Any]) -> ToolResult:
    export_type = str(payload.get("exportType") or "inventory_snapshot").strip().lower()
    if export_type == "selection_uprn":
        return _start_selection_export(payload)
    return _export_inventory_snapshot(payload)


def _get_export(payload: dict[str, Any]) -> ToolResult:
    export_id = payload.get("exportId")
    normalized = _normalize_export_id(export_id)
    if not normalized:
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "exportId must be a UUID string",
        }
    job = _read_job(normalized)
    if not job:
        return 404, {
            "isError": True,
            "code": "NOT_FOUND",
            "message": f"Export job not found for {normalized}",
        }
    job.setdefault("statusUri", _job_status_uri(normalized))
    return 200, job


register(
    Tool(
        name="os_map.inventory",
        description="Return a bounded inventory (UPRNs, buildings, road links, path links) for a bbox.",
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "os_map.inventory"},
                "bbox": {
                    "type": "array",
                    "items": {"type": "number"},
                    "minItems": 4,
                    "maxItems": 4,
                    "description": "WGS84 bbox [minLon,minLat,maxLon,maxLat]",
                },
                "layers": {
                    "oneOf": [
                        {"type": "array", "items": {"type": "string"}, "minItems": 1},
                        {"type": "string", "minLength": 1},
                        {"type": "null"},
                    ],
                    "description": "Requested layers (uprns, buildings, road_links, path_links).",
                },
                "limits": {"type": "object", "description": "Per-layer max features (budgets)."},
                "pageTokens": {"type": "object", "description": "Per-layer paging tokens for NGD layers."},
                "includeGeometry": {
                    "type": "object",
                    "description": "Per-layer includeGeometry overrides (NGD layers only).",
                },
                "collections": {
                    "type": "object",
                    "description": "Per-layer NGD collection id overrides (NGD layers only).",
                },
            },
            "required": ["bbox"],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "bbox": {
                    "type": "array",
                    "items": {"type": "number"},
                    "minItems": 4,
                    "maxItems": 4,
                },
                "layers": {"type": "object"},
                "requestedLayers": {"type": "array", "items": {"type": "string"}},
                "limits": {"type": "object"},
                "hints": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["layers"],
            "additionalProperties": True,
        },
        handler=_inventory,
    )
)

register(
    Tool(
        name="os_map.export",
        description=(
            "Export a map artifact. "
            "Legacy mode exports inventory snapshots from bbox; selection_uprn mode queues async "
            "selector-driven UPRN exports."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "os_map.export"},
                "exportType": {
                    "type": "string",
                    "enum": ["inventory_snapshot", "selection_uprn"],
                    "default": "inventory_snapshot",
                },
                "bbox": {
                    "type": "array",
                    "items": {"type": "number"},
                    "minItems": 4,
                    "maxItems": 4,
                },
                "name": {"type": "string"},
                "recipe": {"type": "object"},
                "layers": {
                    "oneOf": [
                        {"type": "array", "items": {"type": "string"}, "minItems": 1},
                        {"type": "string", "minLength": 1},
                        {"type": "null"},
                    ],
                    "description": "Requested layers (uprns, buildings, road_links, path_links).",
                },
                "limits": {"type": "object"},
                "includeGeometry": {"type": "object"},
                "collections": {"type": "object"},
                "selectionSpec": {"type": "object"},
                "format": {"type": "string", "enum": ["csv", "json"]},
                "columns": {"type": "object"},
                "filters": {"type": "object"},
                "delivery": {"type": "string", "enum": ["resource", "auto", "inline"]},
                "derivationMode": {"type": "string", "enum": ["exact", "best_fit"]},
            },
            "required": [],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "exportId": {"type": "string"},
                "uri": {"type": "string"},
                "path": {"type": "string"},
                "notes": {"type": "array", "items": {"type": "string"}},
                "status": {"type": "string"},
                "statusUri": {"type": "string"},
                "resultUri": {"type": ["string", "null"]},
            },
            "required": ["exportId"],
            "additionalProperties": True,
        },
        handler=_export,
    )
)

register(
    Tool(
        name="os_map.get_export",
        description="Get async export status for a selector-driven os_map.export job.",
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "os_map.get_export"},
                "exportId": {"type": "string"},
            },
            "required": ["exportId"],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "exportId": {"type": "string"},
                "status": {"type": "string"},
                "statusUri": {"type": "string"},
                "resultUri": {"type": ["string", "null"]},
                "error": {"type": ["object", "null"]},
                "warnings": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["exportId", "status"],
            "additionalProperties": True,
        },
        handler=_get_export,
    )
)
