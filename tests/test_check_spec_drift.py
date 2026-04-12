from __future__ import annotations

import subprocess
from pathlib import Path

import scripts.check_spec_drift as spec_drift


def test_audit_target_treats_uninitialized_submodule_as_missing_local_git_state(
    monkeypatch,
    tmp_path: Path,
) -> None:
    submodule_root = tmp_path / "docs" / "vendor" / "example"
    submodule_root.mkdir(parents=True)
    target = spec_drift.SpecTarget(
        name="example",
        submodule_path="docs/vendor/example",
        tracked_paths=("README.md",),
    )

    calls: list[tuple[Path, tuple[str, ...]]] = []

    def fake_run_git(path: Path, *args: str) -> str | None:
        calls.append((path, args))
        return "should-not-be-used"

    monkeypatch.setattr(spec_drift, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(spec_drift, "_run_git", fake_run_git)

    audit = spec_drift.audit_target(target)

    assert audit.local_head is None
    assert audit.remote_head is None
    assert audit.drift_status == "missing_local_git_state"
    assert audit.missing_paths == ["docs/vendor/example/README.md"]
    assert calls == []


def test_audit_target_reads_heads_for_initialized_standalone_checkout(
    monkeypatch,
    tmp_path: Path,
) -> None:
    submodule_root = tmp_path / "docs" / "vendor" / "example"
    submodule_root.mkdir(parents=True)
    (submodule_root / ".git").write_text("gitdir: ../.git/modules/example\n", encoding="utf-8")
    (submodule_root / "README.md").write_text("ok\n", encoding="utf-8")
    target = spec_drift.SpecTarget(
        name="example",
        submodule_path="docs/vendor/example",
        tracked_paths=("README.md",),
    )

    def fake_run_git(path: Path, *args: str) -> str | None:
        assert path == submodule_root
        if args == ("rev-parse", "--show-toplevel"):
            return str(submodule_root)
        if args == ("rev-parse", "HEAD"):
            return "abc123"
        if args == ("ls-remote", "origin", "HEAD"):
            return "def456\tHEAD"
        raise AssertionError(f"Unexpected git args: {args}")

    monkeypatch.setattr(spec_drift, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(spec_drift, "_run_git", fake_run_git)

    audit = spec_drift.audit_target(target)

    assert audit.local_head == "abc123"
    assert audit.remote_head == "def456"
    assert audit.drift_status == "behind_or_diverged"
    assert audit.missing_paths == []


def test_fail_on_drift_ignores_remote_unavailable_without_missing_paths(monkeypatch) -> None:
    audit = spec_drift.TargetAudit(
        name="example",
        submodule_path="docs/vendor/example",
        local_head="abc123",
        remote_head=None,
        drift_status="remote_unavailable",
        missing_paths=[],
        notes="offline",
    )

    monkeypatch.setattr(spec_drift, "SPEC_TARGETS", (object(),))
    monkeypatch.setattr(spec_drift, "audit_target", lambda _target: audit)
    monkeypatch.setattr(spec_drift, "render_text", lambda _audits: "Specification Drift Audit\n")

    assert spec_drift.main(["--fail-on-drift"]) == 0


def test_fail_on_drift_returns_error_for_missing_paths_even_if_remote_unavailable(
    monkeypatch,
) -> None:
    audit = spec_drift.TargetAudit(
        name="example",
        submodule_path="docs/vendor/example",
        local_head="abc123",
        remote_head=None,
        drift_status="remote_unavailable",
        missing_paths=["docs/vendor/example/README.md"],
        notes="offline",
    )

    monkeypatch.setattr(spec_drift, "SPEC_TARGETS", (object(),))
    monkeypatch.setattr(spec_drift, "audit_target", lambda _target: audit)
    monkeypatch.setattr(spec_drift, "render_text", lambda _audits: "Specification Drift Audit\n")

    assert spec_drift.main(["--fail-on-drift"]) == 1


def test_run_git_uses_path_resolved_git(monkeypatch, tmp_path: Path) -> None:
    seen_args: list[list[str]] = []

    def fake_run(args: list[str], **kwargs) -> subprocess.CompletedProcess[str]:
        seen_args.append(args)
        assert kwargs["check"] is True
        assert kwargs["capture_output"] is True
        assert kwargs["text"] is True
        return subprocess.CompletedProcess(args=args, returncode=0, stdout="abc123\n")

    monkeypatch.setattr(spec_drift.shutil, "which", lambda name: "/opt/homebrew/bin/git")
    monkeypatch.setattr(spec_drift.subprocess, "run", fake_run)

    result = spec_drift._run_git(tmp_path, "rev-parse", "HEAD")

    assert result == "abc123"
    assert seen_args == [["/opt/homebrew/bin/git", "-C", str(tmp_path), "rev-parse", "HEAD"]]
