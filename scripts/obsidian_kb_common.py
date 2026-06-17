from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import shutil
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "Obsidian" / "MCP Geo Knowledge Base"
DEFAULT_MANIFEST_PATH = REPO_ROOT / "data" / "knowledge_base" / "obsidian_kb_manifest.json"
DEFAULT_OVERLAY_MANIFEST_PATH = (
    REPO_ROOT / "data" / "knowledge_base" / "obsidian_kb_overlay_manifest.json"
)
OVERLAY_SUBDIR = "98 Local Overlay"
OBSIDIAN_DIRNAME = "Obsidian"
WORKTREE_REF = "WORKTREE"
HARD_EXCLUSIONS = (
    "Obsidian/",
    "data/knowledge_base/obsidian_kb_manifest.json",
    "data/knowledge_base/obsidian_kb_overlay_manifest.json",
    "logs/",
    "build/",
    ".venv/",
    ".git/",
    ".pytest_cache/",
    ".mypy_cache/",
    ".ruff_cache/",
    "node_modules/",
    "playground/node_modules/",
    "playground/test-results/",
    "test-results/",
    "tmp/",
    "output/",
    "research/Archive/",
)
SOURCE_ROOTS = (
    "server/",
    "tools/",
    "resources/",
    "scripts/",
    "ui/",
    "playground/",
    "tests/",
    "README.md",
    "AGENTS.md",
    "CONTEXT.md",
    "PROGRESS.MD",
    "CHANGELOG.md",
    "SKILL.md",
    "GEMINI.md",
    "Gemini-Code-Review.md",
    ".github/workflows/",
    "RELEASE_NOTES/",
    "research/",
    "docs/",
    "troubleshooting/",
    "skills/",
    "data/",
    "pyproject.toml",
    "pytest.ini",
    "mcp.json",
)
TOPIC_THREADS: dict[str, tuple[str, ...]] = {
    "Authentication and Security": (
        "auth",
        "security",
        "secret",
        "owasp",
        "jwt",
        "token",
    ),
    "LandIS": ("landis",),
    "Map Delivery": ("map", "wheelchair", "route", "vector", "maplibre"),
    "Evaluation and Evidence": ("benchmark", "evaluation", "trace", "report", "audit"),
    "CI and Release": ("ci", "release", "docker", "ghcr", "scorecard"),
    "Knowledge Base": ("obsidian", "knowledge base"),
}
IMPORTANT_SERVER_MODULES = {
    "server/main.py",
    "server/config.py",
    "server/stdio_adapter.py",
    "server/mcp/tools.py",
    "server/mcp/resources.py",
    "server/mcp/playground.py",
}
IMPORTANT_SCRIPT_MODULES = {
    "scripts/build_obsidian_kb.py",
    "scripts/validate_obsidian_kb.py",
    "scripts/repo_extent_complexity_report.py",
    "scripts/codex_long_horizon_summary.py",
    "scripts/generate_mcp_geo_analytical_index.py",
    "scripts/trace_session.py",
    "scripts/trace_report.py",
}
MARKDOWN_SUFFIXES = {".md", ".mdx"}
BINARY_SUFFIXES = {
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".docx",
    ".pptx",
    ".xlsx",
    ".zip",
    ".svg",
    ".json",
    ".html",
}
GENERATED_DATA_ALLOWLIST = (
    "data/benchmarking/stakeholder_eval/live_run_latest.json",
    "data/report_inputs/",
)


@dataclass
class SourceRecord:
    path: str
    category: str
    note_path: str
    kb_kind: str
    title: str
    sha256: str
    size_bytes: int
    is_binary: bool
    first_seen_date: str
    last_commit_date: str
    source_url: str
    summary: str = ""
    headings: list[str] = field(default_factory=list)
    tests: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class NoteRecord:
    note_path: str
    title: str
    kb_kind: str
    source_paths: list[str]
    body: str
    frontmatter: dict[str, Any]


class GitRepo:
    def __init__(self, root: Path, git_ref: str = WORKTREE_REF) -> None:
        self.root = root
        self.git_ref = git_ref or WORKTREE_REF
        self._first_seen_cache: dict[str, str] = {}
        self._last_commit_cache: dict[str, str] = {}
        self._resolved_ref_cache: dict[str, str] = {}
        self._remote_url_cache: str | None = None
        self._tracked_cache: list[str] | None = None

    def run(self, *args: str, text: bool = True, check: bool = True) -> str | bytes:
        result = subprocess.run(
            ["git", *args],
            cwd=self.root,
            check=check,
            capture_output=True,
            text=text,
        )
        return result.stdout

    def tracked_paths(self) -> list[str]:
        if self._tracked_cache is not None:
            return list(self._tracked_cache)
        if self.git_ref == WORKTREE_REF:
            output = self.run("ls-files")
        else:
            output = self.run("ls-tree", "-r", "--name-only", self.git_ref)
        self._tracked_cache = [line.strip() for line in str(output).splitlines() if line.strip()]
        return list(self._tracked_cache)

    def resolve_ref(self, ref: str | None = None) -> str:
        lookup = ref or self.git_ref
        if lookup in self._resolved_ref_cache:
            return self._resolved_ref_cache[lookup]
        target = "HEAD" if lookup == WORKTREE_REF else lookup
        resolved = str(self.run("rev-parse", target)).strip()
        self._resolved_ref_cache[lookup] = resolved
        return resolved

    def is_dirty(self) -> bool:
        return bool(str(self.run("status", "--short")).strip())

    def file_bytes(self, rel_path: str) -> bytes:
        if self.git_ref == WORKTREE_REF:
            return (self.root / rel_path).read_bytes()
        output = self.run("show", f"{self.git_ref}:{rel_path}", text=False)
        if isinstance(output, bytes):
            return output
        return output.encode("utf-8")

    def file_text(self, rel_path: str) -> str:
        return self.file_bytes(rel_path).decode("utf-8", errors="replace")

    def first_seen_date(self, rel_path: str) -> str:
        if rel_path in self._first_seen_cache:
            return self._first_seen_cache[rel_path]
        output = str(
            self.run(
                "log", "--diff-filter=A", "--follow", "--format=%ad", "--date=short", "--", rel_path
            )
        ).strip()
        first_seen = output.splitlines()[-1] if output else ""
        self._first_seen_cache[rel_path] = first_seen
        return first_seen

    def last_commit_date(self, rel_path: str) -> str:
        if rel_path in self._last_commit_cache:
            return self._last_commit_cache[rel_path]
        output = str(self.run("log", "-1", "--format=%ad", "--date=short", "--", rel_path)).strip()
        self._last_commit_cache[rel_path] = output
        return output

    def remote_https_url(self) -> str:
        if self._remote_url_cache is not None:
            return self._remote_url_cache
        try:
            raw = str(self.run("remote", "get-url", "origin")).strip()
        except subprocess.CalledProcessError:
            raw = "https://example.invalid/local/mcp-geo"
        if raw.startswith("git@github.com:"):
            raw = raw.replace("git@github.com:", "https://github.com/")
        raw = raw.removesuffix(".git")
        self._remote_url_cache = raw
        return raw


def utc_now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def hard_excluded(rel_path: str) -> bool:
    if rel_path.endswith(".DS_Store"):
        return True
    return rel_path.startswith(HARD_EXCLUSIONS)


def source_in_scope(rel_path: str) -> bool:
    if hard_excluded(rel_path):
        return False
    return rel_path.startswith(SOURCE_ROOTS) or rel_path in SOURCE_ROOTS


