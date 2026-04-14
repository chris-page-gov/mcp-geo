from __future__ import annotations

import json
from pathlib import Path


def test_obsidian_agent_control_smoke_pack_has_expected_shape() -> None:
    path = Path("docs/benchmarking/obsidian_agent_control_smoke_pack_v1.json")
    pack = json.loads(path.read_text(encoding="utf-8"))

    assert pack["id"] == "obsidian_agent_control_smoke_v1"
    assert pack["clients"] == ["codex", "claude", "gemini", "vscode"]
    assert pack["modes"] == ["classic", "obsidian"]

    scenarios = pack["scenarios"]
    scenario_ids = [scenario["id"] for scenario in scenarios]
    assert scenario_ids == [
        "active_profile_discovery",
        "current_focus_lookup",
        "work_queue_lookup",
        "repo_navigation_lookup",
        "update_discipline_behavior",
        "guardrail_adherence",
    ]

    for scenario in scenarios:
        assert scenario["prompt"]
        assert scenario["successConditions"]
        assert set(scenario["modeExpectations"]) == {"classic", "obsidian"}
