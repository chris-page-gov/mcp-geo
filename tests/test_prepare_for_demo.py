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
        "+refs/heads/release/demo:refs/remotes/origin/release/demo",
    ]
    assert prepare_for_demo.git_fetch_args_for_ref("v1.2.3") == [
        "git",
        "fetch",
        "--quiet",
        "origin",
        "+refs/heads/v1.2.3:refs/remotes/origin/v1.2.3",
    ]


def test_git_fetch_ref_resolves_unqualified_branch_to_remote_tracking(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: list[list[str]] = []

    def fake_run(
        args: list[str],
        *,
        check: bool = True,
        env: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> prepare_for_demo.CommandResult:
        assert check is False
        assert env is None
        assert timeout is None
        seen.append(args)
        return prepare_for_demo.CommandResult(0, "", "")

    monkeypatch.setattr(prepare_for_demo, "_run", fake_run)

    result, target_ref = prepare_for_demo.git_fetch_ref("release/demo")

    assert result.returncode == 0
    assert target_ref == "origin/release/demo"
    assert seen == [
        [
            "git",
            "fetch",
            "--quiet",
            "origin",
            "+refs/heads/release/demo:refs/remotes/origin/release/demo",
        ],
    ]


def test_git_fetch_ref_falls_back_to_tag_ref(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[list[str]] = []

    def fake_run(
        args: list[str],
        *,
        check: bool = True,
        env: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> prepare_for_demo.CommandResult:
        assert check is False
        assert env is None
        assert timeout is None
        seen.append(args)
        if "refs/heads/v1.2.3" in args[-1]:
            return prepare_for_demo.CommandResult(128, "", "branch not found")
        return prepare_for_demo.CommandResult(0, "", "")

    monkeypatch.setattr(prepare_for_demo, "_run", fake_run)

    result, target_ref = prepare_for_demo.git_fetch_ref("v1.2.3")

    assert result.returncode == 0
    assert target_ref == "refs/tags/v1.2.3"
    assert seen == [
        [
            "git",
            "fetch",
            "--quiet",
            "origin",
            "+refs/heads/v1.2.3:refs/remotes/origin/v1.2.3",
        ],
        ["git", "fetch", "--quiet", "origin", "+refs/tags/v1.2.3:refs/tags/v1.2.3"],
    ]


def test_git_fetch_ref_skips_fetch_for_head(monkeypatch: pytest.MonkeyPatch) -> None:
    def unexpected_run(
        args: list[str],
        *,
        check: bool = True,
        env: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> prepare_for_demo.CommandResult:
        raise AssertionError(f"Unexpected fetch command for local ref: {args}")

    monkeypatch.setattr(prepare_for_demo, "_run", unexpected_run)

    result, target_ref = prepare_for_demo.git_fetch_ref("HEAD")

    assert result.returncode == 0
    assert result.stdout == "Using local ref HEAD; fetch skipped."
    assert target_ref == "HEAD"


def test_git_fetch_ref_skips_fetch_for_local_sha(monkeypatch: pytest.MonkeyPatch) -> None:
    def unexpected_run(
        args: list[str],
        *,
        check: bool = True,
        env: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> prepare_for_demo.CommandResult:
        raise AssertionError(f"Unexpected fetch command for local SHA: {args}")

    monkeypatch.setattr(prepare_for_demo, "_run", unexpected_run)
    monkeypatch.setattr(prepare_for_demo, "git_ref_full", lambda _ref: "a" * 40)

    result, target_ref = prepare_for_demo.git_fetch_ref("abc1234")

    assert result.returncode == 0
    assert result.stdout == "Using local ref abc1234; fetch skipped."
    assert target_ref == "abc1234"


def test_git_ref_helpers_peel_refs_to_commits(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[list[str]] = []

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
        seen.append(args)
        if args[:2] == ["git", "show"]:
            return prepare_for_demo.CommandResult(0, "1776166330\n", "")
        if "--short" in args:
            return prepare_for_demo.CommandResult(0, "abc123\n", "")
        return prepare_for_demo.CommandResult(0, "abc123full\n", "")

    monkeypatch.setattr(prepare_for_demo, "_run", fake_run)

    assert prepare_for_demo.git_ref_full("v1.0.0") == "abc123full"
    assert prepare_for_demo.git_ref_short("v1.0.0") == "abc123"
    assert prepare_for_demo.git_ref_timestamp("v1.0.0") == datetime.fromtimestamp(
        1776166330,
        tz=UTC,
    )
    assert seen == [
        ["git", "rev-parse", "v1.0.0^{commit}"],
        ["git", "rev-parse", "--short", "v1.0.0^{commit}"],
        ["git", "show", "-s", "--format=%ct", "v1.0.0^{commit}"],
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


def test_image_ref_matching_treats_latest_and_untagged_as_equivalent() -> None:
    assert prepare_for_demo.image_ref_matches("mcp-geo-server", "mcp-geo-server:latest")
    assert prepare_for_demo.image_ref_matches("mcp-geo-server:latest", "mcp-geo-server")
    assert prepare_for_demo.image_ref_matches(
        "localhost:5000/mcp-geo-server",
        "localhost:5000/mcp-geo-server:latest",
    )
    assert prepare_for_demo.image_ref_matches(
        "localhost:5000/mcp-geo-server:latest",
        "localhost:5000/mcp-geo-server",
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

    scan = prepare_for_demo.running_app_containers("docker", "mcp-geo-server:demo")

    assert scan.error is None
    assert [container["id"] for container in scan.containers] == ["keep"]


def test_running_app_containers_surfaces_docker_ps_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(
        args: list[str],
        *,
        check: bool = True,
        env: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> prepare_for_demo.CommandResult:
        assert args == ["docker", "ps", "--format", "{{json .}}"]
        assert check is False
        assert env is None
        assert timeout is None
        return prepare_for_demo.CommandResult(1, "", "permission denied")

    monkeypatch.setattr(prepare_for_demo, "_run", fake_run)

    scan = prepare_for_demo.running_app_containers("docker", "mcp-geo-server")

    assert scan.containers == []
    assert scan.error == "permission denied"


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


def test_run_checks_blocks_on_fetch_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    def unexpected_run(
        args: list[str],
        *,
        check: bool = True,
        env: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> prepare_for_demo.CommandResult:
        raise AssertionError(f"Unexpected command after fetch failure: {args}")

    monkeypatch.setattr(prepare_for_demo, "_run", unexpected_run)
    monkeypatch.setattr(
        prepare_for_demo,
        "git_fetch_ref",
        lambda _ref: (prepare_for_demo.CommandResult(1, "", "auth failed"), "origin/main"),
    )

    checks = prepare_for_demo.run_checks(
        Namespace(fetch=True, ref="origin/main", image="mcp-geo-server", rebuild=False)
    )

    assert [(check.level, check.name) for check in checks] == [("FAIL", "git.fetch")]
    assert checks[0].detail == "auth failed"


def test_run_checks_continues_after_local_ref_fetch_skip(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ref_time = datetime(2026, 4, 22, 12, 0, tzinfo=UTC)

    def fake_run(
        args: list[str],
        *,
        check: bool = True,
        env: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> prepare_for_demo.CommandResult:
        assert env is None
        assert timeout is None
        if args == ["git", "status", "--porcelain"]:
            assert check is True
            return prepare_for_demo.CommandResult(0, "", "")
        if args == ["docker", "info"]:
            assert check is False
            return prepare_for_demo.CommandResult(0, "", "")
        raise AssertionError(f"Unexpected command: {args}")

    monkeypatch.setattr(prepare_for_demo, "_run", fake_run)
    monkeypatch.setattr(prepare_for_demo, "git_ref_full", lambda _ref: "same-sha")
    monkeypatch.setattr(prepare_for_demo, "git_ref_short", lambda _ref: "same")
    monkeypatch.setattr(prepare_for_demo, "git_ref_timestamp", lambda _ref: ref_time)
    monkeypatch.setattr(prepare_for_demo, "configured_docker_error", lambda _env: None)
    monkeypatch.setattr(prepare_for_demo, "find_docker", lambda _env: "docker")
    monkeypatch.setattr(
        prepare_for_demo,
        "image_info",
        lambda _docker, _image: ("image-id", ref_time),
    )
    monkeypatch.setattr(
        prepare_for_demo,
        "running_app_containers",
        lambda _docker, _image: prepare_for_demo.ContainerScan([], None),
    )
    monkeypatch.setattr(prepare_for_demo, "APP_WRAPPERS", {})

    checks = prepare_for_demo.run_checks(
        Namespace(fetch=True, ref="HEAD", image="mcp-geo-server", rebuild=False)
    )

    assert checks[0] == prepare_for_demo.Check(
        "PASS",
        "git.fetch",
        "Using local ref HEAD; fetch skipped.",
    )
    assert any(check.name == "git.ref" and check.level == "PASS" for check in checks)


def test_run_checks_resolves_successfully_fetched_branch_target(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ref_time = datetime(2026, 4, 22, 12, 0, tzinfo=UTC)
    resolved_refs: list[str] = []

    def fake_run(
        args: list[str],
        *,
        check: bool = True,
        env: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> prepare_for_demo.CommandResult:
        assert env is None
        assert timeout is None
        if args == ["git", "status", "--porcelain"]:
            assert check is True
            return prepare_for_demo.CommandResult(0, "", "")
        if args == ["docker", "info"]:
            assert check is False
            return prepare_for_demo.CommandResult(0, "", "")
        raise AssertionError(f"Unexpected command: {args}")

    def fake_ref_full(ref: str) -> str:
        resolved_refs.append(ref)
        return "same-sha"

    monkeypatch.setattr(prepare_for_demo, "_run", fake_run)
    monkeypatch.setattr(
        prepare_for_demo,
        "git_fetch_ref",
        lambda _ref: (prepare_for_demo.CommandResult(0, "", ""), "origin/release/demo"),
    )
    monkeypatch.setattr(prepare_for_demo, "git_ref_full", fake_ref_full)
    monkeypatch.setattr(prepare_for_demo, "git_ref_short", lambda _ref: "same")
    monkeypatch.setattr(prepare_for_demo, "git_ref_timestamp", lambda _ref: ref_time)
    monkeypatch.setattr(prepare_for_demo, "configured_docker_error", lambda _env: None)
    monkeypatch.setattr(prepare_for_demo, "find_docker", lambda _env: "docker")
    monkeypatch.setattr(
        prepare_for_demo,
        "image_info",
        lambda _docker, _image: ("image-id", ref_time),
    )
    monkeypatch.setattr(
        prepare_for_demo,
        "running_app_containers",
        lambda _docker, _image: prepare_for_demo.ContainerScan([], None),
    )
    monkeypatch.setattr(prepare_for_demo, "APP_WRAPPERS", {})

    checks = prepare_for_demo.run_checks(
        Namespace(fetch=True, ref="release/demo", image="mcp-geo-server", rebuild=False)
    )

    assert resolved_refs == ["HEAD", "origin/release/demo"]
    assert any(
        check.name == "git.ref" and "origin/release/demo" in check.detail for check in checks
    )


def test_run_checks_fails_when_docker_container_scan_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ref_time = datetime(2026, 4, 22, 12, 0, tzinfo=UTC)

    def fake_run(
        args: list[str],
        *,
        check: bool = True,
        env: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> prepare_for_demo.CommandResult:
        assert env is None
        assert timeout is None
        if args == ["git", "status", "--porcelain"]:
            assert check is True
            return prepare_for_demo.CommandResult(0, "", "")
        if args == ["docker", "info"]:
            assert check is False
            return prepare_for_demo.CommandResult(0, "", "")
        raise AssertionError(f"Unexpected command: {args}")

    monkeypatch.setattr(prepare_for_demo, "_run", fake_run)
    monkeypatch.setattr(prepare_for_demo, "git_ref_full", lambda _ref: "same-sha")
    monkeypatch.setattr(prepare_for_demo, "git_ref_short", lambda _ref: "same")
    monkeypatch.setattr(prepare_for_demo, "git_ref_timestamp", lambda _ref: ref_time)
    monkeypatch.setattr(prepare_for_demo, "configured_docker_error", lambda _env: None)
    monkeypatch.setattr(prepare_for_demo, "find_docker", lambda _env: "docker")
    monkeypatch.setattr(
        prepare_for_demo,
        "image_info",
        lambda _docker, _image: ("image-id", ref_time),
    )
    monkeypatch.setattr(
        prepare_for_demo,
        "running_app_containers",
        lambda _docker, _image: prepare_for_demo.ContainerScan([], "permission denied"),
    )
    monkeypatch.setattr(prepare_for_demo, "APP_WRAPPERS", {})

    checks = prepare_for_demo.run_checks(
        Namespace(fetch=False, ref="HEAD", image="mcp-geo-server", rebuild=False)
    )

    container_checks = [check for check in checks if check.name == "docker.containers"]
    assert [check.level for check in container_checks] == ["FAIL"]
    assert "permission denied" in container_checks[0].detail


def test_run_checks_reports_docker_rebuild_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ref_time = datetime(2026, 4, 22, 12, 0, tzinfo=UTC)

    def fake_run(
        args: list[str],
        *,
        check: bool = True,
        env: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> prepare_for_demo.CommandResult:
        assert env is None
        assert timeout is None
        if args == ["git", "status", "--porcelain"]:
            assert check is True
            return prepare_for_demo.CommandResult(0, "", "")
        if args == ["docker", "info"]:
            assert check is False
            return prepare_for_demo.CommandResult(0, "", "")
        raise AssertionError(f"Unexpected command: {args}")

    monkeypatch.setattr(prepare_for_demo, "_run", fake_run)
    monkeypatch.setattr(prepare_for_demo, "git_ref_full", lambda _ref: "same-sha")
    monkeypatch.setattr(prepare_for_demo, "git_ref_short", lambda _ref: "same")
    monkeypatch.setattr(prepare_for_demo, "git_ref_timestamp", lambda _ref: ref_time)
    monkeypatch.setattr(prepare_for_demo, "configured_docker_error", lambda _env: None)
    monkeypatch.setattr(prepare_for_demo, "find_docker", lambda _env: "docker")
    monkeypatch.setattr(
        prepare_for_demo,
        "build_image",
        lambda _docker, _image: prepare_for_demo.CommandResult(1, "", "build failed"),
    )
    monkeypatch.setattr(prepare_for_demo, "image_info", lambda _docker, _image: None)
    monkeypatch.setattr(
        prepare_for_demo,
        "running_app_containers",
        lambda _docker, _image: prepare_for_demo.ContainerScan([], None),
    )
    monkeypatch.setattr(prepare_for_demo, "APP_WRAPPERS", {})

    checks = prepare_for_demo.run_checks(
        Namespace(fetch=False, ref="HEAD", image="mcp-geo-server", rebuild=True)
    )

    rebuild_checks = [check for check in checks if check.name == "docker.image.rebuild"]
    assert [check.level for check in rebuild_checks] == ["INFO", "FAIL"]
    assert "build failed" in rebuild_checks[1].detail
