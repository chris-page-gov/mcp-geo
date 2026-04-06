from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any

try:
    import psycopg
except ImportError:  # pragma: no cover - optional dependency fallback
    psycopg = None  # type: ignore[assignment]

from scripts import landis_ingest


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PORTAL_ARCHIVE = Path.home() / "Data" / "landis_portal_archive_2026-04-04"
_EXTERNAL_PREFIX = "/Volumes/ExtSSD-Data/Data/"
_LOCAL_PREFIX = f"{Path.home()}/Data/"

_THEMATIC_DATASETS: dict[str, dict[str, str]] = {
    "NATMAPsoilscapes": {"productId": "natmap-soilscapes", "codeKey": "SS_ID", "labelKey": "SOILSCAPE"},
    "NATMAPtopsoiltexture": {
        "productId": "natmap-topsoil-texture",
        "codeKey": "TEXTURE",
        "labelKey": "TEXTURE",
    },
    "NATMAPsubsoiltexture": {
        "productId": "natmap-subsoil-texture",
        "codeKey": "TEXTURE",
        "labelKey": "TEXTURE",
    },
    "NATMAPsubstratetexture": {
        "productId": "natmap-substrate-texture",
        "codeKey": "TEXTURE",
        "labelKey": "TEXTURE",
    },
    "NATMAPavailablewater": {
        "productId": "natmap-available-water",
        "codeKey": "AWC",
        "labelKey": "AWC",
    },
    "NATMAPcarbon": {"productId": "natmap-carbon", "codeKey": "TOPOCCLASS", "labelKey": "TOPOCCLASS"},
    "NATMAPwrb2006": {"productId": "natmap-wrb2006", "codeKey": "WRBCODE", "labelKey": "WRB06"},
    "NATMAPregions": {"productId": "natmap-regions", "codeKey": "REGION", "labelKey": "NAME"},
}

_NSI_OBSERVATION_DATASETS = (
    "NSIprofile",
    "NSIfeatures",
    "NSItexture",
    "NSItopsoil1",
    "NSItopsoil2",
    "NSImagnetic",
)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _localize_archive_path(raw_path: str) -> Path:
    localized = raw_path.replace(_EXTERNAL_PREFIX, _LOCAL_PREFIX, 1)
    return Path(localized).expanduser()


def _dataset_dir(portal_root: Path, dataset_name: str) -> Path:
    matches = sorted(portal_root.glob(f"data_source/*_{dataset_name}"))
    if not matches:
        raise FileNotFoundError(f"Dataset {dataset_name} not found under {portal_root}")
    return matches[0]


def _dataset_context(portal_root: Path, dataset_name: str) -> dict[str, Any]:
    item_dir = _dataset_dir(portal_root, dataset_name)
    inventory = _read_json(item_dir / "inventory_record.json")
    detail = _read_json(item_dir / "item_detail.json")
    summary = _read_json(item_dir / "feature_service" / "download_summary.json")
    files: list[Path] = []
    for layer in summary.get("layers", []):
        if not isinstance(layer, dict):
            continue
        for raw_path in layer.get("files", []):
            if isinstance(raw_path, str):
                files.append(_localize_archive_path(raw_path))
    return {
        "datasetName": dataset_name,
        "itemDir": item_dir,
        "inventory": inventory,
        "detail": detail,
        "summary": summary,
        "files": files,
        "sourceUrl": summary.get("serviceUrl") or inventory.get("url"),
        "licenseName": detail.get("licenseInfo") or inventory.get("licenseInfo") or "",
        "datasetVersion": "2026-03-31-portal",
        "updatedAt": _iso_from_millis(detail.get("modified") or inventory.get("modified")),
    }


def _iso_from_millis(value: Any) -> str | None:
    if value in {None, "", 0}:
        return None
    try:
        millis = float(value)
    except (TypeError, ValueError):
        return None
    if millis <= 0:
        return None
    return dt.datetime.fromtimestamp(millis / 1000.0, tz=dt.timezone.utc).isoformat()


def _iter_features(files: list[Path]) -> list[dict[str, Any]]:
    features: list[dict[str, Any]] = []
    for path in files:
        features.extend(landis_ingest._load_geojson_features(path))
    return features


