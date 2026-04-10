from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

try:
    import duckdb
except ImportError:  # pragma: no cover - optional dependency fallback
    duckdb = None  # type: ignore[assignment]

DEFAULT_DROP_SOURCE_CODES = ("7666OW", "7666OP")
DEFAULT_ROW_GROUP_SIZE = 250_000
DEFAULT_COMPRESSION = "zstd"
DEFAULT_THREADS = 1
DEFAULT_MEMORY_LIMIT = "1GB"

CANONICAL_COLUMN_ALIASES = {
    "UPRN": ("UPRN", "uprn"),
    "XREF_KEY": ("XREF_KEY", "xRefKey", "xref_key"),
    "CROSS_REFERENCE": ("CROSS_REFERENCE", "crossReference", "cross_reference"),
    "SOURCE": ("SOURCE", "source"),
    "VERSION": ("VERSION", "version"),
    "START_DATE": ("START_DATE", "startDate", "start_date"),
    "END_DATE": ("END_DATE", "endDate", "end_date"),
    "LAST_UPDATE_DATE": ("LAST_UPDATE_DATE", "lastUpdateDate", "last_update_date"),
    "ENTRY_DATE": ("ENTRY_DATE", "entryDate", "entry_date"),
}
REQUIRED_COLUMNS = {"UPRN", "SOURCE"}
OUTPUT_COLUMNS = (
    ("UPRN", "uprn"),
    ("XREF_KEY", "xref_key"),
    ("CROSS_REFERENCE", "cross_reference"),
    ("SOURCE", "source"),
    ("VERSION", "version"),
    ("START_DATE", "start_date"),
    ("END_DATE", "end_date"),
    ("LAST_UPDATE_DATE", "last_update_date"),
    ("ENTRY_DATE", "entry_date"),
)


def _normalize_column_name(value: str) -> str:
    return "".join(ch for ch in value.lower() if ch.isalnum())


def _resolve_column_mapping(fieldnames: list[str]) -> tuple[dict[str, str], list[str]]:
    actual_by_normalized = {
        _normalize_column_name(fieldname): fieldname
        for fieldname in fieldnames
        if fieldname
    }
    mapping: dict[str, str] = {}
    missing: list[str] = []
    for canonical, aliases in CANONICAL_COLUMN_ALIASES.items():
        actual = next(
            (
                actual_by_normalized.get(_normalize_column_name(alias))
                for alias in aliases
                if actual_by_normalized.get(_normalize_column_name(alias))
            ),
            None,
        )
        if actual is None:
            if canonical in REQUIRED_COLUMNS:
                missing.append(canonical)
            continue
        mapping[canonical] = actual
    return mapping, missing


def _quote_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def _quoted_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _source_relation_sql(input_path: Path) -> str:
    suffix = input_path.suffix.lower()
    quoted = _quoted_literal(str(input_path))
    if suffix == ".parquet":
        return f"read_parquet({quoted})"
    if suffix == ".csv":
        return f"read_csv_auto({quoted}, header=true, all_varchar=true)"
    raise ValueError(f"Unsupported input file type: {input_path.suffix or '<none>'}")


def _projection_expression(mapping: dict[str, str], canonical: str, alias: str) -> str:
    actual = mapping.get(canonical)
    if actual is None:
        return f"CAST(NULL AS VARCHAR) AS {alias}"
    expression = f"CAST({_quote_identifier(actual)} AS VARCHAR)"
    if canonical == "SOURCE":
        expression = f"UPPER(TRIM({expression}))"
    return f"{expression} AS {alias}"


