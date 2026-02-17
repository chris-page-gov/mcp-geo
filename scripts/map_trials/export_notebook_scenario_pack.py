#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _iso_now() -> str:
    return datetime.now(tz=UTC).isoformat().replace("+00:00", "Z")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return f"sha256:{digest}"


def _repo_relative(path: Path, repo_root: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(repo_root))
    except ValueError:
        return str(resolved)


def _extract_scenarios(notebook: dict[str, Any]) -> list[dict[str, str]]:
    scenarios: list[dict[str, str]] = []
    seen: set[str] = set()
    for cell in notebook.get("cells", []):
        if not isinstance(cell, dict):
            continue
        if cell.get("cell_type") != "markdown":
            continue
        source = cell.get("source")
        if isinstance(source, list):
            text = "".join(str(row) for row in source)
        else:
            text = str(source or "")
        for line in text.splitlines():
            line = line.strip()
            if not line.startswith("## "):
                continue
            title = line[3:].strip()
            if not title:
                continue
            scenario_id = (
                title.lower().replace("/", "-").replace(" ", "-").replace("_", "-")
            )
            scenario_id = "".join(ch for ch in scenario_id if ch.isalnum() or ch == "-").strip("-")
            if not scenario_id or scenario_id in seen:
                continue
            seen.add(scenario_id)
            scenarios.append({"id": scenario_id, "title": title, "description": title})
    if scenarios:
        return scenarios
    return [
        {
            "id": "notebook-default",
            "title": "Notebook scenario export",
            "description": "Fallback scenario generated when no markdown headings were found.",
        }
    ]


def export_scenario_pack(*, notebook_path: Path, out_dir: Path) -> Path:
    notebook_obj = json.loads(notebook_path.read_text(encoding="utf-8"))
    notebook_hash = _sha256(notebook_path)
    generated_at = _iso_now()
    scenarios = _extract_scenarios(notebook_obj)
    pack_id = notebook_path.stem.replace(" ", "_")
    repo_root = _repo_root()
    source_notebook = _repo_relative(notebook_path, repo_root)
    payload = {
        "packId": pack_id,
        "sourceNotebook": source_notebook,
        "generatedAt": generated_at,
        "hash": notebook_hash,
        "scenarios": scenarios,
        "provenance": {
            "generator": "scripts/map_trials/export_notebook_scenario_pack.py",
            "sourceNotebookHash": notebook_hash,
        },
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{pack_id}.json"
    out_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    return out_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert notebook-driven map scenarios to a resource-backed scenario pack."
    )
    parser.add_argument(
        "--notebook",
        default=str(
            _repo_root()
            / "research"
            / "map_delivery_research_2026-02"
            / "notebooks"
            / "map_delivery_option_tracker.ipynb"
        ),
        help="Notebook file path.",
    )
    parser.add_argument(
        "--out-dir",
        default=str(_repo_root() / "data" / "map_scenario_packs"),
        help="Scenario pack output directory.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    notebook_path = Path(args.notebook).resolve()
    out_dir = Path(args.out_dir).resolve()
    out_path = export_scenario_pack(notebook_path=notebook_path, out_dir=out_dir)
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
