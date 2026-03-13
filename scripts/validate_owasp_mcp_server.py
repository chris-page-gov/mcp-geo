#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from server.owasp_mcp_validation import (
    ValidationDataError,
    should_fail,
    validate_repo,
    write_outputs,
)


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
