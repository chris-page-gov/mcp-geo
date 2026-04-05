from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from server.config import settings
from server.error_taxonomy import classify_error
from server.logging import log_upstream_error

try:
    import psycopg
    from psycopg import sql
    from psycopg.rows import dict_row
except ImportError:  # pragma: no cover - optional dependency fallback
    psycopg = None  # type: ignore[assignment]
    sql = None  # type: ignore[assignment]
    dict_row = None  # type: ignore[assignment]


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LANDIS_REGISTRY_PATH = ROOT / "resources" / "landis_products.json"
DEFAULT_LANDIS_DOCS_DIR = ROOT / "resources" / "landis"
DEFAULT_LANDIS_ARCHIVE_TRIAGE_PATH = (
    ROOT / "research" / "landis-data-source" / "landis_archive_triage_2026-04-05.json"
)
DEFAULT_LANDIS_FULL_RELEASE_MANIFEST_PATH = (
    ROOT / "research" / "landis-data-source" / "landis_full_release_manifest_2026-04-05.json"
)

SOILSCAPE_CAVEATS = [
    "Soilscapes outputs are generalized regional soil patterns, not site investigation results.",
    "Use field survey and geotechnical checks before making parcel-scale or engineering decisions.",
    "Local artificial ground, recent disturbance, and drainage interventions may not be reflected.",
]

PIPE_RISK_CAVEATS = [
    *SOILSCAPE_CAVEATS,
    (
        "Pipe risk is a screening indicator derived from generalized soil "
        "classes and must not be treated as an engineering design approval."
    ),
]

PIPE_RISK_CHECKLIST = [
    "Confirm pipe corridor alignment and construction depth against current design drawings.",
    "Verify local ground conditions with geotechnical or trial-pit evidence before trenching.",
    (
        "Check for made ground, recent utility works, and drainage "
        "modifications not reflected in LandIS layers."
    ),
]

NATMAP_CAVEATS = [
    "NATMAP outputs are generalized polygon interpretations, not parcel-scale ground truth.",
    "Use site investigation before relying on NATMAP outputs for engineering, planning, or regulatory decisions.",
    "Recent disturbance, made ground, and drainage change may not be reflected in the map unit surface.",
]

NSI_CAVEATS = [
    "NSI outputs are sampled observations, not wall-to-wall area coverage.",
    "Nearby NSI sites indicate evidence points and should not be treated as complete local condition mapping.",
    "Use field verification before extrapolating NSI evidence to a development parcel or utility corridor.",
]

_LANDIS_LOCAL_DATA_CANDIDATES = (
    Path.home() / "Data",
    Path("/Volumes/ExtSSD-Data/Data"),
    ROOT / "data" / "landis",
)

_THEMATIC_PRODUCT_CONFIG: dict[str, dict[str, str]] = {
    "natmap-soilscapes": {"title": "NATMAP Soilscapes", "labelKey": "SOILSCAPE", "codeKey": "SS_ID"},
    "natmap-topsoil-texture": {
        "title": "NATMAP Topsoil Texture",
        "labelKey": "TEXTURE",
        "codeKey": "TEXTURE",
    },
    "natmap-subsoil-texture": {
        "title": "NATMAP Subsoil Texture",
        "labelKey": "TEXTURE",
        "codeKey": "TEXTURE",
    },
    "natmap-substrate-texture": {
        "title": "NATMAP Substrate Texture",
        "labelKey": "TEXTURE",
        "codeKey": "TEXTURE",
    },
    "natmap-available-water": {
        "title": "NATMAP Available Water Capacity",
        "labelKey": "AWC",
        "codeKey": "AWC",
    },
    "natmap-carbon": {
        "title": "NATMAP Carbon",
        "labelKey": "TOPOCCLASS",
        "codeKey": "TOPOCCLASS",
    },
    "natmap-wrb2006": {"title": "NATMAP WRB 2006", "labelKey": "WRB06", "codeKey": "WRBCODE"},
    "natmap-regions": {"title": "NATMAP Regions", "labelKey": "NAME", "codeKey": "REGION"},
}

_OBSERVATION_DATASET_TITLES: dict[str, str] = {
    "NSIfeatures": "National Soil Inventory Features",
    "NSImagnetic": "National Soil Inventory Magnetic",
    "NSIprofile": "National Soil Inventory Profile",
    "NSItexture": "National Soil Inventory Texture",
    "NSItopsoil1": "National Soil Inventory Topsoil 1",
    "NSItopsoil2": "National Soil Inventory Topsoil 2",
}


class LandisWarehouseDisabled(RuntimeError):
    pass


class LandisWarehouseUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class AreaInput:
    geometry: dict[str, Any]
    bbox: list[float] | None


def _resolve_repo_path(raw: str | None, default: Path) -> Path:
    value = str(raw or str(default))
    path = Path(value)
    if not path.is_absolute():
        path = ROOT / value
    return path


def _resolve_data_path(raw: str | None, default: Path) -> Path:
    value = str(raw or str(default))
    path = Path(value).expanduser()
    if path.is_absolute():
        return path
    return ROOT / value


def _normalize_text(value: str) -> str:
    return " ".join(value.strip().lower().split())


def landis_registry_path() -> Path:
    return _resolve_repo_path(
        getattr(settings, "LANDIS_REGISTRY_PATH", None),
        DEFAULT_LANDIS_REGISTRY_PATH,
    )


def landis_docs_dir() -> Path:
    return _resolve_repo_path(getattr(settings, "LANDIS_DOCS_DIR", None), DEFAULT_LANDIS_DOCS_DIR)


def landis_archive_triage_path() -> Path:
    return _resolve_repo_path(
        getattr(settings, "LANDIS_ARCHIVE_TRIAGE_PATH", None),
        DEFAULT_LANDIS_ARCHIVE_TRIAGE_PATH,
    )


def landis_full_release_manifest_path() -> Path:
    return _resolve_repo_path(
        getattr(settings, "LANDIS_FULL_RELEASE_MANIFEST_PATH", None),
        DEFAULT_LANDIS_FULL_RELEASE_MANIFEST_PATH,
    )


