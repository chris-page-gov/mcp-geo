from __future__ import annotations

import json
import sys
from pathlib import Path

import scripts.route_graph_pipeline as route_graph_pipeline


def test_capture_provenance_drops_sensitive_download_fields(tmp_path: Path, monkeypatch) -> None:
    def fake_downloads_get(path: str):
        if path == "/products":
            return (
                200,
                [
                    {
                        "id": "os-mrn",
                        "name": "OS Multi Modal Routing Network",
                        "license": "Open Government Licence",
                        "downloadUrl": "https://example.invalid/products/os-mrn?token=abc123",
                    }
                ],
            )
        if path == "/products/os-mrn/downloads":
            return (
                200,
                [
                    {
                        "id": "mrn-2026-03-01",
                        "name": "March 2026 MRN",
                        "releaseDate": "2026-03-01",
                        "checksum": "sha256:deadbeef",
                        "url": "https://example.invalid/download?password=hunter2",
                        "apiToken": "abc123",
                    }
                ],
            )
        raise AssertionError(path)

    monkeypatch.setattr(route_graph_pipeline, "_downloads_get", fake_downloads_get)

    output_path = tmp_path / "os_mrn_downloads.json"
    payload = route_graph_pipeline._capture_provenance(
        "multi modal routing network",
        limit=10,
        output_path=output_path,
    )

    assert payload["selectedProduct"] == {
        "id": "os-mrn",
        "name": "OS Multi Modal Routing Network",
        "license": "Open Government Licence",
    }
    assert payload["latestDownload"] == {
        "id": "mrn-2026-03-01",
        "name": "March 2026 MRN",
        "releaseDate": "2026-03-01",
        "checksum": "sha256:deadbeef",
    }

    stored = json.loads(output_path.read_text(encoding="utf-8"))
    assert stored == payload
    assert "url" not in stored["latestDownload"]
    assert "apiToken" not in stored["latestDownload"]
    text = output_path.read_text(encoding="utf-8")
    assert "hunter2" not in text
    assert "abc123" not in text


def test_bootstrap_schema_result_does_not_include_raw_dsn(monkeypatch, tmp_path: Path) -> None:
    dsn = "postgresql://mcp_geo:supersecret@postgis:5432/mcp_geo"
    schema_path = tmp_path / "route_graph_schema.sql"
    schema_path.write_text("SELECT 1;", encoding="utf-8")

    executed: list[str] = []

    class _Cursor:
        def __enter__(self) -> _Cursor:
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def execute(self, sql: str) -> None:
            executed.append(sql)

    class _Connection:
        def __enter__(self) -> _Connection:
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def cursor(self) -> _Cursor:
            return _Cursor()

    class _Psycopg:
        @staticmethod
        def connect(received_dsn: str, autocommit: bool = False) -> _Connection:
            assert received_dsn == dsn
            assert autocommit is True
            return _Connection()

    monkeypatch.setattr(route_graph_pipeline, "psycopg", _Psycopg())
    monkeypatch.setattr(route_graph_pipeline, "_SCHEMA_SQL", schema_path)

    result = route_graph_pipeline._bootstrap_schema(dsn)

    assert executed == ["SELECT 1;"]
    assert result == {
        "dsnConfigured": True,
        "schemaSql": str(schema_path),
        "status": "bootstrapped",
    }
    assert dsn not in json.dumps(result, ensure_ascii=True)


def test_main_redacts_dsn_in_error_output(monkeypatch, capsys) -> None:
    dsn = "postgresql://mcp_geo:supersecret@postgis:5432/mcp_geo"

    def fake_bootstrap(received_dsn: str) -> dict[str, object]:
        raise RuntimeError(f"failed to connect using {received_dsn}")

    monkeypatch.setattr(route_graph_pipeline, "_bootstrap_schema", fake_bootstrap)
    monkeypatch.setattr(
        sys,
        "argv",
        ["route_graph_pipeline.py", "bootstrap", "--dsn", dsn],
    )

    assert route_graph_pipeline.main() == 1

    output = capsys.readouterr().out
    assert "supersecret" not in output
    assert dsn not in output
    assert "[REDACTED]" in output
