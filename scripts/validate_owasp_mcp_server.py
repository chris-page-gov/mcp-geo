#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib
import os
import sys
from pathlib import Path

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

owasp_validation = importlib.import_module("server.owasp_mcp_validation")
ValidationDataError = owasp_validation.ValidationDataError
should_fail = owasp_validation.should_fail
validate_repo = owasp_validation.validate_repo
write_outputs = owasp_validation.write_outputs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate MCP-Geo against the OWASP MCP server hardening baseline."
    )
    parser.add_argument("--profile", default="prod-strict")
    parser.add_argument(
        "--format",
        default="both",
        choices=["json", "markdown", "both"],
        help="Report format to emit. JSON backlog is always emitted.",
    )
    parser.add_argument("--output-dir", required=True)
    parser.add_argument(
        "--fail-on",
        default="required",
        choices=["none", "minimum_bar", "required"],
    )
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parent.parent))
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    repo_root = Path(args.repo_root).resolve()
    try:
        report, backlog = validate_repo(repo_root, profile=args.profile)
        outputs = write_outputs(
            report,
            backlog,
            output_dir=Path(args.output_dir).resolve(),
            output_format=args.format,
        )
    except ValidationDataError as exc:
        parser.error(str(exc))
        return 2

    print("OWASP MCP validation completed.")
    print(f"JSON report: {outputs['json_report']}")
    print(f"Markdown report: {outputs['markdown_report']}")
    print(f"Backlog: {outputs['backlog']}")
    return 1 if should_fail(report, args.fail_on) else 0


if __name__ == "__main__":
    raise SystemExit(main())
