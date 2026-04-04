from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    import geopandas as gpd  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover - optional dependency fallback
    gpd = None

try:
    import psycopg
except ImportError:  # pragma: no cover - optional dependency fallback
    psycopg = None  # type: ignore[assignment]


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PRODUCTS_JSON = ROOT / "resources" / "landis_products.json"
DEFAULT_SCHEMA_SQL = ROOT / "scripts" / "landis_schema.sql"


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_geojson_features(path: Path) -> list[dict[str, Any]]:
    payload = _read_json(path)
    if not isinstance(payload, dict) or payload.get("type") != "FeatureCollection":
        raise ValueError(f"{path} must be a GeoJSON FeatureCollection")
    features = payload.get("features")
    if not isinstance(features, list):
        raise ValueError(f"{path} is missing FeatureCollection.features")
    return [feature for feature in features if isinstance(feature, dict)]


def _load_features(path: Path) -> list[dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix in {".json", ".geojson"}:
        return _load_geojson_features(path)
    if gpd is None:
        raise RuntimeError(
            "geopandas is required for non-GeoJSON LandIS sources. "
            "Install with `pip install -e .[landis]`."
        )
    frame = gpd.read_file(path)
    payload = json.loads(frame.to_json())
    features = payload.get("features") if isinstance(payload, dict) else None
    return [feature for feature in features if isinstance(feature, dict)] if isinstance(features, list) else []


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load normalized LandIS MVP layers into PostGIS.")
    parser.add_argument("--dsn", required=True, help="PostgreSQL/PostGIS DSN")
    parser.add_argument("--schema", default="landis", help="Target schema name")
    parser.add_argument(
        "--products-json",
        default=str(DEFAULT_PRODUCTS_JSON),
        help="Checked-in LandIS product registry JSON path",
    )
    parser.add_argument(
        "--schema-sql",
        default=str(DEFAULT_SCHEMA_SQL),
        help="SQL file used to create the LandIS schema objects",
    )
    parser.add_argument("--soilscapes", help="Normalized Soilscapes GeoJSON/GPKG input")
    parser.add_argument("--pipe-risk", help="Normalized pipe-risk GeoJSON/GPKG input")
    parser.add_argument("--dataset-version", default="2026-mvp", help="Dataset version label")
    parser.add_argument("--source-url", default="https://www.landis.org.uk/", help="Source URL")
    parser.add_argument(
        "--license-name",
        default="LandIS open-access status requires operator validation",
        help="Licence label recorded on ingested rows",
    )
    return parser.parse_args()


def _execute_schema(conn: Any, schema_sql: Path, schema_name: str) -> None:
    sql_text = schema_sql.read_text(encoding="utf-8").replace("landis.", f"{schema_name}.")
    sql_text = sql_text.replace(
        "CREATE SCHEMA IF NOT EXISTS landis",
        f"CREATE SCHEMA IF NOT EXISTS {schema_name}",
    )
    with conn.cursor() as cur:
        cur.execute(sql_text)


def _product_rows(products_json: Path) -> list[dict[str, Any]]:
    payload = _read_json(products_json)
    products = payload.get("products") if isinstance(payload, dict) else None
    if not isinstance(products, list):
        raise ValueError("LandIS products JSON must contain a products array")
    rows = []
    for product in products:
        if not isinstance(product, dict):
            continue
        rows.append(
            {
                "product_id": str(product.get("id") or ""),
                "title": str(product.get("title") or ""),
                "family": str(product.get("family") or ""),
                "metadata": json.dumps(product, ensure_ascii=True),
                "resource_uri": str(product.get("resourceUri") or "") or None,
                "dataset_version": str(product.get("datasetVersion") or "") or None,
                "updated_at": str(product.get("updatedAt") or "") or None,
            }
        )
    return [row for row in rows if row["product_id"] and row["title"] and row["family"]]


def _normalize_soilscapes_feature(
    feature: dict[str, Any],
    *,
    dataset_version: str,
    source_url: str,
    license_name: str,
) -> dict[str, Any]:
    properties = feature.get("properties")
    geometry = feature.get("geometry")
    if not isinstance(properties, dict) or not isinstance(geometry, dict):
        raise ValueError("Soilscapes feature must include properties and geometry")
    return {
        "class_code": (
            properties.get("class_code") or properties.get("code") or properties.get("SOILSCAPE")
        ),
        "class_name": (
            properties.get("class_name") or properties.get("name") or properties.get("SOIL_NAME")
        ),
        "dominant_texture": properties.get("dominant_texture") or properties.get("texture"),
        "drainage_class": properties.get("drainage_class") or properties.get("drainage"),
        "carbon_status": properties.get("carbon_status") or properties.get("carbon"),
        "habitat_note": properties.get("habitat_note") or properties.get("habitat"),
        "scale_label": properties.get("scale_label") or "Generalized Soilscapes",
        "dataset_version": dataset_version,
        "source_url": source_url,
        "license_name": license_name,
        "updated_at": properties.get("updated_at") or dataset_version,
        "geom": json.dumps(geometry, ensure_ascii=True, separators=(",", ":")),
    }


def _normalize_pipe_risk_feature(
    feature: dict[str, Any],
    *,
    dataset_version: str,
    source_url: str,
    license_name: str,
) -> dict[str, Any]:
    properties = feature.get("properties")
    geometry = feature.get("geometry")
    if not isinstance(properties, dict) or not isinstance(geometry, dict):
        raise ValueError("Pipe-risk feature must include properties and geometry")
    return {
        "shrink_swell_code": properties.get("shrink_swell_code") or properties.get("shrink_code"),
        "shrink_swell_label": (
            properties.get("shrink_swell_label") or properties.get("shrink_label")
        ),
        "shrink_swell_score": int(
            properties.get("shrink_swell_score") or properties.get("shrink_score") or 0
        ),
        "corrosion_code": properties.get("corrosion_code"),
        "corrosion_label": properties.get("corrosion_label"),
        "corrosion_score": int(properties.get("corrosion_score") or 0),
        "dataset_version": dataset_version,
        "source_url": source_url,
        "license_name": license_name,
        "updated_at": properties.get("updated_at") or dataset_version,
        "geom": json.dumps(geometry, ensure_ascii=True, separators=(",", ":")),
    }


def _replace_rows(
    conn: Any,
    schema: str,
    table: str,
    columns: list[str],
    rows: list[dict[str, Any]],
) -> int:
    with conn.cursor() as cur:
        cur.execute(f"TRUNCATE TABLE {schema}.{table};")
        for row in rows:
            placeholders = ", ".join(["%s"] * len(columns[:-1]))
            statement = (
                f"INSERT INTO {schema}.{table} ({', '.join(columns)}) "
                f"VALUES ({placeholders}, ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326));"
            )
            values = [row[column] for column in columns]
            cur.execute(statement, values)
    return len(rows)


def _replace_products(conn: Any, schema: str, rows: list[dict[str, Any]]) -> int:
    with conn.cursor() as cur:
        cur.execute(f"TRUNCATE TABLE {schema}.product_registry;")
        for row in rows:
            cur.execute(
                f"""
                INSERT INTO {schema}.product_registry
                    (product_id, title, family, metadata, resource_uri, dataset_version, updated_at)
                VALUES (%s, %s, %s, %s::jsonb, %s, %s, %s);
                """,
                (
                    row["product_id"],
                    row["title"],
                    row["family"],
                    row["metadata"],
                    row["resource_uri"],
                    row["dataset_version"],
                    row["updated_at"],
                ),
            )
    return len(rows)


def _replace_provenance(
    conn: Any,
    schema: str,
    *,
    dataset_id: str,
    title: str,
    source_url: str,
    license_name: str,
    dataset_version: str,
    row_count: int,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            f"""
            INSERT INTO {schema}.dataset_provenance
                (dataset_id, title, source_url, license_name, dataset_version, details)
            VALUES (%s, %s, %s, %s, %s, %s::jsonb)
            ON CONFLICT (dataset_id) DO UPDATE
            SET title = EXCLUDED.title,
                source_url = EXCLUDED.source_url,
                license_name = EXCLUDED.license_name,
                dataset_version = EXCLUDED.dataset_version,
                checked_at = NOW(),
                details = EXCLUDED.details;
            """,
            (
                dataset_id,
                title,
                source_url,
                license_name,
                dataset_version,
                json.dumps({"rowCount": row_count}, ensure_ascii=True),
            ),
        )


def main() -> None:
    args = _parse_args()
    if psycopg is None:
        raise SystemExit("psycopg is required. Install with `pip install -e .[landis]`.")

    products_json = Path(args.products_json).expanduser().resolve()
    schema_sql = Path(args.schema_sql).expanduser().resolve()
    soilscapes_path = Path(args.soilscapes).expanduser().resolve() if args.soilscapes else None
    pipe_risk_path = Path(args.pipe_risk).expanduser().resolve() if args.pipe_risk else None

    with psycopg.connect(args.dsn, autocommit=True) as conn:
        _execute_schema(conn, schema_sql, args.schema)
        product_count = _replace_products(conn, args.schema, _product_rows(products_json))
        print(json.dumps({"stage": "product_registry", "rows": product_count}))

        if soilscapes_path:
            soilscapes_rows = [
                _normalize_soilscapes_feature(
                    feature,
                    dataset_version=args.dataset_version,
                    source_url=args.source_url,
                    license_name=args.license_name,
                )
                for feature in _load_features(soilscapes_path)
            ]
            row_count = _replace_rows(
                conn,
                args.schema,
                "soilscapes_polygons",
                [
                    "class_code",
                    "class_name",
                    "dominant_texture",
                    "drainage_class",
                    "carbon_status",
                    "habitat_note",
                    "scale_label",
                    "dataset_version",
                    "source_url",
                    "license_name",
                    "updated_at",
                    "geom",
                ],
                soilscapes_rows,
            )
            _replace_provenance(
                conn,
                args.schema,
                dataset_id="soilscapes",
                title="LandIS Soilscapes",
                source_url=args.source_url,
                license_name=args.license_name,
                dataset_version=args.dataset_version,
                row_count=row_count,
            )
            print(json.dumps({"stage": "soilscapes", "rows": row_count}))

        if pipe_risk_path:
            pipe_risk_rows = [
                _normalize_pipe_risk_feature(
                    feature,
                    dataset_version=args.dataset_version,
                    source_url=args.source_url,
                    license_name=args.license_name,
                )
                for feature in _load_features(pipe_risk_path)
            ]
            row_count = _replace_rows(
                conn,
                args.schema,
                "pipe_risk_polygons",
                [
                    "shrink_swell_code",
                    "shrink_swell_label",
                    "shrink_swell_score",
                    "corrosion_code",
                    "corrosion_label",
                    "corrosion_score",
                    "dataset_version",
                    "source_url",
                    "license_name",
                    "updated_at",
                    "geom",
                ],
                pipe_risk_rows,
            )
            _replace_provenance(
                conn,
                args.schema,
                dataset_id="pipe-risk",
                title="LandIS Pipe Risk Screening",
                source_url=args.source_url,
                license_name=args.license_name,
                dataset_version=args.dataset_version,
                row_count=row_count,
            )
            print(json.dumps({"stage": "pipe_risk", "rows": row_count}))


if __name__ == "__main__":
    main()
