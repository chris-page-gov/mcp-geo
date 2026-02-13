#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


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


def _error_signature(errors: list[dict[str, Any]]) -> list[str]:
    signature: list[str] = []
    for entry in errors:
        family_id = entry.get("family_id") or "unknown"
        for err in entry.get("errors", []) or []:
            signature.append(f"{family_id}:{err}")
    return sorted(signature)


def _families_from_errors(errors: list[dict[str, Any]]) -> list[str]:
    families = []
    for entry in errors:
        family_id = entry.get("family_id")
        if family_id:
            families.append(str(family_id))
    return sorted(set(families))


def _run_pipeline(args: list[str]) -> int:
    cmd = ["python", "scripts/boundary_pipeline.py", *args]
    return subprocess.call(cmd, cwd=REPO_ROOT.as_posix())


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run full boundary pipeline then rerun failing families until stable."
    )
    parser.add_argument("--workdir", default="data/boundary_runs")
    parser.add_argument("--manifest", default="docs/Boundaries.json")
    parser.add_argument("--max-iterations", type=int, default=5)
    parser.add_argument("--sleep", type=int, default=2)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_root = Path(args.workdir)
    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        raise SystemExit(f"Missing manifest at {manifest_path}")

    print(f"[{_timestamp()}] starting full run")
    exit_code = _run_pipeline(["--mode", "all"])
    if exit_code != 0:
        raise SystemExit(f"pipeline failed with exit code {exit_code}")

    previous_signature: list[str] | None = None
    for iteration in range(1, args.max_iterations + 1):
        report_path = _latest_run_report(run_root)
        if report_path is None:
            raise SystemExit("No run_report.json produced by pipeline.")
        report = _load_json(report_path)
        errors = report.get("errors", []) or []
        if not errors:
            print(f"[{_timestamp()}] no errors, done")
            return
        signature = _error_signature(errors)
        if previous_signature is not None and signature == previous_signature:
            print(f"[{_timestamp()}] error set unchanged after iteration {iteration}, stopping")
            return
        previous_signature = signature
        families = _families_from_errors(errors)
        if not families:
            print(f"[{_timestamp()}] no failing families found, stopping")
            return
        print(
            f"[{_timestamp()}] iteration {iteration} rerun families={len(families)} "
            f"({', '.join(families)})"
        )
        exit_code = _run_pipeline(["--mode", "all", *sum([["--family", f] for f in families], [])])
        if exit_code != 0:
            raise SystemExit(f"pipeline failed with exit code {exit_code}")
        time.sleep(max(1, int(args.sleep)))

    print(f"[{_timestamp()}] reached max iterations without convergence")


if __name__ == "__main__":
    main()
