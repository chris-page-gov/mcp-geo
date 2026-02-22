from __future__ import annotations

from scripts import live_missing_tools_probe as probe


def test_ordered_missing_tools_prioritizes_dependency_sequence() -> None:
    missing = [
        "os_offline.get",
        "os_downloads.get_export",
        "os_downloads.prepare_export",
        "os_offline.descriptor",
    ]
    ordered = probe._ordered_missing_tools(missing)
    assert ordered == [
        "os_downloads.prepare_export",
        "os_downloads.get_export",
        "os_offline.descriptor",
        "os_offline.get",
    ]


def test_classify_auth_and_not_found_outcomes() -> None:
    assert probe._classify(401, {"code": "OS_API_KEY_INVALID"}) == "blocked_auth"
    assert probe._classify(404, {"code": "NOT_FOUND"}) == "data_not_found"
    assert probe._classify(200, {"isError": True, "code": "NO_API_KEY"}) == "blocked_auth"
    assert probe._classify(200, {"ok": True}) == "pass"
