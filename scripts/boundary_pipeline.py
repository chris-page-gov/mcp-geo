#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import time
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

try:
    import requests
except ImportError:  # pragma: no cover - optional dependency fallback
    requests = None  # type: ignore[assignment]

try:
    import psycopg
except ImportError:  # pragma: no cover - optional dependency fallback
    psycopg = None  # type: ignore[assignment]

try:
    import pyogrio
except ImportError:  # pragma: no cover - optional dependency fallback
    pyogrio = None  # type: ignore[assignment]

try:
    from shapely.geometry import MultiPolygon, Polygon
    from shapely.ops import transform as shapely_transform
except ImportError:  # pragma: no cover - optional dependency fallback
    MultiPolygon = None  # type: ignore[assignment]
    Polygon = None  # type: ignore[assignment]
    shapely_transform = None  # type: ignore[assignment]

try:
    import pandas as pd
except ImportError:  # pragma: no cover - optional dependency fallback
    pd = None  # type: ignore[assignment]

try:
    from pyproj import Transformer
except ImportError:  # pragma: no cover - optional dependency fallback
    Transformer = None  # type: ignore[assignment]


DEFAULT_MANIFEST = "docs/Boundaries.json"
DEFAULT_CHECKLIST = "docs/boundaries_completion_checklist.json"
DEFAULT_DSN = "postgresql://mcp_geo:mcp_geo@postgis:5432/mcp_geo"


@dataclass
class RunPaths:
    root: Path
    downloads: Path
    extracts: Path
    evidence: Path
    evidence_ckan: Path
    evidence_meta: Path
    evidence_checksums: Path


def _fail(message: str) -> None:
    raise SystemExit(message)


def _require_requests() -> None:
    if requests is None:
        _fail("requests is required. Install with `pip install -e .`.")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def _sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _timestamp_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _ensure_paths(base_dir: Path) -> RunPaths:
    root = base_dir / _timestamp_slug()
    downloads = root / "downloads"
    extracts = root / "extracts"
    evidence = root / "evidence"
    evidence_ckan = evidence / "ckan_package_show_responses"
    evidence_meta = evidence / "source_page_metadata"
    evidence_checksums = evidence / "checksums"
    for path in [downloads, extracts, evidence_ckan, evidence_meta, evidence_checksums]:
        path.mkdir(parents=True, exist_ok=True)
    return RunPaths(
        root=root,
        downloads=downloads,
        extracts=extracts,
        evidence=evidence,
        evidence_ckan=evidence_ckan,
        evidence_meta=evidence_meta,
        evidence_checksums=evidence_checksums,
    )


def _extract_variant(text: str, regex: str) -> str | None:
    match = re.search(regex, text, flags=re.IGNORECASE)
    if not match:
        return None
    return match.group(1).upper()


def _extract_vintage(text: str) -> str | None:
    if not text:
        return None
    match = re.search(r"((January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})", text)
    if match:
        return match.group(1).replace(" ", "_")
    match = re.search(r"\b(19|20)\d{2}\b", text)
    if match:
        return match.group(0)
    return None


def _resource_matches(resource: dict[str, Any], preference: list[dict[str, Any]]) -> int:
    fmt = str(resource.get("format", "")).lower()
    name = str(resource.get("name", "")).lower()
    desc = str(resource.get("description", "")).lower()
    for score, rule in enumerate(preference, start=1):
        formats = [f.lower() for f in rule.get("format_any_of", [])]
        must_contain = str(rule.get("must_contain", "")).lower()
        if any(f in fmt for f in formats):
            base_score = len(preference) - score + 1
            if not must_contain:
                return base_score
            if must_contain in name or must_contain in desc:
                return base_score
            return max(1, base_score - 1)
    return 0


