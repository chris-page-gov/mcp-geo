from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.map_trials.host_simulation_profiles import build_replay_matrix, load_profiles


def test_load_profiles_reads_valid_fixture(tmp_path: Path) -> None:
    fixture = tmp_path / "profiles.json"
    fixture.write_text(
        json.dumps(
            {
                "profiles": [
                    {
                        "id": "ui_supported_inline",
                        "uiSupported": True,
                        "degradationMode": "full_ui",
                        "description": "UI host",
                    },
                    {
                        "id": "ui_unsupported_static",
                        "uiSupported": False,
                        "degradationMode": "no_ui",
                        "description": "No UI host",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    rows = load_profiles(fixture)
    assert [row.profile_id for row in rows] == ["ui_supported_inline", "ui_unsupported_static"]
    assert rows[0].ui_supported is True
    assert rows[1].degradation_mode == "no_ui"


def test_build_replay_matrix_is_deterministic_order(tmp_path: Path) -> None:
    fixture = tmp_path / "profiles.json"
    fixture.write_text(
        json.dumps(
            {
                "profiles": [
                    {"id": "b", "uiSupported": False, "degradationMode": "no_ui"},
                    {"id": "a", "uiSupported": True, "degradationMode": "full_ui"},
                ]
            }
        ),
        encoding="utf-8",
    )
    profiles = load_profiles(fixture)
    matrix = build_replay_matrix(profiles, engines=["chromium-desktop", "webkit-desktop"])
    assert len(matrix) == 4
    assert matrix[0]["engine"] == "chromium-desktop"
    assert matrix[0]["profileId"] == "a"
    assert matrix[1]["profileId"] == "b"
    assert matrix[2]["engine"] == "webkit-desktop"
    assert matrix[2]["profileId"] == "a"


def test_load_profiles_rejects_invalid_fixture(tmp_path: Path) -> None:
    fixture = tmp_path / "profiles.json"
    fixture.write_text(json.dumps({"profiles": []}), encoding="utf-8")
    with pytest.raises(ValueError):
        load_profiles(fixture)


def test_default_fixture_includes_host_benchmark_profiles() -> None:
    fixture = Path("playground/trials/fixtures/host_capability_profiles.json")
    rows = load_profiles(fixture)
    ids = {row.profile_id for row in rows}
    assert {"codex_cli_stdio", "codex_ide_ui", "claude_desktop_ui_partial"} <= ids
