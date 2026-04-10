from __future__ import annotations

from pathlib import Path

import pytest

from scripts import addressbase_build_xref


def _write_input_csv(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "uprn,xRefKey,crossReference,source,version,startDate,endDate,lastUpdateDate,entryDate",
                "100000000002,X2,NDR-1,7666VN,1,2024-01-01,,2024-02-01,2024-01-01",
                "100000000001,X1,CT-1,7666VC,1,2024-01-01,,2024-02-01,2024-01-01",
                "100000000003,X3,WARD-1,7666OW,1,2024-01-01,,2024-02-01,2024-01-01",
                "100000000004,X4,PARISH-1,7666OP,1,2024-01-01,,2024-02-01,2024-01-01",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _write_input_parquet(path: Path) -> None:
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
                    "100000000003",
                    "X3",
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
        connection.execute(
            f"COPY input_rows TO '{quoted_path}' (FORMAT PARQUET)"
        )
    finally:
        connection.close()


def test_build_serving_parquet_filters_and_sorts_rows(tmp_path: Path) -> None:
    duckdb = pytest.importorskip("duckdb")
    input_path = tmp_path / "xref.parquet"
    output_path = tmp_path / "xref_voa_os.parquet"
    _write_input_parquet(input_path)

    result = addressbase_build_xref.build_serving_parquet(
        input_path=input_path,
        output_path=output_path,
        drop_source_codes=["7666OW", "7666OP"],
        row_group_size=10_000,
        compression="zstd",
        sort_by_uprn=True,
        threads=1,
        memory_limit="512MB",
    )

    assert result["retainedRowCount"] == 2
    connection = duckdb.connect(database=":memory:")
    quoted_output = str(output_path).replace("'", "''")
    try:
        rows = connection.execute(f"SELECT * FROM read_parquet('{quoted_output}')").fetchall()
        columns = [
            row[0]
            for row in connection.execute(
                f"DESCRIBE SELECT * FROM read_parquet('{quoted_output}')"
            ).fetchall()
        ]
    finally:
        connection.close()

    assert columns == [
        "uprn",
        "xref_key",
        "cross_reference",
        "source",
        "version",
        "start_date",
        "end_date",
        "last_update_date",
        "entry_date",
    ]
    assert rows == [
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
    ]


def test_build_serving_parquet_supports_csv_sources(tmp_path: Path) -> None:
    duckdb = pytest.importorskip("duckdb")
    input_path = tmp_path / "xref_full.csv"
    output_path = tmp_path / "xref_voa_os.parquet"
    _write_input_csv(input_path)

    addressbase_build_xref.build_serving_parquet(
        input_path=input_path,
        output_path=output_path,
        drop_source_codes=["7666OW", "7666OP"],
        row_group_size=10_000,
        compression="zstd",
        sort_by_uprn=False,
        threads=1,
        memory_limit="512MB",
    )

    connection = duckdb.connect(database=":memory:")
    quoted_output = str(output_path).replace("'", "''")
    try:
        rows = connection.execute(
            f"SELECT uprn, source FROM read_parquet('{quoted_output}')"
        ).fetchall()
    finally:
        connection.close()

    assert rows == [
        ("100000000002", "7666VN"),
        ("100000000001", "7666VC"),
    ]
