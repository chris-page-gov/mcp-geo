from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

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


@dataclass(frozen=True)
class BoundaryGeometryResult:
    bbox: list[float] | None
    geometry: dict[str, Any] | None
    meta: dict[str, Any]
    name: str | None
    level: str | None


class BoundaryCache:
    def __init__(
        self,
        *,
        dsn: str,
        schema: str,
        table: str,
        dataset_table: str,
        max_age_days: int,
    ) -> None:
        self._dsn = dsn
        self._schema = schema
        self._table = table
        self._dataset_table = dataset_table
        self._max_age_days = max_age_days

    @classmethod
    def from_settings(cls) -> "BoundaryCache":
        return cls(
            dsn=getattr(settings, "BOUNDARY_CACHE_DSN", ""),
            schema=getattr(settings, "BOUNDARY_CACHE_SCHEMA", "public"),
            table=getattr(settings, "BOUNDARY_CACHE_TABLE", "admin_boundaries"),
            dataset_table=getattr(settings, "BOUNDARY_DATASET_TABLE", "boundary_datasets"),
            max_age_days=int(getattr(settings, "BOUNDARY_CACHE_MAX_AGE_DAYS", 180)),
        )

    def enabled(self) -> bool:
        return bool(getattr(settings, "BOUNDARY_CACHE_ENABLED", False)) and bool(self._dsn)

    def _connect(self):
        if psycopg is None:
            raise RuntimeError("psycopg is not installed")
        return psycopg.connect(self._dsn, row_factory=dict_row)

    def _freshness(self, release_date: Any, ingested_at: Any) -> tuple[bool | None, int | None]:
        if not self._max_age_days:
            return None, None
        now = datetime.now(timezone.utc).date()
        ref_date = None
        if release_date:
            ref_date = release_date
        elif ingested_at:
            ref_date = ingested_at.date() if hasattr(ingested_at, "date") else None
        if not ref_date:
            return None, None
        age_days = (now - ref_date).days
        return age_days <= self._max_age_days, age_days

    def area_geometry(
        self,
        area_id: str,
        *,
        include_geometry: bool,
        zoom: float | None = None,
    ) -> BoundaryGeometryResult | None:
        if not self.enabled():
            return None
        if psycopg is None or sql is None:
            log_upstream_error(
                service="boundary_cache",
                code="BOUNDARY_CACHE_ERROR",
                detail="psycopg not installed",
                error_category=classify_error("BOUNDARY_CACHE_ERROR"),
            )
            return None
        geom_expr = sql.SQL("ST_AsGeoJSON(b.geom)") if include_geometry else sql.SQL("NULL")
        table_ident = sql.Identifier(self._schema, self._table)
        dataset_ident = sql.Identifier(self._schema, self._dataset_table)
        query = sql.SQL(
            """
            SELECT
                b.area_id,
                b.name,
                b.level,
                b.resolution,
                b.min_zoom,
                b.max_zoom,
                b.resolution_rank,
                b.is_valid,
                b.valid_reason,
                b.dataset_id,
                b.source,
                d.title AS dataset_title,
                d.release_date,
                d.ingested_at,
                d.license AS dataset_license,
                ST_XMin(COALESCE(b.bbox, ST_Envelope(b.geom))) AS minx,
                ST_YMin(COALESCE(b.bbox, ST_Envelope(b.geom))) AS miny,
                ST_XMax(COALESCE(b.bbox, ST_Envelope(b.geom))) AS maxx,
                ST_YMax(COALESCE(b.bbox, ST_Envelope(b.geom))) AS maxy,
                {geom_expr} AS geometry
            FROM {table} b
            LEFT JOIN {dataset} d ON d.dataset_id = b.dataset_id
            WHERE b.area_id = %s
              AND (
                %s IS NULL OR (
                  (b.min_zoom IS NULL OR b.min_zoom <= %s)
                  AND (b.max_zoom IS NULL OR b.max_zoom >= %s)
                )
              )
            ORDER BY b.resolution_rank ASC NULLS LAST
            LIMIT 1;
            """
        ).format(table=table_ident, dataset=dataset_ident, geom_expr=geom_expr)
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (area_id, zoom, zoom, zoom))
                    row = cur.fetchone()
            if row is None and zoom is not None:
                with self._connect() as conn:
                    with conn.cursor() as cur:
                        cur.execute(query, (area_id, None, None, None))
                        row = cur.fetchone()
        except Exception as exc:
            log_upstream_error(
                service="boundary_cache",
                code="BOUNDARY_CACHE_ERROR",
                detail=str(exc),
                error_category=classify_error("BOUNDARY_CACHE_ERROR"),
            )
            return None
        if not row:
            return None
        bbox_values = [row.get("minx"), row.get("miny"), row.get("maxx"), row.get("maxy")]
        bbox = None if any(v is None for v in bbox_values) else [float(v) for v in bbox_values]
        geometry = None
        raw_geometry = row.get("geometry")
        if raw_geometry:
            try:
                geometry = json.loads(raw_geometry)
            except (TypeError, json.JSONDecodeError):
                geometry = None
        fresh, age_days = self._freshness(row.get("release_date"), row.get("ingested_at"))
        meta: dict[str, Any] = {
            "level": row.get("level"),
            "source": row.get("source") or "postgis",
            "datasetId": row.get("dataset_id"),
            "datasetTitle": row.get("dataset_title"),
            "datasetLicense": row.get("dataset_license"),
            "resolution": row.get("resolution"),
            "minZoom": row.get("min_zoom"),
            "maxZoom": row.get("max_zoom"),
            "resolutionRank": row.get("resolution_rank"),
            "valid": row.get("is_valid"),
            "validReason": row.get("valid_reason"),
            "geometryFormat": "geojson",
            "releaseDate": row.get("release_date").isoformat()
            if row.get("release_date")
            else None,
            "ingestedAt": row.get("ingested_at").isoformat()
            if row.get("ingested_at")
            else None,
        }
        if fresh is not None:
            meta["fresh"] = fresh
            meta["ageDays"] = age_days
        return BoundaryGeometryResult(
            bbox=bbox,
            geometry=geometry,
            meta=meta,
            name=row.get("name"),
            level=row.get("level"),
        )

    def containing_areas(self, lat: float, lon: float) -> list[dict[str, Any]] | None:
        if not self.enabled():
            return None
        if psycopg is None or sql is None:
            log_upstream_error(
                service="boundary_cache",
                code="BOUNDARY_CACHE_ERROR",
                detail="psycopg not installed",
                error_category=classify_error("BOUNDARY_CACHE_ERROR"),
            )
            return None
        table_ident = sql.Identifier(self._schema, self._table)
        query = sql.SQL(
            """
            SELECT DISTINCT ON (b.area_id)
                b.area_id,
                b.level,
                b.name,
                b.resolution_rank
            FROM {table} b
            WHERE ST_Intersects(
                b.geom,
                ST_SetSRID(ST_Point(%s, %s), 4326)
            )
            ORDER BY b.area_id, b.resolution_rank ASC NULLS LAST;
            """
        ).format(table=table_ident)
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (lon, lat))
                    rows = cur.fetchall() or []
        except Exception as exc:
            log_upstream_error(
                service="boundary_cache",
                code="BOUNDARY_CACHE_ERROR",
                detail=str(exc),
                error_category=classify_error("BOUNDARY_CACHE_ERROR"),
            )
            return None
        return [
            {
                "id": str(row.get("area_id")),
                "level": row.get("level"),
                "name": row.get("name") or str(row.get("area_id")),
            }
            for row in rows
            if row.get("area_id") is not None
        ]

    def find_by_id(self, area_id: str) -> dict[str, Any] | None:
        if not self.enabled():
            return None
        if psycopg is None or sql is None:
            log_upstream_error(
                service="boundary_cache",
                code="BOUNDARY_CACHE_ERROR",
                detail="psycopg not installed",
                error_category=classify_error("BOUNDARY_CACHE_ERROR"),
            )
            return None
        table_ident = sql.Identifier(self._schema, self._table)
        query = sql.SQL(
            """
            SELECT
                b.area_id,
                b.level,
                b.name,
                ST_Y(COALESCE(b.centroid, ST_PointOnSurface(b.geom))) AS lat,
                ST_X(COALESCE(b.centroid, ST_PointOnSurface(b.geom))) AS lon,
                b.resolution_rank
            FROM {table} b
            WHERE b.area_id = %s
            ORDER BY b.resolution_rank ASC NULLS LAST
            LIMIT 1;
            """
        ).format(table=table_ident)
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (area_id,))
                    row = cur.fetchone()
        except Exception as exc:
            log_upstream_error(
                service="boundary_cache",
                code="BOUNDARY_CACHE_ERROR",
                detail=str(exc),
                error_category=classify_error("BOUNDARY_CACHE_ERROR"),
            )
            return None
        if not row:
            return None
        return {
            "id": str(row.get("area_id")),
            "level": row.get("level"),
            "name": row.get("name") or str(row.get("area_id")),
            "lat": row.get("lat"),
            "lon": row.get("lon"),
        }

    def status(self) -> dict[str, Any] | None:
        if not self.enabled():
            return None
        if psycopg is None or sql is None:
            log_upstream_error(
                service="boundary_cache",
                code="BOUNDARY_CACHE_ERROR",
                detail="psycopg not installed",
                error_category=classify_error("BOUNDARY_CACHE_ERROR"),
            )
            return None
        table_ident = sql.Identifier(self._schema, self._table)
        dataset_ident = sql.Identifier(self._schema, self._dataset_table)
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        sql.SQL(
                            """
                            SELECT level,
                                   COUNT(*) AS total,
                                   COUNT(*) FILTER (WHERE geom IS NOT NULL) AS geom_count
                            FROM {table}
                            GROUP BY level
                            ORDER BY level;
                            """
                        ).format(table=table_ident)
                    )
                    per_level = cur.fetchall() or []
                    cur.execute(
                        sql.SQL(
                            """
                            SELECT COUNT(*) AS total,
                                   COUNT(*) FILTER (WHERE geom IS NOT NULL) AS geom_count
                            FROM {table};
                            """
                        ).format(table=table_ident)
                    )
                    totals = cur.fetchone() or {}
                    cur.execute(
                        sql.SQL(
                            """
                            SELECT
                                dataset_id,
                                source,
                                title,
                                release_date,
                                ingested_at,
                                resolution,
                                coverage,
                                record_count,
                                license
                            FROM {dataset}
                            ORDER BY ingested_at DESC NULLS LAST, release_date DESC NULLS LAST
                            LIMIT 200;
                            """
                        ).format(dataset=dataset_ident)
                    )
                    datasets = cur.fetchall() or []
        except Exception as exc:
            log_upstream_error(
                service="boundary_cache",
                code="BOUNDARY_CACHE_ERROR",
                detail=str(exc),
                error_category=classify_error("BOUNDARY_CACHE_ERROR"),
            )
            return None
        per_level_stats = []
        for row in per_level:
            total = int(row.get("total") or 0)
            geom_count = int(row.get("geom_count") or 0)
            per_level_stats.append(
                {
                    "level": row.get("level"),
                    "total": total,
                    "geomCount": geom_count,
                    "geomPct": (geom_count / total) if total else None,
                }
            )
        total = int(totals.get("total") or 0)
        geom_total = int(totals.get("geom_count") or 0)
        dataset_rows = []
        for row in datasets:
            dataset_rows.append(
                {
                    "datasetId": row.get("dataset_id"),
                    "source": row.get("source"),
                    "title": row.get("title"),
                    "releaseDate": row.get("release_date").isoformat()
                    if row.get("release_date")
                    else None,
                    "ingestedAt": row.get("ingested_at").isoformat()
                    if row.get("ingested_at")
                    else None,
                    "resolution": row.get("resolution"),
                    "coverage": row.get("coverage"),
                    "recordCount": row.get("record_count"),
                    "license": row.get("license"),
                }
            )
        return {
            "enabled": True,
            "schema": self._schema,
            "table": self._table,
            "datasetTable": self._dataset_table,
            "total": total,
            "geomCount": geom_total,
            "geomPct": (geom_total / total) if total else None,
            "levels": per_level_stats,
            "datasets": dataset_rows,
            "maxAgeDays": self._max_age_days,
        }

    def search(
        self,
        *,
        query: str | None = None,
        level: str | None = None,
        limit: int = 25,
        include_geometry: bool = False,
    ) -> list[dict[str, Any]] | None:
        if not self.enabled():
            return None
        if psycopg is None or sql is None:
            log_upstream_error(
                service="boundary_cache",
                code="BOUNDARY_CACHE_ERROR",
                detail="psycopg not installed",
                error_category=classify_error("BOUNDARY_CACHE_ERROR"),
            )
            return None
        table_ident = sql.Identifier(self._schema, self._table)
        geom_expr = (
            sql.SQL("ST_AsGeoJSON(b.geom)")
            if include_geometry
            else sql.SQL("NULL")
        )
        clauses = []
        params: list[Any] = []
        if level:
            clauses.append(sql.SQL("b.level = %s"))
            params.append(level)
        if query:
            clauses.append(sql.SQL("(b.area_id ILIKE %s OR b.name ILIKE %s)"))
            like = f"%{query}%"
            params.extend([like, like])
        where_sql = sql.SQL("WHERE ") + sql.SQL(" AND ").join(clauses) if clauses else sql.SQL("")
        params.append(limit)
        query_sql = sql.SQL(
            """
            SELECT
                b.area_id,
                b.name,
                b.level,
                b.dataset_id,
                ST_XMin(COALESCE(b.bbox, ST_Envelope(b.geom))) AS minx,
                ST_YMin(COALESCE(b.bbox, ST_Envelope(b.geom))) AS miny,
                ST_XMax(COALESCE(b.bbox, ST_Envelope(b.geom))) AS maxx,
                ST_YMax(COALESCE(b.bbox, ST_Envelope(b.geom))) AS maxy,
                {geom_expr} AS geometry
            FROM {table} b
            {where}
            ORDER BY b.level, b.area_id
            LIMIT %s;
            """
        ).format(table=table_ident, where=where_sql, geom_expr=geom_expr)
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(query_sql, params)
                    rows = cur.fetchall() or []
        except Exception as exc:
            log_upstream_error(
                service="boundary_cache",
                code="BOUNDARY_CACHE_ERROR",
                detail=str(exc),
                error_category=classify_error("BOUNDARY_CACHE_ERROR"),
            )
            return None
        results = []
        for row in rows:
            bbox_values = [row.get("minx"), row.get("miny"), row.get("maxx"), row.get("maxy")]
            bbox = None if any(v is None for v in bbox_values) else [float(v) for v in bbox_values]
            geometry = None
            raw_geometry = row.get("geometry")
            if raw_geometry:
                try:
                    geometry = json.loads(raw_geometry)
                except (TypeError, json.JSONDecodeError):
                    geometry = None
            results.append(
                {
                    "id": row.get("area_id"),
                    "name": row.get("name"),
                    "level": row.get("level"),
                    "datasetId": row.get("dataset_id"),
                    "bbox": bbox,
                    "geometry": geometry if include_geometry else None,
                }
            )
        return results


_CACHE: BoundaryCache | None = None


def get_boundary_cache() -> BoundaryCache | None:
    global _CACHE
    if _CACHE is None:
        _CACHE = BoundaryCache.from_settings()
    if not _CACHE.enabled():
        return None
    return _CACHE


def reset_boundary_cache() -> None:
    global _CACHE
    _CACHE = None


__all__ = ["BoundaryCache", "BoundaryGeometryResult", "get_boundary_cache", "reset_boundary_cache"]
