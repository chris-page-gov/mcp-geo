from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient

import tools.ons_geo as ons_geo_tools
from server import ons_geo_freshness
from server.config import settings
from server.main import app
from server.ons_geo_cache import ONSGeoCacheReadError, ensure_schema

client = TestClient(app)


class _FakeTool:
    def __init__(self, handler):
        self._handler = handler

    def call(self, payload):  # type: ignore[no-untyped-def]
        return self._handler(payload)


def _insert_product(
    conn: sqlite3.Connection,
    *,
    product_id: str,
    key_type: str,
    derivation_mode: str,
    source_name: str,
) -> None:
    conn.execute(
        """
        INSERT INTO ons_geo_products (
            product_id,
            dataset_kind,
            key_type,
            derivation_mode,
            release,
            resolved_release,
            source_name,
            source_path,
            resolved_source_url,
            resolver_type,
            source_format,
            source_sha256,
            schema_fingerprint,
            schema_validation_json,
            record_count,
            status,
            ingested_at,
            retrieved_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            product_id,
            "product",
            key_type,
            derivation_mode,
            "2026-02",
            "April 2026 (Epoch 126)"
            if product_id == "ONSUD"
            else "December 2025 (Epoch 123)"
            if product_id == "NSUL"
            else "2026-02",
            source_name,
            f"{product_id.lower()}.csv",
            (
                "https://example.test/onsud-epoch-126.zip"
                if product_id == "ONSUD"
                else "https://example.test/nsul-epoch-123.zip"
                if product_id == "NSUL"
                else f"https://example.test/{product_id.lower()}.csv"
            ),
            "static_file",
            "csv",
            f"hash-{product_id.lower()}",
            f"schema-{product_id.lower()}",
            json.dumps({"requiredFound": [key_type], "requiredMissing": [], "status": "ok"}),
            1,
            "ingested",
            "2026-02-22T00:00:00Z",
            "2026-02-22T00:00:00Z",
        ),
    )


def _insert_row(
    conn: sqlite3.Connection,
    *,
    product_id: str,
    key_type: str,
    key_norm: str,
    derivation_mode: str,
    source_name: str,
    payload: dict[str, str],
    normalized_payload: dict[str, object] | None = None,
) -> None:
    conn.execute(
        """
        INSERT INTO ons_geo_rows (
            product_id,
            key_type,
            key_norm,
            derivation_mode,
            release,
            source_name,
            product_priority,
            row_json,
            normalized_json,
            cached_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            product_id,
            key_type,
            key_norm,
            derivation_mode,
            "2026-02",
            source_name,
            10,
            json.dumps(payload, ensure_ascii=True),
            json.dumps(normalized_payload or {}, ensure_ascii=True),
            "2026-02-22T00:00:00Z",
        ),
    )