def landis_local_data_root() -> Path | None:
    configured = str(getattr(settings, "LANDIS_LOCAL_DATA_ROOT", "") or "").strip()
    if configured:
        path = Path(configured).expanduser()
        return path if path.exists() else None
    for candidate in _LANDIS_LOCAL_DATA_CANDIDATES:
        if candidate.exists():
            return candidate
    return None


def _latest_archive_dir(prefix: str, *, configured: str) -> Path | None:
    raw = str(getattr(settings, configured, "") or "").strip()
    if raw:
        path = Path(raw).expanduser()
        return path if path.exists() else None
    root = landis_local_data_root()
    if root is None or not root.exists():
        return None
    matches = [
        path
        for path in root.glob(f"{prefix}*")
        if path.is_dir() and "-smoke" not in path.name
    ]
    return sorted(matches)[-1] if matches else None


def landis_portal_archive_dir() -> Path | None:
    return _latest_archive_dir("landis_portal_archive_", configured="LANDIS_PORTAL_ARCHIVE_DIR")


def landis_full_release_archive_dir() -> Path | None:
    return _latest_archive_dir(
        "landis_full_release_archive_",
        configured="LANDIS_FULL_RELEASE_ARCHIVE_DIR",
    )


def resolve_landis_archive_file(raw_path: str | None) -> Path | None:
    if not raw_path:
        return None
    path = Path(raw_path)
    if path.exists():
        return path
    root = landis_local_data_root()
    if root is None:
        return None
    archive_prefixes = (
        "landis_portal_archive_",
        "landis_full_release_archive_",
    )
    for index, part in enumerate(path.parts):
        if any(part.startswith(prefix) for prefix in archive_prefixes):
            candidate = root / Path(*path.parts[index:])
            return candidate if candidate.exists() else None
    return None


@lru_cache(maxsize=1)
def load_landis_registry() -> dict[str, Any]:
    fallback: dict[str, Any] = {
        "version": "missing",
        "products": [],
        "sources": [],
        "updatedAt": None,
    }
    path = landis_registry_path()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return fallback
    except json.JSONDecodeError:
        fallback["version"] = "invalid"
        return fallback
    if not isinstance(payload, dict):
        fallback["version"] = "invalid"
        return fallback
    products = payload.get("products")
    if not isinstance(products, list):
        payload["products"] = []
    return payload


def list_landis_products() -> list[dict[str, Any]]:
    raw = load_landis_registry().get("products")
    if not isinstance(raw, list):
        return []
    return [entry for entry in raw if isinstance(entry, dict)]


def get_landis_product(product_id: str) -> dict[str, Any] | None:
    target = _normalize_text(product_id)
    for product in list_landis_products():
        current_id = str(product.get("id") or "")
        aliases = product.get("aliases")
        candidates = [current_id]
        if isinstance(aliases, list):
            candidates.extend(str(item) for item in aliases if isinstance(item, str))
        if any(_normalize_text(candidate) == target for candidate in candidates if candidate):
            return product
    return None


@lru_cache(maxsize=1)
def load_landis_archive_triage() -> dict[str, Any]:
    fallback: dict[str, Any] = {
        "version": "missing",
        "generatedAt": None,
        "portalItems": [],
        "supplementaryPublicItems": [],
        "supplementaryDataGovPackages": [],
    }
    path = landis_archive_triage_path()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return fallback
    except json.JSONDecodeError:
        fallback["version"] = "invalid"
        return fallback
    if not isinstance(payload, dict):
        fallback["version"] = "invalid"
        return fallback
    return payload


@lru_cache(maxsize=1)
def load_landis_full_release_manifest() -> dict[str, Any]:
    fallback: dict[str, Any] = {
        "generatedAt": None,
        "destination": None,
        "publicItems": [],
        "dataGovPackages": [],
        "summary": {},
    }
    path = landis_full_release_manifest_path()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return fallback
    except json.JSONDecodeError:
        fallback["summary"] = {"status": "invalid"}
        return fallback
    if not isinstance(payload, dict):
        fallback["summary"] = {"status": "invalid"}
        return fallback
    return payload


def list_landis_archive_items() -> list[dict[str, Any]]:
    triage = load_landis_archive_triage()
    raw = triage.get("portalItems")
    if not isinstance(raw, list):
        return []
    return [item for item in raw if isinstance(item, dict)]


def get_landis_archive_item(archive_id: str) -> dict[str, Any] | None:
    target = _normalize_text(archive_id)
    for item in list_landis_archive_items():
        candidates = [str(item.get("archiveId") or ""), str(item.get("title") or "")]
        aliases = item.get("aliases")
        if isinstance(aliases, list):
            candidates.extend(str(alias) for alias in aliases if isinstance(alias, str))
        if any(_normalize_text(candidate) == target for candidate in candidates if candidate):
            return item
    return None


def archive_item_detail(item: dict[str, Any]) -> dict[str, Any]:
    detail: dict[str, Any] = {
        "archiveId": item.get("archiveId"),
        "title": item.get("title"),
        "itemType": item.get("itemType"),
        "runtimeFamily": item.get("runtimeFamily"),
        "surfacingClass": item.get("surfacingClass"),
        "recordCount": item.get("recordCount"),
        "geometryType": item.get("geometryType"),
        "serviceUrl": item.get("serviceUrl"),
        "tags": item.get("tags", []),
        "localPaths": {},
    }
    for key in ("itemPath", "inventoryPath", "downloadSummaryPath", "metadataPath"):
        resolved = resolve_landis_archive_file(item.get(key))
        if resolved is not None:
            detail["localPaths"][key] = str(resolved)
    return detail


