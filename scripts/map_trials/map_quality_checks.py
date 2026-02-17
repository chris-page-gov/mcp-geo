#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from PIL import Image

DEFAULT_OBS = "research/map_delivery_research_2026-02/evidence/logs/playwright_trials_observations.jsonl"
DEFAULT_OUT = "research/map_delivery_research_2026-02/reports/map_quality_report.json"
DEFAULT_WAIVERS = "research/map_delivery_research_2026-02/reports/map_quality_waivers.json"

CONTRAST_FAIL_MIN = 0.20
CONTRAST_WARN_MIN = 0.28
LABEL_DENSITY_WARN_MIN = 0.22
LABEL_DENSITY_FAIL_MIN = 0.36


@dataclass(frozen=True)
class QualityMetrics:
    contrast: float
    label_density: float


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_observations(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def _parse_timestamp(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    normalized = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


def latest_rows(rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    latest: dict[tuple[str, str], tuple[datetime | None, int, dict[str, Any]]] = {}
    for index, row in enumerate(rows):
        trial = str(row.get("trialId", ""))
        browser = str(row.get("browser", ""))
        ts = _parse_timestamp(row.get("timestamp"))
        key = (trial, browser)
        current = latest.get(key)
        if current is None:
            latest[key] = (ts, index, row)
            continue
        current_ts, current_index, _ = current
        if ts is not None and current_ts is not None:
            if ts > current_ts or (ts == current_ts and index > current_index):
                latest[key] = (ts, index, row)
            continue
        if ts is not None and current_ts is None:
            latest[key] = (ts, index, row)
            continue
        if ts is None and current_ts is None and index > current_index:
            latest[key] = (ts, index, row)
    return {key: value[2] for key, value in latest.items()}


def resolve_path(path_text: str | None, repo_root: Path) -> Path | None:
    if not path_text:
        return None
    normalized = str(path_text)
    for prefix in ("/workspaces/mcp-geo/", "/workspace/mcp-geo/"):
        if normalized.startswith(prefix):
            normalized = str(repo_root / normalized[len(prefix) :])
            break
    path = Path(normalized)
    if path.is_absolute():
        return path
    return (repo_root / path).resolve()


def to_relative(path: Path, repo_root: Path) -> str:
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(path)


def image_quality_metrics(path: Path) -> QualityMetrics:
    img = Image.open(path).convert("L")
    width, height = img.size
    pixels = img.load()
    values: list[int] = []
    edge_hits = 0
    edge_total = 0
    step = max(1, min(width, height) // 120)
    for y in range(0, height, step):
        for x in range(0, width, step):
            value = int(pixels[x, y])
            values.append(value)
            if x + step < width:
                edge_total += 1
                if abs(value - int(pixels[x + step, y])) > 18:
                    edge_hits += 1
            if y + step < height:
                edge_total += 1
                if abs(value - int(pixels[x, y + step])) > 18:
                    edge_hits += 1
    if not values:
        return QualityMetrics(contrast=0.0, label_density=0.0)
    ordered = sorted(values)
    lo = ordered[int(0.05 * (len(ordered) - 1))]
    hi = ordered[int(0.95 * (len(ordered) - 1))]
    contrast = (hi - lo) / 255.0
    label_density = (edge_hits / edge_total) if edge_total else 0.0
    return QualityMetrics(contrast=contrast, label_density=label_density)


def load_waivers(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        return {}
    waivers = obj.get("waivers")
    if not isinstance(waivers, list):
        return {}
    out: dict[str, str] = {}
    for entry in waivers:
        if not isinstance(entry, dict):
            continue
        trial_id = entry.get("trialId")
        reason = entry.get("reason")
        if isinstance(trial_id, str) and trial_id.strip():
            out[trial_id.strip()] = str(reason or "waiver")
    return out


def classify(
    *,
    trial_id: str,
    metrics: QualityMetrics,
    accessibility_present: bool,
    waivers: dict[str, str],
) -> tuple[str, list[str], str | None]:
    findings: list[str] = []
    status = "pass"

    if metrics.contrast < CONTRAST_FAIL_MIN:
        status = "fail"
        findings.append(f"contrast below fail threshold ({metrics.contrast:.3f} < {CONTRAST_FAIL_MIN:.2f})")
    elif metrics.contrast < CONTRAST_WARN_MIN:
        status = "warning"
        findings.append(f"contrast below warn threshold ({metrics.contrast:.3f} < {CONTRAST_WARN_MIN:.2f})")

    if metrics.label_density >= LABEL_DENSITY_FAIL_MIN:
        status = "fail"
        findings.append(
            f"label density above fail threshold ({metrics.label_density:.3f} >= {LABEL_DENSITY_FAIL_MIN:.2f})"
        )
    elif metrics.label_density >= LABEL_DENSITY_WARN_MIN and status == "pass":
        status = "warning"
        findings.append(
            f"label density above warn threshold ({metrics.label_density:.3f} >= {LABEL_DENSITY_WARN_MIN:.2f})"
        )

    if not accessibility_present and status == "pass":
        status = "warning"
        findings.append("accessibility metadata missing")

    waiver_reason = waivers.get(trial_id)
    if waiver_reason and status == "fail":
        status = "warning"
        findings.append(f"waiver applied: {waiver_reason}")
        return status, findings, waiver_reason
    return status, findings, None


def build_report(*, repo_root: Path, observations: list[dict[str, Any]], waivers: dict[str, str]) -> dict[str, Any]:
    latest = latest_rows(observations)
    checks: list[dict[str, Any]] = []
    status_counter: Counter[str] = Counter()

    for (_trial, _browser), row in sorted(latest.items(), key=lambda item: (item[0][0], item[0][1])):
        trial_id = str(row.get("trialId", "unknown"))
        browser = str(row.get("browser", "unknown"))
        details = row.get("details", {})
        if not isinstance(details, dict):
            continue
        map_panel = resolve_path(details.get("mapPanel"), repo_root)
        if map_panel is None or not map_panel.exists():
            continue
        metrics = image_quality_metrics(map_panel)
        accessibility_meta = details.get("accessibility")
        accessibility_present = isinstance(accessibility_meta, dict) and bool(accessibility_meta.get("altText"))
        status, findings, waiver = classify(
            trial_id=trial_id,
            metrics=metrics,
            accessibility_present=accessibility_present,
            waivers=waivers,
        )
        status_counter[status] += 1
        checks.append(
            {
                "trialId": trial_id,
                "browser": browser,
                "status": status,
                "findings": findings,
                "waiver": waiver,
                "metrics": {
                    "contrast": round(metrics.contrast, 4),
                    "labelDensity": round(metrics.label_density, 4),
                },
                "mapPanel": to_relative(map_panel, repo_root),
                "accessibilityPresent": accessibility_present,
            }
        )

    return {
        "generatedAt": datetime.now(tz=UTC).isoformat().replace("+00:00", "Z"),
        "thresholds": {
            "contrastFailMin": CONTRAST_FAIL_MIN,
            "contrastWarnMin": CONTRAST_WARN_MIN,
            "labelDensityWarnMin": LABEL_DENSITY_WARN_MIN,
            "labelDensityFailMin": LABEL_DENSITY_FAIL_MIN,
        },
        "statusCounts": dict(status_counter),
        "checks": checks,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run map output quality checks over trial screenshots.")
    parser.add_argument("--repo-root", default=str(_repo_root()), help="Repository root path.")
    parser.add_argument("--observations", default=DEFAULT_OBS, help="Observation JSONL path.")
    parser.add_argument("--out", default=DEFAULT_OUT, help="Output report JSON path.")
    parser.add_argument("--waivers", default=DEFAULT_WAIVERS, help="Optional waiver file path.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    observations = load_observations((repo_root / args.observations).resolve())
    waivers = load_waivers((repo_root / args.waivers).resolve())
    report = build_report(repo_root=repo_root, observations=observations, waivers=waivers)
    out_path = (repo_root / args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
