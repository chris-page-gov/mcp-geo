from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import server.landis as landis


@pytest.fixture(autouse=True)
def _clear_landis_caches() -> None:
    landis.load_landis_registry.cache_clear()
    landis.load_landis_archive_triage.cache_clear()
    landis.load_landis_full_release_manifest.cache_clear()
    landis.get_landis_warehouse.cache_clear()
    yield
    landis.load_landis_registry.cache_clear()
    landis.load_landis_archive_triage.cache_clear()
    landis.load_landis_full_release_manifest.cache_clear()
    landis.get_landis_warehouse.cache_clear()


class _FakeSQLTemplate:
    def __init__(self, text: str) -> None:
        self.text = text

    def format(self, *, table: object) -> str:
        return self.text.replace("{table}", str(table))


class _FakeSQLModule:
    @staticmethod
    def SQL(text: str) -> _FakeSQLTemplate:
        return _FakeSQLTemplate(text)

    @staticmethod
    def Identifier(*parts: str) -> str:
        return ".".join(parts)


class _FakeCursor:
    def __init__(
        self,
        *,
        row: dict[str, object] | None = None,
        rows: list[dict[str, object]] | None = None,
        execute_error: Exception | None = None,
    ) -> None:
        self._row = row
        self._rows = rows or []
        self.execute_error = execute_error
        self.execute_calls: list[tuple[object, object]] = []

    def __enter__(self) -> _FakeCursor:
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def execute(self, query: object, params: object = None) -> None:
        if self.execute_error is not None:
            raise self.execute_error
        self.execute_calls.append((query, params))

    def fetchone(self) -> dict[str, object] | None:
        return self._row

    def fetchall(self) -> list[dict[str, object]]:
        return self._rows


class _FakeConn:
    def __init__(self, cursor: _FakeCursor) -> None:
        self._cursor = cursor

    def __enter__(self) -> _FakeConn:
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def cursor(self) -> _FakeCursor:
        return self._cursor


class _TestWarehouse(landis.LandisWarehouse):
    def __init__(self, connection: _FakeConn | Exception, *, dsn: str = "postgres://landis") -> None:
        super().__init__(
            dsn=dsn,
            schema="landis",
            product_registry_table="product_registry",
            provenance_table="dataset_provenance",
            soilscapes_table="soilscapes_polygons",
            pipe_risk_table="pipe_risk_polygons",
            natmap_table="natmap_polygons",
            natmap_thematic_table="natmap_thematic_polygons",
            nsi_sites_table="nsi_sites",
            nsi_observations_table="nsi_observations",
        )
        self._connection = connection

    def _connect(self) -> _FakeConn:
        if isinstance(self._connection, Exception):
            raise self._connection
        return self._connection


def _set_registry(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, payload: object) -> Path:
    path = tmp_path / "landis_products.json"
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    monkeypatch.setattr(landis.settings, "LANDIS_REGISTRY_PATH", str(path), raising=False)
    landis.load_landis_registry.cache_clear()
    return path


def _set_json_path(
    monkeypatch: pytest.MonkeyPatch,
    attr: str,
    tmp_path: Path,
    name: str,
    payload: object,
) -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    monkeypatch.setattr(landis.settings, attr, str(path), raising=False)
    return path


