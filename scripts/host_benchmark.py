#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tests.evaluation.questions import ALL_QUESTIONS

from scripts.trace_report import _build_summary as build_trace_summary
from scripts.trace_utils import (
    DOCKER_LOCAL_WRAPPER_NAMES,
    build_ui_event_env,
    classify_startup_discovery,
    classify_tool_search_usage,
    extract_fallback_responses,
    extract_resource_reads,
    find_trace_files,
    find_response_by_id,
    parse_mcp_trace,
    parse_ui_events,
    summarize_upstream_log,
)

DEFAULT_SCENARIO_PACK = REPO_ROOT / "docs" / "benchmarking" / "codex_vs_claude_host_scenarios_v1.json"
DEFAULT_SESSION_ROOT = REPO_ROOT / "logs" / "sessions"
DEFAULT_REPORT_ROOT = REPO_ROOT / "docs" / "reports"
EXPECTED_TRACKS = [
    ("codex_cli", "Codex CLI", "codex", "cli"),
    ("codex_ide", "Codex IDE", "codex", "ide"),
    ("claude_desktop", "Claude Desktop", "claude", "desktop"),
]
QUESTION_BY_ID = {question.id: question for question in ALL_QUESTIONS}
_TOOL_NAME_MAPS: tuple[dict[str, str], dict[str, str]] | None = None


def _utc_now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _slug(value: str) -> str:
    text = "".join(ch.lower() if ch.isalnum() else "-" for ch in value)
    while "--" in text:
        text = text.replace("--", "-")
    return text.strip("-") or "session"


def _status_from_score(score: float) -> str:
    if score >= 0.9:
        return "pass"
    if score >= 0.5:
        return "partial"
    return "fail"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_scenario_pack(path: Path = DEFAULT_SCENARIO_PACK) -> dict[str, Any]:
    pack = _load_json(path)
    scenarios = pack.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        raise ValueError(f"Scenario pack missing scenarios: {path}")
    for scenario in scenarios:
        if not isinstance(scenario, dict):
            raise ValueError(f"Scenario pack contains non-object entry: {path}")
        question_id = scenario.get("sourceQuestionId")
        question = QUESTION_BY_ID.get(question_id)
        if question is None:
            raise ValueError(f"Unknown sourceQuestionId in scenario pack: {question_id}")
        prompt = scenario.get("prompt")
        if prompt != question.question:
            raise ValueError(
                f"Scenario prompt mismatch for {question_id}: {prompt!r} != {question.question!r}"
            )
    return pack


def _scenario_by_id(pack: dict[str, Any], scenario_id: str) -> dict[str, Any]:
    for scenario in pack["scenarios"]:
        if scenario.get("id") == scenario_id:
            return scenario
    raise KeyError(f"Scenario not found in pack: {scenario_id}")


def _normalize_tool_name(name: str | None) -> str | None:
    if not isinstance(name, str):
        return None
    global _TOOL_NAME_MAPS
    if _TOOL_NAME_MAPS is None:
        import tools.registry as _registry  # noqa: F401
        from server.mcp import tools as _mcp_import  # noqa: F401
        from server.tool_naming import build_tool_name_maps
        from tools.registry import all_tools

        _TOOL_NAME_MAPS = build_tool_name_maps([tool.name for tool in all_tools()])
    _, sanitized_to_original = _TOOL_NAME_MAPS
    return sanitized_to_original.get(name, name)


def _load_session_meta(session_dir: Path) -> dict[str, Any]:
    session_path = session_dir / "session.json"
    if not session_path.exists():
        return {}
    return _load_json(session_path)