def build_serving_parquet(
    *,
    input_path: Path,
    output_path: Path,
    drop_source_codes: list[str],
    row_group_size: int,
    compression: str,
    sort_by_uprn: bool,
    threads: int,
    memory_limit: str,
) -> dict[str, Any]:
    if duckdb is None:
        raise RuntimeError("duckdb is required to build AddressBase parquet derivatives")

    relation_sql = _source_relation_sql(input_path)
    connection = duckdb.connect(database=":memory:")  # type: ignore[union-attr]
    try:
        connection.execute(f"PRAGMA threads={max(1, threads)}")
        if memory_limit.strip():
            connection.execute(f"SET memory_limit={_quoted_literal(memory_limit.strip())}")

        schema_rows = connection.execute(f"DESCRIBE SELECT * FROM {relation_sql}").fetchall()
        column_mapping, missing = _resolve_column_mapping(
            [str(row[0]) for row in schema_rows if row and row[0]]
        )
        if missing:
            raise ValueError(
                "AddressBase source is missing required columns: " + ", ".join(sorted(missing))
            )

        projection_sql = ",\n                ".join(
            _projection_expression(column_mapping, canonical, alias)
            for canonical, alias in OUTPUT_COLUMNS
        )
        drop_codes_sql = ", ".join(_quoted_literal(code.upper()) for code in drop_source_codes)
        source_filter_expression = (
            f"UPPER(TRIM(CAST({_quote_identifier(column_mapping['SOURCE'])} AS VARCHAR)))"
        )
        order_sql = "ORDER BY uprn, source, cross_reference, xref_key" if sort_by_uprn else ""

        output_path.parent.mkdir(parents=True, exist_ok=True)
        source_count = connection.execute(
            f"""
            SELECT COUNT(*)
            FROM {relation_sql}
            WHERE {source_filter_expression} NOT IN ({drop_codes_sql})
            """
        ).fetchone()[0]

        copy_sql = f"""
        COPY (
            SELECT
                {projection_sql}
            FROM {relation_sql}
            WHERE {source_filter_expression} NOT IN ({drop_codes_sql})
            {order_sql}
        ) TO {_quoted_literal(str(output_path))}
        (
            FORMAT PARQUET,
            COMPRESSION {_quoted_literal(compression)},
            ROW_GROUP_SIZE {int(row_group_size)}
        )
        """
        connection.execute(copy_sql)
    finally:
        connection.close()

    return {
        "inputPath": str(input_path),
        "outputPath": str(output_path),
        "retainedRowCount": int(source_count),
        "droppedSourceCodes": [code.upper() for code in drop_source_codes],
        "sortByUprn": sort_by_uprn,
        "compression": compression,
        "rowGroupSize": int(row_group_size),
    }


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build a Parquet serving file for AddressBase Premium XRef workloads using DuckDB."
        )
    )
    parser.add_argument("--input", required=True, help="Source xref CSV or Parquet file.")
    parser.add_argument("--output", required=True, help="Destination Parquet file.")
    parser.add_argument(
        "--drop-source-code",
        action="append",
        default=None,
        help=(
            "SOURCE code to exclude from the serving Parquet. "
            "Defaults to 7666OW and 7666OP."
        ),
    )
    parser.add_argument(
        "--row-group-size",
        type=int,
        default=DEFAULT_ROW_GROUP_SIZE,
        help=f"Parquet row group size. Default: {DEFAULT_ROW_GROUP_SIZE}.",
    )
    parser.add_argument(
        "--compression",
        default=DEFAULT_COMPRESSION,
        help=f"Parquet compression codec. Default: {DEFAULT_COMPRESSION}.",
    )
    parser.add_argument(
        "--threads",
        type=int,
        default=DEFAULT_THREADS,
        help=f"DuckDB thread count. Default: {DEFAULT_THREADS}.",
    )
    parser.add_argument(
        "--memory-limit",
        default=DEFAULT_MEMORY_LIMIT,
        help=f"DuckDB memory limit. Default: {DEFAULT_MEMORY_LIMIT}.",
    )
    parser.add_argument(
        "--no-sort",
        action="store_true",
        help="Skip the ORDER BY uprn/source step when writing the serving Parquet.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    drop_source_codes = args.drop_source_code or list(DEFAULT_DROP_SOURCE_CODES)
    result = build_serving_parquet(
        input_path=input_path,
        output_path=output_path,
        drop_source_codes=[code.upper() for code in drop_source_codes],
        row_group_size=args.row_group_size,
        compression=args.compression,
        sort_by_uprn=not args.no_sort,
        threads=args.threads,
        memory_limit=args.memory_limit,
    )
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
