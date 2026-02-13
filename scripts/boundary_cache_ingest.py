#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlparse

try:
    import requests
except ImportError:  # pragma: no cover - optional dependency fallback
    requests = None  # type: ignore[assignment]

try:
    import psycopg
except ImportError:  # pragma: no cover - optional dependency fallback
    psycopg = None  # type: ignore[assignment]

SCHEMA_SQL = Path(__file__).resolve().parent / "boundary_cache_schema.sql"


def _fail(message: str) -> None:
    raise SystemExit(message)


def _require_psycopg() -> None:
    if psycopg is None:
        _fail("psycopg is required. Install with `pip install -e .[dev]`.")


def _require_requests() -> None:
    if requests is None:
        _fail("requests is required. Install with `pip install -e .`.")


def _sanitize_table_name(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_]+", "_", value).strip("_").lower()
    return cleaned or "boundary_import"


def _ensure_identifier(value: str, label: str) -> str:
    if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", value):
        _fail(f"Invalid {label}: {value}")
    return value


def _dsn_to_pg(dsn: str) -> str:
    parsed = urlparse(dsn)
    if not parsed.scheme or parsed.scheme not in {"postgresql", "postgres"}:
        return dsn
    user = parsed.username or ""
    password = parsed.password or ""
    host = parsed.hostname or "localhost"
    port = parsed.port or 5432
    dbname = parsed.path.lstrip("/") if parsed.path else ""
    parts = [
        f"dbname='{dbname}'",
        f"host='{host}'",
        f"port='{port}'",
    ]
    if user:
        parts.append(f"user='{user}'")
    if password:
        parts.append(f"password='{password}'")
    return "PG:" + " ".join(parts)


def _download(url: str, dest_dir: Path) -> Path:
    _require_requests()
    dest_dir.mkdir(parents=True, exist_ok=True)
    filename = Path(urlparse(url).path).name or "boundary_download"
    target = dest_dir / filename
    if target.exists():
        return target
    with requests.get(url, stream=True, timeout=60) as resp:
        resp.raise_for_status()
        with target.open("wb") as handle:
            for chunk in resp.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)
    return target


def _run(cmd: list[str]) -> None:
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        _fail(f"Command failed: {' '.join(cmd)}")


def _apply_schema(conn) -> None:
    if not SCHEMA_SQL.exists():
        _fail(f"Missing schema SQL at {SCHEMA_SQL}")
    sql_text = SCHEMA_SQL.read_text(encoding="utf-8")
    with conn.cursor() as cur:
        cur.execute(sql_text)


def _load_with_ogr2ogr(
    *,
    dsn: str,
    input_path: str,
    layer: str | None,
    staging_table: str,
) -> None:
    if shutil.which("ogr2ogr") is None:
        _fail("ogr2ogr is required. Install GDAL to import boundary datasets.")
    pg_conn = _dsn_to_pg(dsn)
    cmd = [
        "ogr2ogr",
        "-f",
        "PostgreSQL",
        pg_conn,
        input_path,
        "-nln",
        staging_table,
        "-lco",
        "GEOMETRY_NAME=geom",
        "-lco",
        "FID=id",
        "-t_srs",
        "EPSG:4326",
        "-nlt",
        "MULTIPOLYGON",
        "-overwrite",
    ]
    if layer:
        cmd.append(layer)
    _run(cmd)


