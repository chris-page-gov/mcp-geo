#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def _latest_run_report(run_root: Path) -> Path | None:
    if not run_root.exists():
        return None
    candidates = sorted(run_root.glob("*/run_report.json"))
    if not candidates:
        return None
    return candidates[-1]


def _as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(v) for v in value]
    return []


def _required_variants_for_family(
    *,
    family: dict[str, Any],
    templates: dict[str, Any],
    completion_defaults: list[str],
    run_report: dict[str, Any],
) -> tuple[list[str], str]:
    if family.get("required_variants"):
        return _as_list(family.get("required_variants")), "family"
    template_name = family.get("template")
    if template_name:
        template = templates.get(template_name) or {}
        req = template.get("variant_policy", {}).get("required_variants")
        if req:
            return _as_list(req), f"template:{template_name}"
    family_id = family.get("family_id")
    if family_id:
        for section in ("resolved_resources", "downloads", "ingestions", "validations"):
            variants = run_report.get(section, {}).get(family_id)
            if isinstance(variants, dict) and variants:
                return [str(v) for v in variants.keys()], f"run_report:{section}"
    if completion_defaults:
        return completion_defaults, "manifest_defaults"
    return [], "unknown"


def _resolved_ok(entry: dict[str, Any] | None) -> tuple[bool, bool]:
    if not entry:
        return False, False
    status = entry.get("status")
    if status == "resolved":
        return True, False
    if status == "not_published":
        return bool(entry.get("evidence_ref")), True
    return False, False


def _download_ok(entry: dict[str, Any] | None) -> bool:
    if not entry:
        return False
    if entry.get("download_status") != "ok":
        return False
    if entry.get("gdal_readable") is False:
        return False
    return True


def _ingest_ok(entry: dict[str, Any] | None) -> bool:
    if not entry or not isinstance(entry, dict):
        return False
    statuses = []
    for payload in entry.values():
        if isinstance(payload, dict):
            statuses.append(payload.get("ingest_status") in {"ok", "skipped"})
    return bool(statuses) and all(statuses)


def _validation_ok(entry: dict[str, Any] | None) -> bool:
    if not entry or not isinstance(entry, dict):
        return False
    table_results = []
    for table_payload in entry.values():
        if not isinstance(table_payload, dict):
            continue
        table_results.append(_validation_table_ok(table_payload))
    return bool(table_results) and all(table_results)


def _validation_table_ok(table_payload: dict[str, Any]) -> bool:
    schema = table_payload.get("schema") or {}
    ingest = table_payload.get("ingest") or {}
    uniqueness = table_payload.get("uniqueness") or {}
    geometry = table_payload.get("geometry") or {}
    row_count = table_payload.get("row_count") or {}

    if schema.get("code_field_present") is False:
        return False
    if schema.get("name_field_present") is False:
        return False
    if ingest.get("geom_column_exists") is False:
        return False
    if ingest.get("srid") in (None, 0):
        return False
    if ingest.get("row_count") in (None, 0):
        return False
    if uniqueness.get("duplicate_code_count", 0) not in (0, None):
        return False
    if geometry.get("post_repair_invalid_geom_count", 0) not in (0, None):
        return False
    rc = row_count.get("row_count")
    rc_min = row_count.get("row_count_min")
    if rc is not None and rc_min is not None and rc < rc_min:
        return False
    return True


def _pct(num: int, den: int) -> float | None:
    if not den:
        return None
    return round((num / den) * 100.0, 2)


