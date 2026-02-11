import datetime as dt

import pytest

from server.boundary_cache import BoundaryCache, get_boundary_cache, reset_boundary_cache
from server.config import settings


class _FakeCursor:
    def __init__(self, row=None, rows=None):
        self._row = row
        self._rows = rows or []

    def execute(self, query, params=None):  # noqa: ARG002
        return None

    def fetchone(self):
        return self._row

    def fetchall(self):
        return self._rows

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):  # noqa: ARG002
        return False


class _FakeConn:
    def __init__(self, row=None, rows=None):
        self._row = row
        self._rows = rows or []

    def cursor(self):
        return _FakeCursor(self._row, self._rows)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):  # noqa: ARG002
        return False


class _SeqCursor:
    def __init__(self, responses):
        self._responses = responses
        self._index = -1

    def execute(self, query, params=None):  # noqa: ARG002
        self._index += 1
        return None

    def fetchone(self):
        resp = self._responses[self._index]
        return resp.get("one")

    def fetchall(self):
        resp = self._responses[self._index]
        return resp.get("all", [])

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):  # noqa: ARG002
        return False


class _SeqConn:
    def __init__(self, responses):
        self._responses = responses

    def cursor(self):
        return _SeqCursor(self._responses)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):  # noqa: ARG002
        return False


def test_boundary_cache_disabled_returns_none(monkeypatch):
    reset_boundary_cache()
    monkeypatch.setattr(settings, "BOUNDARY_CACHE_ENABLED", False, raising=False)
    cache = get_boundary_cache()
    assert cache is None


def test_boundary_cache_enabled_returns_instance(monkeypatch):
    reset_boundary_cache()
    monkeypatch.setattr(settings, "BOUNDARY_CACHE_ENABLED", True, raising=False)
    monkeypatch.setattr(settings, "BOUNDARY_CACHE_DSN", "postgresql://example", raising=False)
    cache = get_boundary_cache()
    assert cache is not None


def test_boundary_cache_connect_requires_psycopg(monkeypatch):
    from server import boundary_cache

    cache = BoundaryCache(
        dsn="postgresql://example",
        schema="public",
        table="admin_boundaries",
        dataset_table="boundary_datasets",
        max_age_days=180,
    )
    monkeypatch.setattr(boundary_cache, "psycopg", None)
    with pytest.raises(RuntimeError):
        cache._connect()


def test_boundary_cache_area_geometry_parses_geojson(monkeypatch):
    today = dt.date.today()
    row = {
        "area_id": "E00000001",
        "name": "Test Ward",
        "level": "WARD",
        "resolution": "BGC",
        "min_zoom": 8,
        "max_zoom": 12,
        "resolution_rank": 1,
        "is_valid": True,
        "valid_reason": "Valid Geometry",
        "dataset_id": "ons_ward_2019_bgc",
        "source": "postgis",
        "dataset_title": "Ward boundaries",
        "release_date": today,
        "ingested_at": dt.datetime.now(dt.timezone.utc),
        "dataset_license": "OGL",
        "minx": -0.2,
        "miny": 51.4,
        "maxx": -0.1,
        "maxy": 51.6,
        "geometry": (
            '{"type":"Polygon","coordinates":[[[-0.2,51.4],[-0.1,51.4],'
            '[-0.1,51.6],[-0.2,51.6],[-0.2,51.4]]]}'
        ),
    }
    cache = BoundaryCache(
        dsn="postgresql://example",
        schema="public",
        table="admin_boundaries",
        dataset_table="boundary_datasets",
        max_age_days=180,
    )
    monkeypatch.setattr(settings, "BOUNDARY_CACHE_ENABLED", True, raising=False)
    monkeypatch.setattr(cache, "_connect", lambda: _FakeConn(row=row))

    result = cache.area_geometry("E00000001", include_geometry=True, zoom=10)
    assert result is not None
    assert result.bbox == [-0.2, 51.4, -0.1, 51.6]
    assert result.geometry["type"] == "Polygon"
    assert result.meta["fresh"] is True
    assert result.meta["geometryFormat"] == "geojson"


