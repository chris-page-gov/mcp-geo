#!/usr/bin/env python3
"""Opt-in live validation for resolver-driven ONS geo sources."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.ons_geo_cache_refresh import (
    DEFAULT_SOURCES_PATH,
    _build_field_mapping,
    _open_rows,
    load_manifest,
    probe_dataset_source,
)
from server.ons_geo_freshness import (
    load_addressbase_epoch_schedule,
    summarize_uprn_dataset_freshness,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Resolve ONS geo sources and validate their schemas without "
            "ingesting the cache."
        )
    )
    parser.add_argument(
        "--sources",
        default=str(DEFAULT_SOURCES_PATH),
        help="Path to sources manifest JSON",
    )
    parser.add_argument("--timeout", type=float, default=60.0, help="HTTP timeout seconds")
    parser.add_argument(
        "--product-file",
        action="append",
        default=[],
        help="Dataset input override as DATASET_ID=/path/to/file (repeatable)",
    )
    parser.add_argument(
        "--product-url",
        action="append",
        default=[],
        help="Dataset URL override as DATASET_ID=https://... (repeatable)",
    )
    return parser.parse_args()


def _parse_map(values: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in values:
        key, _, value = item.partition("=")
        key = key.strip().upper()
        value = value.strip()
        if key and value:
            out[key] = value
    return out


def main() -> int:
    args = parse_args()
    version, products, support_products = load_manifest(Path(args.sources).resolve())
    file_overrides = _parse_map(args.product_file)
    url_overrides = _parse_map(args.product_url)
    summaries: list[dict[str, object]] = []
    failures = 0
    warnings = 0
    epoch_schedule = load_addressbase_epoch_schedule()

    for dataset in [*support_products, *products]:
        try:
            probe = probe_dataset_source(
                dataset,
                timeout=float(args.timeout),
                file_overrides=file_overrides,
                url_overrides=url_overrides,
            )
            fieldnames = list(probe.schema_fields)
            metadata_aliases = dict(probe.field_aliases)
            if probe.schema_probe_status == "local_file":
                source_path_text = str(probe.metadata.get("sourcePath") or "").strip()
                if not source_path_text:
                    raise ValueError(
                        f"Local probe for {dataset.dataset_id} did not include sourcePath metadata"
                    )
                with _open_rows(Path(source_path_text), dataset=dataset) as (
                    _rows_iter,
                    local_fieldnames,
                ):
                    fieldnames = local_fieldnames or fieldnames

            if fieldnames:
                mapping, schema_validation = _build_field_mapping(
                    dataset,
                    fieldnames=fieldnames,
                    metadata_aliases=metadata_aliases,
                )
                status = (
                    "ok" if not schema_validation.get("requiredMissing") else "schema_drift"
                )
            else:
                mapping = {}
                schema_validation = {
                    "requiredFound": [],
                    "requiredMissing": [],
                    "optionalFound": [],
                    "unknownFields": [],
                    "status": "not_checked",
                }
                status = "warning" if probe.warning else "ok"

            freshness = summarize_uprn_dataset_freshness(
                dataset_id=dataset.dataset_id,
                resolved_release=probe.resolved_release,
                resolved_source_url=probe.resolved_source_url,
                schedule=epoch_schedule,
            )
            warning_messages: list[str] = []
            if probe.warning:
                warning_messages.append(str(probe.warning))
            if isinstance(freshness, dict) and freshness.get("status") == "lagging":
                warning_messages.append(
                    str(freshness.get("message") or "Dataset epoch is lagging.")
                )
                if status == "ok":
                    status = "warning"

            if status == "schema_drift":
                failures += 1
            elif status == "warning":
                warnings += 1
            summaries.append(
                {
                    "id": dataset.dataset_id,
                    "kind": dataset.dataset_kind,
                    "status": status,
                    "resolverType": probe.resolver_type,
                    "resolvedRelease": probe.resolved_release,
                    "resolvedSourceUrl": probe.resolved_source_url,
                    "sourceFormat": probe.source_format,
                    "schemaProbeStatus": probe.schema_probe_status,
                    "matchedFields": mapping,
                    "schemaValidation": schema_validation,
                    "freshness": freshness,
                    "warning": " ".join(warning_messages) or None,
                }
            )
        except Exception as exc:  # pragma: no cover - live validation path
            failures += 1
            summaries.append(
                {
                    "id": dataset.dataset_id,
                    "kind": dataset.dataset_kind,
                    "status": "error",
                    "error": str(exc),
                }
            )

    payload = {
        "version": version,
        "status": "error" if failures else ("warning" if warnings else "ok"),
        "datasets": summaries,
    }
    print(json.dumps(payload, ensure_ascii=True, indent=2))
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