def _first_present(properties: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = properties.get(key)
        if value is not None:
            return value
    return None


def _normalize_natmap_polygon_feature(
    feature: dict[str, Any],
    *,
    dataset_version: str,
    source_url: str,
    license_name: str,
    updated_at: str | None,
) -> dict[str, Any]:
    properties = feature.get("properties")
    geometry = feature.get("geometry")
    if not isinstance(properties, dict) or not isinstance(geometry, dict):
        raise ValueError("NATMAP polygon feature must include properties and geometry")
    return {
        "map_unit_id": str(properties.get("MUSID") or ""),
        "map_symbol": properties.get("MAP_SYMBOL"),
        "map_unit_name": properties.get("MU_NAME"),
        "description": properties.get("DESC_"),
        "geology": properties.get("GEOLOGY"),
        "dominant_soils": properties.get("DOM_SOILS"),
        "associated_soils": properties.get("ASSOC_SOIL"),
        "site_class": properties.get("SITE"),
        "crop_landuse": properties.get("CROP_LU"),
        "soilscape": properties.get("SOILSCAPE"),
        "drainage": properties.get("DRAINAGE"),
        "fertility": properties.get("FERTILITY"),
        "habitats": properties.get("HABITATS"),
        "drains_to": properties.get("DRAINS_TO"),
        "water_protection": properties.get("WATER_PROT"),
        "soilguide": properties.get("SOILGUIDE"),
        "dataset_version": dataset_version,
        "source_url": source_url,
        "license_name": license_name,
        "updated_at": updated_at,
        "geom": json.dumps(geometry, ensure_ascii=True, separators=(",", ":")),
    }


def _normalize_thematic_feature(
    feature: dict[str, Any],
    *,
    product_id: str,
    code_key: str,
    label_key: str,
    dataset_version: str,
    source_url: str,
    license_name: str,
    updated_at: str | None,
) -> dict[str, Any]:
    properties = feature.get("properties")
    geometry = feature.get("geometry")
    if not isinstance(properties, dict) or not isinstance(geometry, dict):
        raise ValueError("Thematic feature must include properties and geometry")
    metrics = {
        key: value
        for key, value in properties.items()
        if key not in {"OBJECTID", "Shape__Area", "Shape__Length", code_key, label_key}
    }
    return {
        "product_id": product_id,
        "class_code": str(properties.get(code_key) or ""),
        "class_label": str(properties.get(label_key) or ""),
        "metrics": json.dumps(metrics, ensure_ascii=True),
        "dataset_version": dataset_version,
        "source_url": source_url,
        "license_name": license_name,
        "updated_at": updated_at,
        "geom": json.dumps(geometry, ensure_ascii=True, separators=(",", ":")),
    }


def _normalize_nsi_site_feature(
    feature: dict[str, Any],
    *,
    dataset_version: str,
    source_url: str,
    license_name: str,
    updated_at: str | None,
) -> dict[str, Any]:
    properties = feature.get("properties")
    geometry = feature.get("geometry")
    if not isinstance(properties, dict) or not isinstance(geometry, dict):
        raise ValueError("NSI site feature must include properties and geometry")
    return {
        "nsi_id": int(properties.get("NSI_ID") or 0),
        "series_name": properties.get("SERIESNAME"),
        "variant": properties.get("VARIANT"),
        "subgroup": properties.get("SUBGROUP"),
        "landuse": properties.get("LANDUSE"),
        "madeground": properties.get("MADEGROUND"),
        "rocktype": properties.get("ROCKTYPE"),
        "survey_date": _iso_from_millis(properties.get("SURVEYDATE")),
        "altitude": properties.get("ALTITUDE"),
        "slope": properties.get("SLOPE"),
        "aspect": properties.get("ASPECT"),
        "easting": properties.get("EASTING"),
        "northing": properties.get("NORTHING"),
        "dataset_version": dataset_version,
        "source_url": source_url,
        "license_name": license_name,
        "updated_at": updated_at,
        "geom": json.dumps(geometry, ensure_ascii=True, separators=(",", ":")),
    }


def _normalize_nsi_observation_feature(
    feature: dict[str, Any],
    *,
    dataset_id: str,
    dataset_version: str,
    source_url: str,
    license_name: str,
    updated_at: str | None,
) -> dict[str, Any]:
    properties = feature.get("properties")
    geometry = feature.get("geometry")
    if not isinstance(properties, dict) or not isinstance(geometry, dict):
        raise ValueError("NSI observation feature must include properties and geometry")
    top_depth = _first_present(properties, "UPPERDEPTH", "DTOP")
    lower_depth = _first_present(properties, "LOWERDEPTH", "DGLEY")
    label = None
    if dataset_id == "NSIprofile":
        label = f"{properties.get('TEXTURE') or 'profile'} {top_depth}-{lower_depth}cm"
    elif dataset_id == "NSIfeatures":
        label = f"features texture={properties.get('TEXTURE') or 'unknown'}"
    elif dataset_id == "NSItexture":
        label = "texture fractions"
    elif dataset_id.startswith("NSItopsoil"):
        label = f"topsoil chemistry {dataset_id[-1]}"
    elif dataset_id == "NSImagnetic":
        label = "magnetic profile"
    summary = {
        key: value
        for key, value in properties.items()
        if key not in {"OBJECTID", "NSI_ID", "EAST_NSI", "NORTH_NSI", "Shape__Area", "Shape__Length"}
    }
    return {
        "dataset_id": dataset_id,
        "nsi_id": int(properties.get("NSI_ID") or 0),
        "observation_label": label,
        "top_depth_cm": top_depth,
        "lower_depth_cm": lower_depth,
        "summary": json.dumps(summary, ensure_ascii=True),
        "dataset_version": dataset_version,
        "source_url": source_url,
        "license_name": license_name,
        "updated_at": updated_at,
        "geom": json.dumps(geometry, ensure_ascii=True, separators=(",", ":")),
    }


def _replace_json_rows(
    conn: Any,
    *,
    schema: str,
    table: str,
    columns: list[str],
    rows: list[dict[str, Any]],
    geom_expression: str,
    json_columns: set[str] | None = None,
) -> int:
    json_columns = json_columns or set()
    with conn.cursor() as cur:
        cur.execute(f"TRUNCATE TABLE {schema}.{table};")
        placeholders: list[str] = []
        for column in columns:
            if column == "geom":
                placeholders.append(geom_expression)
            elif column in json_columns:
                placeholders.append("%s::jsonb")
            else:
                placeholders.append("%s")
        statement = (
            f"INSERT INTO {schema}.{table} ({', '.join(columns)}) "
            f"VALUES ({', '.join(placeholders)});"
        )
        values = [[row[column] for column in columns] for row in rows]
        cur.executemany(statement, values)
    return len(rows)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load LandIS phase-2 NATMAP and NSI datasets from the local archive.")
    parser.add_argument("--dsn", required=True, help="PostgreSQL/PostGIS DSN")
    parser.add_argument("--schema", default="landis", help="Target schema name")
    parser.add_argument(
        "--portal-archive-root",
        default=str(DEFAULT_PORTAL_ARCHIVE),
        help="Local portal archive root to ingest from",
    )
    parser.add_argument(
        "--products-json",
        default=str(ROOT / "resources" / "landis_products.json"),
        help="Checked-in LandIS product registry JSON path",
    )
    parser.add_argument(
        "--schema-sql",
        default=str(ROOT / "scripts" / "landis_schema.sql"),
        help="SQL file used to create the LandIS schema objects",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    if psycopg is None:
        raise SystemExit("psycopg is required. Install with `pip install -e .[landis]`.")

    portal_root = Path(args.portal_archive_root).expanduser().resolve()
    products_json = Path(args.products_json).expanduser().resolve()
    schema_sql = Path(args.schema_sql).expanduser().resolve()

    with psycopg.connect(args.dsn, autocommit=True) as conn:
        landis_ingest._execute_schema(conn, schema_sql, args.schema)
        product_count = landis_ingest._replace_products(
            conn,
            args.schema,
            landis_ingest._product_rows(products_json),
        )
        print(json.dumps({"stage": "product_registry", "rows": product_count}))

        natmap_ctx = _dataset_context(portal_root, "NationalSoilMap")
        natmap_rows = [
            _normalize_natmap_polygon_feature(
                feature,
                dataset_version=natmap_ctx["datasetVersion"],
                source_url=str(natmap_ctx["sourceUrl"] or ""),
                license_name=str(natmap_ctx["licenseName"] or ""),
                updated_at=natmap_ctx["updatedAt"],
            )
            for feature in _iter_features(natmap_ctx["files"])
        ]
        natmap_count = _replace_json_rows(
            conn,
            schema=args.schema,
            table="natmap_polygons",
            columns=[
                "map_unit_id",
                "map_symbol",
                "map_unit_name",
                "description",
                "geology",
                "dominant_soils",
                "associated_soils",
                "site_class",
                "crop_landuse",
                "soilscape",
                "drainage",
                "fertility",
                "habitats",
                "drains_to",
                "water_protection",
                "soilguide",
                "dataset_version",
                "source_url",
                "license_name",
                "updated_at",
                "geom",
            ],
            rows=natmap_rows,
            geom_expression="ST_Multi(ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326))",
        )
        landis_ingest._replace_provenance(
            conn,
            args.schema,
            dataset_id="natmap-core",
            title="LandIS NATMAP Core",
            source_url=str(natmap_ctx["sourceUrl"] or ""),
            license_name=str(natmap_ctx["licenseName"] or ""),
            dataset_version=natmap_ctx["datasetVersion"],
            row_count=natmap_count,
        )
        print(json.dumps({"stage": "natmap_polygons", "rows": natmap_count}))

        thematic_rows: list[dict[str, Any]] = []
        for dataset_name, config in _THEMATIC_DATASETS.items():
            ctx = _dataset_context(portal_root, dataset_name)
            thematic_rows.extend(
                _normalize_thematic_feature(
                    feature,
                    product_id=config["productId"],
                    code_key=config["codeKey"],
                    label_key=config["labelKey"],
                    dataset_version=ctx["datasetVersion"],
                    source_url=str(ctx["sourceUrl"] or ""),
                    license_name=str(ctx["licenseName"] or ""),
                    updated_at=ctx["updatedAt"],
                )
                for feature in _iter_features(ctx["files"])
            )
        thematic_count = _replace_json_rows(
            conn,
            schema=args.schema,
            table="natmap_thematic_polygons",
            columns=[
                "product_id",
                "class_code",
                "class_label",
                "metrics",
                "dataset_version",
                "source_url",
                "license_name",
                "updated_at",
                "geom",
            ],
            rows=thematic_rows,
            geom_expression="ST_Multi(ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326))",
            json_columns={"metrics"},
        )
        landis_ingest._replace_provenance(
            conn,
            args.schema,
            dataset_id="natmap-thematics",
            title="LandIS NATMAP Thematic Layers",
            source_url=str(natmap_ctx["sourceUrl"] or ""),
            license_name=str(natmap_ctx["licenseName"] or ""),
            dataset_version="2026-03-31-portal",
            row_count=thematic_count,
        )
        print(json.dumps({"stage": "natmap_thematics", "rows": thematic_count}))

        nsi_site_ctx = _dataset_context(portal_root, "NSIsite")
        nsi_site_rows = [
            _normalize_nsi_site_feature(
                feature,
                dataset_version=nsi_site_ctx["datasetVersion"],
                source_url=str(nsi_site_ctx["sourceUrl"] or ""),
                license_name=str(nsi_site_ctx["licenseName"] or ""),
                updated_at=nsi_site_ctx["updatedAt"],
            )
            for feature in _iter_features(nsi_site_ctx["files"])
        ]
        nsi_site_count = _replace_json_rows(
            conn,
            schema=args.schema,
            table="nsi_sites",
            columns=[
                "nsi_id",
                "series_name",
                "variant",
                "subgroup",
                "landuse",
                "madeground",
                "rocktype",
                "survey_date",
                "altitude",
                "slope",
                "aspect",
                "easting",
                "northing",
                "dataset_version",
                "source_url",
                "license_name",
                "updated_at",
                "geom",
            ],
            rows=nsi_site_rows,
            geom_expression="ST_Centroid(ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326))",
        )
        observation_rows: list[dict[str, Any]] = []
        for dataset_name in _NSI_OBSERVATION_DATASETS:
            ctx = _dataset_context(portal_root, dataset_name)
            observation_rows.extend(
                _normalize_nsi_observation_feature(
                    feature,
                    dataset_id=dataset_name,
                    dataset_version=ctx["datasetVersion"],
                    source_url=str(ctx["sourceUrl"] or ""),
                    license_name=str(ctx["licenseName"] or ""),
                    updated_at=ctx["updatedAt"],
                )
                for feature in _iter_features(ctx["files"])
            )
        observation_count = _replace_json_rows(
            conn,
            schema=args.schema,
            table="nsi_observations",
            columns=[
                "dataset_id",
                "nsi_id",
                "observation_label",
                "top_depth_cm",
                "lower_depth_cm",
                "summary",
                "dataset_version",
                "source_url",
                "license_name",
                "updated_at",
                "geom",
            ],
            rows=observation_rows,
            geom_expression="ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326)",
            json_columns={"summary"},
        )
        landis_ingest._replace_provenance(
            conn,
            args.schema,
            dataset_id="nsi-evidence",
            title="LandIS NSI Evidence",
            source_url=str(nsi_site_ctx["sourceUrl"] or ""),
            license_name=str(nsi_site_ctx["licenseName"] or ""),
            dataset_version=nsi_site_ctx["datasetVersion"],
            row_count=nsi_site_count + observation_count,
        )
        print(json.dumps({"stage": "nsi_sites", "rows": nsi_site_count}))
        print(json.dumps({"stage": "nsi_observations", "rows": observation_count}))


if __name__ == "__main__":
    main()
