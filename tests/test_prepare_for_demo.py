from __future__ import annotations

import json
import os
from argparse import Namespace
from datetime import UTC, datetime
from pathlib import Path

import pytest

from scripts import prepare_for_demo


def test_parse_timestamp_accepts_git_epoch_seconds() -> None:
    parsed = prepare_for_demo.parse_timestamp("1776166330")

    assert parsed == datetime.fromtimestamp(1776166330, tz=UTC)


def test_parse_timestamp_accepts_docker_nanosecond_rfc3339() -> None:
    parsed = prepare_for_demo.parse_timestamp("2026-04-15T11:03:38.416763763Z")

    assert parsed == datetime(2026, 4, 15, 11, 3, 38, 416763, tzinfo=UTC)


def test_image_staleness_compares_created_time_to_reference() -> None:
    image_created = prepare_for_demo.parse_timestamp("2026-04-15T11:03:38.416763763Z")
    merged_ref = prepare_for_demo.parse_timestamp("2026-04-22T21:35:38Z")

    assert prepare_for_demo.is_stale(image_created, merged_ref) is True
    assert prepare_for_demo.is_stale(merged_ref, image_created) is False


def test_git_fetch_args_target_remote_tracking_ref() -> None:
    assert prepare_for_demo.git_fetch_args_for_ref("origin/release/demo") == [
        "git",
        "fetch",
        "--quiet",
        "origin",
        "release/demo:refs/remotes/origin/release/demo",
    ]
    assert prepare_for_demo.git_fetch_args_for_ref("v1.2.3") == [
        "git",
        "fetch",
        "--quiet",
        "origin",
        "v1.2.3",
    ]


def test_configured_docker_bin_must_be_executable(tmp_path: Path) -> None:
    docker_stub = tmp_path / "docker"
    docker_stub.write_text("#!/bin/sh\n", encoding="utf-8")
    docker_stub.chmod(0o644)

    assert prepare_for_demo.configured_docker_error(
        {"MCP_GEO_DOCKER_BIN": str(docker_stub)}
    ) == f"MCP_GEO_DOCKER_BIN is not executable: {docker_stub}."
    assert prepare_for_demo.find_docker({"MCP_GEO_DOCKER_BIN": str(docker_stub)}) is None

    docker_stub.chmod(0o755)

    assert (
        prepare_for_demo.configured_docker_error({"MCP_GEO_DOCKER_BIN": str(docker_stub)})
        is None
    )
    assert prepare_for_demo.find_docker({"MCP_GEO_DOCKER_BIN": str(docker_stub)}) == str(
        docker_stub
    )


def test_configured_docker_bin_rejects_directory(tmp_path: Path) -> None:
    assert prepare_for_demo.configured_docker_error(
        {"MCP_GEO_DOCKER_BIN": str(tmp_path)}
    ) == f"MCP_GEO_DOCKER_BIN points to a directory, not an executable: {tmp_path}."


def test_image_ref_matching_preserves_tags_and_registry_ports() -> None:
    assert prepare_for_demo.image_ref_matches("mcp-geo-server:demo", "mcp-geo-server:demo")
    assert not prepare_for_demo.image_ref_matches(
        "mcp-geo-server:old", "mcp-geo-server:demo"
    )
    assert prepare_for_demo.image_ref_matches(
        "localhost:5000/mcp-geo-server:demo",
        "localhost:5000/mcp-geo-server:demo",
    )
    assert not prepare_for_demo.image_ref_matches(
        "localhost:5000/mcp-geo-server:old",
        "localhost:5000/mcp-geo-server:demo",
    )