def landis_registry_meta() -> dict[str, Any]:
    payload = load_landis_registry()
    return {
        "registryVersion": payload.get("version"),
        "updatedAt": payload.get("updatedAt"),
        "registryUri": "resource://mcp-geo/landis-products",
        "archiveTriageUri": "resource://mcp-geo/landis-archive-triage",
        "portalInventoryUri": "resource://mcp-geo/landis-portal-inventory",
        "fullReleaseManifestUri": "resource://mcp-geo/landis-full-release-manifest",
        "portalBase": getattr(settings, "LANDIS_PORTAL_BASE", "https://portal.landis.org.uk"),
        "localDataRoot": str(landis_local_data_root()) if landis_local_data_root() else None,
        "sources": payload.get("sources", []),
    }


def parse_bbox(value: Any) -> list[float] | None:
    if not isinstance(value, list) or len(value) != 4:
        return None
    try:
        bbox = [float(value[0]), float(value[1]), float(value[2]), float(value[3])]
    except (TypeError, ValueError):
        return None
    if bbox[0] >= bbox[2] or bbox[1] >= bbox[3]:
        return None
    return bbox


def bbox_to_geometry(bbox: list[float]) -> dict[str, Any]:
    min_lon, min_lat, max_lon, max_lat = bbox
    return {
        "type": "Polygon",
        "coordinates": [[
            [min_lon, min_lat],
            [max_lon, min_lat],
            [max_lon, max_lat],
            [min_lon, max_lat],
            [min_lon, min_lat],
        ]],
    }


