#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import scripts.host_benchmark as host_benchmark  # noqa: E402

DEFAULT_SCENARIO_PACK = host_benchmark.DEFAULT_SCENARIO_PACK
DEFAULT_SESSION_ROOT = REPO_ROOT / "logs" / "sessions"
DEFAULT_REPORT_ROOT = REPO_ROOT / "docs" / "reports"
DEFAULT_TRACKS = ("codex_cli", "gemini_cli", "claude_cli", "vscode_ide")
DEFAULT_VSCODE_TRACE_PATH = REPO_ROOT / "logs" / "vscode-mcp-trace.jsonl"
DEFAULT_VSCODE_UI_PATH = REPO_ROOT / "logs" / "ui-events.vscode-trace.jsonl"
DEFAULT_GEMINI_SERVER = "mcp-geo-benchmark"

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


def _utc_now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _timestamp_slug() -> str:
    return dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")


def _slug(value: str) -> str:
    text = "".join(ch.lower() if ch.isalnum() else "-" for ch in value)
    while "--" in text:
        text = text.replace("--", "-")
    return text.strip("-") or "session"


def _scenario_prompt(scenario: dict[str, Any]) -> str:
    return host_benchmark._prompt_for_scenario(scenario)


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
    keys = (
        "OS_API_KEY",
        "OS_API_KEY_FILE",
        "ONS_LIVE_ENABLED",
        "STDIO_KEY",
        "BEARER_TOKENS",
        "MCP_GEO_DOCKER_BUILD",
        "MCP_TOOLS_DEFAULT_TOOLSET",
        "MCP_TOOLS_DEFAULT_INCLUDE_TOOLSETS",
        "MCP_TOOLS_DEFAULT_EXCLUDE_TOOLSETS",
    )
    env = {key: value for key in keys if (value := os.getenv(key))}
    env.setdefault("MCP_GEO_DOCKER_BUILD", "never")
    return env


def _session_name(track_id: str, scenario_id: str) -> str:
    return f"{_timestamp_slug()}-{_slug(track_id)}-{_slug(scenario_id)}"


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
    scenario_id: str,
    model: str,
    track: dict[str, str],
) -> None:
    host_benchmark._write_initial_session_meta(
        session_dir,
        command=command,
        scenario_pack=scenario_pack,
        scenario_id=scenario_id,
        model=model,
        source=track["source"],
        surface=track["surface"],
        host_profile=track["hostProfile"],
        client_version=_client_version(track["clientCommand"]),
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
    path.write_text(text, encoding="utf-8")


def _coerce_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _stderr_path(session_dir: Path, client: str) -> Path:
    return session_dir / f"{client}-exec.stderr.txt"


def _trace_report(session_dir: Path) -> None:
    subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "trace_report.py"), str(session_dir)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


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
    scenario: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    cached = _load_existing_score_artifacts(session_dir)
    if cached is not None:
        return cached
    evidence, score = host_benchmark.score_session(session_dir, scenario)
    host_benchmark.write_score_artifacts(session_dir, evidence, score)
    return evidence, score


def _classify_attempt(
    *,
    exit_code: int,
    evidence: dict[str, Any] | None,
) -> tuple[str, str | None]:
    if exit_code != 0:
        return ("runner_error", f"client exited with code {exit_code}")
    if evidence is None:
        return ("runner_error", "no evidence captured")
    request_count = int(evidence.get("traceSummary", {}).get("mcp", {}).get("requestCount") or 0)
    tool_calls = evidence.get("toolCalls") or []
    if request_count == 0:
        return ("no_mcp_traffic", "client produced no MCP traffic")
    if not tool_calls:
        return ("startup_only", "client initialized and listed capabilities but made no tool calls")
    return ("scored", None)


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


