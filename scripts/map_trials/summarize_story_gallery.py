#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PREFERRED_BROWSERS = [
    "chromium-desktop",
    "firefox-desktop",
    "webkit-desktop",
    "chromium-mobile",
    "webkit-mobile",
]

TOOL_DESCRIPTIONS: dict[str, str] = {
    "os_maps.render": "Static map baseline render contract",
    "os_map.inventory": "Bounded map inventory layers (UPRNs/buildings/road/path)",
    "os_map.export": "Export lifecycle for map inventory snapshots",
    "os_vector_tiles.descriptor": "Vector style/tiles descriptor for rich map clients",
    "os_maps.wmts_capabilities": "WMTS capability discovery",
    "os_maps.raster_tile": "Raster tile retrieval",
    "admin_lookup.containing_areas": "Point-in-area administrative lookup",
    "admin_lookup.area_geometry": "Area geometry retrieval",
    "os_places.by_postcode": "Address/U PRN lookup by postcode",
    "os_places.radius": "Radius-based address search",
    "os_features.query": "Feature query by collection + bbox",
    "os_features.wfs_capabilities": "WFS capability discovery",
    "os_apps.render_geography_selector": "Interactive geography selector widget",
    "os_apps.render_boundary_explorer": "Interactive boundary explorer widget",
    "os_apps.render_route_planner": "Interactive route planner widget",
    "os_apps.render_feature_inspector": "Interactive feature inspector widget",
    "os_apps.render_statistics_dashboard": "Interactive statistics dashboard widget",
    "os_apps.render_ui_probe": "MCP-Apps UI capability probe",
}


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(value, dict):
        return value
    return {}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        if isinstance(row, dict):
            rows.append(row)
    return rows


