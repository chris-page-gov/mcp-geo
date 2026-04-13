#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import importlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

VENV_PYTHON = REPO_ROOT / ".venv" / "bin" / "python"
if os.environ.get("MCP_GEO_SKIP_VENV_REEXEC") != "1":
    try:
        importlib.import_module("fastapi")
    except ModuleNotFoundError:
        if VENV_PYTHON.exists() and Path(sys.executable).resolve() != VENV_PYTHON.resolve():
            env = dict(os.environ)
            env["MCP_GEO_SKIP_VENV_REEXEC"] = "1"
            os.execve(str(VENV_PYTHON), [str(VENV_PYTHON), __file__, *sys.argv[1:]], env)

import scripts.host_benchmark as host_benchmark  # noqa: E402
from scripts.benchmark_env import resolve_inherited_env, resolved_process_env  # noqa: E402

DEFAULT_SCENARIO_PACK = host_benchmark.DEFAULT_SCENARIO_PACK
DEFAULT_SESSION_ROOT = REPO_ROOT / "logs" / "sessions"
DEFAULT_REPORT_ROOT = REPO_ROOT / "docs" / "reports"
DEFAULT_WORKSPACE_ROOT = REPO_ROOT / "logs" / "benchmark-workspaces"
DEFAULT_TRACKS = ("codex_cli", "gemini_cli", "claude_cli", "vscode_ide")
DEFAULT_GEMINI_SERVER = "mcp-geo-benchmark"
RECOVERY_TRACK_IDS = {"gemini_cli", "vscode_ide"}
GEMINI_SETTINGS_PATH = Path.home() / ".gemini"
VSCODE_LOG_ROOT = Path.home() / "Library" / "Application Support" / "Code" / "logs"
VSCODE_WORKSPACE_MCP_RELATIVE_PATH = Path(".vscode") / "mcp.json"
VSCODE_WINDOW_POLL_INTERVAL_SEC = 0.5
VSCODE_CHAT_FIRST_ACTIVITY_TIMEOUT_SEC = 30.0
VSCODE_CHAT_IDLE_TIMEOUT_SEC = 12.0
VSCODE_WINDOW_CLOSE_TIMEOUT_SEC = 5.0
VSCODE_BENCH_TOOL_ALIAS_PREFIX = "mcp_mcp-geo-bench_"
VSCODE_READINESS_TOOL_ALIAS = f"{VSCODE_BENCH_TOOL_ALIAS_PREFIX}os_resources_get"
VSCODE_READINESS_RESOURCE_URI = "resource://mcp-geo/area-summary-workflows"
VSCODE_READINESS_RESOURCE_NAME = "area-summary-workflows"
VSCODE_MCP_PRIMER_PROMPT = (
    "Do not inspect the repository or use any tools. Reply with READY in one word."
)
GEMINI_MCP_ONLY_POLICY = """[[rule]]
toolName = "mcp_*"
decision = "allow"
priority = 900
interactive = false

[[rule]]
toolName = "*"
decision = "deny"
priority = 800
interactive = false
"""

READINESS_TASK = {
    "id": "readiness_probe",
    "label": "Readiness probe",
    "prompt": (
        "Call the connected MCP tool `os_mcp_descriptor` (`os_mcp.descriptor`) "
        "with an empty input object `{}` and reply with the server name plus "
        "one safe example capability in one sentence."
    ),
    "expectedMcpEvidence": [
        "initialize",
        "tools/call:os_mcp.descriptor",
    ],
    "expectedTools": ["os_mcp.descriptor"],
    "expectedResources": [],
    "successConditions": [
        "Reaches at least one MCP request during startup.",
        "Makes a compact useful tool call against the connected server.",
    ],
    "fallbackConditions": [],
    "requiresLiveOsApi": False,
    "requiresUiRuntime": False,
    "toolFamily": "descriptor",
    "expectedCapability": "readiness_probe",
    "scoringHints": {
        "toolSearch": "optional",
        "resourcesRead": "none",
        "uiRuntime": "not_applicable",
        "fallbackExpectedOn": [],
    },
}
VSCODE_READINESS_TASK = {
    **READINESS_TASK,
    "prompt": (
        f"Call the VS Code MCP tool alias `{VSCODE_READINESS_TOOL_ALIAS}` "
        f'with `{{"uri":"{VSCODE_READINESS_RESOURCE_URI}"}}` and reply with '
        "the resource URI plus one short reason it is useful in one sentence."
    ),
    "expectedMcpEvidence": [
        "initialize",
        "tools/call:os_resources.get",
    ],
    "expectedTools": ["os_resources.get"],
    "toolFamily": "resource_bridge",
}
GEMINI_WORKSPACE_SIGNATURES = (
    "Path not in workspace",
    ".gemini/settings.json",
)
CLAUDE_AUTH_SIGNATURES = (
    "Failed to authenticate",
    "authentication credentials",
    "authentication_error",
)

TRACKS = (
    {
        "id": "codex_cli",
        "label": "Codex CLI",
        "source": "codex",
        "surface": "cli",
        "hostProfile": "codex_cli_stdio",
        "clientCommand": "codex",
    },
    {
        "id": "gemini_cli",
        "label": "Gemini CLI",
        "source": "gemini",
        "surface": "cli",
        "hostProfile": "gemini_cli_stdio",
        "clientCommand": "gemini",
    },
    {
        "id": "claude_cli",
        "label": "Claude Code CLI",
        "source": "claude",
        "surface": "cli",
        "hostProfile": "claude_cli_stdio",
        "clientCommand": "claude",
    },
    {
        "id": "vscode_ide",
        "label": "VS Code Agent",
        "source": "vscode",
        "surface": "ide",
        "hostProfile": "vscode_agent_chat",
        "clientCommand": "code",
    },
)
TRACK_BY_ID = {track["id"]: track for track in TRACKS}


@dataclass(frozen=True)
class VSCodeWindow:
    name: str
    document: str


def _utc_now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _timestamp_slug() -> str:
    return dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")


def _slug(value: str) -> str:
    text = "".join(ch.lower() if ch.isalnum() else "-" for ch in value)
    while "--" in text:
        text = text.replace("--", "-")
    return text.strip("-") or "session"


def _task_prompt(
    task: dict[str, Any],
    *,
    track_id: str | None = None,
    server_name: str = "mcp-geo",
) -> str:
    if track_id != "vscode_ide":
        return host_benchmark._prompt_for_scenario(task)
    if task.get("id") == READINESS_TASK["id"]:
        return (
            f"Use only the connected {server_name} MCP server in this VS Code "
            "window. In this VS Code agent window, the benchmark MCP tools are "
            f"exposed with `{VSCODE_BENCH_TOOL_ALIAS_PREFIX}...` aliases. Call "
            f"the exact MCP tool `{VSCODE_READINESS_TOOL_ALIAS}` with "
            f'{{"uri":"{VSCODE_READINESS_RESOURCE_URI}"}}. If that field shape '
            f"fails, retry the same exact tool with "
            f'{{"name":"{VSCODE_READINESS_RESOURCE_NAME}"}}. Do not inspect '
            "the repository, use any other tool, or use fallback paths outside "
            "MCP. Stop after one sentence."
        )
    return (
        f"Use only the connected `{server_name}` MCP server in this VS Code "
        "window. Do not use repository inspection, shell commands, HTTP "
        "endpoints, or fallback paths outside MCP. Return a concise final "
        "answer.\n\n"
        f"User request: {task['prompt']}"
    )


