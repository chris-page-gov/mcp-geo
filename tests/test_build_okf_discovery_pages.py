from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import build_okf_discovery_pages as pages


def _build(tmp_path: Path) -> Path:
    output = tmp_path / "site"
    pages.build_site(output)
    return output


def test_pages_build_contains_key_free_static_discovery_surface(tmp_path: Path) -> None:
    output = _build(tmp_path)

    assert (output / ".nojekyll").is_file()
    assert (output / "favicon.svg").is_file()
    assert (output / "overview.md").read_text(encoding="utf-8").startswith(
        "# Ordnance Survey data discovery with OKF and MCP"
    )

    landing = (output / "index.html").read_text(encoding="utf-8")
    assert "Find the data <br />behind the map" in landing
    assert "404" in landing
    assert "210" in landing
    assert "15" in landing
    assert "{{" not in landing
    assert 'href="./discovery/"' in landing

    discovery = (output / "discovery" / "index.html").read_text(encoding="utf-8")
    assert '<html lang="en" data-static-snapshot="true">' in discovery
    assert 'href="./assets/maplibre-gl.css"' in discovery
    assert 'src="./assets/okf_discovery.js"' in discovery
    assert 'href="../favicon.svg"' in discovery
    assert 'href="/ui/' not in discovery
    assert 'src="/ui/' not in discovery

    script = (output / "discovery" / "assets" / "okf_discovery.js").read_text(
        encoding="utf-8"
    )
    public_client_text = discovery + script
    assert "STATIC_SNAPSHOT_MODE" in script
    assert 'STATIC_SNAPSHOT_MODE ? "./data"' in script
    assert "localStorage" not in public_client_text
    assert "sessionStorage" not in public_client_text
    assert 'type="password"' not in public_client_text
    assert "OS_API_KEY_FILE" not in public_client_text


def test_pages_build_copies_complete_consistent_okf_pack(tmp_path: Path) -> None:
    output = _build(tmp_path)
    data_dir = output / "discovery" / "data"

    assert {path.name for path in data_dir.iterdir()} == set(pages.PACK_FILES)
    records = json.loads((data_dir / "records.json").read_text(encoding="utf-8"))
    spatial = json.loads((data_dir / "spatial-index.json").read_text(encoding="utf-8"))
    bindings = json.loads((data_dir / "mcp-bindings.json").read_text(encoding="utf-8"))
    overview = json.loads((data_dir / "overview.json").read_text(encoding="utf-8"))

    assert overview["counts"]["records"] == len(records) == 404
    assert overview["counts"]["spatial_profiles"] == len(spatial["records"]) == 210
    assert overview["counts"]["mcp_bindings"] == len(bindings["bindings"]) == 15
    assert not any(path.is_symlink() for path in output.rglob("*"))


def test_pages_check_detects_and_clears_drift(tmp_path: Path) -> None:
    output = _build(tmp_path)
    pages.check_site(output)

    (output / "index.html").write_text("drift\n", encoding="utf-8")
    with pytest.raises(pages.BuildError, match=r"changed: index\.html"):
        pages.check_site(output)

    pages.build_site(output)
    pages.check_site(output)


def test_pages_builder_refuses_unsafe_output_directory() -> None:
    with pytest.raises(pages.BuildError, match="unsafe output"):
        pages.build_site(pages.REPO_ROOT)
