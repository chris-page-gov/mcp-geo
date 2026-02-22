from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient

from server.config import settings
from server.main import app
from server.ons_geo_cache import ensure_schema

client = TestClient(app)


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
            key_type,
            derivation_mode,
            release,
            source_name,
            source_path,
            source_sha256,
            record_count,
            ingested_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            product_id,
            key_type,
            derivation_mode,
            "2026-02",
            source_name,
            f"{product_id.lower()}.csv",
            f"hash-{product_id.lower()}",
            1,
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
            cached_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        payload={"LAD24CD": "E09000033", "LAD24NM": "Westminster"},
    )
    _insert_row(
        conn,
        product_id="NSPL",
        key_type="postcode",
        key_norm="SW1A1AA",
        derivation_mode="best_fit",
        source_name="NSPL",
        payload={"LAD24CD": "E09000001", "LAD24NM": "City of London"},
    )
    _insert_row(
        conn,
        product_id="ONSUD",
        key_type="uprn",
        key_norm="100023336959",
        derivation_mode="exact",
        source_name="ONSUD",
        payload={"LAD24CD": "E08000026", "LAD24NM": "Coventry"},
    )
    _insert_row(
        conn,
        product_id="NSUL",
        key_type="uprn",
        key_norm="100023336959",
        derivation_mode="best_fit",
        source_name="NSUL",
        payload={"LAD24CD": "E08000026", "LAD24NM": "Coventry"},
    )
    conn.commit()
    conn.close()

    index_path = tmp_path / "ons_geo_cache_index.json"
    index_path.write_text(
        json.dumps(
            {
                "version": "2026-02-22",
                "generatedAt": "2026-02-22T00:00:00Z",
                "products": [
                    {"id": "ONSPD", "derivationMode": "exact"},
                    {"id": "ONSUD", "derivationMode": "exact"},
                    {"id": "NSPL", "derivationMode": "best_fit"},
                    {"id": "NSUL", "derivationMode": "best_fit"},
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


def test_ons_geo_by_uprn_exact_mode(tmp_path: Path, monkeypatch) -> None:
    cache_dir, db_name, index_path = _seed_cache(tmp_path)
    _configure_cache_settings(
        monkeypatch,
        cache_dir=cache_dir,
        db_name=db_name,
        index_path=index_path,
    )

    resp = client.post(
        "/tools/call",
        json={"tool": "ons_geo.by_uprn", "uprn": "100023336959", "derivationMode": "exact"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["lookup"]["product"] == "ONSUD"
    assert body["geographies"]["lad24"]["code"] == "E08000026"


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
    assert body["productCount"] == 4
    assert body["primaryDerivationMode"] == "exact"
