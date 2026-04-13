from __future__ import annotations

import json
import subprocess
from pathlib import Path

import scripts.unattended_client_eval as unattended_client_eval


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


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


def test_prepare_gemini_workspace_recreates_stable_root(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(unattended_client_eval, "DEFAULT_WORKSPACE_ROOT", tmp_path / "workspaces")
    task = {"id": "address_lookup_postcode"}
    workspace = unattended_client_eval._prepare_gemini_workspace(task)
    stale = workspace / "stale.txt"
    stale.write_text("old", encoding="utf-8")

    recreated = unattended_client_eval._prepare_gemini_workspace(task)

    assert recreated == workspace
    assert recreated.name == "address-lookup-postcode"
    assert not stale.exists()


def test_prepare_vscode_workspace_recreates_stable_root(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(unattended_client_eval, "DEFAULT_WORKSPACE_ROOT", tmp_path / "workspaces")
    task = {"id": "readiness_probe"}
    workspace = unattended_client_eval._prepare_vscode_workspace(task)
    stale = workspace / "stale.txt"
    stale.write_text("old", encoding="utf-8")

    recreated = unattended_client_eval._prepare_vscode_workspace(task)

    assert recreated == workspace
    assert recreated.name == "readiness-probe"
    assert not stale.exists()


def test_prepare_vscode_workspace_supports_unique_workspace_name(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(unattended_client_eval, "DEFAULT_WORKSPACE_ROOT", tmp_path / "workspaces")

    workspace = unattended_client_eval._prepare_vscode_workspace(
        {"id": "readiness_probe"},
        workspace_name="unique-readiness-probe",
    )

    assert workspace == tmp_path / "workspaces" / "vscode" / "unique-readiness-probe"


def test_write_vscode_workspace_mcp_config_writes_ephemeral_workspace_file(
    monkeypatch, tmp_path: Path
) -> None:
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir(parents=True)
    session_dir = tmp_path / "session"
    session_dir.mkdir(parents=True)

    monkeypatch.setattr(unattended_client_eval, "_build_inherited_env", lambda: {})
    monkeypatch.setattr(
        unattended_client_eval.host_benchmark,
        "_build_temp_stdio_server",
        lambda *_args, **_kwargs: {
            "command": "python",
            "args": ["server.py"],
            "env": {"UI_EVENT_LOG_PATH": str(session_dir / "ui-events.jsonl"), "A": "B"},
        },
    )

    trace_paths, ui_paths = unattended_client_eval._write_vscode_workspace_mcp_config(
        workspace_dir,
        session_dir,
        "mcp-geo-bench-fixed-vscode-session",
    )

    workspace_mcp = json.loads(
        (workspace_dir / ".vscode" / "mcp.json").read_text(encoding="utf-8")
    )
    server = workspace_mcp["servers"]["mcp-geo-bench-fixed-vscode-session"]
    assert server["type"] == "stdio"
    assert server["command"] == "python"
    assert server["args"] == ["server.py"]
    assert server["env"]["A"] == "B"
    assert trace_paths == [session_dir / "mcp-stdio-trace.jsonl"]
    assert ui_paths == [session_dir / "ui-events.jsonl"]


def test_find_vscode_window_for_workspace_matches_name_and_document(
    monkeypatch, tmp_path: Path
) -> None:
    workspace_dir = tmp_path / "benchmark-workspace"
    workspace_dir.mkdir()
    workspace_uri = workspace_dir.resolve().as_uri()
    expected = unattended_client_eval.VSCodeWindow(
        name="benchmark-workspace",
        document=workspace_uri,
    )

    monkeypatch.setattr(
        unattended_client_eval,
        "_list_vscode_windows",
        lambda: [
            unattended_client_eval.VSCodeWindow(name="PROGRESS.MD — mcp-geo", document=""),
            expected,
        ],
    )

    assert unattended_client_eval._find_vscode_window_for_workspace(workspace_dir) == expected


def test_close_vscode_window_confirms_session_dialog(monkeypatch) -> None:
    window = unattended_client_eval.VSCodeWindow(name="benchmark", document="")
    responses = iter(
        [
            subprocess.CompletedProcess(["osascript"], 0, stdout="ok\n", stderr=""),
            subprocess.CompletedProcess(["osascript"], 0, stdout="confirmed\n", stderr=""),
        ]
    )
    windows = iter([[window], []])

    monkeypatch.setattr(
        unattended_client_eval,
        "_run_osascript",
        lambda *_args: next(responses),
    )
    monkeypatch.setattr(
        unattended_client_eval,
        "_list_vscode_windows",
        lambda: next(windows),
    )
    monkeypatch.setattr(unattended_client_eval.time, "sleep", lambda _seconds: None)

    assert unattended_client_eval._close_vscode_window(window) is True


def test_trace_activity_since_distinguishes_startup_from_useful_requests(tmp_path: Path) -> None:
    trace_path = tmp_path / "mcp-stdio-trace.jsonl"
    trace_path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "direction": "client->server",
                        "json": {"id": 1, "method": "initialize", "params": {}},
                    }
                ),
                json.dumps(
                    {
                        "direction": "client->server",
                        "json": {"id": 2, "method": "tools/list", "params": {}},
                    }
                ),
                json.dumps(
                    {
                        "direction": "client->server",
                        "json": {
                            "id": 3,
                            "method": "tools/call",
                            "params": {"name": "os_apps.log_event"},
                        },
                    }
                ),
                json.dumps(
                    {
                        "direction": "client->server",
                        "json": {
                            "id": 4,
                            "method": "tools/call",
                            "params": {"name": "os_resources.get"},
                        },
                    }
                ),
                json.dumps(
                    {
                        "direction": "client->server",
                        "json": {"id": 5, "method": "resources/read", "params": {}},
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    activity = unattended_client_eval._trace_activity_since({trace_path: 0})

    assert activity["requestCount"] == 5
    assert activity["startupRequestCount"] == 2
    assert activity["usefulRequestCount"] == 2
    assert activity["methods"] == [
        "initialize",
        "tools/list",
        "tools/call",
        "tools/call",
        "resources/read",
    ]


def test_cleanup_vscode_workspace_terminates_lingering_workspace_processes(
    monkeypatch, tmp_path: Path
) -> None:
    workspace_dir = tmp_path / "benchmark-workspace"
    workspace_dir.mkdir()
    window = unattended_client_eval.VSCodeWindow(name="benchmark-workspace", document="")

    monkeypatch.setattr(
        unattended_client_eval,
        "_close_vscode_window",
        lambda _window: False,
    )
    monkeypatch.setattr(
        unattended_client_eval,
        "_find_vscode_window_for_workspace",
        lambda _workspace_dir: window,
    )
    monkeypatch.setattr(
        unattended_client_eval,
        "_find_vscode_workspace_process_roots",
        lambda _workspace_dir: [101],
    )
    monkeypatch.setattr(
        unattended_client_eval,
        "_terminate_vscode_workspace_processes",
        lambda _workspace_dir: [101, 202],
    )

    cleanup = unattended_client_eval._cleanup_vscode_workspace(workspace_dir, window)

    assert cleanup == {
        "closeAttempted": True,
        "windowClosed": False,
        "killedProcessPids": [101, 202],
    }


def test_classify_blocker_category_detects_gemini_workspace_restriction(tmp_path: Path) -> None:
    session_dir = tmp_path / "session"
    session_dir.mkdir()
    (session_dir / "assistant-response.txt").write_text("", encoding="utf-8")
    (session_dir / "gemini-exec.stderr.txt").write_text(
        (
            'Error executing tool read_file: Path not in workspace: Attempted path '
            '"/Users/test/.gemini/settings.json" resolves outside the allowed workspace directories'
        ),
        encoding="utf-8",
    )

    category, message = unattended_client_eval._classify_blocker_category(
        track_id="gemini_cli",
        purpose="readiness",
        exit_code=124,
        evidence={"traceSummary": {"mcp": {"requestCount": 0}}, "toolCalls": [], "errorCodes": []},
        runner_blocker="gemini_cli_timeout_after_45s",
        session_dir=session_dir,
    )

    assert category == "client_workspace_restriction"
    assert "~/.gemini/settings.json" in message


def test_classify_blocker_category_detects_claude_auth_failure(tmp_path: Path) -> None:
    session_dir = tmp_path / "session"
    session_dir.mkdir()
    (session_dir / "assistant-response.txt").write_text(
        (
            "Failed to authenticate. API Error: 401 "
            '{"type":"error","error":{"type":"authentication_error"}}'
        ),
        encoding="utf-8",
    )

    category, message = unattended_client_eval._classify_blocker_category(
        track_id="claude_cli",
        purpose="readiness",
        exit_code=1,
        evidence={"traceSummary": {"mcp": {"requestCount": 6}}, "toolCalls": [], "errorCodes": []},
        runner_blocker="claude_cli_failed",
        session_dir=session_dir,
    )

    assert category == "client_auth_failure"
    assert "authentication" in message


def test_run_gemini_track_includes_home_settings_directory(monkeypatch, tmp_path: Path) -> None:
    session_root = tmp_path / "logs" / "sessions"
    session_root.mkdir(parents=True)
    workspaces = tmp_path / "benchmark-workspaces"
    commands: list[list[str]] = []
    cwds: list[Path] = []

    monkeypatch.setattr(unattended_client_eval, "DEFAULT_WORKSPACE_ROOT", workspaces)
    monkeypatch.setattr(
        unattended_client_eval.host_benchmark,
        "_build_temp_stdio_server",
        lambda *_args, **_kwargs: {"command": "python", "args": ["server.py"], "env": {"A": "B"}},
    )
    monkeypatch.setattr(unattended_client_eval, "_build_inherited_env", lambda: {})
    monkeypatch.setattr(unattended_client_eval, "_client_version", lambda _command: "gemini test")

    def fake_run(command: list[str], **kwargs) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        cwds.append(kwargs["cwd"])
        return subprocess.CompletedProcess(command, 0, stdout="{}", stderr="")

    monkeypatch.setattr(unattended_client_eval.subprocess, "run", fake_run)

    session_dir, exit_code, blocker = unattended_client_eval._run_gemini_track(
        task={"id": "address_lookup_postcode", "label": "Address", "prompt": "UPRNs for SW1A 1AA"},
        scenario_pack_id="pack-id",
        session_root=session_root,
        model="",
        timeout_sec=5,
        attempt_kind="capability",
    )

    assert session_dir.exists()
    assert exit_code == 0
    assert blocker is None
    include_dirs = [
        commands[0][idx + 1]
        for idx, token in enumerate(commands[0])
        if token == "--include-directories"
    ]
    assert include_dirs == [str(Path.home() / ".gemini"), str(unattended_client_eval.REPO_ROOT)]
    assert cwds[0] == workspaces / "gemini" / "address-lookup-postcode"
    settings = json.loads(
        (workspaces / "gemini" / "address-lookup-postcode" / ".gemini" / "settings.json").read_text(
            encoding="utf-8"
        )
    )
    server_name = "mcp-geo-benchmark-address-lookup-postcode"
    assert settings["tools"]["core"] == []
    assert settings["mcp"]["allowed"] == [server_name]
    assert settings["mcpServers"][server_name]["command"] == "python"
    policy = (
        workspaces
        / "gemini"
        / "address-lookup-postcode"
        / ".gemini"
        / "policies"
        / "00-mcp-only.toml"
    ).read_text(encoding="utf-8")
    assert 'toolName = "mcp_*"' in policy
    assert 'decision = "deny"' in policy


def test_run_vscode_track_uses_workspace_mcp_config_and_session_window(
    monkeypatch, tmp_path: Path
) -> None:
    session_root = tmp_path / "logs" / "sessions"
    session_root.mkdir(parents=True)
    commands: list[list[str]] = []
    envs: list[dict[str, str] | None] = []
    rewrites: list[tuple[Path, Path, str]] = []
    raised: list[unattended_client_eval.VSCodeWindow] = []
    cleanup_calls: list[tuple[Path, unattended_client_eval.VSCodeWindow | None]] = []
    task = {"id": "address_lookup_postcode", "label": "Address", "prompt": "UPRNs for SW1A 1AA"}
    expected_prompt = unattended_client_eval._task_prompt(
        task,
        track_id="vscode_ide",
        server_name="mcp-geo-bench-fixed-vscode-session",
    )
    workspace_root = tmp_path / "workspaces"
    expected_workspace_dir = workspace_root / "vscode" / "fixed-vscode-session"
    benchmark_window = unattended_client_eval.VSCodeWindow(
        name="fixed-vscode-session",
        document="",
    )
    expected_server_log = tmp_path / "Code" / "logs" / "window25" / "mcpServer.log"

    monkeypatch.setattr(unattended_client_eval, "_client_version", lambda _command: "code test")
    monkeypatch.setattr(
        unattended_client_eval,
        "_session_name",
        lambda _track_id, _task_id: "fixed-vscode-session",
    )
    monkeypatch.setattr(unattended_client_eval, "DEFAULT_WORKSPACE_ROOT", workspace_root)
    monkeypatch.setattr(
        unattended_client_eval,
        "_list_vscode_windows",
        lambda: [unattended_client_eval.VSCodeWindow(name="PROGRESS.MD — mcp-geo", document="")],
    )
    monkeypatch.setattr(
        unattended_client_eval,
        "_wait_for_new_vscode_window",
        lambda _existing, *, workspace_name, timeout_sec=10.0: benchmark_window,
    )

    def fake_write_vscode_workspace_mcp_config(
        workspace_dir: Path,
        session_dir: Path,
        server_name: str,
    ) -> tuple[list[Path], list[Path]]:
        rewrites.append((workspace_dir, session_dir, server_name))
        return ([session_dir / "mcp-stdio-trace.jsonl"], [session_dir / "ui-events.jsonl"])

    monkeypatch.setattr(
        unattended_client_eval,
        "_write_vscode_workspace_mcp_config",
        fake_write_vscode_workspace_mcp_config,
    )
    monkeypatch.setattr(
        unattended_client_eval,
        "_raise_vscode_window",
        lambda window: raised.append(window) or True,
    )
    monkeypatch.setattr(
        unattended_client_eval,
        "_cleanup_vscode_workspace",
        lambda workspace_dir, window: cleanup_calls.append((workspace_dir, window))
        or {
            "closeAttempted": True,
            "windowClosed": True,
            "killedProcessPids": [],
        },
    )
    monkeypatch.setattr(
        unattended_client_eval,
        "_wait_for_vscode_mcp_server_discovery",
        lambda _server_name, *, timeout_sec=20.0: (expected_server_log, True),
    )

    def fake_run(command: list[str], **kwargs) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        envs.append(kwargs.get("env"))
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
        task=task,
        scenario_pack_id="pack-id",
        session_root=session_root,
        timeout_sec=1,
        attempt_kind="readiness",
    )

    assert session_dir.exists()
    assert exit_code == 0
    assert blocker is None
    assert commands == [
        [
            "code",
            "--new-window",
            str(expected_workspace_dir),
        ],
        [
            "code",
            "chat",
            "--mode",
            "agent",
            "--reuse-window",
            unattended_client_eval.VSCODE_MCP_PRIMER_PROMPT,
        ],
        [
            "code",
            "chat",
            "--mode",
            "agent",
            "--reuse-window",
            expected_prompt,
        ],
    ]
    assert envs[0]["OS_API_KEY_FILE"] == "/tmp/os_api_key.txt"
    assert "VSCODE_PORTABLE" not in envs[0]
    assert "VSCODE_PORTABLE" not in envs[1]
    assert rewrites == [
        (
            expected_workspace_dir,
            session_dir,
            "mcp-geo-bench-fixed-vscode-session",
        )
    ]
    assert raised == [benchmark_window, benchmark_window]
    assert cleanup_calls == [(expected_workspace_dir, benchmark_window)]
    session_meta = json.loads((session_dir / "session.json").read_text(encoding="utf-8"))
    assert session_meta["vscodeServerLog"] == str(expected_server_log)
    assert session_meta["vscodePrimerCommand"] == commands[1]
    assert session_meta["vscodeCleanupWindowClosed"] is True
    assert session_meta["vscodeCleanupKilledProcessPids"] == []


def test_run_vscode_track_blocks_until_workspace_server_tools_are_ready(
    monkeypatch, tmp_path: Path
) -> None:
    session_root = tmp_path / "logs" / "sessions"
    session_root.mkdir(parents=True)
    commands: list[list[str]] = []
    task = {"id": "readiness_probe", "label": "Readiness", "prompt": "Call the descriptor."}
    benchmark_window = unattended_client_eval.VSCodeWindow(name="readiness-probe", document="")
    expected_server_log = tmp_path / "Code" / "logs" / "window25" / "mcpServer.log"

    monkeypatch.setattr(unattended_client_eval, "_client_version", lambda _command: "code test")
    monkeypatch.setattr(
        unattended_client_eval,
        "_session_name",
        lambda _track_id, _task_id: "fixed-vscode-session",
    )
    monkeypatch.setattr(unattended_client_eval, "DEFAULT_WORKSPACE_ROOT", tmp_path / "workspaces")
    monkeypatch.setattr(unattended_client_eval, "_list_vscode_windows", lambda: [])
    monkeypatch.setattr(
        unattended_client_eval,
        "_wait_for_new_vscode_window",
        lambda _existing, *, workspace_name, timeout_sec=10.0: benchmark_window,
    )
    monkeypatch.setattr(
        unattended_client_eval,
        "_write_vscode_workspace_mcp_config",
        lambda workspace_dir, session_dir, server_name: (
            [session_dir / "mcp-stdio-trace.jsonl"],
            [],
        ),
    )
    monkeypatch.setattr(
        unattended_client_eval,
        "_raise_vscode_window",
        lambda window: True,
    )
    monkeypatch.setattr(
        unattended_client_eval,
        "_cleanup_vscode_workspace",
        lambda _workspace_dir, _window: {
            "closeAttempted": True,
            "windowClosed": True,
            "killedProcessPids": [],
        },
    )
    monkeypatch.setattr(
        unattended_client_eval,
        "_wait_for_vscode_mcp_server_discovery",
        lambda _server_name, *, timeout_sec=20.0: (expected_server_log, False),
    )

    def fake_run(command: list[str], **kwargs) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(unattended_client_eval.subprocess, "run", fake_run)
    monkeypatch.setattr(unattended_client_eval, "_read_lines", lambda _path: [])
    monkeypatch.setattr(unattended_client_eval.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(unattended_client_eval, "resolved_process_env", lambda: {})

    session_dir, exit_code, blocker = unattended_client_eval._run_vscode_track(
        task=task,
        scenario_pack_id="pack-id",
        session_root=session_root,
        timeout_sec=1,
        attempt_kind="readiness",
    )

    assert session_dir.exists()
    assert exit_code == 0
    assert blocker == "vscode_mcp_server_not_ready"
    assert commands == [
        [
            "code",
            "--new-window",
            str(tmp_path / "workspaces" / "vscode" / "fixed-vscode-session"),
        ],
        [
            "code",
            "chat",
            "--mode",
            "agent",
            "--reuse-window",
            unattended_client_eval.VSCODE_MCP_PRIMER_PROMPT,
        ],
    ]
    session_meta = json.loads((session_dir / "session.json").read_text(encoding="utf-8"))
    assert session_meta["vscodeServerLog"] == str(expected_server_log)


def test_task_prompt_uses_vscode_native_mcp_guidance() -> None:
    prompt = unattended_client_eval._task_prompt(
        {"id": "readiness_probe", "prompt": "Call the descriptor."},
        track_id="vscode_ide",
        server_name="mcp-geo-bench-readiness-probe",
    )

    assert prompt == (
        "Use only the connected mcp-geo-bench-readiness-probe MCP server in this VS Code "
        "window. In this VS Code agent window, the benchmark MCP tools are exposed "
        f"with `{unattended_client_eval.VSCODE_BENCH_TOOL_ALIAS_PREFIX}...` aliases. "
        f"Call the exact MCP tool `{unattended_client_eval.VSCODE_READINESS_TOOL_ALIAS}` "
        f'with {{"uri":"{unattended_client_eval.VSCODE_READINESS_RESOURCE_URI}"}}. '
        "If that field shape fails, retry the same exact tool with "
        f'{{"name":"{unattended_client_eval.VSCODE_READINESS_RESOURCE_NAME}"}}. '
        "Do not inspect the repository, use any other tool, or use fallback paths "
        "outside MCP. Stop after one sentence."
    )


def test_readiness_task_for_vscode_uses_resource_probe() -> None:
    readiness_task = unattended_client_eval._readiness_task_for_track("vscode_ide")

    assert readiness_task["expectedTools"] == ["os_resources.get"]
    assert readiness_task["toolFamily"] == "resource_bridge"


def test_run_track_readiness_limits_recovery_to_one_attempt(monkeypatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr(
        unattended_client_eval,
        "_env_readiness_facts",
        lambda: {
            "osApiKeyPresent": False,
            "osApiKeyFilePresent": True,
            "liveOsReady": True,
            "defaultToolset": "starter",
            "includeToolsets": "ons_geo_lookup",
            "excludeToolsets": None,
        },
    )

    def fake_execute_attempt(**kwargs) -> dict:
        calls.append(kwargs["attempt_kind"])
        ready = len(calls) == 2
        return {
            "trackId": kwargs["track_id"],
            "trackLabel": unattended_client_eval.TRACK_BY_ID[kwargs["track_id"]]["label"],
            "attemptKind": kwargs["attempt_kind"],
            "runStatus": "ready" if ready else "not_ready",
            "blockerCategory": None if ready else "client_no_mcp_traffic",
            "blocker": None if ready else "client produced no MCP traffic",
            "latencyToFirstUsefulToolCallMs": 1500 if ready else None,
            "requestCount": 1 if ready else 0,
            "toolCallCount": 1 if ready else 0,
        }

    monkeypatch.setattr(unattended_client_eval, "_execute_attempt", fake_execute_attempt)

    readiness, attempts = unattended_client_eval._run_track_readiness(
        track_id="vscode_ide",
        scenario_pack_id="pack-id",
        session_root=Path("/tmp/unused"),
        codex_model="gpt-5.4",
        gemini_model="",
        claude_model="",
        gemini_timeout_sec=90,
        claude_timeout_sec=60,
        vscode_timeout_sec=45,
    )

    assert [attempt["attemptKind"] for attempt in attempts] == ["readiness", "recovery"]
    assert readiness["firstAttemptOutcome"] == "not_ready"
    assert readiness["recovered"] is True
    assert readiness["outcome"] == "ready"


def test_make_skipped_capability_attempt_marks_live_key_gap() -> None:
    attempt = unattended_client_eval._make_skipped_capability_attempt(
        track_id="codex_cli",
        task={
            "id": "address_lookup_postcode",
            "label": "Address lookup by postcode",
            "prompt": "UPRNs for SW1A 1AA",
            "requiresLiveOsApi": True,
            "toolFamily": "places",
            "expectedCapability": "live_os_lookup",
        },
        reason_category="server_no_live_key",
        reason_message="live OS scenario skipped",
    )

    assert attempt["runStatus"] == "skipped"
    assert attempt["blockerCategory"] == "server_no_live_key"
    assert attempt["capabilityGroup"] == "live_os"


def test_summarize_attempts_separates_readiness_and_capability() -> None:
    scenario_pack = {
        "id": "pack-id",
        "scenarios": [
            {
                "id": "tool_search_postcode",
                "label": "Find postcode tools",
                "toolFamily": "discovery",
                "expectedCapability": "tool_discovery",
                "requiresLiveOsApi": False,
                "requiresUiRuntime": False,
            },
            {
                "id": "address_lookup_postcode",
                "label": "Address lookup",
                "toolFamily": "places",
                "expectedCapability": "live_os_lookup",
                "requiresLiveOsApi": True,
                "requiresUiRuntime": False,
            },
        ],
    }
    readiness_results = {
        "codex_cli": {
            "trackId": "codex_cli",
            "trackLabel": "Codex CLI",
            "configVisibility": {
                "osApiKeyPresent": False,
                "osApiKeyFilePresent": True,
                "liveOsReady": True,
                "defaultToolset": "starter",
                "includeToolsets": "ons_geo_lookup",
                "excludeToolsets": None,
            },
            "attempts": [],
            "attemptCount": 1,
            "outcome": "ready",
            "firstAttemptOutcome": "ready",
            "finalAttemptKind": "readiness",
            "recovered": False,
            "blockerCategory": None,
            "blocker": None,
            "readinessLatencyMs": 1200,
            "requestCount": 3,
            "toolCallCount": 1,
            "liveOsReady": True,
        },
        "gemini_cli": {
            "trackId": "gemini_cli",
            "trackLabel": "Gemini CLI",
            "configVisibility": {
                "osApiKeyPresent": False,
                "osApiKeyFilePresent": False,
                "liveOsReady": False,
                "defaultToolset": None,
                "includeToolsets": None,
                "excludeToolsets": None,
            },
            "attempts": [],
            "attemptCount": 2,
            "outcome": "not_ready",
            "firstAttemptOutcome": "not_ready",
            "finalAttemptKind": "recovery",
            "recovered": False,
            "blockerCategory": "client_workspace_restriction",
            "blocker": "workspace blocked",
            "readinessLatencyMs": None,
            "requestCount": 0,
            "toolCallCount": 0,
            "liveOsReady": False,
        },
        "claude_cli": {
            "trackId": "claude_cli",
            "trackLabel": "Claude Code CLI",
            "configVisibility": {
                "osApiKeyPresent": False,
                "osApiKeyFilePresent": True,
                "liveOsReady": True,
                "defaultToolset": "starter",
                "includeToolsets": "ons_geo_lookup",
                "excludeToolsets": None,
            },
            "attempts": [],
            "attemptCount": 1,
            "outcome": "ready",
            "firstAttemptOutcome": "ready",
            "finalAttemptKind": "readiness",
            "recovered": False,
            "blockerCategory": None,
            "blocker": None,
            "readinessLatencyMs": 1400,
            "requestCount": 2,
            "toolCallCount": 1,
            "liveOsReady": True,
        },
        "vscode_ide": {
            "trackId": "vscode_ide",
            "trackLabel": "VS Code Agent",
            "configVisibility": {
                "osApiKeyPresent": False,
                "osApiKeyFilePresent": True,
                "liveOsReady": True,
                "defaultToolset": "starter",
                "includeToolsets": "ons_geo_lookup",
                "excludeToolsets": None,
            },
            "attempts": [],
            "attemptCount": 1,
            "outcome": "ready",
            "firstAttemptOutcome": "ready",
            "finalAttemptKind": "readiness",
            "recovered": False,
            "blockerCategory": None,
            "blocker": None,
            "readinessLatencyMs": 1600,
            "requestCount": 2,
            "toolCallCount": 1,
            "liveOsReady": True,
        },
    }
    attempts = [
        {
            "trackId": "codex_cli",
            "trackLabel": "Codex CLI",
            "attemptKind": "readiness",
            "taskId": "readiness_probe",
            "taskLabel": "Readiness probe",
            "scenarioId": None,
            "scenarioLabel": None,
            "sessionDir": "/tmp/codex-readiness",
            "runStatus": "ready",
            "blockerCategory": None,
            "blocker": None,
            "overallScore": None,
            "overallStatus": None,
            "diagnosticScore": 0.92,
            "toolCallCount": 1,
            "requestCount": 2,
            "errorCodes": [],
            "latencyToFirstUsefulToolCallMs": 1200,
            "capabilityGroup": None,
            "expectedCapability": "readiness_probe",
            "toolFamily": "descriptor",
            "requiresLiveOsApi": False,
            "requiresUiRuntime": False,
        },
        {
            "trackId": "gemini_cli",
            "trackLabel": "Gemini CLI",
            "attemptKind": "readiness",
            "taskId": "readiness_probe",
            "taskLabel": "Readiness probe",
            "scenarioId": None,
            "scenarioLabel": None,
            "sessionDir": "/tmp/gemini-readiness",
            "runStatus": "not_ready",
            "blockerCategory": "client_workspace_restriction",
            "blocker": "workspace blocked",
            "overallScore": None,
            "overallStatus": None,
            "diagnosticScore": 0.48,
            "toolCallCount": 0,
            "requestCount": 0,
            "errorCodes": [],
            "latencyToFirstUsefulToolCallMs": None,
            "capabilityGroup": None,
            "expectedCapability": "readiness_probe",
            "toolFamily": "descriptor",
            "requiresLiveOsApi": False,
            "requiresUiRuntime": False,
        },
        {
            "trackId": "codex_cli",
            "trackLabel": "Codex CLI",
            "attemptKind": "capability",
            "taskId": "tool_search_postcode",
            "taskLabel": "Find postcode tools",
            "scenarioId": "tool_search_postcode",
            "scenarioLabel": "Find postcode tools",
            "sessionDir": "/tmp/codex-capability",
            "runStatus": "scored",
            "blockerCategory": None,
            "blocker": None,
            "overallScore": 0.75,
            "overallStatus": "partial",
            "diagnosticScore": None,
            "toolCallCount": 1,
            "requestCount": 3,
            "errorCodes": [],
            "latencyToFirstUsefulToolCallMs": 1200,
            "capabilityGroup": "offline_safe",
            "expectedCapability": "tool_discovery",
            "toolFamily": "discovery",
            "requiresLiveOsApi": False,
            "requiresUiRuntime": False,
        },
        {
            "trackId": "codex_cli",
            "trackLabel": "Codex CLI",
            "attemptKind": "capability",
            "taskId": "address_lookup_postcode",
            "taskLabel": "Address lookup",
            "scenarioId": "address_lookup_postcode",
            "scenarioLabel": "Address lookup",
            "sessionDir": None,
            "runStatus": "skipped",
            "blockerCategory": "server_no_live_key",
            "blocker": "live OS scenario skipped",
            "overallScore": None,
            "overallStatus": None,
            "diagnosticScore": None,
            "toolCallCount": 0,
            "requestCount": 0,
            "errorCodes": [],
            "latencyToFirstUsefulToolCallMs": None,
            "capabilityGroup": "live_os",
            "expectedCapability": "live_os_lookup",
            "toolFamily": "places",
            "requiresLiveOsApi": True,
            "requiresUiRuntime": False,
        },
    ]

    aggregate, markdown = unattended_client_eval._summarize_attempts(
        scenario_pack=scenario_pack,
        readiness_results=readiness_results,
        attempts=attempts,
    )

    assert aggregate["readiness"]["summary"]["firstAttemptReadyCount"] == 3
    assert aggregate["readiness"]["summary"]["notReadyCount"] == 1
    assert aggregate["tracks"]["codex_cli"]["capability"]["capabilities"]["tool_discovery"][
        "scoredCount"
    ] == 1
    assert aggregate["capability"]["toolFamilies"]["discovery"]["scoredCount"] == 1
    assert "Readiness Summary" in markdown
    assert "Capability Summary" in markdown
    assert "Tool Family Summary" in markdown
    assert "client_workspace_restriction" in markdown
    assert "not_ready" in markdown


def test_summarize_attempts_supports_requested_track_subset() -> None:
    scenario_pack = {
        "id": "pack-id",
        "scenarios": [
            {
                "id": "readiness_probe",
                "label": "Readiness probe",
                "toolFamily": "descriptor",
                "expectedCapability": "readiness_probe",
                "requiresLiveOsApi": False,
                "requiresUiRuntime": False,
            }
        ],
    }
    readiness_results = {
        "vscode_ide": {
            "trackId": "vscode_ide",
            "trackLabel": "VS Code Agent",
            "configVisibility": {
                "osApiKeyPresent": False,
                "osApiKeyFilePresent": True,
                "liveOsReady": True,
                "defaultToolset": "starter",
                "includeToolsets": "ons_geo_lookup",
                "excludeToolsets": None,
            },
            "attempts": [],
            "attemptCount": 1,
            "outcome": "ready",
            "firstAttemptOutcome": "ready",
            "finalAttemptKind": "readiness",
            "recovered": False,
            "blockerCategory": None,
            "blocker": None,
            "readinessLatencyMs": 900,
            "requestCount": 2,
            "toolCallCount": 1,
            "liveOsReady": True,
        }
    }
    attempts = [
        {
            "trackId": "vscode_ide",
            "trackLabel": "VS Code Agent",
            "attemptKind": "readiness",
            "taskId": "readiness_probe",
            "taskLabel": "Readiness probe",
            "scenarioId": None,
            "scenarioLabel": None,
            "sessionDir": "/tmp/vscode-readiness",
            "runStatus": "ready",
            "blockerCategory": None,
            "blocker": None,
            "overallScore": None,
            "overallStatus": None,
            "diagnosticScore": 0.9,
            "toolCallCount": 1,
            "requestCount": 2,
            "errorCodes": [],
            "latencyToFirstUsefulToolCallMs": 900,
            "capabilityGroup": None,
            "expectedCapability": "readiness_probe",
            "toolFamily": "descriptor",
            "requiresLiveOsApi": False,
            "requiresUiRuntime": False,
        }
    ]

    aggregate, markdown = unattended_client_eval._summarize_attempts(
        scenario_pack=scenario_pack,
        readiness_results=readiness_results,
        attempts=attempts,
        readiness_only=True,
    )

    assert list(aggregate["tracks"]) == ["vscode_ide"]
    assert "| VS Code Agent |" in markdown
    assert "| Codex CLI |" not in markdown