def slugify(text: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", " ", text).strip()
    return re.sub(r"\s+", " ", cleaned) or "Untitled"


def title_from_path(rel_path: str) -> str:
    path = Path(rel_path)
    stem = path.stem
    if stem in {"__init__", "__main__"}:
        stem = f"{path.parent.name} package"
    stem = stem.replace("_", " ").replace("-", " ")
    titled = " ".join(word.capitalize() for word in stem.split())
    return titled or rel_path


def sha256_hex(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def markdown_headings(text: str, limit: int = 8) -> list[str]:
    headings: list[str] = []
    for line in text.splitlines():
        if line.startswith("#"):
            heading = line.lstrip("#").strip()
            if heading:
                headings.append(heading)
        if len(headings) >= limit:
            break
    return headings


def extract_docstring_or_summary(text: str) -> str:
    lines = text.splitlines()
    if not lines:
        return ""
    if lines[0].startswith("#!"):
        lines = lines[1:]
    joined = "\n".join(lines).lstrip()
    for quote in ('"""', "'''"):
        if joined.startswith(quote):
            end = joined.find(quote, 3)
            if end > 3:
                return " ".join(joined[3:end].strip().split())
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip()
        return stripped[:200]
    return ""


def markdown_preview(text: str, limit: int = 220) -> str:
    stripped = text
    if stripped.startswith("---\n"):
        end = stripped.find("\n---\n", 4)
        if end != -1:
            stripped = stripped[end + 5 :]
    lines = [line.strip() for line in stripped.splitlines() if line.strip()]
    preview = " ".join(line for line in lines if not line.startswith("#"))
    return preview[:limit].strip()


def human_bytes(size_bytes: int) -> str:
    units = ["B", "KB", "MB", "GB"]
    value = float(size_bytes)
    unit = units[0]
    for unit in units:
        if value < 1024 or unit == units[-1]:
            break
        value /= 1024.0
    return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"


def top_level_path(rel_path: str) -> str:
    return rel_path.split("/", 1)[0]


def repo_tree_url(remote_url: str, commit: str, rel_path: str, *, is_dir: bool = False) -> str:
    kind = "tree" if is_dir or rel_path.endswith("/") else "blob"
    return f"{remote_url}/{kind}/{commit}/{rel_path}"


def detect_tool_family(rel_path: str) -> str:
    stem = Path(rel_path).stem
    if stem in {"__init__", "__main__"}:
        return f"{Path(rel_path).parent.name}_package"
    known_prefixes = (
        "admin_lookup",
        "council_tax",
        "landis",
        "nomis",
        "ons_data",
        "ons_dimensions",
        "ons_geo",
        "ons_search",
        "ons_select",
        "os_apps",
        "os_common",
        "os_delivery",
        "os_downloads",
        "os_features",
        "os_landscape",
        "os_linked_ids",
        "os_maps",
        "os_mcp",
        "os_names",
        "os_offline",
        "os_places",
        "os_poi",
        "os_qgis",
        "os_resources",
        "os_route",
        "os_vector_tiles",
    )
    for prefix in known_prefixes:
        if stem == prefix or stem.startswith(prefix + "_"):
            return prefix
    if "_" in stem:
        first, second, *_rest = stem.split("_")
        if first in {"os", "ons"} and second:
            return f"{first}_{second}"
        return f"{first}_{second}"
    return stem


def detect_script_family(rel_path: str) -> str:
    stem = Path(rel_path).stem
    if stem in {"__init__", "__main__"}:
        return f"{Path(rel_path).parent.name}_package"
    if rel_path.startswith("scripts/map_trials/"):
        return "map_trials"
    for prefix in (
        "boundary",
        "build_obsidian_kb",
        "check",
        "codex",
        "generate",
        "host_benchmark",
        "landis",
        "mcp",
        "ons_catalog",
        "os_catalog",
        "pack_cache",
        "rate_limit",
        "repo_extent",
        "route_graph",
        "stakeholder",
        "trace",
        "validate",
    ):
        if stem == prefix or stem.startswith(prefix + "_"):
            return prefix
    return stem.split("_", 1)[0]


def group_report_path(rel_path: str) -> str:
    if rel_path.startswith("docs/reports/assets/"):
        return "30 Docs and Research/Report Assets.md"
    if rel_path.startswith("docs/reports/peatland-case-study/"):
        return "30 Docs and Research/Peatland Case Study.md"
    return "30 Docs and Research/Reports Catalog.md"


def group_research_path(rel_path: str) -> str:
    parts = Path(rel_path).parts
    if len(parts) >= 2:
        return f"30 Docs and Research/Research Pack - {slugify(parts[1])}.md"
    return "30 Docs and Research/Research Overview.md"


def classify_path(rel_path: str) -> tuple[str, str, str, str]:
    if rel_path in {
        "README.md",
        "AGENTS.md",
        "CONTEXT.md",
        "PROGRESS.MD",
        "CHANGELOG.md",
        "SKILL.md",
    }:
        return (
            "storyline_control",
            "10 Repository Map/Storyline and Control.md",
            "storyline_note",
            title_from_path(rel_path),
        )
    if rel_path in {"GEMINI.md", "Gemini-Code-Review.md"}:
        return (
            "storyline_control",
            "10 Repository Map/Review and Companion Documents.md",
            "storyline_note",
            title_from_path(rel_path),
        )
    if rel_path == "pyproject.toml":
        return (
            "storyline_control",
            "10 Repository Map/Project Configuration.md",
            "storyline_note",
            "Pyproject",
        )
    if rel_path.startswith(".github/workflows/"):
        return (
            "storyline_control",
            "40 Timeline and Journal/CI and Release Controls.md",
            "storyline_note",
            title_from_path(rel_path),
        )
    if rel_path.startswith("RELEASE_NOTES/"):
        return (
            "storyline_control",
            "40 Timeline and Journal/Release Ledger.md",
            "timeline_note",
            title_from_path(rel_path),
        )
    if rel_path.startswith("server/"):
        if rel_path in IMPORTANT_SERVER_MODULES:
            title = title_from_path(rel_path)
            return (
                "code_runtime",
                f"20 Code/{title}.md",
                "code_module",
                title,
            )
        if rel_path.startswith("server/mcp/"):
            return ("code_runtime", "20 Code/MCP Surface Overview.md", "code_family", "MCP Surface")
        if rel_path.startswith("server/audit/"):
            return (
                "code_runtime",
                "20 Code/Audit and Transcript Infrastructure.md",
                "code_family",
                "Audit and Transcript Infrastructure",
            )
        return (
            "code_runtime",
            "20 Code/Server Runtime Overview.md",
            "code_family",
            "Server Runtime",
        )
    if rel_path.startswith("tools/"):
        family = detect_tool_family(rel_path)
        return (
            "code_runtime",
            f"20 Code/Tool Family - {slugify(family)}.md",
            "code_family",
            title_from_path(rel_path),
        )
    if rel_path.startswith("scripts/"):
        if rel_path in IMPORTANT_SCRIPT_MODULES:
            title = title_from_path(rel_path)
            return ("code_runtime", f"20 Code/{title}.md", "code_module", title)
        family = detect_script_family(rel_path)
        return (
            "code_runtime",
            f"20 Code/Script Family - {slugify(family)}.md",
            "code_family",
            title_from_path(rel_path),
        )
    if rel_path.startswith("resources/"):
        return (
            "code_runtime",
            "20 Code/Resources and Data Assets.md",
            "code_family",
            title_from_path(rel_path),
        )
    if rel_path.startswith("ui/"):
        return ("code_runtime", "20 Code/UI Surfaces.md", "code_family", title_from_path(rel_path))
    if rel_path.startswith("playground/"):
        return (
            "code_runtime",
            "20 Code/Playground and Browser Tests.md",
            "code_family",
            title_from_path(rel_path),
        )
    if rel_path.startswith("tests/"):
        return (
            "code_runtime",
            "20 Code/Test and Validation Surface.md",
            "code_family",
            title_from_path(rel_path),
        )
    if rel_path.startswith("docs/reports/"):
        return (
            "docs_research",
            group_report_path(rel_path),
            "artifact_catalog",
            title_from_path(rel_path),
        )
    if rel_path.startswith("research/"):
        return (
            "docs_research",
            group_research_path(rel_path),
            "artifact_catalog",
            title_from_path(rel_path),
        )
    if rel_path.startswith("docs/vendor/") or rel_path.startswith("submodules/"):
        return (
            "external_context",
            "50 Standards and Ecosystem/External Mirrors and Submodules.md",
            "external_context",
            title_from_path(rel_path),
        )
    if rel_path.startswith("docs/spec_package/"):
        return (
            "standards_ecosystem",
            "50 Standards and Ecosystem/Specification Package.md",
            "standards_note",
            title_from_path(rel_path),
        )
    if rel_path.startswith("docs/public_sector_ai_community/"):
        return (
            "standards_ecosystem",
            "50 Standards and Ecosystem/Public Sector AI Community Narrative.md",
            "standards_note",
            title_from_path(rel_path),
        )
    if rel_path.startswith("docs/"):
        return (
            "docs_research",
            "30 Docs and Research/Documentation Surface.md",
            "artifact_catalog",
            title_from_path(rel_path),
        )
    if rel_path.startswith("troubleshooting/"):
        return (
            "docs_research",
            "30 Docs and Research/Troubleshooting and Case Notes.md",
            "artifact_catalog",
            title_from_path(rel_path),
        )
    if rel_path.startswith("skills/"):
        return (
            "skills_maintenance",
            "60 Skills and Maintenance/Repository Skills.md",
            "maintenance_note",
            title_from_path(rel_path),
        )
    if rel_path.startswith("data/"):
        if rel_path.startswith(GENERATED_DATA_ALLOWLIST) or rel_path in GENERATED_DATA_ALLOWLIST:
            return (
                "docs_research",
                "30 Docs and Research/Data Manifests.md",
                "artifact_catalog",
                title_from_path(rel_path),
            )
        return (
            "docs_research",
            "30 Docs and Research/Data Manifests.md",
            "artifact_catalog",
            title_from_path(rel_path),
        )
    return (
        "docs_research",
        "10 Repository Map/Miscellaneous Tracked Surface.md",
        "artifact_catalog",
        title_from_path(rel_path),
    )


def build_test_index(repo: GitRepo) -> dict[str, list[str]]:
    test_paths = [
        path for path in repo.tracked_paths() if path.startswith("tests/") and path.endswith(".py")
    ]
    test_contents: list[tuple[str, str]] = []
    for path in test_paths:
        try:
            test_contents.append((path, repo.file_text(path)))
        except FileNotFoundError:
            continue

    index: dict[str, list[str]] = defaultdict(list)
    source_paths = [path for path in repo.tracked_paths() if path.endswith((".py", ".md", ".json"))]
    for rel_path in source_paths:
        basename = Path(rel_path).name
        stem = Path(rel_path).stem
        for test_path, content in test_contents:
            if basename in content or stem in content:
                index[rel_path].append(test_path)
    return {key: sorted(set(value)) for key, value in index.items()}


def summarize_source(repo: GitRepo, rel_path: str) -> tuple[str, list[str], bool]:
    suffix = Path(rel_path).suffix.lower()
    is_binary = suffix in BINARY_SUFFIXES and suffix not in {".json", ".html"}
    if is_binary:
        return "", [], True
    text = repo.file_text(rel_path)
    if suffix in MARKDOWN_SUFFIXES:
        return markdown_preview(text), markdown_headings(text), False
    if suffix == ".json":
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return text[:200].strip(), [], False
        if isinstance(payload, dict):
            keys = ", ".join(sorted(payload.keys())[:8])
            return f"JSON object keys: {keys}", [], False
        if isinstance(payload, list):
            return f"JSON array with {len(payload)} entries", [], False
        return f"JSON scalar of type {type(payload).__name__}", [], False
    if suffix == ".html":
        title_match = re.search(r"<title>(.*?)</title>", text, re.IGNORECASE | re.DOTALL)
        title = title_match.group(1).strip() if title_match else ""
        return title or text[:160].strip(), [], False
    return extract_docstring_or_summary(text), [], False


def collect_sources(repo_root: Path, git_ref: str = WORKTREE_REF) -> list[SourceRecord]:
    repo = GitRepo(repo_root, git_ref=git_ref)
    commit = repo.resolve_ref()
    remote_url = repo.remote_https_url()
    test_index = build_test_index(repo)
    records: list[SourceRecord] = []
    for rel_path in sorted(repo.tracked_paths()):
        if not source_in_scope(rel_path):
            continue
        category, note_path, kb_kind, title = classify_path(rel_path)
        absolute_path = repo_root / rel_path
        is_directory_entry = git_ref == WORKTREE_REF and absolute_path.is_dir()
        if is_directory_entry:
            payload = rel_path.encode("utf-8")
            summary = "Tracked directory or submodule entry."
            headings = []
            is_binary = False
        else:
            payload = repo.file_bytes(rel_path)
            summary, headings, is_binary = summarize_source(repo, rel_path)
        record = SourceRecord(
            path=rel_path,
            category=category,
            note_path=note_path,
            kb_kind=kb_kind,
            title=title,
            sha256=sha256_hex(payload),
            size_bytes=len(payload),
            is_binary=is_binary,
            first_seen_date=repo.first_seen_date(rel_path),
            last_commit_date=repo.last_commit_date(rel_path),
            source_url=repo_tree_url(remote_url, commit, rel_path, is_dir=is_directory_entry),
            summary=summary,
            headings=headings,
            tests=test_index.get(rel_path, []),
        )
        records.append(record)
    return records


def render_frontmatter(frontmatter: dict[str, Any]) -> str:
    lines = ["---"]
    for key, value in frontmatter.items():
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                if isinstance(item, dict):
                    lines.append("  -")
                    for sub_key, sub_value in item.items():
                        lines.append(f"    {sub_key}: {json.dumps(sub_value, ensure_ascii=True)}")
                else:
                    lines.append(f"  - {json.dumps(item, ensure_ascii=True)}")
        elif isinstance(value, dict):
            lines.append(f"{key}:")
            for sub_key, sub_value in value.items():
                if key == "source_hashes" and isinstance(sub_value, str):
                    rendered_value = json.dumps(_format_hash_for_frontmatter(sub_value))
                else:
                    rendered_value = json.dumps(sub_value, ensure_ascii=True)
                lines.append(f"  {sub_key}: {rendered_value}")
        elif isinstance(value, bool):
            lines.append(f"{key}: {'true' if value else 'false'}")
        elif value is None:
            lines.append(f"{key}: null")
        else:
            lines.append(f"{key}: {json.dumps(value, ensure_ascii=True)}")
    lines.append("---")
    return "\n".join(lines)


def _format_hash_for_frontmatter(value: str) -> str:
    if re.fullmatch(r"[0-9a-f]{64}", value):
        return "sha256:" + "-".join(value[idx : idx + 8] for idx in range(0, len(value), 8))
    return value


def note_link(note_path: str) -> str:
    return Path(note_path).stem


def list_links(note_paths: list[str]) -> str:
    return ", ".join(f"[[{note_link(path)}]]" for path in note_paths)


def build_home_note(records: list[SourceRecord], build_meta: dict[str, Any]) -> NoteRecord:
    category_counts = Counter(record.category for record in records)
    note_paths_by_category: dict[str, list[str]] = defaultdict(list)
    for record in records:
        note_paths_by_category[record.category].append(record.note_path)

    frontmatter = base_frontmatter(
        title="MCP Geo Knowledge Base",
        kb_kind="vault_home",
        records=records,
        build_meta=build_meta,
    )
    lines = [
        "# MCP Geo Knowledge Base",
        "",
        "## Summary",
        "",
        (
            "- Deterministic canonical vault generated from repo sources while excluding "
            "`Obsidian/**`."
        ),
        (
            "- Evidence-first notes record source files, hashes, dates, and commit-pinned "
            "GitHub links."
        ),
        f"- Generated from `{build_meta['source_commit']}`"
        + (" (dirty worktree)" if build_meta.get("source_commit_dirty") else "")
        + ".",
        "",
        "## Navigation",
        "",
        f"- [[{note_link('10 Repository Map/10 - Repository Map.md')}]]",
        f"- [[{note_link('20 Code/20 - Code Hub.md')}]]",
        f"- [[{note_link('30 Docs and Research/30 - Docs and Research Hub.md')}]]",
        f"- [[{note_link('40 Timeline and Journal/40 - Timeline and Journal Hub.md')}]]",
        f"- [[{note_link('50 Standards and Ecosystem/50 - Standards and Ecosystem Hub.md')}]]",
        f"- [[{note_link('60 Skills and Maintenance/60 - Skills and Maintenance Hub.md')}]]",
        f"- [[{note_link('90 Assets/90 - Assets.md')}]]",
        "",
        "## Source Coverage",
        "",
        "| Category | Count | Notes |",
        "| --- | ---: | --- |",
    ]
    for category, count in sorted(category_counts.items()):
        category_links = list_links(sorted(set(note_paths_by_category[category])))
        lines.append(
            f"| `{category}` | {count} | {category_links} |"
        )
    lines.extend(
        [
            "",
            "## Canonical Rules",
            "",
            "- `Obsidian/**` is always excluded from source scanning.",
            (
                "- Canonical notes are built from repo sources; local traces belong in the "
                "overlay tier only."
            ),
            "- Point-in-time links use commit-pinned GitHub URLs rather than moving branch links.",
        ]
    )
    return NoteRecord(
        note_path="00 Home/00 - Home.md",
        title="MCP Geo Knowledge Base",
        kb_kind="vault_home",
        source_paths=sorted(
            {
                record.path
                for record in records
                if record.category in {"storyline_control", "code_runtime", "docs_research"}
            }
        ),
        body=render_frontmatter(frontmatter) + "\n" + "\n".join(lines).rstrip() + "\n",
        frontmatter=frontmatter,
    )


def base_frontmatter(
    title: str,
    kb_kind: str,
    records: list[SourceRecord],
    build_meta: dict[str, Any],
) -> dict[str, Any]:
    paths = sorted({record.path for record in records})
    first_seen = min(
        (record.first_seen_date for record in records if record.first_seen_date), default=""
    )
    source_urls = [record.source_url for record in records[:32]]
    source_hashes = {record.path: record.sha256 for record in records[:32]}
    return {
        "title": title,
        "kb_kind": kb_kind,
        "source_paths": paths,
        "source_commit": build_meta["source_commit"],
        "source_commit_dirty": build_meta.get("source_commit_dirty", False),
        "source_urls": source_urls,
        "source_hashes": source_hashes,
        "generated_at": build_meta["generated_at"],
        "evidence_scope": build_meta["evidence_scope"],
        "first_seen_date": first_seen,
        "last_validated_at": build_meta["generated_at"],
    }


def build_group_note(
    note_path: str,
    records: list[SourceRecord],
    build_meta: dict[str, Any],
) -> NoteRecord:
    title = Path(note_path).stem
    kb_kind = records[0].kb_kind if records else "catalog_note"
    frontmatter = base_frontmatter(
        title=title, kb_kind=kb_kind, records=records, build_meta=build_meta
    )
    lines = [f"# {title}", ""]
    categories = sorted({record.category for record in records})
    lines.extend(
        [
            "## Evidence Scope",
            "",
            f"- Categories: {', '.join(f'`{category}`' for category in categories)}",
            f"- Source file count: {len(records)}",
            "",
            "## Source Inventory",
            "",
            "| Path | Summary | First Seen | Last Commit | Related Tests |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for record in sorted(records, key=lambda item: item.path):
        summary = record.summary or ("Binary artifact" if record.is_binary else "")
        tests = ", ".join(f"`{path}`" for path in record.tests[:4])
        lines.append(
            "| "
            + f"`{record.path}` | {summary[:120]} | {record.first_seen_date or '-'} | "
            + f"{record.last_commit_date or '-'} | {tests or '-'} |"
        )
    markdown_records = [
        record for record in records if record.path.endswith(tuple(MARKDOWN_SUFFIXES))
    ]
    if markdown_records:
        lines.extend(["", "## Visible Headings", ""])
        for record in markdown_records[:18]:
            if record.headings:
                lines.append(
                    f"- `{record.path}`: "
                    + " | ".join(f"`{heading}`" for heading in record.headings[:6])
                )
    binary_records = [record for record in records if record.is_binary]
    if binary_records:
        lines.extend(["", "## Binary Artifacts", ""])
        for record in binary_records[:40]:
            lines.append(
                f"- `{record.path}` ({human_bytes(record.size_bytes)}): "
                f"[Pinned source]({record.source_url})"
            )
    lines.extend(["", "## Pinned Sources", ""])
    for record in records[:40]:
        lines.append(f"- [`{record.path}`]({record.source_url})")
    return NoteRecord(
        note_path=note_path,
        title=title,
        kb_kind=kb_kind,
        source_paths=sorted({record.path for record in records}),
        body=render_frontmatter(frontmatter) + "\n" + "\n".join(lines).rstrip() + "\n",
        frontmatter=frontmatter,
    )


def build_repository_map_notes(
    records: list[SourceRecord], build_meta: dict[str, Any]
) -> list[NoteRecord]:
    by_top = Counter(top_level_path(record.path) for record in records)
    repo_map_records = [
        record
        for record in records
        if record.category in {"storyline_control", "code_runtime", "docs_research"}
    ]
    frontmatter = base_frontmatter(
        title="Repository Map",
        kb_kind="repository_map",
        records=repo_map_records,
        build_meta=build_meta,
    )
    lines = [
        "# Repository Map",
        "",
        "## Top-Level Inventory",
        "",
        "| Entry | Tracked Files |",
        "| --- | ---: |",
    ]
    for top_level, count in sorted(by_top.items()):
        lines.append(f"| `{top_level}` | {count} |")
    lines.extend(
        [
            "",
            "## Core Hubs",
            "",
            f"- [[{note_link('10 Repository Map/Storyline and Control.md')}]]",
            f"- [[{note_link('20 Code/20 - Code Hub.md')}]]",
            f"- [[{note_link('30 Docs and Research/30 - Docs and Research Hub.md')}]]",
            f"- [[{note_link('40 Timeline and Journal/40 - Timeline and Journal Hub.md')}]]",
            f"- [[{note_link('50 Standards and Ecosystem/50 - Standards and Ecosystem Hub.md')}]]",
        ]
    )
    repo_map_note = NoteRecord(
        note_path="10 Repository Map/10 - Repository Map.md",
        title="Repository Map",
        kb_kind="repository_map",
        source_paths=sorted({record.path for record in repo_map_records}),
        body=render_frontmatter(frontmatter) + "\n" + "\n".join(lines).rstrip() + "\n",
        frontmatter=frontmatter,
    )
    source_catalog_note = build_group_note(
        "10 Repository Map/Source Catalog.md",
        records,
        build_meta,
    )
    misc_records = [
        record
        for record in records
        if record.note_path == "10 Repository Map/Miscellaneous Tracked Surface.md"
    ]
    misc_note = None
    if misc_records:
        misc_note = build_group_note(
            "10 Repository Map/Miscellaneous Tracked Surface.md", misc_records, build_meta
        )
    notes = [repo_map_note, source_catalog_note]
    if misc_note is not None:
        notes.append(misc_note)
    return notes


def build_code_hub(records: list[SourceRecord], build_meta: dict[str, Any]) -> NoteRecord:
    code_records = [record for record in records if record.category == "code_runtime"]
    by_note = sorted(
        {
            record.note_path
            for record in code_records
            if record.note_path != "20 Code/20 - Code Hub.md"
        }
    )
    frontmatter = base_frontmatter(
        title="Code Hub",
        kb_kind="code_hub",
        records=code_records,
        build_meta=build_meta,
    )
    lines = [
        "# Code Hub",
        "",
        "## Coverage",
        "",
        f"- Tracked source files in scope: {len(code_records)}",
        f"- Generated code notes: {len(by_note)}",
        "",
        "## Subsystem Notes",
        "",
    ]
    for note_path in by_note:
        lines.append(f"- [[{note_link(note_path)}]]")
    lines.extend(
        [
            "",
            "## Documentation Policy",
            "",
            "- Important entrypoints get module notes.",
            "- Broader families are summarized by grouped inventory notes.",
            "- Every tracked code/runtime source maps to at least one canonical note.",
        ]
    )
    return NoteRecord(
        note_path="20 Code/20 - Code Hub.md",
        title="Code Hub",
        kb_kind="code_hub",
        source_paths=sorted({record.path for record in code_records}),
        body=render_frontmatter(frontmatter) + "\n" + "\n".join(lines).rstrip() + "\n",
        frontmatter=frontmatter,
    )


def build_docs_hub(records: list[SourceRecord], build_meta: dict[str, Any]) -> NoteRecord:
    scoped_records = [record for record in records if record.category == "docs_research"]
    by_note = sorted(
        {
            record.note_path
            for record in scoped_records
            if record.note_path != "30 Docs and Research/30 - Docs and Research Hub.md"
        }
    )
    frontmatter = base_frontmatter(
        title="Docs and Research Hub",
        kb_kind="docs_hub",
        records=scoped_records,
        build_meta=build_meta,
    )
    lines = [
        "# Docs and Research Hub",
        "",
        "## Note Groups",
        "",
    ]
    for note_path in by_note:
        lines.append(f"- [[{note_link(note_path)}]]")
    lines.extend(
        [
            "",
            "## Handling Rules",
            "",
            "- Markdown artifacts are summarized only from visible headings and text.",
            "- Binary artifacts are listed with metadata and pinned source links.",
            "- Report and research notes remain descriptive rather than interpretive.",
        ]
    )
    return NoteRecord(
        note_path="30 Docs and Research/30 - Docs and Research Hub.md",
        title="Docs and Research Hub",
        kb_kind="docs_hub",
        source_paths=sorted({record.path for record in scoped_records}),
        body=render_frontmatter(frontmatter) + "\n" + "\n".join(lines).rstrip() + "\n",
        frontmatter=frontmatter,
    )


def build_timeline_hub(records: list[SourceRecord], build_meta: dict[str, Any]) -> NoteRecord:
    timeline_records = [
        record
        for record in records
        if record.category in {"storyline_control", "docs_research", "standards_ecosystem"}
    ]
    frontmatter = base_frontmatter(
        title="Timeline and Journal Hub",
        kb_kind="timeline_hub",
        records=timeline_records,
        build_meta=build_meta,
    )
    lines = [
        "# Timeline and Journal Hub",
        "",
        "## Navigation",
        "",
        f"- [[{note_link('40 Timeline and Journal/Chronology.md')}]]",
        f"- [[{note_link('40 Timeline and Journal/Topic Threads.md')}]]",
        f"- [[{note_link('40 Timeline and Journal/Release Ledger.md')}]]",
        f"- [[{note_link('40 Timeline and Journal/CI and Release Controls.md')}]]",
        "",
        "## Evidence Rules",
        "",
        (
            "- Entries come from explicit commits, dated reports, release notes, and "
            "tracked context files."
        ),
        "- Topic threads connect evidence items by shared terms without inventing intent.",
        "- Local session traces belong in the overlay tier, not in the canonical timeline.",
    ]
    return NoteRecord(
        note_path="40 Timeline and Journal/40 - Timeline and Journal Hub.md",
        title="Timeline and Journal Hub",
        kb_kind="timeline_hub",
        source_paths=sorted({record.path for record in timeline_records}),
        body=render_frontmatter(frontmatter) + "\n" + "\n".join(lines).rstrip() + "\n",
        frontmatter=frontmatter,
    )


def build_standards_hub(records: list[SourceRecord], build_meta: dict[str, Any]) -> NoteRecord:
    scoped_records = [
        record
        for record in records
        if record.category in {"standards_ecosystem", "external_context"}
    ]
    frontmatter = base_frontmatter(
        title="Standards and Ecosystem Hub",
        kb_kind="standards_hub",
        records=scoped_records,
        build_meta=build_meta,
    )
    lines = [
        "# Standards and Ecosystem Hub",
        "",
        "## Notes",
        "",
        f"- [[{note_link('50 Standards and Ecosystem/MCP and Host Evolution.md')}]]",
        f"- [[{note_link('50 Standards and Ecosystem/Specification Package.md')}]]",
        f"- [[{note_link('50 Standards and Ecosystem/Public Sector AI Community Narrative.md')}]]",
        f"- [[{note_link('50 Standards and Ecosystem/External Mirrors and Submodules.md')}]]",
    ]
    return NoteRecord(
        note_path="50 Standards and Ecosystem/50 - Standards and Ecosystem Hub.md",
        title="Standards and Ecosystem Hub",
        kb_kind="standards_hub",
        source_paths=sorted({record.path for record in scoped_records}),
        body=render_frontmatter(frontmatter) + "\n" + "\n".join(lines).rstrip() + "\n",
        frontmatter=frontmatter,
    )


def build_maintenance_hub(records: list[SourceRecord], build_meta: dict[str, Any]) -> NoteRecord:
    scoped_records = [
        record
        for record in records
        if record.category in {"skills_maintenance", "storyline_control"}
        or record.path in IMPORTANT_SCRIPT_MODULES
    ]
    frontmatter = base_frontmatter(
        title="Skills and Maintenance Hub",
        kb_kind="maintenance_hub",
        records=scoped_records,
        build_meta=build_meta,
    )
    lines = [
        "# Skills and Maintenance Hub",
        "",
        "## Notes",
        "",
        f"- [[{note_link('60 Skills and Maintenance/Repository Skills.md')}]]",
        f"- [[{note_link('60 Skills and Maintenance/Knowledge Base Maintenance.md')}]]",
        f"- [[{note_link('60 Skills and Maintenance/Maintenance Workflow.md')}]]",
        "",
        "## Maintenance Rules",
        "",
        "- Refresh the canonical vault from tracked repo content.",
        "- Generate overlay notes only when local evidence is required.",
        "- Run validator checks before treating the vault as current.",
    ]
    return NoteRecord(
        note_path="60 Skills and Maintenance/60 - Skills and Maintenance Hub.md",
        title="Skills and Maintenance Hub",
        kb_kind="maintenance_hub",
        source_paths=sorted({record.path for record in scoped_records}),
        body=render_frontmatter(frontmatter) + "\n" + "\n".join(lines).rstrip() + "\n",
        frontmatter=frontmatter,
    )


def build_assets_note(build_meta: dict[str, Any]) -> NoteRecord:
    frontmatter = {
        "title": "Assets",
        "kb_kind": "assets_hub",
        "source_paths": [],
        "source_commit": build_meta["source_commit"],
        "source_commit_dirty": build_meta.get("source_commit_dirty", False),
        "source_urls": [],
        "source_hashes": {},
        "generated_at": build_meta["generated_at"],
        "evidence_scope": build_meta["evidence_scope"],
        "first_seen_date": "",
        "last_validated_at": build_meta["generated_at"],
    }
    lines = [
        "# Assets",
        "",
        (
            "This directory is reserved for immutable copied artifacts when a note needs "
            "an in-vault copy."
        ),
        "",
        (
            "Current canonical build keeps large report and research binaries in place and "
            "links back to their"
        ),
        (
            "tracked source paths plus commit-pinned GitHub URLs instead of duplicating "
            "them into the vault."
        ),
    ]
    return NoteRecord(
        note_path="90 Assets/90 - Assets.md",
        title="Assets",
        kb_kind="assets_hub",
        source_paths=[],
        body=render_frontmatter(frontmatter) + "\n" + "\n".join(lines).rstrip() + "\n",
        frontmatter=frontmatter,
    )


def build_chronology_note(
    repo_root: Path, records: list[SourceRecord], build_meta: dict[str, Any], limit: int = 120
) -> NoteRecord:
    repo = GitRepo(repo_root, git_ref=WORKTREE_REF)
    output = str(repo.run("log", "--date=short", "--pretty=format:%h|%ad|%s", f"-n{limit}")).strip()
    lines = [
        "# Chronology",
        "",
        "## Recent Commits",
        "",
        "| Commit | Date | Subject |",
        "| --- | --- | --- |",
    ]
    for entry in output.splitlines():
        commit, date_str, subject = entry.split("|", 2)
        commit_url = f"{build_meta['remote_url']}/commit/{commit}"
        lines.append(f"| [`{commit}`]({commit_url}) | {date_str} | {subject} |")

    dated_artifacts = sorted(
        (
            record
            for record in records
            if re.search(r"20\d{2}-\d{2}-\d{2}|20\d{6}", record.path)
            or re.search(r"20\d{2}-\d{2}-\d{2}|20\d{6}", record.title)
        ),
        key=lambda item: (item.first_seen_date or "", item.path),
    )
    if dated_artifacts:
        lines.extend(["", "## Dated Reports and Research Packs", ""])
        for record in dated_artifacts[:120]:
            lines.append(
                f"- `{record.first_seen_date or record.last_commit_date or ''}` `{record.path}`"
            )

    timeline_sources = [
        record
        for record in records
        if record.path in {"CHANGELOG.md", "CONTEXT.md", "PROGRESS.MD"}
        or record.path.startswith("RELEASE_NOTES/")
    ]
    frontmatter = base_frontmatter(
        title="Chronology",
        kb_kind="timeline_note",
        records=timeline_sources,
        build_meta=build_meta,
    )
    return NoteRecord(
        note_path="40 Timeline and Journal/Chronology.md",
        title="Chronology",
        kb_kind="timeline_note",
        source_paths=sorted({record.path for record in timeline_sources}),
        body=render_frontmatter(frontmatter) + "\n" + "\n".join(lines).rstrip() + "\n",
        frontmatter=frontmatter,
    )


def build_topic_threads_note(records: list[SourceRecord], build_meta: dict[str, Any]) -> NoteRecord:
    frontmatter = base_frontmatter(
        title="Topic Threads",
        kb_kind="timeline_note",
        records=[
            record
            for record in records
            if record.path in {"CHANGELOG.md", "CONTEXT.md", "PROGRESS.MD"}
        ],
        build_meta=build_meta,
    )
    lines = [
        "# Topic Threads",
        "",
        (
            "The groupings below are keyword-based evidence threads. They connect explicit "
            "traces without"
        ),
        "guessing why the work happened.",
        "",
    ]
    for thread, terms in TOPIC_THREADS.items():
        matching = [
            record
            for record in records
            if any(
                term.lower() in f"{record.path} {record.summary} {record.title}".lower()
                for term in terms
            )
        ]
        lines.append(f"## {thread}")
        lines.append("")
        if not matching:
            lines.append("- No current canonical source matched this thread.")
            lines.append("")
            continue
        for record in sorted(
            matching, key=lambda item: (item.last_commit_date or "", item.path), reverse=True
        )[:16]:
            lines.append(
                f"- `{record.last_commit_date or '-'}` `{record.path}`: "
                f"{record.summary or record.title}"
            )
        lines.append("")
    return NoteRecord(
        note_path="40 Timeline and Journal/Topic Threads.md",
        title="Topic Threads",
        kb_kind="timeline_note",
        source_paths=sorted(
            {
                record.path
                for record in records
                if record.path in {"CHANGELOG.md", "CONTEXT.md", "PROGRESS.MD"}
            }
        ),
        body=render_frontmatter(frontmatter) + "\n" + "\n".join(lines).rstrip() + "\n",
        frontmatter=frontmatter,
    )


def build_release_ledger_note(
    records: list[SourceRecord], build_meta: dict[str, Any]
) -> NoteRecord:
    release_records = [record for record in records if record.path.startswith("RELEASE_NOTES/")]
    frontmatter = base_frontmatter(
        title="Release Ledger",
        kb_kind="timeline_note",
        records=release_records or [record for record in records if record.path == "CHANGELOG.md"],
        build_meta=build_meta,
    )
    lines = [
        "# Release Ledger",
        "",
        "| Release Note | First Seen | Pinned Source |",
        "| --- | --- | --- |",
    ]
    for record in sorted(release_records, key=lambda item: item.path):
        lines.append(
            f"| `{record.path}` | {record.first_seen_date or '-'} | [link]({record.source_url}) |"
        )
    return NoteRecord(
        note_path="40 Timeline and Journal/Release Ledger.md",
        title="Release Ledger",
        kb_kind="timeline_note",
        source_paths=sorted({record.path for record in release_records}),
        body=render_frontmatter(frontmatter) + "\n" + "\n".join(lines).rstrip() + "\n",
        frontmatter=frontmatter,
    )


def build_mcp_evolution_note(records: list[SourceRecord], build_meta: dict[str, Any]) -> NoteRecord:
    relevant = [
        record
        for record in records
        if record.path.startswith("docs/spec_package/")
        or record.path.startswith("docs/public_sector_ai_community/")
        or record.path in {"README.md", "CONTEXT.md"}
    ]
    frontmatter = base_frontmatter(
        title="MCP and Host Evolution",
        kb_kind="standards_note",
        records=relevant,
        build_meta=build_meta,
    )
    lines = [
        "# MCP and Host Evolution",
        "",
        "## Canonical Sources",
        "",
    ]
    for record in relevant[:40]:
        lines.append(f"- `{record.path}`: [Pinned source]({record.source_url})")
    lines.extend(
        [
            "",
            "## Repo Interpretation Rules",
            "",
            "- Use tracked documentation and tests as the source of truth for standards handling.",
            (
                "- Treat submodules and vendor mirrors as context, not primary "
                "implementation evidence."
            ),
            (
                "- Record host/client behaviors only when they are reflected in tracked "
                "docs, tests, or reports."
            ),
        ]
    )
    return NoteRecord(
        note_path="50 Standards and Ecosystem/MCP and Host Evolution.md",
        title="MCP and Host Evolution",
        kb_kind="standards_note",
        source_paths=sorted({record.path for record in relevant}),
        body=render_frontmatter(frontmatter) + "\n" + "\n".join(lines).rstrip() + "\n",
        frontmatter=frontmatter,
    )


def build_maintenance_notes(
    records: list[SourceRecord], build_meta: dict[str, Any]
) -> list[NoteRecord]:
    skills_records = [record for record in records if record.path.startswith("skills/")]
    workflow_sources = [
        record
        for record in records
        if record.path
        in {
            "README.md",
            "AGENTS.md",
            "CONTEXT.md",
            "PROGRESS.MD",
            "CHANGELOG.md",
            "scripts/build_obsidian_kb.py",
            "scripts/validate_obsidian_kb.py",
        }
    ]
    skills_note = (
        build_group_note(
            "60 Skills and Maintenance/Repository Skills.md", skills_records, build_meta
        )
        if skills_records
        else None
    )
    maintenance_workflow = NoteRecord(
        note_path="60 Skills and Maintenance/Maintenance Workflow.md",
        title="Maintenance Workflow",
        kb_kind="maintenance_note",
        source_paths=sorted({record.path for record in workflow_sources}),
        frontmatter=base_frontmatter(
            title="Maintenance Workflow",
            kb_kind="maintenance_note",
            records=workflow_sources,
            build_meta=build_meta,
        ),
        body="",
    )
    workflow_lines = [
        "# Maintenance Workflow",
        "",
        "1. Refresh the canonical vault with `scripts/build_obsidian_kb.py --mode canon`.",
        "2. Refresh the local overlay only when local traces are needed.",
        "3. Run `scripts/validate_obsidian_kb.py` against the canonical manifest.",
        "4. Update repo tracking docs when the KB work introduces a new maintained surface.",
    ]
    maintenance_workflow.body = (
        render_frontmatter(maintenance_workflow.frontmatter)
        + "\n"
        + "\n".join(workflow_lines).rstrip()
        + "\n"
    )
    kb_records = [
        record
        for record in records
        if record.path in {"scripts/build_obsidian_kb.py", "scripts/validate_obsidian_kb.py"}
    ]
    kb_note = build_group_note(
        "60 Skills and Maintenance/Knowledge Base Maintenance.md",
        kb_records,
        build_meta,
    )
    notes = [maintenance_workflow, kb_note]
    if skills_note is not None:
        notes.insert(0, skills_note)
    return notes


def build_overlay_notes(
    repo_root: Path, build_meta: dict[str, Any]
) -> tuple[list[NoteRecord], dict[str, Any]]:
    overlay_root = repo_root / "logs"
    overlay_notes: list[NoteRecord] = []
    source_paths: list[str] = []
    if not overlay_root.exists():
        return overlay_notes, {"source_paths": source_paths, "session_count": 0, "log_files": 0}

    session_dirs = (
        sorted(path for path in (overlay_root / "sessions").glob("*") if path.is_dir())
        if (overlay_root / "sessions").exists()
        else []
    )
    log_files = sorted(path for path in overlay_root.glob("*.jsonl"))
    readme_frontmatter = {
        "title": "Local Overlay",
        "kb_kind": "overlay_hub",
        "source_paths": [path.relative_to(repo_root).as_posix() for path in log_files]
        + [path.relative_to(repo_root).as_posix() for path in session_dirs],
        "source_commit": build_meta["source_commit"],
        "source_commit_dirty": build_meta.get("source_commit_dirty", False),
        "source_urls": [],
        "source_hashes": {},
        "generated_at": build_meta["generated_at"],
        "evidence_scope": "overlay",
        "first_seen_date": "",
        "last_validated_at": build_meta["generated_at"],
    }
    lines = [
        "# Local Overlay",
        "",
        "- This subtree is machine-local and ignored by git.",
        (
            "- Sources come from `logs/` and other local traces, not from the canonical "
            "tracked inventory."
        ),
        f"- Session directories discovered: {len(session_dirs)}",
        f"- Root JSONL logs discovered: {len(log_files)}",
    ]
    overlay_notes.append(
        NoteRecord(
            note_path=f"{OVERLAY_SUBDIR}/98 - Local Overlay.md",
            title="Local Overlay",
            kb_kind="overlay_hub",
            source_paths=readme_frontmatter["source_paths"],
            body=render_frontmatter(readme_frontmatter) + "\n" + "\n".join(lines).rstrip() + "\n",
            frontmatter=readme_frontmatter,
        )
    )
    source_paths.extend(readme_frontmatter["source_paths"])

    for session_dir in session_dirs[:64]:
        rel_session = session_dir.relative_to(repo_root).as_posix()
        session_files = sorted(path.name for path in session_dir.iterdir() if path.is_file())
        frontmatter = {
            "title": session_dir.name,
            "kb_kind": "overlay_session",
            "source_paths": [rel_session],
            "source_commit": build_meta["source_commit"],
            "source_commit_dirty": build_meta.get("source_commit_dirty", False),
            "source_urls": [],
            "source_hashes": {},
            "generated_at": build_meta["generated_at"],
            "evidence_scope": "overlay",
            "first_seen_date": "",
            "last_validated_at": build_meta["generated_at"],
        }
        body_lines = [
            f"# {session_dir.name}",
            "",
            f"- Session directory: `{rel_session}`",
            f"- File count: {len(session_files)}",
            "",
            "## Files",
            "",
        ]
        for filename in session_files:
            body_lines.append(f"- `{filename}`")
        overlay_notes.append(
            NoteRecord(
                note_path=f"{OVERLAY_SUBDIR}/Sessions/{session_dir.name}.md",
                title=session_dir.name,
                kb_kind="overlay_session",
                source_paths=[rel_session],
                body=render_frontmatter(frontmatter) + "\n" + "\n".join(body_lines).rstrip() + "\n",
                frontmatter=frontmatter,
            )
        )
        source_paths.append(rel_session)
    return overlay_notes, {
        "source_paths": sorted(set(source_paths)),
        "session_count": len(session_dirs),
        "log_files": len(log_files),
    }


def build_obsidian_notes(
    repo_root: Path, git_ref: str = WORKTREE_REF
) -> tuple[list[NoteRecord], dict[str, Any], list[SourceRecord]]:
    repo = GitRepo(repo_root, git_ref=git_ref)
    records = collect_sources(repo_root, git_ref=git_ref)
    build_meta = {
        "generated_at": utc_now(),
        "source_commit": repo.resolve_ref(),
        "source_commit_dirty": repo.is_dirty() if git_ref == WORKTREE_REF else False,
        "evidence_scope": "canon",
        "remote_url": repo.remote_https_url(),
        "git_ref": git_ref,
        "hard_exclusions": list(HARD_EXCLUSIONS),
    }
    grouped: dict[str, list[SourceRecord]] = defaultdict(list)
    for record in records:
        grouped[record.note_path].append(record)

    notes: list[NoteRecord] = [
        build_home_note(records, build_meta),
        *build_repository_map_notes(records, build_meta),
        build_code_hub(records, build_meta),
        build_docs_hub(records, build_meta),
        build_timeline_hub(records, build_meta),
        build_standards_hub(records, build_meta),
        build_maintenance_hub(records, build_meta),
        build_assets_note(build_meta),
        build_chronology_note(repo_root, records, build_meta),
        build_topic_threads_note(records, build_meta),
        build_release_ledger_note(records, build_meta),
        build_mcp_evolution_note(records, build_meta),
        *build_maintenance_notes(records, build_meta),
    ]

    emitted = {note.note_path for note in notes}
    for note_path, group_records in sorted(grouped.items()):
        if note_path in emitted:
            continue
        notes.append(build_group_note(note_path, group_records, build_meta))
    return notes, build_meta, records


def ensure_obsidian_defaults(output_root: Path) -> None:
    obsidian_root = output_root / ".obsidian"
    obsidian_root.mkdir(parents=True, exist_ok=True)
    defaults = {
        "app.json": {},
        "appearance.json": {"theme": "system", "baseFontSize": 16},
        "core-plugins.json": ["file-explorer", "search", "backlink"],
        "workspace.json": {},
    }
    for filename, payload in defaults.items():
        path = obsidian_root / filename
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_notes(output_root: Path, notes: list[NoteRecord]) -> None:
    for note in notes:
        note_path = output_root / note.note_path
        note_path.parent.mkdir(parents=True, exist_ok=True)
        note_path.write_text(note.body, encoding="utf-8")


def build_manifest(
    repo_root: Path,
    output_root: Path,
    build_meta: dict[str, Any],
    records: list[SourceRecord],
    notes: list[NoteRecord],
    *,
    mode: str,
    overlay_manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source_index = {
        record.path: {
            "category": record.category,
            "note_path": record.note_path,
            "kb_kind": record.kb_kind,
            "sha256": record.sha256,
            "size_bytes": record.size_bytes,
            "is_binary": record.is_binary,
            "first_seen_date": record.first_seen_date,
            "last_commit_date": record.last_commit_date,
            "source_url": record.source_url,
            "summary": record.summary,
            "headings": record.headings,
            "tests": record.tests,
        }
        for record in records
    }
    note_index = {
        note.note_path: {
            "title": note.title,
            "kb_kind": note.kb_kind,
            "source_paths": note.source_paths,
        }
        for note in notes
    }
    return {
        "schema_version": 1,
        "mode": mode,
        "repo_root": str(repo_root),
        "output_root": str(output_root),
        "source_commit": build_meta["source_commit"],
        "source_commit_dirty": build_meta.get("source_commit_dirty", False),
        "git_ref": build_meta.get("git_ref", WORKTREE_REF),
        "generated_at": build_meta["generated_at"],
        "evidence_scope": build_meta["evidence_scope"],
        "remote_url": build_meta["remote_url"],
        "exclusions": list(build_meta.get("hard_exclusions", HARD_EXCLUSIONS)),
        "source_index": source_index,
        "note_index": note_index,
        "stats": {
            "source_count": len(records),
            "note_count": len(notes),
            "category_counts": dict(Counter(record.category for record in records)),
            "kb_kind_counts": dict(Counter(note.kb_kind for note in notes)),
        },
        "overlay": overlay_manifest or None,
    }


def write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def reset_output_root(output_root: Path) -> None:
    if output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)


def build_vault(
    repo_root: Path,
    *,
    mode: str = "canon",
    git_ref: str = WORKTREE_REF,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
    include_local_evidence: bool = False,
    overlay_manifest_path: Path = DEFAULT_OVERLAY_MANIFEST_PATH,
) -> dict[str, Any]:
    output_root = output_root.resolve()
    if mode not in {"canon", "overlay", "all"}:
        raise ValueError(f"Unsupported mode: {mode}")
    overlay_info: dict[str, Any] | None = None

    if mode in {"canon", "all"}:
        notes, build_meta, records = build_obsidian_notes(repo_root, git_ref=git_ref)
        reset_output_root(output_root)
        ensure_obsidian_defaults(output_root)
        write_notes(output_root, notes)
        manifest = build_manifest(
            repo_root,
            output_root,
            build_meta,
            records,
            notes,
            mode=mode,
        )
        write_manifest(manifest_path, manifest)
    else:
        if not output_root.exists():
            output_root.mkdir(parents=True, exist_ok=True)
            ensure_obsidian_defaults(output_root)
        repo = GitRepo(repo_root, git_ref=WORKTREE_REF)
        build_meta = {
            "generated_at": utc_now(),
            "source_commit": repo.resolve_ref(),
            "source_commit_dirty": repo.is_dirty(),
            "evidence_scope": "overlay",
            "remote_url": repo.remote_https_url(),
            "git_ref": WORKTREE_REF,
            "hard_exclusions": list(HARD_EXCLUSIONS),
        }
        manifest = {
            "schema_version": 1,
            "mode": mode,
            "repo_root": str(repo_root),
            "output_root": str(output_root),
            "source_commit": build_meta["source_commit"],
            "source_commit_dirty": build_meta["source_commit_dirty"],
            "git_ref": WORKTREE_REF,
            "generated_at": build_meta["generated_at"],
            "evidence_scope": "overlay",
            "remote_url": build_meta["remote_url"],
            "exclusions": list(HARD_EXCLUSIONS),
            "source_index": {},
            "note_index": {},
            "stats": {
                "source_count": 0,
                "note_count": 0,
                "category_counts": {},
                "kb_kind_counts": {},
            },
            "overlay": None,
        }

    if mode in {"overlay", "all"}:
        if include_local_evidence:
            overlay_notes, overlay_info = build_overlay_notes(repo_root, build_meta)
            if overlay_notes:
                write_notes(output_root, overlay_notes)
            write_manifest(
                overlay_manifest_path,
                {
                    "schema_version": 1,
                    "mode": "overlay",
                    "repo_root": str(repo_root),
                    "output_root": str(output_root),
                    "generated_at": build_meta["generated_at"],
                    "source_commit": build_meta["source_commit"],
                    "source_commit_dirty": build_meta["source_commit_dirty"],
                    "overlay": overlay_info,
                    "note_index": {
                        note.note_path: {
                            "title": note.title,
                            "kb_kind": note.kb_kind,
                            "source_paths": note.source_paths,
                        }
                        for note in overlay_notes
                    },
                },
            )
            if mode == "all":
                manifest["overlay"] = overlay_info
                write_manifest(manifest_path, manifest)
        else:
            overlay_info = {"source_paths": [], "session_count": 0, "log_files": 0}
            if mode == "all":
                manifest["overlay"] = overlay_info
                write_manifest(manifest_path, manifest)
    return manifest


def validate_manifest(
    repo_root: Path,
    manifest: dict[str, Any],
    *,
    validate_drift: bool = True,
    validate_coverage: bool = True,
    validate_recursion: bool = True,
    validate_orphans: bool = True,
) -> dict[str, list[str]]:
    issues: dict[str, list[str]] = {"drift": [], "coverage": [], "recursion": [], "orphan": []}
    exclusions = manifest.get("exclusions") or []
    source_index: dict[str, Any] = manifest.get("source_index") or {}
    note_index: dict[str, Any] = manifest.get("note_index") or {}

    if validate_recursion:
        if "Obsidian/" not in exclusions:
            issues["recursion"].append("Manifest exclusions do not include Obsidian/.")
        for rel_path in source_index:
            if rel_path.startswith("Obsidian/"):
                issues["recursion"].append(
                    f"Source path incorrectly includes excluded vault content: {rel_path}"
                )

    repo = GitRepo(repo_root, git_ref=WORKTREE_REF)
    tracked_paths = sorted(path for path in repo.tracked_paths() if source_in_scope(path))

    if validate_coverage:
        for rel_path in tracked_paths:
            if rel_path not in source_index:
                issues["coverage"].append(f"Tracked source missing from manifest: {rel_path}")
        for rel_path, payload in source_index.items():
            note_path = payload.get("note_path")
            if note_path not in note_index:
                issues["coverage"].append(
                    f"Manifest source points at unknown note: {rel_path} -> {note_path}"
                )

    if validate_orphans:
        output_root = Path(manifest["output_root"])
        for note_path, payload in note_index.items():
            note_file = output_root / note_path
            if not note_file.exists():
                issues["orphan"].append(f"Manifest note missing on disk: {note_path}")
            for rel_path in payload.get("source_paths") or []:
                if rel_path not in source_index:
                    issues["orphan"].append(
                        f"Note references missing source index entry: {note_path} -> {rel_path}"
                    )

    if validate_drift:
        tracked_set = set(tracked_paths)
        for rel_path in tracked_paths:
            if rel_path not in source_index:
                continue
            try:
                absolute_path = repo_root / rel_path
                if absolute_path.is_dir():
                    current_hash = sha256_hex(rel_path.encode("utf-8"))
                else:
                    current_hash = sha256_hex(absolute_path.read_bytes())
            except FileNotFoundError:
                issues["drift"].append(f"Tracked source missing on disk: {rel_path}")
                continue
            if current_hash != source_index[rel_path].get("sha256"):
                issues["drift"].append(f"Source hash changed since manifest generation: {rel_path}")
        for rel_path in source_index:
            if rel_path not in tracked_set:
                issues["drift"].append(f"Manifest source no longer tracked in repo: {rel_path}")
    return issues


def flatten_issues(issues: dict[str, list[str]]) -> list[str]:
    flattened: list[str] = []
    for category, items in issues.items():
        for item in items:
            flattened.append(f"{category}: {item}")
    return flattened