def _run_codex_track(
    *,
    scenario: dict[str, Any],
    scenario_pack_path: Path,
    scenario_pack_id: str,
    session_root: Path,
    model: str,
) -> tuple[Path, int, str | None]:
    name = _session_name("codex_cli", scenario["id"])
    latest_before = _latest_session_dir(session_root)
    args = argparse.Namespace(
        scenario_id=scenario["id"],
        scenario_pack=str(scenario_pack_path),
        model=model,
        server_name="mcp-geo",
        wrapper=str(REPO_ROOT / "scripts" / "codex-mcp-local"),
        session_root=str(session_root),
        name=name,
    )
    blocker: str | None = None
    exit_code = 0
    try:
        host_benchmark.cmd_run_codex_cli(args)
    except Exception as exc:
        exit_code = 1
        blocker = str(exc)
    session_dir = _locate_session_dir(session_root, name=name, latest_before=latest_before)
    if session_dir is None:
        session_dir = _session_path(session_root, name)
        session_dir.mkdir(parents=True, exist_ok=True)
    _update_session_meta(
        session_dir,
        scenarioPack=scenario_pack_id,
        scenarioId=scenario["id"],
    )
    if blocker:
        _update_session_meta(session_dir, runnerError=blocker)
        _write_text(session_dir / "runner-error.txt", blocker + "\n")
    return (session_dir, exit_code, blocker)


def _run_gemini_track(
    *,
    scenario: dict[str, Any],
    scenario_pack_id: str,
    session_root: Path,
    model: str,
    timeout_sec: int,
) -> tuple[Path, int, str | None]:
    track = TRACK_BY_ID["gemini_cli"]
    name = _session_name(track["id"], scenario["id"])
    session_dir = host_benchmark._ensure_session_dir(session_root, name)
    server_name = f"{DEFAULT_GEMINI_SERVER}-{_slug(session_dir.name)}"
    prompt = _scenario_prompt(scenario)
    server_config = host_benchmark._build_temp_stdio_server(
        session_dir,
        wrapper=REPO_ROOT / "scripts" / "gemini-mcp-local",
        inherited_env=_build_inherited_env(),
    )
    command = [
        "gemini",
        "--allowed-mcp-server-names",
        server_name,
        "--approval-mode",
        "yolo",
        "--output-format",
        "json",
    ]
    if model:
        command.extend(["--model", model])
    command.extend(["--prompt", prompt])
    _initial_session_meta(
        session_dir,
        command=command,
        scenario_pack=scenario_pack_id,
        scenario_id=scenario["id"],
        model=model,
        track=track,
    )
    _update_session_paths(
        session_dir,
        assistantResponse=str(session_dir / "assistant-response.txt"),
        clientStderr=str(_stderr_path(session_dir, "gemini")),
    )
    exit_code = 0
    blocker: str | None = None
    proc: subprocess.CompletedProcess[str] | None = None
    with tempfile.TemporaryDirectory(prefix="mcp-geo-gemini-project-") as temp_project:
        project_dir = Path(temp_project)
        try:
            _gemini_remove_server(server_name, cwd=project_dir)
            _gemini_add_stdio_server(server_name, server_config, cwd=project_dir)
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
                if exc.stderr:
                    _write_text(_stderr_path(session_dir, "gemini"), _coerce_text(exc.stderr))
                _update_session_meta(session_dir, runnerError=blocker)
                return (session_dir, 124, blocker)
            _write_text(session_dir / "assistant-response.txt", proc.stdout)
            if proc.stderr:
                _write_text(_stderr_path(session_dir, "gemini"), proc.stderr)
            exit_code = proc.returncode
        finally:
            _gemini_remove_server(server_name, cwd=project_dir)
    if proc is not None and proc.returncode != 0:
        blocker = "gemini_cli_failed"
        _update_session_meta(session_dir, runnerError=blocker)
    return (session_dir, exit_code, blocker)


