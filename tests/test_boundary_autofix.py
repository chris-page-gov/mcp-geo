from __future__ import annotations

from pathlib import Path

from scripts import boundary_autofix


def test_run_pipeline_forwards_workdir(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_call(cmd, cwd):
        captured["cmd"] = cmd
        captured["cwd"] = cwd
        return 0

    monkeypatch.setattr(boundary_autofix.subprocess, "call", fake_call)

    exit_code = boundary_autofix._run_pipeline(
        ["--mode", "all"],
        workdir=Path("/tmp/boundary-runs"),
    )

    assert exit_code == 0
    assert captured["cwd"] == boundary_autofix.REPO_ROOT.as_posix()
    assert captured["cmd"] == [
        "python",
        "scripts/boundary_pipeline.py",
        "--workdir",
        "/tmp/boundary-runs",
        "--mode",
        "all",
    ]