def _clean_query(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _strip_after_boundaries(text: str) -> str:
    match = re.search(r"\bBoundaries\b", text, flags=re.IGNORECASE)
    if not match:
        return text
    return text[: match.end()].strip()


def _build_ckan_query_candidates(query: str) -> list[str]:
    base = _clean_query(query).replace('"', "")
    if not base:
        return []
    stripped = _strip_after_boundaries(base)
    candidates: list[str] = []

    def _add(q: str | None) -> None:
        if not q:
            return
        q = _clean_query(q)
        if q and q not in candidates:
            candidates.append(q)

    if re.search(r"\bBoundaries\b", stripped, flags=re.IGNORECASE):
        _add(f'title:"{stripped}"')
    else:
        _add(f'title:"{stripped}" AND title:Boundaries')

    if stripped != base:
        if re.search(r"\bBoundaries\b", base, flags=re.IGNORECASE):
            _add(f'title:"{base}"')
        else:
            _add(f'title:"{base}" AND title:Boundaries')

    _add(f'"{stripped}"' if stripped else f'"{base}"')
    if "boundaries" not in base.lower():
        _add(f'"{base}" Boundaries')
        _add(f"{base} Boundaries")
    _add(base)
    return candidates


def _format_allowlist(preference: list[dict[str, Any]]) -> set[str]:
    allowed = set()
    for rule in preference:
        for fmt in rule.get("format_any_of", []) or []:
            allowed.add(str(fmt).lower())
    allowed.update(
        {
            "geopackage",
            "gpkg",
            "shapefile",
            "shp",
            "geojson",
            "json",
            "gml",
            "filegdb",
            "fgdb",
        }
    )
    return allowed


def _is_geospatial_resource(resource: dict[str, Any], allowed_formats: set[str]) -> bool:
    fmt = str(resource.get("format", "")).lower()
    name = str(resource.get("name", "")).lower()
    desc = str(resource.get("description", "")).lower()
    for token in allowed_formats:
        if token and (token in fmt or token in name or token in desc):
            return True
    return False


def _filter_packages(packages: list[dict[str, Any]], allowed_formats: set[str]) -> list[dict[str, Any]]:
    filtered: list[dict[str, Any]] = []
    for pkg in packages:
        resources = pkg.get("resources", []) or []
        if any(_is_geospatial_resource(resource, allowed_formats) for resource in resources):
            filtered.append(pkg)
    return filtered


def _download(
    url: str,
    dest: Path,
    *,
    headers: dict[str, str] | None = None,
    allow_redirects: bool = True,
    max_attempts: int = 6,
    wait_seconds: float = 10.0,
) -> tuple[int, str]:
    _require_requests()
    if dest.exists():
        return dest.stat().st_size, _sha256_path(dest)
    attempt = 0
    while attempt < max_attempts:
        attempt += 1
        with requests.get(
            url,
            stream=True,
            timeout=120,
            headers=headers,
            allow_redirects=allow_redirects,
        ) as resp:
            resp.raise_for_status()
            content_type = resp.headers.get("Content-Type", "").lower()
            if "application/json" in content_type:
                payload = resp.json()
                status = str(payload.get("status", "")).lower()
                download_url = payload.get("downloadUrl") or payload.get("url")
                if download_url and download_url != url:
                    url = download_url
                    continue
                if status in {"pending", "inprogress", "in_progress"} and attempt < max_attempts:
                    time.sleep(wait_seconds * attempt)
                    continue
                raise RuntimeError(f"download_not_ready:{status or 'unknown'}")
            with dest.open("wb") as handle:
                for chunk in resp.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        handle.write(chunk)
        return dest.stat().st_size, _sha256_path(dest)
    raise RuntimeError("download_not_ready:max_attempts_exceeded")


def _list_archive(path: Path) -> list[str]:
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as zf:
            return zf.namelist()
    return [path.name]


def _archive_uncompressed_bytes(path: Path) -> int:
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as zf:
            return sum(info.file_size for info in zf.infolist())
    return path.stat().st_size


def _download_looks_valid(path: Path) -> bool:
    if zipfile.is_zipfile(path):
        return True
    name = path.name.lower()
    try:
        with path.open("rb") as handle:
            header = handle.read(256)
    except OSError:
        return False
    if b"Redirecting" in header or b"redirecting" in header:
        return False
    if path.suffix.lower() == ".zip" or "shapefile" in name:
        return False
    if path.suffix.lower() == ".gpkg" or "geopackage" in name:
        return b"SQLite format 3" in header
    return True


def _extract_archive(path: Path, dest_dir: Path) -> list[Path]:
    if not zipfile.is_zipfile(path):
        return [path]
    dest_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path) as zf:
        zf.extractall(dest_dir)
    return list(dest_dir.rglob("*"))


def _pick_dataset_files(files: Iterable[Path]) -> list[Path]:
    gpkg = [
        f
        for f in files
        if f.is_file()
        and (
            f.suffix.lower() == ".gpkg"
            or f.name.lower() in {"geopackage", "geo_package", "geo-package"}
            or "geopackage" in f.name.lower()
        )
    ]
    if gpkg:
        return gpkg
    shp = [f for f in files if f.is_file() and f.suffix.lower() == ".shp"]
    if shp:
        return shp
    geojson = [
        f for f in files if f.is_file() and f.suffix.lower() in {".geojson", ".json"}
    ]
    if geojson:
        return geojson
    return []


def _ensure_postgis(conn) -> None:
    with conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS postgis;")


def _ensure_schema(conn, schema: str) -> None:
    with conn.cursor() as cur:
        cur.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema}";')


def _infer_sql_type(series) -> str:
    if pd is None:
        return "TEXT"
    if pd.api.types.is_integer_dtype(series):
        return "BIGINT"
    if pd.api.types.is_float_dtype(series):
        return "DOUBLE PRECISION"
    if pd.api.types.is_bool_dtype(series):
        return "BOOLEAN"
    return "TEXT"


def _detect_fields(columns: list[str], regex: str | None) -> str | None:
    if not regex:
        return None
    pattern = re.compile(regex, flags=re.IGNORECASE)
    for col in columns:
        if pattern.match(col):
            return col
    return None