def test_running_app_containers_matches_requested_tag(monkeypatch: pytest.MonkeyPatch) -> None:
    ps_rows = [
        {"ID": "keep", "Image": "mcp-geo-server:demo", "Names": "demo", "Status": "Up"},
        {"ID": "skip", "Image": "mcp-geo-server:old", "Names": "old", "Status": "Up"},
    ]

    def fake_run(
        args: list[str],
        *,
        check: bool = True,
        env: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> prepare_for_demo.CommandResult:
        assert check in {True, False}
        assert env is None
        assert timeout is None
        if args == ["docker", "ps", "--format", "{{json .}}"]:
            stdout = "\n".join(json.dumps(row) for row in ps_rows)
            return prepare_for_demo.CommandResult(0, stdout, "")
        if args[:3] == ["docker", "container", "inspect"]:
            payload = {
                "Image": f"sha256:{args[3]}",
                "Created": "2026-04-22T12:00:00Z",
            }
            return prepare_for_demo.CommandResult(0, json.dumps(payload), "")
        raise AssertionError(f"Unexpected command: {args}")

    monkeypatch.setattr(prepare_for_demo, "_run", fake_run)

    containers = prepare_for_demo.running_app_containers("docker", "mcp-geo-server:demo")

    assert [container["id"] for container in containers] == ["keep"]


def test_render_checks_reports_failures_and_remediation() -> None:
    rendered = prepare_for_demo.render_checks(
        [
            prepare_for_demo.Check("PASS", "git.clean", "Working tree is clean."),
            prepare_for_demo.Check(
                "FAIL",
                "docker.image",
                "Image is older than origin/main.",
                "Run: docker build -t mcp-geo-server .",
            ),
            prepare_for_demo.Check("WARN", "wrapper.claude.os_key", "OS key not visible."),
        ]
    )

    assert "PASS: git.clean: Working tree is clean." in rendered
    assert "FAIL: docker.image: Image is older than origin/main." in rendered
    assert "  -> Run: docker build -t mcp-geo-server ." in rendered
    assert "Summary: 1 fail, 1 warn." in rendered


@pytest.mark.parametrize(
    "value",
    ["", "not-a-time"],
)
def test_parse_timestamp_rejects_invalid_values(value: str) -> None:
    with pytest.raises(ValueError):
        prepare_for_demo.parse_timestamp(value)


def test_run_returns_command_result_for_os_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(*_args: object, **_kwargs: object) -> object:
        raise PermissionError("not executable")

    monkeypatch.setattr(prepare_for_demo.subprocess, "run", fake_run)

    result = prepare_for_demo._run([os.devnull, "info"], check=False)

    assert result.returncode == 126
    assert "not executable" in result.stderr


def test_run_returns_command_result_for_timeouts(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(*_args: object, **_kwargs: object) -> object:
        raise prepare_for_demo.subprocess.TimeoutExpired(
            cmd=["slow-wrapper"],
            timeout=3,
            output="partial output",
            stderr="still running",
        )

    monkeypatch.setattr(prepare_for_demo.subprocess, "run", fake_run)

    result = prepare_for_demo._run(["slow-wrapper"], check=False, timeout=3)

    assert result.returncode == 124
    assert result.stdout == "partial output"
    assert result.stderr == "still running"


def test_wrapper_plan_uses_timeout(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    wrapper = tmp_path / "wrapper"
    wrapper.write_text("#!/bin/sh\n", encoding="utf-8")
    seen: dict[str, object] = {}

    def fake_run(
        args: list[str],
        *,
        check: bool = True,
        env: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> prepare_for_demo.CommandResult:
        seen["args"] = args
        seen["check"] = check
        seen["env"] = env
        seen["timeout"] = timeout
        return prepare_for_demo.CommandResult(124, "", "timed out after 15s")

    monkeypatch.setattr(prepare_for_demo, "_run", fake_run)

    plan = prepare_for_demo.wrapper_plan(wrapper)

    assert plan == {"error": "timed out after 15s"}
    assert seen["args"] == [str(wrapper)]
    assert seen["check"] is False
    assert seen["timeout"] == prepare_for_demo.WRAPPER_PLAN_TIMEOUT_SECONDS
    assert isinstance(seen["env"], dict)
    assert seen["env"]["MCP_GEO_DOCKER_PLAN_ONLY"] == "1"


def test_run_checks_reports_unresolved_ref(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(
        args: list[str],
        *,
        check: bool = True,
        env: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> prepare_for_demo.CommandResult:
        assert check is True
        assert env is None
        assert timeout is None
        if args == ["git", "status", "--porcelain"]:
            return prepare_for_demo.CommandResult(0, "", "")
        raise AssertionError(f"Unexpected command: {args}")

    def fake_git_ref_full(ref: str) -> str:
        if ref == "HEAD":
            return "head-sha"
        raise RuntimeError("git rev-parse missing-ref failed: ambiguous argument")

    monkeypatch.setattr(prepare_for_demo, "_run", fake_run)
    monkeypatch.setattr(prepare_for_demo, "git_ref_full", fake_git_ref_full)

    checks = prepare_for_demo.run_checks(
        Namespace(fetch=False, ref="missing-ref", image="mcp-geo-server", rebuild=False)
    )

    assert checks[-1].level == "FAIL"
    assert checks[-1].name == "git.ref"
    assert "missing-ref" in checks[-1].detail
    assert not any(check.name.startswith("docker.") for check in checks)