def test_registry_loader_handles_missing_invalid_and_valid_payloads(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    missing = tmp_path / "missing.json"
    monkeypatch.setattr(landis.settings, "LANDIS_REGISTRY_PATH", str(missing), raising=False)
    landis.load_landis_registry.cache_clear()
    assert landis.load_landis_registry()["version"] == "missing"
    assert landis.list_landis_products() == []

    invalid = tmp_path / "invalid.json"
    invalid.write_text("{bad json", encoding="utf-8")
    monkeypatch.setattr(landis.settings, "LANDIS_REGISTRY_PATH", str(invalid), raising=False)
    landis.load_landis_registry.cache_clear()
    assert landis.load_landis_registry()["version"] == "invalid"

    _set_registry(
        monkeypatch,
        tmp_path,
        {
            "version": "test-registry",
            "updatedAt": "2026-04-04",
            "sources": [{"title": "Source"}],
            "products": [
                {
                    "id": "soilscapes",
                    "aliases": ["soil-scapes"],
                    "title": "Soilscapes",
                    "resourceUri": "resource://mcp-geo/landis-products",
                    "datasetVersion": "2026-mvp",
                    "sourceUrl": "https://example.test/soilscapes",
                    "license": "test licence",
                    "updatedAt": "2026-04-04",
                    "citations": [{"title": "Citation"}],
                }
            ],
        },
    )
    assert landis.get_landis_product("soil-scapes")["id"] == "soilscapes"
    assert landis.landis_registry_meta()["registryVersion"] == "test-registry"


def test_path_and_area_helpers_cover_supported_and_invalid_inputs(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(landis.settings, "LANDIS_DOCS_DIR", "resources/landis", raising=False)
    docs_dir = landis.landis_docs_dir()
    assert docs_dir.is_absolute()
    assert docs_dir.name == "landis"

    assert landis.parse_bbox([-1.5, 52.0, -1.4, 52.2]) == [-1.5, 52.0, -1.4, 52.2]
    assert landis.parse_bbox([-1.5, 52.0, -1.5, 52.2]) is None
    assert landis.parse_bbox("bad") is None
    assert landis._float("3.5") == 3.5
    assert landis._float("bad") is None
    assert landis._int("4") == 4
    assert landis._int("bad") is None
    assert landis._isoformat(None) is None
    assert landis._isoformat(SimpleNamespace(isoformat=lambda: "2026-04-04T00:00:00Z")) == (
        "2026-04-04T00:00:00Z"
    )

    geometry = landis.bbox_to_geometry([-1.5, 52.0, -1.4, 52.2])
    assert geometry["type"] == "Polygon"
    assert landis.resolve_area_input({"bbox": [-1.5, 52.0, -1.4, 52.2]}) == (
        landis.AreaInput(geometry=geometry, bbox=[-1.5, 52.0, -1.4, 52.2]),
        None,
    )
    feature_input, feature_error = landis.resolve_area_input(
        {
            "geometry": {
                "type": "Feature",
                "geometry": {"type": "MultiPolygon", "coordinates": [[[[0, 0], [1, 0], [1, 1], [0, 0]]]]},
            }
        }
    )
    assert feature_error is None
    assert feature_input is not None
    assert feature_input.geometry["type"] == "MultiPolygon"
    assert landis.resolve_area_input({"geometry": {"type": "Point", "coordinates": [0, 0]}}) == (
        None,
        "geometry must be a GeoJSON Polygon or MultiPolygon",
    )
    assert landis.resolve_area_input({}) == (None, "Provide bbox or geometry")

    local_root = tmp_path / "Data"
    portal_dir = local_root / "landis_portal_archive_2026-04-04"
    release_dir = local_root / "landis_full_release_archive_2026-04-05"
    portal_dir.mkdir(parents=True)
    release_dir.mkdir(parents=True)
    monkeypatch.setattr(landis.settings, "LANDIS_LOCAL_DATA_ROOT", str(local_root), raising=False)
    monkeypatch.setattr(landis.settings, "LANDIS_PORTAL_ARCHIVE_DIR", "", raising=False)
    monkeypatch.setattr(landis.settings, "LANDIS_FULL_RELEASE_ARCHIVE_DIR", "", raising=False)
    assert landis.landis_local_data_root() == local_root
    assert landis.landis_portal_archive_dir() == portal_dir
    assert landis.landis_full_release_archive_dir() == release_dir

    archived_file = portal_dir / "data_source" / "abc" / "item_detail.json"
    archived_file.parent.mkdir(parents=True)
    archived_file.write_text("{}", encoding="utf-8")
    resolved = landis.resolve_landis_archive_file(
        "/Volumes/ExtSSD-Data/Data/landis_portal_archive_2026-04-04/data_source/abc/item_detail.json"
    )
    assert resolved == archived_file


def test_archive_loaders_and_item_helpers(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    triage_payload = {
        "version": "2026-04-05-phase2",
        "generatedAt": "2026-04-05T00:00:00Z",
        "portalItems": [
            {
                "archiveId": "svc-1",
                "title": "NationalSoilMap",
                "aliases": ["National Soil Map"],
                "itemType": "Feature Service",
                "runtimeFamily": "natmap",
                "surfacingClass": "warehouse_next",
                "itemPath": "/Volumes/ExtSSD-Data/Data/landis_portal_archive_2026-04-04/data_source/svc-1",
                "inventoryPath": "/Volumes/ExtSSD-Data/Data/landis_portal_archive_2026-04-04/data_source/svc-1/inventory_record.json",
                "metadataPath": "/Volumes/ExtSSD-Data/Data/landis_portal_archive_2026-04-04/data_source/svc-1/item_detail.json",
            }
        ],
        "supplementaryPublicItems": [],
        "supplementaryDataGovPackages": [],
    }
    release_payload = {
        "generatedAt": "2026-04-05T00:00:00Z",
        "destination": "/Users/crpage/Data/landis_full_release_archive_2026-04-05",
        "publicItems": [{"slug": "host"}],
        "dataGovPackages": [{"name": "soil-series"}],
        "summary": {"status": "ok"},
    }
    _set_json_path(
        monkeypatch,
        "LANDIS_ARCHIVE_TRIAGE_PATH",
        tmp_path,
        "triage.json",
        triage_payload,
    )
    _set_json_path(
        monkeypatch,
        "LANDIS_FULL_RELEASE_MANIFEST_PATH",
        tmp_path,
        "release.json",
        release_payload,
    )
    landis.load_landis_archive_triage.cache_clear()
    landis.load_landis_full_release_manifest.cache_clear()

    local_root = tmp_path / "Data"
    local_root.mkdir()
    monkeypatch.setattr(landis.settings, "LANDIS_LOCAL_DATA_ROOT", str(local_root), raising=False)
    archive_file = local_root / "landis_portal_archive_2026-04-04" / "data_source" / "svc-1" / "item_detail.json"
    archive_file.parent.mkdir(parents=True)
    archive_file.write_text("{}", encoding="utf-8")

    assert landis.load_landis_archive_triage()["version"] == "2026-04-05-phase2"
    assert landis.load_landis_full_release_manifest()["summary"]["status"] == "ok"
    item = landis.get_landis_archive_item("National Soil Map")
    assert item is not None
    detail = landis.archive_item_detail(item)
    assert detail["archiveId"] == "svc-1"
    assert detail["localPaths"]["metadataPath"] == str(archive_file)
    assert landis.landis_registry_meta()["archiveTriageUri"] == "resource://mcp-geo/landis-archive-triage"


def test_build_provenance_prefers_registry_values(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _set_registry(
        monkeypatch,
        tmp_path,
        {
            "version": "test-registry",
            "products": [
                {
                    "id": "pipe-risk",
                    "title": "Pipe Risk",
                    "resourceUri": "resource://mcp-geo/landis-products",
                    "datasetVersion": "2026-mvp",
                    "sourceUrl": "https://example.test/pipe-risk",
                    "license": "test licence",
                    "updatedAt": "2026-04-04",
                    "citations": [{"title": "Citation"}],
                }
            ],
        },
    )
    provenance = landis.build_provenance(product_id="pipe-risk", warehouse=True)
    assert provenance["productId"] == "pipe-risk"
    assert provenance["warehouseBacked"] is True
    assert provenance["citations"] == [{"title": "Citation"}]


def test_landis_warehouse_settings_and_dependency_guards(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(landis.settings, "LANDIS_ENABLED", True, raising=False)
    monkeypatch.setattr(landis.settings, "LANDIS_LIVE_ENABLED", True, raising=False)
    monkeypatch.setattr(landis.settings, "LANDIS_WAREHOUSE_DSN", "", raising=False)
    monkeypatch.setattr(landis.settings, "BOUNDARY_CACHE_DSN", "postgres://fallback", raising=False)
    warehouse = landis.LandisWarehouse.from_settings()
    assert warehouse.enabled() is True

    monkeypatch.setattr(landis.settings, "LANDIS_ENABLED", False, raising=False)
    assert warehouse.disabled_reason() == "landis_disabled"
    monkeypatch.setattr(landis.settings, "LANDIS_ENABLED", True, raising=False)
    monkeypatch.setattr(landis.settings, "LANDIS_LIVE_ENABLED", False, raising=False)
    assert warehouse.disabled_reason() == "landis_live_disabled"
    monkeypatch.setattr(landis.settings, "LANDIS_LIVE_ENABLED", True, raising=False)
    warehouse_without_dsn = _TestWarehouse(_FakeConn(_FakeCursor()), dsn="")
    assert warehouse_without_dsn.disabled_reason() == "landis_warehouse_unconfigured"
    with pytest.raises(landis.LandisWarehouseDisabled):
        warehouse_without_dsn._require_enabled()

    monkeypatch.setattr(landis, "psycopg", None)
    with pytest.raises(landis.LandisWarehouseUnavailable):
        warehouse._connect()

    monkeypatch.setattr(landis, "sql", None)
    with pytest.raises(landis.LandisWarehouseUnavailable):
        warehouse._table_identifier("soilscapes_polygons")


def test_landis_warehouse_point_success_and_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(landis.settings, "LANDIS_ENABLED", True, raising=False)
    monkeypatch.setattr(landis.settings, "LANDIS_LIVE_ENABLED", True, raising=False)
    monkeypatch.setattr(landis, "sql", _FakeSQLModule())
    cursor = _FakeCursor(
        row={
            "class_code": "12",
            "class_name": "Freely draining",
            "dominant_texture": "loamy",
            "drainage_class": "free",
            "carbon_status": "moderate",
            "habitat_note": "arable",
            "scale_label": "Generalized",
            "dataset_version": "2026-mvp",
            "source_url": "https://example.test/soilscapes",
            "license_name": "test licence",
            "updated_at": "2026-04-04",
        }
    )
    warehouse = _TestWarehouse(_FakeConn(cursor))
    result = warehouse.soilscapes_point(lat=52.0, lon=-1.5)
    assert result is not None
    assert result["soilscape"]["code"] == "12"
    assert result["provenance"]["warehouseBacked"] is True
    assert cursor.execute_calls[0][1] == (-1.5, 52.0)

    empty = _TestWarehouse(_FakeConn(_FakeCursor(row=None)))
    assert empty.soilscapes_point(lat=52.0, lon=-1.5) is None


def test_landis_warehouse_point_wraps_runtime_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(landis.settings, "LANDIS_ENABLED", True, raising=False)
    monkeypatch.setattr(landis.settings, "LANDIS_LIVE_ENABLED", True, raising=False)
    monkeypatch.setattr(landis, "sql", _FakeSQLModule())
    warehouse = _TestWarehouse(RuntimeError("boom"))
    with pytest.raises(landis.LandisWarehouseUnavailable):
        warehouse.soilscapes_point(lat=52.0, lon=-1.5)


def test_landis_warehouse_area_summary_success_and_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(landis.settings, "LANDIS_ENABLED", True, raising=False)
    monkeypatch.setattr(landis.settings, "LANDIS_LIVE_ENABLED", True, raising=False)
    monkeypatch.setattr(landis, "sql", _FakeSQLModule())
    rows = [
        {
            "class_code": "12",
            "class_name": "Freely draining",
            "dominant_texture": "loamy",
            "drainage_class": "free",
            "carbon_status": "moderate",
            "habitat_note": "arable",
            "scale_label": "Generalized",
            "area_m2": 60.0,
            "dataset_version": "2026-mvp",
            "source_url": "https://example.test/soilscapes",
            "license_name": "test licence",
            "updated_at": "2026-04-04",
            "input_area_m2": 100.0,
        },
        {
            "class_code": "7",
            "class_name": "Seasonally wet",
            "dominant_texture": "clayey",
            "drainage_class": "poor",
            "carbon_status": "low",
            "habitat_note": "grassland",
            "scale_label": "Generalized",
            "area_m2": 40.0,
            "dataset_version": "2026-mvp",
            "source_url": "https://example.test/soilscapes",
            "license_name": "test licence",
            "updated_at": "2026-04-04",
            "input_area_m2": 100.0,
        },
    ]
    warehouse = _TestWarehouse(_FakeConn(_FakeCursor(rows=rows)))
    summary = warehouse.soilscapes_area_summary(
        geometry={"type": "Polygon", "coordinates": [[[-1.5, 52.0], [-1.4, 52.0], [-1.4, 52.2], [-1.5, 52.0]]]}
    )
    assert summary is not None
    assert summary["areaSqM"] == 100.0
    assert summary["classes"][0]["percent"] == 60.0
    assert summary["dominantClass"]["code"] == "12"

    empty = _TestWarehouse(_FakeConn(_FakeCursor(rows=[])))
    assert empty.soilscapes_area_summary(geometry={"type": "Polygon", "coordinates": []}) is None


@pytest.mark.parametrize(
    ("row", "expected_band"),
    [
        (
            {
                "shrink_swell_code": "S1",
                "shrink_swell_label": "Low",
                "shrink_swell_score": 1,
                "corrosion_code": "C2",
                "corrosion_label": "Low",
                "corrosion_score": 2,
                "area_m2": 100.0,
                "dataset_version": "2026-mvp",
                "source_url": "https://example.test/pipe-risk",
                "license_name": "test licence",
                "updated_at": "2026-04-04",
                "input_area_m2": 100.0,
            },
            "low",
        ),
        (
            {
                "shrink_swell_code": "S3",
                "shrink_swell_label": "Moderate",
                "shrink_swell_score": 3,
                "corrosion_code": "C2",
                "corrosion_label": "Low",
                "corrosion_score": 2,
                "area_m2": 100.0,
                "dataset_version": "2026-mvp",
                "source_url": "https://example.test/pipe-risk",
                "license_name": "test licence",
                "updated_at": "2026-04-04",
                "input_area_m2": 100.0,
            },
            "medium",
        ),
        (
            {
                "shrink_swell_code": "S3",
                "shrink_swell_label": "Moderate",
                "shrink_swell_score": 3,
                "corrosion_code": "C4",
                "corrosion_label": "High",
                "corrosion_score": 4,
                "area_m2": 100.0,
                "dataset_version": "2026-mvp",
                "source_url": "https://example.test/pipe-risk",
                "license_name": "test licence",
                "updated_at": "2026-04-04",
                "input_area_m2": 100.0,
            },
            "high",
        ),
    ],
)
def test_landis_warehouse_pipe_risk_summary_assigns_expected_band(
    monkeypatch: pytest.MonkeyPatch,
    row: dict[str, object],
    expected_band: str,
) -> None:
    monkeypatch.setattr(landis.settings, "LANDIS_ENABLED", True, raising=False)
    monkeypatch.setattr(landis.settings, "LANDIS_LIVE_ENABLED", True, raising=False)
    monkeypatch.setattr(landis, "sql", _FakeSQLModule())
    warehouse = _TestWarehouse(_FakeConn(_FakeCursor(rows=[row])))
    summary = warehouse.pipe_risk_summary(geometry={"type": "Polygon", "coordinates": []})
    assert summary is not None
    assert summary["riskBand"] == expected_band
    assert summary["provenance"]["productId"] == "pipe-risk"


def test_get_landis_warehouse_uses_cached_from_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    landis.get_landis_warehouse.cache_clear()
    sentinel = object()
    monkeypatch.setattr(landis.LandisWarehouse, "from_settings", classmethod(lambda cls: sentinel))
    assert landis.get_landis_warehouse() is sentinel
    assert landis.get_landis_warehouse() is sentinel


def test_landis_warehouse_natmap_queries(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(landis.settings, "LANDIS_ENABLED", True, raising=False)
    monkeypatch.setattr(landis.settings, "LANDIS_LIVE_ENABLED", True, raising=False)
    monkeypatch.setattr(landis, "sql", _FakeSQLModule())

    point_cursor = _FakeCursor(
        row={
            "map_unit_id": "MU1",
            "map_symbol": "SX1",
            "map_unit_name": "Freely draining loams",
            "description": "desc",
            "geology": "mudstone",
            "dominant_soils": "loam",
            "associated_soils": "clay",
            "site_class": "site",
            "crop_landuse": "arable",
            "soilscape": "Soilscape 8",
            "drainage": "free",
            "fertility": "good",
            "habitats": "mixed",
            "drains_to": "river",
            "water_protection": "moderate",
            "soilguide": "guide",
            "dataset_version": "2026-03-31-portal",
            "source_url": "https://portal.landis.org.uk/",
            "license_name": "test",
            "updated_at": "2026-04-05",
        }
    )
    point_result = _TestWarehouse(_FakeConn(point_cursor)).natmap_point(lat=52.0, lon=-1.5)
    assert point_result is not None
    assert point_result["mapUnit"]["mapUnitId"] == "MU1"
    assert point_result["provenance"]["productId"] == "natmap-core"

    area_rows = [
        {
            "map_unit_id": "MU1",
            "map_symbol": "SX1",
            "map_unit_name": "Freely draining loams",
            "soilscape": "Soilscape 8",
            "drainage": "free",
            "fertility": "good",
            "area_m2": 75.0,
            "dataset_version": "2026-03-31-portal",
            "source_url": "https://portal.landis.org.uk/",
            "license_name": "test",
            "updated_at": "2026-04-05",
            "input_area_m2": 100.0,
        }
    ]
    area_result = _TestWarehouse(_FakeConn(_FakeCursor(rows=area_rows))).natmap_area_summary(
        geometry={"type": "Polygon", "coordinates": []}
    )
    assert area_result is not None
    assert area_result["dominantMapUnit"]["mapUnitId"] == "MU1"
    assert area_result["mapUnits"][0]["percent"] == 75.0

    thematic_rows = [
        {
            "product_id": "natmap-carbon",
            "class_code": "4",
            "class_label": "High",
            "metrics": {"TOPOCC": "4"},
            "area_m2": 60.0,
            "dataset_version": "2026-03-31-portal",
            "source_url": "https://portal.landis.org.uk/",
            "license_name": "test",
            "updated_at": "2026-04-05",
            "input_area_m2": 100.0,
        }
    ]
    thematic_result = _TestWarehouse(_FakeConn(_FakeCursor(rows=thematic_rows))).natmap_thematic_area_summary(
        product_id="natmap-carbon",
        geometry={"type": "Polygon", "coordinates": []},
    )
    assert thematic_result is not None
    assert thematic_result["productId"] == "natmap-carbon"
    assert thematic_result["classes"][0]["metrics"] == {"TOPOCC": "4"}


def test_landis_warehouse_nsi_queries(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(landis.settings, "LANDIS_ENABLED", True, raising=False)
    monkeypatch.setattr(landis.settings, "LANDIS_LIVE_ENABLED", True, raising=False)
    monkeypatch.setattr(landis, "sql", _FakeSQLModule())

    nearest_rows = [
        {
            "nsi_id": 101,
            "series_name": "Wickham",
            "variant": None,
            "subgroup": "gley",
            "landuse": "grass",
            "madeground": "No",
            "rocktype": "Mudstone",
            "survey_date": "2026-04-05",
            "altitude": 80,
            "slope": 2,
            "aspect": "N",
            "easting": 430000,
            "northing": 260000,
            "dataset_version": "2026-03-31-portal",
            "source_url": "https://portal.landis.org.uk/",
            "license_name": "test",
            "updated_at": "2026-04-05",
            "lat": 52.2,
            "lon": -1.5,
            "distance_km": 0.321,
        }
    ]
    nearest = _TestWarehouse(_FakeConn(_FakeCursor(rows=nearest_rows))).nsi_nearest_sites(
        lat=52.2,
        lon=-1.5,
        limit=5,
        max_distance_km=3.0,
    )
    assert nearest["sites"][0]["nsiId"] == 101
    assert nearest["provenance"]["productId"] == "nsi-evidence"

    within_rows = [
        {
            "nsi_id": 101,
            "series_name": "Wickham",
            "variant": None,
            "subgroup": "gley",
            "landuse": "grass",
            "madeground": "No",
            "rocktype": "Mudstone",
            "survey_date": "2026-04-05",
            "altitude": 80,
            "slope": 2,
            "aspect": "N",
            "easting": 430000,
            "northing": 260000,
            "dataset_version": "2026-03-31-portal",
            "source_url": "https://portal.landis.org.uk/",
            "license_name": "test",
            "updated_at": "2026-04-05",
            "lat": 52.2,
            "lon": -1.5,
            "total_count": 1,
        }
    ]
    within = _TestWarehouse(_FakeConn(_FakeCursor(rows=within_rows))).nsi_sites_within_area(
        geometry={"type": "Polygon", "coordinates": []},
        limit=25,
        offset=0,
    )
    assert within["sites"][0]["seriesName"] == "Wickham"
    assert within["totalCount"] == 1

    profile = _TestWarehouse(
        _FakeConn(
            _FakeCursor(
                row={
                    "nsi_id": 101,
                    "series_name": "Wickham",
                    "variant": None,
                    "subgroup": "gley",
                    "landuse": "grass",
                    "madeground": "No",
                    "rocktype": "Mudstone",
                    "survey_date": "2026-04-05",
                    "altitude": 80,
                    "slope": 2,
                    "aspect": "N",
                    "easting": 430000,
                    "northing": 260000,
                    "dataset_version": "2026-03-31-portal",
                    "source_url": "https://portal.landis.org.uk/",
                    "license_name": "test",
                    "updated_at": "2026-04-05",
                    "lat": 52.2,
                    "lon": -1.5,
                },
                rows=[
                    {
                        "dataset_id": "NSIprofile",
                        "observation_label": "profile 0-30cm",
                        "top_depth_cm": 0,
                        "lower_depth_cm": 30,
                        "summary": {"texture": "clay"},
                        "dataset_version": "2026-03-31-portal",
                        "source_url": "https://portal.landis.org.uk/",
                        "license_name": "test",
                        "updated_at": "2026-04-05",
                    }
                ],
            )
        )
    ).nsi_profile_summary(nsi_id=101)
    assert profile is not None
    assert profile["site"]["nsiId"] == 101
    assert profile["datasets"][0]["datasetId"] == "NSIprofile"