def _client_version(command: str) -> str | None:
    try:
        proc = subprocess.run(
            [command, "--version"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return None
    if proc.returncode != 0:
        return None
    output = (proc.stdout or proc.stderr).strip()
    if not output:
        return None
    return output.splitlines()[0].strip()


def _build_inherited_env() -> dict[str, str]:
    return resolve_inherited_env()


def _env_readiness_facts(inherited_env: dict[str, str] | None = None) -> dict[str, Any]:
    env = dict(inherited_env or _build_inherited_env())
    return {
        "osApiKeyPresent": bool(env.get("OS_API_KEY")),
        "osApiKeyFilePresent": bool(env.get("OS_API_KEY_FILE")),
        "liveOsReady": bool(env.get("OS_API_KEY") or env.get("OS_API_KEY_FILE")),
        "defaultToolset": env.get("MCP_TOOLS_DEFAULT_TOOLSET"),
        "includeToolsets": env.get("MCP_TOOLS_DEFAULT_INCLUDE_TOOLSETS"),
        "excludeToolsets": env.get("MCP_TOOLS_DEFAULT_EXCLUDE_TOOLSETS"),
    }


def _session_name(track_id: str, task_id: str) -> str:
    return f"{_timestamp_slug()}-{_slug(track_id)}-{_slug(task_id)}"


def _session_path(session_root: Path, name: str) -> Path:
    return session_root / name


def _latest_session_dir(session_root: Path) -> Path | None:
    latest_path = session_root / ".latest"
    if not latest_path.exists():
        return None
    text = latest_path.read_text(encoding="utf-8").strip()
    if not text:
        return None
    return Path(text)


def _locate_session_dir(
    session_root: Path,
    *,
    name: str,
    latest_before: Path | None = None,
) -> Path | None:
    exact = _session_path(session_root, name)
    if exact.exists():
        return exact

    latest_after = _latest_session_dir(session_root)
    if (
        latest_after is not None
        and latest_after != latest_before
        and latest_after.parent == session_root
        and latest_after.name.startswith(name)
        and latest_after.exists()
    ):
        return latest_after

    matches = sorted(
        session_root.glob(f"{name}*"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if matches:
        return matches[0]
    return None


def _initial_session_meta(
    session_dir: Path,
    *,
    command: list[str],
    scenario_pack: str,
    task: dict[str, Any],
    model: str,
    track: dict[str, str],
    attempt_kind: str,
    capability_group: str | None,
) -> None:
    host_benchmark._write_initial_session_meta(
        session_dir,
        command=command,
        scenario_pack=scenario_pack,
        scenario_id=task["id"],
        model=model,
        source=track["source"],
        surface=track["surface"],
        host_profile=track["hostProfile"],
        client_version=_client_version(track["clientCommand"]),
    )
    _update_session_meta(
        session_dir,
        taskId=task["id"],
        taskLabel=task.get("label", task["id"]),
        attemptKind=attempt_kind,
        capabilityGroup=capability_group,
        expectedCapability=task.get("expectedCapability"),
        toolFamily=task.get("toolFamily"),
        requiresLiveOsApi=bool(task.get("requiresLiveOsApi") or task.get("requiresOsApi")),
        requiresUiRuntime=bool(task.get("requiresUiRuntime")),
    )


def _update_session_meta(session_dir: Path, **updates: Any) -> None:
    payload = host_benchmark._load_session_meta(session_dir)
    payload.update(updates)
    host_benchmark._save_session_meta(session_dir, payload)


def _update_session_paths(session_dir: Path, **updates: str) -> None:
    payload = host_benchmark._load_session_meta(session_dir)
    paths = payload.setdefault("paths", {})
    if isinstance(paths, dict):
        paths.update(updates)
    host_benchmark._save_session_meta(session_dir, payload)


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _coerce_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _stderr_path(session_dir: Path, client: str) -> Path:
    return session_dir / f"{client}-exec.stderr.txt"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    _write_text(path, json.dumps(payload, indent=2))


def _trace_report(session_dir: Path) -> None:
    subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "trace_report.py"), str(session_dir)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _load_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return payload


def _load_existing_score_artifacts(
    session_dir: Path,
) -> tuple[dict[str, Any], dict[str, Any]] | None:
    evidence_path = session_dir / "benchmark-evidence.json"
    score_path = session_dir / "benchmark-score.json"
    if not evidence_path.exists() or not score_path.exists():
        return None
    return (_load_json_object(evidence_path), _load_json_object(score_path))


def _score_session(
    session_dir: Path,
    task: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    cached = _load_existing_score_artifacts(session_dir)
    if cached is not None:
        return cached
    evidence, score = host_benchmark.score_session(session_dir, task)
    host_benchmark.write_score_artifacts(session_dir, evidence, score)
    return evidence, score


def _scenario_capability_group(task: dict[str, Any]) -> str:
    if bool(task.get("requiresUiRuntime")):
        return "ui"
    if bool(task.get("requiresLiveOsApi") or task.get("requiresOsApi")):
        return "live_os"
    return "offline_safe"


def _expected_capability(task: dict[str, Any]) -> str:
    capability = task.get("expectedCapability")
    if isinstance(capability, str) and capability:
        return capability
    if task.get("expectedResources") and (
        task.get("scoringHints", {}).get("resourcesRead") == "required"
    ):
        return "resource_consumption"
    intent = task.get("intent")
    if isinstance(intent, str) and intent:
        return intent
    return _scenario_capability_group(task)


def _tool_family(task: dict[str, Any]) -> str:
    family = task.get("toolFamily")
    if isinstance(family, str) and family:
        return family
    expected_tools = task.get("expectedTools") or []
    for tool_name in expected_tools:
        if not isinstance(tool_name, str) or "/" in tool_name:
            continue
        return tool_name.split(".", 1)[0]
    return _expected_capability(task)


def _readiness_task_for_track(track_id: str) -> dict[str, Any]:
    if track_id == "vscode_ide":
        return VSCODE_READINESS_TASK
    return READINESS_TASK


def _classify_capability_status(
    *,
    exit_code: int,
    evidence: dict[str, Any] | None,
) -> str:
    if exit_code != 0:
        return "runner_error"
    if evidence is None:
        return "runner_error"
    request_count = int(evidence.get("traceSummary", {}).get("mcp", {}).get("requestCount") or 0)
    tool_calls = evidence.get("toolCalls") or []
    if request_count == 0:
        return "no_mcp_traffic"
    if not tool_calls:
        return "startup_only"
    return "scored"


def _classify_readiness_status(
    *,
    exit_code: int,
    evidence: dict[str, Any] | None,
) -> str:
    if exit_code != 0 or evidence is None:
        return "not_ready"
    request_count = int(evidence.get("traceSummary", {}).get("mcp", {}).get("requestCount") or 0)
    tool_calls = evidence.get("toolCalls") or []
    if request_count == 0 or not tool_calls:
        return "not_ready"
    return "ready"


def _classify_blocker_category(
    *,
    track_id: str,
    purpose: str,
    exit_code: int,
    evidence: dict[str, Any] | None,
    runner_blocker: str | None,
    session_dir: Path | None,
) -> tuple[str | None, str | None]:
    error_codes = {str(code) for code in (evidence or {}).get("errorCodes", [])}
    request_count = int(
        (evidence or {}).get("traceSummary", {}).get("mcp", {}).get("requestCount") or 0
    )
    tool_calls = (evidence or {}).get("toolCalls") or []
    assistant_text = (
        _read_text((session_dir or Path()) / "assistant-response.txt") if session_dir else ""
    )
    stderr_text = (
        _read_text(_stderr_path(session_dir, track_id.split("_", 1)[0])) if session_dir else ""
    )
    combined = "\n".join(
        value for value in (runner_blocker or "", assistant_text, stderr_text) if value
    )
    lowered = combined.lower()

    if "NO_API_KEY" in error_codes:
        return ("server_no_live_key", "server returned NO_API_KEY")
    if track_id == "claude_cli" and any(
        signature.lower() in lowered for signature in CLAUDE_AUTH_SIGNATURES
    ):
        return ("client_auth_failure", "client authentication failed before prompt execution")
    if track_id == "gemini_cli" and all(
        signature.lower() in lowered for signature in GEMINI_WORKSPACE_SIGNATURES
    ):
        return (
            "client_workspace_restriction",
            "Gemini workspace restrictions blocked access to ~/.gemini/settings.json",
        )
    if track_id == "vscode_ide" and (
        runner_blocker in {
            "vscode_workspace_open_failed",
            "vscode_workspace_focus_failed",
            "vscode_mcp_server_not_ready",
        }
        or str(runner_blocker or "").startswith("vscode_primer_timeout_after_")
    ):
        return (
            "client_workspace_restriction",
            "VS Code failed to attach the benchmark workspace MCP tools before chat",
        )
    if request_count == 0:
        if exit_code != 0:
            return (
                "client_launch_failure",
                runner_blocker or f"client exited with code {exit_code}",
            )
        return ("client_no_mcp_traffic", "client produced no MCP traffic")
    if purpose in {"readiness", "recovery"} and not tool_calls:
        return ("client_no_useful_tool_call", "client initialized but made no useful tool call")
    if exit_code != 0:
        if purpose == "capability":
            return (
                "scenario_tool_failure",
                runner_blocker or f"client exited with code {exit_code}",
            )
        return ("client_launch_failure", runner_blocker or f"client exited with code {exit_code}")
    if purpose == "capability" and runner_blocker:
        return ("scenario_tool_failure", runner_blocker)
    return (None, None)


def _gemini_remove_server(name: str, *, cwd: Path) -> None:
    subprocess.run(
        ["gemini", "mcp", "remove", name],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def _gemini_add_stdio_server(name: str, server_config: dict[str, Any], *, cwd: Path) -> None:
    command = [
        "gemini",
        "mcp",
        "add",
        "--scope",
        "project",
        "--trust",
        "--timeout",
        "120000",
    ]
    for key, value in sorted((server_config.get("env") or {}).items()):
        command.extend(["-e", f"{key}={value}"])
    command.append(name)
    command.append(server_config["command"])
    command.extend(server_config.get("args") or [])
    proc = subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "gemini mcp add failed")


def _prepare_gemini_workspace(task: dict[str, Any]) -> Path:
    workspace_dir = DEFAULT_WORKSPACE_ROOT / "gemini" / _slug(task["id"])
    if workspace_dir.exists():
        shutil.rmtree(workspace_dir)
    workspace_dir.mkdir(parents=True, exist_ok=True)
    (workspace_dir / ".gemini" / "policies").mkdir(parents=True, exist_ok=True)
    _write_text(workspace_dir / ".gemini" / "policies" / "00-mcp-only.toml", GEMINI_MCP_ONLY_POLICY)
    return workspace_dir


def _configure_gemini_workspace(
    *,
    workspace_dir: Path,
    server_name: str,
    server_config: dict[str, Any],
) -> None:
    settings = {
        "tools": {
            "core": [],
        },
        "mcp": {
            "allowed": [server_name],
        },
        "mcpServers": {
            server_name: {
                "command": server_config["command"],
                "args": server_config.get("args") or [],
                "env": server_config.get("env") or {},
                "cwd": str(REPO_ROOT),
                "timeout": 120000,
                "trust": True,
            }
        },
    }
    _write_json(workspace_dir / ".gemini" / "settings.json", settings)


def _prepare_vscode_workspace(
    task: dict[str, Any],
    *,
    workspace_name: str | None = None,
) -> Path:
    workspace_dir = DEFAULT_WORKSPACE_ROOT / "vscode" / (workspace_name or _slug(task["id"]))
    if workspace_dir.exists():
        shutil.rmtree(workspace_dir)
    workspace_dir.mkdir(parents=True, exist_ok=True)
    return workspace_dir


def _vscode_workspace_mcp_path(workspace_dir: Path) -> Path:
    return workspace_dir / VSCODE_WORKSPACE_MCP_RELATIVE_PATH


def _write_vscode_workspace_mcp_config(
    workspace_dir: Path,
    session_dir: Path,
    server_name: str,
) -> tuple[list[Path], list[Path]]:
    workspace_path = _vscode_workspace_mcp_path(workspace_dir)
    payload = {}
    server_config = host_benchmark._build_temp_stdio_server(
        session_dir,
        wrapper=REPO_ROOT / "scripts" / "vscode_mcp_stdio.py",
        inherited_env=_build_inherited_env(),
    )
    servers = payload.setdefault("servers", {})
    if not isinstance(servers, dict):
        raise ValueError("VS Code MCP config 'servers' payload must be an object.")
    payload.setdefault("inputs", [])
    servers[server_name] = {
        "type": "stdio",
        "command": server_config["command"],
        "args": server_config.get("args") or [],
        "cwd": str(REPO_ROOT),
        "env": server_config.get("env") or {},
    }
    _write_json(workspace_path, payload)
    trace_paths = [session_dir / "mcp-stdio-trace.jsonl"]
    ui_paths: list[Path] = []
    ui_log = (server_config.get("env") or {}).get("UI_EVENT_LOG_PATH")
    if isinstance(ui_log, str) and ui_log:
        ui_paths.append(Path(ui_log))
    return (trace_paths, ui_paths)


def _run_osascript(lines: list[str], *args: str) -> subprocess.CompletedProcess[str]:
    command = ["osascript"]
    for line in lines:
        command.extend(["-e", line])
    command.extend(args)
    return subprocess.run(command, capture_output=True, text=True, check=False)


def _list_vscode_windows() -> list[VSCodeWindow]:
    names_proc = _run_osascript(
        ['tell application "System Events" to tell process "Code" to get name of every window']
    )
    if names_proc.returncode != 0:
        return []
    docs_proc = _run_osascript(
        [
            'tell application "System Events" to tell process "Code" '
            'to get value of attribute "AXDocument" of every window'
        ]
    )
    if docs_proc.returncode != 0:
        return []
    names = [item.strip() for item in names_proc.stdout.strip().split(",") if item.strip()]
    raw_docs = [item.strip() for item in docs_proc.stdout.strip().split(",")]
    docs = ["" if item == "missing value" else item for item in raw_docs]
    windows: list[VSCodeWindow] = []
    for index, name in enumerate(names):
        document = docs[index] if index < len(docs) else ""
        windows.append(VSCodeWindow(name=name, document=document))
    return windows


def _find_vscode_mcp_server_logs(server_name: str) -> list[Path]:
    if not VSCODE_LOG_ROOT.exists():
        return []
    matches = VSCODE_LOG_ROOT.rglob(f"mcpServer.mcp.config.*.{server_name}.log")
    return sorted(matches, key=lambda path: path.stat().st_mtime, reverse=True)


def _vscode_mcp_server_tools_discovered(log_path: Path) -> bool:
    return any("Discovered " in line and " tools" in line for line in _read_lines(log_path))


def _wait_for_vscode_mcp_server_discovery(
    server_name: str,
    *,
    timeout_sec: float = 20.0,
) -> tuple[Path | None, bool]:
    latest_log: Path | None = None
    deadline = time.monotonic() + timeout_sec
    while time.monotonic() < deadline:
        matches = _find_vscode_mcp_server_logs(server_name)
        if matches:
            latest_log = matches[0]
            if _vscode_mcp_server_tools_discovered(latest_log):
                return (latest_log, True)
        time.sleep(VSCODE_WINDOW_POLL_INTERVAL_SEC)
    return (latest_log, False)


def _wait_for_new_vscode_window(
    existing_windows: list[VSCodeWindow],
    *,
    workspace_name: str,
    timeout_sec: float = 10.0,
) -> VSCodeWindow | None:
    baseline = set(existing_windows)
    deadline = time.monotonic() + timeout_sec
    while time.monotonic() < deadline:
        windows = _list_vscode_windows()
        for window in windows:
            if window not in baseline:
                return window
        for window in windows:
            if workspace_name in window.name:
                return window
        time.sleep(VSCODE_WINDOW_POLL_INTERVAL_SEC)
    return None


def _find_vscode_window_for_workspace(workspace_dir: Path) -> VSCodeWindow | None:
    workspace_uri = workspace_dir.resolve().as_uri()
    workspace_name = workspace_dir.name
    for window in _list_vscode_windows():
        if workspace_name and workspace_name in window.name:
            return window
        if window.document and (
            workspace_uri in window.document or str(workspace_dir.resolve()) in window.document
        ):
            return window
    return None


def _raise_vscode_window(window: VSCodeWindow) -> bool:
    proc = _run_osascript(
        [
            "on run argv",
            '  set targetName to item 1 of argv',
            '  set targetDocument to item 2 of argv',
            '  tell application "System Events"',
            '    if not (exists process "Code") then return "missing"',
            '    tell process "Code"',
            "      repeat with w in windows",
            '        set windowName to ""',
            '        set windowDocument to ""',
            "        try",
            "          set windowName to name of w as text",
            "        end try",
            "        try",
            '          set windowDocument to value of attribute "AXDocument" of w as text',
            "        end try",
            '        if windowName is targetName and (targetDocument is "" or ¬',
            'windowDocument is targetDocument) then',
            '          perform action "AXRaise" of w',
            '          return "ok"',
            "        end if",
            "      end repeat",
            "    end tell",
            "  end tell",
            '  return "missing"',
            "end run",
        ],
        window.name,
        window.document,
    )
    return proc.returncode == 0 and proc.stdout.strip() == "ok"


def _confirm_vscode_close_dialog() -> bool:
    proc = _run_osascript(
        [
            'tell application "System Events"',
            '  if not (exists process "Code") then return "missing"',
            '  tell process "Code"',
            "    repeat 10 times",
            "      try",
            '        if exists button "Yes" of sheet 1 of window 1 then',
            '          click button "Yes" of sheet 1 of window 1',
            '          return "confirmed"',
            "        end if",
            "      end try",
            "      try",
            '        if exists button "Yes" of window 1 then',
            '          click button "Yes" of window 1',
            '          return "confirmed"',
            "        end if",
            "      end try",
            "      delay 0.2",
            "    end repeat",
            "  end tell",
            "end tell",
            'return "none"',
        ]
    )
    return proc.returncode == 0 and proc.stdout.strip() in {"confirmed", "none"}


def _window_present(window: VSCodeWindow) -> bool:
    return window in _list_vscode_windows()


def _close_vscode_window(window: VSCodeWindow) -> bool:
    proc = _run_osascript(
        [
            "on run argv",
            '  set targetName to item 1 of argv',
            '  set targetDocument to item 2 of argv',
            '  tell application "System Events"',
            '    if not (exists process "Code") then return "missing"',
            '    tell process "Code"',
            "      repeat with w in windows",
            '        set windowName to ""',
            '        set windowDocument to ""',
            "        try",
            "          set windowName to name of w as text",
            "        end try",
            "        try",
            '          set windowDocument to value of attribute "AXDocument" of w as text',
            "        end try",
            '        if windowName is targetName and (targetDocument is "" or ¬',
            'windowDocument is targetDocument) then',
            "          click button 1 of w",
            '          return "ok"',
            "        end if",
            "      end repeat",
            "    end tell",
            "  end tell",
            '  return "missing"',
            "end run",
        ],
        window.name,
        window.document,
    )
    if proc.returncode != 0 or proc.stdout.strip() != "ok":
        return False
    _confirm_vscode_close_dialog()
    deadline = time.monotonic() + VSCODE_WINDOW_CLOSE_TIMEOUT_SEC
    while time.monotonic() < deadline:
        if not _window_present(window):
            return True
        time.sleep(VSCODE_WINDOW_POLL_INTERVAL_SEC)
    return not _window_present(window)


def _run_codex_track(
    *,
    task: dict[str, Any],
    scenario_pack_id: str,
    session_root: Path,
    model: str,
    attempt_kind: str,
) -> tuple[Path, int, str | None]:
    track = TRACK_BY_ID["codex_cli"]
    name = _session_name(track["id"], task["id"])
    session_dir = host_benchmark._ensure_session_dir(session_root, name)
    prompt = _task_prompt(task)
    wrapper = REPO_ROOT / "scripts" / "codex-mcp-local"
    inherited_env = _build_inherited_env()
    server_name = "mcp-geo"
    server_config = host_benchmark._build_temp_stdio_server(
        session_dir,
        wrapper=wrapper,
        inherited_env=inherited_env,
    )
    previous = host_benchmark._codex_get_server(server_name)
    restore_config = host_benchmark._prepare_restore_server_config(previous)
    command = [
        "codex",
        "exec",
        "-m",
        model,
        "--json",
        "-o",
        str(session_dir / "assistant-response.txt"),
        "-C",
        str(REPO_ROOT),
        prompt,
    ]
    _initial_session_meta(
        session_dir,
        command=command,
        scenario_pack=scenario_pack_id,
        task=task,
        model=model,
        track=track,
        attempt_kind=attempt_kind,
        capability_group=None if attempt_kind != "capability" else _scenario_capability_group(task),
    )
    _update_session_paths(
        session_dir,
        assistantResponse=str(session_dir / "assistant-response.txt"),
        clientStderr=str(_stderr_path(session_dir, "codex")),
    )

    exit_code = 0
    blocker: str | None = None
    try:
        host_benchmark._codex_remove_server(server_name)
        host_benchmark._codex_add_stdio_server(server_name, server_config)
        proc = subprocess.run(
            command,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        (session_dir / "codex-events.jsonl").write_text(proc.stdout, encoding="utf-8")
        if proc.stderr:
            _write_text(_stderr_path(session_dir, "codex"), proc.stderr)
        exit_code = proc.returncode
        if proc.returncode != 0:
            blocker = f"codex exec failed with code {proc.returncode}"
            _update_session_meta(session_dir, runnerError=blocker)
    finally:
        host_benchmark._restore_server(server_name, restore_config)

    return (session_dir, exit_code, blocker)


def _run_gemini_track(
    *,
    task: dict[str, Any],
    scenario_pack_id: str,
    session_root: Path,
    model: str,
    timeout_sec: int,
    attempt_kind: str,
) -> tuple[Path, int, str | None]:
    track = TRACK_BY_ID["gemini_cli"]
    name = _session_name(track["id"], task["id"])
    session_dir = host_benchmark._ensure_session_dir(session_root, name)
    prompt = _task_prompt(task)
    project_dir = _prepare_gemini_workspace(task)
    server_name = f"{DEFAULT_GEMINI_SERVER}-{_slug(task['id'])}"
    server_config = host_benchmark._build_temp_stdio_server(
        session_dir,
        wrapper=REPO_ROOT / "scripts" / "gemini-mcp-local",
        inherited_env=_build_inherited_env(),
    )
    _configure_gemini_workspace(
        workspace_dir=project_dir,
        server_name=server_name,
        server_config=server_config,
    )
    command = [
        "gemini",
        "--allowed-mcp-server-names",
        server_name,
        "--approval-mode",
        "yolo",
        "--output-format",
        "json",
        "--include-directories",
        str(GEMINI_SETTINGS_PATH),
        "--include-directories",
        str(REPO_ROOT),
    ]
    if model:
        command.extend(["--model", model])
    command.extend(["--prompt", prompt])
    _initial_session_meta(
        session_dir,
        command=command,
        scenario_pack=scenario_pack_id,
        task=task,
        model=model,
        track=track,
        attempt_kind=attempt_kind,
        capability_group=None if attempt_kind != "capability" else _scenario_capability_group(task),
    )
    _update_session_meta(session_dir, benchmarkWorkspace=str(project_dir))
    _update_session_paths(
        session_dir,
        assistantResponse=str(session_dir / "assistant-response.txt"),
        clientStderr=str(_stderr_path(session_dir, "gemini")),
    )

    exit_code = 0
    blocker: str | None = None
    proc: subprocess.CompletedProcess[str] | None = None
    try:
        proc = subprocess.run(
            command,
            cwd=project_dir,
            capture_output=True,
            text=True,
            check=False,
            timeout=max(timeout_sec, 1),
        )
    except subprocess.TimeoutExpired as exc:
        blocker = f"gemini_cli_timeout_after_{timeout_sec}s"
        _write_text(session_dir / "assistant-response.txt", _coerce_text(exc.stdout))
        if exc.stderr is not None:
            _write_text(_stderr_path(session_dir, "gemini"), _coerce_text(exc.stderr))
        _update_session_meta(session_dir, runnerError=blocker)
        return (session_dir, 124, blocker)
    _write_text(session_dir / "assistant-response.txt", proc.stdout)
    if proc.stderr:
        _write_text(_stderr_path(session_dir, "gemini"), proc.stderr)
    exit_code = proc.returncode
    if proc is not None and proc.returncode != 0:
        blocker = "gemini_cli_failed"
        _update_session_meta(session_dir, runnerError=blocker)
    return (session_dir, exit_code, blocker)


def _run_claude_track(
    *,
    task: dict[str, Any],
    scenario_pack_id: str,
    session_root: Path,
    model: str,
    timeout_sec: int,
    attempt_kind: str,
) -> tuple[Path, int, str | None]:
    track = TRACK_BY_ID["claude_cli"]
    name = _session_name(track["id"], task["id"])
    session_dir = host_benchmark._ensure_session_dir(session_root, name)
    server_config = host_benchmark._build_temp_stdio_server(
        session_dir,
        wrapper=REPO_ROOT / "scripts" / "claude-mcp-local",
        inherited_env=_build_inherited_env(),
    )
    mcp_config = {
        "mcpServers": {
            "mcp-geo": {
                "command": server_config["command"],
                "args": server_config.get("args") or [],
                "env": server_config.get("env") or {},
            }
        }
    }
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".json",
        encoding="utf-8",
        delete=False,
    ) as handle:
        json.dump(mcp_config, handle)
        config_path = Path(handle.name)
    prompt = _task_prompt(task)
    command = ["claude", "--strict-mcp-config", "--mcp-config", str(config_path)]
    if model:
        command.extend(["--model", model])
    command.extend(["-p", "--output-format", "json", prompt])
    _initial_session_meta(
        session_dir,
        command=command,
        scenario_pack=scenario_pack_id,
        task=task,
        model=model,
        track=track,
        attempt_kind=attempt_kind,
        capability_group=None if attempt_kind != "capability" else _scenario_capability_group(task),
    )
    _update_session_paths(
        session_dir,
        assistantResponse=str(session_dir / "assistant-response.txt"),
        clientStderr=str(_stderr_path(session_dir, "claude")),
    )

    proc: subprocess.CompletedProcess[str] | None = None
    blocker: str | None = None
    try:
        try:
            proc = subprocess.run(
                command,
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
                timeout=max(timeout_sec, 1),
            )
        except subprocess.TimeoutExpired as exc:
            blocker = f"claude_cli_timeout_after_{timeout_sec}s"
            _write_text(session_dir / "assistant-response.txt", _coerce_text(exc.stdout))
            if exc.stderr is not None:
                _write_text(_stderr_path(session_dir, "claude"), _coerce_text(exc.stderr))
            _update_session_meta(session_dir, runnerError=blocker)
            return (session_dir, 124, blocker)
        _write_text(session_dir / "assistant-response.txt", proc.stdout)
        if proc.stderr:
            _write_text(_stderr_path(session_dir, "claude"), proc.stderr)
        if proc.returncode != 0:
            blocker = "claude_cli_failed"
            _update_session_meta(session_dir, runnerError=blocker)
        return (session_dir, proc.returncode, blocker)
    finally:
        try:
            config_path.unlink(missing_ok=True)
        except OSError:
            pass


def _read_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


def _write_lines(path: Path, lines: list[str]) -> None:
    if not lines:
        return
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _snapshot_line_counts(paths: list[Path]) -> dict[Path, int]:
    return {path: len(_read_lines(path)) for path in paths}


def _delta_line_count(snapshot: dict[Path, int]) -> int:
    total = 0
    for path, before in snapshot.items():
        total += max(len(_read_lines(path)) - before, 0)
    return total


def _materialize_log_delta(output_path: Path, snapshot: dict[Path, int]) -> None:
    lines: list[str] = []
    for path, before in snapshot.items():
        source_lines = _read_lines(path)
        if len(source_lines) > before:
            lines.extend(source_lines[before:])
    if output_path.exists():
        output_path.unlink()
    _write_lines(output_path, lines)


def _run_vscode_track(
    *,
    task: dict[str, Any],
    scenario_pack_id: str,
    session_root: Path,
    timeout_sec: int,
    attempt_kind: str,
) -> tuple[Path, int, str | None]:
    track = TRACK_BY_ID["vscode_ide"]
    name = _session_name(track["id"], task["id"])
    session_dir = host_benchmark._ensure_session_dir(session_root, name)
    workspace_dir = _prepare_vscode_workspace(task, workspace_name=name)
    server_name = f"mcp-geo-bench-{_slug(name)}"
    prompt = _task_prompt(task, track_id="vscode_ide", server_name=server_name)
    existing_windows = _list_vscode_windows()
    open_command = [
        "code",
        "--new-window",
        str(workspace_dir),
    ]
    chat_command = [
        "code",
        "chat",
        "--mode",
        "agent",
        "--reuse-window",
        prompt,
    ]
    primer_command = [
        "code",
        "chat",
        "--mode",
        "agent",
        "--reuse-window",
        VSCODE_MCP_PRIMER_PROMPT,
    ]
    _initial_session_meta(
        session_dir,
        command=chat_command,
        scenario_pack=scenario_pack_id,
        task=task,
        model="copilot-agent",
        track=track,
        attempt_kind=attempt_kind,
        capability_group=None if attempt_kind != "capability" else _scenario_capability_group(task),
    )
    _update_session_paths(
        session_dir,
        assistantResponse=str(session_dir / "assistant-response.txt"),
        clientStderr=str(_stderr_path(session_dir, "vscode")),
    )
    _update_session_meta(
        session_dir,
        benchmarkWorkspace=str(workspace_dir),
        vscodeServerName=server_name,
        vscodeOpenCommand=open_command,
        vscodePrimerCommand=primer_command,
    )
    trace_path = session_dir / "mcp-stdio-trace.jsonl"
    ui_path = session_dir / "ui-events.jsonl"
    workspace_env = resolved_process_env()
    trace_paths, ui_paths = _write_vscode_workspace_mcp_config(
        workspace_dir,
        session_dir,
        server_name,
    )
    _update_session_paths(
        session_dir,
        vscodeWorkspaceMcpConfig=str(_vscode_workspace_mcp_path(workspace_dir)),
    )
    trace_snapshot = _snapshot_line_counts(trace_paths)
    ui_snapshot = _snapshot_line_counts(ui_paths)
    stderr_chunks: list[str] = []
    assistant_output = ""
    exit_code = 0
    blocker: str | None = None
    benchmark_window: VSCodeWindow | None = None
    open_timeout_sec = min(max(timeout_sec, 5), 20)
    discovery_timeout_sec = min(max(timeout_sec, 15), 30)
    primer_timeout_sec = min(max(timeout_sec, 5), 30)
    phase = "workspace_open"
    try:
        try:
            open_proc = subprocess.run(
                open_command,
                cwd=workspace_dir,
                env=workspace_env,
                capture_output=True,
                text=True,
                check=False,
                timeout=open_timeout_sec,
            )
            if open_proc.stderr:
                stderr_chunks.append(open_proc.stderr)
            if open_proc.returncode != 0:
                exit_code = open_proc.returncode
                blocker = "vscode_workspace_open_failed"
            else:
                benchmark_window = _wait_for_new_vscode_window(
                    existing_windows,
                    workspace_name=workspace_dir.name,
                    timeout_sec=10.0,
                )
                if benchmark_window is not None:
                    _raise_vscode_window(benchmark_window)
                    _update_session_meta(
                        session_dir,
                        vscodeWindowName=benchmark_window.name,
                        vscodeWindowDocument=benchmark_window.document,
                    )
                phase = "primer"
                primer_proc = subprocess.run(
                    primer_command,
                    cwd=workspace_dir,
                    env=workspace_env,
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=primer_timeout_sec,
                )
                if primer_proc.stderr:
                    stderr_chunks.append(primer_proc.stderr)
                if primer_proc.returncode != 0:
                    exit_code = primer_proc.returncode
                    blocker = "vscode_chat_failed"
                server_log, ready_for_chat = _wait_for_vscode_mcp_server_discovery(
                    server_name,
                    timeout_sec=discovery_timeout_sec,
                )
                if server_log is not None:
                    _update_session_meta(session_dir, vscodeServerLog=str(server_log))
                if blocker is None and not ready_for_chat:
                    blocker = "vscode_mcp_server_not_ready"
                elif blocker is None:
                    benchmark_window = (
                        _find_vscode_window_for_workspace(workspace_dir) or benchmark_window
                    )
                    if benchmark_window is not None:
                        _raise_vscode_window(benchmark_window)
                        _update_session_meta(
                            session_dir,
                            vscodeWindowName=benchmark_window.name,
                            vscodeWindowDocument=benchmark_window.document,
                        )
                    trace_snapshot = _snapshot_line_counts(trace_paths)
                    ui_snapshot = _snapshot_line_counts(ui_paths)
                    phase = "chat"
                    chat_proc = subprocess.run(
                        chat_command,
                        cwd=workspace_dir,
                        env=workspace_env,
                        capture_output=True,
                        text=True,
                        check=False,
                        timeout=max(timeout_sec, 5),
                    )
                    assistant_output = chat_proc.stdout
                    if chat_proc.stderr:
                        stderr_chunks.append(chat_proc.stderr)
                    exit_code = chat_proc.returncode
                    if chat_proc.returncode != 0:
                        blocker = "vscode_chat_failed"
        except subprocess.TimeoutExpired as exc:
            exit_code = 124
            assistant_output = _coerce_text(exc.stdout)
            if exc.stderr is not None:
                stderr_chunks.append(_coerce_text(exc.stderr))
            if phase == "workspace_open":
                blocker = "vscode_workspace_open_failed"
                stderr_chunks.append(f"workspace open timed out after {open_timeout_sec}s")
            elif phase == "primer":
                blocker = f"vscode_primer_timeout_after_{primer_timeout_sec}s"
            else:
                blocker = f"vscode_chat_timeout_after_{timeout_sec}s"

        deadline = time.monotonic() + max(timeout_sec, 5)
        first_activity_deadline = time.monotonic() + min(
            max(timeout_sec / 2, VSCODE_CHAT_IDLE_TIMEOUT_SEC),
            VSCODE_CHAT_FIRST_ACTIVITY_TIMEOUT_SEC,
        )
        last_growth_at: float | None = None
        last_trace_count = _delta_line_count(trace_snapshot)
        last_ui_count = _delta_line_count(ui_snapshot)

        if last_trace_count > 0 or last_ui_count > 0:
            last_growth_at = time.monotonic()

        while time.monotonic() < deadline:
            time.sleep(2)
            current_trace_count = _delta_line_count(trace_snapshot)
            current_ui_count = _delta_line_count(ui_snapshot)
            if current_trace_count > last_trace_count or current_ui_count > last_ui_count:
                last_growth_at = time.monotonic()
                last_trace_count = current_trace_count
                last_ui_count = current_ui_count
                continue
            if last_growth_at is None and time.monotonic() >= first_activity_deadline:
                break
            if (
                last_growth_at is not None
                and time.monotonic() - last_growth_at >= VSCODE_CHAT_IDLE_TIMEOUT_SEC
            ):
                break
    finally:
        if benchmark_window is not None:
            benchmark_window = _find_vscode_window_for_workspace(workspace_dir) or benchmark_window
            _close_vscode_window(benchmark_window)

    _write_text(session_dir / "assistant-response.txt", assistant_output)
    if stderr_chunks:
        _write_text(_stderr_path(session_dir, "vscode"), "\n\n".join(stderr_chunks))
    time.sleep(1)
    _materialize_log_delta(trace_path, trace_snapshot)
    _materialize_log_delta(ui_path, ui_snapshot)

    if blocker is not None:
        _update_session_meta(session_dir, runnerError=blocker)
    return (session_dir, exit_code, blocker)


def _run_track(
    *,
    track_id: str,
    task: dict[str, Any],
    scenario_pack_id: str,
    session_root: Path,
    codex_model: str,
    gemini_model: str,
    claude_model: str,
    gemini_timeout_sec: int,
    claude_timeout_sec: int,
    vscode_timeout_sec: int,
    attempt_kind: str,
) -> tuple[Path, int, str | None]:
    if track_id == "codex_cli":
        return _run_codex_track(
            task=task,
            scenario_pack_id=scenario_pack_id,
            session_root=session_root,
            model=codex_model,
            attempt_kind=attempt_kind,
        )
    if track_id == "gemini_cli":
        return _run_gemini_track(
            task=task,
            scenario_pack_id=scenario_pack_id,
            session_root=session_root,
            model=gemini_model,
            timeout_sec=gemini_timeout_sec,
            attempt_kind=attempt_kind,
        )
    if track_id == "claude_cli":
        return _run_claude_track(
            task=task,
            scenario_pack_id=scenario_pack_id,
            session_root=session_root,
            model=claude_model,
            timeout_sec=claude_timeout_sec,
            attempt_kind=attempt_kind,
        )
    if track_id == "vscode_ide":
        return _run_vscode_track(
            task=task,
            scenario_pack_id=scenario_pack_id,
            session_root=session_root,
            timeout_sec=vscode_timeout_sec,
            attempt_kind=attempt_kind,
        )
    raise KeyError(f"Unknown track: {track_id}")


def _execute_attempt(
    *,
    track_id: str,
    task: dict[str, Any],
    scenario_pack_id: str,
    session_root: Path,
    codex_model: str,
    gemini_model: str,
    claude_model: str,
    gemini_timeout_sec: int,
    claude_timeout_sec: int,
    vscode_timeout_sec: int,
    attempt_kind: str,
) -> dict[str, Any]:
    session_dir: Path | None = None
    exit_code = 1
    runner_blocker: str | None = None
    evidence: dict[str, Any] | None = None
    score: dict[str, Any] | None = None
    purpose = "capability" if attempt_kind == "capability" else attempt_kind
    started_at = _utc_now()
    started_monotonic = time.monotonic()
    try:
        session_dir, exit_code, runner_blocker = _run_track(
            track_id=track_id,
            task=task,
            scenario_pack_id=scenario_pack_id,
            session_root=session_root,
            codex_model=codex_model,
            gemini_model=gemini_model,
            claude_model=claude_model,
            gemini_timeout_sec=gemini_timeout_sec,
            claude_timeout_sec=claude_timeout_sec,
            vscode_timeout_sec=vscode_timeout_sec,
            attempt_kind=attempt_kind,
        )
    except Exception as exc:
        runner_blocker = str(exc)
        if session_dir is None:
            session_dir = _session_path(
                session_root,
                _session_name(track_id, task["id"]),
            )
        session_dir.mkdir(parents=True, exist_ok=True)
        _write_text(session_dir / "runner-error.txt", f"{type(exc).__name__}: {exc}\n")
        _update_session_meta(session_dir, runnerError=runner_blocker)

    if session_dir is not None and session_dir.exists():
        _trace_report(session_dir)
        try:
            evidence, score = _score_session(session_dir, task)
        except Exception as exc:
            runner_blocker = runner_blocker or f"score_session failed: {exc}"
            _write_text(session_dir / "score-error.txt", f"{type(exc).__name__}: {exc}\n")

    if attempt_kind == "capability":
        run_status = _classify_capability_status(exit_code=exit_code, evidence=evidence)
    else:
        run_status = _classify_readiness_status(exit_code=exit_code, evidence=evidence)

    blocker_category, blocker_message = _classify_blocker_category(
        track_id=track_id,
        purpose=purpose,
        exit_code=exit_code,
        evidence=evidence,
        runner_blocker=runner_blocker,
        session_dir=session_dir,
    )
    duration_ms = round((time.monotonic() - started_monotonic) * 1000, 2)
    capability_group = None if attempt_kind != "capability" else _scenario_capability_group(task)

    attempt: dict[str, Any] = {
        "trackId": track_id,
        "trackLabel": TRACK_BY_ID[track_id]["label"],
        "attemptKind": attempt_kind,
        "taskId": task["id"],
        "taskLabel": task.get("label", task["id"]),
        "scenarioId": task["id"] if attempt_kind == "capability" else None,
        "scenarioLabel": task.get("label", task["id"]) if attempt_kind == "capability" else None,
        "sessionDir": str(session_dir) if session_dir is not None else None,
        "startedAt": started_at,
        "durationMs": duration_ms,
        "exitCode": exit_code,
        "runStatus": run_status,
        "blockerCategory": blocker_category,
        "blocker": blocker_message or runner_blocker,
        "blockerRaw": runner_blocker,
        "overallScore": None,
        "overallStatus": None,
        "diagnosticScore": None,
        "toolCallCount": 0,
        "requestCount": 0,
        "errorCodes": [],
        "latencyToFirstUsefulToolCallMs": None,
        "capabilityGroup": capability_group,
        "expectedCapability": _expected_capability(task),
        "toolFamily": _tool_family(task),
        "requiresLiveOsApi": bool(task.get("requiresLiveOsApi") or task.get("requiresOsApi")),
        "requiresUiRuntime": bool(task.get("requiresUiRuntime")),
    }
    if evidence is not None:
        attempt["toolCallCount"] = len(evidence.get("toolCalls") or [])
        attempt["requestCount"] = int(
            evidence.get("traceSummary", {}).get("mcp", {}).get("requestCount") or 0
        )
        attempt["errorCodes"] = list(evidence.get("errorCodes") or [])
        attempt["latencyToFirstUsefulToolCallMs"] = (
            evidence.get("traceSummary", {})
            .get("hostSignals", {})
            .get("latencyToFirstUsefulToolCallMs")
        )
    if score is not None:
        if attempt_kind == "capability" and run_status == "scored":
            attempt["overallScore"] = score.get("overallScore")
            attempt["overallStatus"] = score.get("overallStatus")
        else:
            attempt["diagnosticScore"] = score.get("overallScore")
    return attempt


def _run_track_readiness(
    *,
    track_id: str,
    scenario_pack_id: str,
    session_root: Path,
    codex_model: str,
    gemini_model: str,
    claude_model: str,
    gemini_timeout_sec: int,
    claude_timeout_sec: int,
    vscode_timeout_sec: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    config_facts = _env_readiness_facts()
    readiness_task = _readiness_task_for_track(track_id)
    attempts = [
        _execute_attempt(
            track_id=track_id,
            task=readiness_task,
            scenario_pack_id=scenario_pack_id,
            session_root=session_root,
            codex_model=codex_model,
            gemini_model=gemini_model,
            claude_model=claude_model,
            gemini_timeout_sec=gemini_timeout_sec,
            claude_timeout_sec=claude_timeout_sec,
            vscode_timeout_sec=vscode_timeout_sec,
            attempt_kind="readiness",
        )
    ]
    if attempts[0]["runStatus"] != "ready" and track_id in RECOVERY_TRACK_IDS:
        attempts.append(
            _execute_attempt(
                track_id=track_id,
                task=readiness_task,
                scenario_pack_id=scenario_pack_id,
                session_root=session_root,
                codex_model=codex_model,
                gemini_model=gemini_model,
                claude_model=claude_model,
                gemini_timeout_sec=gemini_timeout_sec,
                claude_timeout_sec=claude_timeout_sec,
                vscode_timeout_sec=vscode_timeout_sec,
                attempt_kind="recovery",
            )
        )
    final_attempt = attempts[-1]
    first_attempt = attempts[0]
    outcome = "ready" if final_attempt["runStatus"] == "ready" else "not_ready"
    readiness = {
        "trackId": track_id,
        "trackLabel": TRACK_BY_ID[track_id]["label"],
        "configVisibility": config_facts,
        "attempts": attempts,
        "attemptCount": len(attempts),
        "outcome": outcome,
        "firstAttemptOutcome": first_attempt["runStatus"],
        "finalAttemptKind": final_attempt["attemptKind"],
        "recovered": (
            first_attempt["runStatus"] != "ready" and final_attempt["runStatus"] == "ready"
        ),
        "blockerCategory": None if outcome == "ready" else final_attempt["blockerCategory"],
        "blocker": None if outcome == "ready" else final_attempt["blocker"],
        "readinessLatencyMs": final_attempt.get("latencyToFirstUsefulToolCallMs"),
        "requestCount": final_attempt.get("requestCount", 0),
        "toolCallCount": final_attempt.get("toolCallCount", 0),
        "liveOsReady": bool(config_facts["liveOsReady"]),
    }
    return readiness, attempts


def _make_skipped_capability_attempt(
    *,
    track_id: str,
    task: dict[str, Any],
    reason_category: str,
    reason_message: str,
) -> dict[str, Any]:
    return {
        "trackId": track_id,
        "trackLabel": TRACK_BY_ID[track_id]["label"],
        "attemptKind": "capability",
        "taskId": task["id"],
        "taskLabel": task.get("label", task["id"]),
        "scenarioId": task["id"],
        "scenarioLabel": task.get("label", task["id"]),
        "sessionDir": None,
        "startedAt": _utc_now(),
        "durationMs": 0.0,
        "exitCode": None,
        "runStatus": "skipped",
        "blockerCategory": reason_category,
        "blocker": reason_message,
        "blockerRaw": None,
        "overallScore": None,
        "overallStatus": None,
        "diagnosticScore": None,
        "toolCallCount": 0,
        "requestCount": 0,
        "errorCodes": [],
        "latencyToFirstUsefulToolCallMs": None,
        "capabilityGroup": _scenario_capability_group(task),
        "expectedCapability": _expected_capability(task),
        "toolFamily": _tool_family(task),
        "requiresLiveOsApi": bool(task.get("requiresLiveOsApi") or task.get("requiresOsApi")),
        "requiresUiRuntime": bool(task.get("requiresUiRuntime")),
    }


def _selected_scenarios(
    pack: dict[str, Any],
    requested_ids: set[str] | None,
) -> list[dict[str, Any]]:
    scenarios = [scenario for scenario in pack["scenarios"] if isinstance(scenario, dict)]
    if not requested_ids:
        return scenarios
    return [scenario for scenario in scenarios if scenario["id"] in requested_ids]


def _bucket_summary(attempts: list[dict[str, Any]]) -> dict[str, Any]:
    scored_attempts = [
        attempt
        for attempt in attempts
        if attempt.get("runStatus") == "scored" and attempt.get("overallScore") is not None
    ]
    average = None
    if scored_attempts:
        average = round(
            sum(float(attempt["overallScore"]) for attempt in scored_attempts)
            / len(scored_attempts),
            4,
        )
    return {
        "attemptCount": len(attempts),
        "scoredCount": len(scored_attempts),
        "averageScore": average,
        "statuses": {
            status: len([attempt for attempt in attempts if attempt.get("runStatus") == status])
            for status in sorted({str(attempt.get("runStatus")) for attempt in attempts})
        },
    }


def _summarize_attempts(
    *,
    scenario_pack: dict[str, Any],
    readiness_results: dict[str, dict[str, Any]],
    attempts: list[dict[str, Any]],
    readiness_only: bool = False,
) -> tuple[dict[str, Any], str]:
    readiness_attempts = [
        attempt for attempt in attempts if attempt["attemptKind"] != "capability"
    ]
    capability_attempts = [
        attempt for attempt in attempts if attempt["attemptKind"] == "capability"
    ]
    scenario_labels = {
        scenario["id"]: scenario.get("label", scenario["id"])
        for scenario in scenario_pack["scenarios"]
    }
    active_tracks = [track for track in TRACKS if track["id"] in readiness_results]
    aggregate: dict[str, Any] = {
        "generatedAt": _utc_now(),
        "scenarioPack": scenario_pack["id"],
        "attempts": attempts,
        "readiness": {
            "summary": {
                "trackCount": len(readiness_results),
                "readyCount": len(
                    [
                        result
                        for result in readiness_results.values()
                        if result["outcome"] == "ready"
                    ]
                ),
                "firstAttemptReadyCount": len(
                    [
                        result
                        for result in readiness_results.values()
                        if result["firstAttemptOutcome"] == "ready"
                    ]
                ),
                "recoveredCount": len(
                    [result for result in readiness_results.values() if result["recovered"]]
                ),
                "notReadyCount": len(
                    [
                        result
                        for result in readiness_results.values()
                        if result["outcome"] != "ready"
                    ]
                ),
            },
            "attempts": readiness_attempts,
        },
        "capability": {
            "attempts": capability_attempts,
            "toolFamilies": {},
            "expectedCapabilities": {},
        },
        "tracks": {},
    }

    for track in active_tracks:
        readiness = readiness_results[track["id"]]
        track_capability_attempts = [
            attempt for attempt in capability_attempts if attempt["trackId"] == track["id"]
        ]
        capability_summary = _bucket_summary(track_capability_attempts)
        capability_summary["capabilities"] = {}
        capability_summary["toolFamilies"] = {}
        for capability in sorted(
            {
                str(attempt.get("expectedCapability"))
                for attempt in track_capability_attempts
                if attempt.get("expectedCapability")
            }
        ):
            capability_attempts_for_name = [
                attempt
                for attempt in track_capability_attempts
                if attempt.get("expectedCapability") == capability
            ]
            capability_summary["capabilities"][capability] = _bucket_summary(
                capability_attempts_for_name
            )
        for family in sorted(
            {
                str(attempt.get("toolFamily"))
                for attempt in track_capability_attempts
                if attempt.get("toolFamily")
            }
        ):
            family_attempts = [
                attempt
                for attempt in track_capability_attempts
                if attempt.get("toolFamily") == family
            ]
            capability_summary["toolFamilies"][family] = _bucket_summary(family_attempts)
        aggregate["tracks"][track["id"]] = {
            "label": track["label"],
            "readiness": readiness,
            "capability": capability_summary,
        }

    for family in sorted(
        {
            str(attempt.get("toolFamily"))
            for attempt in capability_attempts
            if attempt.get("toolFamily")
        }
    ):
        family_attempts = [
            attempt for attempt in capability_attempts if attempt.get("toolFamily") == family
        ]
        aggregate["capability"]["toolFamilies"][family] = _bucket_summary(family_attempts)
    for capability in sorted(
        {
            str(attempt.get("expectedCapability"))
            for attempt in capability_attempts
            if attempt.get("expectedCapability")
        }
    ):
        capability_attempts_for_name = [
            attempt
            for attempt in capability_attempts
            if attempt.get("expectedCapability") == capability
        ]
        aggregate["capability"]["expectedCapabilities"][capability] = _bucket_summary(
            capability_attempts_for_name
        )

    lines = [
        "# MCP Geo Unattended Client Evaluation",
        f"Generated: {aggregate['generatedAt']}",
        f"Scenario pack: {scenario_pack['id']}",
        "",
        "## Readiness Summary",
        (
            "| Track | Outcome | First Attempt | Final Attempt | Recovery | "
            "Live OS Ready | Config | Blocker |"
        ),
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for track in active_tracks:
        readiness = aggregate["tracks"][track["id"]]["readiness"]
        config = readiness["configVisibility"]
        config_text = (
            f"key={str(config['osApiKeyPresent']).lower()}, "
            f"file={str(config['osApiKeyFilePresent']).lower()}, "
            f"toolset={config.get('defaultToolset') or 'unset'}, "
            f"include={config.get('includeToolsets') or 'unset'}"
        )
        blocker_text = readiness.get("blockerCategory") or readiness.get("blocker") or "none"
        lines.append(
            f"| {track['label']} | {readiness['outcome']} | {readiness['firstAttemptOutcome']} | "
            f"{readiness['finalAttemptKind']} | {str(readiness['recovered']).lower()} | "
            f"{str(readiness['liveOsReady']).lower()} | {config_text} | {blocker_text} |"
        )

    if not readiness_only:
        lines.extend(
            [
                "",
                "## Capability Summary",
                "| Track | Attempts | Scored | Average | Statuses |",
                "| --- | ---: | ---: | ---: | --- |",
            ]
        )
        for track in active_tracks:
            summary = aggregate["tracks"][track["id"]]["capability"]
            average = "n/a" if summary["averageScore"] is None else f"{summary['averageScore']:.2f}"
            statuses = ", ".join(
                f"{status}={count}" for status, count in sorted(summary["statuses"].items())
            ) or "none"
            lines.append(
                f"| {track['label']} | {summary['attemptCount']} | {summary['scoredCount']} | "
                f"{average} | {statuses} |"
            )

        lines.extend(
            [
                "",
                "## Capability Breakdown",
                "| Track | Capability | Attempts | Scored | Average |",
                "| --- | --- | ---: | ---: | ---: |",
            ]
        )
        for track in active_tracks:
            capabilities = aggregate["tracks"][track["id"]]["capability"]["capabilities"]
            for capability, summary in sorted(capabilities.items()):
                average = (
                    "n/a"
                    if summary["averageScore"] is None
                    else f"{summary['averageScore']:.2f}"
                )
                lines.append(
                    f"| {track['label']} | {capability} | {summary['attemptCount']} | "
                    f"{summary['scoredCount']} | {average} |"
                )

        lines.extend(
            [
                "",
                "## Tool Family Summary",
                "| Tool Family | Attempts | Scored | Average | Statuses |",
                "| --- | ---: | ---: | ---: | --- |",
            ]
        )
        for family, summary in sorted(aggregate["capability"]["toolFamilies"].items()):
            average = "n/a" if summary["averageScore"] is None else f"{summary['averageScore']:.2f}"
            statuses = ", ".join(
                f"{status}={count}" for status, count in sorted(summary["statuses"].items())
            ) or "none"
            lines.append(
                f"| {family} | {summary['attemptCount']} | {summary['scoredCount']} | "
                f"{average} | {statuses} |"
            )

        lines.extend(
            [
                "",
                "## Scenario Matrix",
                "| Scenario | " + " | ".join(track["label"] for track in active_tracks) + " |",
                "| --- | " + " | ".join("---" for _track in active_tracks) + " |",
            ]
        )
        for scenario in scenario_pack["scenarios"]:
            row = [scenario_labels[scenario["id"]]]
            for track in active_tracks:
                readiness = readiness_results[track["id"]]
                if readiness["outcome"] != "ready":
                    blocker = (
                        readiness.get("blockerCategory")
                        or readiness.get("blocker")
                        or "not_ready"
                    )
                    row.append(f"not_ready<br>{blocker}")
                    continue
                attempt = next(
                    (
                        item
                        for item in capability_attempts
                        if item["trackId"] == track["id"] and item["scenarioId"] == scenario["id"]
                    ),
                    None,
                )
                if attempt is None:
                    row.append("missing")
                    continue
                if attempt["runStatus"] != "scored" or attempt.get("overallScore") is None:
                    cell = attempt["runStatus"]
                    blocker = attempt.get("blockerCategory") or attempt.get("blocker")
                    if blocker:
                        cell = f"{cell}<br>{blocker}"
                    diagnostic = attempt.get("diagnosticScore")
                    if diagnostic is not None:
                        cell = f"{cell}<br>diagnostic={float(diagnostic):.2f}"
                    row.append(cell)
                    continue
                cell = f"{attempt['runStatus']} ({float(attempt['overallScore']):.2f})"
                blocker = attempt.get("blockerCategory") or attempt.get("blocker")
                if blocker:
                    cell = f"{cell}<br>{blocker}"
                row.append(cell)
            lines.append(f"| {' | '.join(row)} |")

    lines.extend(
        [
            "",
            "## Attempt Log",
        ]
    )
    for attempt in attempts:
        label = attempt.get("scenarioId") or attempt["taskId"]
        lines.append(
            f"- `{attempt['trackId']}` `{attempt['attemptKind']}` `{label}`: {attempt['runStatus']}"
            + (
                f", score={float(attempt['overallScore']):.2f}"
                if attempt.get("overallScore") is not None
                else ""
            )
            + (
                f", diagnosticScore={float(attempt['diagnosticScore']):.2f}"
                if attempt.get("diagnosticScore") is not None
                else ""
            )
            + (
                f", blocker={attempt['blockerCategory']}"
                if attempt.get("blockerCategory")
                else ""
            )
            + (f", session={attempt['sessionDir']}" if attempt.get("sessionDir") else "")
        )

    return aggregate, "\n".join(lines).strip() + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run unattended MCP Geo interop evaluation across client hosts."
    )
    parser.add_argument("--scenario-pack", default=str(DEFAULT_SCENARIO_PACK))
    parser.add_argument(
        "--tracks",
        default=",".join(DEFAULT_TRACKS),
        help="Comma-separated track ids. Default: codex_cli,gemini_cli,claude_cli,vscode_ide",
    )
    parser.add_argument(
        "--scenario-ids",
        help="Optional comma-separated scenario ids from the host benchmark pack.",
    )
    parser.add_argument("--session-root", default=str(DEFAULT_SESSION_ROOT))
    parser.add_argument("--out-prefix")
    parser.add_argument("--codex-model", default="gpt-5.4")
    parser.add_argument("--gemini-model", default="")
    parser.add_argument("--claude-model", default="")
    parser.add_argument("--gemini-timeout-sec", type=int, default=90)
    parser.add_argument("--claude-timeout-sec", type=int, default=60)
    parser.add_argument("--vscode-timeout-sec", type=int, default=45)
    parser.add_argument(
        "--readiness-only",
        action="store_true",
        help="Run readiness probes only and skip capability scenarios.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    scenario_pack_path = Path(args.scenario_pack).resolve()
    scenario_pack = host_benchmark.load_scenario_pack(scenario_pack_path)
    session_root = Path(args.session_root).resolve()
    session_root.mkdir(parents=True, exist_ok=True)

    requested_tracks = [item.strip() for item in args.tracks.split(",") if item.strip()]
    for track_id in requested_tracks:
        if track_id not in TRACK_BY_ID:
            raise SystemExit(f"Unknown track id: {track_id}")

    requested_ids = None
    if args.scenario_ids:
        requested_ids = {item.strip() for item in args.scenario_ids.split(",") if item.strip()}
    scenarios = _selected_scenarios(scenario_pack, requested_ids)
    if not scenarios and not args.readiness_only:
        raise SystemExit("No scenarios selected.")

    readiness_results: dict[str, dict[str, Any]] = {}
    all_attempts: list[dict[str, Any]] = []

    for track_id in requested_tracks:
        readiness, readiness_attempts = _run_track_readiness(
            track_id=track_id,
            scenario_pack_id=scenario_pack["id"],
            session_root=session_root,
            codex_model=args.codex_model,
            gemini_model=args.gemini_model,
            claude_model=args.claude_model,
            gemini_timeout_sec=args.gemini_timeout_sec,
            claude_timeout_sec=args.claude_timeout_sec,
            vscode_timeout_sec=args.vscode_timeout_sec,
        )
        readiness_results[track_id] = readiness
        all_attempts.extend(readiness_attempts)
        if args.readiness_only or readiness["outcome"] != "ready":
            continue

        for scenario in scenarios:
            if bool(scenario.get("requiresLiveOsApi") or scenario.get("requiresOsApi")) and not (
                readiness["liveOsReady"]
            ):
                all_attempts.append(
                    _make_skipped_capability_attempt(
                        track_id=track_id,
                        task=scenario,
                        reason_category="server_no_live_key",
                        reason_message=(
                            "live OS scenario skipped because readiness did not observe "
                            "OS_API_KEY or OS_API_KEY_FILE"
                        ),
                    )
                )
                continue
            all_attempts.append(
                _execute_attempt(
                    track_id=track_id,
                    task=scenario,
                    scenario_pack_id=scenario_pack["id"],
                    session_root=session_root,
                    codex_model=args.codex_model,
                    gemini_model=args.gemini_model,
                    claude_model=args.claude_model,
                    gemini_timeout_sec=args.gemini_timeout_sec,
                    claude_timeout_sec=args.claude_timeout_sec,
                    vscode_timeout_sec=args.vscode_timeout_sec,
                    attempt_kind="capability",
                )
            )

    aggregate, markdown = _summarize_attempts(
        scenario_pack=scenario_pack,
        readiness_results=readiness_results,
        attempts=all_attempts,
        readiness_only=args.readiness_only,
    )
    date_stamp = dt.date.today().isoformat()
    out_prefix = (
        Path(args.out_prefix).resolve()
        if args.out_prefix
        else DEFAULT_REPORT_ROOT / f"client_interop_unattended_eval_{date_stamp}"
    )
    out_prefix.parent.mkdir(parents=True, exist_ok=True)
    json_path = out_prefix.with_suffix(".json")
    md_path = out_prefix.with_suffix(".md")
    json_path.write_text(json.dumps(aggregate, indent=2), encoding="utf-8")
    md_path.write_text(markdown, encoding="utf-8")
    for track_id, readiness in readiness_results.items():
        readiness_path = out_prefix.parent / f"{out_prefix.stem}.{track_id}.readiness.json"
        readiness_path.write_text(json.dumps(readiness, indent=2), encoding="utf-8")
    print(md_path)
    print(json_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
