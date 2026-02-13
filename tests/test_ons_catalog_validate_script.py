from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _run_validator(path: Path, extra: list[str] | None = None) -> subprocess.CompletedProcess[str]:
    args = [sys.executable, "scripts/ons_catalog_validate.py", "--input", str(path), "--json"]
    if extra:
        args.extend(extra)
    return subprocess.run(args, capture_output=True, text=True, check=False, cwd=Path(__file__).resolve().parent.parent)


def test_ons_catalog_validate_script_success(tmp_path: Path):
    path = tmp_path / "ons_catalog.json"
    payload = {
        "generatedAt": "2026-02-11T00:00:00Z",
        "source": "test",
        "placeholder": False,
        "items": [
            {
                "id": "dataset-1",
                "title": "Dataset 1",
                "description": "Sample",
                "keywords": ["sample"],
                "state": "published",
                "links": {
                    "editions": {"href": "https://example.test/editions"},
                    "latest_version": {"href": "https://example.test/version/1"},
                    "self": {"href": "https://example.test/datasets/dataset-1"},
                },
            }
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    result = _run_validator(path)
    assert result.returncode == 0
    body = json.loads(result.stdout)
    assert body["ok"] is True
    assert body["items"] == 1


def test_ons_catalog_validate_script_failure(tmp_path: Path):
    path = tmp_path / "ons_catalog.json"
    path.write_text(json.dumps({"placeholder": False, "items": [{}]}), encoding="utf-8")
    result = _run_validator(path)
    assert result.returncode == 1
    body = json.loads(result.stdout)
    assert body["ok"] is False
    assert body["errorCount"] >= 1
