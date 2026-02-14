#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path


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


def build_markdown(
    *,
    repo_root: Path,
    observations: list[dict],
    result_counts: dict[str, int],
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
    lines.append("")

    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in observations:
        grouped[row.get("trialId", "unknown")].append(row)

    for trial_id in sorted(grouped):
        lines.append(f"## {trial_id}")
        lines.append("")
        lines.append("| Browser | Status | Screenshot | Map panel |")
        lines.append("| --- | --- | --- | --- |")
        for row in sorted(grouped[trial_id], key=lambda item: item.get("browser", "")):
            details = row.get("details", {})
            screenshot = to_rel(details.get("screenshot"), repo_root)
            map_panel = to_rel(details.get("mapPanel"), repo_root)
            screenshot_md = f"`{screenshot}`" if screenshot else "-"
            map_panel_md = f"`{map_panel}`" if map_panel else "-"
            lines.append(
                f"| {row.get('browser', '-')} | {row.get('status', '-')} | "
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
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    observations = load_observations((repo_root / args.observations).resolve())
    result_counts = load_result_stats((repo_root / args.results).resolve())
    content = build_markdown(
        repo_root=repo_root,
        observations=observations,
        result_counts=result_counts,
        generated_at=datetime.now(tz=UTC),
    )

    out_path = (repo_root / args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content, encoding="utf-8")
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
