from __future__ import annotations

import json
from pathlib import Path

from scripts import check_lmr_host4


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    text = "".join(json.dumps(row) + "\n" for row in rows)
    path.write_text(text, encoding="utf-8")


def test_analyze_lmr_host4_inconclusive_when_no_boundary_calls(tmp_path: Path) -> None:
    trace_path = tmp_path / "trace.jsonl"
    ui_path = tmp_path / "ui-events.jsonl"
    _write_jsonl(
        trace_path,
        [
            {
                "ts": 1_700_000_000.0,
                "direction": "client->server",
                "json": {"id": 1, "method": "tools/list", "params": {}},
            }
        ],
    )
    _write_jsonl(ui_path, [])

    report = check_lmr_host4.analyze_lmr_host4(
        trace_path=trace_path,
        ui_events_path=ui_path,
        window_seconds=120.0,
    )

    assert report.verdict == "INCONCLUSIVE"
    assert report.boundary_tool_calls == 0
    assert report.boundary_ui_runtime_events == 0


def test_analyze_lmr_host4_fail_server_when_boundary_call_not_successful(tmp_path: Path) -> None:
    trace_path = tmp_path / "trace.jsonl"
    ui_path = tmp_path / "ui-events.jsonl"
    _write_jsonl(
        trace_path,
        [
            {
                "ts": 1_700_000_000.0,
                "direction": "client->server",
                "json": {
                    "id": 10,
                    "method": "tools/call",
                    "params": {"name": "os_apps.render_boundary_explorer", "arguments": {}},
                },
            },
            {
                "ts": 1_700_000_001.0,
                "direction": "server->client",
                "json": {"id": 10, "result": {"status": 500, "isError": True}},
            },
        ],
    )
    _write_jsonl(ui_path, [])

    report = check_lmr_host4.analyze_lmr_host4(
        trace_path=trace_path,
        ui_events_path=ui_path,
        window_seconds=120.0,
    )

    assert report.verdict == "FAIL_SERVER"
    assert report.boundary_tool_calls == 1
    assert report.boundary_tool_successes == 0
    assert report.boundary_ui_runtime_events == 0


def test_analyze_lmr_host4_fail_resource_read_when_missing(tmp_path: Path) -> None:
    trace_path = tmp_path / "trace.jsonl"
    ui_path = tmp_path / "ui-events.jsonl"
    _write_jsonl(
        trace_path,
        [
            {
                "ts": 1_700_000_000.0,
                "direction": "client->server",
                "json": {
                    "id": 20,
                    "method": "tools/call",
                    "params": {"name": "os_apps_render_boundary_explorer", "arguments": {}},
                },
            },
            {
                "ts": 1_700_000_001.0,
                "direction": "server->client",
                "json": {"id": 20, "result": {"status": 200, "ok": True}},
            },
        ],
    )
    _write_jsonl(ui_path, [])

    report = check_lmr_host4.analyze_lmr_host4(
        trace_path=trace_path,
        ui_events_path=ui_path,
        window_seconds=120.0,
    )

    assert report.verdict == "FAIL_RESOURCE_READ"
    assert report.boundary_tool_successes == 1
    assert report.boundary_resource_reads == 0
    assert report.boundary_ui_runtime_events == 0


def test_analyze_lmr_host4_fail_host_runtime_when_no_bridge_events(tmp_path: Path) -> None:
    trace_path = tmp_path / "trace.jsonl"
    ui_path = tmp_path / "ui-events.jsonl"
    _write_jsonl(
        trace_path,
        [
            {
                "ts": 1_700_000_000.0,
                "direction": "client->server",
                "json": {
                    "id": 30,
                    "method": "tools/call",
                    "params": {"name": "os_apps.render_boundary_explorer", "arguments": {}},
                },
            },
            {
                "ts": 1_700_000_001.0,
                "direction": "server->client",
                "json": {"id": 30, "result": {"status": 200, "ok": True}},
            },
            {
                "ts": 1_700_000_003.0,
                "direction": "client->server",
                "json": {
                    "id": 31,
                    "method": "resources/read",
                    "params": {"uri": "ui://mcp-geo/boundary-explorer"},
                },
            },
        ],
    )
    _write_jsonl(ui_path, [])

    report = check_lmr_host4.analyze_lmr_host4(
        trace_path=trace_path,
        ui_events_path=ui_path,
        window_seconds=120.0,
    )

    assert report.verdict == "FAIL_HOST_RUNTIME"
    assert report.boundary_resource_reads == 1
    assert report.log_event_calls == 0
    assert report.boundary_ui_runtime_events == 0


