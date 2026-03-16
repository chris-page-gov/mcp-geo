from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def _load_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "docx_hygiene.py"
    spec = importlib.util.spec_from_file_location("docx_hygiene", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_docx(
    path: Path,
    *,
    creator: str = "Chris Page",
    modified_by: str = "Chris Page",
    custom_property_name: str = "MSIP_Label_Example",
    body_text: str = "See /Users/crpage/example/file.txt",
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    core = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><dc:title>Sample</dc:title><dc:subject></dc:subject><dc:creator>{creator}</dc:creator><cp:keywords></cp:keywords><dc:description></dc:description><cp:lastModifiedBy>{modified_by}</cp:lastModifiedBy><cp:revision>2</cp:revision><dcterms:created xsi:type="dcterms:W3CDTF">2026-03-16T08:01:00Z</dcterms:created><dcterms:modified xsi:type="dcterms:W3CDTF">2026-03-16T08:01:00Z</dcterms:modified></cp:coreProperties>"""
    custom = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/custom-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"><property fmtid="{{D5CDD505-2E9C-101B-9397-08002B2CF9AE}}" pid="2" name="{custom_property_name}"><vt:lpwstr>true</vt:lpwstr></property></Properties>"""
    document = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>{body_text}</w:t></w:r></w:p></w:body></w:document>"""
    with ZipFile(path, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("docProps/core.xml", core)
        archive.writestr("docProps/custom.xml", custom)
        archive.writestr("word/document.xml", document)


def test_build_report_detects_metadata_and_missing_siblings(tmp_path: Path):
    module = _load_module()
    docx_path = tmp_path / "docs" / "report.docx"
    _write_docx(docx_path)
    (tmp_path / "docs" / "report.md").write_text("# report\n", encoding="utf-8")

    report = module.build_report(tmp_path)
    summary = report["summary"]
    assert summary["public_docx_total"] == 1
    assert summary["missing_md"] == []
    assert summary["missing_pdf"] == ["docs/report.docx"]
    assert summary["unsafe_metadata"] == ["docs/report.docx"]
    assert summary["body_absolute_paths"] == ["docs/report.docx"]


def test_sanitize_docx_metadata_strips_creator_modifier_and_custom_props(tmp_path: Path):
    module = _load_module()
    docx_path = tmp_path / "docs" / "report.docx"
    _write_docx(docx_path)

    changed = module.sanitize_docx_metadata(docx_path)
    assert changed is True

    with ZipFile(docx_path) as archive:
        core_xml = archive.read("docProps/core.xml").decode("utf-8")
        custom_xml = archive.read("docProps/custom.xml").decode("utf-8")
    assert "<dc:creator></dc:creator>" in core_xml
    assert "<cp:lastModifiedBy></cp:lastModifiedBy>" in core_xml
    assert custom_xml.strip().endswith("/>")


def test_cli_scan_writes_json_and_markdown_reports(tmp_path: Path, monkeypatch):
    module = _load_module()
    docx_path = tmp_path / "troubleshooting" / "note.docx"
    _write_docx(docx_path, body_text="No path leak here")
    json_path = tmp_path / "out.json"
    md_path = tmp_path / "out.md"

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "sys.argv",
        [
            "docx_hygiene.py",
            "scan",
            "--root",
            str(tmp_path),
            "--json-output",
            str(json_path),
            "--markdown-output",
            str(md_path),
        ],
    )
    assert module.main() == 0
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["summary"]["public_docx_total"] == 1
    assert md_path.read_text(encoding="utf-8").startswith("# DOCX Hygiene Audit")