def test_boundary_cache_area_geometry_fallback_on_zoom(monkeypatch):
    row = {
        "area_id": "E00000001",
        "name": "Test Ward",
        "level": "WARD",
        "resolution": "BGC",
        "min_zoom": 8,
        "max_zoom": 12,
        "resolution_rank": 1,
        "is_valid": True,
        "valid_reason": "Valid Geometry",
        "dataset_id": "ons_ward_2019_bgc",
        "source": "postgis",
        "dataset_title": "Ward boundaries",
        "release_date": dt.date.today(),
        "ingested_at": dt.datetime.now(dt.timezone.utc),
        "dataset_license": "OGL",
        "minx": -0.2,
        "miny": 51.4,
        "maxx": -0.1,
        "maxy": 51.6,
        "geometry": None,
    }

    calls = {"count": 0}

    def _connect():
        calls["count"] += 1
        if calls["count"] == 1:
            return _FakeConn(row=None)
        return _FakeConn(row=row)

    cache = BoundaryCache(
        dsn="postgresql://example",
        schema="public",
        table="admin_boundaries",
        dataset_table="boundary_datasets",
        max_age_days=180,
    )
    monkeypatch.setattr(settings, "BOUNDARY_CACHE_ENABLED", True, raising=False)
    monkeypatch.setattr(cache, "_connect", _connect)
    result = cache.area_geometry("E00000001", include_geometry=False, zoom=20)
    assert result is not None
    assert calls["count"] == 2


def test_boundary_cache_area_geometry_invalid_json(monkeypatch):
    row = {
        "area_id": "E00000001",
        "name": "Test Ward",
        "level": "WARD",
        "resolution": "BGC",
        "min_zoom": 8,
        "max_zoom": 12,
        "resolution_rank": 1,
        "is_valid": True,
        "valid_reason": "Valid Geometry",
        "dataset_id": "ons_ward_2019_bgc",
        "source": "postgis",
        "dataset_title": "Ward boundaries",
        "release_date": dt.date.today(),
        "ingested_at": dt.datetime.now(dt.timezone.utc),
        "dataset_license": "OGL",
        "minx": -0.2,
        "miny": 51.4,
        "maxx": -0.1,
        "maxy": 51.6,
        "geometry": "{not-json}",
    }
    cache = BoundaryCache(
        dsn="postgresql://example",
        schema="public",
        table="admin_boundaries",
        dataset_table="boundary_datasets",
        max_age_days=180,
    )
    monkeypatch.setattr(settings, "BOUNDARY_CACHE_ENABLED", True, raising=False)
    monkeypatch.setattr(cache, "_connect", lambda: _FakeConn(row=row))
    result = cache.area_geometry("E00000001", include_geometry=True, zoom=10)
    assert result is not None
    assert result.geometry is None


def test_boundary_cache_area_geometry_psycopg_missing(monkeypatch):
    from server import boundary_cache

    cache = BoundaryCache(
        dsn="postgresql://example",
        schema="public",
        table="admin_boundaries",
        dataset_table="boundary_datasets",
        max_age_days=180,
    )
    monkeypatch.setattr(settings, "BOUNDARY_CACHE_ENABLED", True, raising=False)
    monkeypatch.setattr(boundary_cache, "psycopg", None)
    monkeypatch.setattr(boundary_cache, "sql", None)
    assert cache.area_geometry("E00000001", include_geometry=True, zoom=10) is None


def test_boundary_cache_area_geometry_error(monkeypatch):
    cache = BoundaryCache(
        dsn="postgresql://example",
        schema="public",
        table="admin_boundaries",
        dataset_table="boundary_datasets",
        max_age_days=180,
    )
    monkeypatch.setattr(settings, "BOUNDARY_CACHE_ENABLED", True, raising=False)

    def _boom():
        raise RuntimeError("db down")

    monkeypatch.setattr(cache, "_connect", _boom)
    assert cache.area_geometry("E00000001", include_geometry=False, zoom=10) is None


def test_boundary_cache_area_geometry_no_row(monkeypatch):
    cache = BoundaryCache(
        dsn="postgresql://example",
        schema="public",
        table="admin_boundaries",
        dataset_table="boundary_datasets",
        max_age_days=180,
    )
    monkeypatch.setattr(settings, "BOUNDARY_CACHE_ENABLED", True, raising=False)
    monkeypatch.setattr(cache, "_connect", lambda: _FakeConn(row=None))
    assert cache.area_geometry("E00000001", include_geometry=False, zoom=None) is None


