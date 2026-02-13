#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import scripts.boundary_run_tracker as tracker


REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _latest_run_report(run_root: Path) -> Path | None:
    if not run_root.exists():
        return None
    candidates = sorted(run_root.glob("*/run_report.json"))
    if not candidates:
        return None
    return candidates[-1]


def _error_counts(report: dict[str, Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for entry in report.get("errors", []) or []:
        for err in entry.get("errors", []) or []:
            key = str(err).split(":")[0]
            counts[key] = counts.get(key, 0) + 1
    return counts


def _format_counts(counts: dict[str, int]) -> str:
    if not counts:
        return "none"
    parts = [f"{k}={v}" for k, v in sorted(counts.items())]
    return ", ".join(parts)


def _print_status(report_path: Path, manifest_path: Path) -> None:
    report = _load_json(report_path)
    manifest = _load_json(manifest_path)
    summary = tracker._summarize(report, manifest)["summary"]
    errors = _error_counts(report)
    exceptions = len(report.get("exceptions", []) or [])
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    line = (
        f"[{timestamp}] families_ok={summary['families_ok']}/{summary['families_total']} "
        f"downloads_ok={summary['download_ok']}/{summary['download_expected']} "
        f"ingest_ok={summary['ingest_ok']}/{summary['download_expected']} "
        f"validation_ok={summary['validation_ok']}/{summary['download_expected']} "
        f"errors=({ _format_counts(errors) }) exceptions={exceptions}"
    )
    print(line)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Boundary pipeline status ticker.")
    parser.add_argument("--manifest", default="docs/Boundaries.json")
    parser.add_argument("--workdir", default="data/boundary_runs")
    parser.add_argument("--watch", action="store_true", help="Emit ticker updates repeatedly.")
    parser.add_argument("--interval", type=int, default=60, help="Seconds between updates.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_root = Path(args.workdir)
    report_path = _latest_run_report(run_root)
    if report_path is None:
        raise SystemExit(f"No run_report.json found under {run_root}")
    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        raise SystemExit(f"Missing manifest at {manifest_path}")
    if not args.watch:
        _print_status(report_path, manifest_path)
        return
    while True:
        report_path = _latest_run_report(run_root)
        if report_path is None:
            print("Waiting for run_report.json...")
        else:
            _print_status(report_path, manifest_path)
        time.sleep(max(5, args.interval))


if __name__ == "__main__":
    main()
