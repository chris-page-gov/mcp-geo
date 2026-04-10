from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from server.main import app
from tools import council_tax


def _write_xref_csv(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "UPRN,XREF_KEY,CROSS_REFERENCE,VERSION,SOURCE,START_DATE,END_DATE,LAST_UPDATE_DATE,ENTRY_DATE",
                "100000000001,X1,CT-1,1,7666VC,2024-01-01,,2024-02-01,2024-01-01",
                "100000000002,X2,NDR-1,1,7666VN,2024-01-01,,2024-02-01,2024-01-01",
                "100000000003,X3,OLD-CT,1,7666VC,2020-01-01,2023-12-31,2023-12-31,2020-01-01",
                "100000000004,X4,MIX-CT,1,7666VC,2024-01-01,,2024-02-01,2024-01-01",
                "100000000004,X5,MIX-NDR,1,7666VN,2024-01-01,,2024-02-01,2024-01-01",
                "100000000005,X6,WARD-1,1,7666OW,2024-01-01,,2024-02-01,2024-01-01",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _write_extracted_xref_csv(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "uprn,xRefKey,crossReference,source,version,startDate,endDate,lastUpdateDate,entryDate",
                "100000000001,X1,CT-1,7666VC,1,2024-01-01,,2024-02-01,2024-01-01",
                "100000000002,X2,NDR-1,7666VN,1,2024-01-01,,2024-02-01,2024-01-01",
                "100000000003,X3,OLD-CT,7666VC,1,2020-01-01,2023-12-31,2023-12-31,2020-01-01",
                "100000000004,X4,WARD-1,7666OW,1,2024-01-01,,2024-02-01,2024-01-01",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _write_xref_parquet(path: Path, *, rows: int = 6) -> None:
    duckdb = pytest.importorskip("duckdb")
    quoted_path = str(path).replace("'", "''")
    connection = duckdb.connect(database=":memory:")
    try:
        connection.execute(
            """
            CREATE TABLE input_rows (
                uprn VARCHAR,
                xRefKey VARCHAR,
                crossReference VARCHAR,
                source VARCHAR,
                version VARCHAR,
                startDate VARCHAR,
                endDate VARCHAR,
                lastUpdateDate VARCHAR,
                entryDate VARCHAR
            )
            """
        )
        if rows <= 6:
            connection.executemany(
                "INSERT INTO input_rows VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    (
                        "100000000001",
                        "X1",
                        "CT-1",
                        "7666VC",
                        "1",
                        "2024-01-01",
                        "",
                        "2024-02-01",
                        "2024-01-01",
                    ),
                    (
                        "100000000002",
                        "X2",
                        "NDR-1",
                        "7666VN",
                        "1",
                        "2024-01-01",
                        "",
                        "2024-02-01",
                        "2024-01-01",
                    ),
                    (
                        "100000000003",
                        "X3",
                        "OLD-CT",
                        "7666VC",
                        "1",
                        "2020-01-01",
                        "2023-12-31",
                        "2023-12-31",
                        "2020-01-01",
                    ),
                    (
                        "100000000004",
                        "X4",
                        "BOTH-CT",
                        "7666VC",
                        "1",
                        "2024-01-01",
                        "",
                        "2024-02-01",
                        "2024-01-01",
                    ),
                    (
                        "100000000004",
                        "X5",
                        "BOTH-NDR",
                        "7666VN",
                        "1",
                        "2024-01-01",
                        "",
                        "2024-02-01",
                        "2024-01-01",
                    ),
                    (
                        "100000000005",
                        "X6",
                        "WARD-1",
                        "7666OW",
                        "1",
                        "2024-01-01",
                        "",
                        "2024-02-01",
                        "2024-01-01",
                    ),
                ],
            )
        else:
            connection.execute(
                f"""
                INSERT INTO input_rows
                SELECT
                    LPAD(CAST(100000000000 + i AS VARCHAR), 12, '0') AS uprn,
                    'X' || CAST(i AS VARCHAR) AS xRefKey,
                    'CT-' || CAST(i AS VARCHAR) AS crossReference,
                    '7666VC' AS source,
                    '1' AS version,
                    '2024-01-01' AS startDate,
                    '' AS endDate,
                    '2024-02-01' AS lastUpdateDate,
                    '2024-01-01' AS entryDate
                FROM range({rows}) AS t(i)
                """
            )
        connection.execute(
            f"COPY input_rows TO '{quoted_path}' (FORMAT PARQUET)"
        )
    finally:
        connection.close()