def _regex_from_fields(fields: list[str] | None) -> str | None:
    if not fields:
        return None
    escaped = [re.escape(field) for field in fields if field]
    if not escaped:
        return None
    return "^(" + "|".join(escaped) + ")$"


def _source_hints(manifest: dict[str, Any], source_id: str | None) -> dict[str, Any]:
    if not source_id:
        return {}
    sources = manifest.get("catalogue_sources", [])
    source = next((s for s in sources if s.get("source_id") == source_id), None)
    if not source:
        return {}
    hints = source.get("http_hints", {}) or {}
    headers = {}
    user_agent = hints.get("user_agent")
    if user_agent:
        headers["User-Agent"] = user_agent
    allow_redirects = hints.get("follow_redirects")
    return {
        "headers": headers,
        "allow_redirects": True if allow_redirects is None else bool(allow_redirects),
    }


def _coerce_multipolygon(geom):
    if MultiPolygon is None or Polygon is None:
        return geom
    if geom is None:
        return None
    if geom.geom_type == "Polygon":
        return MultiPolygon([geom])
    return geom


def _reproject_geometry(geom, transformer):
    if transformer is None or shapely_transform is None or geom is None:
        return geom
    return shapely_transform(transformer.transform, geom)


def _read_dataframe(dataset_path: Path, layer: str | None = None):
    if pyogrio is None:
        return None
    return pyogrio.read_dataframe(dataset_path.as_posix(), layer=layer)


def _list_layers(dataset_path: Path) -> list[str]:
    if pyogrio is None:
        return []
    layers = pyogrio.list_layers(dataset_path.as_posix())
    return [entry[0] for entry in layers]


def _geom_column_name(df) -> str:
    if hasattr(df, "geometry"):
        return df.geometry.name
    return "geometry"


def _sanitize_identifier(value: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9_]+", "_", value).strip("_").lower()
    return safe or "layer"


def _ingest_dataframe(
    conn,
    *,
    df,
    schema: str,
    table: str,
    target_srid: int,
) -> dict[str, Any]:
    if pd is None:
        return {"ingest_status": "error", "error": "pandas not installed"}
    geom_col = _geom_column_name(df)
    columns = [col for col in df.columns if col != geom_col]
    with conn.cursor() as cur:
        cur.execute(f'DROP TABLE IF EXISTS "{schema}"."{table}" CASCADE;')
        column_defs = []
        for col in columns:
            col_type = _infer_sql_type(df[col])
            column_defs.append(f'"{col}" {col_type}')
        column_defs.append(f'"geom" geometry(MultiPolygon, {target_srid})')
        cur.execute(
            f'CREATE TABLE "{schema}"."{table}" ({", ".join(column_defs)});'
        )
    transformer = None
    src_epsg = None
    if getattr(df, "crs", None) is not None:
        try:
            src_epsg = int(df.crs.to_epsg()) if df.crs else None
        except Exception:
            src_epsg = None
    if src_epsg and src_epsg != target_srid and Transformer is not None:
        transformer = Transformer.from_crs(src_epsg, target_srid, always_xy=True)
    insert_cols = columns + ["geom"]
    col_sql = ", ".join([f'"{col}"' for col in insert_cols])
    geom_placeholder = f"ST_GeomFromWKB(%s, {target_srid})"
    placeholders = ", ".join(["%s"] * len(columns) + [geom_placeholder])
    sql = f'INSERT INTO "{schema}"."{table}" ({col_sql}) VALUES ({placeholders})'
    rows: list[tuple[Any, ...]] = []
    for _, row in df.iterrows():
        values = []
        for col in columns:
            value = row.get(col)
            if pd.isna(value):
                value = None
            values.append(value)
        geom = row.get(geom_col)
        geom = _coerce_multipolygon(geom)
        if transformer:
            geom = _reproject_geometry(geom, transformer)
        values.append(geom.wkb if geom is not None else None)
        rows.append(tuple(values))
        if len(rows) >= 1000:
            with conn.cursor() as cur:
                cur.executemany(sql, rows)
            rows = []
    if rows:
        with conn.cursor() as cur:
            cur.executemany(sql, rows)
    return {"ingest_status": "ok"}


