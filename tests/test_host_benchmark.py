from __future__ import annotations

import json
import subprocess
import sys
from argparse import Namespace
from pathlib import Path

import pytest

import scripts.host_benchmark as host_benchmark
from scripts.host_benchmark import load_scenario_pack, score_session, summarize_sessions, write_score_artifacts


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def _request(ts: float, req_id: int, method: str, params: dict | None = None) -> dict:
    return {
        "ts": ts,
        "direction": "client->server",
        "json": {"jsonrpc": "2.0", "id": req_id, "method": method, "params": params or {}},
    }


def _response(ts: float, req_id: int, result: dict) -> dict:
    return {
        "ts": ts,
        "direction": "server->client",
        "json": {"jsonrpc": "2.0", "id": req_id, "result": result},
    }


def _make_session_dir(tmp_path: Path, name: str, metadata: dict, trace_rows: list[dict], ui_events: list[dict] | None = None) -> Path:
    session_dir = tmp_path / name
    session_dir.mkdir()
    (session_dir / "session.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    _write_jsonl(session_dir / "mcp-stdio-trace.jsonl", trace_rows)
    if ui_events is not None:
        _write_jsonl(session_dir / "ui-events.jsonl", ui_events)
    return session_dir


def test_scenario_pack_matches_evaluation_questions() -> None:
    pack = load_scenario_pack()
    assert pack["id"] == "codex_vs_claude_host_v1"
    scenario_ids = {scenario["id"] for scenario in pack["scenarios"]}
    assert {
        "address_lookup_postcode",
        "tool_search_postcode",
        "geography_selector_widget",
        "boundary_explorer_widget",
    } <= scenario_ids


def test_score_session_classifies_fallback_only_cli_run(tmp_path: Path) -> None:
    pack = load_scenario_pack()
    scenario = next(s for s in pack["scenarios"] if s["id"] == "geography_selector_widget")
    session_dir = _make_session_dir(
        tmp_path,
        "codex-cli-fallback",
        {
            "sessionId": "codex-cli-fallback",
            "mode": "stdio",
            "source": "codex",
            "surface": "cli",
            "hostProfile": "codex_cli_stdio",
            "scenarioId": scenario["id"],
            "scenarioPack": pack["id"],
        },
        [
            _request(1.0, 1, "initialize", {"capabilities": {}}),
            _response(1.1, 1, {"protocolVersion": "2025-11-25"}),
            _request(1.2, 2, "tools/list", {"query": "postcode", "limit": 5}),
            _response(1.3, 2, {"tools": [{"name": "os_places_by_postcode"}]}),
            _request(1.4, 3, "tools/call", {"name": "os_mcp_route_query", "arguments": {"query": scenario["prompt"]}}),
            _response(1.5, 3, {"ok": True, "data": {"recommended_tool": "os_apps.render_geography_selector"}}),
            _request(1.6, 4, "tools/call", {"name": "os_apps_render_geography_selector", "arguments": {}}),
            _response(
                1.8,
                4,
                {
                    "ok": True,
                    "data": {
                        "tool": "os_apps.render_geography_selector",
                        "fallback": {"type": "static_map", "widgetUnsupported": True},
                    },
                },
            ),
        ],
    )

    evidence, score = score_session(session_dir, scenario)
    write_score_artifacts(session_dir, evidence, score)

    assert evidence["toolSearchUsage"] == "supported"
    assert evidence["fallbackCount"] == 1
    assert score["categories"]["fallbackBehavior"]["status"] == "pass"
    assert score["categories"]["resourcesRead"]["status"] == "pass"
    assert score["categories"]["mcpAppsRuntime"]["status"] == "pass"


def test_score_session_classifies_ui_runtime_and_resources(tmp_path: Path) -> None:
    pack = load_scenario_pack()
    scenario = next(s for s in pack["scenarios"] if s["id"] == "geography_selector_widget")
    session_dir = _make_session_dir(
        tmp_path,
        "codex-ide-ui",
        {
            "sessionId": "codex-ide-ui",
            "mode": "stdio",
            "source": "codex",
            "surface": "ide",
            "hostProfile": "codex_ide_ui",
            "scenarioId": scenario["id"],
            "scenarioPack": pack["id"],
        },
        [
            _request(1.0, 1, "initialize", {"capabilities": {"extensions": {"io.modelcontextprotocol/ui": {}}}}),
            _response(1.1, 1, {"protocolVersion": "2025-11-25"}),
            _request(1.2, 2, "tools/call", {"name": "os_apps_render_geography_selector", "arguments": {}}),
            _response(
                1.3,
                2,
                {
                    "ok": True,
                    "data": {"tool": "os_apps.render_geography_selector"},
                    "content": [{"type": "resource_link", "uri": "ui://mcp-geo/geography-selector"}],
                },
            ),
            _request(1.4, 3, "resources/read", {"uri": "ui://mcp-geo/geography-selector"}),
            _response(1.5, 3, {"contents": [{"uri": "ui://mcp-geo/geography-selector", "mimeType": "text/html"}]}),
            _request(1.6, 4, "tools/call", {"name": "os_apps_log_event", "arguments": {"eventType": "host_ready"}}),
            _response(1.7, 4, {"ok": True, "data": {"status": "logged"}}),
        ],
        ui_events=[
            {"timestamp": 1.65, "eventType": "host_ready", "source": "geography-selector"}
        ],
    )

    evidence, score = score_session(session_dir, scenario)

    assert evidence["resourceReads"] == ["ui://mcp-geo/geography-selector"]
    assert evidence["uiEventCount"] == 1
    assert score["categories"]["resourcesRead"]["status"] == "pass"
    assert score["categories"]["mcpAppsRuntime"]["status"] == "pass"
    assert score["categories"]["fallbackBehavior"]["status"] == "pass"


def test_score_session_penalizes_unrecovered_but_normalized_error(tmp_path: Path) -> None:
    pack = load_scenario_pack()
    scenario = next(s for s in pack["scenarios"] if s["id"] == "boundary_not_found_recovery")
    session_dir = _make_session_dir(
        tmp_path,
        "normalized-error-no-recovery",
        {
            "sessionId": "normalized-error-no-recovery",
            "mode": "stdio",
            "source": "codex",
            "surface": "cli",
            "hostProfile": "codex_cli_stdio",
            "scenarioId": scenario["id"],
            "scenarioPack": pack["id"],
        },
        [
            _request(1.0, 1, "initialize", {"capabilities": {}}),
            _response(1.1, 1, {"protocolVersion": "2025-11-25"}),
            _request(1.2, 2, "tools/call", {"name": "admin_lookup_area_geometry", "arguments": {"id": "bad"}}),
            {
                "ts": 1.3,
                "direction": "server->client",
                "json": {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "result": {
                        "isError": True,
                        "code": "NOT_FOUND",
                        "message": "Area not found",
                    },
                },
            },
        ],
    )

    _evidence, score = score_session(session_dir, scenario)

    assert score["categories"]["errorRecovery"]["status"] == "partial"
    assert score["categories"]["errorRecovery"]["score"] == 0.5
    assert score["categories"]["errorRecovery"]["detail"] == "normalized error observed without recovery"


def test_score_session_fails_unnormalized_error(tmp_path: Path) -> None:
    pack = load_scenario_pack()
    scenario = next(s for s in pack["scenarios"] if s["id"] == "boundary_not_found_recovery")
    session_dir = _make_session_dir(
        tmp_path,
        "unnormalized-error",
        {
            "sessionId": "unnormalized-error",
            "mode": "stdio",
            "source": "claude",
            "surface": "desktop",
            "hostProfile": "claude_desktop_ui_partial",
            "scenarioId": scenario["id"],
            "scenarioPack": pack["id"],
        },
        [
            _request(1.0, 1, "initialize", {"capabilities": {}}),
            _response(1.1, 1, {"protocolVersion": "2025-11-25"}),
            _request(1.2, 2, "tools/call", {"name": "admin_lookup_area_geometry", "arguments": {"id": "bad"}}),
            {
                "ts": 1.3,
                "direction": "server->client",
                "json": {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "result": {
                        "isError": True,
                        "message": "Unhandled failure",
                    },
                },
            },
        ],
    )

    _evidence, score = score_session(session_dir, scenario)

    assert score["categories"]["errorRecovery"]["status"] == "fail"
    assert score["categories"]["errorRecovery"]["score"] == 0.0
    assert score["categories"]["errorRecovery"]["detail"] == "unnormalized error observed"


def test_score_session_requires_expected_method_signals(tmp_path: Path) -> None:
    pack = load_scenario_pack()
    scenario = next(s for s in pack["scenarios"] if s["id"] == "tool_search_postcode")
    session_dir = _make_session_dir(
        tmp_path,
        "tool-search-missing-method",
        {
            "sessionId": "tool-search-missing-method",
            "mode": "stdio",
            "source": "codex",
            "surface": "cli",
            "hostProfile": "codex_cli_stdio",
            "scenarioId": scenario["id"],
            "scenarioPack": pack["id"],
        },
        [
            _request(1.0, 1, "initialize", {"capabilities": {}}),
            _response(1.1, 1, {"protocolVersion": "2025-11-25"}),
            _request(1.2, 2, "tools/list", {"limit": 5}),
            _response(1.3, 2, {"tools": [{"name": "os_places_by_postcode"}]}),
        ],
    )

    evidence, score = score_session(session_dir, scenario)

    assert evidence["toolSearchUsage"] == "unused"
    assert score["categories"]["toolSelection"]["status"] == "fail"
    assert score["categories"]["toolSelection"]["score"] == 0.0
    assert score["categories"]["toolSelection"]["matchedMethods"] == []
    assert score["categories"]["toolSelection"]["expectedMethods"] == ["tools/search"]


def test_build_temp_stdio_server_keeps_host_ui_event_path_for_codex_wrapper(tmp_path: Path) -> None:
    session_dir = tmp_path / "logs" / "sessions" / "trace"
    session_dir.mkdir(parents=True)

    server = host_benchmark._build_temp_stdio_server(
        session_dir,
        wrapper=Path("/tmp/codex-mcp-local"),
        inherited_env={"MCP_GEO_LOG_DIR": str(tmp_path / "logs")},
    )

    assert server["env"]["UI_EVENT_LOG_PATH"] == str(session_dir / "ui-events.jsonl")
    assert (
        server["env"]["MCP_GEO_DOCKER_UI_EVENT_LOG_PATH"]
        == "/logs/sessions/trace/ui-events.jsonl"
    )


def test_run_codex_cli_refuses_to_clobber_non_stdio_server(monkeypatch, tmp_path: Path) -> None:
    removed: list[str] = []
    added: list[tuple[str, dict]] = []

    monkeypatch.setattr(host_benchmark, "_codex_get_server", lambda _name: {"transport": {"type": "http", "url": "http://127.0.0.1:8000/mcp"}})
    monkeypatch.setattr(host_benchmark, "_codex_remove_server", lambda name: removed.append(name))
    monkeypatch.setattr(host_benchmark, "_codex_add_stdio_server", lambda name, config: added.append((name, config)))
    monkeypatch.setattr(host_benchmark, "_codex_client_version", lambda: "codex-cli test")

    args = Namespace(
        scenario_id="tool_search_postcode",
        scenario_pack=str(host_benchmark.DEFAULT_SCENARIO_PACK),
        model="gpt-5.4",
        server_name="mcp-geo",
        wrapper=str(host_benchmark.REPO_ROOT / "scripts" / "codex-mcp-local"),
        session_root=str(tmp_path / "logs" / "sessions"),
        name="non-stdio-guard",
    )

    with pytest.raises(RuntimeError, match="refusing to mutate a non-stdio server config"):
        host_benchmark.cmd_run_codex_cli(args)

    assert removed == []
    assert added == []


def test_summarize_sessions_builds_three_track_report(tmp_path: Path) -> None:
    pack = load_scenario_pack()
    scenario = next(s for s in pack["scenarios"] if s["id"] == "tool_search_postcode")
    base_rows = [
        _request(1.0, 1, "initialize", {"capabilities": {}}),
        _response(1.1, 1, {"protocolVersion": "2025-11-25"}),
        _request(1.2, 2, "tools/search", {"query": "postcode"}),
        _response(1.3, 2, {"tools": [{"name": "os_places_by_postcode"}]}),
    ]
    session_defs = [
        ("codex-cli", "codex", "cli", "codex_cli_stdio"),
        ("codex-ide", "codex", "ide", "codex_ide_ui"),
        ("claude-desktop", "claude", "desktop", "claude_desktop_ui_partial"),
    ]
    session_dirs = []
    for name, source, surface, host_profile in session_defs:
        session_dir = _make_session_dir(
            tmp_path,
            name,
            {
                "sessionId": name,
                "mode": "stdio",
                "source": source,
                "surface": surface,
                "hostProfile": host_profile,
                "scenarioId": scenario["id"],
                "scenarioPack": pack["id"],
            },
            base_rows,
        )
        evidence, score = score_session(session_dir, scenario)
        write_score_artifacts(session_dir, evidence, score)
        session_dirs.append(session_dir)

    aggregate, markdown = summarize_sessions(session_dirs, scenario_pack=pack)

    assert set(aggregate["tracks"].keys()) >= {"codex_cli", "codex_ide", "claude_desktop"}
    assert "Codex CLI" in markdown
    assert "Codex IDE" in markdown
    assert "Claude Desktop" in markdown


def test_host_benchmark_cli_scores_and_summarizes_stored_sessions(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    pack = load_scenario_pack()
    scenario = next(s for s in pack["scenarios"] if s["id"] == "tool_search_postcode")
    session_dir = _make_session_dir(
        tmp_path,
        "codex-cli-cli",
        {
            "sessionId": "codex-cli-cli",
            "mode": "stdio",
            "source": "codex",
            "surface": "cli",
            "hostProfile": "codex_cli_stdio",
            "scenarioId": scenario["id"],
            "scenarioPack": pack["id"],
        },
        [
            _request(1.0, 1, "initialize", {"capabilities": {}}),
            _response(1.1, 1, {"protocolVersion": "2025-11-25"}),
            _request(1.2, 2, "tools/search", {"query": "postcode"}),
            _response(1.3, 2, {"tools": [{"name": "os_places_by_postcode"}]}),
        ],
    )

    subprocess.run(
        [sys.executable, "scripts/host_benchmark.py", "score-session", str(session_dir)],
        cwd=repo_root,
        check=True,
    )
    assert (session_dir / "benchmark-evidence.json").exists()
    assert (session_dir / "benchmark-score.json").exists()

    out_prefix = tmp_path / "codex-vs-claude"
    subprocess.run(
        [
            sys.executable,
            "scripts/host_benchmark.py",
            "summarize",
            str(session_dir),
            "--out-prefix",
            str(out_prefix),
        ],
        cwd=repo_root,
        check=True,
    )

    assert out_prefix.with_suffix(".md").exists()
    assert out_prefix.with_suffix(".json").exists()
