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
DEFAULT_PORTAL_ARCHIVE_ROOT = Path.home() / "Data"

_THEMATIC_DATASETS: dict[str, dict[str, str]] = {
    "NATMAPsoilscapes": {
        "productId": "natmap-soilscapes",
        "codeKey": "SS_ID",
        "labelKey": "SOILSCAPE",
    },
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
    "NATMAPcarbon": {
        "productId": "natmap-carbon",
        "codeKey": "TOPOCCLASS",
        "labelKey": "TOPOCCLASS",
    },
    "NATMAPwrb2006": {
        "productId": "natmap-wrb2006",
        "codeKey": "WRBCODE",
        "labelKey": "WRB06",
    },
    "NATMAPregions": {
        "productId": "natmap-regions",
        "codeKey": "REGION",
        "labelKey": "NAME",
    },
}

_NSI_OBSERVATION_DATASETS = (
    "NSIprofile",
    "NSIfeatures",
    "NSItexture",
    "NSItopsoil1",
    "NSItopsoil2",
    "NSImagnetic",
)


def _required_portal_dataset_names() -> tuple[str, ...]:
    return (
        "NationalSoilMap",
        *tuple(_THEMATIC_DATASETS.keys()),
        "NSIsite",
        *_NSI_OBSERVATION_DATASETS,
    )


def _portal_archive_validation_errors(portal_root: Path) -> list[str]:
    if not portal_root.is_dir():
        return [f"Portal archive root does not exist: {portal_root}"]

    errors: list[str] = []
    for dataset_name in _required_portal_dataset_names():
        try:
            item_dir = _dataset_dir(portal_root, dataset_name)
        except FileNotFoundError:
            errors.append(f"Missing dataset directory for {dataset_name}")
            continue

        inventory_path = item_dir / "inventory_record.json"
        detail_path = item_dir / "item_detail.json"
        summary_path = item_dir / "feature_service" / "download_summary.json"
        for path in (inventory_path, detail_path, summary_path):
            if not path.is_file():
                errors.append(f"Missing required file for {dataset_name}: {path.name}")
        if not summary_path.is_file():
            continue

        try:
            summary = _read_json(summary_path)
        except json.JSONDecodeError as exc:
            errors.append(f"Invalid download summary for {dataset_name}: {exc}")
            continue
        layers = summary.get("layers")
        if not isinstance(layers, list) or not layers:
            errors.append(f"Download summary for {dataset_name} has no layers")
            continue

        file_count = 0
        for layer in layers:
            if not isinstance(layer, dict):
                continue
            raw_files = layer.get("files")
            if not isinstance(raw_files, list):
                continue
            for raw_path in raw_files:
                if not isinstance(raw_path, str):
                    continue
                file_count += 1
                candidate = _localize_archive_path(raw_path, portal_root=portal_root)
                if not candidate.is_file():
                    errors.append(
                        f"Missing archived layer file for {dataset_name}: {candidate}"
                    )
        if file_count == 0:
            errors.append(f"Download summary for {dataset_name} lists no layer files")
    return errors


def _portal_archive_is_complete(portal_root: Path) -> bool:
    return not _portal_archive_validation_errors(portal_root)


def _latest_portal_archive_dir(root: Path = DEFAULT_PORTAL_ARCHIVE_ROOT) -> Path:
    matches = sorted(path for path in root.glob("landis_portal_archive_*") if path.is_dir())
    for include_smoke in (False, True):
        for path in reversed(matches):
            if not include_smoke and "-smoke" in path.name:
                continue
            if _portal_archive_is_complete(path):
                return path
    return root / "landis_portal_archive_2026-04-04"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _localize_archive_path(raw_path: str, *, portal_root: Path) -> Path:
    candidate = Path(raw_path).expanduser()
    if candidate.exists():
        return candidate

    raw_candidate = Path(raw_path)
    if portal_root.name in raw_candidate.parts:
        suffix = raw_candidate.parts[raw_candidate.parts.index(portal_root.name) + 1 :]
        return portal_root.joinpath(*suffix)

    parent_root_name = portal_root.parent.name
    if parent_root_name:
        indices = [
            index
            for index, part in enumerate(raw_candidate.parts)
            if part == parent_root_name
        ]
        if indices:
            suffix = raw_candidate.parts[indices[-1] + 1 :]
            if suffix:
                return portal_root.parent.joinpath(*suffix)
    return candidate


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
                files.append(_localize_archive_path(raw_path, portal_root=portal_root))
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
    return dt.datetime.fromtimestamp(millis / 1000.0, tz=dt.UTC).isoformat()


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
        if key
        not in {"OBJECTID", "NSI_ID", "EAST_NSI", "NORTH_NSI", "Shape__Area", "Shape__Length"}
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
    parser = argparse.ArgumentParser(
        description="Load LandIS phase-2 NATMAP and NSI datasets from the local archive."
    )
    parser.add_argument("--dsn", required=True, help="PostgreSQL/PostGIS DSN")
    parser.add_argument("--schema", default="landis", help="Target schema name")
    parser.add_argument(
        "--portal-archive-root",
        default=str(_latest_portal_archive_dir()),
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
    parser.add_argument(
        "--validate-archive-root",
        action="store_true",
        help="Validate that the selected portal archive root contains the full phase-2 slice.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    portal_root = Path(args.portal_archive_root).expanduser().resolve()
    products_json = Path(args.products_json).expanduser().resolve()
    schema_sql = Path(args.schema_sql).expanduser().resolve()
    validation_errors = _portal_archive_validation_errors(portal_root)
    if args.validate_archive_root:
        if validation_errors:
            print(
                json.dumps(
                    {
                        "portalArchiveRoot": str(portal_root),
                        "status": "invalid",
                        "errors": validation_errors,
                    },
                    ensure_ascii=True,
                )
            )
            raise SystemExit(1)
        print(
            json.dumps(
                {
                    "portalArchiveRoot": str(portal_root),
                    "status": "ok",
                },
                ensure_ascii=True,
            )
        )
        return

    if validation_errors:
        raise SystemExit(
            "Portal archive root is incomplete: " + "; ".join(validation_errors[:5])
        )
    if psycopg is None:
        raise SystemExit("psycopg is required. Install with `pip install -e .[landis]`.")

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