def _validation_queries(
    conn,
    schema: str,
    table: str,
    code_col: str | None,
    row_min: int,
    *,
    allow_duplicate_codes: bool = False,
) -> dict[str, Any]:
    validations: dict[str, Any] = {}
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=%s AND table_name=%s AND column_name='geom';",
            (schema, table),
        )
        geom_column_exists = cur.fetchone()[0] > 0
        srid = None
        if geom_column_exists:
            cur.execute(f'SELECT ST_SRID(geom) FROM "{schema}"."{table}" LIMIT 1;')
            row = cur.fetchone()
            srid = row[0] if row else None
        cur.execute(f'SELECT COUNT(*) FROM "{schema}"."{table}";')
        row_count = cur.fetchone()[0]
    validations["ingest"] = {
        "geom_column_exists": geom_column_exists,
        "srid": srid,
        "row_count": row_count,
    }
    if code_col and not allow_duplicate_codes:
        with conn.cursor() as cur:
            cur.execute(
                f'SELECT COUNT(*) FROM (SELECT "{code_col}", COUNT(*) c FROM "{schema}"."{table}" GROUP BY "{code_col}" HAVING COUNT(*) > 1) t;'
            )
            validations["uniqueness"] = {"duplicate_code_count": cur.fetchone()[0]}
    with conn.cursor() as cur:
        cur.execute(f'SELECT COUNT(*) FROM "{schema}"."{table}" WHERE NOT ST_IsValid(geom);')
        invalid_count = cur.fetchone()[0]
    if invalid_count:
        with conn.cursor() as cur:
            cur.execute(f'UPDATE "{schema}"."{table}" SET geom = ST_MakeValid(geom) WHERE NOT ST_IsValid(geom);')
        with conn.cursor() as cur:
            cur.execute(f'SELECT COUNT(*) FROM "{schema}"."{table}" WHERE NOT ST_IsValid(geom);')
            post_invalid = cur.fetchone()[0]
        validations["geometry"] = {
            "invalid_geom_count": invalid_count,
            "repair_attempted": True,
            "post_repair_invalid_geom_count": post_invalid,
        }
    else:
        validations["geometry"] = {
            "invalid_geom_count": 0,
            "repair_attempted": False,
            "post_repair_invalid_geom_count": 0,
        }
    validations["row_count"] = {"row_count": validations["ingest"]["row_count"], "row_count_min": row_min}
    return validations


def _table_size_bytes(conn, schema: str, table: str) -> int | None:
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT pg_total_relation_size(%s::regclass);",
                (f"{schema}.{table}",),
            )
            row = cur.fetchone()
    except Exception:
        return None
    if not row:
        return None
    return int(row[0]) if row[0] is not None else None