def _summarize(run_report: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    families = manifest.get("boundary_families", [])
    templates = manifest.get("templates", {})
    completion_defaults = _as_list(
        manifest.get("completion_definition", {}).get("required_variants")
    )

    family_status = run_report.get("family_status", {}) or {}
    resolved = run_report.get("resolved_resources", {}) or {}
    downloads = run_report.get("downloads", {}) or {}
    ingestions = run_report.get("ingestions", {}) or {}
    validations = run_report.get("validations", {}) or {}

    totals = {
        "families_total": len(families),
        "families_ok": 0,
        "families_error": 0,
        "families_unknown": 0,
        "expected_variants_total": 0,
        "expected_variants_unknown": 0,
        "resolved_ok": 0,
        "resolved_not_published": 0,
        "resolved_missing": 0,
        "download_expected": 0,
        "download_ok": 0,
        "download_failed": 0,
        "ingest_ok": 0,
        "ingest_failed": 0,
        "validation_ok": 0,
        "validation_failed": 0,
        "download_bytes": 0,
        "archive_uncompressed_bytes": 0,
        "extracted_bytes": 0,
        "ingested_table_bytes": 0,
    }
    by_family: dict[str, Any] = {}

    for family_downloads in downloads.values():
        if not isinstance(family_downloads, dict):
            continue
        for entry in family_downloads.values():
            if not isinstance(entry, dict):
                continue
            totals["download_bytes"] += int(entry.get("bytes") or 0)
            totals["archive_uncompressed_bytes"] += int(entry.get("archiveUncompressedBytes") or 0)
            totals["extracted_bytes"] += int(entry.get("extractedBytes") or 0)

    for family_ingests in ingestions.values():
        if not isinstance(family_ingests, dict):
            continue
        for variant_entry in family_ingests.values():
            if not isinstance(variant_entry, dict):
                continue
            for table_entry in variant_entry.values():
                if not isinstance(table_entry, dict):
                    continue
                totals["ingested_table_bytes"] += int(table_entry.get("tableBytes") or 0)

    for family in families:
        family_id = family.get("family_id")
        if not family_id:
            continue
        status = family_status.get(family_id)
        if status == "ok":
            totals["families_ok"] += 1
        elif status == "error":
            totals["families_error"] += 1
        else:
            totals["families_unknown"] += 1

        expected_variants, source = _required_variants_for_family(
            family=family,
            templates=templates,
            completion_defaults=completion_defaults,
            run_report=run_report,
        )
        if not expected_variants:
            totals["expected_variants_unknown"] += 1
        else:
            totals["expected_variants_total"] += len(expected_variants)

        fam_counts = {
            "status": status,
            "expected_variants": expected_variants,
            "expected_variants_source": source,
            "resolved_ok": 0,
            "resolved_not_published": 0,
            "resolved_missing": 0,
            "download_ok": 0,
            "download_failed": 0,
            "ingest_ok": 0,
            "ingest_failed": 0,
            "validation_ok": 0,
            "validation_failed": 0,
        }

        for variant in expected_variants:
            res_entry = resolved.get(family_id, {}).get(variant)
            res_ok, res_not_pub = _resolved_ok(res_entry)
            if res_ok:
                fam_counts["resolved_ok"] += 1
                totals["resolved_ok"] += 1
                if res_not_pub:
                    fam_counts["resolved_not_published"] += 1
                    totals["resolved_not_published"] += 1
            else:
                fam_counts["resolved_missing"] += 1
                totals["resolved_missing"] += 1

            if res_not_pub:
                continue

            totals["download_expected"] += 1
            dl_ok = _download_ok(downloads.get(family_id, {}).get(variant))
            if dl_ok:
                fam_counts["download_ok"] += 1
                totals["download_ok"] += 1
            else:
                fam_counts["download_failed"] += 1
                totals["download_failed"] += 1

            ing_ok = _ingest_ok(ingestions.get(family_id, {}).get(variant))
            if ing_ok:
                fam_counts["ingest_ok"] += 1
                totals["ingest_ok"] += 1
            else:
                fam_counts["ingest_failed"] += 1
                totals["ingest_failed"] += 1

            val_ok = _validation_ok(validations.get(family_id, {}).get(variant))
            if val_ok:
                fam_counts["validation_ok"] += 1
                totals["validation_ok"] += 1
            else:
                fam_counts["validation_failed"] += 1
                totals["validation_failed"] += 1

        by_family[family_id] = fam_counts

    totals["families_ok_pct"] = _pct(totals["families_ok"], totals["families_total"])
    totals["resolved_ok_pct"] = _pct(totals["resolved_ok"], totals["expected_variants_total"])
    totals["download_ok_pct"] = _pct(totals["download_ok"], totals["download_expected"])
    totals["ingest_ok_pct"] = _pct(totals["ingest_ok"], totals["download_expected"])
    totals["validation_ok_pct"] = _pct(totals["validation_ok"], totals["download_expected"])

    return {
        "pipeline_status": run_report.get("pipeline_status"),
        "run_started_at": run_report.get("run_started_at"),
        "run_finished_at": run_report.get("run_finished_at"),
        "summary": totals,
        "families": by_family,
    }


def _load_summary(path: Path) -> dict[str, Any]:
    return _load_json(path)


def _delta_summary(current: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    current_summary = current.get("summary", {})
    baseline_summary = baseline.get("summary", {})
    delta = {}
    for key, value in current_summary.items():
        if isinstance(value, (int, float)) and isinstance(baseline_summary.get(key), (int, float)):
            delta[key] = round(value - baseline_summary[key], 2)
    return delta


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize boundary run effectiveness.")
    parser.add_argument("--run-report", help="Path to run_report.json")
    parser.add_argument("--workdir", default="data/boundary_runs")
    parser.add_argument("--manifest", default="docs/Boundaries.json")
    parser.add_argument("--out", help="Write summary JSON to this path")
    parser.add_argument("--compare", help="Baseline run_report.json to compute deltas")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report_path = Path(args.run_report) if args.run_report else None
    if report_path is None:
        report_path = _latest_run_report(Path(args.workdir))
    if not report_path or not report_path.exists():
        raise SystemExit("No run_report.json found.")

    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        raise SystemExit(f"Manifest not found: {manifest_path}")

    run_report = _load_json(report_path)
    manifest = _load_json(manifest_path)
    summary = _summarize(run_report, manifest)
    summary["run_report"] = str(report_path)

    out_path = Path(args.out) if args.out else report_path.parent / "run_tracker.json"
    if args.compare:
        baseline_path = Path(args.compare)
        if baseline_path.exists():
            baseline = _summarize(_load_json(baseline_path), manifest)
            summary["baseline_run_report"] = str(baseline_path)
            summary["delta"] = _delta_summary(summary, baseline)
    _write_json(out_path, summary)
    print(json.dumps(summary, indent=2, ensure_ascii=True))
    print(f"Wrote tracker summary: {out_path}")


if __name__ == "__main__":
    main()
