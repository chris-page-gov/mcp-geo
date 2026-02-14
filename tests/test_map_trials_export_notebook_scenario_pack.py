from __future__ import annotations

import json
from pathlib import Path

from scripts.map_trials.export_notebook_scenario_pack import export_scenario_pack


def test_export_scenario_pack_from_markdown_headings(tmp_path: Path) -> None:
    notebook_path = tmp_path / "tracker.ipynb"
    notebook_path.write_text(
        json.dumps(
            {
                "cells": [
                    {"cell_type": "markdown", "source": ["## Static baseline\n", "Details"]},
                    {"cell_type": "markdown", "source": ["## Fallback consistency"]},
                ]
            }
        ),
        encoding="utf-8",
    )
    out_dir = tmp_path / "packs"
    out_path = export_scenario_pack(notebook_path=notebook_path, out_dir=out_dir)
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["packId"] == "tracker"
    assert payload["sourceNotebook"] == str(notebook_path)
    assert payload["hash"].startswith("sha256:")
    scenario_ids = [row["id"] for row in payload["scenarios"]]
    assert "static-baseline" in scenario_ids
    assert "fallback-consistency" in scenario_ids


def test_export_scenario_pack_uses_default_when_no_markdown_headings(tmp_path: Path) -> None:
    notebook_path = tmp_path / "empty.ipynb"
    notebook_path.write_text(json.dumps({"cells": [{"cell_type": "code", "source": ["print(1)"]}]}), encoding="utf-8")
    out_path = export_scenario_pack(notebook_path=notebook_path, out_dir=tmp_path / "packs")
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["scenarios"][0]["id"] == "notebook-default"