def _ckan_search(
    session,
    *,
    family_id: str,
    api_url: str,
    params: dict[str, Any],
    paths: RunPaths,
    attempt: int,
) -> tuple[dict[str, Any], Path]:
    resp = session.get(api_url, params=params, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    evidence_path = paths.evidence_ckan / f"{family_id}_package_search_{attempt:02d}.json"
    _write_json(evidence_path, {"request": params, "response": data})
    return data, evidence_path


def resolve_downloads(
    family: dict[str, Any],
    template: dict[str, Any],
    manifest: dict[str, Any],
    paths: RunPaths,
    session,
) -> dict[str, Any]:
    required_variants = manifest["completion_definition"]["required_variants"]
    resolved: dict[str, Any] = {}
    downloads = family.get("downloads")
    if downloads:
        source_id = family.get("source_id") or family.get("category")
        http_hints = _source_hints(manifest, source_id)
        for variant in required_variants:
            matches = [d for d in downloads if d.get("variant") == variant]
            if matches:
                resolved[variant] = {
                    "status": "resolved",
                    "download_url": matches[0].get("url"),
                    "download_candidates": [
                        {
                            "url": m.get("url"),
                            "format": m.get("format"),
                            "http_hints": http_hints,
                        }
                        for m in matches
                        if m.get("url")
                    ],
                    "source_id": source_id or "direct_download",
                    "format": matches[0].get("format"),
                    "http_hints": http_hints,
                }
            else:
                evidence_path = paths.evidence_meta / f"{family['family_id']}_{variant}_not_published.json"
                _write_json(
                    evidence_path,
                    {
                        "family_id": family["family_id"],
                        "variant": variant,
                        "status": "not_published",
                        "reason": "variant_not_listed_in_manifest_downloads",
                    },
                )
                resolved[variant] = {
                    "status": "not_published",
                    "evidence_ref": str(evidence_path.relative_to(paths.root)),
                }
        return resolved
    discovery = family.get("discovery") or template.get("discovery")
    if not discovery:
        for variant in required_variants:
            evidence_path = paths.evidence_meta / f"{family['family_id']}_{variant}_not_published.json"
            _write_json(
                evidence_path,
                {
                    "family_id": family["family_id"],
                    "variant": variant,
                    "status": "not_published",
                    "reason": "no_discovery_config",
                },
            )
            resolved[variant] = {
                "status": "not_published",
                "evidence_ref": str(evidence_path.relative_to(paths.root)),
            }
        return resolved
    source_id = discovery.get("source_id")
    source = next((s for s in manifest["catalogue_sources"] if s["source_id"] == source_id), None)
    if not source:
        for variant in required_variants:
            resolved[variant] = {"status": "not_published", "reason": "missing_source"}
        return resolved
    if discovery.get("method") == "fixed_api_endpoint":
        _require_requests()
        download_request = discovery.get("download_request")
        resp = session.get(download_request, allow_redirects=False, timeout=60)
        url = resp.headers.get("Location") or download_request
        resolved["BFC"] = {
            "status": "resolved",
            "download_url": url,
            "source_id": source_id,
        }
        for variant in required_variants:
            if variant != "BFC":
                evidence_path = paths.evidence_meta / f"{family['family_id']}_{variant}_not_published.json"
                _write_json(
                    evidence_path,
                    {
                        "family_id": family["family_id"],
                        "variant": variant,
                        "status": "not_published",
                        "reason": "boundaryline_not_variant_specific",
                    },
                )
                resolved[variant] = {
                    "status": "not_published",
                    "evidence_ref": str(evidence_path.relative_to(paths.root)),
                }
        return resolved
    if discovery.get("method") == "ckan_package_search":
        _require_requests()
        query = discovery.get("query") or family.get("discovery_overrides", {}).get("query") or ""
        organisation = discovery.get("ckan_organisation") or template.get("discovery", {}).get(
            "ckan_organisation"
        )
        tags_any = (
            family.get("discovery_overrides", {}).get("tags_any")
            or discovery.get("tags_any")
            or []
        )
        fq_parts = []
        if organisation:
            fq_parts.append(f"organization:{organisation}")
        fq_org = " AND ".join(fq_parts)
        fq_with_tags = fq_org
        if tags_any:
            tag_query = " OR ".join([f"tags:{tag}" for tag in tags_any])
            fq_with_tags = " AND ".join([fq_org, f"({tag_query})"]) if fq_org else f"({tag_query})"
        query_candidates = _build_ckan_query_candidates(query)
        if not query_candidates and query:
            query_candidates = [query]
        preference = template.get("discovery", {}).get("resource_preference", [])
        allowed_formats = _format_allowlist(preference)
        packages: list[dict[str, Any]] = []
        evidence_path = None
        attempt = 0
        fq_candidates = []
        if fq_with_tags:
            fq_candidates.append(fq_with_tags)
        if fq_org and fq_org not in fq_candidates:
            fq_candidates.append(fq_org)
        if not fq_candidates:
            fq_candidates.append("")
        for candidate in query_candidates:
            for fq in fq_candidates:
                attempt += 1
                params = {"q": candidate, "rows": 200, "sort": "metadata_modified desc"}
                if fq:
                    params["fq"] = fq
                data, attempt_path = _ckan_search(
                    session,
                    family_id=family["family_id"],
                    api_url=source["api"]["package_search"],
                    params=params,
                    paths=paths,
                    attempt=attempt,
                )
                candidate_packages = data.get("result", {}).get("results", []) or []
                candidate_packages = _filter_packages(candidate_packages, allowed_formats)
                if candidate_packages:
                    packages = candidate_packages
                    evidence_path = attempt_path
                    break
            if packages:
                break
        if evidence_path is None and attempt:
            evidence_path = paths.evidence_ckan / f"{family['family_id']}_package_search_{attempt:02d}.json"
        variant_regex = template.get("variant_policy", {}).get("variant_detection", {}).get(
            "from_title_regex",
            r"\\b(BFC|BFE|BGC|BUC|BSC)\\b",
        )
        for pkg in packages:
            pkg_title = pkg.get("title", "")
            vintage = _extract_vintage(pkg_title)
            for resource in pkg.get("resources", []) or []:
                if not _is_geospatial_resource(resource, allowed_formats):
                    continue
                resource_name = resource.get("name") or ""
                resource_desc = resource.get("description") or ""
                variant = _extract_variant(resource_name, variant_regex)
                if not variant:
                    variant = _extract_variant(resource_desc, variant_regex)
                if not variant:
                    variant = _extract_variant(pkg_title, variant_regex)
                if not variant:
                    variant = template.get("variant_policy", {}).get("variant_detection", {}).get(
                        "fallback", "BFC"
                    )
                variant = variant.upper()
                if variant not in required_variants:
                    continue
                score = _resource_matches(resource, preference)
                current = resolved.get(variant)
                if current and current.get("score", 0) >= score:
                    continue
                resolved[variant] = {
                    "status": "resolved",
                    "download_url": resource.get("url"),
                    "source_id": source_id,
                    "package_id": pkg.get("id"),
                    "resource_id": resource.get("id"),
                    "format": resource.get("format"),
                    "score": score,
                    "vintage_id": vintage,
                    "evidence_ref": str(evidence_path.relative_to(paths.root)) if evidence_path else None,
                }
        for variant in required_variants:
            if variant not in resolved:
                evidence_path = paths.evidence_meta / f"{family['family_id']}_{variant}_not_published.json"
                _write_json(
                    evidence_path,
                    {
                        "family_id": family["family_id"],
                        "variant": variant,
                        "status": "not_published",
                        "reason": "no_ckan_resource_match",
                    },
                )
                resolved[variant] = {
                    "status": "not_published",
                    "evidence_ref": str(evidence_path.relative_to(paths.root)),
                }
        return resolved
    for variant in required_variants:
        resolved[variant] = {"status": "not_published", "reason": "unsupported_discovery"}
    return resolved


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Boundary ingest pipeline.")
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST)
    parser.add_argument("--checklist", default=DEFAULT_CHECKLIST)
    parser.add_argument("--dsn", default=os.getenv("BOUNDARY_CACHE_DSN", DEFAULT_DSN))
    parser.add_argument("--workdir", default="data/boundary_runs")
    parser.add_argument("--mode", choices=["all", "resolve", "download", "ingest", "validate"], default="all")
    parser.add_argument("--family", action="append", help="Limit to one or more family_id values.")
    parser.add_argument("--variant", action="append", help="Limit to one or more variant values.")
    return parser.parse_args()


