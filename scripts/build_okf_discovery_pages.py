#!/usr/bin/env python3
"""Build the key-free GitHub Pages artifact for the OKF discovery demonstrator.

The build uses checked-in inputs only. It never reads environment variables,
credentials, the network, or the current clock. ``--check`` rebuilds into a
temporary directory and compares every path and byte with an existing artifact.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "_site"
PACK_DIR = REPO_ROOT / "resources" / "okf_geo_discovery"
LANDING_TEMPLATE = REPO_ROOT / "pages" / "index.html"
LANDING_STYLES = REPO_ROOT / "pages" / "site.css"
FAVICON = REPO_ROOT / "pages" / "favicon.svg"
DISCOVERY_HTML = REPO_ROOT / "ui" / "okf_discovery.html"
DISCOVERY_STYLES = REPO_ROOT / "ui" / "shared" / "okf_discovery.css"
DISCOVERY_SCRIPT = REPO_ROOT / "ui" / "shared" / "okf_discovery.js"
OVERVIEW_DOCUMENT = (
    REPO_ROOT / "docs" / "work_packages" / "ordnance_survey_okf_mcp_demonstrator_overview.md"
)

PACK_FILES = (
    "descriptor.json",
    "manifest.json",
    "overview.json",
    "records.json",
    "spatial-index.json",
    "mcp-bindings.json",
)

VENDOR_FILES = (
    "maplibre-gl.css",
    "maplibre-gl.js",
    "maplibre-gl-csp-worker.js",
    "maplibre-gl-js.LICENSE.txt",
)

HTML_REWRITES = {
    'href="/ui/vendor/maplibre-gl.css"': 'href="./assets/maplibre-gl.css"',
    'href="/ui/shared/okf_discovery.css"': 'href="./assets/okf_discovery.css"',
    'src="/ui/vendor/maplibre-gl.js"': 'src="./assets/maplibre-gl.js"',
    'src="/ui/shared/okf_discovery.js"': 'src="./assets/okf_discovery.js"',
}


class BuildError(RuntimeError):
    """Raised when checked-in publication inputs are inconsistent."""


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BuildError(f"Could not read JSON input {path.relative_to(REPO_ROOT)}: {exc}") from exc


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _validate_pack() -> dict[str, int]:
    missing = [name for name in PACK_FILES if not (PACK_DIR / name).is_file()]
    if missing:
        raise BuildError(f"OKF pack is incomplete: {', '.join(missing)}")

    descriptor = _read_json(PACK_DIR / "descriptor.json")
    overview = _read_json(PACK_DIR / "overview.json")
    records = _read_json(PACK_DIR / "records.json")
    spatial = _read_json(PACK_DIR / "spatial-index.json")
    bindings = _read_json(PACK_DIR / "mcp-bindings.json")

    if not isinstance(descriptor, dict) or not isinstance(overview, dict):
        raise BuildError("Descriptor and overview must be JSON objects")
    if not isinstance(records, list):
        raise BuildError("records.json must contain a JSON array")
    if not isinstance(spatial, dict) or not isinstance(spatial.get("records"), list):
        raise BuildError("spatial-index.json must contain a records array")
    if not isinstance(bindings, dict) or not isinstance(bindings.get("bindings"), list):
        raise BuildError("mcp-bindings.json must contain a bindings array")

    counts = overview.get("counts")
    if not isinstance(counts, dict):
        raise BuildError("overview.json must contain a counts object")
    expected_counts = {
        "records": len(records),
        "spatial_profiles": len(spatial["records"]),
        "mcp_bindings": len(bindings["bindings"]),
    }
    for name, expected in expected_counts.items():
        if counts.get(name) != expected:
            raise BuildError(
                f"overview count {name} is {counts.get(name)!r}; expected {expected}"
            )

    entrypoints = descriptor.get("entrypoints")
    integrity = descriptor.get("entrypoint_integrity")
    if not isinstance(entrypoints, dict) or not isinstance(integrity, dict):
        raise BuildError("descriptor must contain entrypoints and entrypoint_integrity objects")
    for name, relative_path in entrypoints.items():
        if not isinstance(relative_path, str) or Path(relative_path).name != relative_path:
            raise BuildError(f"descriptor entrypoint {name!r} is not a portable pack filename")
        reference = integrity.get(name)
        if not isinstance(reference, dict) or reference.get("path") != relative_path:
            raise BuildError(f"descriptor integrity entry {name!r} is missing or inconsistent")
        actual = _sha256(PACK_DIR / relative_path)
        if reference.get("sha256") != actual:
            raise BuildError(f"descriptor integrity mismatch for {relative_path}")

    return {name: int(counts[name]) for name in expected_counts}


def _render_landing(counts: dict[str, int]) -> str:
    rendered = LANDING_TEMPLATE.read_text(encoding="utf-8")
    replacements = {
        "{{RECORD_COUNT}}": str(counts["records"]),
        "{{SPATIAL_COUNT}}": str(counts["spatial_profiles"]),
        "{{BINDING_COUNT}}": str(counts["mcp_bindings"]),
    }
    for marker, value in replacements.items():
        if rendered.count(marker) != 1:
            raise BuildError(f"Landing template must contain {marker} exactly once")
        rendered = rendered.replace(marker, value)
    if "{{" in rendered or "}}" in rendered:
        raise BuildError("Landing template contains an unresolved marker")
    return rendered


def _render_discovery_html() -> str:
    rendered = DISCOVERY_HTML.read_text(encoding="utf-8")
    root = '<html lang="en">'
    if rendered.count(root) != 1:
        raise BuildError("Discovery HTML must contain one canonical html root")
    rendered = rendered.replace(root, '<html lang="en" data-static-snapshot="true">', 1)
    title = "    <title>OS data discovery — OKF + MCP demonstrator</title>"
    if rendered.count(title) != 1:
        raise BuildError("Discovery HTML must contain the canonical title")
    rendered = rendered.replace(
        title,
        title + '\n    <link rel="icon" href="../favicon.svg" type="image/svg+xml" />',
        1,
    )
    for source, destination in HTML_REWRITES.items():
        if rendered.count(source) != 1:
            raise BuildError(f"Discovery HTML must contain {source!r} exactly once")
        rendered = rendered.replace(source, destination)
    if 'href="/ui/' in rendered or 'src="/ui/' in rendered:
        raise BuildError("Discovery HTML still contains server-root UI asset paths")
    return rendered


def build_site(output_dir: Path) -> None:
    """Create a fresh deterministic Pages artifact at ``output_dir``."""

    output_dir = output_dir.resolve()
    forbidden = {
        Path("/"),
        Path.home().resolve(),
        REPO_ROOT.resolve(),
        (REPO_ROOT / ".git").resolve(),
    }
    if output_dir in forbidden or (REPO_ROOT / ".git").resolve() in output_dir.parents:
        raise BuildError("Refusing to replace an unsafe output directory")
    if output_dir.exists():
        shutil.rmtree(output_dir)

    counts = _validate_pack()
    discovery_dir = output_dir / "discovery"
    assets_dir = discovery_dir / "assets"
    data_dir = discovery_dir / "data"
    assets_dir.mkdir(parents=True)
    data_dir.mkdir(parents=True)

    (output_dir / ".nojekyll").write_text("", encoding="utf-8")
    (output_dir / "index.html").write_text(_render_landing(counts), encoding="utf-8")
    shutil.copyfile(LANDING_STYLES, output_dir / "site.css")
    shutil.copyfile(FAVICON, output_dir / "favicon.svg")
    shutil.copyfile(OVERVIEW_DOCUMENT, output_dir / "overview.md")
    (discovery_dir / "index.html").write_text(_render_discovery_html(), encoding="utf-8")
    shutil.copyfile(DISCOVERY_STYLES, assets_dir / "okf_discovery.css")
    shutil.copyfile(DISCOVERY_SCRIPT, assets_dir / "okf_discovery.js")

    vendor_dir = REPO_ROOT / "ui" / "vendor"
    for name in VENDOR_FILES:
        shutil.copyfile(vendor_dir / name, assets_dir / name)
    for name in PACK_FILES:
        shutil.copyfile(PACK_DIR / name, data_dir / name)

    symlinks = [path for path in output_dir.rglob("*") if path.is_symlink()]
    if symlinks:
        raise BuildError(f"Generated site contains symlinks: {', '.join(map(str, symlinks))}")


def _tree_bytes(root: Path) -> dict[str, bytes]:
    if not root.is_dir():
        raise BuildError(f"Pages artifact does not exist: {root}")
    files: dict[str, bytes] = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            raise BuildError(f"Pages artifact contains a symlink: {relative}")
        if path.is_file():
            files[relative] = path.read_bytes()
    return files


def check_site(output_dir: Path) -> None:
    """Raise ``BuildError`` when ``output_dir`` differs from a clean rebuild."""

    current = _tree_bytes(output_dir.resolve())
    with tempfile.TemporaryDirectory(dir=REPO_ROOT, prefix=".pages-check-") as temp_root:
        expected_dir = Path(temp_root) / "site"
        build_site(expected_dir)
        expected = _tree_bytes(expected_dir)

    missing = sorted(expected.keys() - current.keys())
    unexpected = sorted(current.keys() - expected.keys())
    changed = sorted(
        path for path in expected.keys() & current.keys() if expected[path] != current[path]
    )
    if missing or unexpected or changed:
        details = []
        if missing:
            details.append(f"missing: {', '.join(missing)}")
        if unexpected:
            details.append(f"unexpected: {', '.join(unexpected)}")
        if changed:
            details.append(f"changed: {', '.join(changed)}")
        raise BuildError("Pages artifact drift detected (" + "; ".join(details) + ")")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Generated site directory (default: %(default)s)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Compare the existing output directory with a clean deterministic rebuild",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.check:
            check_site(args.output_dir)
            print(f"Pages artifact is current: {args.output_dir}")
        else:
            build_site(args.output_dir)
            print(f"Built Pages artifact: {args.output_dir}")
    except BuildError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
