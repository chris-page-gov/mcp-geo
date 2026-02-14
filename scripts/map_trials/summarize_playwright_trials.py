#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def load_observations(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def load_result_stats(path: Path) -> dict[str, int]:
    if not path.exists():
        return {}
    obj = json.loads(path.read_text(encoding="utf-8"))
    counts: dict[str, int] = defaultdict(int)

    def walk_suite(suite: dict) -> None:
        for spec in suite.get("specs", []):
            for test in spec.get("tests", []):
                for result in test.get("results", []):
                    status = result.get("status") or "unknown"
                    counts[status] += 1
        for child in suite.get("suites", []):
            walk_suite(child)

    for suite in obj.get("suites", []):
        walk_suite(suite)
    return dict(sorted(counts.items()))


def load_quality_report(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        return {}
    return obj


def to_rel(path: str | None, repo_root: Path) -> str | None:
    if not path:
        return None
    p = Path(path)
    if not p.is_absolute():
        return path
    text = str(p)
    for prefix in ("/workspaces/mcp-geo/", "/workspace/mcp-geo/"):
        if text.startswith(prefix):
            return text[len(prefix) :]
    try:
        return str(p.relative_to(repo_root))
    except ValueError:
        return str(p)


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    rank = max(0.0, min(1.0, pct)) * (len(values) - 1)
    lower = int(rank)
    upper = min(lower + 1, len(values) - 1)
    if lower == upper:
        return values[lower]
    weight = rank - lower
    return values[lower] * (1.0 - weight) + values[upper] * weight


def latency_summary(observations: list[dict]) -> dict[str, float]:
    latencies: list[float] = []
    budget_checks = 0
    budget_passes = 0
    for row in observations:
        details = row.get("details", {})
        if not isinstance(details, dict):
            continue
        latency = details.get("latencyMs")
        if isinstance(latency, (int, float)):
            latencies.append(float(latency))
        budget = details.get("latencyBudgetMs")
        passed = details.get("latencyPass")
        if isinstance(budget, (int, float)) and isinstance(passed, bool):
            budget_checks += 1
            if passed:
                budget_passes += 1
    if not latencies:
        return {
            "samples": 0.0,
            "p50": 0.0,
            "p90": 0.0,
            "p95": 0.0,
            "max": 0.0,
            "budgetChecks": float(budget_checks),
            "budgetPasses": float(budget_passes),
            "budgetPassRate": 0.0,
        }
    ordered = sorted(latencies)
    pass_rate = (budget_passes / budget_checks) if budget_checks else 0.0
    return {
        "samples": float(len(ordered)),
        "p50": percentile(ordered, 0.50),
        "p90": percentile(ordered, 0.90),
        "p95": percentile(ordered, 0.95),
        "max": max(ordered),
        "budgetChecks": float(budget_checks),
        "budgetPasses": float(budget_passes),
        "budgetPassRate": pass_rate,
    }


def build_markdown(
    *,
    repo_root: Path,
    observations: list[dict],
    result_counts: dict[str, int],
    quality_report: dict[str, Any],
    generated_at: datetime,
) -> str:
    lines: list[str] = []
    lines.append("# Playwright Trial Summary")
    lines.append("")
    lines.append(f"- Generated at (UTC): {generated_at.isoformat().replace('+00:00', 'Z')}")
    if result_counts:
        lines.append(
            "- Result counts: "
            + ", ".join(f"`{key}={value}`" for key, value in result_counts.items())
        )
    lines.append(f"- Observation rows: `{len(observations)}`")
    latency = latency_summary(observations)
    if latency["samples"] > 0:
        lines.append(
            "- Latency summary (ms): "
            f"`p50={latency['p50']:.1f}`, `p90={latency['p90']:.1f}`, "
            f"`p95={latency['p95']:.1f}`, `max={latency['max']:.1f}`"
        )
    if latency["budgetChecks"] > 0:
        lines.append(
            "- Latency budget compliance: "
            f"`{int(latency['budgetPasses'])}/{int(latency['budgetChecks'])}` "
            f"({latency['budgetPassRate'] * 100:.1f}%)"
        )
    quality_counts = quality_report.get("statusCounts")
    if isinstance(quality_counts, dict) and quality_counts:
        lines.append(
            "- Quality status counts: "
            + ", ".join(f"`{key}={value}`" for key, value in sorted(quality_counts.items()))
        )
    lines.append("")

    quality_lookup: dict[tuple[str, str], str] = {}
    checks = quality_report.get("checks")
    if isinstance(checks, list):
        for row in checks:
            if not isinstance(row, dict):
                continue
            trial = row.get("trialId")
            browser = row.get("browser")
            status = row.get("status")
            if isinstance(trial, str) and isinstance(browser, str) and isinstance(status, str):
                quality_lookup[(trial, browser)] = status

    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in observations:
        grouped[row.get("trialId", "unknown")].append(row)

    for trial_id in sorted(grouped):
        lines.append(f"## {trial_id}")
        lines.append("")
        lines.append("| Browser | Status | Quality | Latency | Budget | Pass | Screenshot | Map panel |")
        lines.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
        for row in sorted(grouped[trial_id], key=lambda item: item.get("browser", "")):
            details = row.get("details", {})
            screenshot = to_rel(details.get("screenshot"), repo_root)
            map_panel = to_rel(details.get("mapPanel"), repo_root)
            screenshot_md = f"`{screenshot}`" if screenshot else "-"
            map_panel_md = f"`{map_panel}`" if map_panel else "-"
            latency_ms = details.get("latencyMs")
            budget_ms = details.get("latencyBudgetMs")
            latency_pass = details.get("latencyPass")
            quality_status = quality_lookup.get((trial_id, row.get("browser", "")), "-")
            latency_md = f"`{latency_ms:.1f}`" if isinstance(latency_ms, (int, float)) else "-"
            budget_md = f"`{budget_ms:.1f}`" if isinstance(budget_ms, (int, float)) else "-"
            pass_md = "yes" if latency_pass is True else ("no" if latency_pass is False else "-")
            lines.append(
                f"| {row.get('browser', '-')} | {row.get('status', '-')} | "
                f"{quality_status} | "
                f"{latency_md} | {budget_md} | {pass_md} | "
                f"{screenshot_md} | {map_panel_md} |"
            )
        lines.append("")

    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize map delivery Playwright trials.")
    parser.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parents[2]),
        help="Repository root path.",
    )
    parser.add_argument(
        "--observations",
        default="research/map_delivery_research_2026-02/evidence/logs/playwright_trials_observations.jsonl",
        help="Path to observation JSONL.",
    )
    parser.add_argument(
        "--results",
        default="research/map_delivery_research_2026-02/evidence/logs/playwright_trials_results.json",
        help="Path to Playwright JSON report.",
    )
    parser.add_argument(
        "--out",
        default="research/map_delivery_research_2026-02/reports/trial_summary.md",
        help="Output markdown path.",
    )
    parser.add_argument(
        "--quality",
        default="research/map_delivery_research_2026-02/reports/map_quality_report.json",
        help="Optional map quality report path.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    observations = load_observations((repo_root / args.observations).resolve())
    result_counts = load_result_stats((repo_root / args.results).resolve())
    quality_report = load_quality_report((repo_root / args.quality).resolve())
    content = build_markdown(
        repo_root=repo_root,
        observations=observations,
        result_counts=result_counts,
        quality_report=quality_report,
        generated_at=datetime.now(tz=UTC),
    )

    out_path = (repo_root / args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content, encoding="utf-8")
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