def _evaluate_pipeline(report: dict[str, Any], manifest: dict[str, Any], checklist: dict[str, Any]) -> None:
    errors: list[dict[str, Any]] = []
    required_variants = checklist["scope"]["required_variants_path"].split(".")
    required = manifest
    for part in required_variants:
        required = required.get(part, [])
    for family in manifest.get("boundary_families", []):
        family_id = family.get("family_id")
        resolved = report["resolved_resources"].get(family_id, {})
        downloads = report["downloads"].get(family_id, {})
        ingestions = report["ingestions"].get(family_id, {})
        validations = report["validations"].get(family_id, {})
        family_errors = []
        for variant in required:
            resolved_entry = resolved.get(variant)
            if not resolved_entry:
                family_errors.append(f"missing_resolved:{variant}")
                continue
            status = resolved_entry.get("status")
            if status not in {"resolved", "not_published"}:
                family_errors.append(f"invalid_resolved_status:{variant}")
                continue
            if status == "not_published" and not resolved_entry.get("evidence_ref"):
                family_errors.append(f"missing_not_published_evidence:{variant}")
            if status == "resolved":
                download_entry = downloads.get(variant, {})
                if download_entry.get("download_status") != "ok":
                    family_errors.append(f"download_failed:{variant}")
                ingest_entry = ingestions.get(variant, {})
                if not ingest_entry:
                    family_errors.append(f"ingest_failed:{variant}")
                elif isinstance(ingest_entry, dict):
                    if ingest_entry.get("ingest_status") == "error":
                        family_errors.append(f"ingest_failed:{variant}")
                    else:
                        statuses = [
                            entry.get("ingest_status")
                            for entry in ingest_entry.values()
                            if isinstance(entry, dict)
                        ]
                        if statuses:
                            if any(status == "error" for status in statuses):
                                family_errors.append(f"ingest_failed:{variant}")
                            elif not any(status in {"ok", "skipped"} for status in statuses):
                                family_errors.append(f"ingest_failed:{variant}")
                if validations.get(variant):
                    for table_name, val in validations[variant].items():
                        schema_check = val.get("schema", {})
                        if schema_check.get("code_field_present") is False:
                            family_errors.append(f"code_field_missing:{variant}:{table_name}")
                        if schema_check.get("name_field_present") is False:
                            family_errors.append(f"name_field_missing:{variant}:{table_name}")
                        row_check = val.get("row_count", {})
                        if row_check and row_check.get("row_count", 0) < row_check.get("row_count_min", 1):
                            family_errors.append(f"row_count_low:{variant}:{table_name}")
                        geom_check = val.get("geometry", {})
                        if geom_check.get("post_repair_invalid_geom_count", 0) > 0:
                            family_errors.append(f"invalid_geometry:{variant}:{table_name}")
                        uniq_check = val.get("uniqueness", {})
                        if uniq_check and uniq_check.get("duplicate_code_count", 0) > 0:
                            family_errors.append(f"duplicate_codes:{variant}:{table_name}")
        if family_errors:
            errors.append({"family_id": family_id, "errors": family_errors})
            report["family_status"][family_id] = "error"
        else:
            report["family_status"][family_id] = "ok"
    report["errors"] = errors
    report["pipeline_status"] = (
        checklist["final_status_values"]["pass"]
        if not errors and not report["exceptions"]
        else checklist["final_status_values"]["fail"]
    )