def _extract_geometry(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    if value.get("type") == "Feature":
        inner = value.get("geometry")
        return inner if isinstance(inner, dict) else None
    return value


def _geometry_supported(geometry: dict[str, Any]) -> bool:
    geom_type = geometry.get("type")
    coordinates = geometry.get("coordinates")
    return geom_type in {"Polygon", "MultiPolygon"} and isinstance(coordinates, list)


def resolve_area_input(payload: dict[str, Any]) -> tuple[AreaInput | None, str | None]:
    geometry = _extract_geometry(payload.get("geometry"))
    if geometry is not None:
        if not _geometry_supported(geometry):
            return None, "geometry must be a GeoJSON Polygon or MultiPolygon"
        return AreaInput(geometry=geometry, bbox=None), None
    bbox = parse_bbox(payload.get("bbox"))
    if bbox is not None:
        return AreaInput(geometry=bbox_to_geometry(bbox), bbox=bbox), None
    return None, "Provide bbox or geometry"


def build_provenance(
    *,
    product_id: str | None = None,
    resource_uri: str | None = None,
    dataset_version: str | None = None,
    source_url: str | None = None,
    license_name: str | None = None,
    updated_at: str | None = None,
    warehouse: bool = False,
) -> dict[str, Any]:
    product = get_landis_product(product_id) if product_id else None
    citations = []
    if isinstance(product, dict):
        raw_citations = product.get("citations")
        if isinstance(raw_citations, list):
            citations = [item for item in raw_citations if isinstance(item, dict)]
    return {
        "productId": product.get("id") if isinstance(product, dict) else product_id,
        "title": product.get("title") if isinstance(product, dict) else None,
        "resourceUri": (
            resource_uri or (product.get("resourceUri") if isinstance(product, dict) else None)
        ),
        "datasetVersion": (
            dataset_version
            or (
                product.get("datasetVersion")
                if isinstance(product, dict)
                else None
            )
        ),
        "sourceUrl": (
            source_url or (product.get("sourceUrl") if isinstance(product, dict) else None)
        ),
        "license": license_name or (product.get("license") if isinstance(product, dict) else None),
        "updatedAt": (
            updated_at or (product.get("updatedAt") if isinstance(product, dict) else None)
        ),
        "portalBase": getattr(settings, "LANDIS_PORTAL_BASE", "https://portal.landis.org.uk"),
        "warehouseBacked": warehouse,
        "citations": citations,
    }


def _isoformat(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return str(value.isoformat())
    return str(value)


def _float(value: Any) -> float | None:
    try:
        return None if value is None else float(value)
    except (TypeError, ValueError):
        return None


def _int(value: Any) -> int | None:
    try:
        return None if value is None else int(value)
    except (TypeError, ValueError):
        return None


class LandisWarehouse:
    def __init__(
        self,
        *,
        dsn: str,
        schema: str,
        product_registry_table: str,
        provenance_table: str,
        soilscapes_table: str,
        pipe_risk_table: str,
        natmap_table: str,
        natmap_thematic_table: str,
        nsi_sites_table: str,
        nsi_observations_table: str,
    ) -> None:
        self._dsn = dsn
        self._schema = schema
        self._product_registry_table = product_registry_table
        self._provenance_table = provenance_table
        self._soilscapes_table = soilscapes_table
        self._pipe_risk_table = pipe_risk_table
        self._natmap_table = natmap_table
        self._natmap_thematic_table = natmap_thematic_table
        self._nsi_sites_table = nsi_sites_table
        self._nsi_observations_table = nsi_observations_table

    @classmethod
    def from_settings(cls) -> LandisWarehouse:
        dsn = getattr(settings, "LANDIS_WAREHOUSE_DSN", "") or getattr(
            settings,
            "BOUNDARY_CACHE_DSN",
            "",
        )
        return cls(
            dsn=dsn,
            schema=getattr(settings, "LANDIS_WAREHOUSE_SCHEMA", "landis"),
            product_registry_table=getattr(
                settings,
                "LANDIS_PRODUCT_REGISTRY_TABLE",
                "product_registry",
            ),
            provenance_table=getattr(settings, "LANDIS_PROVENANCE_TABLE", "dataset_provenance"),
            soilscapes_table=getattr(settings, "LANDIS_SOILSCAPES_TABLE", "soilscapes_polygons"),
            pipe_risk_table=getattr(settings, "LANDIS_PIPE_RISK_TABLE", "pipe_risk_polygons"),
            natmap_table=getattr(settings, "LANDIS_NATMAP_TABLE", "natmap_polygons"),
            natmap_thematic_table=getattr(
                settings,
                "LANDIS_NATMAP_THEMATIC_TABLE",
                "natmap_thematic_polygons",
            ),
            nsi_sites_table=getattr(settings, "LANDIS_NSI_SITES_TABLE", "nsi_sites"),
            nsi_observations_table=getattr(
                settings,
                "LANDIS_NSI_OBSERVATIONS_TABLE",
                "nsi_observations",
            ),
        )

    def enabled(self) -> bool:
        return (
            bool(getattr(settings, "LANDIS_ENABLED", True))
            and bool(getattr(settings, "LANDIS_LIVE_ENABLED", True))
            and bool(self._dsn)
        )

    def disabled_reason(self) -> str:
        if not getattr(settings, "LANDIS_ENABLED", True):
            return "landis_disabled"
        if not getattr(settings, "LANDIS_LIVE_ENABLED", True):
            return "landis_live_disabled"
        if not self._dsn:
            return "landis_warehouse_unconfigured"
        return "landis_live_disabled"

    def _require_enabled(self) -> None:
        if not self.enabled():
            raise LandisWarehouseDisabled(self.disabled_reason())

    def _log_error(self, detail: str) -> None:
        log_upstream_error(
            service="landis",
            code="UPSTREAM_CONNECT_ERROR",
            detail=detail,
            error_category=classify_error("UPSTREAM_CONNECT_ERROR"),
        )

    def _connect(self):
        if psycopg is None:
            raise LandisWarehouseUnavailable("psycopg is not installed")
        return psycopg.connect(self._dsn, row_factory=dict_row)

    def _table_identifier(self, table_name: str):
        if sql is None:
            raise LandisWarehouseUnavailable("psycopg sql module unavailable")
        return sql.Identifier(self._schema, table_name)

    def soilscapes_point(self, *, lat: float, lon: float) -> dict[str, Any] | None:
        self._require_enabled()
        table_ident = self._table_identifier(self._soilscapes_table)
        query = sql.SQL(
            """
            SELECT
                class_code,
                class_name,
                dominant_texture,
                drainage_class,
                carbon_status,
                habitat_note,
                scale_label,
                dataset_version,
                source_url,
                license_name,
                updated_at
            FROM {table}
            WHERE ST_Intersects(geom, ST_SetSRID(ST_Point(%s, %s), 4326))
            ORDER BY class_name ASC
            LIMIT 1;
            """
        ).format(table=table_ident)
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (lon, lat))
                    row = cur.fetchone()
        except LandisWarehouseUnavailable:
            raise
        except Exception as exc:  # pragma: no cover - defensive runtime path
            self._log_error(str(exc))
            raise LandisWarehouseUnavailable(str(exc)) from exc
        if not row:
            return None
        return {
            "soilscape": {
                "code": row.get("class_code"),
                "name": row.get("class_name"),
                "dominantTexture": row.get("dominant_texture"),
                "drainageClass": row.get("drainage_class"),
                "carbonStatus": row.get("carbon_status"),
                "habitatNote": row.get("habitat_note"),
                "scaleLabel": row.get("scale_label"),
            },
            "provenance": build_provenance(
                product_id="soilscapes",
                dataset_version=str(row.get("dataset_version") or ""),
                source_url=str(row.get("source_url") or ""),
                license_name=str(row.get("license_name") or ""),
                updated_at=_isoformat(row.get("updated_at")),
                warehouse=True,
            ),
        }

    def soilscapes_area_summary(self, *, geometry: dict[str, Any]) -> dict[str, Any] | None:
        self._require_enabled()
        table_ident = self._table_identifier(self._soilscapes_table)
        query = sql.SQL(
            """
            WITH input_geom AS (
                SELECT ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326) AS geom
            ),
            area_meta AS (
                SELECT ST_Area(geom::geography) AS input_area_m2
                FROM input_geom
            )
            SELECT
                s.class_code,
                s.class_name,
                s.dominant_texture,
                s.drainage_class,
                s.carbon_status,
                s.habitat_note,
                s.scale_label,
                SUM(ST_Area(ST_Intersection(s.geom, i.geom)::geography)) AS area_m2,
                MAX(s.dataset_version) AS dataset_version,
                MAX(s.source_url) AS source_url,
                MAX(s.license_name) AS license_name,
                MAX(s.updated_at) AS updated_at,
                area_meta.input_area_m2
            FROM {table} s
            CROSS JOIN input_geom i
            CROSS JOIN area_meta
            WHERE ST_Intersects(s.geom, i.geom)
            GROUP BY
                s.class_code,
                s.class_name,
                s.dominant_texture,
                s.drainage_class,
                s.carbon_status,
                s.habitat_note,
                s.scale_label,
                area_meta.input_area_m2
            ORDER BY area_m2 DESC, s.class_name ASC;
            """
        ).format(table=table_ident)
        geojson = json.dumps(geometry, ensure_ascii=True, separators=(",", ":"))
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (geojson,))
                    rows = cur.fetchall() or []
        except LandisWarehouseUnavailable:
            raise
        except Exception as exc:  # pragma: no cover - defensive runtime path
            self._log_error(str(exc))
            raise LandisWarehouseUnavailable(str(exc)) from exc
        if not rows:
            return None
        input_area = _float(rows[0].get("input_area_m2")) or 0.0
        classes: list[dict[str, Any]] = []
        dataset_version: str | None = None
        source_url: str | None = None
        license_name: str | None = None
        updated_at: str | None = None
        for row in rows:
            area_m2 = _float(row.get("area_m2")) or 0.0
            classes.append(
                {
                    "code": row.get("class_code"),
                    "name": row.get("class_name"),
                    "areaSqM": round(area_m2, 2),
                    "percent": round((area_m2 / input_area) * 100.0, 2) if input_area else 0.0,
                    "dominantTexture": row.get("dominant_texture"),
                    "drainageClass": row.get("drainage_class"),
                    "carbonStatus": row.get("carbon_status"),
                    "habitatNote": row.get("habitat_note"),
                    "scaleLabel": row.get("scale_label"),
                }
            )
            dataset_version = dataset_version or str(row.get("dataset_version") or "") or None
            source_url = source_url or str(row.get("source_url") or "") or None
            license_name = license_name or str(row.get("license_name") or "") or None
            updated_at = updated_at or _isoformat(row.get("updated_at"))
        return {
            "areaSqM": round(input_area, 2),
            "classes": classes,
            "dominantClass": classes[0] if classes else None,
            "provenance": build_provenance(
                product_id="soilscapes",
                dataset_version=dataset_version,
                source_url=source_url,
                license_name=license_name,
                updated_at=updated_at,
                warehouse=True,
            ),
        }

    def pipe_risk_summary(self, *, geometry: dict[str, Any]) -> dict[str, Any] | None:
        self._require_enabled()
        table_ident = self._table_identifier(self._pipe_risk_table)
        query = sql.SQL(
            """
            WITH input_geom AS (
                SELECT ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326) AS geom
            ),
            area_meta AS (
                SELECT ST_Area(geom::geography) AS input_area_m2
                FROM input_geom
            )
            SELECT
                p.shrink_swell_code,
                p.shrink_swell_label,
                p.shrink_swell_score,
                p.corrosion_code,
                p.corrosion_label,
                p.corrosion_score,
                SUM(ST_Area(ST_Intersection(p.geom, i.geom)::geography)) AS area_m2,
                MAX(p.dataset_version) AS dataset_version,
                MAX(p.source_url) AS source_url,
                MAX(p.license_name) AS license_name,
                MAX(p.updated_at) AS updated_at,
                area_meta.input_area_m2
            FROM {table} p
            CROSS JOIN input_geom i
            CROSS JOIN area_meta
            WHERE ST_Intersects(p.geom, i.geom)
            GROUP BY
                p.shrink_swell_code,
                p.shrink_swell_label,
                p.shrink_swell_score,
                p.corrosion_code,
                p.corrosion_label,
                p.corrosion_score,
                area_meta.input_area_m2
            ORDER BY area_m2 DESC,
                     p.corrosion_score DESC NULLS LAST,
                     p.shrink_swell_score DESC NULLS LAST;
            """
        ).format(table=table_ident)
        geojson = json.dumps(geometry, ensure_ascii=True, separators=(",", ":"))
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (geojson,))
                    rows = cur.fetchall() or []
        except LandisWarehouseUnavailable:
            raise
        except Exception as exc:  # pragma: no cover - defensive runtime path
            self._log_error(str(exc))
            raise LandisWarehouseUnavailable(str(exc)) from exc
        if not rows:
            return None

        input_area = _float(rows[0].get("input_area_m2")) or 0.0
        corrosion_classes: list[dict[str, Any]] = []
        shrink_classes: list[dict[str, Any]] = []
        weighted_corrosion = 0.0
        weighted_shrink = 0.0
        worst_corrosion = 0
        worst_shrink = 0
        dataset_version: str | None = None
        source_url: str | None = None
        license_name: str | None = None
        updated_at: str | None = None

        for row in rows:
            area_m2 = _float(row.get("area_m2")) or 0.0
            area_pct = round((area_m2 / input_area) * 100.0, 2) if input_area else 0.0
            corrosion_score = _int(row.get("corrosion_score")) or 0
            shrink_score = _int(row.get("shrink_swell_score")) or 0
            weighted_corrosion += area_pct * corrosion_score
            weighted_shrink += area_pct * shrink_score
            worst_corrosion = max(worst_corrosion, corrosion_score)
            worst_shrink = max(worst_shrink, shrink_score)
            corrosion_classes.append(
                {
                    "code": row.get("corrosion_code"),
                    "label": row.get("corrosion_label"),
                    "score": corrosion_score,
                    "areaSqM": round(area_m2, 2),
                    "percent": area_pct,
                }
            )
            shrink_classes.append(
                {
                    "code": row.get("shrink_swell_code"),
                    "label": row.get("shrink_swell_label"),
                    "score": shrink_score,
                    "areaSqM": round(area_m2, 2),
                    "percent": area_pct,
                }
            )
            dataset_version = dataset_version or str(row.get("dataset_version") or "") or None
            source_url = source_url or str(row.get("source_url") or "") or None
            license_name = license_name or str(row.get("license_name") or "") or None
            updated_at = updated_at or _isoformat(row.get("updated_at"))

        weighted_corrosion_score = round(weighted_corrosion / 100.0, 2) if input_area else 0.0
        weighted_shrink_score = round(weighted_shrink / 100.0, 2) if input_area else 0.0
        overall_score = round(
            max(
                worst_corrosion,
                worst_shrink,
                weighted_corrosion_score,
                weighted_shrink_score,
            ),
            2,
        )
        if overall_score >= 4:
            risk_band = "high"
        elif overall_score >= 3:
            risk_band = "medium"
        else:
            risk_band = "low"
        return {
            "areaSqM": round(input_area, 2),
            "riskBand": risk_band,
            "scores": {
                "overall": overall_score,
                "weightedCorrosion": weighted_corrosion_score,
                "weightedShrinkSwell": weighted_shrink_score,
                "worstCorrosion": worst_corrosion,
                "worstShrinkSwell": worst_shrink,
            },
            "corrosionClasses": corrosion_classes,
            "shrinkSwellClasses": shrink_classes,
            "provenance": build_provenance(
                product_id="pipe-risk",
                dataset_version=dataset_version,
                source_url=source_url,
                license_name=license_name,
                updated_at=updated_at,
                warehouse=True,
            ),
        }

    def natmap_point(self, *, lat: float, lon: float) -> dict[str, Any] | None:
        self._require_enabled()
        table_ident = self._table_identifier(self._natmap_table)
        query = sql.SQL(
            """
            SELECT
                map_unit_id,
                map_symbol,
                map_unit_name,
                description,
                geology,
                dominant_soils,
                associated_soils,
                site_class,
                crop_landuse,
                soilscape,
                drainage,
                fertility,
                habitats,
                drains_to,
                water_protection,
                soilguide,
                dataset_version,
                source_url,
                license_name,
                updated_at
            FROM {table}
            WHERE ST_Intersects(geom, ST_SetSRID(ST_Point(%s, %s), 4326))
            ORDER BY map_unit_name ASC, map_symbol ASC
            LIMIT 1;
            """
        ).format(table=table_ident)
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (lon, lat))
                    row = cur.fetchone()
        except LandisWarehouseUnavailable:
            raise
        except Exception as exc:  # pragma: no cover - defensive runtime path
            self._log_error(str(exc))
            raise LandisWarehouseUnavailable(str(exc)) from exc
        if not row:
            return None
        return {
            "mapUnit": {
                "mapUnitId": row.get("map_unit_id"),
                "mapSymbol": row.get("map_symbol"),
                "name": row.get("map_unit_name"),
                "description": row.get("description"),
                "geology": row.get("geology"),
                "dominantSoils": row.get("dominant_soils"),
                "associatedSoils": row.get("associated_soils"),
                "siteClass": row.get("site_class"),
                "cropLandUse": row.get("crop_landuse"),
                "soilscape": row.get("soilscape"),
                "drainage": row.get("drainage"),
                "fertility": row.get("fertility"),
                "habitats": row.get("habitats"),
                "drainsTo": row.get("drains_to"),
                "waterProtection": row.get("water_protection"),
                "soilGuide": row.get("soilguide"),
            },
            "provenance": build_provenance(
                product_id="natmap-core",
                dataset_version=str(row.get("dataset_version") or ""),
                source_url=str(row.get("source_url") or ""),
                license_name=str(row.get("license_name") or ""),
                updated_at=_isoformat(row.get("updated_at")),
                warehouse=True,
            ),
        }

    def natmap_area_summary(self, *, geometry: dict[str, Any]) -> dict[str, Any] | None:
        self._require_enabled()
        table_ident = self._table_identifier(self._natmap_table)
        query = sql.SQL(
            """
            WITH input_geom AS (
                SELECT ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326) AS geom
            ),
            area_meta AS (
                SELECT ST_Area(geom::geography) AS input_area_m2
                FROM input_geom
            )
            SELECT
                n.map_unit_id,
                n.map_symbol,
                n.map_unit_name,
                n.soilscape,
                n.drainage,
                n.fertility,
                SUM(ST_Area(ST_Intersection(n.geom, i.geom)::geography)) AS area_m2,
                MAX(n.dataset_version) AS dataset_version,
                MAX(n.source_url) AS source_url,
                MAX(n.license_name) AS license_name,
                MAX(n.updated_at) AS updated_at,
                area_meta.input_area_m2
            FROM {table} n
            CROSS JOIN input_geom i
            CROSS JOIN area_meta
            WHERE ST_Intersects(n.geom, i.geom)
            GROUP BY
                n.map_unit_id,
                n.map_symbol,
                n.map_unit_name,
                n.soilscape,
                n.drainage,
                n.fertility,
                area_meta.input_area_m2
            ORDER BY area_m2 DESC, n.map_unit_name ASC
            LIMIT 25;
            """
        ).format(table=table_ident)
        geojson = json.dumps(geometry, ensure_ascii=True, separators=(",", ":"))
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (geojson,))
                    rows = cur.fetchall() or []
        except LandisWarehouseUnavailable:
            raise
        except Exception as exc:  # pragma: no cover - defensive runtime path
            self._log_error(str(exc))
            raise LandisWarehouseUnavailable(str(exc)) from exc
        if not rows:
            return None

        input_area = _float(rows[0].get("input_area_m2")) or 0.0
        classes: list[dict[str, Any]] = []
        dataset_version: str | None = None
        source_url: str | None = None
        license_name: str | None = None
        updated_at: str | None = None
        for row in rows:
            area_m2 = _float(row.get("area_m2")) or 0.0
            classes.append(
                {
                    "mapUnitId": row.get("map_unit_id"),
                    "mapSymbol": row.get("map_symbol"),
                    "name": row.get("map_unit_name"),
                    "soilscape": row.get("soilscape"),
                    "drainage": row.get("drainage"),
                    "fertility": row.get("fertility"),
                    "areaSqM": round(area_m2, 2),
                    "percent": round((area_m2 / input_area) * 100.0, 2) if input_area else 0.0,
                }
            )
            dataset_version = dataset_version or str(row.get("dataset_version") or "") or None
            source_url = source_url or str(row.get("source_url") or "") or None
            license_name = license_name or str(row.get("license_name") or "") or None
            updated_at = updated_at or _isoformat(row.get("updated_at"))
        return {
            "areaSqM": round(input_area, 2),
            "mapUnits": classes,
            "dominantMapUnit": classes[0] if classes else None,
            "provenance": build_provenance(
                product_id="natmap-core",
                dataset_version=dataset_version,
                source_url=source_url,
                license_name=license_name,
                updated_at=updated_at,
                warehouse=True,
            ),
        }

    def natmap_thematic_area_summary(
        self,
        *,
        product_id: str,
        geometry: dict[str, Any],
    ) -> dict[str, Any] | None:
        self._require_enabled()
        table_ident = self._table_identifier(self._natmap_thematic_table)
        query = sql.SQL(
            """
            WITH input_geom AS (
                SELECT ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326) AS geom
            ),
            area_meta AS (
                SELECT ST_Area(geom::geography) AS input_area_m2
                FROM input_geom
            )
            SELECT
                t.product_id,
                t.class_code,
                t.class_label,
                t.metrics,
                SUM(ST_Area(ST_Intersection(t.geom, i.geom)::geography)) AS area_m2,
                MAX(t.dataset_version) AS dataset_version,
                MAX(t.source_url) AS source_url,
                MAX(t.license_name) AS license_name,
                MAX(t.updated_at) AS updated_at,
                area_meta.input_area_m2
            FROM {table} t
            CROSS JOIN input_geom i
            CROSS JOIN area_meta
            WHERE t.product_id = %s
              AND ST_Intersects(t.geom, i.geom)
            GROUP BY
                t.product_id,
                t.class_code,
                t.class_label,
                t.metrics,
                area_meta.input_area_m2
            ORDER BY area_m2 DESC, t.class_label ASC
            LIMIT 25;
            """
        ).format(table=table_ident)
        geojson = json.dumps(geometry, ensure_ascii=True, separators=(",", ":"))
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (geojson, product_id))
                    rows = cur.fetchall() or []
        except LandisWarehouseUnavailable:
            raise
        except Exception as exc:  # pragma: no cover - defensive runtime path
            self._log_error(str(exc))
            raise LandisWarehouseUnavailable(str(exc)) from exc
        if not rows:
            return None
        input_area = _float(rows[0].get("input_area_m2")) or 0.0
        classes: list[dict[str, Any]] = []
        dataset_version: str | None = None
        source_url: str | None = None
        license_name: str | None = None
        updated_at: str | None = None
        for row in rows:
            area_m2 = _float(row.get("area_m2")) or 0.0
            metrics = row.get("metrics")
            classes.append(
                {
                    "code": row.get("class_code"),
                    "label": row.get("class_label"),
                    "areaSqM": round(area_m2, 2),
                    "percent": round((area_m2 / input_area) * 100.0, 2) if input_area else 0.0,
                    "metrics": metrics if isinstance(metrics, dict) else {},
                }
            )
            dataset_version = dataset_version or str(row.get("dataset_version") or "") or None
            source_url = source_url or str(row.get("source_url") or "") or None
            license_name = license_name or str(row.get("license_name") or "") or None
            updated_at = updated_at or _isoformat(row.get("updated_at"))
        return {
            "productId": product_id,
            "areaSqM": round(input_area, 2),
            "classes": classes,
            "dominantClass": classes[0] if classes else None,
            "product": _THEMATIC_PRODUCT_CONFIG.get(product_id, {"title": product_id}),
            "provenance": build_provenance(
                product_id="natmap-core",
                dataset_version=dataset_version,
                source_url=source_url,
                license_name=license_name,
                updated_at=updated_at,
                warehouse=True,
            ),
        }

    def nsi_nearest_sites(
        self,
        *,
        lat: float,
        lon: float,
        limit: int,
        max_distance_km: float | None,
    ) -> dict[str, Any]:
        self._require_enabled()
        table_ident = self._table_identifier(self._nsi_sites_table)
        distance_clause = ""
        params: list[Any] = []
        if max_distance_km is not None:
            distance_clause = "WHERE ST_DWithin(geom::geography, ST_SetSRID(ST_Point(%s, %s), 4326)::geography, %s)"
            params.extend([lon, lat, max_distance_km * 1000.0])
        query = sql.SQL(
            f"""
            SELECT
                nsi_id,
                series_name,
                variant,
                subgroup,
                landuse,
                madeground,
                rocktype,
                survey_date,
                altitude,
                slope,
                aspect,
                easting,
                northing,
                dataset_version,
                source_url,
                license_name,
                updated_at,
                ST_Y(geom) AS lat,
                ST_X(geom) AS lon,
                ST_DistanceSphere(geom, ST_SetSRID(ST_Point(%s, %s), 4326)) / 1000.0 AS distance_km
            FROM {{table}}
            {distance_clause}
            ORDER BY distance_km ASC, nsi_id ASC
            LIMIT %s;
            """
        ).format(table=table_ident)
        params.extend([lon, lat, limit])
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, params)
                    rows = cur.fetchall() or []
        except LandisWarehouseUnavailable:
            raise
        except Exception as exc:  # pragma: no cover - defensive runtime path
            self._log_error(str(exc))
            raise LandisWarehouseUnavailable(str(exc)) from exc
        results: list[dict[str, Any]] = []
        dataset_version: str | None = None
        source_url: str | None = None
        license_name: str | None = None
        updated_at: str | None = None
        for row in rows:
            results.append(
                {
                    "nsiId": row.get("nsi_id"),
                    "distanceKm": round(_float(row.get("distance_km")) or 0.0, 3),
                    "location": {"lat": _float(row.get("lat")), "lon": _float(row.get("lon"))},
                    "seriesName": row.get("series_name"),
                    "variant": row.get("variant"),
                    "subgroup": row.get("subgroup"),
                    "landUse": row.get("landuse"),
                    "madeGround": row.get("madeground"),
                    "rockType": row.get("rocktype"),
                    "surveyDate": _isoformat(row.get("survey_date")),
                    "altitude": row.get("altitude"),
                    "slope": row.get("slope"),
                    "aspect": row.get("aspect"),
                    "easting": row.get("easting"),
                    "northing": row.get("northing"),
                }
            )
            dataset_version = dataset_version or str(row.get("dataset_version") or "") or None
            source_url = source_url or str(row.get("source_url") or "") or None
            license_name = license_name or str(row.get("license_name") or "") or None
            updated_at = updated_at or _isoformat(row.get("updated_at"))
        return {
            "sites": results,
            "provenance": build_provenance(
                product_id="nsi-evidence",
                dataset_version=dataset_version,
                source_url=source_url,
                license_name=license_name,
                updated_at=updated_at,
                warehouse=True,
            ),
        }

    def nsi_sites_within_area(
        self,
        *,
        geometry: dict[str, Any],
        limit: int,
        offset: int,
    ) -> dict[str, Any]:
        self._require_enabled()
        table_ident = self._table_identifier(self._nsi_sites_table)
        geojson = json.dumps(geometry, ensure_ascii=True, separators=(",", ":"))
        query = sql.SQL(
            """
            WITH input_geom AS (
                SELECT ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326) AS geom
            ),
            matches AS (
                SELECT
                    nsi_id,
                    series_name,
                    variant,
                    subgroup,
                    landuse,
                    madeground,
                    rocktype,
                    survey_date,
                    altitude,
                    slope,
                    aspect,
                    easting,
                    northing,
                    dataset_version,
                    source_url,
                    license_name,
                    updated_at,
                    ST_Y(geom) AS lat,
                    ST_X(geom) AS lon
                FROM {table}
                WHERE ST_Intersects(geom, (SELECT geom FROM input_geom))
            )
            SELECT *, (SELECT COUNT(*) FROM matches) AS total_count
            FROM matches
            ORDER BY nsi_id ASC
            OFFSET %s
            LIMIT %s;
            """
        ).format(table=table_ident)
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (geojson, offset, limit))
                    rows = cur.fetchall() or []
        except LandisWarehouseUnavailable:
            raise
        except Exception as exc:  # pragma: no cover - defensive runtime path
            self._log_error(str(exc))
            raise LandisWarehouseUnavailable(str(exc)) from exc
        total_count = _int(rows[0].get("total_count")) if rows else 0
        results: list[dict[str, Any]] = []
        dataset_version: str | None = None
        source_url: str | None = None
        license_name: str | None = None
        updated_at: str | None = None
        for row in rows:
            results.append(
                {
                    "nsiId": row.get("nsi_id"),
                    "location": {"lat": _float(row.get("lat")), "lon": _float(row.get("lon"))},
                    "seriesName": row.get("series_name"),
                    "variant": row.get("variant"),
                    "subgroup": row.get("subgroup"),
                    "landUse": row.get("landuse"),
                    "madeGround": row.get("madeground"),
                    "rockType": row.get("rocktype"),
                    "surveyDate": _isoformat(row.get("survey_date")),
                    "altitude": row.get("altitude"),
                    "slope": row.get("slope"),
                    "aspect": row.get("aspect"),
                    "easting": row.get("easting"),
                    "northing": row.get("northing"),
                }
            )
            dataset_version = dataset_version or str(row.get("dataset_version") or "") or None
            source_url = source_url or str(row.get("source_url") or "") or None
            license_name = license_name or str(row.get("license_name") or "") or None
            updated_at = updated_at or _isoformat(row.get("updated_at"))
        return {
            "sites": results,
            "totalCount": total_count or 0,
            "nextOffset": (offset + limit) if total_count and (offset + limit) < total_count else None,
            "provenance": build_provenance(
                product_id="nsi-evidence",
                dataset_version=dataset_version,
                source_url=source_url,
                license_name=license_name,
                updated_at=updated_at,
                warehouse=True,
            ),
        }

    def nsi_profile_summary(self, *, nsi_id: int) -> dict[str, Any] | None:
        self._require_enabled()
        sites_ident = self._table_identifier(self._nsi_sites_table)
        obs_ident = self._table_identifier(self._nsi_observations_table)
        site_query = sql.SQL(
            """
            SELECT
                nsi_id,
                series_name,
                variant,
                subgroup,
                landuse,
                madeground,
                rocktype,
                survey_date,
                altitude,
                slope,
                aspect,
                easting,
                northing,
                ST_Y(geom) AS lat,
                ST_X(geom) AS lon,
                dataset_version,
                source_url,
                license_name,
                updated_at
            FROM {table}
            WHERE nsi_id = %s
            LIMIT 1;
            """
        ).format(table=sites_ident)
        obs_query = sql.SQL(
            """
            SELECT
                dataset_id,
                observation_label,
                top_depth_cm,
                lower_depth_cm,
                summary,
                dataset_version,
                source_url,
                license_name,
                updated_at
            FROM {table}
            WHERE nsi_id = %s
            ORDER BY dataset_id ASC, top_depth_cm ASC NULLS FIRST, lower_depth_cm ASC NULLS FIRST
            LIMIT 250;
            """
        ).format(table=obs_ident)
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(site_query, (nsi_id,))
                    site = cur.fetchone()
                    cur.execute(obs_query, (nsi_id,))
                    rows = cur.fetchall() or []
        except LandisWarehouseUnavailable:
            raise
        except Exception as exc:  # pragma: no cover - defensive runtime path
            self._log_error(str(exc))
            raise LandisWarehouseUnavailable(str(exc)) from exc
        if not site:
            return None

        grouped: dict[str, dict[str, Any]] = {}
        dataset_version: str | None = str(site.get("dataset_version") or "") or None
        source_url: str | None = str(site.get("source_url") or "") or None
        license_name: str | None = str(site.get("license_name") or "") or None
        updated_at: str | None = _isoformat(site.get("updated_at"))
        for row in rows:
            dataset_id = str(row.get("dataset_id") or "unknown")
            bucket = grouped.setdefault(
                dataset_id,
                {"datasetId": dataset_id, "title": _OBSERVATION_DATASET_TITLES.get(dataset_id, dataset_id), "count": 0, "samples": []},
            )
            bucket["count"] += 1
            if len(bucket["samples"]) < 5:
                bucket["samples"].append(
                    {
                        "label": row.get("observation_label"),
                        "topDepthCm": _float(row.get("top_depth_cm")),
                        "lowerDepthCm": _float(row.get("lower_depth_cm")),
                        "summary": row.get("summary") if isinstance(row.get("summary"), dict) else {},
                    }
                )
            dataset_version = dataset_version or str(row.get("dataset_version") or "") or None
            source_url = source_url or str(row.get("source_url") or "") or None
            license_name = license_name or str(row.get("license_name") or "") or None
            updated_at = updated_at or _isoformat(row.get("updated_at"))
        return {
            "site": {
                "nsiId": site.get("nsi_id"),
                "location": {"lat": _float(site.get("lat")), "lon": _float(site.get("lon"))},
                "seriesName": site.get("series_name"),
                "variant": site.get("variant"),
                "subgroup": site.get("subgroup"),
                "landUse": site.get("landuse"),
                "madeGround": site.get("madeground"),
                "rockType": site.get("rocktype"),
                "surveyDate": _isoformat(site.get("survey_date")),
                "altitude": site.get("altitude"),
                "slope": site.get("slope"),
                "aspect": site.get("aspect"),
                "easting": site.get("easting"),
                "northing": site.get("northing"),
            },
            "datasets": list(grouped.values()),
            "provenance": build_provenance(
                product_id="nsi-evidence",
                dataset_version=dataset_version,
                source_url=source_url,
                license_name=license_name,
                updated_at=updated_at,
                warehouse=True,
            ),
        }


@lru_cache(maxsize=1)
def get_landis_warehouse() -> LandisWarehouse:
    return LandisWarehouse.from_settings()
