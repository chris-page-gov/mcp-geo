import subprocess
from pathlib import Path

import scripts.generate_mcp_geo_analytical_index as analytical_index
from scripts.generate_mcp_geo_analytical_index import (
    DEFAULT_INPUT,
    REPO_ROOT,
    _appendix_replacement,
    _bundle_markdown,
    _load_json,
    _parse_figures,
    _split_sections,
    _validate_markdown_contract,
    _validate_top_level_entries,
)


def _load_report_and_manifest() -> tuple[dict[str, object], str]:
    manifest = _load_json(DEFAULT_INPUT)
    report_path = REPO_ROOT / Path(manifest["canonical_markdown"])
    return manifest, report_path.read_text(encoding="utf-8")


def test_analytical_index_contract_is_valid() -> None:
    manifest, report = _load_report_and_manifest()
    assert _validate_markdown_contract(report, manifest) == []
    assert _validate_top_level_entries(manifest) == []


def test_appendix_replacement_promotes_appendix_title() -> None:
    _manifest, report = _load_report_and_manifest()
    appendix = _appendix_replacement(report)
    assert appendix.startswith("# Appendix A. Analytical Index to the Public MCP-Geo Repository\n")
    assert "## 1. Reader Orientation" in appendix
    assert "/Users/crpage/Downloads/20260225-AI-Community-MCP-Talk.txt" in appendix


def test_bundle_split_emits_overview_and_appendices() -> None:
    manifest, report = _load_report_and_manifest()
    bundle_markdown = _bundle_markdown(report, _parse_figures(manifest))
    section_titles = [title for title, _chunk in _split_sections(bundle_markdown)]
    assert section_titles[0] == "Overview"
    assert "7. Appendix A. Infographic Prompts" in section_titles
    assert "8. Appendix B. Citation Method and Baseline Replacement Audit" in section_titles


def test_validate_top_level_entries_falls_back_to_head_when_pinned_ref_is_unavailable(
    monkeypatch,
) -> None:
    calls: list[tuple[str, ...]] = []

    def fake_git(*args: str) -> str:
        calls.append(args)
        if args == ("ls-tree", "--name-only", "missing-ref"):
            raise subprocess.CalledProcessError(128, ["git", *args])
        if args == ("ls-tree", "--name-only", "HEAD"):
            return "README.md\nserver\nplayground"
        raise AssertionError(f"Unexpected git args: {args}")

    monkeypatch.setattr(analytical_index, "_git", fake_git)
    errors = _validate_top_level_entries(
        {
            "git_ref": "missing-ref",
            "tracked_top_level_entries": ["README.md", "server", "playground"],
        }
    )
    assert errors == []
    assert calls == [
        ("ls-tree", "--name-only", "missing-ref"),
        ("ls-tree", "--name-only", "HEAD"),
    ]