def test_boundary_cache_containing_areas(monkeypatch):
    rows = [
        {"area_id": "E00000001", "level": "WARD", "name": "Test Ward"},
        {"area_id": "E00000002", "level": "DISTRICT", "name": "Test District"},
    ]
    cache = BoundaryCache(
        dsn="postgresql://example",
        schema="public",
        table="admin_boundaries",
        dataset_table="boundary_datasets",
        max_age_days=180,
    )
    monkeypatch.setattr(settings, "BOUNDARY_CACHE_ENABLED", True, raising=False)
    monkeypatch.setattr(cache, "_connect", lambda: _FakeConn(rows=rows))
    results = cache.containing_areas(51.5, -0.1)
    assert results and results[0]["id"] == "E00000001"


def test_boundary_cache_containing_areas_disabled(monkeypatch):
    cache = BoundaryCache(
        dsn="postgresql://example",
        schema="public",
        table="admin_boundaries",
        dataset_table="boundary_datasets",
        max_age_days=180,
    )
    monkeypatch.setattr(settings, "BOUNDARY_CACHE_ENABLED", False, raising=False)
    assert cache.containing_areas(51.5, -0.1) is None


def test_boundary_cache_containing_areas_psycopg_missing(monkeypatch):
    from server import boundary_cache

    cache = BoundaryCache(
        dsn="postgresql://example",
        schema="public",
        table="admin_boundaries",
        dataset_table="boundary_datasets",
        max_age_days=180,
    )
    monkeypatch.setattr(settings, "BOUNDARY_CACHE_ENABLED", True, raising=False)
    monkeypatch.setattr(boundary_cache, "psycopg", None)
    monkeypatch.setattr(boundary_cache, "sql", None)
    assert cache.containing_areas(51.5, -0.1) is None


def test_boundary_cache_containing_areas_error(monkeypatch):
    cache = BoundaryCache(
        dsn="postgresql://example",
        schema="public",
        table="admin_boundaries",
        dataset_table="boundary_datasets",
        max_age_days=180,
    )
    monkeypatch.setattr(settings, "BOUNDARY_CACHE_ENABLED", True, raising=False)

    def _boom():
        raise RuntimeError("db down")

    monkeypatch.setattr(cache, "_connect", _boom)
    assert cache.containing_areas(51.5, -0.1) is None


def test_boundary_cache_find_by_id(monkeypatch):
    row = {
        "area_id": "E00000003",
        "level": "WARD",
        "name": "Test Ward",
        "lat": 51.5,
        "lon": -0.1,
        "resolution_rank": 0,
    }
    cache = BoundaryCache(
        dsn="postgresql://example",
        schema="public",
        table="admin_boundaries",
        dataset_table="boundary_datasets",
        max_age_days=180,
    )
    monkeypatch.setattr(settings, "BOUNDARY_CACHE_ENABLED", True, raising=False)
    monkeypatch.setattr(cache, "_connect", lambda: _FakeConn(row=row))
    result = cache.find_by_id("E00000003")
    assert result["lat"] == 51.5


def test_boundary_cache_find_by_id_disabled(monkeypatch):
    cache = BoundaryCache(
        dsn="postgresql://example",
        schema="public",
        table="admin_boundaries",
        dataset_table="boundary_datasets",
        max_age_days=180,
    )
    monkeypatch.setattr(settings, "BOUNDARY_CACHE_ENABLED", False, raising=False)
    assert cache.find_by_id("E00000003") is None


def test_boundary_cache_find_by_id_psycopg_missing(monkeypatch):
    from server import boundary_cache

    cache = BoundaryCache(
        dsn="postgresql://example",
        schema="public",
        table="admin_boundaries",
        dataset_table="boundary_datasets",
        max_age_days=180,
    )
    monkeypatch.setattr(settings, "BOUNDARY_CACHE_ENABLED", True, raising=False)
    monkeypatch.setattr(boundary_cache, "psycopg", None)
    monkeypatch.setattr(boundary_cache, "sql", None)
    assert cache.find_by_id("E00000003") is None


