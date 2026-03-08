from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path


def _write_file(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def test_ons_geo_cache_refresh_ingests_all_products(tmp_path: Path) -> None:
    sources = _write_file(
        tmp_path / "ons_geo_sources.json",
        json.dumps(
            {
                "version": "2026-02-22",
                "products": [
                    {
                        "id": "ONSPD",
                        "title": "ONSPD",
                        "keyType": "postcode",
                        "derivationMode": "exact",
                        "priority": 10,
                        "release": "2026-02",
                        "fieldCandidates": {"key": ["pcds"]},
                        "source": {"downloadUrl": ""},
                    },
                    {
                        "id": "NSPL",
                        "title": "NSPL",
                        "keyType": "postcode",
                        "derivationMode": "best_fit",
                        "priority": 20,
                        "release": "2026-02",
                        "fieldCandidates": {"key": ["pcds"]},
                        "source": {"downloadUrl": ""},
                    },
                    {
                        "id": "ONSUD",
                        "title": "ONSUD",
                        "keyType": "uprn",
                        "derivationMode": "exact",
                        "priority": 10,
                        "release": "2026-02",
                        "fieldCandidates": {"key": ["UPRN"]},
                        "source": {"downloadUrl": ""},
                    },
                    {
                        "id": "NSUL",
                        "title": "NSUL",
                        "keyType": "uprn",
                        "derivationMode": "best_fit",
                        "priority": 20,
                        "release": "2026-02",
                        "fieldCandidates": {"key": ["UPRN"]},
                        "source": {"downloadUrl": ""},
                    },
                ],
            },
            ensure_ascii=True,
        ),
    )
    onspd = _write_file(
        tmp_path / "onspd.csv",
        "pcds,LAD24CD,LAD24NM\nSW1A1AA,E09000033,Westminster\n",
    )
    nspl = _write_file(
        tmp_path / "nspl.csv",
        "pcds,LAD24CD,LAD24NM\nSW1A1AA,E09000001,City of London\n",
    )
    onsud = _write_file(
        tmp_path / "onsud.csv",
        "UPRN,LAD24CD,LAD24NM\n100023336959,E08000026,Coventry\n",
    )
    nsul = _write_file(
        tmp_path / "nsul.csv",
        "UPRN,LAD24CD,LAD24NM\n100023336959,E08000026,Coventry\n",
    )
    cache_dir = tmp_path / "cache"
    index_path = tmp_path / "ons_geo_cache_index.json"
    db_name = "ons_geo_cache.sqlite"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/ons_geo_cache_refresh.py",
            "--sources",
            str(sources),
            "--cache-dir",
            str(cache_dir),
            "--index-path",
            str(index_path),
            "--db-name",
            db_name,
            "--product-file",
            f"ONSPD={onspd}",
            "--product-file",
            f"NSPL={nspl}",
            "--product-file",
            f"ONSUD={onsud}",
            "--product-file",
            f"NSUL={nsul}",
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=Path(__file__).resolve().parent.parent,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    statuses = {entry["id"]: entry["status"] for entry in payload["products"]}
    assert statuses == {
        "ONSPD": "ingested",
        "NSPL": "ingested",
        "ONSUD": "ingested",
        "NSUL": "ingested",
    }

    index_payload = json.loads(index_path.read_text(encoding="utf-8"))
    assert index_payload["version"] == "2026-02-22"
    assert len(index_payload["products"]) == 4

    conn = sqlite3.connect(str(cache_dir / db_name))
    row_count = conn.execute("SELECT COUNT(*) FROM ons_geo_rows").fetchone()[0]
    assert row_count == 4
    uprn_index_count = conn.execute("SELECT COUNT(*) FROM ons_geo_uprn_index").fetchone()[0]
    assert uprn_index_count == 2
    indexed = conn.execute(
        """
        SELECT uprn, lad_code, lad_name
        FROM ons_geo_uprn_index
        WHERE derivation_mode = 'exact'
        ORDER BY uprn
        """
    ).fetchall()
    assert indexed
    assert indexed[0][0] == "100023336959"
    assert indexed[0][1] == "E08000026"
    assert indexed[0][2] == "Coventry"
    derivation_modes = {
        row[0]
        for row in conn.execute(
            "SELECT DISTINCT derivation_mode FROM ons_geo_rows"
        ).fetchall()
    }
    assert derivation_modes == {"exact", "best_fit"}
    conn.close()
