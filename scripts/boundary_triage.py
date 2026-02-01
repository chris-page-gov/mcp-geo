#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import scripts.boundary_run_tracker as tracker


REPO_ROOT = Path(__file__).resolve().parents[1]

ERROR_FIXES = {
    "code_field_missing": {
        "cause": "Expected code column not detected by regex.",
        "fix": "Update validation_overrides.code_column_regex for the family in docs/Boundaries.json.",
    },
    "name_field_missing": {
        "cause": "Expected name column not detected by regex.",
        "fix": "Update validation_overrides.name_column_regex for the family in docs/Boundaries.json.",
    },
    "duplicate_codes": {
        "cause": "Dataset has non-unique codes within a layer.",
        "fix": "Allow duplicates via validation_overrides.allow_duplicate_codes or exclude the layer.",
    },
    "invalid_geometry": {
        "cause": "Geometries remain invalid after ST_MakeValid.",
        "fix": "Switch to a different variant or exclude the layer; inspect invalid rows.",
    },
    "row_count_low": {
        "cause": "Ingested row count below expected minimum.",
        "fix": "Adjust validation_overrides.row_count_sanity.min or fix layer selection.",
    },
}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _latest_run_report(run_root: Path) -> Path | None:
    if not run_root.exists():
        return None
    candidates = sorted(run_root.glob("*/run_report.json"))
    if not candidates:
        return None
    return candidates[-1]


def _variant_status_ok(entry: dict[str, Any] | None) -> bool:
    return bool(entry and entry.get("download_status") == "ok")


def _ingest_ok(entry: dict[str, Any] | None) -> bool:
    return tracker._ingest_ok(entry)


def _validation_failures(
    report: dict[str, Any],
    *,
    only_when_ingest_ok: bool = True,
) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    for family_id, variants in (report.get("validations", {}) or {}).items():
        for variant, tables in (variants or {}).items():
            if only_when_ingest_ok:
                download_entry = report.get("downloads", {}).get(family_id, {}).get(variant)
                ingest_entry = report.get("ingestions", {}).get(family_id, {}).get(variant)
                if not _variant_status_ok(download_entry):
                    continue
                if not _ingest_ok(ingest_entry):
                    continue
            for table, payload in (tables or {}).items():
                schema = payload.get("schema", {}) or {}
                uniq = payload.get("uniqueness", {}) or {}
                geom = payload.get("geometry", {}) or {}
                row = payload.get("row_count", {}) or {}
                if schema.get("code_field_present") is False:
                    failures.append(
                        {
                            "family_id": family_id,
                            "variant": variant,
                            "table": table,
                            "error": "code_field_missing",
                        }
                    )
                if schema.get("name_field_present") is False:
                    failures.append(
                        {
                            "family_id": family_id,
                            "variant": variant,
                            "table": table,
                            "error": "name_field_missing",
                        }
                    )
                if uniq.get("duplicate_code_count", 0) not in (0, None):
                    failures.append(
                        {
                            "family_id": family_id,
                            "variant": variant,
                            "table": table,
                            "error": "duplicate_codes",
                            "count": uniq.get("duplicate_code_count"),
                        }
                    )
                if geom.get("post_repair_invalid_geom_count", 0) not in (0, None):
                    failures.append(
                        {
                            "family_id": family_id,
                            "variant": variant,
                            "table": table,
                            "error": "invalid_geometry",
                            "count": geom.get("post_repair_invalid_geom_count"),
                        }
                    )
                if row:
                    rc = row.get("row_count")
                    rc_min = row.get("row_count_min")
                    if rc is not None and rc_min is not None and rc < rc_min:
                        failures.append(
                            {
                                "family_id": family_id,
                                "variant": variant,
                                "table": table,
                                "error": "row_count_low",
                                "row_count": rc,
                                "row_count_min": rc_min,
                            }
                        )
    return failures


def _error_counts(failures: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for entry in failures:
        key = entry.get("error")
        counts[key] = counts.get(key, 0) + 1
    return counts


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Boundary pipeline triage helper.")
    parser.add_argument("--manifest", default="docs/Boundaries.json")
    parser.add_argument("--workdir", default="data/boundary_runs")
    parser.add_argument("--output", default=None, help="Write triage JSON to this path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report_path = _latest_run_report(Path(args.workdir))
    if report_path is None:
        raise SystemExit("No run_report.json found.")
    report = _load_json(report_path)
    manifest = _load_json(Path(args.manifest))
    summary = tracker._summarize(report, manifest)["summary"]
    failures = _validation_failures(report, only_when_ingest_ok=True)
    counts = _error_counts(failures)
    triage = {
        "run_report": str(report_path),
        "summary": summary,
        "validation_failures": failures,
        "validation_error_counts": counts,
        "error_fixes": ERROR_FIXES,
    }
    if args.output:
        _write_json(Path(args.output), triage)
    print(json.dumps(triage, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
