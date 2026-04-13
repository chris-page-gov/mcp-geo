from __future__ import annotations

import json
import subprocess
from pathlib import Path

import scripts.unattended_client_eval as unattended_client_eval


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_run_codex_track_preserves_session_dir_on_runner_failure(
    monkeypatch,
    tmp_path: Path,
) -> None:
    session_root = tmp_path / "logs" / "sessions"
    session_root.mkdir(parents=True)

    def fake_run_codex_cli(args: object) -> int:
        assert args.scenario_id == "tool_search_postcode"  # type: ignore[attr-defined]
        session_dir = session_root / "forced-codex-session"
        session_dir.mkdir()
        _write_json(session_dir / "session.json", {"sessionId": "forced-codex-session"})
        (session_root / ".latest").write_text(str(session_dir), encoding="utf-8")
        raise RuntimeError("codex exec failed with code 1")

    monkeypatch.setattr(
        unattended_client_eval.host_benchmark,
        "cmd_run_codex_cli",
        fake_run_codex_cli,
    )
    monkeypatch.setattr(
        unattended_client_eval,
        "_session_name",
        lambda *_args: "forced-codex-session",
    )

    session_dir, exit_code, blocker = unattended_client_eval._run_codex_track(
        scenario={"id": "tool_search_postcode", "prompt": "Find CV3 1HB"},
        scenario_pack_path=Path("/tmp/scenarios.json"),
        scenario_pack_id="pack-id",
        session_root=session_root,
        model="gpt-5.4",
    )

    assert session_dir == session_root / "forced-codex-session"
    assert exit_code == 1
    assert blocker == "codex exec failed with code 1"
    session_meta = json.loads((session_dir / "session.json").read_text(encoding="utf-8"))
    assert session_meta["scenarioPack"] == "pack-id"
    assert session_meta["scenarioId"] == "tool_search_postcode"
    assert session_meta["runnerError"] == "codex exec failed with code 1"


def test_score_session_reuses_existing_benchmark_artifacts(tmp_path: Path) -> None:
    session_dir = tmp_path / "session"
    session_dir.mkdir()
    expected_evidence = {"toolCalls": ["os_places.search"]}
    expected_score = {"overallScore": 0.75, "overallStatus": "partial"}
    _write_json(session_dir / "benchmark-evidence.json", expected_evidence)
    _write_json(session_dir / "benchmark-score.json", expected_score)

    evidence, score = unattended_client_eval._score_session(
        session_dir,
        {"id": "tool_search_postcode"},
    )

    assert evidence == expected_evidence
    assert score == expected_score


def test_summarize_attempts_reports_blocked_and_scored_tracks() -> None:
    scenario_pack = {
        "id": "pack-id",
        "scenarios": [
            {"id": "tool_search_postcode", "label": "Find postcode tools"},
            {"id": "geography_selector_widget", "label": "Open geography selector"},
        ],
    }
    attempts = [
        {
            "trackId": "codex_cli",
            "scenarioId": "tool_search_postcode",
            "runStatus": "scored",
            "overallScore": 1.0,
            "blocker": None,
            "sessionDir": "/tmp/codex",
        },
        {
            "trackId": "gemini_cli",
            "scenarioId": "tool_search_postcode",
            "runStatus": "runner_error",
            "overallScore": None,
            "diagnosticScore": 0.52,
            "blocker": "gemini_cli_failed",
            "sessionDir": "/tmp/gemini",
        },
        {
            "trackId": "claude_cli",
            "scenarioId": "geography_selector_widget",
            "runStatus": "no_mcp_traffic",
            "overallScore": None,
            "diagnosticScore": 0.36,
            "blocker": "client produced no MCP traffic",
            "sessionDir": "/tmp/claude",
        },
    ]

    aggregate, markdown = unattended_client_eval._summarize_attempts(
        scenario_pack=scenario_pack,
        attempts=attempts,
    )

    assert aggregate["tracks"]["codex_cli"]["scoredCount"] == 1
    assert aggregate["tracks"]["gemini_cli"]["scoredCount"] == 0
    assert aggregate["tracks"]["gemini_cli"]["statuses"] == {"runner_error": 1}
    assert aggregate["tracks"]["claude_cli"]["statuses"] == {"no_mcp_traffic": 1}
    assert "Gemini CLI" in markdown
    assert "runner_error" in markdown
    assert "diagnostic=0.52" in markdown
    assert "Find postcode tools" in markdown