def test_analyze_lmr_host4_pass_with_resource_name_log_event_and_ms_ui_events(tmp_path: Path) -> None:
    trace_path = tmp_path / "trace.jsonl"
    ui_path = tmp_path / "ui-events.jsonl"
    _write_jsonl(
        trace_path,
        [
            {
                "ts": 1_700_000_100.0,
                "direction": "client->server",
                "json": {
                    "id": 40,
                    "method": "tools/call",
                    "params": {"name": "os_apps_render_boundary_explorer", "arguments": {}},
                },
            },
            {
                "ts": 1_700_000_101.0,
                "direction": "server->client",
                "json": {"id": 40, "result": {"status": 200, "ok": True}},
            },
            {
                "ts": 1_700_000_102.0,
                "direction": "client->server",
                "json": {
                    "id": 41,
                    "method": "resources/read",
                    "params": {"name": "ui_boundary_explorer"},
                },
            },
            {
                "ts": 1_700_000_103.0,
                "direction": "client->server",
                "json": {
                    "id": 42,
                    "method": "tools/call",
                    "params": {"name": "os_apps.log_event", "arguments": {"eventType": "host_ready"}},
                },
            },
        ],
    )
    _write_jsonl(
        ui_path,
        [
            {
                "timestamp": 1_700_000_104_000,
                "eventType": "host_ready",
            }
        ],
    )

    report = check_lmr_host4.analyze_lmr_host4(
        trace_path=trace_path,
        ui_events_path=ui_path,
        window_seconds=120.0,
    )

    assert report.verdict == "PASS"
    assert report.log_event_calls == 1
    assert report.ui_events_in_window == 1
    assert report.ui_event_types_in_window == ["host_ready"]
    assert report.boundary_ui_runtime_events == 0


def test_analyze_lmr_host4_pass_ui_only_when_boundary_runtime_events_exist(tmp_path: Path) -> None:
    trace_path = tmp_path / "trace.jsonl"
    ui_path = tmp_path / "ui-events.vscode-trace.jsonl"
    ui_alt = tmp_path / "ui-events.vscode.jsonl"
    _write_jsonl(trace_path, [])
    _write_jsonl(ui_path, [])
    _write_jsonl(
        ui_alt,
        [
            {
                "timestamp": 1_700_000_200.0,
                "eventType": "host_ready",
                "source": "boundary-explorer",
                "sessionId": "ui_123",
            }
        ],
    )

    report = check_lmr_host4.analyze_lmr_host4(
        trace_path=trace_path,
        ui_events_path=ui_path,
        window_seconds=120.0,
    )

    assert report.verdict == "PASS_UI_ONLY"
    assert report.boundary_tool_calls == 0
    assert report.boundary_ui_runtime_events == 1
    assert report.ui_events_path == str(ui_alt)


def test_run_playwright_smoke_applies_project_filters_and_test_path(monkeypatch) -> None:
    calls: list[list[str]] = []

    class _Proc:
        returncode = 0
        stderr = ""
        stdout = "ok"

    def _fake_run(cmd, **kwargs):  # type: ignore[no-untyped-def]
        calls.append(list(cmd))
        assert kwargs["capture_output"] is True
        assert kwargs["text"] is True
        assert kwargs["check"] is False
        assert kwargs["cwd"] == "playground"
        return _Proc()

    monkeypatch.setattr(check_lmr_host4.subprocess, "run", _fake_run)

    ok, summary = check_lmr_host4._run_playwright_smoke(
        projects=["chromium-desktop", "webkit-desktop"],
        grep="trial-5 deterministic host-simulation fixtures are stable across engines",
        workers=2,
        test_path="trials/tests/map_delivery_matrix.spec.js",
    )

    assert ok is True
    assert "chromium-desktop,webkit-desktop" in summary
    assert calls == [
        [
            "npx",
            "playwright",
            "test",
            "trials/tests/map_delivery_matrix.spec.js",
            "--config",
            "playwright.trials.config.js",
            "--workers=2",
            "-g",
            "trial-5 deterministic host-simulation fixtures are stable across engines",
            "--project",
            "chromium-desktop",
            "--project",
            "webkit-desktop",
        ]
    ]


def test_run_playwright_smoke_rejects_invalid_worker_count() -> None:
    ok, summary = check_lmr_host4._run_playwright_smoke(
        projects=[],
        grep="trial-5",
        workers=0,
        test_path=None,
    )
    assert ok is False
    assert "workers must be >= 1" in summary