def test_boundary_cache_find_by_id_no_row(monkeypatch):
    cache = BoundaryCache(
        dsn="postgresql://example",
        schema="public",
        table="admin_boundaries",
        dataset_table="boundary_datasets",
        max_age_days=180,
    )
    monkeypatch.setattr(settings, "BOUNDARY_CACHE_ENABLED", True, raising=False)
    monkeypatch.setattr(cache, "_connect", lambda: _FakeConn(row=None))
    assert cache.find_by_id("E00000003") is None


def test_boundary_cache_find_by_id_error(monkeypatch):
    cache = BoundaryCache(
        dsn="postgresql://example",
        schema="public",
        table="admin_boundaries",
        dataset_table="boundary_datasets",
        max_age_days=180,
    )
    monkeypatch.setattr(settings, "BOUNDARY_CACHE_ENABLED", True, raising=False)

    def _boom():
        raise RuntimeError("db down")

    monkeypatch.setattr(cache, "_connect", _boom)
    assert cache.find_by_id("E00000003") is None


def test_boundary_cache_freshness_from_ingest_date():
    cache = BoundaryCache(
        dsn="postgresql://example",
        schema="public",
        table="admin_boundaries",
        dataset_table="boundary_datasets",
        max_age_days=1,
    )
    fresh, age_days = cache._freshness(None, dt.datetime.now(dt.timezone.utc))
    assert fresh in (True, False)
    assert age_days is not None


def test_boundary_cache_freshness_no_reference_date():
    cache = BoundaryCache(
        dsn="postgresql://example",
        schema="public",
        table="admin_boundaries",
        dataset_table="boundary_datasets",
        max_age_days=1,
    )
    fresh, age_days = cache._freshness(None, None)
    assert fresh is None
    assert age_days is None


def test_boundary_cache_freshness_disabled():
    cache = BoundaryCache(
        dsn="postgresql://example",
        schema="public",
        table="admin_boundaries",
        dataset_table="boundary_datasets",
        max_age_days=0,
    )
    fresh, age_days = cache._freshness(dt.date.today(), None)
    assert fresh is None
    assert age_days is None


def test_boundary_cache_status(monkeypatch):
    responses = [
        {"all": [{"level": "OA", "total": 2, "geom_count": 2}]},
        {"one": {"total": 2, "geom_count": 2}},
        {
            "all": [
                {
                    "dataset_id": "ons_oa_2021_bgc",
                    "source": "ONS",
                    "title": "OA 2021",
                    "release_date": dt.date.today(),
                    "ingested_at": dt.datetime.now(dt.timezone.utc),
                    "resolution": "BGC",
                    "coverage": "EW",
                    "record_count": 2,
                    "license": "OGL",
                }
            ]
        },
    ]
    cache = BoundaryCache(
        dsn="postgresql://example",
        schema="public",
        table="admin_boundaries",
        dataset_table="boundary_datasets",
        max_age_days=180,
    )
    monkeypatch.setattr(settings, "BOUNDARY_CACHE_ENABLED", True, raising=False)
    monkeypatch.setattr(cache, "_connect", lambda: _SeqConn(responses))
    status = cache.status()
    assert status["enabled"] is True
    assert status["levels"][0]["level"] == "OA"
    assert status["datasets"][0]["datasetId"] == "ons_oa_2021_bgc"
    assert status["datasets"][0]["freshnessState"] in {"fresh", "stale", "unknown"}
    assert status["maturity"]["state"] in {"ready", "degraded", "stale", "unknown", "cold_start", "unusable"}
    assert "staleDatasetIds" in status["staleness"]


def test_boundary_cache_search(monkeypatch):
    rows = [
        {
            "area_id": "E00000001",
            "name": "Test",
            "level": "OA",
            "dataset_id": "ons_oa_2021_bgc",
            "minx": -0.2,
            "miny": 51.4,
            "maxx": -0.1,
            "maxy": 51.6,
            "geometry": '{"type":"Polygon","coordinates":[[[-0.2,51.4],[-0.1,51.4],[-0.1,51.6],[-0.2,51.6],[-0.2,51.4]]]}',
        }
    ]
    cache = BoundaryCache(
        dsn="postgresql://example",
        schema="public",
        table="admin_boundaries",
        dataset_table="boundary_datasets",
        max_age_days=180,
    )
    monkeypatch.setattr(settings, "BOUNDARY_CACHE_ENABLED", True, raising=False)
    monkeypatch.setattr(cache, "_connect", lambda: _FakeConn(rows=rows))
    results = cache.search(query="Test", level="OA", limit=5, include_geometry=True)
    assert results and results[0]["id"] == "E00000001"