def _write_padded_uprn_xref_parquet(path: Path) -> None:
    duckdb = pytest.importorskip("duckdb")
    quoted_path = str(path).replace("'", "''")
    connection = duckdb.connect(database=":memory:")
    try:
        connection.execute(
            """
            CREATE TABLE input_rows (
                uprn VARCHAR,
                xRefKey VARCHAR,
                crossReference VARCHAR,
                source VARCHAR,
                version VARCHAR,
                startDate VARCHAR,
                endDate VARCHAR,
                lastUpdateDate VARCHAR,
                entryDate VARCHAR
            )
            """
        )
        connection.executemany(
            "INSERT INTO input_rows VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    " 100000000001 ",
                    "X1",
                    "CT-1",
                    "7666VC",
                    "1",
                    "2024-01-01",
                    "",
                    "2024-02-01",
                    "2024-01-01",
                ),
                (
                    "1000 00000002",
                    "X2",
                    "NDR-1",
                    "7666VN",
                    "1",
                    "2024-01-01",
                    "",
                    "2024-02-01",
                    "2024-01-01",
                ),
            ],
        )
        connection.execute(f"COPY input_rows TO '{quoted_path}' (FORMAT PARQUET)")
    finally:
        connection.close()


def _write_bad_xref_parquet(path: Path) -> None:
    duckdb = pytest.importorskip("duckdb")
    quoted_path = str(path).replace("'", "''")
    connection = duckdb.connect(database=":memory:")
    try:
        connection.execute(
            """
            CREATE TABLE bad_input_rows (
                uprn VARCHAR,
                xRefKey VARCHAR
            )
            """
        )
        connection.execute(
            """
            INSERT INTO bad_input_rows VALUES
                ('100000000001', 'X1')
            """
        )
        connection.execute(f"COPY bad_input_rows TO '{quoted_path}' (FORMAT PARQUET)")
    finally:
        connection.close()


def test_council_tax_uprn_query_requires_uprns(client: TestClient) -> None:
    response = client.post("/tools/call", json={"tool": "council_tax.query"})
    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_INPUT"


def test_council_tax_uprn_query_rejects_invalid_uprn(client: TestClient) -> None:
    response = client.post(
        "/tools/call",
        json={"tool": "council_tax.query", "uprns": ["not-a-uprn"]},
    )
    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_INPUT"


def test_council_tax_uprn_query_requires_configured_source(monkeypatch) -> None:
    monkeypatch.setattr(council_tax.settings, "ADDRESSBASE_PREMIUM_XREF_PATH", "", raising=False)
    client = TestClient(app)
    response = client.post(
        "/tools/call",
        json={"tool": "council_tax.query", "uprns": ["100000000001"]},
    )
    assert response.status_code == 501
    assert response.json()["code"] == "NO_ADDRESSBASE_PREMIUM_DATA"