def _save_session_meta(session_dir: Path, payload: dict[str, Any]) -> None:
    (session_dir / "session.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _ensure_session_dir(session_root: Path, name: str) -> Path:
    session_root.mkdir(parents=True, exist_ok=True)
    candidate = session_root / name
    counter = 1
    while candidate.exists():
        candidate = session_root / f"{name}-{counter}"
        counter += 1
    candidate.mkdir(parents=True, exist_ok=True)
    latest = session_root / ".latest"
    latest.write_text(str(candidate), encoding="utf-8")
    return candidate


def _build_temp_stdio_server(
    session_dir: Path,
    *,
    wrapper: Path,
    inherited_env: dict[str, str],
) -> dict[str, Any]:
    env = build_ui_event_env(
        session_dir,
        existing_env=inherited_env,
        default_log_root=REPO_ROOT / "logs",
        docker_compatible=wrapper.name in DOCKER_LOCAL_WRAPPER_NAMES,
    )
    env.pop("MCP_STDIO_UI_SUPPORTED", None)
    env.pop("MCP_STDIO_CLAUDE_APPS_CONTENT_MODE", None)
    return {
        "command": sys.executable,
        "args": [
            str(REPO_ROOT / "scripts" / "mcp_stdio_trace_proxy.py"),
            "--log",
            str(session_dir / "mcp-stdio-trace.jsonl"),
            "--",
            str(wrapper),
        ],
        "env": env,
    }


def _prepare_restore_server_config(previous: dict[str, Any] | None) -> dict[str, Any] | None:
    if previous is None:
        return None
    transport = previous.get("transport") or {}
    if transport.get("type") != "stdio":
        raise RuntimeError(
            "Benchmark harness only supports temporarily replacing stdio MCP "
            "registrations; refusing to mutate a non-stdio server config."
        )
    command = transport.get("command")
    if not isinstance(command, str) or not command:
        raise RuntimeError("Cannot restore stdio server without a command.")
    return {
        "command": command,
        "args": transport.get("args") or [],
        "env": transport.get("env") or {},
    }


def _codex_get_server(name: str) -> dict[str, Any] | None:
    proc = subprocess.run(
        ["codex", "mcp", "get", "--json", name],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return None
    return json.loads(proc.stdout)


def _codex_remove_server(name: str) -> None:
    for command in (["codex", "mcp", "remove", name], ["codex", "mcp", "rm", name]):
        proc = subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True, check=False)
        if proc.returncode == 0:
            return


def _codex_add_stdio_server(name: str, server_config: dict[str, Any]) -> None:
    command = ["codex", "mcp", "add"]
    for key, value in sorted((server_config.get("env") or {}).items()):
        command.extend(["--env", f"{key}={value}"])
    command.append(name)
    command.append("--")
    command.append(server_config["command"])
    command.extend(server_config.get("args") or [])
    subprocess.run(command, cwd=REPO_ROOT, check=True)


def _restore_server(name: str, restore_config: dict[str, Any] | None) -> None:
    _codex_remove_server(name)
    if restore_config is None:
        return
    _codex_add_stdio_server(name, restore_config)


def _codex_client_version() -> str | None:
    proc = subprocess.run(
        ["codex", "--version"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return None
    return proc.stdout.strip() or None


def _write_initial_session_meta(
    session_dir: Path,
    *,
    command: list[str],
    scenario_pack: str,
    scenario_id: str,
    model: str,
    source: str,
    surface: str,
    host_profile: str,
    client_version: str | None,
) -> None:
    payload = {
        "sessionId": session_dir.name,
        "startedAt": _utc_now(),
        "mode": "stdio",
        "source": source,
        "surface": surface,
        "hostProfile": host_profile,
        "clientVersion": client_version,
        "model": model,
        "scenarioPack": scenario_pack,
        "scenarioId": scenario_id,
        "cwd": str(REPO_ROOT),
        "repoRoot": str(REPO_ROOT),
        "command": command,
        "paths": {
            "sessionDir": str(session_dir),
            "mcpStdioTrace": str(session_dir / "mcp-stdio-trace.jsonl"),
            "uiEvents": str(session_dir / "ui-events.jsonl"),
            "codexEvents": str(session_dir / "codex-events.jsonl"),
            "assistantResponse": str(session_dir / "assistant-response.txt"),
        },
    }
    _save_session_meta(session_dir, payload)


def _load_traces(session_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any] | None, dict[str, Any]]:
    files = find_trace_files(session_dir)
    mcp_summaries: list[dict[str, Any]] = []
    if "stdio" in files:
        mcp_summaries.append(parse_mcp_trace(files["stdio"], "stdio"))
    if "http" in files:
        mcp_summaries.append(parse_mcp_trace(files["http"], "http"))
    requests = [request for summary in mcp_summaries for request in summary["requests"]]
    responses = [response for summary in mcp_summaries for response in summary["responses"]]
    for request in requests:
        request["toolNormalized"] = _normalize_tool_name(request.get("tool"))
    ui_summary = parse_ui_events(files["ui"]) if "ui" in files else None
    return requests, responses, ui_summary, files


def collect_session_evidence(session_dir: Path) -> dict[str, Any]:
    requests, responses, ui_summary, files = _load_traces(session_dir)
    session_meta = _load_session_meta(session_dir)
    tool_calls = [
        request["toolNormalized"]
        for request in requests
        if request.get("method") == "tools/call" and isinstance(request.get("toolNormalized"), str)
    ]
    ui_event_types = defaultdict(int)
    if ui_summary:
        for event in ui_summary["events"]:
            event_type = event.get("eventType")
            if isinstance(event_type, str):
                ui_event_types[event_type] += 1
    summary = build_trace_summary(
        session_dir,
        files,
        [parse_mcp_trace(files[key], key) for key in ("stdio", "http") if key in files],
        ui_summary,
        summarize_upstream_log(files["upstream"]) if "upstream" in files else [],
    )
    tool_response_pairs = []
    for request in requests:
        if request.get("method") != "tools/call":
            continue
        response = find_response_by_id(responses, request)
        tool_response_pairs.append(
            {
                "tool": request.get("toolNormalized"),
                "requestId": request.get("id"),
                "isError": bool(response and response.get("is_error")),
                "errorCode": response.get("code") if response else None,
                "hasFallback": bool(
                    isinstance(response, dict)
                    and isinstance(response.get("result", {}).get("data"), dict)
                    and isinstance(response.get("result", {}).get("data", {}).get("fallback"), dict)
                ),
                "contentTypes": [
                    block.get("type")
                    for block in ((response or {}).get("result", {}).get("content") or [])
                    if isinstance(block, dict) and isinstance(block.get("type"), str)
                ],
            }
        )
    return {
        "session": summary["session"],
        "traceSummary": summary,
        "startupDiscoveryPattern": classify_startup_discovery(requests),
        "toolSearchUsage": classify_tool_search_usage(requests),
        "toolCalls": tool_calls,
        "toolResponses": tool_response_pairs,
        "methodCounts": summary["mcp"]["methodCounts"],
        "resourceReads": extract_resource_reads(requests),
        "uiEventCount": len(ui_summary["events"]) if ui_summary else 0,
        "uiEventTypes": dict(ui_event_types),
        "fallbackCount": len(extract_fallback_responses(responses)),
        "fallbackTools": [
            pair["tool"] for pair in tool_response_pairs if pair["hasFallback"] and isinstance(pair.get("tool"), str)
        ],
        "errorCodes": [
            str(response.get("code") or "UNKNOWN")
            for response in responses
            if response.get("is_error")
        ],
    }


def _surface_expects_ui_runtime(session_meta: dict[str, Any]) -> bool:
    surface = session_meta.get("surface")
    host_profile = session_meta.get("hostProfile")
    return surface in {"ide", "desktop"} or host_profile in {
        "codex_ide_ui",
        "claude_desktop_ui_partial",
    }


def _category(score: float, detail: str, **extra: Any) -> dict[str, Any]:
    payload = {"score": round(score, 4), "status": _status_from_score(score), "detail": detail}
    payload.update(extra)
    return payload


def score_session(session_dir: Path, scenario: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    evidence = collect_session_evidence(session_dir)
    session_meta = evidence["session"]
    tool_calls = evidence["toolCalls"]
    expected_tool_signals = scenario.get("expectedTools", [])
    expected_tools = [tool for tool in expected_tool_signals if "/" not in tool]
    expected_methods = [method for method in expected_tool_signals if "/" in method]
    matched_tools = [tool for tool in expected_tools if tool in tool_calls]
    method_counts = evidence["methodCounts"]
    matched_methods = [method for method in expected_methods if method_counts.get(method, 0) > 0]
    expected_signal_count = len(expected_tools) + len(expected_methods)
    matched_signal_count = len(matched_tools) + len(matched_methods)
    tool_ratio = 1.0 if expected_signal_count == 0 else matched_signal_count / expected_signal_count
    resource_reads = evidence["resourceReads"]
    expected_resources = scenario.get("expectedResources", [])
    has_expected_resources = all(resource in resource_reads for resource in expected_resources)
    surface = str(session_meta.get("surface") or "unknown")
    expects_ui_runtime = _surface_expects_ui_runtime(session_meta)
    fallback_expected = surface in set(scenario.get("scoringHints", {}).get("fallbackExpectedOn", []))
    fallback_observed = evidence["fallbackCount"] > 0
    error_codes = [
        str(pair.get("errorCode") or "UNKNOWN")
        for pair in evidence["toolResponses"]
        if pair.get("isError")
    ]
    normalized_error = bool(error_codes) and all(code != "UNKNOWN" for code in error_codes)
    recovered_after_error = False
    error_seen = False
    for pair in evidence["toolResponses"]:
        if pair["isError"]:
            error_seen = True
            continue
        if error_seen and not pair["isError"]:
            recovered_after_error = True
            break

    if not error_seen:
        error_recovery_score = 1.0
        error_recovery_detail = "no error observed"
    elif normalized_error and recovered_after_error:
        error_recovery_score = 1.0
        error_recovery_detail = "normalized error observed and host recovered"
    elif normalized_error:
        error_recovery_score = 0.5
        error_recovery_detail = "normalized error observed without recovery"
    else:
        error_recovery_score = 0.0
        error_recovery_detail = "unnormalized error observed"

    tool_search_hint = scenario.get("scoringHints", {}).get("toolSearch", "optional")
    tool_search_usage = evidence["toolSearchUsage"]
    if tool_search_hint == "preferred":
        tool_search_score = {"used": 1.0, "supported": 0.75, "unused": 0.25, "not evidenced": 0.0}[tool_search_usage]
    elif tool_search_hint == "optional":
        tool_search_score = {"used": 1.0, "supported": 1.0, "unused": 0.75, "not evidenced": 0.5}[tool_search_usage]
    else:
        tool_search_score = {"used": 0.5, "supported": 0.5, "unused": 1.0, "not evidenced": 1.0}[tool_search_usage]

    resource_hint = scenario.get("scoringHints", {}).get("resourcesRead", "none")
    if resource_hint == "required":
        resource_score = 1.0 if has_expected_resources else 0.0
    elif resource_hint == "ui_only":
        if expects_ui_runtime:
            resource_score = 1.0 if has_expected_resources else 0.0
        else:
            resource_score = 1.0 if not resource_reads or fallback_observed else 0.75
    elif resource_hint == "optional":
        resource_score = 1.0 if (not expected_resources or has_expected_resources) else 0.5
    else:
        resource_score = 1.0 if not resource_reads else 0.75

    ui_runtime_hint = scenario.get("scoringHints", {}).get("uiRuntime", "not_applicable")
    ui_runtime_evidenced = evidence["uiEventCount"] > 0 and "os_apps.log_event" in tool_calls
    if ui_runtime_hint == "ui_only":
        if expects_ui_runtime:
            ui_runtime_score = 1.0 if ui_runtime_evidenced else 0.0
        else:
            ui_runtime_score = 1.0
    else:
        ui_runtime_score = 1.0

    latency_ms = evidence["traceSummary"]["hostSignals"].get("latencyToFirstUsefulToolCallMs")
    if isinstance(latency_ms, (int, float)):
        if latency_ms <= 2_000:
            latency_score = 1.0
        elif latency_ms <= 5_000:
            latency_score = 0.85
        elif latency_ms <= 10_000:
            latency_score = 0.6
        else:
            latency_score = 0.25
        latency_detail = f"{latency_ms:.1f} ms"
    else:
        latency_score = 0.0
        latency_detail = "no useful tool call observed"

    startup_pattern = evidence["startupDiscoveryPattern"]
    startup_score = {
        "search_first": 1.0,
        "search_mixed": 0.9,
        "scoped_list": 0.85,
        "resource_catalog": 0.7,
        "direct_call": 0.7,
        "full_catalog": 0.35,
    }.get(startup_pattern, 0.5)

    categories = {
        "protocolNegotiation": _category(
            1.0 if method_counts.get("initialize", 0) > 0 else 0.0,
            f"initialize calls={method_counts.get('initialize', 0)}",
        ),
        "startupDiscovery": _category(startup_score, startup_pattern),
        "toolSearch": _category(tool_search_score, tool_search_usage),
        "toolSelection": _category(
            tool_ratio,
            f"matched {matched_signal_count}/{expected_signal_count} expected tool/method signals",
            matchedTools=matched_tools,
            expectedTools=expected_tools,
            matchedMethods=matched_methods,
            expectedMethods=expected_methods,
            observedTools=tool_calls,
            observedMethods=sorted(method_counts),
        ),
        "errorRecovery": _category(
            error_recovery_score,
            error_recovery_detail,
            errorSeen=error_seen,
            recoveredAfterError=recovered_after_error,
            errorCodes=error_codes,
        ),
        "resourcesRead": _category(
            resource_score,
            f"reads={len(resource_reads)}",
            expectedResources=expected_resources,
            observedResources=resource_reads,
        ),
        "mcpAppsRuntime": _category(
            ui_runtime_score,
            "ui runtime evidenced" if ui_runtime_evidenced else "ui runtime not evidenced",
            uiEventCount=evidence["uiEventCount"],
            uiEventTypes=evidence["uiEventTypes"],
        ),
        "fallbackBehavior": _category(
            1.0 if fallback_observed == fallback_expected else 0.0,
            f"expected={fallback_expected} observed={fallback_observed}",
            fallbackExpected=fallback_expected,
            fallbackObserved=fallback_observed,
            fallbackTools=evidence["fallbackTools"],
        ),
        "latencyToFirstUsefulToolCall": _category(
            latency_score,
            latency_detail,
            latencyMs=latency_ms,
        ),
    }

    overall = round(sum(category["score"] for category in categories.values()) / len(categories), 4)
    score = {
        "generatedAt": _utc_now(),
        "scenarioId": scenario["id"],
        "scenarioLabel": scenario.get("label"),
        "sessionId": session_meta.get("sessionId", session_dir.name),
        "session": session_meta,
        "overallScore": overall,
        "overallStatus": _status_from_score(overall),
        "categories": categories,
    }
    return evidence, score


def write_score_artifacts(session_dir: Path, evidence: dict[str, Any], score: dict[str, Any]) -> None:
    (session_dir / "benchmark-evidence.json").write_text(
        json.dumps(evidence, indent=2), encoding="utf-8"
    )
    (session_dir / "benchmark-score.json").write_text(json.dumps(score, indent=2), encoding="utf-8")


def _track_id_for_session(session: dict[str, Any]) -> str:
    source = session.get("source")
    surface = session.get("surface")
    for track_id, _label, expected_source, expected_surface in EXPECTED_TRACKS:
        if source == expected_source and surface == expected_surface:
            return track_id
    return f"{source}_{surface}"


def summarize_sessions(
    session_dirs: list[Path],
    *,
    scenario_pack: dict[str, Any],
) -> tuple[dict[str, Any], str]:
    scenario_labels = {scenario["id"]: scenario.get("label", scenario["id"]) for scenario in scenario_pack["scenarios"]}
    track_rows: dict[str, dict[str, Any]] = {}
    for track_id, label, source, surface in EXPECTED_TRACKS:
        track_rows[track_id] = {
            "label": label,
            "source": source,
            "surface": surface,
            "sessions": [],
            "overallScores": [],
            "categoryScores": defaultdict(list),
            "scenarios": {},
        }

    session_summaries = []
    for session_dir in session_dirs:
        score_path = session_dir / "benchmark-score.json"
        evidence_path = session_dir / "benchmark-evidence.json"
        if not score_path.exists() or not evidence_path.exists():
            continue
        score = _load_json(score_path)
        evidence = _load_json(evidence_path)
        track_id = _track_id_for_session(score.get("session") or {})
        track = track_rows.setdefault(
            track_id,
            {
                "label": track_id,
                "source": score.get("session", {}).get("source"),
                "surface": score.get("session", {}).get("surface"),
                "sessions": [],
                "overallScores": [],
                "categoryScores": defaultdict(list),
                "scenarios": {},
            },
        )
        track["sessions"].append(str(session_dir))
        track["overallScores"].append(float(score.get("overallScore") or 0.0))
        for category_name, category in (score.get("categories") or {}).items():
            track["categoryScores"][category_name].append(float(category.get("score") or 0.0))
        scenario_id = score.get("scenarioId") or "unknown"
        track["scenarios"][scenario_id] = {
            "status": score.get("overallStatus"),
            "score": score.get("overallScore"),
            "toolSearchUsage": evidence.get("toolSearchUsage"),
            "startupDiscoveryPattern": evidence.get("startupDiscoveryPattern"),
            "uiEventCount": evidence.get("uiEventCount"),
            "fallbackCount": evidence.get("fallbackCount"),
        }
        session_summaries.append(
            {
                "sessionDir": str(session_dir),
                "scenarioId": scenario_id,
                "trackId": track_id,
                "overallScore": score.get("overallScore"),
                "overallStatus": score.get("overallStatus"),
            }
        )

    aggregate = {
        "generatedAt": _utc_now(),
        "scenarioPack": scenario_pack.get("id"),
        "sessions": session_summaries,
        "tracks": {},
    }

    lines = [
        "# Codex vs Claude MCP Host Benchmark",
        f"Generated: {aggregate['generatedAt']}",
        f"Scenario pack: {scenario_pack.get('id')}",
        "",
        "## Tracks",
        "| Track | Sessions | Scenario Coverage | Overall |",
        "| --- | ---: | ---: | ---: |",
    ]

    for track_id, track in track_rows.items():
        scenario_count = len(track["scenarios"])
        overall = round(sum(track["overallScores"]) / len(track["overallScores"]), 4) if track["overallScores"] else None
        category_avgs = {
            name: round(sum(values) / len(values), 4)
            for name, values in track["categoryScores"].items()
            if values
        }
        aggregate["tracks"][track_id] = {
            "label": track["label"],
            "source": track["source"],
            "surface": track["surface"],
            "sessionCount": len(track["sessions"]),
            "scenarioCount": scenario_count,
            "overallScore": overall,
            "categoryAverages": category_avgs,
            "scenarios": track["scenarios"],
        }
        overall_text = f"{overall:.2f}" if overall is not None else "missing"
        lines.append(f"| {track['label']} | {len(track['sessions'])} | {scenario_count} | {overall_text} |")

    lines.extend([
        "",
        "## Scenario Matrix",
        "| Scenario | Codex CLI | Codex IDE | Claude Desktop |",
        "| --- | --- | --- | --- |",
    ])
    for scenario in scenario_pack["scenarios"]:
        scenario_id = scenario["id"]
        row = [scenario_labels[scenario_id]]
        for track_id, _label, _source, _surface in EXPECTED_TRACKS:
            details = aggregate["tracks"].get(track_id, {}).get("scenarios", {}).get(scenario_id)
            if not details:
                row.append("missing")
                continue
            row.append(
                f"{details.get('status')} ({float(details.get('score') or 0.0):.2f})"
            )
        lines.append(f"| {' | '.join(row)} |")

    lines.extend([
        "",
        "## Category Averages",
        "| Category | Codex CLI | Codex IDE | Claude Desktop |",
        "| --- | ---: | ---: | ---: |",
    ])
    categories = [
        "protocolNegotiation",
        "startupDiscovery",
        "toolSearch",
        "toolSelection",
        "errorRecovery",
        "resourcesRead",
        "mcpAppsRuntime",
        "fallbackBehavior",
        "latencyToFirstUsefulToolCall",
    ]
    for category in categories:
        row = [category]
        for track_id, _label, _source, _surface in EXPECTED_TRACKS:
            avg = aggregate["tracks"].get(track_id, {}).get("categoryAverages", {}).get(category)
            row.append(f"{avg:.2f}" if avg is not None else "missing")
        lines.append(f"| {' | '.join(row)} |")

    markdown = "\n".join(lines).strip() + "\n"
    return aggregate, markdown


def cmd_scenario_pack(args: argparse.Namespace) -> int:
    pack = load_scenario_pack(Path(args.scenario_pack).resolve())
    text = json.dumps(pack, indent=2) + "\n"
    if args.out:
        out_path = Path(args.out).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text, encoding="utf-8")
        print(out_path)
    else:
        print(text, end="")
    return 0


def cmd_score_session(args: argparse.Namespace) -> int:
    session_dir = Path(args.session_dir).resolve()
    pack = load_scenario_pack(Path(args.scenario_pack).resolve())
    meta = _load_session_meta(session_dir)
    updates = {
        key: value
        for key, value in {
            "source": args.source,
            "surface": args.surface,
            "hostProfile": args.host_profile,
            "clientVersion": args.client_version,
            "model": args.model,
            "scenarioPack": pack.get("id"),
            "scenarioId": args.scenario_id or meta.get("scenarioId"),
        }.items()
        if value is not None
    }
    if updates:
        meta.update(updates)
        _save_session_meta(session_dir, meta)
    scenario_id = args.scenario_id or meta.get("scenarioId")
    if not scenario_id:
        raise SystemExit("Session metadata must include scenarioId or pass --scenario-id.")
    scenario = _scenario_by_id(pack, scenario_id)
    evidence, score = score_session(session_dir, scenario)
    write_score_artifacts(session_dir, evidence, score)
    print(session_dir)
    return 0


def cmd_summarize(args: argparse.Namespace) -> int:
    pack = load_scenario_pack(Path(args.scenario_pack).resolve())
    session_dirs = [Path(value).resolve() for value in args.sessions]
    aggregate, markdown = summarize_sessions(session_dirs, scenario_pack=pack)
    date_stamp = dt.date.today().isoformat()
    prefix = Path(args.out_prefix).resolve() if args.out_prefix else DEFAULT_REPORT_ROOT / f"codex_vs_claude_host_benchmark_{date_stamp}"
    prefix.parent.mkdir(parents=True, exist_ok=True)
    json_path = prefix.with_suffix(".json")
    md_path = prefix.with_suffix(".md")
    json_path.write_text(json.dumps(aggregate, indent=2), encoding="utf-8")
    md_path.write_text(markdown, encoding="utf-8")
    print(md_path)
    print(json_path)
    return 0


def _prompt_for_scenario(scenario: dict[str, Any]) -> str:
    return (
        "Use the connected `mcp-geo` MCP server to answer the user request below. "
        "Prefer MCP tools and resources over repository inspection or shell commands. "
        "If the server returns a UI tool and the host does not support UI, use the fallback payload. "
        "Return a concise final answer.\n\n"
        f"User request: {scenario['prompt']}"
    )


def cmd_run_codex_cli(args: argparse.Namespace) -> int:
    pack = load_scenario_pack(Path(args.scenario_pack).resolve())
    scenario = _scenario_by_id(pack, args.scenario_id)
    scenario_slug = _slug(scenario["id"])
    session_name = args.name or f"{dt.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}-codex-cli-{scenario_slug}"
    session_dir = _ensure_session_dir(Path(args.session_root).resolve(), session_name)
    wrapper = Path(args.wrapper).resolve()
    inherited_env = {
        key: value
        for key, value in {
            "OS_API_KEY": os.getenv("OS_API_KEY"),
            "ONS_API_KEY": os.getenv("ONS_API_KEY"),
            "ONS_LIVE_ENABLED": os.getenv("ONS_LIVE_ENABLED"),
            "STDIO_KEY": os.getenv("STDIO_KEY"),
            "BEARER_TOKENS": os.getenv("BEARER_TOKENS"),
            "MCP_GEO_DOCKER_BUILD": os.getenv("MCP_GEO_DOCKER_BUILD", "missing"),
            "MCP_TOOLS_DEFAULT_TOOLSET": os.getenv("MCP_TOOLS_DEFAULT_TOOLSET"),
            "MCP_TOOLS_DEFAULT_INCLUDE_TOOLSETS": os.getenv("MCP_TOOLS_DEFAULT_INCLUDE_TOOLSETS"),
            "MCP_TOOLS_DEFAULT_EXCLUDE_TOOLSETS": os.getenv("MCP_TOOLS_DEFAULT_EXCLUDE_TOOLSETS"),
        }.items()
        if value
    }
    temp_server = _build_temp_stdio_server(session_dir, wrapper=wrapper, inherited_env=inherited_env)
    previous = _codex_get_server(args.server_name)
    restore_config = _prepare_restore_server_config(previous)
    _write_initial_session_meta(
        session_dir,
        command=["codex", "exec", "-m", args.model, "--json", _prompt_for_scenario(scenario)],
        scenario_pack=pack["id"],
        scenario_id=scenario["id"],
        model=args.model,
        source="codex",
        surface="cli",
        host_profile="codex_cli_stdio",
        client_version=_codex_client_version(),
    )

    try:
        _codex_remove_server(args.server_name)
        _codex_add_stdio_server(args.server_name, temp_server)
        command = [
            "codex",
            "exec",
            "-m",
            args.model,
            "--json",
            "-o",
            str(session_dir / "assistant-response.txt"),
            "-C",
            str(REPO_ROOT),
            _prompt_for_scenario(scenario),
        ]
        proc = subprocess.run(
            command,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        (session_dir / "codex-events.jsonl").write_text(proc.stdout, encoding="utf-8")
        if proc.stderr:
            (session_dir / "codex-exec.stderr.txt").write_text(proc.stderr, encoding="utf-8")
        if proc.returncode != 0:
            raise RuntimeError(f"codex exec failed with code {proc.returncode}")
    finally:
        _restore_server(args.server_name, restore_config)

    subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "trace_report.py"), str(session_dir)],
        cwd=REPO_ROOT,
        check=False,
    )
    evidence, score = score_session(session_dir, scenario)
    write_score_artifacts(session_dir, evidence, score)
    print(session_dir)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run and score MCP host benchmarks.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scenario_pack_parser = subparsers.add_parser("scenario-pack", help="Print or export the scenario pack.")
    scenario_pack_parser.add_argument("--scenario-pack", default=str(DEFAULT_SCENARIO_PACK))
    scenario_pack_parser.add_argument("--out")
    scenario_pack_parser.set_defaults(func=cmd_scenario_pack)

    score_parser = subparsers.add_parser("score-session", help="Score an existing traced session.")
    score_parser.add_argument("session_dir")
    score_parser.add_argument("--scenario-pack", default=str(DEFAULT_SCENARIO_PACK))
    score_parser.add_argument("--scenario-id")
    score_parser.add_argument("--source")
    score_parser.add_argument("--surface")
    score_parser.add_argument("--host-profile")
    score_parser.add_argument("--client-version")
    score_parser.add_argument("--model")
    score_parser.set_defaults(func=cmd_score_session)

    summarize_parser = subparsers.add_parser("summarize", help="Aggregate scored sessions into a report.")
    summarize_parser.add_argument("sessions", nargs="+")
    summarize_parser.add_argument("--scenario-pack", default=str(DEFAULT_SCENARIO_PACK))
    summarize_parser.add_argument("--out-prefix")
    summarize_parser.set_defaults(func=cmd_summarize)

    run_parser = subparsers.add_parser("run-codex-cli", help="Run a scripted Codex CLI benchmark scenario.")
    run_parser.add_argument("scenario_id")
    run_parser.add_argument("--scenario-pack", default=str(DEFAULT_SCENARIO_PACK))
    run_parser.add_argument("--model", default="gpt-5.4")
    run_parser.add_argument("--server-name", default="mcp-geo")
    run_parser.add_argument("--wrapper", default=str(REPO_ROOT / "scripts" / "codex-mcp-local"))
    run_parser.add_argument("--session-root", default=str(DEFAULT_SESSION_ROOT))
    run_parser.add_argument("--name")
    run_parser.set_defaults(func=cmd_run_codex_cli)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