def _run_claude_track(
    *,
    scenario: dict[str, Any],
    scenario_pack_id: str,
    session_root: Path,
    model: str,
    timeout_sec: int,
) -> tuple[Path, int, str | None]:
    track = TRACK_BY_ID["claude_cli"]
    name = _session_name(track["id"], scenario["id"])
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
    prompt = _scenario_prompt(scenario)
    command = ["claude", "--strict-mcp-config", "--mcp-config", str(config_path)]
    if model:
        command.extend(["--model", model])
    command.extend(["-p", "--output-format", "json", prompt])
    _initial_session_meta(
        session_dir,
        command=command,
        scenario_pack=scenario_pack_id,
        scenario_id=scenario["id"],
        model=model,
        track=track,
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
            if exc.stderr:
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


def _run_vscode_track(
    *,
    scenario: dict[str, Any],
    scenario_pack_id: str,
    session_root: Path,
    timeout_sec: int,
) -> tuple[Path, int, str | None]:
    track = TRACK_BY_ID["vscode_ide"]
    name = _session_name(track["id"], scenario["id"])
    session_dir = host_benchmark._ensure_session_dir(session_root, name)
    trace_before = len(_read_lines(DEFAULT_VSCODE_TRACE_PATH))
    ui_before = len(_read_lines(DEFAULT_VSCODE_UI_PATH))
    prompt = _scenario_prompt(scenario)
    command = ["code", "chat", "--mode", "agent", "--reuse-window", prompt]
    _initial_session_meta(
        session_dir,
        command=command,
        scenario_pack=scenario_pack_id,
        scenario_id=scenario["id"],
        model="copilot-agent",
        track=track,
    )
    _update_session_paths(
        session_dir,
        assistantResponse=str(session_dir / "assistant-response.txt"),
        clientStderr=str(_stderr_path(session_dir, "vscode")),
    )
    workspace_command = ["code", "--reuse-window", "."]
    workspace_proc = subprocess.run(
        workspace_command,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if workspace_proc.returncode != 0:
        if workspace_proc.stderr:
            _write_text(_stderr_path(session_dir, "vscode"), workspace_proc.stderr)
        blocker = "vscode_workspace_open_failed"
        _update_session_meta(session_dir, runnerError=blocker)
        return (session_dir, workspace_proc.returncode or 1, blocker)
    time.sleep(2)
    proc = subprocess.run(
        command,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    _write_text(session_dir / "assistant-response.txt", proc.stdout)
    if proc.stderr:
        _write_text(_stderr_path(session_dir, "vscode"), proc.stderr)

    deadline = time.monotonic() + max(timeout_sec, 5)
    last_growth_at: float | None = None
    last_trace_count = trace_before
    last_ui_count = ui_before

    while time.monotonic() < deadline:
        time.sleep(2)
        current_trace_count = len(_read_lines(DEFAULT_VSCODE_TRACE_PATH))
        current_ui_count = len(_read_lines(DEFAULT_VSCODE_UI_PATH))
        if current_trace_count > last_trace_count or current_ui_count > last_ui_count:
            last_growth_at = time.monotonic()
            last_trace_count = current_trace_count
            last_ui_count = current_ui_count
            continue
        if last_growth_at is not None and time.monotonic() - last_growth_at >= 6:
            break

    trace_delta = _read_lines(DEFAULT_VSCODE_TRACE_PATH)[trace_before:]
    ui_delta = _read_lines(DEFAULT_VSCODE_UI_PATH)[ui_before:]
    _write_lines(session_dir / "mcp-stdio-trace.jsonl", trace_delta)
    _write_lines(session_dir / "ui-events.jsonl", ui_delta)
    blocker = None
    if proc.returncode != 0:
        blocker = "vscode_chat_failed"
        _update_session_meta(session_dir, runnerError=blocker)
    return (session_dir, proc.returncode, blocker)


def _run_track(
    *,
    track_id: str,
    scenario: dict[str, Any],
    scenario_pack_path: Path,
    scenario_pack_id: str,
    session_root: Path,
    codex_model: str,
    gemini_model: str,
    claude_model: str,
    gemini_timeout_sec: int,
    claude_timeout_sec: int,
    vscode_timeout_sec: int,
) -> tuple[Path, int, str | None]:
    if track_id == "codex_cli":
        return _run_codex_track(
            scenario=scenario,
            scenario_pack_path=scenario_pack_path,
            scenario_pack_id=scenario_pack_id,
            session_root=session_root,
            model=codex_model,
        )
    if track_id == "gemini_cli":
        return _run_gemini_track(
            scenario=scenario,
            scenario_pack_id=scenario_pack_id,
            session_root=session_root,
            model=gemini_model,
            timeout_sec=gemini_timeout_sec,
        )
    if track_id == "claude_cli":
        return _run_claude_track(
            scenario=scenario,
            scenario_pack_id=scenario_pack_id,
            session_root=session_root,
            model=claude_model,
            timeout_sec=claude_timeout_sec,
        )
    if track_id == "vscode_ide":
        return _run_vscode_track(
            scenario=scenario,
            scenario_pack_id=scenario_pack_id,
            session_root=session_root,
            timeout_sec=vscode_timeout_sec,
        )
    raise KeyError(f"Unknown track: {track_id}")


def _summarize_attempts(
    *,
    scenario_pack: dict[str, Any],
    attempts: list[dict[str, Any]],
) -> tuple[dict[str, Any], str]:
    scenario_labels = {
        scenario["id"]: scenario.get("label", scenario["id"])
        for scenario in scenario_pack["scenarios"]
    }
    aggregate: dict[str, Any] = {
        "generatedAt": _utc_now(),
        "scenarioPack": scenario_pack["id"],
        "attempts": attempts,
        "tracks": {},
    }
    for track in TRACKS:
        track_attempts = [attempt for attempt in attempts if attempt["trackId"] == track["id"]]
        scored_attempts = [
            attempt
            for attempt in track_attempts
            if attempt["runStatus"] == "scored" and attempt.get("overallScore") is not None
        ]
        average = None
        if scored_attempts:
            average = round(
                sum(float(attempt["overallScore"]) for attempt in scored_attempts)
                / len(scored_attempts),
                4,
            )
        aggregate["tracks"][track["id"]] = {
            "label": track["label"],
            "attemptCount": len(track_attempts),
            "scoredCount": len(scored_attempts),
            "averageScore": average,
            "statuses": {
                status: len(
                    [attempt for attempt in track_attempts if attempt["runStatus"] == status]
                )
                for status in sorted({attempt["runStatus"] for attempt in track_attempts})
            },
        }

    lines = [
        "# MCP Geo Unattended Client Evaluation",
        f"Generated: {aggregate['generatedAt']}",
        f"Scenario pack: {scenario_pack['id']}",
        "",
        "## Track Summary",
        "| Track | Attempts | Scored | Average | Statuses |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for track in TRACKS:
        summary = aggregate["tracks"][track["id"]]
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
            "## Scenario Matrix",
            "| Scenario | "
            + " | ".join(track["label"] for track in TRACKS)
            + " |",
            "| --- | " + " | ".join("---" for _track in TRACKS) + " |",
        ]
    )
    for scenario in scenario_pack["scenarios"]:
        row = [scenario_labels[scenario["id"]]]
        for track in TRACKS:
            attempt = next(
                (
                    item
                    for item in attempts
                    if item["trackId"] == track["id"] and item["scenarioId"] == scenario["id"]
                ),
                None,
            )
            if attempt is None:
                row.append("missing")
                continue
            if attempt["runStatus"] != "scored" or attempt.get("overallScore") is None:
                cell = attempt["runStatus"]
                blocker = attempt.get("blocker")
                if blocker:
                    cell = f"{cell}<br>{blocker}"
                diagnostic = attempt.get("diagnosticScore")
                if diagnostic is not None:
                    cell = f"{cell}<br>diagnostic={float(diagnostic):.2f}"
                row.append(cell)
                continue
            blocker = attempt.get("blocker")
            cell = f"{attempt['runStatus']} ({float(attempt['overallScore']):.2f})"
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
        lines.append(
            f"- `{attempt['trackId']}` `{attempt['scenarioId']}`: {attempt['runStatus']}"
            + (
                f", score={float(attempt['overallScore']):.2f}"
                if attempt["runStatus"] == "scored" and attempt.get("overallScore") is not None
                else ""
            )
            + (
                f", diagnosticScore={float(attempt['diagnosticScore']):.2f}"
                if attempt.get("diagnosticScore") is not None
                else ""
            )
            + (f", blocker={attempt['blocker']}" if attempt.get("blocker") else "")
            + (f", session={attempt['sessionDir']}" if attempt.get("sessionDir") else "")
        )

    return aggregate, "\n".join(lines).strip() + "\n"


def _selected_scenarios(
    pack: dict[str, Any],
    requested_ids: set[str] | None,
) -> list[dict[str, Any]]:
    scenarios = [scenario for scenario in pack["scenarios"] if isinstance(scenario, dict)]
    if not requested_ids:
        return scenarios
    return [scenario for scenario in scenarios if scenario["id"] in requested_ids]


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
    if not scenarios:
        raise SystemExit("No scenarios selected.")

    attempts: list[dict[str, Any]] = []

    for track_id in requested_tracks:
        for scenario in scenarios:
            session_dir: Path | None = None
            exit_code = 1
            blocker: str | None = None
            evidence: dict[str, Any] | None = None
            score: dict[str, Any] | None = None
            try:
                session_dir, exit_code, runner_blocker = _run_track(
                    track_id=track_id,
                    scenario=scenario,
                    scenario_pack_path=scenario_pack_path,
                    scenario_pack_id=scenario_pack["id"],
                    session_root=session_root,
                    codex_model=args.codex_model,
                    gemini_model=args.gemini_model,
                    claude_model=args.claude_model,
                    gemini_timeout_sec=args.gemini_timeout_sec,
                    claude_timeout_sec=args.claude_timeout_sec,
                    vscode_timeout_sec=args.vscode_timeout_sec,
                )
                blocker = runner_blocker
            except Exception as exc:
                blocker = str(exc)
                if session_dir is None:
                    session_dir = _session_path(
                        session_root,
                        _session_name(track_id, scenario["id"]),
                    )
                session_dir.mkdir(parents=True, exist_ok=True)
                _write_text(session_dir / "runner-error.txt", f"{type(exc).__name__}: {exc}\n")
                _update_session_meta(session_dir, runnerError=str(exc))

            if session_dir.exists():
                _trace_report(session_dir)
                try:
                    evidence, score = _score_session(session_dir, scenario)
                except Exception as exc:
                    blocker = blocker or f"score_session failed: {exc}"
                    _write_text(
                        session_dir / "score-error.txt",
                        f"{type(exc).__name__}: {exc}\n",
                    )

            run_status, classified_blocker = _classify_attempt(
                exit_code=exit_code,
                evidence=evidence,
            )
            blocker = blocker or classified_blocker
            attempt: dict[str, Any] = {
                "trackId": track_id,
                "trackLabel": TRACK_BY_ID[track_id]["label"],
                "scenarioId": scenario["id"],
                "scenarioLabel": scenario.get("label", scenario["id"]),
                "sessionDir": str(session_dir) if session_dir is not None else None,
                "exitCode": exit_code,
                "runStatus": run_status,
                "blocker": blocker,
                "overallScore": None,
                "overallStatus": None,
                "diagnosticScore": None,
                "toolCallCount": 0,
                "requestCount": 0,
            }
            if evidence is not None:
                attempt["toolCallCount"] = len(evidence.get("toolCalls") or [])
                attempt["requestCount"] = int(
                    evidence.get("traceSummary", {}).get("mcp", {}).get("requestCount") or 0
                )
            if score is not None:
                if run_status == "scored":
                    attempt["overallScore"] = score.get("overallScore")
                    attempt["overallStatus"] = score.get("overallStatus")
                else:
                    attempt["diagnosticScore"] = score.get("overallScore")
            attempts.append(attempt)

    aggregate, markdown = _summarize_attempts(scenario_pack=scenario_pack, attempts=attempts)
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
    print(md_path)
    print(json_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