def _upsert_dataset(
    conn,
    *,
    dataset_id: str,
    source: str | None,
    title: str | None,
    url: str | None,
    license_name: str | None,
    release_date: str | None,
    resolution: str | None,
    coverage: str | None,
    notes: str | None,
) -> None:
    release_dt = None
    if release_date:
        release_dt = dt.date.fromisoformat(release_date)
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO boundary_datasets (
                dataset_id,
                source,
                title,
                url,
                license,
                release_date,
                ingested_at,
                resolution,
                coverage,
                notes
            )
            VALUES (%s, %s, %s, %s, %s, %s, NOW(), %s, %s, %s)
            ON CONFLICT (dataset_id)
            DO UPDATE SET
                source = EXCLUDED.source,
                title = EXCLUDED.title,
                url = EXCLUDED.url,
                license = EXCLUDED.license,
                release_date = EXCLUDED.release_date,
                ingested_at = NOW(),
                resolution = EXCLUDED.resolution,
                coverage = EXCLUDED.coverage,
                notes = EXCLUDED.notes;
            """,
            (
                dataset_id,
                source,
                title,
                url,
                license_name,
                release_dt,
                resolution,
                coverage,
                notes,
            ),
        )


def _populate_admin_boundaries(
    conn,
    *,
    staging_table: str,
    dataset_id: str,
    source: str | None,
    level: str,
    id_field: str,
    name_field: str,
    resolution: str,
    resolution_rank: int,
    min_zoom: int | None,
    max_zoom: int | None,
    simplify_tolerance: float | None,
) -> None:
    with conn.cursor() as cur:
        cur.execute("DELETE FROM admin_boundaries WHERE dataset_id = %s", (dataset_id,))
        geom_expr = "geom"
        if simplify_tolerance is not None:
            geom_expr = f"ST_SimplifyPreserveTopology(geom, {simplify_tolerance})"
        cur.execute(
            f"""
            WITH cleaned AS (
                SELECT
                    CAST({id_field} AS TEXT) AS area_id,
                    CAST({name_field} AS TEXT) AS name,
                    ST_Multi(ST_MakeValid({geom_expr})) AS geom_clean
                FROM {staging_table}
                WHERE {id_field} IS NOT NULL
            )
            INSERT INTO admin_boundaries (
                area_id,
                level,
                name,
                resolution,
                resolution_rank,
                min_zoom,
                max_zoom,
                dataset_id,
                geom,
                bbox,
                centroid,
                is_valid,
                valid_reason,
                ingested_at,
                source
            )
            SELECT
                area_id,
                %s AS level,
                name,
                %s AS resolution,
                %s AS resolution_rank,
                %s AS min_zoom,
                %s AS max_zoom,
                %s AS dataset_id,
                geom_clean,
                ST_Envelope(geom_clean),
                ST_PointOnSurface(geom_clean),
                ST_IsValid(geom_clean),
                ST_IsValidReason(geom_clean),
                NOW(),
                %s AS source
            FROM cleaned;
            """,
            (
                level,
                resolution,
                resolution_rank,
                min_zoom,
                max_zoom,
                dataset_id,
                source,
            ),
        )
        cur.execute(
            """
            UPDATE boundary_datasets
            SET record_count = (
                SELECT COUNT(*) FROM admin_boundaries WHERE dataset_id = %s
            )
            WHERE dataset_id = %s;
            """,
            (dataset_id, dataset_id),
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest boundary datasets into PostGIS.")
    parser.add_argument("--dsn", default=os.getenv("BOUNDARY_CACHE_DSN", ""))
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--source")
    parser.add_argument("--title")
    parser.add_argument("--url")
    parser.add_argument("--license")
    parser.add_argument("--release-date", help="YYYY-MM-DD")
    parser.add_argument("--coverage")
    parser.add_argument("--notes")
    parser.add_argument("--level", required=True)
    parser.add_argument("--id-field", required=True)
    parser.add_argument("--name-field", required=True)
    parser.add_argument("--resolution", required=True)
    parser.add_argument("--resolution-rank", type=int, default=0)
    parser.add_argument("--min-zoom", type=int, default=None)
    parser.add_argument("--max-zoom", type=int, default=None)
    parser.add_argument("--simplify-tolerance", type=float, default=None)
    parser.add_argument("--input", help="Local file path or URL to dataset")
    parser.add_argument("--layer", help="OGR layer name (optional)")
    parser.add_argument("--workdir", default="data/boundaries")
    parser.add_argument("--apply-schema", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    _require_psycopg()
    if not args.dsn:
        _fail("Missing --dsn or BOUNDARY_CACHE_DSN")
    if not args.input and not args.url:
        _fail("Provide --input or --url for the dataset source")
    input_path = args.input
    if not input_path and args.url:
        input_path = str(_download(args.url, Path(args.workdir)))
    if not input_path:
        _fail("Unable to resolve dataset input path")
    staging_table = _sanitize_table_name(f"boundary_import_{args.dataset_id}")
    id_field = _ensure_identifier(args.id_field, "id-field")
    name_field = _ensure_identifier(args.name_field, "name-field")
    with psycopg.connect(args.dsn, autocommit=True) as conn:
        if args.apply_schema:
            _apply_schema(conn)
        _load_with_ogr2ogr(
            dsn=args.dsn,
            input_path=input_path,
            layer=args.layer,
            staging_table=staging_table,
        )
        _upsert_dataset(
            conn,
            dataset_id=args.dataset_id,
            source=args.source,
            title=args.title,
            url=args.url,
            license_name=args.license,
            release_date=args.release_date,
            resolution=args.resolution,
            coverage=args.coverage,
            notes=args.notes,
        )
        _populate_admin_boundaries(
            conn,
            staging_table=staging_table,
            dataset_id=args.dataset_id,
            source=args.source,
            level=args.level,
            id_field=id_field,
            name_field=name_field,
            resolution=args.resolution,
            resolution_rank=args.resolution_rank,
            min_zoom=args.min_zoom,
            max_zoom=args.max_zoom,
            simplify_tolerance=args.simplify_tolerance,
        )
    print(json.dumps({"status": "ok", "dataset": args.dataset_id}))


if __name__ == "__main__":
    main()
