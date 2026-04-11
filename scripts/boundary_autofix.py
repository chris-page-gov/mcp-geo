#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from server.boundary_run_paths import (  # noqa: E402
    latest_boundary_run_report,
    resolve_boundary_run_dir,
)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def _run_pipeline(args: list[str], *, workdir: Path) -> int:
    cmd = ["python", "scripts/boundary_pipeline.py", "--workdir", workdir.as_posix(), *args]
    return subprocess.call(cmd, cwd=REPO_ROOT.as_posix())


def _timestamp() -> str:
    return datetime.now(datetime.UTC).strftime("%Y-%m-%d %H:%M:%SZ")


def _family_args(families: Iterable[str]) -> list[str]:
    args: list[str] = []
    for family in families:
        args.extend(["--family", family])
    return args


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run full boundary pipeline then rerun failing families until stable."
    )
    parser.add_argument("--workdir", default=None)
    parser.add_argument("--manifest", default="docs/Boundaries.json")
    parser.add_argument("--max-iterations", type=int, default=5)
    parser.add_argument("--sleep", type=int, default=2)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_root = resolve_boundary_run_dir(args.workdir)
    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        raise SystemExit(f"Missing manifest at {manifest_path}")

    print(f"[{_timestamp()}] starting full run")
    exit_code = _run_pipeline(["--mode", "all"], workdir=run_root)
    if exit_code != 0:
        raise SystemExit(f"pipeline failed with exit code {exit_code}")

    previous_signature: list[str] | None = None
    for iteration in range(1, args.max_iterations + 1):
        report_path = latest_boundary_run_report(run_root)
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
        exit_code = _run_pipeline(
            ["--mode", "all", *_family_args(families)],
            workdir=run_root,
        )
        if exit_code != 0:
            raise SystemExit(f"pipeline failed with exit code {exit_code}")
        time.sleep(max(1, int(args.sleep)))

    print(f"[{_timestamp()}] reached max iterations without convergence")


if __name__ == "__main__":
    main()
