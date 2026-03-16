#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path
from xml.etree import ElementTree
from zipfile import ZIP_DEFLATED, ZipFile

CORE_PROPS_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><dc:title>{title}</dc:title><dc:subject>{subject}</dc:subject><dc:creator></dc:creator><cp:keywords>{keywords}</cp:keywords><dc:description>{description}</dc:description><cp:lastModifiedBy></cp:lastModifiedBy><cp:revision>{revision}</cp:revision><dcterms:created xsi:type="dcterms:W3CDTF">{created}</dcterms:created><dcterms:modified xsi:type="dcterms:W3CDTF">{modified}</dcterms:modified></cp:coreProperties>"""

EMPTY_CUSTOM_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/custom-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"/>"""

ABSOLUTE_PATH_PATTERNS = [
    re.compile(r"(?<![A-Za-z0-9:/])/(?:[^<\s`)\]\"]+/)+[^<\s`)\]\"]+"),
    re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:(?:\\|/)(?:[^<\s`)\]\"]+(?:\\|/))+[^<\s`)\]\"]+"),
]

EXCLUDED_ROOTS = {"data", "submodules"}
EXCLUDED_PARTS = {("docs", "vendor")}
PUBLIC_DOC_DIRS = ("docs", "troubleshooting")


@dataclass
class DocxRecord:
    path: str
    has_md: bool
    has_pdf: bool
    creator: str
    last_modified_by: str
    custom_properties: list[str]
    body_absolute_paths: list[str]


def _is_lockfile(path: Path) -> bool:
    return path.name.startswith("~$")


def _is_excluded(path: Path, root: Path) -> bool:
    relative = path.relative_to(root)
    if not relative.parts:
        return False
    if relative.parts[0] in EXCLUDED_ROOTS:
        return True
    return any(relative.parts[: len(parts)] == parts for parts in EXCLUDED_PARTS)


def _is_public_doc(path: Path, root: Path) -> bool:
    relative = path.relative_to(root)
    return bool(relative.parts) and relative.parts[0] in PUBLIC_DOC_DIRS


def _read_zip_text(docx_path: Path, member: str) -> str:
    with ZipFile(docx_path) as archive:
        if member not in archive.namelist():
            return ""
        return archive.read(member).decode("utf-8", errors="ignore")


def _extract_tag(xml_text: str, tag: str) -> str:
    match = re.search(fr"<{tag}[^>]*>(.*?)</{tag}>", xml_text)
    return match.group(1) if match else ""


def _extract_custom_property_names(xml_text: str) -> list[str]:
    return re.findall(r'<property [^>]* name="([^"]+)"', xml_text)


def _extract_body_absolute_paths(xml_text: str) -> list[str]:
    try:
        text = " ".join(text for text in ElementTree.fromstring(xml_text).itertext() if text)
    except ElementTree.ParseError:
        text = xml_text
    hits: set[str] = set()
    for pattern in ABSOLUTE_PATH_PATTERNS:
        hits.update(pattern.findall(text))
    return sorted(hits)


def _matching_sibling(path: Path, root: Path, suffix: str) -> bool:
    return path.with_suffix(suffix).exists()


def build_report(root: Path) -> dict[str, object]:
    docx_paths = sorted(root.rglob("*.docx"))
    lockfiles = [
        str(path.relative_to(root).as_posix())
        for path in docx_paths
        if _is_lockfile(path) and not _is_excluded(path, root)
    ]
    records: list[DocxRecord] = []
    for path in docx_paths:
        if _is_lockfile(path) or _is_excluded(path, root):
            continue
        core_xml = _read_zip_text(path, "docProps/core.xml")
        custom_xml = _read_zip_text(path, "docProps/custom.xml")
        document_xml = _read_zip_text(path, "word/document.xml")
        records.append(
            DocxRecord(
                path=path.relative_to(root).as_posix(),
                has_md=_matching_sibling(path, root, ".md"),
                has_pdf=_matching_sibling(path, root, ".pdf"),
                creator=_extract_tag(core_xml, "dc:creator"),
                last_modified_by=_extract_tag(core_xml, "cp:lastModifiedBy"),
                custom_properties=_extract_custom_property_names(custom_xml),
                body_absolute_paths=_extract_body_absolute_paths(document_xml),
            )
        )
    authored = [record for record in records if _is_public_doc(root / record.path, root)]
    summary = {
        "docx_total": len(records),
        "public_docx_total": len(authored),
        "lockfiles": lockfiles,
        "missing_md": [record.path for record in authored if not record.has_md],
        "missing_pdf": [record.path for record in authored if not record.has_pdf],
        "missing_both": [
            record.path for record in authored if not record.has_md and not record.has_pdf
        ],
        "unsafe_metadata": [
            record.path
            for record in authored
            if record.creator or record.last_modified_by or record.custom_properties
        ],
        "body_absolute_paths": [
            record.path for record in authored if record.body_absolute_paths
        ],
    }
    return {
        "summary": summary,
        "records": [asdict(record) for record in authored],
    }


