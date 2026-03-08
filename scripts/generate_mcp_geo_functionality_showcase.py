#!/usr/bin/env python3
"""Generate a repeatable showcase report for MCP-Geo evaluation examples."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import textwrap
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont, ImageOps

REPO_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = REPO_ROOT / "docs" / "reports"
REPORT_ASSETS_DIR = REPORTS_DIR / "assets"
DEFAULT_INPUT = REPO_ROOT / "data" / "report_inputs" / "mcp_geo_functionality_showcase_examples.json"
DEFAULT_REPO_URL = "https://github.com/chris-page-gov/mcp-geo.git"

PAPER_BG = "#f4efe6"
CARD_BG = "#fbf8f2"
INK = "#112430"
MUTED = "#50636f"
GRID = "#d5cdc0"
TEAL = "#0f8b8d"
AMBER = "#d7921f"
RED = "#d45a43"
SAND = "#d9cfbe"
SLATE = "#6f7f89"


@dataclass(frozen=True)
class PeninsulaCounts:
    buildings: int
    building_parts: int
    road_links: int
    path_links: int


@dataclass(frozen=True)
class WheelchairTownMetrics:
    name: str
    road_links: int
    path_links: int
    pavements: int
    preferred_km: float
    care_km: float
    barrier_km: float
    anchor_gap_1: str
    anchor_gap_2: str


def strip_git_suffix(repo_url: str) -> str:
    if repo_url.endswith(".git"):
        return repo_url[:-4]
    return repo_url


def build_github_blob_url(repo_url: str, git_ref: str, path: Path) -> str:
    return f"{strip_git_suffix(repo_url)}/blob/{git_ref}/{path.as_posix()}"


def parse_pipe_rows(markdown_text: str) -> dict[str, list[str]]:
    rows: dict[str, list[str]] = {}
    for raw_line in markdown_text.splitlines():
        line = raw_line.strip()
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 2:
            continue
        if set("".join(cells)) <= {"-", ":", " "}:
            continue
        rows[cells[0]] = cells[1:]
    return rows


def _clean_numeric(raw_value: str) -> str:
    return raw_value.replace("`", "").replace(",", "").replace(" km", "").strip()


def parse_peninsula_counts(markdown_text: str) -> PeninsulaCounts:
    rows = parse_pipe_rows(markdown_text)
    return PeninsulaCounts(
        buildings=int(_clean_numeric(rows["Buildings"][1])),
        building_parts=int(_clean_numeric(rows["Building parts"][1])),
        road_links=int(_clean_numeric(rows["Road links"][1])),
        path_links=int(_clean_numeric(rows["Path links"][1])),
    )


def parse_wheelchair_comparison(markdown_text: str) -> list[WheelchairTownMetrics]:
    rows = parse_pipe_rows(markdown_text)
    towns = ("Teignmouth", "Exmouth", "Sidmouth")
    metrics: list[WheelchairTownMetrics] = []
    for index, town in enumerate(towns):
        metrics.append(
            WheelchairTownMetrics(
                name=town,
                road_links=int(_clean_numeric(rows["Road links"][index])),
                path_links=int(_clean_numeric(rows["Path links"][index])),
                pavements=int(_clean_numeric(rows["Pavement polygons"][index])),
                preferred_km=float(_clean_numeric(rows["Preferred route length"][index])),
                care_km=float(_clean_numeric(rows["Use-with-care route length"][index])),
                barrier_km=float(_clean_numeric(rows["Barrier length"][index])),
                anchor_gap_1=rows["Anchor gap 1"][index].replace("`", ""),
                anchor_gap_2=rows["Anchor gap 2"][index].replace("`", ""),
            )
        )
    return metrics


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates: list[str] = []
    if bold:
        candidates.extend(
            [
                "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
                "/Library/Fonts/Arial Bold.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            ]
        )
    else:
        candidates.extend(
            [
                "/System/Library/Fonts/Supplemental/Arial.ttf",
                "/Library/Fonts/Arial.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            ]
        )
    for candidate in candidates:
        font_path = Path(candidate)
        if font_path.exists():
            return ImageFont.truetype(str(font_path), size=size)
    return ImageFont.load_default()


def _text_bbox(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    return right - left, bottom - top


def _wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    max_width: int,
) -> list[str]:
    words = text.split()
    if not words:
        return [""]
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if _text_bbox(draw, candidate, font)[0] <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def _draw_wrapped_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    *,
    xy: tuple[int, int],
    font: ImageFont.ImageFont,
    fill: str,
    max_width: int,
    line_gap: int = 6,
) -> int:
    x, y = xy
    for line in _wrap_text(draw, text, font, max_width):
        draw.text((x, y), line, font=font, fill=fill)
        _, height = _text_bbox(draw, line, font)
        y += height + line_gap
    return y


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def generate_peninsula_counts_chart(output_path: Path, counts: PeninsulaCounts) -> None:
    _ensure_parent(output_path)
    width = 1600
    height = 900
    image = Image.new("RGB", (width, height), PAPER_BG)
    draw = ImageDraw.Draw(image)
    title_font = _load_font(54, bold=True)
    subtitle_font = _load_font(24)
    label_font = _load_font(28, bold=True)
    value_font = _load_font(24, bold=True)
    small_font = _load_font(22)

    draw.rounded_rectangle((42, 42, width - 42, height - 42), radius=28, fill=CARD_BG, outline=GRID)
    draw.text((86, 82), "Teignmouth peninsula profiling counts", font=title_font, fill=INK)
    draw.text(
        (86, 154),
        "Exact south-of-railway extract counts used for the building-profile brief.",
        font=subtitle_font,
        fill=MUTED,
    )

    chart_left = 116
    chart_top = 274
    chart_right = width - 116
    chart_bottom = 720
    draw.line((chart_left, chart_bottom, chart_right, chart_bottom), fill=SLATE, width=3)
    draw.line((chart_left, chart_top, chart_left, chart_bottom), fill=SLATE, width=3)

    bars = [
        ("Buildings", counts.buildings, TEAL),
        ("Building parts", counts.building_parts, AMBER),
        ("Road links", counts.road_links, SLATE),
        ("Path links", counts.path_links, RED),
    ]
    max_value = max(value for _, value, _ in bars)
    bar_width = 200
    gap = 96
    start_x = chart_left + 90
    usable_height = chart_bottom - chart_top - 20

    for index, (label, value, color) in enumerate(bars):
        x0 = start_x + index * (bar_width + gap)
        x1 = x0 + bar_width
        bar_height = int((value / max_value) * usable_height)
        y0 = chart_bottom - bar_height
        draw.rounded_rectangle((x0, y0, x1, chart_bottom - 1), radius=18, fill=color)
        value_text = f"{value}"
        value_width, value_height = _text_bbox(draw, value_text, value_font)
        draw.text((x0 + (bar_width - value_width) / 2, y0 - value_height - 18), value_text, font=value_font, fill=INK)
        label_lines = _wrap_text(draw, label, small_font, bar_width + 30)
        label_y = chart_bottom + 24
        for line in label_lines:
            line_width, line_height = _text_bbox(draw, line, small_font)
            draw.text((x0 + (bar_width - line_width) / 2, label_y), line, font=small_font, fill=INK)
            label_y += line_height + 2

    callout_x0 = 1080
    callout_y0 = 262
    draw.rounded_rectangle((callout_x0, callout_y0, width - 96, 494), radius=24, fill="#f0efe7", outline=GRID)
    draw.text((callout_x0 + 24, callout_y0 + 24), "Reading the peninsula", font=label_font, fill=INK)
    y_cursor = callout_y0 + 84
    y_cursor = _draw_wrapped_text(
        draw,
        "Building parts outnumber whole buildings by 172, which is enough to justify part-level skyline and use graphics.",
        xy=(callout_x0 + 24, y_cursor),
        font=small_font,
        fill=MUTED,
        max_width=370,
    )
    y_cursor += 14
    _draw_wrapped_text(
        draw,
        "Road and path links together describe both the carriageway structure and the pedestrian permeability of the peninsula.",
        xy=(callout_x0 + 24, y_cursor),
        font=small_font,
        fill=MUTED,
        max_width=370,
    )

    footer_text = "Source: docs/reports/teignmouth_peninsula_building_profile_brief_2026-03-06.md"
    draw.text((86, 792), footer_text, font=small_font, fill=MUTED)

    image.save(output_path)


def generate_wheelchair_comparison_chart(
    output_path: Path,
    metrics: list[WheelchairTownMetrics],
) -> None:
    _ensure_parent(output_path)
    width = 1800
    height = 980
    image = Image.new("RGB", (width, height), PAPER_BG)
    draw = ImageDraw.Draw(image)
    title_font = _load_font(58, bold=True)
    subtitle_font = _load_font(24)
    heading_font = _load_font(28, bold=True)
    label_font = _load_font(22)
    value_font = _load_font(24, bold=True)

    draw.rounded_rectangle((40, 40, width - 40, height - 40), radius=30, fill=CARD_BG, outline=GRID)
    draw.text((88, 82), "Wheelchair route comparison", font=title_font, fill=INK)
    draw.text(
        (88, 156),
        "Live 2026-03-07 extracts under the same conservative MCP-Geo route filter.",
        font=subtitle_font,
        fill=MUTED,
    )

    colors = {
        "Preferred route": TEAL,
        "Use with care": AMBER,
        "Barrier in data": RED,
    }
    max_value = max(max(item.preferred_km, item.care_km, item.barrier_km) for item in metrics)
    card_width = 520
    card_height = 650
    gap = 36
    start_x = 88
    start_y = 236

    for index, town in enumerate(metrics):
        x0 = start_x + index * (card_width + gap)
        y0 = start_y
        x1 = x0 + card_width
        y1 = y0 + card_height
        draw.rounded_rectangle((x0, y0, x1, y1), radius=26, fill="#f8f4ed", outline=GRID)
        draw.text((x0 + 28, y0 + 24), town.name, font=heading_font, fill=INK)
        draw.text(
            (x0 + 28, y0 + 66),
            f"{town.road_links} road links, {town.path_links} path links, {town.pavements} pavements",
            font=label_font,
            fill=MUTED,
        )
        bar_specs = [
            ("Preferred route", town.preferred_km),
            ("Use with care", town.care_km),
            ("Barrier in data", town.barrier_km),
        ]
        bar_y = y0 + 140
        for label, value in bar_specs:
            draw.text((x0 + 28, bar_y - 34), label, font=label_font, fill=INK)
            track_x0 = x0 + 28
            track_x1 = x1 - 28
            draw.rounded_rectangle((track_x0, bar_y, track_x1, bar_y + 32), radius=16, fill="#ebe5d9")
            bar_length = int((value / max_value) * (track_x1 - track_x0))
            draw.rounded_rectangle(
                (track_x0, bar_y, track_x0 + max(bar_length, 12), bar_y + 32),
                radius=16,
                fill=colors[label],
            )
            value_text = f"{value:.2f} km"
            value_width, _ = _text_bbox(draw, value_text, value_font)
            draw.text((track_x1 - value_width, bar_y - 38), value_text, font=value_font, fill=INK)
            bar_y += 110

        draw.text((x0 + 28, y0 + 490), "Anchor gaps", font=heading_font, fill=INK)
        y_cursor = y0 + 540
        y_cursor = _draw_wrapped_text(
            draw,
            town.anchor_gap_1,
            xy=(x0 + 28, y_cursor),
            font=label_font,
            fill=MUTED,
            max_width=card_width - 56,
        )
        _draw_wrapped_text(
            draw,
            town.anchor_gap_2,
            xy=(x0 + 28, y_cursor + 6),
            font=label_font,
            fill=MUTED,
            max_width=card_width - 56,
        )

    footer_text = "Source: docs/reports/teignmouth_exmouth_sidmouth_access_comparison_2026-03-07.md"
    draw.text((88, 904), footer_text, font=label_font, fill=MUTED)

    image.save(output_path)


def generate_map_triptych(output_path: Path, panels: list[tuple[str, Path]]) -> None:
    _ensure_parent(output_path)
    width = 1860
    height = 1080
    image = Image.new("RGB", (width, height), PAPER_BG)
    draw = ImageDraw.Draw(image)
    title_font = _load_font(56, bold=True)
    subtitle_font = _load_font(24)
    label_font = _load_font(26, bold=True)

    draw.rounded_rectangle((38, 38, width - 38, height - 38), radius=30, fill=CARD_BG, outline=GRID)
    draw.text((84, 80), "Wheelchair access maps", font=title_font, fill=INK)
    draw.text(
        (84, 154),
        "Tracked PNG artefacts generated from the MCP-Geo route filter for Teignmouth, Exmouth, and Sidmouth.",
        font=subtitle_font,
        fill=MUTED,
    )

    panel_width = 540
    panel_height = 770
    gap = 36
    start_x = 84
    start_y = 234

    for index, (label, path) in enumerate(panels):
        panel_x0 = start_x + index * (panel_width + gap)
        panel_y0 = start_y
        panel_x1 = panel_x0 + panel_width
        panel_y1 = panel_y0 + panel_height
        draw.rounded_rectangle((panel_x0, panel_y0, panel_x1, panel_y1), radius=24, fill="#f8f4ed", outline=GRID)
        draw.text((panel_x0 + 24, panel_y0 + 20), label, font=label_font, fill=INK)
        source = Image.open(path).convert("RGB")
        fitted = ImageOps.contain(source, (panel_width - 28, panel_height - 90))
        image.paste(fitted, (panel_x0 + (panel_width - fitted.width) // 2, panel_y0 + 64))

    footer = "HTML counterparts are linked from the report body."
    draw.text((84, 1000), footer, font=subtitle_font, fill=MUTED)
    image.save(output_path)


def _relative_path(from_dir: Path, target: Path) -> str:
    return os.path.relpath(target, from_dir).replace(os.sep, "/")


def _render_pandoc(input_path: Path, output_path: Path, command: list[str]) -> None:
    subprocess.run(command, cwd=str(input_path.parent), check=True)


def _write_report_markdown(
    *,
    manifest: dict[str, Any],
    report_path: Path,
    repo_url: str,
    git_ref: str,
    report_date: str,
    peninsula_counts: PeninsulaCounts,
    wheelchair_metrics: list[WheelchairTownMetrics],
    peninsula_chart_path: Path,
    wheelchair_chart_path: Path,
    wheelchair_triptych_path: Path,
) -> None:
    report_dir = report_path.parent
    manifest_rel = Path("data/report_inputs/mcp_geo_functionality_showcase_examples.json")
    generator_rel = Path("scripts/generate_mcp_geo_functionality_showcase.py")
    source_urls = {
        "manifest": build_github_blob_url(repo_url, git_ref, manifest_rel),
        "generator": build_github_blob_url(repo_url, git_ref, generator_rel),
        "readme": build_github_blob_url(repo_url, git_ref, Path("README.md")),
        "tool_registry": build_github_blob_url(repo_url, git_ref, Path("server/mcp/tools.py")),
        "wheelchair_generator": build_github_blob_url(
            repo_url,
            git_ref,
            Path("scripts/generate_teignmouth_wheelchair_access_map.py"),
        ),
    }

    cases = {case["id"]: case for case in manifest["cases"]}
    stanley = cases["stanley_house"]
    peninsula = cases["peninsula_profile"]
    wheelchair = cases["wheelchair_routes"]

    stanley_png = REPO_ROOT / "output" / "playwright" / "stanley-house-os-light-wider-panel.png"
    stanley_rel = _relative_path(report_dir, stanley_png)
    peninsula_chart_rel = _relative_path(report_dir, peninsula_chart_path)
    wheelchair_chart_rel = _relative_path(report_dir, wheelchair_chart_path)
    wheelchair_triptych_rel = _relative_path(report_dir, wheelchair_triptych_path)

    town_map_lines: list[str] = []
    for artifact in wheelchair["artifacts"]:
        png_url = build_github_blob_url(repo_url, git_ref, Path(artifact["path"]))
        if artifact.get("html_path"):
            html_url = build_github_blob_url(repo_url, git_ref, Path(artifact["html_path"]))
            town_map_lines.append(
                f"- {artifact['label']}: [PNG artefact]({png_url}) and [HTML map]({html_url})"
            )
        else:
            town_map_lines.append(f"- {artifact['label']}: [artefact]({png_url})")

    stanley_sources = ", ".join(
        f"[{source['label']}]({build_github_blob_url(repo_url, git_ref, Path(source['path']))})"
        for source in stanley["sources"]
    )
    peninsula_sources = ", ".join(
        f"[{source['label']}]({build_github_blob_url(repo_url, git_ref, Path(source['path']))})"
        for source in peninsula["sources"]
    )
    wheelchair_sources = ", ".join(
        f"[{source['label']}]({build_github_blob_url(repo_url, git_ref, Path(source['path']))})"
        for source in wheelchair["sources"]
    )

    wheelchair_summary_lines = [
        f"- `{item.name}`: preferred `{item.preferred_km:.2f} km`, use with care `{item.care_km:.2f} km`, barrier `{item.barrier_km:.2f} km`; {item.anchor_gap_1}; {item.anchor_gap_2}."
        for item in wheelchair_metrics
    ]
    stanley_highlights = "\n".join(f"- {point}" for point in stanley["highlights"])
    peninsula_highlights = "\n".join(f"- {point}" for point in peninsula["highlights"])
    wheelchair_highlights = "\n".join(f"- {point}" for point in wheelchair["highlights"])
    wheelchair_summary_block = "\n".join(wheelchair_summary_lines)
    town_map_block = "\n".join(town_map_lines)

    markdown = textwrap.dedent(
        f"""\
        ---
        title: "{manifest['title']}"
        subtitle: "{manifest['subtitle']}"
        date: "{report_date}"
        toc: true
        geometry: margin=0.85in
        colorlinks: true
        urlcolor: blue
        papersize: a4
        ---

        # Overview

        This report packages a small set of real MCP-Geo questions asked from Codex into a reusable evaluation document for people deciding whether MCP-Geo is useful in practice.
        It focuses on three patterns that matter to evaluators:

        - starting from a simple address-level question and expanding into surrounding context
        - defining and profiling a custom area of interest rather than only answering lookups
        - producing decision-support maps that are explicit about both the evidence and the current limits

        The report is generated from a curated input manifest, existing repo notes, and tracked illustration artefacts.
        The public source of truth for this run is the repo on `{git_ref}`:
        [input manifest]({source_urls['manifest']}), [generator script]({source_urls['generator']}), [README]({source_urls['readme']}), and [tool registration module]({source_urls['tool_registry']}).

        # What MCP-Geo Is Demonstrating

        These examples show MCP-Geo being used for more than raw API passthrough.
        Across the three cases, the workflow repeatedly combines:

        - identifier and address resolution
        - OS road, path, pavement, and building layers
        - user-framed study areas rather than fixed administrative cuts
        - presentation outputs that can be read as markdown, static figures, or interactive HTML

        The underlying product surface is visible in the public repository:
        the top-level [README]({source_urls['readme']}) describes the server and its tool families, while [server/mcp/tools.py]({source_urls['tool_registry']}) shows the registered tool modules that make those workflows possible.

        # Example 1: From a Random Postcode to Dual-Road Building Context

        **Question asked**

        `{stanley['question']}`

        **Follow-up**

        `{stanley['follow_up']}`

        {stanley['why_it_matters']}

        {stanley_highlights}

        ![Clampet Lane and Orchard Gardens context panel]({stanley_rel}){{ width=92% }}

        This example is useful because it shows an evaluator what "good enough for urban context" looks like in MCP-Geo.
        The original query starts at postcode level, but the answer moves into road width, building-part height, frontage grouping, and OS-backed map output without leaving the same workflow.

        Related artefacts:

        - [Stanley House on OS MasterMap context]({build_github_blob_url(repo_url, git_ref, Path('output/playwright/stanley-house-os-mastermap-context.png'))})
        - [Stanley House focused OS Light view]({build_github_blob_url(repo_url, git_ref, Path('output/playwright/stanley-house-os-light-focused.png'))})
        - [Clampet Lane and Orchard Gardens wider context panel]({build_github_blob_url(repo_url, git_ref, Path('output/playwright/stanley-house-os-light-wider-panel.png'))})

        Online sources: {stanley_sources}

        # Example 2: From a Town-Centre Question to a Repeatable Profiling Brief

        **Question asked**

        `{peninsula['question']}`

        **Follow-up**

        `{peninsula['follow_up']}`

        {peninsula['why_it_matters']}

        {peninsula_highlights}

        ![Teignmouth peninsula profile counts]({peninsula_chart_rel}){{ width=88% }}

        The key shift here is from "tell me about this place" to "define an operational area of interest and specify the analytics pack".
        That makes this example especially useful for evaluators who want to know whether MCP-Geo can support briefs, profiling exercises, and future infographic or dashboard work.

        The peninsula brief records the exact live counts used in the chart above:

        - buildings: `{peninsula_counts.buildings}`
        - building parts: `{peninsula_counts.building_parts}`
        - road links: `{peninsula_counts.road_links}`
        - path links: `{peninsula_counts.path_links}`

        Online sources: {peninsula_sources}

        # Example 3: From a Wheelchair Routing Question to Comparative Town Maps

        **Question asked**

        `{wheelchair['question']}`

        **Follow-up**

        `{wheelchair['follow_up']}`

        {wheelchair['why_it_matters']}

        {wheelchair_highlights}

        ![Wheelchair route comparison chart]({wheelchair_chart_rel}){{ width=94% }}

        ![Teignmouth, Exmouth and Sidmouth wheelchair map triptych]({wheelchair_triptych_rel}){{ width=96% }}

        The comparative work is especially useful for evaluation because it does not stop at a single map.
        It applies one conservative route filter across three coastal towns and then makes the strengths and limits explicit.

        {wheelchair_summary_block}

        Interactive and static artefacts:

        {town_map_block}

        Implementation note:
        the underlying map-production workflow is public in [scripts/generate_teignmouth_wheelchair_access_map.py]({source_urls['wheelchair_generator']}).

        Online sources: {wheelchair_sources}

        # What These Examples Show About Utility

        Taken together, the three cases suggest that MCP-Geo is most useful when the user is trying to move through three layers of work:

        1. resolve a place, address, or route question into stable identifiers and geometry
        2. combine several related spatial layers into an interpretable answer
        3. turn that answer into a re-usable artefact such as a note, map, or briefing graphic

        The Stanley House case shows address-to-context movement.
        The peninsula case shows profiling and briefing.
        The wheelchair work shows public-realm interpretation, comparative mapping, and honest treatment of product limits.

        # Current Limits and Future Value

        The wheelchair case is the clearest reminder that good geospatial answers are not the same thing as a final audit.
        The current evidence stack is strong on road width, path type, pavement coverage, lighting, and gradient proxies, but it is weaker where access depends on dropped kerbs, crossing detail, temporary obstructions, and other on-the-ground conditions.

        For evaluators, that is a strength rather than a weakness if it is stated clearly:
        MCP-Geo works well as a hypothesis engine, a profiling tool, and a map/report generator.
        It is not yet a replacement for doorway-level access surveys or formal public-realm audits.

        # Repeatability

        This report is designed to be rerun.
        The content is driven by [the manifest]({source_urls['manifest']}) and generated by [the script]({source_urls['generator']}).
        By default the report links to the public `main` branch for web readability, but the generator accepts `--git-ref` so a future run can pin every citation to a release tag or commit.

        Regeneration command:

        ```bash
        ./.venv/bin/python scripts/generate_mcp_geo_functionality_showcase.py --git-ref main
        ```

        Outputs written by the generator:

        - `docs/reports/mcp_geo_functionality_showcase_{report_date}.md`
        - `docs/reports/mcp_geo_functionality_showcase_{report_date}.docx`
        - `docs/reports/mcp_geo_functionality_showcase_{report_date}.pdf`

        # Repository Sources Used

        - [README.md]({source_urls['readme']})
        - [server/mcp/tools.py]({source_urls['tool_registry']})
        - [{stanley['sources'][0]['label']}]({build_github_blob_url(repo_url, git_ref, Path(stanley['sources'][0]['path']))})
        - [{peninsula['sources'][0]['label']}]({build_github_blob_url(repo_url, git_ref, Path(peninsula['sources'][0]['path']))})
        - [{wheelchair['sources'][0]['label']}]({build_github_blob_url(repo_url, git_ref, Path(wheelchair['sources'][0]['path']))})
        - [{wheelchair['sources'][1]['label']}]({build_github_blob_url(repo_url, git_ref, Path(wheelchair['sources'][1]['path']))})
        - [{wheelchair['sources'][2]['label']}]({build_github_blob_url(repo_url, git_ref, Path(wheelchair['sources'][2]['path']))})
        - [{wheelchair['sources'][3]['label']}]({build_github_blob_url(repo_url, git_ref, Path(wheelchair['sources'][3]['path']))})
        """
    )
    markdown = markdown.replace("\n        ", "\n").lstrip().rstrip() + "\n"
    report_path.write_text(markdown, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Path to report input manifest.")
    parser.add_argument("--repo-url", default=DEFAULT_REPO_URL, help="Public repository URL.")
    parser.add_argument(
        "--git-ref",
        default="main",
        help="Git ref used for public citation links. Default: %(default)s.",
    )
    parser.add_argument(
        "--date",
        default=date.today().isoformat(),
        help="Date suffix used in generated filenames. Default: today's date.",
    )
    parser.add_argument(
        "--skip-docx",
        action="store_true",
        help="Generate markdown only, skipping DOCX conversion.",
    )
    parser.add_argument(
        "--skip-pdf",
        action="store_true",
        help="Generate markdown only, skipping PDF conversion.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    manifest = _load_json(args.input)

    peninsula_note = REPORTS_DIR / "teignmouth_peninsula_building_profile_brief_2026-03-06.md"
    wheelchair_note = REPORTS_DIR / "teignmouth_exmouth_sidmouth_access_comparison_2026-03-07.md"

    peninsula_counts = parse_peninsula_counts(peninsula_note.read_text(encoding="utf-8"))
    wheelchair_metrics = parse_wheelchair_comparison(wheelchair_note.read_text(encoding="utf-8"))

    report_stem = f"mcp_geo_functionality_showcase_{args.date}"
    report_path = REPORTS_DIR / f"{report_stem}.md"
    docx_path = REPORTS_DIR / f"{report_stem}.docx"
    pdf_path = REPORTS_DIR / f"{report_stem}.pdf"
    peninsula_chart_path = REPORT_ASSETS_DIR / f"teignmouth_peninsula_profile_counts_{args.date}.png"
    wheelchair_chart_path = REPORT_ASSETS_DIR / f"wheelchair_route_comparison_{args.date}.png"
    wheelchair_triptych_path = REPORT_ASSETS_DIR / f"wheelchair_access_maps_triptych_{args.date}.png"

    generate_peninsula_counts_chart(peninsula_chart_path, peninsula_counts)
    generate_wheelchair_comparison_chart(wheelchair_chart_path, wheelchair_metrics)
    generate_map_triptych(
        wheelchair_triptych_path,
        [
            ("Teignmouth", REPO_ROOT / "output" / "playwright" / "teignmouth-wheelchair-access-map-2026-03-07.png"),
            ("Exmouth", REPO_ROOT / "output" / "playwright" / "exmouth-wheelchair-access-map-2026-03-07.png"),
            ("Sidmouth", REPO_ROOT / "output" / "playwright" / "sidmouth-wheelchair-access-map-2026-03-07.png"),
        ],
    )

    _write_report_markdown(
        manifest=manifest,
        report_path=report_path,
        repo_url=args.repo_url,
        git_ref=args.git_ref,
        report_date=args.date,
        peninsula_counts=peninsula_counts,
        wheelchair_metrics=wheelchair_metrics,
        peninsula_chart_path=peninsula_chart_path,
        wheelchair_chart_path=wheelchair_chart_path,
        wheelchair_triptych_path=wheelchair_triptych_path,
    )

    if not args.skip_docx:
        _render_pandoc(
            report_path,
            docx_path,
            [
                "pandoc",
                report_path.name,
                "-o",
                docx_path.name,
                "--from=markdown+link_attributes",
            ],
        )

    if not args.skip_pdf:
        _render_pandoc(
            report_path,
            pdf_path,
            [
                "pandoc",
                report_path.name,
                "-o",
                pdf_path.name,
                "--from=markdown+link_attributes",
                "--pdf-engine=xelatex",
                "-V",
                "geometry:margin=0.85in",
                "-V",
                "papersize:a4",
                "-V",
                "colorlinks=true",
                "-V",
                "urlcolor=blue",
            ],
        )

    print(report_path)
    if not args.skip_docx:
        print(docx_path)
    if not args.skip_pdf:
        print(pdf_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