def test_boundary_cache_status_psycopg_missing(monkeypatch):
    from server import boundary_cache

    cache = BoundaryCache(
        dsn="postgresql://example",
        schema="public",
        table="admin_boundaries",
        dataset_table="boundary_datasets",
        max_age_days=180,
    )
    monkeypatch.setattr(settings, "BOUNDARY_CACHE_ENABLED", True, raising=False)
    monkeypatch.setattr(boundary_cache, "psycopg", None)
    monkeypatch.setattr(boundary_cache, "sql", None)
    assert cache.status() is None


def test_boundary_cache_status_disabled(monkeypatch):
    cache = BoundaryCache(
        dsn="postgresql://example",
        schema="public",
        table="admin_boundaries",
        dataset_table="boundary_datasets",
        max_age_days=180,
    )
    monkeypatch.setattr(settings, "BOUNDARY_CACHE_ENABLED", False, raising=False)
    assert cache.status() is None


def test_boundary_cache_status_error(monkeypatch):
    cache = BoundaryCache(
        dsn="postgresql://example",
        schema="public",
        table="admin_boundaries",
        dataset_table="boundary_datasets",
        max_age_days=180,
    )
    monkeypatch.setattr(settings, "BOUNDARY_CACHE_ENABLED", True, raising=False)

    def _boom():
        raise RuntimeError("db down")

    monkeypatch.setattr(cache, "_connect", _boom)
    assert cache.status() is None


def test_boundary_cache_search_psycopg_missing(monkeypatch):
    from server import boundary_cache

    cache = BoundaryCache(
        dsn="postgresql://example",
        schema="public",
        table="admin_boundaries",
        dataset_table="boundary_datasets",
        max_age_days=180,
    )
    monkeypatch.setattr(settings, "BOUNDARY_CACHE_ENABLED", True, raising=False)
    monkeypatch.setattr(boundary_cache, "psycopg", None)
    monkeypatch.setattr(boundary_cache, "sql", None)
    assert cache.search(query="Test") is None


def test_boundary_cache_search_disabled(monkeypatch):
    cache = BoundaryCache(
        dsn="postgresql://example",
        schema="public",
        table="admin_boundaries",
        dataset_table="boundary_datasets",
        max_age_days=180,
    )
    monkeypatch.setattr(settings, "BOUNDARY_CACHE_ENABLED", False, raising=False)
    assert cache.search(query="Test") is None


def test_boundary_cache_search_error(monkeypatch):
    cache = BoundaryCache(
        dsn="postgresql://example",
        schema="public",
        table="admin_boundaries",
        dataset_table="boundary_datasets",
        max_age_days=180,
    )
    monkeypatch.setattr(settings, "BOUNDARY_CACHE_ENABLED", True, raising=False)

    def _boom():
        raise RuntimeError("db down")

    monkeypatch.setattr(cache, "_connect", _boom)
    assert cache.search(query="Test") is None


def test_boundary_cache_search_invalid_json(monkeypatch):
    rows = [
        {
            "area_id": "E00000002",
            "name": "Bad Geometry",
            "level": "OA",
            "dataset_id": "ons_oa_2021_bgc",
            "minx": -0.2,
            "miny": 51.4,
            "maxx": -0.1,
            "maxy": 51.6,
            "geometry": "{bad-json}",
        }
    ]
    cache = BoundaryCache(
        dsn="postgresql://example",
        schema="public",
        table="admin_boundaries",
        dataset_table="boundary_datasets",
        max_age_days=180,
    )
    monkeypatch.setattr(settings, "BOUNDARY_CACHE_ENABLED", True, raising=False)
    monkeypatch.setattr(cache, "_connect", lambda: _FakeConn(rows=rows))
    results = cache.search(query="Bad", limit=1, include_geometry=True)
    assert results and results[0]["geometry"] is None