def test_council_tax_uprn_query_classifies_active_sources(tmp_path: Path, monkeypatch) -> None:
    csv_path = tmp_path / "ID23_ApplicationCrossReference.csv"
    _write_xref_csv(csv_path)
    monkeypatch.setattr(
        council_tax.settings,
        "ADDRESSBASE_PREMIUM_XREF_PATH",
        str(csv_path),
        raising=False,
    )

    client = TestClient(app)
    response = client.post(
        "/tools/call",
        json={
            "tool": "council_tax.query",
            "uprns": [
                "100000000001",
                "100000000002",
                "100000000003",
                "100000000004",
                "100000000005",
            ],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["summary"] == {
        "queriedCount": 5,
        "councilTaxCount": 2,
        "businessRatesCount": 2,
        "bothCount": 1,
        "noneCount": 2,
        "activeOnly": True,
    }
    results = {item["uprn"]: item for item in body["results"]}

    assert results["100000000001"]["status"] == "council_tax"
    assert results["100000000001"]["paysCouncilTax"] is True
    assert results["100000000001"]["sourceCodes"] == ["7666VC"]

    assert results["100000000002"]["status"] == "non_domestic_rates"
    assert results["100000000002"]["paysBusinessRates"] is True
    assert results["100000000002"]["sourceCodes"] == ["7666VN"]

    assert results["100000000003"]["status"] == "none"
    assert results["100000000003"]["sourceCodes"] == []
    assert results["100000000003"]["inactiveSourceCodes"] == ["7666VC"]
    assert results["100000000003"]["inactiveRelevantRecordCount"] == 1

    assert results["100000000004"]["status"] == "both"
    assert results["100000000004"]["sourceCodes"] == ["7666VC", "7666VN"]

    assert results["100000000005"]["status"] == "none"
    assert results["100000000005"]["matchedRecordCount"] == 0

    provenance = body["provenance"]
    assert provenance["source"] == "addressbase_premium_application_cross_reference"
    assert provenance["documentation"]["product"] == council_tax.ADDRESSBASE_PREMIUM_DOC_URL
    assert (
        provenance["documentation"]["applicationCrossReference"]
        == council_tax.ADDRESSBASE_PREMIUM_XREF_DOC_URL
    )


def test_council_tax_uprn_query_supports_directory_config(tmp_path: Path, monkeypatch) -> None:
    data_dir = tmp_path / "epoch"
    data_dir.mkdir()
    csv_path = data_dir / "my_ID23_xref_extract.csv"
    _write_xref_csv(csv_path)
    monkeypatch.setattr(
        council_tax.settings,
        "ADDRESSBASE_PREMIUM_XREF_PATH",
        str(data_dir),
        raising=False,
    )

    client = TestClient(app)
    response = client.post(
        "/tools/call",
        json={"tool": "council_tax.query", "uprns": ["100000000001"]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["results"][0]["status"] == "council_tax"
    assert body["provenance"]["configuredPath"].endswith("my_ID23_xref_extract.csv")


def test_council_tax_uprn_query_supports_directory_config_with_uppercase_csv(
    tmp_path: Path,
    monkeypatch,
) -> None:
    data_dir = tmp_path / "epoch"
    data_dir.mkdir()
    csv_path = data_dir / "ID23_ApplicationCrossReference.CSV"
    _write_xref_csv(csv_path)
    monkeypatch.setattr(
        council_tax.settings,
        "ADDRESSBASE_PREMIUM_XREF_PATH",
        str(data_dir),
        raising=False,
    )

    client = TestClient(app)
    response = client.post(
        "/tools/call",
        json={"tool": "council_tax.query", "uprns": ["100000000001"]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["results"][0]["status"] == "council_tax"
    assert body["provenance"]["configuredPath"].endswith("ID23_ApplicationCrossReference.CSV")


def test_council_tax_uprn_query_supports_extracted_csv_headers(
    tmp_path: Path,
    monkeypatch,
) -> None:
    csv_path = tmp_path / "xref_full.csv"
    _write_extracted_xref_csv(csv_path)
    monkeypatch.setattr(
        council_tax.settings,
        "ADDRESSBASE_PREMIUM_XREF_PATH",
        str(csv_path),
        raising=False,
    )

    client = TestClient(app)
    response = client.post(
        "/tools/call",
        json={
            "tool": "council_tax.query",
            "uprns": ["100000000001", "100000000002", "100000000003", "100000000004"],
        },
    )
    assert response.status_code == 200
    body = response.json()
    results = {item["uprn"]: item for item in body["results"]}
    assert results["100000000001"]["status"] == "council_tax"
    assert results["100000000002"]["status"] == "non_domestic_rates"
    assert results["100000000003"]["inactiveSourceCodes"] == ["7666VC"]
    assert results["100000000004"]["matchedRecordCount"] == 0


def test_council_tax_uprn_query_prefers_xref_voa_os_parquet_in_directory(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _write_xref_csv(tmp_path / "xref_test.csv")
    parquet_path = tmp_path / "xref_voa_os.parquet"
    _write_xref_parquet(parquet_path)
    monkeypatch.setattr(
        council_tax.settings,
        "ADDRESSBASE_PREMIUM_XREF_PATH",
        str(tmp_path),
        raising=False,
    )

    client = TestClient(app)
    response = client.post(
        "/tools/call",
        json={"tool": "council_tax.query", "uprns": ["100000000001"]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["results"][0]["status"] == "council_tax"
    assert body["provenance"]["configuredPath"].endswith("xref_voa_os.parquet")
    assert body["provenance"]["method"] == "duckdb_parquet_query"


def test_council_tax_uprn_query_falls_back_to_csv_when_duckdb_missing(
    tmp_path: Path,
    monkeypatch,
) -> None:
    csv_path = tmp_path / "my_ID23_xref_extract.csv"
    _write_xref_csv(csv_path)
    _write_xref_parquet(tmp_path / "xref_voa_os.parquet")
    monkeypatch.setattr(council_tax, "duckdb", None, raising=False)
    monkeypatch.setattr(
        council_tax.settings,
        "ADDRESSBASE_PREMIUM_XREF_PATH",
        str(tmp_path),
        raising=False,
    )

    client = TestClient(app)
    response = client.post(
        "/tools/call",
        json={"tool": "council_tax.query", "uprns": ["100000000001"]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["results"][0]["status"] == "council_tax"
    assert body["provenance"]["configuredPath"].endswith("my_ID23_xref_extract.csv")
    assert body["provenance"]["method"] == "streaming_csv_scan"


def test_council_tax_uprn_query_supports_large_parquet_batches(
    tmp_path: Path,
    monkeypatch,
) -> None:
    parquet_path = tmp_path / "xref_voa_os.parquet"
    _write_xref_parquet(parquet_path, rows=1200)
    monkeypatch.setattr(
        council_tax.settings,
        "ADDRESSBASE_PREMIUM_XREF_PATH",
        str(parquet_path),
        raising=False,
    )

    uprns = [f"{100000000000 + index:012d}" for index in range(1200)]
    client = TestClient(app)
    response = client.post(
        "/tools/call",
        json={"tool": "council_tax.query", "uprns": uprns},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["summary"] == {
        "queriedCount": 1200,
        "councilTaxCount": 1200,
        "businessRatesCount": 0,
        "bothCount": 0,
        "noneCount": 0,
        "activeOnly": True,
    }
    assert body["provenance"]["method"] == "duckdb_parquet_query"
    assert body["results"][0]["sourceCodes"] == ["7666VC"]
    assert body["results"][-1]["status"] == "council_tax"


def test_council_tax_uprn_query_normalizes_parquet_uprn_keys_before_join(
    tmp_path: Path,
    monkeypatch,
) -> None:
    parquet_path = tmp_path / "xref_voa_os.parquet"
    _write_padded_uprn_xref_parquet(parquet_path)
    monkeypatch.setattr(
        council_tax.settings,
        "ADDRESSBASE_PREMIUM_XREF_PATH",
        str(parquet_path),
        raising=False,
    )

    client = TestClient(app)
    response = client.post(
        "/tools/call",
        json={"tool": "council_tax.query", "uprns": ["100000000001", "100000000002"]},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["councilTaxCount"] == 1
    assert body["summary"]["businessRatesCount"] == 1
    results = {item["uprn"]: item for item in body["results"]}
    assert results["100000000001"]["status"] == "council_tax"
    assert results["100000000002"]["status"] == "non_domestic_rates"


def test_council_tax_uprn_query_preserves_inactive_parquet_matches_when_active_only(
    tmp_path: Path,
    monkeypatch,
) -> None:
    parquet_path = tmp_path / "xref_voa_os.parquet"
    _write_xref_parquet(parquet_path)
    monkeypatch.setattr(
        council_tax.settings,
        "ADDRESSBASE_PREMIUM_XREF_PATH",
        str(parquet_path),
        raising=False,
    )

    client = TestClient(app)
    response = client.post(
        "/tools/call",
        json={"tool": "council_tax.query", "uprns": ["100000000003"]},
    )

    assert response.status_code == 200
    result = response.json()["results"][0]
    assert result["status"] == "none"
    assert result["sourceCodes"] == []
    assert result["inactiveSourceCodes"] == ["7666VC"]
    assert result["inactiveRelevantRecordCount"] == 1


def test_council_tax_uprn_query_can_include_ended_records(tmp_path: Path, monkeypatch) -> None:
    csv_path = tmp_path / "ID23_ApplicationCrossReference.csv"
    _write_xref_csv(csv_path)
    monkeypatch.setattr(
        council_tax.settings,
        "ADDRESSBASE_PREMIUM_XREF_PATH",
        str(csv_path),
        raising=False,
    )

    client = TestClient(app)
    response = client.post(
        "/tools/call",
        json={
            "tool": "council_tax.query",
            "uprns": ["100000000003"],
            "activeOnly": False,
        },
    )
    assert response.status_code == 200
    result = response.json()["results"][0]
    assert result["status"] == "council_tax"
    assert result["paysCouncilTax"] is True
    assert result["matches"][0]["active"] is False
    assert result["matches"][0]["endDate"] == "2023-12-31"


def test_council_tax_uprn_query_rejects_invalid_csv_shape(tmp_path: Path, monkeypatch) -> None:
    csv_path = tmp_path / "bad.csv"
    csv_path.write_text("UPRN,XREF_KEY\n100000000001,X1\n", encoding="utf-8")
    monkeypatch.setattr(
        council_tax.settings,
        "ADDRESSBASE_PREMIUM_XREF_PATH",
        str(csv_path),
        raising=False,
    )

    client = TestClient(app)
    response = client.post(
        "/tools/call",
        json={"tool": "council_tax.query", "uprns": ["100000000001"]},
    )
    assert response.status_code == 502
    assert response.json()["code"] == "INVALID_DATA_SOURCE"


def test_scan_addressbase_xref_parquet_requires_duckdb(monkeypatch, tmp_path: Path) -> None:
    parquet_path = tmp_path / "xref_voa_os.parquet"
    _write_xref_parquet(parquet_path)
    monkeypatch.setattr(council_tax, "duckdb", None)

    status, body = council_tax._scan_addressbase_xref_parquet(  # noqa: SLF001
        path=parquet_path,
        uprns=["100000000001"],
        active_only=True,
    )

    assert status == 501
    assert body["code"] == "MISSING_DEPENDENCY"


def test_scan_addressbase_xref_parquet_rejects_missing_columns(tmp_path: Path) -> None:
    parquet_path = tmp_path / "xref_voa_os.parquet"
    _write_bad_xref_parquet(parquet_path)

    status, body = council_tax._scan_addressbase_xref_parquet(  # noqa: SLF001
        path=parquet_path,
        uprns=["100000000001"],
        active_only=True,
    )

    assert status == 502
    assert body["code"] == "INVALID_DATA_SOURCE"
    assert "missing required columns" in body["message"]


def test_scan_addressbase_xref_parquet_normalizes_query_failures(
    monkeypatch,
    tmp_path: Path,
) -> None:
    parquet_path = tmp_path / "xref_voa_os.parquet"
    _write_xref_parquet(parquet_path)

    def _boom(_: object) -> None:
        raise RuntimeError("duckdb exploded")

    monkeypatch.setattr(council_tax, "_configure_addressbase_duckdb_connection", _boom)

    status, body = council_tax._scan_addressbase_xref_parquet(  # noqa: SLF001
        path=parquet_path,
        uprns=["100000000001"],
        active_only=True,
    )

    assert status == 502
    assert body["code"] == "INVALID_DATA_SOURCE"
    assert "duckdb exploded" in body["message"]


def test_scan_addressbase_xref_rejects_unsupported_file_type(tmp_path: Path) -> None:
    bad_path = tmp_path / "xref_voa_os.txt"
    bad_path.write_text("not used\n", encoding="utf-8")

    status, body = council_tax._scan_addressbase_xref(  # noqa: SLF001
        path=bad_path,
        uprns=["100000000001"],
        active_only=True,
    )

    assert status == 502
    assert body["code"] == "INVALID_DATA_SOURCE"
    assert "Unsupported AddressBase Premium xref file type" in body["message"]


def test_duckdb_addressbase_expression_returns_null_for_missing_column() -> None:
    expression = council_tax._duckdb_addressbase_expression(  # noqa: SLF001
        {"UPRN": "uprn"},
        "SOURCE",
        relation_alias="xref",
        normalize_source=True,
    )

    assert expression == "CAST(NULL AS VARCHAR)"


def test_uprn_query_allows_parquet_batches_above_legacy_csv_limit(monkeypatch) -> None:
    monkeypatch.setattr(
        council_tax,
        "_validate_uprn_query",
        lambda payload: (  # noqa: ARG005
            200,
            {
                "uprns": ["100000000001"],
                "activeOnly": True,
                "rawCount": council_tax.ADDRESSBASE_XREF_CSV_MAX_UPRNS + 1,
            },
        ),
    )
    monkeypatch.setattr(
        council_tax,
        "_resolve_addressbase_xref_path",
        lambda: Path("/tmp/xref_voa_os.parquet"),
    )
    monkeypatch.setattr(
        council_tax,
        "_scan_addressbase_xref",
        lambda **kwargs: (  # noqa: ARG005
            200,
            [
                {
                    "uprn": "100000000001",
                    "paysCouncilTax": True,
                    "paysBusinessRates": False,
                    "status": "council_tax",
                    "sourceCodes": ["7666VC"],
                    "inactiveSourceCodes": [],
                    "matchedRecordCount": 1,
                    "inactiveRelevantRecordCount": 0,
                    "matches": [],
                }
            ],
        ),
    )

    status, body = council_tax._uprn_query({})  # noqa: SLF001

    assert status == 200
    assert body["summary"]["queriedCount"] == 1
    assert body["provenance"]["method"] == "duckdb_parquet_query"


def test_uprn_query_enforces_parquet_batch_limit(monkeypatch) -> None:
    monkeypatch.setattr(
        council_tax,
        "_validate_uprn_query",
        lambda payload: (  # noqa: ARG005
            200,
            {
                "uprns": ["100000000001"],
                "activeOnly": True,
                "rawCount": council_tax.ADDRESSBASE_XREF_PARQUET_MAX_UPRNS + 1,
            },
        ),
    )
    monkeypatch.setattr(
        council_tax,
        "_resolve_addressbase_xref_path",
        lambda: Path("/tmp/xref_voa_os.parquet"),
    )

    status, body = council_tax._uprn_query({})  # noqa: SLF001

    assert status == 400
    assert body["code"] == "INVALID_INPUT"
    assert str(council_tax.ADDRESSBASE_XREF_PARQUET_MAX_UPRNS) in body["message"]