def render_markdown(report: dict[str, object]) -> str:
    summary = report["summary"]
    records = report["records"]
    lines = [
        "# DOCX Hygiene Audit",
        "",
        f"- Public DOCX files scanned: `{summary['public_docx_total']}`",
        f"- Lockfiles: `{len(summary['lockfiles'])}`",
        f"- Missing `.md`: `{len(summary['missing_md'])}`",
        f"- Missing `.pdf`: `{len(summary['missing_pdf'])}`",
        f"- Missing both: `{len(summary['missing_both'])}`",
        f"- Unsafe metadata: `{len(summary['unsafe_metadata'])}`",
        f"- Body absolute paths: `{len(summary['body_absolute_paths'])}`",
        "",
        "## Public DOCX Records",
        "",
        "| Path | MD | PDF | Metadata | Body paths |",
        "| --- | --- | --- | --- | --- |",
    ]
    for record in records:
        metadata_flag = "yes" if (
            record["creator"] or record["last_modified_by"] or record["custom_properties"]
        ) else "no"
        body_flag = "yes" if record["body_absolute_paths"] else "no"
        lines.append(
            f"| `{record['path']}` | "
            f"`{'yes' if record['has_md'] else 'no'}` | "
            f"`{'yes' if record['has_pdf'] else 'no'}` | "
            f"`{metadata_flag}` | `{body_flag}` |"
        )
    if summary["lockfiles"]:
        lines.extend(["", "## Lockfiles", ""])
        for path in summary["lockfiles"]:
            lines.append(f"- `{path}`")
    return "\n".join(lines) + "\n"


def sanitize_docx_metadata(docx_path: Path) -> bool:
    changed = False
    core_xml = _read_zip_text(docx_path, "docProps/core.xml")
    custom_xml = _read_zip_text(docx_path, "docProps/custom.xml")
    if not core_xml and not custom_xml:
        return False
    title = _extract_tag(core_xml, "dc:title")
    subject = _extract_tag(core_xml, "dc:subject")
    keywords = _extract_tag(core_xml, "cp:keywords")
    description = _extract_tag(core_xml, "dc:description")
    revision = _extract_tag(core_xml, "cp:revision") or "1"
    created = _extract_tag(core_xml, "dcterms:created")
    modified = _extract_tag(core_xml, "dcterms:modified") or created
    sanitized_core = CORE_PROPS_XML.format(
        title=title,
        subject=subject,
        keywords=keywords,
        description=description,
        revision=revision,
        created=created,
        modified=modified,
    )
    if core_xml == sanitized_core and custom_xml == EMPTY_CUSTOM_XML:
        return False
    temp_path = docx_path.with_suffix(docx_path.suffix + ".tmp")
    with ZipFile(docx_path) as source, ZipFile(temp_path, "w", compression=ZIP_DEFLATED) as out:
        for info in source.infolist():
            data = source.read(info.filename)
            if info.filename == "docProps/core.xml":
                data = sanitized_core.encode("utf-8")
                changed = True
            elif info.filename == "docProps/custom.xml":
                data = EMPTY_CUSTOM_XML.encode("utf-8")
                changed = True
            out.writestr(info, data)
    temp_path.replace(docx_path)
    return changed


def iter_public_docx(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*.docx")):
        if _is_lockfile(path) or _is_excluded(path, root):
            continue
        if _is_public_doc(path, root):
            yield path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scan and sanitize DOCX hygiene in this repo.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan = subparsers.add_parser("scan", help="Generate a DOCX hygiene report.")
    scan.add_argument("--root", default=".", help="Repo root to scan.")
    scan.add_argument("--json-output", help="Optional JSON report output path.")
    scan.add_argument("--markdown-output", help="Optional markdown report output path.")
    scan.add_argument("--fail-on-issues", action="store_true", help="Exit 1 if issues exist.")

    sanitize = subparsers.add_parser(
        "sanitize", help="Strip metadata/custom properties from public DOCX files."
    )
    sanitize.add_argument("--root", default=".", help="Repo root to scan.")
    return parser.parse_args()


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    if args.command == "sanitize":
        changed = []
        for path in iter_public_docx(root):
            if sanitize_docx_metadata(path):
                changed.append(path.relative_to(root).as_posix())
        print(json.dumps({"changed": changed}, indent=2))
        return 0

    report = build_report(root)
    payload = json.dumps(report, indent=2) + "\n"
    markdown = render_markdown(report)
    if args.json_output:
        _write_text(Path(args.json_output), payload)
    if args.markdown_output:
        _write_text(Path(args.markdown_output), markdown)
    print(payload, end="")
    if args.fail_on_issues:
        summary = report["summary"]
        issues = (
            summary["lockfiles"]
            or summary["unsafe_metadata"]
            or summary["body_absolute_paths"]
            or summary["missing_md"]
            or summary["missing_pdf"]
        )
        if issues:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
