#!/usr/bin/env python3
"""Validate and export the MCP-Geo analytical index package."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import textwrap
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = REPO_ROOT / "data" / "report_inputs" / "mcp_geo_analytical_index_manifest.json"

PAPER_BG = "#f4efe6"
CARD_BG = "#fbf8f2"
INK = "#112430"
MUTED = "#50636f"
GRID = "#d5cdc0"
TEAL = "#0f8b8d"
AMBER = "#d7921f"
RED = "#d45a43"
SLATE = "#6f7f89"
MOSS = "#6f8a3a"


@dataclass(frozen=True)
class FigureSpec:
    id: str
    title: str
    filename: str
    placement_heading: str
    purpose: str
    source_basis: list[str]
    aspect_ratio: str
    alt_text: str
    prompt: str


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True).strip()


def _load_font(size: int, *, bold: bool = False) -> ImageFont.ImageFont:
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
    *,
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
    x: int,
    y: int,
    font: ImageFont.ImageFont,
    fill: str,
    max_width: int,
    line_gap: int = 4,
) -> int:
    current_y = y
    for line in _wrap_text(draw, text, font=font, max_width=max_width):
        draw.text((x, current_y), line, font=font, fill=fill)
        _, height = _text_bbox(draw, line, font)
        current_y += height + line_gap
    return current_y


def _draw_card(
    draw: ImageDraw.ImageDraw,
    *,
    box: tuple[int, int, int, int],
    title: str,
    body: str,
    accent: str,
) -> None:
    x0, y0, x1, y1 = box
    title_font = _load_font(26, bold=True)
    body_font = _load_font(20)
    draw.rounded_rectangle(box, radius=22, fill=CARD_BG, outline=GRID, width=2)
    draw.rounded_rectangle((x0, y0, x0 + 16, y1), radius=22, fill=accent, outline=accent)
    draw.text((x0 + 32, y0 + 24), title, font=title_font, fill=INK)
    _draw_wrapped_text(
        draw,
        body,
        x=x0 + 32,
        y=y0 + 70,
        font=body_font,
        fill=MUTED,
        max_width=(x1 - x0) - 56,
        line_gap=6,
    )


def _draw_arrow(
    draw: ImageDraw.ImageDraw,
    start: tuple[int, int],
    end: tuple[int, int],
    *,
    fill: str = SLATE,
    width: int = 6,
) -> None:
    x0, y0 = start
    x1, y1 = end
    draw.line((x0, y0, x1, y1), fill=fill, width=width)
    if x0 == x1 and y0 == y1:
        return
    head = 16
    if abs(x1 - x0) >= abs(y1 - y0):
        direction = 1 if x1 > x0 else -1
        draw.polygon(
            [
                (x1, y1),
                (x1 - direction * head, y1 - head // 2),
                (x1 - direction * head, y1 + head // 2),
            ],
            fill=fill,
        )
    else:
        direction = 1 if y1 > y0 else -1
        draw.polygon(
            [
                (x1, y1),
                (x1 - head // 2, y1 - direction * head),
                (x1 + head // 2, y1 - direction * head),
            ],
            fill=fill,
        )


def _render_canvas(title: str, subtitle: str) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (1600, 900), PAPER_BG)
    draw = ImageDraw.Draw(image)
    title_font = _load_font(50, bold=True)
    subtitle_font = _load_font(24)
    draw.rounded_rectangle((38, 38, 1562, 862), radius=28, fill=CARD_BG, outline=GRID)
    draw.text((80, 78), title, font=title_font, fill=INK)
    _draw_wrapped_text(draw, subtitle, x=80, y=146, font=subtitle_font, fill=MUTED, max_width=1440)
    return image, draw


def _parse_figures(manifest: dict[str, Any]) -> list[FigureSpec]:
    return [
        FigureSpec(
            id=item["id"],
            title=item["title"],
            filename=item["filename"],
            placement_heading=item["placement_heading"],
            purpose=item["purpose"],
            source_basis=item["source_basis"],
            aspect_ratio=item["aspect_ratio"],
            alt_text=item["alt_text"],
            prompt=item["prompt"],
        )
        for item in manifest["figures"]
    ]


def _top_level_entry_counts(git_ref: str) -> Counter[str]:
    entries = _git("ls-tree", "-r", "--name-only", git_ref).splitlines()
    counter: Counter[str] = Counter()
    for entry in entries:
        top = entry.split("/", 1)[0]
        counter[top] += 1
    return counter


def _tool_prefix_counts(git_ref: str) -> Counter[str]:
    content = _git("show", f"{git_ref}:docs/tool_catalog.md")
    counter: Counter[str] = Counter()
    for line in content.splitlines():
        if not line.startswith("| ") or line.startswith("| Tool "):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 3 or "." not in cells[0]:
            continue
        prefix = cells[0].split(".", 1)[0]
        counter[prefix] += 1
    return counter


def _generate_repo_at_a_glance(output_path: Path, counts: Counter[str]) -> None:
    image, draw = _render_canvas(
        "Repository at a glance",
        "Pinned commit structure grouped into the zones a reader is most likely to open first.",
    )
    title_font = _load_font(22, bold=True)
    body_font = _load_font(18)
    chart_left = 120
    chart_bottom = 760
    bar_width = 110
    gap = 52
    keys = ["docs", "tests", "research", "scripts", "server", "tools", "playground", "resources"]
    colors = [TEAL, AMBER, RED, SLATE, MOSS, "#5087a1", "#9d6b53", "#7c6bb0"]
    max_value = max(counts.get(key, 1) for key in keys)
    for index, key in enumerate(keys):
        value = counts.get(key, 0)
        x0 = chart_left + index * (bar_width + gap)
        x1 = x0 + bar_width
        height = int((value / max_value) * 360)
        y0 = chart_bottom - height
        draw.rounded_rectangle((x0, y0, x1, chart_bottom), radius=16, fill=colors[index], outline=colors[index])
        label = key
        draw.text((x0, chart_bottom + 18), label, font=body_font, fill=INK)
        value_text = str(value)
        width, _ = _text_bbox(draw, value_text, title_font)
        draw.text((x0 + (bar_width - width) // 2, y0 - 36), value_text, font=title_font, fill=INK)
    _draw_card(
        draw,
        box=(1080, 250, 1490, 438),
        title="Launch files",
        body="README.md, Dockerfile, .env.example, mcp.json, tutorial.md, and root controls frame startup.",
        accent=TEAL,
    )
    _draw_card(
        draw,
        box=(1080, 466, 1490, 654),
        title="Evidence-heavy surface",
        body="docs/, tests/, research/, scripts/, and troubleshooting/ explain how the runtime was built, checked, and published.",
        accent=AMBER,
    )
    _draw_card(
        draw,
        box=(1080, 682, 1490, 820),
        title="Runtime core",
        body="server/, tools/, resources/, ui/, and playground/ hold the executable system and its host-facing views.",
        accent=SLATE,
    )
    image.save(output_path)


def _generate_reader_pathways(output_path: Path) -> None:
    image, draw = _render_canvas(
        "Reader pathways and start-here matrix",
        "Four routes through the repo depending on whether the job is to run, review, evidence, or publish.",
    )
    lanes = [
        ("First-time operator", "README.md -> .env.example -> Dockerfile -> docs/getting_started.md", TEAL),
        ("Technical reviewer", "server/main.py -> server/stdio_adapter.py -> server/mcp/tools.py -> tools/", AMBER),
        ("Evidence seeker", "docs/reports/README.md -> tests/evaluation/ -> troubleshooting/ -> research/", RED),
        ("Publication editor", "docs/public_sector_ai_community/README.md -> docs/spec_package/README.md -> docs/mcp_geo_prism_bundle/", SLATE),
    ]
    top = 250
    for index, (title, body, accent) in enumerate(lanes):
        x0 = 90 + index * 370
        _draw_card(draw, box=(x0, top, x0 + 320, top + 470), title=title, body=body, accent=accent)
        if index < len(lanes) - 1:
            _draw_arrow(draw, (x0 + 320, top + 235), (x0 + 360, top + 235), fill=accent)
    image.save(output_path)


def _generate_runtime_flow(output_path: Path) -> None:
    image, draw = _render_canvas(
        "Runtime request flow",
        "How a question moves through transport, routing, tools, resources, audit, and the returned answer.",
    )
    boxes = [
        ("Host request", "Claude, Codex, VS Code, playground", TEAL),
        ("Transport", "HTTP /mcp or stdio JSON-RPC", AMBER),
        ("MCP layer", "server/mcp tools, resources, prompts, tool search", SLATE),
        ("Execution", "tools/, resources/, route graph, caches", RED),
        ("Evidence", "audit, observability, correlation IDs", MOSS),
        ("Answer", "JSON result, UI resources, report outputs", "#5087a1"),
    ]
    y0 = 350
    for index, (title, body, accent) in enumerate(boxes):
        x0 = 60 + index * 250
        _draw_card(draw, box=(x0, y0, x0 + 220, y0 + 210), title=title, body=body, accent=accent)
        if index < len(boxes) - 1:
            _draw_arrow(draw, (x0 + 220, y0 + 105), (x0 + 250, y0 + 105), fill=accent)
    image.save(output_path)


def _generate_tool_ecosystem(output_path: Path, counts: Counter[str]) -> None:
    image, draw = _render_canvas(
        "Tool and resource ecosystem map",
        "The callable surface arranged by family so a reader can see breadth before opening schemas.",
    )
    center = (800, 460)
    draw.ellipse((680, 360, 920, 600), fill="#e8f3f3", outline=TEAL, width=3)
    center_font = _load_font(30, bold=True)
    draw.text((738, 430), "Registry", font=center_font, fill=INK)
    draw.text((700, 474), "server/mcp/tools.py", font=_load_font(22), fill=MUTED)
    family_boxes = [
        ((110, 180, 440, 320), "OS Places + Names", f"{counts['os_places'] + counts['os_names']} tools", TEAL),
        ((1160, 180, 1490, 320), "OS Features + Maps", f"{counts['os_features'] + counts['os_maps'] + counts['os_map'] + counts['os_vector_tiles']} tools", AMBER),
        ((90, 610, 420, 770), "ONS + NOMIS", f"{counts['ons_data'] + counts['ons_codes'] + counts['ons_geo'] + counts['ons_search'] + counts['ons_select'] + counts['nomis']} tools", RED),
        ((1180, 610, 1510, 770), "Route + Admin", f"{counts['os_route'] + counts['admin_lookup']} tools", MOSS),
        ((500, 120, 1110, 250), "Resources and UI", "resources/, ui/, os_apps.*, playground/", SLATE),
        ((500, 670, 1110, 800), "Meta tools", f"{counts['os_mcp'] + counts['os_apps']} tools plus prompt and resource layers", "#5087a1"),
    ]
    for box, title, body, accent in family_boxes:
        _draw_card(draw, box=box, title=title, body=body, accent=accent)
    line_targets = [(440, 250), (1160, 250), (420, 690), (1180, 690), (800, 250), (800, 670)]
    for target in line_targets:
        _draw_arrow(draw, center, target, fill=SLATE, width=4)
    image.save(output_path)


def _generate_docs_stack(output_path: Path) -> None:
    image, draw = _render_canvas(
        "Documentation and publication stack",
        "From quick-start notes to reusable publication packages, the docs layer forms its own navigable system.",
    )
    stacks = [
        ("Quick start", "README.md, docs/getting_started.md, tutorial.md", TEAL),
        ("Specification", "docs/spec_package/README.md and chapter files", AMBER),
        ("Narrative", "docs/public_sector_ai_community/README.md and chapter set", RED),
        ("Reports", "docs/reports/README.md and generated evidence notes", SLATE),
        ("Slides and event record", "docs/slides/...pdf and mcp_geo_ai_community_event_record.docx", MOSS),
        ("Prism package", "docs/mcp_geo_prism_bundle/ and Prism-ready LaTeX outputs", "#5087a1"),
    ]
    x0, x1 = 260, 1340
    y = 730
    height = 90
    for title, body, accent in stacks:
        draw.rounded_rectangle((x0, y, x1, y + height), radius=20, fill=accent, outline=accent)
        draw.text((x0 + 26, y + 18), title, font=_load_font(28, bold=True), fill="white")
        draw.text((x0 + 360, y + 20), body, font=_load_font(22), fill="white")
        y -= 100
        x0 += 36
        x1 -= 36
    image.save(output_path)


def _generate_assurance_ladder(output_path: Path) -> None:
    image, draw = _render_canvas(
        "Evidence and assurance ladder",
        "The repo moves from exploratory material to public evidence through explicit assurance layers.",
    )
    steps = [
        ("Research inputs", "research/, option papers, slide notes", TEAL),
        ("Build and scripts", "scripts/, data/, resources/, devcontainer support", AMBER),
        ("Automated tests", "tests/, playground/tests/, focused regression suites", RED),
        ("Evaluation packs", "tests/evaluation/, data/benchmarking/, docs/evaluation.md", SLATE),
        ("Reports and traces", "docs/reports/, troubleshooting/, output/playwright/", MOSS),
        ("Audit and publication", "server/audit/, Prism bundle, release notes, changelog", "#5087a1"),
    ]
    x = 220
    y = 700
    for index, (title, body, accent) in enumerate(steps):
        _draw_card(draw, box=(x, y, x + 900, y + 96), title=title, body=body, accent=accent)
        if index < len(steps) - 1:
            _draw_arrow(draw, (x + 900, y + 48), (x + 980, y - 12), fill=accent)
        x += 70
        y -= 110
    image.save(output_path)


def _generate_release_pipeline(output_path: Path) -> None:
    image, draw = _render_canvas(
        "Release and iteration pipeline",
        "Implementation, validation, release packaging, and context updates form one visible feedback loop.",
    )
    nodes = [
        ((130, 220, 430, 360), "Implementation", "server/, tools/, ui/, scripts/", TEAL),
        ((620, 120, 980, 260), "Verification", "tests/, playground/tests/, CI workflow", AMBER),
        ((1130, 220, 1470, 360), "Release packaging", "CHANGELOG.md, RELEASE_NOTES/, docs/reports/", RED),
        ((1080, 570, 1450, 720), "Context refresh", "CONTEXT.md, PROGRESS.MD, README.md", SLATE),
        ((160, 570, 520, 720), "Troubleshooting and evidence", "troubleshooting/, traces, benchmark reports", MOSS),
    ]
    for box, title, body, accent in nodes:
        _draw_card(draw, box=box, title=title, body=body, accent=accent)
    arrows = [
        ((430, 290), (620, 190), TEAL),
        ((980, 190), (1130, 290), AMBER),
        ((1300, 360), (1270, 570), RED),
        ((1080, 645), (520, 645), SLATE),
        ((320, 570), (280, 360), MOSS),
    ]
    for start, end, color in arrows:
        _draw_arrow(draw, start, end, fill=color)
    image.save(output_path)


def _generate_governed_loop(output_path: Path) -> None:
    image, draw = _render_canvas(
        "Governed answer loop",
        "The repo turns a question into an answer, captures provenance, and then republishes the result as reusable evidence.",
    )
    nodes = [
        ((650, 120, 980, 240), "Question", "Talk prompt, operator task, evaluation scenario", TEAL),
        ((1060, 270, 1480, 390), "MCP routing", "Transport, tool search, route_query, registry", AMBER),
        ((1060, 520, 1480, 640), "Evidence retrieval", "tools/, resources/, caches, route graph", RED),
        ((620, 660, 1010, 790), "Answer + audit", "result payload, audit pack, provenance, traces", MOSS),
        ((120, 520, 540, 640), "Report + visuals", "docs/reports/, figures, PDF, Prism bundle", SLATE),
        ((120, 270, 540, 390), "Public reuse", "appendix replacement, slides, publication workflow", "#5087a1"),
    ]
    for box, title, body, accent in nodes:
        _draw_card(draw, box=box, title=title, body=body, accent=accent)
    loop_arrows = [
        ((980, 180), (1060, 330), TEAL),
        ((1270, 390), (1270, 520), AMBER),
        ((1060, 580), (1010, 690), RED),
        ((620, 725), (540, 580), MOSS),
        ((280, 520), (280, 390), SLATE),
        ((540, 330), (650, 180), "#5087a1"),
    ]
    for start, end, color in loop_arrows:
        _draw_arrow(draw, start, end, fill=color)
    image.save(output_path)


def _strip_frontmatter(markdown: str) -> tuple[str, str]:
    if not markdown.startswith("---\n"):
        return "", markdown
    end = markdown.find("\n---\n", 4)
    if end == -1:
        raise ValueError("Markdown frontmatter is not closed.")
    return markdown[4:end], markdown[end + 5 :]


def _extract_links(markdown: str) -> list[str]:
    return re.findall(r"\[[^\]]+\]\(([^)]+)\)", markdown)


def _validate_markdown_contract(markdown: str, manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    lines = markdown.splitlines()
    for line in lines:
        if line.startswith("####"):
            errors.append("Heading depth exceeds level 3.")
            break
    heading_set = {line.strip() for line in lines if line.startswith("##")}
    for required in manifest["required_headings"]:
        if required not in heading_set:
            errors.append(f"Missing required heading: {required}")
    for index, line in enumerate(lines):
        if not (line.startswith("## ") or line.startswith("### ")):
            continue
        cursor = index + 1
        while cursor < len(lines) and not lines[cursor].strip():
            cursor += 1
        if cursor >= len(lines):
            errors.append(f"Heading has no summary paragraph: {line}")
            continue
        candidate = lines[cursor].strip()
        if candidate.startswith("#") or candidate.startswith("![") or candidate.startswith("- "):
            errors.append(f"Heading summary missing before structured content: {line}")
    links = _extract_links(markdown)
    base = f"https://github.com/chris-page-gov/mcp-geo/"
    git_ref = manifest["git_ref"]
    for link in links:
        if link.startswith("assets/") or link.startswith("figures/"):
            continue
        if "/Users/crpage/Downloads/" in link:
            errors.append(f"Context-only source cited in markdown: {link}")
            continue
        if not link.startswith(base):
            errors.append(f"Non-repo link found in report markdown: {link}")
            continue
        if f"/{git_ref}/" not in link and not link.endswith(f"/{git_ref}"):
            errors.append(f"Link is not pinned to the required commit: {link}")
    for figure in manifest["figures"]:
        asset_ref = f"assets/analytical_index/{figure['filename']}"
        if asset_ref not in markdown:
            errors.append(f"Missing figure reference in canonical markdown: {asset_ref}")
        appendix_heading = f"### {figure['id']}."
        if appendix_heading not in markdown:
            errors.append(f"Missing appendix prompt heading for figure {figure['id']}.")
    return errors


def _validate_top_level_entries(manifest: dict[str, Any]) -> list[str]:
    expected = set(manifest["tracked_top_level_entries"])
    actual = set(_git("ls-tree", "--name-only", manifest["git_ref"]).splitlines())
    if expected == actual:
        return []
    missing = sorted(actual - expected)
    unexpected = sorted(expected - actual)
    errors: list[str] = []
    if missing:
        errors.append(f"Manifest is missing top-level entries: {', '.join(missing)}")
    if unexpected:
        errors.append(f"Manifest lists non-existent top-level entries: {', '.join(unexpected)}")
    return errors


def _appendix_replacement(markdown: str) -> str:
    _, body = _strip_frontmatter(markdown)
    lines = body.splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)
    for index, line in enumerate(lines):
        if line.startswith("# "):
            lines[index] = "# Appendix A. Analytical Index to the Public MCP-Geo Repository"
            break
    intro = (
        "This appendix-ready slice reuses the standalone analytical index content without relying on "
        "external context outside commit `fe862910da246ca77f374cfbe484985f5df4d316`."
    )
    if len(lines) > 1:
        lines.insert(1, "")
        lines.insert(2, intro)
        lines.insert(3, "")
    return "\n".join(lines).rstrip() + "\n"


def _write_gap_audit(manifest: dict[str, Any], output_path: Path) -> None:
    git_ref = manifest["git_ref"]
    repo = manifest["repo_url"]
    audit = manifest["baseline_audit"]
    baseline_url = (
        f"{repo}/blob/{git_ref}/docs/mcp_geo_prism_bundle/main.md#L122-L292"
    )
    slide_url = (
        f"{repo}/blob/{git_ref}/docs/slides/20260225%20-%20From_Apps_to_Answers.pdf"
    )
    event_doc_url = (
        f"{repo}/blob/{git_ref}/docs/reports/mcp_geo_ai_community_event_record.docx"
    )
    markdown = textwrap.dedent(
        f"""\
        # MCP-Geo Analytical Index Gap Audit

        This short note records how the replacement analytical index differs from the earlier rough appendix at the pinned public commit.

        Baseline inputs: [rough Prism bundle appendix]({baseline_url}), [slide deck]({slide_url}), and [event record DOCX]({event_doc_url}).

        ## What the earlier appendix already did well

        - {audit['strengths'][0]}
        - {audit['strengths'][1]}
        - {audit['strengths'][2]}

        ## What was incomplete

        - {audit['gaps'][0]}
        - {audit['gaps'][1]}
        - {audit['gaps'][2]}

        ## What the replacement now changes

        - {audit['changes'][0]}
        - {audit['changes'][1]}
        - {audit['changes'][2]}
        """
    )
    output_path.write_text(markdown, encoding="utf-8")


def _bundle_markdown(markdown: str, figures: list[FigureSpec]) -> str:
    bundle_text = markdown
    _, bundle_text = _strip_frontmatter(bundle_text)
    for figure in figures:
        bundle_text = bundle_text.replace(
            f"assets/analytical_index/{figure.filename}",
            f"figures/{figure.filename}",
        )
    return bundle_text.lstrip()


def _split_sections(bundle_markdown: str) -> list[tuple[str, str]]:
    lines = bundle_markdown.splitlines()
    sections: list[tuple[str, str]] = []
    intro_lines: list[str] = []
    current_heading: str | None = None
    current_lines: list[str] = []
    for line in lines:
        if line.startswith("## "):
            if current_heading is None and intro_lines:
                sections.append(("Overview", "# Overview\n\n" + "\n".join(intro_lines).strip() + "\n"))
                intro_lines = []
            if current_heading is not None:
                sections.append((current_heading[3:], current_heading + "\n\n" + "\n".join(current_lines).strip() + "\n"))
            current_heading = line
            current_lines = []
            continue
        if current_heading is None:
            intro_lines.append(line)
        else:
            current_lines.append(line)
    if current_heading is None:
        sections.append(("Overview", "# Overview\n\n" + "\n".join(intro_lines).strip() + "\n"))
    else:
        sections.append((current_heading[3:], current_heading + "\n\n" + "\n".join(current_lines).strip() + "\n"))
    return [(title, chunk.strip() + "\n") for title, chunk in sections if chunk.strip()]


def _demote_headings(chunk: str) -> str:
    output_lines: list[str] = []
    for line in chunk.splitlines():
        if line.startswith("### "):
            output_lines.append("## " + line[4:])
        elif line.startswith("## "):
            output_lines.append("# " + line[3:])
        else:
            output_lines.append(line)
    return "\n".join(output_lines).rstrip() + "\n"


def _pandoc_markdown_to_latex(markdown: str) -> str:
    completed = subprocess.run(
        ["pandoc", "--from=markdown+link_attributes", "--to=latex", "--no-highlight"],
        cwd=REPO_ROOT,
        input=markdown,
        text=True,
        capture_output=True,
        check=True,
    )
    return completed.stdout


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "section"


def _write_bundle(
    manifest: dict[str, Any],
    report_markdown: str,
    figures: list[FigureSpec],
) -> None:
    bundle_dir = REPO_ROOT / manifest["bundle_dir"]
    bundle_dir.mkdir(parents=True, exist_ok=True)
    figures_dir = bundle_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    asset_dir = REPO_ROOT / manifest["asset_dir"]
    for figure in figures:
        shutil.copy2(asset_dir / figure.filename, figures_dir / figure.filename)
    bundle_markdown = _bundle_markdown(report_markdown, figures)
    (bundle_dir / "main.md").write_text(bundle_markdown, encoding="utf-8")

    readme = textwrap.dedent(
        f"""\
        # MCP-Geo Analytical Index Prism Bundle

        This bundle is generated from `{manifest['canonical_markdown']}` and pinned to commit
        `{manifest['git_ref']}` for stable GitHub citations.

        ## Contents

        - `main.md`: bundle-friendly Markdown mirror of the canonical report
        - `main.tex`: Prism-ready LaTeX wrapper
        - `sections/*.tex`: generated section fragments
        - `figures/*.png`: generated infographic assets
        - `references.bib`: starter bibliography scaffolding

        ## Compile locally

        ```bash
        cd docs/mcp_geo_prism_bundle
        pdflatex main.tex
        pdflatex main.tex
        ```

        The canonical draft PDF remains `{manifest['report_pdf']}`; `main.tex` exists so Prism can
        import the same content with editable section files and pinned links.
        """
    )
    (bundle_dir / "README.md").write_text(readme, encoding="utf-8")

    references = textwrap.dedent(
        """\
        @misc{mcpgeo_repo,
          title = {MCP-Geo repository},
          howpublished = {GitHub},
          url = {https://github.com/chris-page-gov/mcp-geo}
        }

        @misc{mcpgeo_talk_slides,
          title = {From Apps to Answers slide deck},
          howpublished = {GitHub repository asset},
          url = {https://github.com/chris-page-gov/mcp-geo}
        }

        @misc{mcpgeo_event_record,
          title = {AI Community event record},
          howpublished = {GitHub repository asset},
          url = {https://github.com/chris-page-gov/mcp-geo}
        }
        """
    )
    (bundle_dir / "references.bib").write_text(references, encoding="utf-8")

    sections_dir = bundle_dir / "sections"
    sections_dir.mkdir(parents=True, exist_ok=True)
    section_files: list[str] = []
    for index, (title, chunk) in enumerate(_split_sections(bundle_markdown), start=1):
        tex = _pandoc_markdown_to_latex(_demote_headings(chunk))
        filename = f"{index:02d}-{_slugify(title)}.tex"
        (sections_dir / filename).write_text(tex, encoding="utf-8")
        section_files.append(filename)

    inputs = "\n".join(f"\\input{{sections/{filename[:-4]}}}" for filename in section_files)
    main_tex = textwrap.dedent(
        f"""\
        \\documentclass[11pt,a4paper]{{article}}

        \\usepackage[margin=2.2cm]{{geometry}}
        \\usepackage[utf8]{{inputenc}}
        \\usepackage[T1]{{fontenc}}
        \\usepackage{{lmodern}}
        \\usepackage{{microtype}}
        \\usepackage{{hyperref}}
        \\usepackage{{graphicx}}
        \\usepackage{{enumitem}}
        \\usepackage{{xurl}}
        \\setlength{{\\emergencystretch}}{{3em}}
        \\sloppy
        \\setlist[itemize]{{leftmargin=*}}
        \\setlist[enumerate]{{leftmargin=*}}
        \\providecommand{{\\tightlist}}{{%
          \\setlength{{\\itemsep}}{{0pt}}\\setlength{{\\parskip}}{{0pt}}}}

        \\title{{{manifest['title']}}}
        \\author{{MCP-Geo Project}}
        \\date{{{manifest['report_date']}}}

        \\begin{{document}}
        \\maketitle
        \\tableofcontents

        {inputs}

        \\end{{document}}
        """
    )
    (bundle_dir / "main.tex").write_text(main_tex.lstrip(), encoding="utf-8")


def _render_pdf(input_path: Path, output_path: Path) -> None:
    subprocess.run(
        [
            "pandoc",
            input_path.name,
            "-o",
            output_path.name,
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
        cwd=input_path.parent,
        check=True,
    )


def _compile_bundle(bundle_dir: Path) -> None:
    subprocess.run(["pdflatex", "main.tex"], cwd=bundle_dir, check=True, capture_output=True)
    subprocess.run(["pdflatex", "main.tex"], cwd=bundle_dir, check=True, capture_output=True)
    for suffix in (".aux", ".log", ".out", ".toc"):
        aux_path = bundle_dir / f"main{suffix}"
        if aux_path.exists():
            aux_path.unlink()


def _generate_figures(manifest: dict[str, Any], figures: list[FigureSpec]) -> None:
    asset_dir = REPO_ROOT / manifest["asset_dir"]
    asset_dir.mkdir(parents=True, exist_ok=True)
    counts = _top_level_entry_counts(manifest["git_ref"])
    tool_counts = _tool_prefix_counts(manifest["git_ref"])
    render_map = {
        "F01": lambda path: _generate_repo_at_a_glance(path, counts),
        "F02": _generate_reader_pathways,
        "F03": _generate_runtime_flow,
        "F04": lambda path: _generate_tool_ecosystem(path, tool_counts),
        "F05": _generate_docs_stack,
        "F06": _generate_assurance_ladder,
        "F07": _generate_release_pipeline,
        "F08": _generate_governed_loop,
    }
    for figure in figures:
        render = render_map.get(figure.id)
        if render is None:
            raise ValueError(f"No render function for figure {figure.id}")
        render(asset_dir / figure.filename)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Path to the manifest JSON.")
    parser.add_argument(
        "--skip-pdf",
        action="store_true",
        help="Validate, generate figures, and build the Prism bundle without rendering the PDF.",
    )
    parser.add_argument(
        "--skip-bundle-compile",
        action="store_true",
        help="Build bundle sources without compiling bundle/main.tex.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    manifest = _load_json(args.input)
    figures = _parse_figures(manifest)
    report_path = REPO_ROOT / manifest["canonical_markdown"]
    appendix_path = REPO_ROOT / manifest["appendix_replacement_markdown"]
    gap_audit_path = REPO_ROOT / manifest["gap_audit_markdown"]
    pdf_path = REPO_ROOT / manifest["report_pdf"]

    report_markdown = report_path.read_text(encoding="utf-8")
    errors = []
    errors.extend(_validate_markdown_contract(report_markdown, manifest))
    errors.extend(_validate_top_level_entries(manifest))
    if errors:
        raise SystemExit("\n".join(errors))

    _generate_figures(manifest, figures)
    appendix_path.write_text(_appendix_replacement(report_markdown), encoding="utf-8")
    _write_gap_audit(manifest, gap_audit_path)
    _write_bundle(manifest, report_markdown, figures)

    if not args.skip_pdf:
        _render_pdf(report_path, pdf_path)
    if not args.skip_bundle_compile:
        _compile_bundle(REPO_ROOT / manifest["bundle_dir"])

    print(report_path)
    print(appendix_path)
    print(gap_audit_path)
    print(REPO_ROOT / manifest["bundle_dir"])
    if not args.skip_pdf:
        print(pdf_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