def main() -> None:
    args = parse_args()
    manifest_path = Path(args.manifest)
    checklist_path = Path(args.checklist)
    if not manifest_path.exists():
        _fail(f"Missing manifest at {manifest_path}")
    if not checklist_path.exists():
        _fail(f"Missing checklist at {checklist_path}")
    manifest = _load_json(manifest_path)
    checklist = _load_json(checklist_path)
    run_started = datetime.now(timezone.utc).isoformat()
    run_paths = _ensure_paths(Path(args.workdir))
    report: dict[str, Any] = {
        "manifest_version": manifest.get("manifest_version"),
        "run_started_at": run_started,
        "run_finished_at": None,
        "resolved_resources": {},
        "downloads": {},
        "ingestions": {},
        "validations": {},
        "exceptions": [],
        "family_status": {},
        "pipeline_status": None,
    }
    session = requests.Session() if requests else None
    allowed_families = set(args.family or [])
    allowed_variants = {v.upper() for v in (args.variant or [])}
    for family in manifest.get("boundary_families", []):
        family_id = family.get("family_id")
        if allowed_families and family_id not in allowed_families:
            continue
        template_id = family.get("template")
        template = manifest.get("templates", {}).get(template_id, {})
        report["resolved_resources"][family_id] = {}
        report["downloads"][family_id] = {}
        report["ingestions"][family_id] = {}
        report["validations"][family_id] = {}
        try:
            resolved = resolve_downloads(family, template, manifest, run_paths, session)
            report["resolved_resources"][family_id] = resolved
            if args.mode in {"resolve"}:
                report["family_status"][family_id] = "resolved"
                continue
            for variant, resolved_entry in resolved.items():
                if allowed_variants and variant not in allowed_variants:
                    continue
                if resolved_entry.get("status") != "resolved":
                    report["downloads"][family_id][variant] = {
                        "download_status": resolved_entry.get("status"),
                        "evidence_ref": resolved_entry.get("evidence_ref"),
                    }
                    continue
                candidates = resolved_entry.get("download_candidates") or []
                if not candidates and resolved_entry.get("download_url"):
                    candidates = [{"url": resolved_entry.get("download_url"), "format": resolved_entry.get("format")}]
                if not candidates:
                    report["downloads"][family_id][variant] = {
                        "download_status": "error",
                        "error": "missing_download_url",
                    }
                    continue
                attempts = []
                download_success = False
                size = None
                checksum = None
                url = None
                for idx, candidate in enumerate(candidates, start=1):
                    url = candidate.get("url")
                    if not url:
                        attempts.append({"attempt": idx, "status": "error", "error": "missing_url"})
                        continue
                    hints = candidate.get("http_hints") or resolved_entry.get("http_hints") or {}
                    headers = hints.get("headers") if isinstance(hints, dict) else None
                    allow_redirects = (
                        hints.get("allow_redirects", True)
                        if isinstance(hints, dict)
                        else True
                    )
                    filename = Path(url).name.split("?")[0] or f"{variant.lower()}_{idx}"
                    dest = run_paths.downloads / family_id / variant / filename
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    try:
                        size, checksum = _download(
                            url,
                            dest,
                            headers=headers,
                            allow_redirects=bool(allow_redirects),
                        )
                        if not _download_looks_valid(dest):
                            attempts.append(
                                {
                                    "attempt": idx,
                                    "status": "error",
                                    "url": url,
                                    "error": "download_validation_failed",
                                    "path": str(dest),
                                }
                            )
                            continue
                        download_success = True
                        attempts.append({"attempt": idx, "status": "ok", "url": url, "path": str(dest)})
                        break
                    except Exception as exc:
                        status_code = None
                        response_text = None
                        if requests is not None and hasattr(exc, "response") and exc.response is not None:
                            status_code = exc.response.status_code
                            response_text = exc.response.text[:2000]
                        evidence_path = (
                            run_paths.evidence_meta / f"{family_id}_{variant}_download_error_{idx:02d}.json"
                        )
                        _write_json(
                            evidence_path,
                            {
                                "family_id": family_id,
                                "variant": variant,
                                "url": url,
                                "status_code": status_code,
                                "error": str(exc),
                                "response_snippet": response_text,
                            },
                        )
                        attempts.append(
                            {
                                "attempt": idx,
                                "status": "error",
                                "url": url,
                                "status_code": status_code,
                                "error": str(exc),
                                "evidence_ref": str(evidence_path.relative_to(run_paths.root)),
                            }
                        )
                if not download_success:
                    report["downloads"][family_id][variant] = {
                        "download_status": "error",
                        "error": "all_candidates_failed",
                        "attempts": attempts,
                    }
                    continue
                checksum_path = run_paths.evidence_checksums / f"{family_id}_{variant}.sha256"
                checksum_path.write_text(checksum, encoding="utf-8")
                file_list = _list_archive(dest)
                uncompressed_bytes = _archive_uncompressed_bytes(dest)
                report["downloads"][family_id][variant] = {
                    "download_status": "ok",
                    "bytes": size,
                    "archiveUncompressedBytes": uncompressed_bytes,
                    "sha256": checksum,
                    "file_list": file_list,
                    "gdal_readable": pyogrio is not None,
                    "attempts": attempts,
                }
                if args.mode in {"download"}:
                    continue
                if pyogrio is None or pd is None or psycopg is None:
                    report["ingestions"][family_id][variant] = {
                        "ingest_status": "error",
                        "error": "missing_optional_dependencies",
                    }
                    continue
                extracted = _extract_archive(dest, run_paths.extracts / family_id / variant)
                extracted_bytes = sum(
                    path.stat().st_size for path in extracted if path.is_file()
                )
                report["downloads"][family_id][variant]["extractedBytes"] = extracted_bytes
                dataset_files = _pick_dataset_files(extracted)
                if not dataset_files:
                    report["ingestions"][family_id][variant] = {
                        "ingest_status": "error",
                        "error": "no_supported_dataset_file_found",
                    }
                    continue
                strategy = (family.get("ingest") or template.get("ingest") or {}).get("strategy")
                table_results: dict[str, Any] = {}
                with psycopg.connect(args.dsn, autocommit=True) as conn:
                    _ensure_postgis(conn)
                    schema = (family.get("ingest") or {}).get("target_schema") or manifest["postgis_defaults"]["schema"]
                    _ensure_schema(conn, schema)
                    include_dataset_suffix = len(dataset_files) > 1
                    for dataset_file in dataset_files:
                        try:
                            layers = _list_layers(dataset_file)
                        except Exception as exc:
                            table_results[dataset_file.name] = {
                                "ingest_status": "error",
                                "error": f"layer_read_failed:{exc}",
                            }
                            continue
                        layer_targets = layers if strategy == "split_layers_to_tables" and layers else [None]
                        dataset_suffix = _sanitize_identifier(dataset_file.stem) if include_dataset_suffix else ""
                        for layer in layer_targets:
                            try:
                                df = _read_dataframe(dataset_file, layer=layer)
                            except Exception as exc:
                                result_key = layer or dataset_suffix or "default"
                                table_results[result_key] = {
                                    "ingest_status": "error",
                                    "error": f"dataset_read_failed:{exc}",
                                }
                                continue
                            result_key = layer or dataset_suffix or "default"
                            if df is None:
                                table_results[result_key] = {
                                    "ingest_status": "error",
                                    "error": "pyogrio_unavailable",
                                }
                                continue
                            geom_col = _geom_column_name(df)
                            if geom_col not in df.columns:
                                table_results[result_key] = {
                                    "ingest_status": "error",
                                    "error": "missing_geometry_column",
                                }
                                continue
                            geom_types = set(
                                t for t in df[geom_col].geom_type.dropna().unique().tolist()
                            )
                            if geom_types and not geom_types.issubset({"Polygon", "MultiPolygon"}):
                                table_results[result_key] = {
                                    "ingest_status": "skipped",
                                    "reason": "unsupported_geometry_type",
                                    "geometry_types": sorted(geom_types),
                                }
                                continue
                            table_base = manifest["postgis_defaults"]["table_naming"]
                            vintage = (
                                resolved_entry.get("vintage_id")
                                or _extract_vintage(dataset_file.name)
                                or "unknown"
                            )
                            variant_name = variant.lower()
                            table_name = table_base.format(
                                family_id=family_id,
                                variant=variant_name,
                                vintage_id=vintage,
                            )
                            if dataset_suffix:
                                table_name = f"{table_name}__{dataset_suffix}"
                            if layer:
                                table_name = f"{table_name}__{_sanitize_identifier(layer)}"
                            ingest_result = _ingest_dataframe(
                                conn,
                                df=df,
                                schema=schema,
                                table=table_name,
                                target_srid=manifest["postgis_defaults"]["target_srid"],
                            )
                            table_bytes = None
                            if ingest_result.get("ingest_status") == "ok":
                                table_bytes = _table_size_bytes(conn, schema, table_name)
                            table_results[result_key] = {
                                "schema": schema,
                                "table": table_name,
                                "tableBytes": table_bytes,
                                **ingest_result,
                            }
                            overrides = family.get("validation_overrides", {})
                            gk = family.get("geography_key", {}) or {}
                            code_regex = overrides.get("code_column_regex") or _regex_from_fields(
                                gk.get("code_fields")
                            )
                            name_regex = overrides.get("name_column_regex") or _regex_from_fields(
                                gk.get("name_fields")
                            )
                            columns = list(df.columns)
                            code_col = _detect_fields(columns, code_regex)
                            name_col = _detect_fields(columns, name_regex)
                            validations = {
                                "schema": {
                                    "code_field_present": bool(code_col),
                                    "name_field_present": bool(name_col) if name_regex else True,
                                    "detected_code_field": code_col,
                                    "detected_name_field": name_col,
                                    "columns": columns,
                                }
                            }
                            validations.update(
                                _validation_queries(
                                    conn,
                                    schema,
                                    table_name,
                                    code_col,
                                    overrides.get("row_count_sanity", {}).get("min", 1),
                                    allow_duplicate_codes=bool(overrides.get("allow_duplicate_codes")),
                                )
                            )
                            report["validations"][family_id].setdefault(variant, {})[
                                table_name
                            ] = validations
                report["ingestions"][family_id][variant] = table_results
            report["family_status"][family_id] = "processed"
        except Exception as exc:  # pragma: no cover - runtime safety
            report["exceptions"].append({"family_id": family_id, "error": str(exc)})
            report["family_status"][family_id] = "error"
    report["run_finished_at"] = datetime.now(timezone.utc).isoformat()
    _evaluate_pipeline(report, manifest, checklist)
    report_path = run_paths.root / "run_report.json"
    _write_json(report_path, report)
    print(report_path)


if __name__ == "__main__":
    main()