def _parse_timestamp(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    normalized = value.strip().replace("Z", "+00:00")
    try:
        ts = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if ts.tzinfo is None:
        return ts.replace(tzinfo=UTC)
    return ts


def latest_by_trial_and_browser(
    rows: list[dict[str, Any]],
) -> dict[tuple[str, str], dict[str, Any]]:
    latest: dict[tuple[str, str], tuple[datetime | None, int, dict[str, Any]]] = {}
    for index, row in enumerate(rows):
        trial_id = str(row.get("trialId") or "")
        browser = str(row.get("browser") or "")
        key = (trial_id, browser)
        ts = _parse_timestamp(row.get("timestamp"))
        existing = latest.get(key)
        if existing is None:
            latest[key] = (ts, index, row)
            continue
        current_ts, current_index, _ = existing
        if ts and current_ts:
            if ts >= current_ts:
                latest[key] = (ts, index, row)
            continue
        if ts and not current_ts:
            latest[key] = (ts, index, row)
            continue
        if not ts and not current_ts and index >= current_index:
            latest[key] = (ts, index, row)
    return {k: v[2] for k, v in latest.items()}


def pick_observation_for_story(
    story_id: str,
    latest_rows: dict[tuple[str, str], dict[str, Any]],
) -> tuple[str | None, dict[str, Any] | None]:
    for browser in PREFERRED_BROWSERS:
        row = latest_rows.get((story_id, browser))
        if row is not None:
            return browser, row
    for (trial_id, browser), row in latest_rows.items():
        if trial_id == story_id:
            return browser, row
    return None, None


def to_relative(path_text: str | None, repo_root: Path) -> str | None:
    if not path_text:
        return None
    value = str(path_text)
    for prefix in ("/workspaces/mcp-geo/", "/workspace/mcp-geo/"):
        if value.startswith(prefix):
            value = value[len(prefix) :]
            break
    path = Path(value)
    if path.is_absolute():
        try:
            return str(path.relative_to(repo_root))
        except ValueError:
            return str(path)
    return str(path)


def build_tool_coverage(stories: list[dict[str, Any]]) -> dict[str, list[str]]:
    coverage: dict[str, list[str]] = defaultdict(list)
    for story in stories:
        story_id = str(story.get("id") or "")
        for tool in story.get("tools") or []:
            tool_name = str(tool)
            if story_id and tool_name:
                coverage[tool_name].append(story_id)
    for tool, story_ids in coverage.items():
        coverage[tool] = sorted(set(story_ids))
    return dict(sorted(coverage.items()))


def markdown_for_story(
    *,
    repo_root: Path,
    report_dir: Path,
    story: dict[str, Any],
    browser: str | None,
    row: dict[str, Any] | None,
) -> str:
    story_id = str(story.get("id") or "unknown-story")
    title = str(story.get("title") or story_id)
    persona = str(story.get("persona") or "")
    question = str(story.get("question") or "")
    decision = str(story.get("decision") or "")
    tools = [str(tool) for tool in (story.get("tools") or [])]
    talking_points = [str(point) for point in (story.get("talkingPoints") or [])]

    details = row.get("details") if isinstance(row, dict) else {}
    if not isinstance(details, dict):
        details = {}

    screenshot_path = to_relative(details.get("screenshot"), repo_root)
    map_panel_path = to_relative(details.get("mapPanel"), repo_root)
    screenshot_md = "_No screenshot captured yet._"
    if screenshot_path:
        rel = Path(screenshot_path)
        try:
            rel_to_report = rel.relative_to(Path("research/map_delivery_research_2026-02"))
            screenshot_md = f"![{title}](../{rel_to_report.as_posix()})"
        except ValueError:
            screenshot_md = f"`{screenshot_path}`"

    layer_counts = details.get("overlayFeatureCounts")
    layer_lines: list[str] = []
    if isinstance(layer_counts, list):
        for row_item in layer_counts:
            if not isinstance(row_item, dict):
                continue
            layer_id = str(row_item.get("id") or "unknown")
            kind = str(row_item.get("kind") or "unknown")
            count = row_item.get("count")
            source = str(row_item.get("source") or "unknown")
            layer_lines.append(f"- `{layer_id}` ({kind}, source={source}) -> `{count}` feature(s)")

    lines: list[str] = []
    lines.append(f"## {title}")
    lines.append("")
    lines.append(f"- Story ID: `{story_id}`")
    lines.append(f"- Persona: {persona}")
    lines.append(f"- Preferred evidence browser: `{browser or 'n/a'}`")
    lines.append(f"- Screenshot: `{screenshot_path or 'missing'}`")
    if map_panel_path:
        lines.append(f"- Map panel crop: `{map_panel_path}`")
    lines.append(f"- Question: {question}")
    lines.append(f"- Decision narrative: {decision}")
    lines.append("")
    lines.append("**Tool choreography**")
    lines.append("")
    for tool in tools:
        description = TOOL_DESCRIPTIONS.get(tool, "Map workflow tool")
        lines.append(f"- `{tool}`: {description}")
    lines.append("")
    lines.append("**Layered story notes**")
    lines.append("")
    for point in talking_points:
        lines.append(f"- {point}")
    if layer_lines:
        lines.append("")
        lines.append("**Observed layer counts from capture**")
        lines.append("")
        lines.extend(layer_lines)
    lines.append("")
    lines.append(screenshot_md)
    lines.append("")
    return "\n".join(lines)


def build_markdown(
    *,
    repo_root: Path,
    report_path: Path,
    scenarios: dict[str, Any],
    observations: list[dict[str, Any]],
) -> str:
    stories = scenarios.get("stories")
    if not isinstance(stories, list):
        stories = []
    version = str(scenarios.get("version") or "unknown")
    latest_rows = latest_by_trial_and_browser(observations)
    coverage = build_tool_coverage(stories)

    lines: list[str] = []
    lines.append("# Map Story Gallery Report")
    lines.append("")
    lines.append(f"- Generated at (UTC): {datetime.now(tz=UTC).isoformat().replace('+00:00', 'Z')}")
    lines.append(f"- Scenario catalog version: `{version}`")
    lines.append(f"- Scenario count: `{len(stories)}`")
    lines.append(f"- Observation rows loaded: `{len(observations)}`")
    lines.append("")

    lines.append("## Functionality Coverage Matrix")
    lines.append("")
    lines.append("| Tool | Capability | Stories |")
    lines.append("| --- | --- | --- |")
    for tool, story_ids in coverage.items():
        desc = TOOL_DESCRIPTIONS.get(tool, "Map workflow tool")
        stories_md = ", ".join(f"`{sid}`" for sid in story_ids)
        lines.append(f"| `{tool}` | {desc} | {stories_md} |")
    lines.append("")

    lines.append("## Slide Storyboards")
    lines.append("")
    report_dir = report_path.parent
    for story in stories:
        story_id = str(story.get("id") or "")
        browser, row = pick_observation_for_story(story_id, latest_rows)
        lines.append(
            markdown_for_story(
                repo_root=repo_root,
                report_dir=report_dir,
                story=story,
                browser=browser,
                row=row,
            )
        )

    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize map story gallery evidence for presentation use."
    )
    parser.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parents[2]),
        help="Repository root path.",
    )
    parser.add_argument(
        "--scenarios",
        default="playground/trials/fixtures/map_story_scenarios.json",
        help="Path to story scenario catalog JSON.",
    )
    parser.add_argument(
        "--observations",
        default="research/map_delivery_research_2026-02/evidence/logs/playwright_trials_observations.jsonl",
        help="Path to observation JSONL.",
    )
    parser.add_argument(
        "--out",
        default="research/map_delivery_research_2026-02/reports/story_gallery_report.md",
        help="Output markdown path.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    scenarios_path = (repo_root / args.scenarios).resolve()
    observations_path = (repo_root / args.observations).resolve()
    out_path = (repo_root / args.out).resolve()

    scenarios = load_json(scenarios_path)
    observations = load_jsonl(observations_path)

    content = build_markdown(
        repo_root=repo_root,
        report_path=out_path,
        scenarios=scenarios,
        observations=observations,
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content, encoding="utf-8")
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