def _seed_cache(tmp_path: Path) -> tuple[Path, str, Path]:
    cache_dir = tmp_path / "ons_geo_cache"
    cache_dir.mkdir(parents=True)
    db_name = "ons_geo_cache.sqlite"
    db_path = cache_dir / db_name
    conn = sqlite3.connect(str(db_path))
    ensure_schema(conn)

    _insert_product(
        conn,
        product_id="ONSPD",
        key_type="postcode",
        derivation_mode="exact",
        source_name="ONSPD",
    )
    _insert_product(
        conn,
        product_id="NSPL",
        key_type="postcode",
        derivation_mode="best_fit",
        source_name="NSPL",
    )
    _insert_product(
        conn,
        product_id="ONSUD",
        key_type="uprn",
        derivation_mode="exact",
        source_name="ONSUD",
    )
    _insert_product(
        conn,
        product_id="NSUL",
        key_type="uprn",
        derivation_mode="best_fit",
        source_name="NSUL",
    )
    _insert_row(
        conn,
        product_id="ONSPD",
        key_type="postcode",
        key_norm="SW1A1AA",
        derivation_mode="exact",
        source_name="ONSPD",
        payload={
            "OA21CD": "E00000111",
            "LSOA21CD": "E01000001",
            "LSOA21NM": "Example LSOA",
            "MSOA21CD": "E02000001",
            "MSOA21NM": "Example MSOA",
            "PARNCP25CD": "E04000001",
            "PARNCP25NM": "Example Parish",
            "PARNCP25NW": "Plwyf Enghreifftiol",
            "LAD24CD": "E09000033",
            "LAD24NM": "Westminster",
            "WD24CD": "E05000001",
            "WD24NM": "Example Ward",
            "CTRY25CD": "E92000001",
            "CTRY25NM": "England",
            "RGN25CD": "E12000007",
            "RGN25NM": "London",
            "oac11ind": "4C1",
        },
        normalized_payload={
            "semanticFields": {
                "postcode": "SW1A1AA",
                "oa_code": "E00000111",
                "lsoa_code": "E01000001",
                "msoa_code": "E02000001",
                "parish_code": "E04000001",
                "lad_code": "E09000033",
                "ward_code": "E05000001",
                "country_code": "E92000001",
                "region_code": "E12000007",
            },
            "geographies": {
                "oa": {"code": "E00000111", "currentCode": "E00000111", "currentName": "E00000111"},
                "lsoa": {
                    "code": "E01000001",
                    "currentCode": "E01000001",
                    "currentName": "Example LSOA",
                    "status": "current",
                    "sourceDataset": "RGC",
                },
                "msoa": {
                    "code": "E02000001",
                    "currentCode": "E02000001",
                    "currentName": "Example MSOA",
                    "status": "current",
                    "sourceDataset": "RGC",
                },
                "parish": {
                    "code": "E04000001",
                    "name": "Example Parish",
                    "nameWelsh": "Plwyf Enghreifftiol",
                    "currentCode": "E04000001",
                    "currentName": "Example Parish",
                    "currentNameWelsh": "Plwyf Enghreifftiol",
                    "status": "current",
                    "sourceDataset": "RGC",
                },
                "lad": {
                    "code": "E09000033",
                    "name": "Westminster",
                    "currentCode": "E09000033",
                    "currentName": "Westminster",
                    "status": "current",
                    "sourceDataset": "RGC",
                },
                "ward": {
                    "code": "E05000001",
                    "currentCode": "E05000001",
                    "currentName": "Example Ward",
                    "status": "current",
                    "sourceDataset": "RGC",
                },
                "country": {
                    "code": "E92000001",
                    "currentCode": "E92000001",
                    "currentName": "England",
                    "status": "current",
                    "sourceDataset": "RGC",
                },
                "region": {
                    "code": "E12000007",
                    "currentCode": "E12000007",
                    "currentName": "London",
                    "status": "current",
                    "sourceDataset": "RGC",
                },
            },
            "codeStatusSummary": {"current": 7},
        },
    )
    _insert_row(
        conn,
        product_id="NSPL",
        key_type="postcode",
        key_norm="SW1A1AA",
        derivation_mode="best_fit",
        source_name="NSPL",
        payload={"LAD24CD": "E09000001", "LAD24NM": "City of London"},
        normalized_payload={
            "semanticFields": {"postcode": "SW1A1AA", "lad_code": "E09000001"},
            "geographies": {
                "lad": {
                    "code": "E09000001",
                    "name": "City of London",
                    "currentCode": "E09000001",
                    "currentName": "City of London",
                    "status": "current",
                    "sourceDataset": "RGC",
                }
            },
            "codeStatusSummary": {"current": 1},
        },
    )
    _insert_row(
        conn,
        product_id="ONSUD",
        key_type="uprn",
        key_norm="100023336959",
        derivation_mode="exact",
        source_name="ONSUD",
        payload={
            "LAD24CD": "E08000026",
            "LAD24NM": "Coventry",
            "MSOA21CD": "E02000001",
            "MSOA21NM": "Example MSOA",
            "PARNCP25CD": "E04000001",
            "PARNCP25NM": "Example Parish",
            "PARNCP25NW": "Plwyf Enghreifftiol",
        },
        normalized_payload={
            "semanticFields": {
                "uprn": "100023336959",
                "msoa_code": "E02000001",
                "parish_code": "E04000001",
                "lad_code": "E08000026",
            },
            "geographies": {
                "msoa": {
                    "code": "E02000001",
                    "currentCode": "E02000001",
                    "currentName": "Example MSOA",
                    "displayName": "Readable MSOA",
                    "displayNameWelsh": "MSOA Darllenadwy",
                    "displayNameSource": {
                        "datasetId": "HOC_MSOA_NAMES_2021",
                        "source": "House of Commons Library MSOA Names",
                        "version": "2.3",
                        "publishedDate": "2026-02-13",
                        "license": "Open Parliament Licence",
                    },
                    "status": "current",
                    "sourceDataset": "RGC",
                },
                "parish": {
                    "code": "E04000001",
                    "name": "Example Parish",
                    "nameWelsh": "Plwyf Enghreifftiol",
                    "currentCode": "E04000001",
                    "currentName": "Example Parish",
                    "currentNameWelsh": "Plwyf Enghreifftiol",
                    "status": "current",
                    "sourceDataset": "RGC",
                },
                "lad": {
                    "code": "E08000026",
                    "name": "Coventry",
                    "currentCode": "E08000026",
                    "currentName": "Coventry",
                    "status": "current",
                    "sourceDataset": "RGC",
                }
            },
            "codeStatusSummary": {"current": 3},
        },
    )
    _insert_row(
        conn,
        product_id="NSUL",
        key_type="uprn",
        key_norm="100023336959",
        derivation_mode="best_fit",
        source_name="NSUL",
        payload={"LAD24CD": "E08000026", "LAD24NM": "Coventry"},
        normalized_payload={
            "semanticFields": {"uprn": "100023336959", "lad_code": "E08000026"},
            "geographies": {
                "lad": {
                    "code": "E08000026",
                    "name": "Coventry",
                    "currentCode": "E08000026",
                    "currentName": "Coventry",
                    "status": "current",
                    "sourceDataset": "RGC",
                }
            },
            "codeStatusSummary": {"current": 1},
        },
    )
    conn.executemany(
        """
        INSERT INTO ons_geo_uprn_index (
            product_id,
            derivation_mode,
            uprn,
            postcode,
            oa_code,
            lsoa_code,
            msoa_code,
            parish_code,
            parish_name,
            parish_name_welsh,
            lad_code,
            lad_name,
            ward_code,
            ward_name,
            country_code,
            country_name,
            region_code,
            region_name,
            postal_delivery,
            geographies_json,
            cached_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                "ONSUD",
                "exact",
                "100000000001",
                "SW1A1AA",
                "E00000111",
                "E01000001",
                "E02000001",
                "E04000001",
                "Example Parish",
                "Plwyf Enghreifftiol",
                "E09000033",
                "Westminster",
                "E05000001",
                "Example Ward",
                "E92000001",
                "England",
                "E12000007",
                "London",
                1,
                json.dumps(
                    {
                        "oa": {"code": "E00000111"},
                        "parish": {
                            "currentCode": "E04000001",
                            "currentName": "Example Parish",
                        },
                    }
                ),
                "2026-02-22T00:00:00Z",
            ),
            (
                "ONSUD",
                "exact",
                "100000000002",
                "SW1A1AA",
                "E00000111",
                "E01000001",
                "E02000001",
                "E04000001",
                "Example Parish",
                "Plwyf Enghreifftiol",
                "E09000033",
                "Westminster",
                "E05000001",
                "Example Ward",
                "E92000001",
                "England",
                "E12000007",
                "London",
                1,
                json.dumps(
                    {
                        "oa": {"code": "E00000111"},
                        "parish": {
                            "currentCode": "E04000001",
                            "currentName": "Example Parish",
                        },
                    }
                ),
                "2026-02-22T00:00:00Z",
            ),
            (
                "ONSUD",
                "exact",
                "100000000003",
                "SW1A2AA",
                "E00000111",
                "E01000001",
                "E02000001",
                "E04000001",
                "Example Parish",
                "Plwyf Enghreifftiol",
                "E09000033",
                "Westminster",
                "E05000001",
                "Example Ward",
                "E92000001",
                "England",
                "E12000007",
                "London",
                0,
                json.dumps(
                    {
                        "oa": {"code": "E00000111"},
                        "parish": {
                            "currentCode": "E04000001",
                            "currentName": "Example Parish",
                        },
                    }
                ),
                "2026-02-22T00:00:00Z",
            ),
        ],
    )
    conn.commit()
    conn.close()

    index_path = tmp_path / "ons_geo_cache_index.json"
    index_path.write_text(
        json.dumps(
            {
                "version": "2026-02-22",
                "generatedAt": "2026-02-22T00:00:00Z",
                "health": {
                    "status": "degraded",
                    "exactReady": True,
                    "bestFitReady": True,
                    "supportReady": True,
                    "freshnessReady": False,
                    "laggingProducts": ["NSUL"],
                    "degradedReasons": ["outdated_addressbase_epochs"],
                },
                "supportProducts": [
                    {"id": "CHD", "status": "ingested"},
                    {"id": "RGC", "status": "ingested"},
                ],
                "products": [
                    {"id": "ONSPD", "derivationMode": "exact", "status": "ingested"},
                    {
                        "id": "ONSUD",
                        "derivationMode": "exact",
                        "status": "ingested",
                        "freshness": {
                            "status": "current",
                            "resolvedEpoch": 126,
                            "latestPublishedEpoch": 126,
                            "lagEpochs": 0,
                        },
                    },
                    {"id": "NSPL", "derivationMode": "best_fit", "status": "ingested"},
                    {
                        "id": "NSUL",
                        "derivationMode": "best_fit",
                        "status": "ingested",
                        "freshness": {
                            "status": "lagging",
                            "resolvedEpoch": 123,
                            "latestPublishedEpoch": 126,
                            "lagEpochs": 3,
                        },
                    },
                ],
            },
            ensure_ascii=True,
        ),
        encoding="utf-8",
    )
    return cache_dir, db_name, index_path


def _configure_cache_settings(
    monkeypatch,
    *,
    cache_dir: Path,
    db_name: str,
    index_path: Path,
) -> None:
    monkeypatch.setattr(settings, "ONS_GEO_CACHE_DIR", str(cache_dir), raising=False)
    monkeypatch.setattr(settings, "ONS_GEO_CACHE_DB", db_name, raising=False)
    monkeypatch.setattr(settings, "ONS_GEO_CACHE_INDEX_PATH", str(index_path), raising=False)
    fixture_schedule = [
        {"epoch": 123, "publication_date": "2025-12-01", "scheduled": False},
        {"epoch": 126, "publication_date": "2026-02-01", "scheduled": False},
        {"epoch": 127, "publication_date": "2026-12-01", "scheduled": True},
    ]
    monkeypatch.setattr(
        ons_geo_freshness,
        "load_addressbase_epoch_schedule",
        lambda path=ons_geo_freshness.DEFAULT_ADDRESSBASE_EPOCH_SCHEDULE_PATH: fixture_schedule,
        raising=False,
    )


def test_ons_geo_by_postcode_exact_mode(tmp_path: Path, monkeypatch) -> None:
    cache_dir, db_name, index_path = _seed_cache(tmp_path)
    _configure_cache_settings(
        monkeypatch,
        cache_dir=cache_dir,
        db_name=db_name,
        index_path=index_path,
    )
    monkeypatch.setattr(settings, "ONS_GEO_PRIMARY_DERIVATION", "exact", raising=False)

    resp = client.post(
        "/tools/call",
        json={"tool": "ons_geo.by_postcode", "postcode": "SW1A 1AA", "includeRaw": True},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["lookup"]["product"] == "ONSPD"
    assert body["query"]["postcode"] == "SW1A1AA"
    assert body["query"]["derivationMode"] == "exact"
    assert body["geographies"]["lad24"]["name"] == "Westminster"
    assert body["normalizedGeographies"]["lad"]["currentCode"] == "E09000033"
    assert body["normalizedGeographies"]["parish"]["currentCode"] == "E04000001"
    assert body["normalizedGeographies"]["parish"]["currentName"] == "Example Parish"
    assert body["normalizedGeographies"]["parish"]["currentNameWelsh"] == "Plwyf Enghreifftiol"
    assert body["semanticFields"]["postcode"] == "SW1A1AA"
    assert body["lookup"]["schemaFingerprint"] == "schema-onspd"
    assert "raw" in body


def test_ons_geo_by_postcode_best_fit_mode(tmp_path: Path, monkeypatch) -> None:
    cache_dir, db_name, index_path = _seed_cache(tmp_path)
    _configure_cache_settings(
        monkeypatch,
        cache_dir=cache_dir,
        db_name=db_name,
        index_path=index_path,
    )

    resp = client.post(
        "/tools/call",
        json={"tool": "ons_geo.by_postcode", "postcode": "SW1A 1AA", "derivationMode": "best_fit"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["lookup"]["product"] == "NSPL"
    assert body["query"]["derivationMode"] == "best_fit"
    assert body["geographies"]["lad24"]["name"] == "City of London"
    assert body["normalizedGeographies"]["lad"]["currentName"] == "City of London"


def test_ons_geo_by_uprn_exact_mode(tmp_path: Path, monkeypatch) -> None:
    cache_dir, db_name, index_path = _seed_cache(tmp_path)
    _configure_cache_settings(
        monkeypatch,
        cache_dir=cache_dir,
        db_name=db_name,
        index_path=index_path,
    )
    monkeypatch.setattr(
        ons_geo_tools,
        "summarize_uprn_dataset_freshness",
        lambda **_: {"status": "current", "lagEpochs": 0},
    )

    resp = client.post(
        "/tools/call",
        json={"tool": "ons_geo.by_uprn", "uprn": "100023336959", "derivationMode": "exact"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["lookup"]["product"] == "ONSUD"
    assert body["geographies"]["lad24"]["code"] == "E08000026"
    assert body["normalizedGeographies"]["lad"]["status"] == "current"
    assert body["normalizedGeographies"]["parish"]["currentCode"] == "E04000001"
    assert body["normalizedGeographies"]["msoa"]["currentName"] == "Example MSOA"
    assert body["normalizedGeographies"]["msoa"]["displayName"] == "Readable MSOA"
    assert body["normalizedGeographies"]["msoa"]["displayNameSource"]["version"] == "2.3"
    assert body["lookup"]["freshness"]["status"] == "current"


def test_ons_geo_area_summary_from_postcode_uses_compact_helpers(
    tmp_path: Path,
    monkeypatch,
) -> None:
    cache_dir, db_name, index_path = _seed_cache(tmp_path)
    _configure_cache_settings(
        monkeypatch,
        cache_dir=cache_dir,
        db_name=db_name,
        index_path=index_path,
    )

    seen_calls: list[tuple[str, dict[str, object]]] = []

    def fake_get_tool(name: str):  # type: ignore[no-untyped-def]
        if name == "admin_lookup.area_geometry":
            return _FakeTool(
                lambda payload: (
                    seen_calls.append((name, dict(payload))),
                    (
                        200,
                        {
                            "id": "E00000111",
                            "name": "Example OA",
                            "bbox": [-0.13, 51.49, -0.12, 51.5],
                            "live": False,
                            "meta": {"level": "OA"},
                        },
                    ),
                )[1]
            )
        if name == "os_map.inventory":
            return _FakeTool(
                lambda payload: (
                    seen_calls.append((name, dict(payload))),
                    (
                        200,
                        {
                            "responseMode": "summary",
                            "layers": {
                                "uprns": {"mode": "summary", "count": 3},
                                "buildings": {"mode": "summary", "count": 2},
                            },
                        },
                    ),
                )[1]
            )
        if name == "nomis.query":
            return _FakeTool(
                lambda payload: (
                    seen_calls.append((name, dict(payload))),
                    (
                        200,
                        {
                            "data": {"value": {"0": 292}},
                            "datasetSummary": {"id": "NM_2021_1", "name": "TS001 - Population"},
                        },
                    ),
                )[1]
            )
        if name == "admin_lookup.reverse_hierarchy":
            return _FakeTool(
                lambda payload: (
                    seen_calls.append((name, dict(payload))),
                    (200, {"chain": [{"id": "E00000111", "level": "OA", "name": "Example OA"}]}),
                )[1]
            )
        return None

    monkeypatch.setattr(ons_geo_tools, "get_tool", fake_get_tool)

    resp = client.post(
        "/tools/call",
        json={"tool": "ons_geo.area_summary", "postcode": "SW1A 1AA"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["area"]["id"] == "E00000111"
    assert body["area"]["level"] == "OA"
    assert body["area"]["name"] == "Example OA"
    assert body["anchor"]["type"] == "postcode"
    assert body["anchor"]["classifications"]["oac11ind"] == "4C1"
    assert body["counts"]["uprnCount"] == 3
    assert body["counts"]["postcodeCount"] == 2
    assert body["counts"]["postalDeliveryUprnCount"] == 2
    assert body["inventory"]["layers"]["uprns"]["count"] == 3
    assert body["population"]["value"] == 292
    assert body["profileDatasets"][0]["category"] == "population"
    inventory_calls = [payload for name, payload in seen_calls if name == "os_map.inventory"]
    assert inventory_calls and inventory_calls[0]["responseMode"] == "summary"


def test_ons_geo_area_summary_resolves_parish_from_uprn(
    tmp_path: Path,
    monkeypatch,
) -> None:
    cache_dir, db_name, index_path = _seed_cache(tmp_path)
    _configure_cache_settings(
        monkeypatch,
        cache_dir=cache_dir,
        db_name=db_name,
        index_path=index_path,
    )

    seen_payloads: list[dict[str, object]] = []

    def fake_get_tool(name: str):  # type: ignore[no-untyped-def]
        if name == "admin_lookup.area_geometry":
            return _FakeTool(
                lambda payload: (
                    seen_payloads.append(dict(payload)),
                    (
                        200,
                        {
                            "id": "E04000001",
                            "name": "Example Parish",
                            "bbox": [-1.6, 52.3, -1.5, 52.4],
                            "live": False,
                            "meta": {"level": "PARISH"},
                        },
                    ),
                )[1]
            )
        return None

    monkeypatch.setattr(ons_geo_tools, "get_tool", fake_get_tool)

    resp = client.post(
        "/tools/call",
        json={
            "tool": "ons_geo.area_summary",
            "uprn": "100023336959",
            "targetLevel": "PARISH",
            "includeInventory": False,
            "includePopulation": False,
            "includeProfileDatasets": False,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["area"]["id"] == "E04000001"
    assert body["area"]["level"] == "PARISH"
    assert body["area"]["name"] == "Example Parish"
    assert body["counts"]["uprnCount"] == 3
    assert body["counts"]["postcodeCount"] == 2
    assert body["counts"]["postalDeliveryUprnCount"] == 2
    assert seen_payloads and seen_payloads[0]["id"] == "E04000001"


def test_ons_geo_area_summary_preserves_msoa_display_name(
    tmp_path: Path,
    monkeypatch,
) -> None:
    cache_dir, db_name, index_path = _seed_cache(tmp_path)
    _configure_cache_settings(
        monkeypatch,
        cache_dir=cache_dir,
        db_name=db_name,
        index_path=index_path,
    )

    def fake_get_tool(name: str):  # type: ignore[no-untyped-def]
        if name == "admin_lookup.area_geometry":
            return _FakeTool(
                lambda payload: (
                    200,
                    {
                        "id": payload["id"],
                        "name": "Example MSOA",
                        "bbox": [-1.6, 52.3, -1.5, 52.4],
                        "live": False,
                        "meta": {"level": "MSOA"},
                    },
                )
            )
        return None

    monkeypatch.setattr(ons_geo_tools, "get_tool", fake_get_tool)

    resp = client.post(
        "/tools/call",
        json={
            "tool": "ons_geo.area_summary",
            "uprn": "100023336959",
            "targetLevel": "MSOA",
            "includeInventory": False,
            "includePopulation": False,
            "includeProfileDatasets": False,
        },
    )
    assert resp.status_code == 200
    area = resp.json()["area"]
    assert area["id"] == "E02000001"
    assert area["name"] == "Example MSOA"
    assert area["currentName"] == "Example MSOA"
    assert area["displayName"] == "Readable MSOA"
    assert area["displayNameWelsh"] == "MSOA Darllenadwy"
    assert area["displayNameSource"]["version"] == "2.3"
    assert "official ONS/RGC label" in area["namePolicy"]


def test_ons_geo_area_summary_requires_anchor_or_explicit_context(
    tmp_path: Path,
    monkeypatch,
) -> None:
    cache_dir, db_name, index_path = _seed_cache(tmp_path)
    _configure_cache_settings(
        monkeypatch,
        cache_dir=cache_dir,
        db_name=db_name,
        index_path=index_path,
    )

    resp = client.post(
        "/tools/call",
        json={"tool": "ons_geo.area_summary", "targetLevel": "OA"},
    )
    assert resp.status_code == 400
    assert "Provide id, postcode, or uprn" in resp.json()["message"]


def test_ons_geo_area_summary_invalid_id_without_target_level_returns_validation_error(
    tmp_path: Path,
    monkeypatch,
) -> None:
    cache_dir, db_name, index_path = _seed_cache(tmp_path)
    _configure_cache_settings(
        monkeypatch,
        cache_dir=cache_dir,
        db_name=db_name,
        index_path=index_path,
    )

    resp = client.post(
        "/tools/call",
        json={"tool": "ons_geo.area_summary", "id": "K04000001"},
    )
    assert resp.status_code == 400
    body = resp.json()
    assert body["code"] == "INVALID_INPUT"
    assert "Could not infer targetLevel from id K04000001" in body["message"]


def test_ons_geo_area_summary_infers_non_civil_parished_code(
    tmp_path: Path,
    monkeypatch,
) -> None:
    missing_dir = tmp_path / "missing"
    _configure_cache_settings(
        monkeypatch,
        cache_dir=missing_dir,
        db_name="ons_geo_cache.sqlite",
        index_path=tmp_path / "ons_geo_cache_index.json",
    )

    def fake_get_tool(name: str):  # type: ignore[no-untyped-def]
        if name == "admin_lookup.area_geometry":
            return _FakeTool(
                lambda payload: (
                    200,
                    {
                        "id": payload["id"],
                        "name": "Example Non-Civil-Parished Area",
                        "bbox": [-1.6, 52.3, -1.5, 52.4],
                        "live": False,
                        "meta": {"level": "PARISH"},
                    },
                )
            )
        return None

    monkeypatch.setattr(ons_geo_tools, "get_tool", fake_get_tool)

    resp = client.post(
        "/tools/call",
        json={
            "tool": "ons_geo.area_summary",
            "id": "E43000246",
            "includeInventory": False,
            "includePopulation": False,
            "includeProfileDatasets": False,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["input"]["targetLevel"] == "PARISH"
    assert body["area"]["id"] == "E43000246"
    assert body["area"]["level"] == "PARISH"
    assert body["area"]["name"] == "Example Non-Civil-Parished Area"


def test_ons_geo_area_summary_unknown_direct_id_returns_not_found(
    tmp_path: Path,
    monkeypatch,
) -> None:
    cache_dir, db_name, index_path = _seed_cache(tmp_path)
    _configure_cache_settings(
        monkeypatch,
        cache_dir=cache_dir,
        db_name=db_name,
        index_path=index_path,
    )
    monkeypatch.setattr(ons_geo_tools, "get_tool", lambda _name: None)

    resp = client.post(
        "/tools/call",
        json={"tool": "ons_geo.area_summary", "id": "E01009999", "targetLevel": "LSOA"},
    )
    assert resp.status_code == 404
    body = resp.json()
    assert body["code"] == "NOT_FOUND"
    assert "E01009999" in body["message"]


def test_ons_geo_area_summary_direct_id_can_resolve_higher_level_from_hierarchy(
    tmp_path: Path,
    monkeypatch,
) -> None:
    cache_dir, db_name, index_path = _seed_cache(tmp_path)
    _configure_cache_settings(
        monkeypatch,
        cache_dir=cache_dir,
        db_name=db_name,
        index_path=index_path,
    )

    def fake_get_tool(name: str):  # type: ignore[no-untyped-def]
        if name == "admin_lookup.reverse_hierarchy":
            return _FakeTool(
                lambda payload: (
                    200,
                    {
                        "chain": [
                            {"id": "E01000001", "level": "LSOA", "name": "Example LSOA"},
                            {"id": "E12000007", "level": "REGION", "name": "London"},
                        ]
                    },
                )
            )
        if name == "admin_lookup.area_geometry":
            return _FakeTool(
                lambda payload: (
                    200,
                    {
                        "id": "E12000007",
                        "name": "London",
                        "bbox": [-0.5, 51.2, 0.3, 51.8],
                        "meta": {"level": "REGION"},
                    },
                )
            )
        return None

    monkeypatch.setattr(ons_geo_tools, "get_tool", fake_get_tool)

    resp = client.post(
        "/tools/call",
        json={
            "tool": "ons_geo.area_summary",
            "id": "E01000001",
            "targetLevel": "REGION",
            "includeInventory": False,
            "includePopulation": False,
            "includeProfileDatasets": False,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["area"]["id"] == "E12000007"
    assert body["area"]["level"] == "REGION"
    assert body["area"]["name"] == "London"
    assert body["counts"]["uprnCount"] == 3


def test_ons_geo_area_summary_tolerates_optional_helper_failures(
    tmp_path: Path,
    monkeypatch,
) -> None:
    cache_dir, db_name, index_path = _seed_cache(tmp_path)
    _configure_cache_settings(
        monkeypatch,
        cache_dir=cache_dir,
        db_name=db_name,
        index_path=index_path,
    )

    def fake_get_tool(name: str):  # type: ignore[no-untyped-def]
        if name == "admin_lookup.area_geometry":
            return _FakeTool(
                lambda _payload: (_ for _ in ()).throw(RuntimeError("helper failed"))
            )
        return None

    monkeypatch.setattr(ons_geo_tools, "get_tool", fake_get_tool)

    resp = client.post(
        "/tools/call",
        json={
            "tool": "ons_geo.area_summary",
            "postcode": "SW1A 1AA",
            "includeInventory": False,
            "includePopulation": False,
            "includeProfileDatasets": False,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["area"]["id"] == "E00000111"
    assert body["area"]["name"] == "E00000111"


def test_ons_geo_area_summary_ignores_blank_anchor_fields(
    tmp_path: Path,
    monkeypatch,
) -> None:
    cache_dir, db_name, index_path = _seed_cache(tmp_path)
    _configure_cache_settings(
        monkeypatch,
        cache_dir=cache_dir,
        db_name=db_name,
        index_path=index_path,
    )
    monkeypatch.setattr(ons_geo_tools, "get_tool", lambda _name: None)

    resp = client.post(
        "/tools/call",
        json={
            "tool": "ons_geo.area_summary",
            "id": "",
            "postcode": "SW1A 1AA",
            "includeInventory": False,
            "includePopulation": False,
            "includeProfileDatasets": False,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["anchor"]["type"] == "postcode"
    assert body["area"]["id"] == "E00000111"


def test_ons_geo_by_postcode_cache_unavailable(tmp_path: Path, monkeypatch) -> None:
    missing_dir = tmp_path / "missing"
    _configure_cache_settings(
        monkeypatch,
        cache_dir=missing_dir,
        db_name="ons_geo_cache.sqlite",
        index_path=tmp_path / "ons_geo_cache_index.json",
    )

    resp = client.post("/tools/call", json={"tool": "ons_geo.by_postcode", "postcode": "SW1A 1AA"})
    assert resp.status_code == 503
    assert resp.json()["code"] == "CACHE_UNAVAILABLE"


def test_ons_geo_by_postcode_invalid_derivation_mode(tmp_path: Path, monkeypatch) -> None:
    cache_dir, db_name, index_path = _seed_cache(tmp_path)
    _configure_cache_settings(
        monkeypatch,
        cache_dir=cache_dir,
        db_name=db_name,
        index_path=index_path,
    )

    resp = client.post(
        "/tools/call",
        json={"tool": "ons_geo.by_postcode", "postcode": "SW1A 1AA", "derivationMode": "wrong"},
    )
    assert resp.status_code == 400
    assert resp.json()["code"] == "INVALID_INPUT"


def test_ons_geo_cache_status_uses_index(tmp_path: Path, monkeypatch) -> None:
    cache_dir, db_name, index_path = _seed_cache(tmp_path)
    _configure_cache_settings(
        monkeypatch,
        cache_dir=cache_dir,
        db_name=db_name,
        index_path=index_path,
    )
    monkeypatch.setattr(settings, "ONS_GEO_PRIMARY_DERIVATION", "exact", raising=False)

    resp = client.post("/tools/call", json={"tool": "ons_geo.cache_status"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["available"] is True
    assert body["status"] == "degraded"
    assert body["productCount"] == 4
    assert body["performance"]["degraded"] is True
    assert body["performance"]["reason"] == "outdated_addressbase_epochs"
    assert body["health"]["supportReady"] is True
    assert body["health"]["freshnessReady"] is False
    assert body["health"]["laggingProducts"] == ["NSUL"]
    assert len(body["supportProducts"]) == 2
    assert body["primaryDerivationMode"] == "exact"


def test_ons_geo_cache_status_unavailable_reports_degraded(tmp_path: Path, monkeypatch) -> None:
    missing_dir = tmp_path / "missing"
    _configure_cache_settings(
        monkeypatch,
        cache_dir=missing_dir,
        db_name="ons_geo_cache.sqlite",
        index_path=tmp_path / "ons_geo_cache_index.json",
    )

    resp = client.post("/tools/call", json={"tool": "ons_geo.cache_status"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["available"] is False
    assert body["status"] == "degraded"
    assert body["performance"]["degraded"] is True
    assert body["performance"]["reason"] == "cache_unavailable"
    assert body["reloadHint"]


def test_ons_geo_cache_status_unavailable_overrides_ready_index(
    tmp_path: Path, monkeypatch
) -> None:
    missing_dir = tmp_path / "missing"
    index_path = tmp_path / "ons_geo_cache_index.json"
    index_path.write_text(
        json.dumps(
            {
                "version": "2026-04-09",
                "health": {
                    "status": "ready",
                    "exactReady": True,
                    "bestFitReady": True,
                    "supportReady": True,
                    "freshnessReady": True,
                    "laggingProducts": [],
                },
                "products": [{"id": "ONSPD"}],
            }
        ),
        encoding="utf-8",
    )
    _configure_cache_settings(
        monkeypatch,
        cache_dir=missing_dir,
        db_name="ons_geo_cache.sqlite",
        index_path=index_path,
    )

    resp = client.post("/tools/call", json={"tool": "ons_geo.cache_status"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["available"] is False
    assert body["status"] == "degraded"
    assert body["performance"]["degraded"] is True
    assert body["performance"]["reason"] == "cache_unavailable"
    assert body["performance"]["exactReady"] is True


def test_ons_geo_release_audit_returns_combined_view(monkeypatch) -> None:
    monkeypatch.setattr(settings, "ONS_LIVE_ENABLED", True, raising=False)
    monkeypatch.setattr(
        ons_geo_tools,
        "build_release_audit",
        lambda timeout: {
            "version": "2026-04-08",
            "addressBaseSchedule": {
                "latestPublished": {"epoch": 126, "publication_date": "2026-04-02"},
                "nextScheduled": {"epoch": 127, "publication_date": "2026-05-14"},
                "source": "resources/addressbase_epoch_schedule.json",
            },
            "publisherNotices": {
                "sourceUrl": "https://geoportal.statistics.gov.uk/api/feed/rss/2.0",
                "status": "paused_by_publisher",
                "relevantNotices": ["We are pausing production of these."],
            },
            "datasets": [
                {
                    "id": "ONSUD",
                    "resolvedRelease": "December 2025",
                    "freshness": {"status": "lagging", "lagEpochs": 3},
                }
            ],
        },
    )

    resp = client.post("/tools/call", json={"tool": "ons_geo.release_audit", "timeout": 5})
    assert resp.status_code == 200
    body = resp.json()
    assert body["publisherNotices"]["status"] == "paused_by_publisher"
    assert body["datasets"][0]["id"] == "ONSUD"
    assert body["datasets"][0]["freshness"]["lagEpochs"] == 3


def test_ons_geo_release_audit_respects_live_disabled(monkeypatch) -> None:
    monkeypatch.setattr(settings, "ONS_LIVE_ENABLED", False, raising=False)
    resp = client.post("/tools/call", json={"tool": "ons_geo.release_audit"})
    assert resp.status_code == 503
    body = resp.json()
    assert body["code"] == "LIVE_DISABLED"


class _BrokenONSGeoCache:
    def available(self) -> bool:
        return True

    def lookup(self, *, key_type: str, key_value: str, derivation_mode: str):
        raise ONSGeoCacheReadError("missing ons_geo_rows table")


def _patch_broken_cache(monkeypatch) -> None:
    monkeypatch.setattr(
        ons_geo_tools.ONSGeoCache,
        "from_settings",
        classmethod(lambda cls: _BrokenONSGeoCache()),
    )


def test_ons_geo_by_postcode_cache_read_error_returns_503(monkeypatch) -> None:
    _patch_broken_cache(monkeypatch)
    resp = client.post("/tools/call", json={"tool": "ons_geo.by_postcode", "postcode": "SW1A 1AA"})
    assert resp.status_code == 503
    body = resp.json()
    assert body["code"] == "CACHE_READ_ERROR"
    assert "unreadable" in body["message"]


def test_ons_geo_by_uprn_cache_read_error_returns_503(monkeypatch) -> None:
    _patch_broken_cache(monkeypatch)
    resp = client.post("/tools/call", json={"tool": "ons_geo.by_uprn", "uprn": "100023336959"})
    assert resp.status_code == 503
    body = resp.json()
    assert body["code"] == "CACHE_READ_ERROR"
    assert "unreadable" in body["message"]


def test_ons_geo_by_postcode_rejects_invalid_include_raw_type(tmp_path: Path, monkeypatch) -> None:
    cache_dir, db_name, index_path = _seed_cache(tmp_path)
    _configure_cache_settings(
        monkeypatch,
        cache_dir=cache_dir,
        db_name=db_name,
        index_path=index_path,
    )

    resp = client.post(
        "/tools/call",
        json={"tool": "ons_geo.by_postcode", "postcode": "SW1A 1AA", "includeRaw": "yes"},
    )
    assert resp.status_code == 400
    assert resp.json()["message"] == "includeRaw must be a boolean"


def test_ons_geo_by_postcode_not_found_returns_404(tmp_path: Path, monkeypatch) -> None:
    cache_dir, db_name, index_path = _seed_cache(tmp_path)
    _configure_cache_settings(
        monkeypatch,
        cache_dir=cache_dir,
        db_name=db_name,
        index_path=index_path,
    )

    resp = client.post("/tools/call", json={"tool": "ons_geo.by_postcode", "postcode": "CV1 1ZZ"})
    assert resp.status_code == 404
    assert resp.json()["code"] == "NOT_FOUND"


def test_ons_geo_by_uprn_invalid_input_paths(tmp_path: Path, monkeypatch) -> None:
    cache_dir, db_name, index_path = _seed_cache(tmp_path)
    _configure_cache_settings(
        monkeypatch,
        cache_dir=cache_dir,
        db_name=db_name,
        index_path=index_path,
    )

    resp = client.post("/tools/call", json={"tool": "ons_geo.by_uprn", "uprn": ""})
    assert resp.status_code == 400
    assert resp.json()["message"] == "uprn must be a non-empty string"

    resp = client.post("/tools/call", json={"tool": "ons_geo.by_uprn", "uprn": "abc"})
    assert resp.status_code == 400
    assert resp.json()["message"] == "uprn must be a numeric string"


def test_ons_geo_release_audit_validates_timeout_and_upstream_error(monkeypatch) -> None:
    monkeypatch.setattr(settings, "ONS_LIVE_ENABLED", True, raising=False)

    resp = client.post("/tools/call", json={"tool": "ons_geo.release_audit", "timeout": 0})
    assert resp.status_code == 400
    assert resp.json()["message"] == "timeout must be a positive number"

    monkeypatch.setattr(
        ons_geo_tools,
        "build_release_audit",
        lambda timeout: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    resp = client.post("/tools/call", json={"tool": "ons_geo.release_audit", "timeout": 5})
    assert resp.status_code == 502
    assert resp.json()["code"] == "UPSTREAM_ERROR"


def test_ons_geo_internal_cache_performance_helpers() -> None:
    degraded = ons_geo_tools._cache_performance(available=True, product_count=0)
    assert degraded["reason"] == "index_empty"
    assert ons_geo_tools._cache_performance(available=True, product_count=2)["degraded"] is False

    ready = ons_geo_tools._cache_performance_from_index(
        available=True,
        index={"health": {"status": "ready", "exactReady": True, "bestFitReady": True}},
    )
    assert ready["degraded"] is False
    assert ready["impact"] == "Cached ONS geography lookup is available."

    degraded = ons_geo_tools._cache_performance_from_index(
        available=True,
        index={"health": {"status": "degraded", "degradedReasons": "bad"}},
    )
    assert degraded["degraded"] is True
    assert degraded["reason"] == "cache_degraded"


def test_ons_geo_invalid_postcode_and_uprn_paths(tmp_path: Path, monkeypatch) -> None:
    cache_dir, db_name, index_path = _seed_cache(tmp_path)
    _configure_cache_settings(
        monkeypatch,
        cache_dir=cache_dir,
        db_name=db_name,
        index_path=index_path,
    )

    resp = client.post("/tools/call", json={"tool": "ons_geo.by_postcode", "postcode": "bad"})
    assert resp.status_code == 400
    assert resp.json()["message"] == "Invalid UK postcode"

    resp = client.post(
        "/tools/call",
        json={"tool": "ons_geo.by_postcode", "postcode": "SW1A 1AA", "derivationMode": 1},
    )
    assert resp.status_code == 400
    assert resp.json()["message"] == "derivationMode must be a string"

    resp = client.post(
        "/tools/call",
        json={"tool": "ons_geo.by_uprn", "uprn": "100023336959", "includeRaw": "yes"},
    )
    assert resp.status_code == 400
    assert resp.json()["message"] == "includeRaw must be a boolean"