def test_run_gemini_track_times_out_cleanly(monkeypatch, tmp_path: Path) -> None:
    session_root = tmp_path / "logs" / "sessions"
    session_root.mkdir(parents=True)

    monkeypatch.setattr(
        unattended_client_eval.host_benchmark,
        "_build_temp_stdio_server",
        lambda *_args, **_kwargs: {"command": "python", "args": [], "env": {}},
    )
    monkeypatch.setattr(
        unattended_client_eval,
        "_gemini_add_stdio_server",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        unattended_client_eval,
        "_gemini_remove_server",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        unattended_client_eval,
        "_build_inherited_env",
        lambda: {"MCP_GEO_DOCKER_BUILD": "never"},
    )
    monkeypatch.setattr(unattended_client_eval, "_client_version", lambda _command: "gemini test")

    def fake_run(*_args, **_kwargs) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(cmd=["gemini"], timeout=5, output=b"", stderr=b"")

    monkeypatch.setattr(unattended_client_eval.subprocess, "run", fake_run)

    session_dir, exit_code, blocker = unattended_client_eval._run_gemini_track(
        scenario={"id": "address_lookup_postcode", "prompt": "UPRNs for SW1A 1AA"},
        scenario_pack_id="pack-id",
        session_root=session_root,
        model="",
        timeout_sec=5,
    )

    assert exit_code == 124
    assert blocker == "gemini_cli_timeout_after_5s"
    session_meta = json.loads((session_dir / "session.json").read_text(encoding="utf-8"))
    assert session_meta["runnerError"] == "gemini_cli_timeout_after_5s"
    assert (session_dir / "assistant-response.txt").read_text(encoding="utf-8") == ""


def test_run_vscode_track_opens_workspace_before_chat(monkeypatch, tmp_path: Path) -> None:
    session_root = tmp_path / "logs" / "sessions"
    session_root.mkdir(parents=True)
    commands: list[list[str]] = []
    envs: list[dict[str, str] | None] = []
    scenario = {"id": "address_lookup_postcode", "prompt": "UPRNs for SW1A 1AA"}
    expected_prompt = unattended_client_eval._scenario_prompt(scenario)

    def fake_run(
        command: list[str],
        **_kwargs,
    ) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        envs.append(_kwargs.get("env"))
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(unattended_client_eval.subprocess, "run", fake_run)
    monkeypatch.setattr(unattended_client_eval, "_read_lines", lambda _path: [])
    monkeypatch.setattr(unattended_client_eval.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(
        unattended_client_eval,
        "resolved_process_env",
        lambda: {"OS_API_KEY_FILE": "/tmp/os_api_key.txt", "MCP_GEO_DOCKER_BUILD": "never"},
    )

    session_dir, exit_code, blocker = unattended_client_eval._run_vscode_track(
        scenario=scenario,
        scenario_pack_id="pack-id",
        session_root=session_root,
        timeout_sec=1,
    )

    assert session_dir.exists()
    assert exit_code == 0
    assert blocker is None
    assert commands[1:3] == [
        ["code", "--reuse-window", "."],
        ["code", "chat", "--mode", "agent", "--reuse-window", expected_prompt],
    ]
    assert envs[1]["OS_API_KEY_FILE"] == "/tmp/os_api_key.txt"
    assert envs[2]["OS_API_KEY_FILE"] == "/tmp/os_api_key.txt"
