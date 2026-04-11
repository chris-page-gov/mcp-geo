from __future__ import annotations

from pathlib import Path

from server import boundary_run_paths


def _write_run(root: Path, run_id: str, payload: str = "{}") -> Path:
    report = root / run_id / "run_report.json"
    report.parent.mkdir(parents=True)
    report.write_text(payload, encoding="utf-8")
    return report


def test_boundary_run_dir_candidates_accept_data_root(tmp_path: Path) -> None:
    data_root = tmp_path / "Data"

    candidates = boundary_run_paths.boundary_run_dir_candidates(data_root)

    assert candidates == [data_root, data_root / "boundary_runs"]


def test_latest_boundary_run_report_searches_extra_data_roots(tmp_path: Path) -> None:
    primary = tmp_path / "local_runs"
    external_data_root = tmp_path / "ExtSSD-Data" / "Data"
    older = _write_run(primary, "20260101T000000Z", '{"source":"local"}')
    newer = _write_run(
        external_data_root / "boundary_runs",
        "20260102T000000Z",
        '{"source":"external"}',
    )

    latest = boundary_run_paths.latest_boundary_run_report(primary, [external_data_root])

    assert latest == newer
    assert latest != older


def test_latest_boundary_run_report_prefers_primary_when_run_ids_tie(tmp_path: Path) -> None:
    primary = tmp_path / "local_runs"
    external_data_root = tmp_path / "ExtSSD-Data" / "Data"
    primary_report = _write_run(primary, "20260102T000000Z", '{"source":"local"}')
    _write_run(
        external_data_root / "boundary_runs",
        "20260102T000000Z",
        '{"source":"external"}',
    )

    latest = boundary_run_paths.latest_boundary_run_report(primary, [external_data_root])

    assert latest == primary_report
