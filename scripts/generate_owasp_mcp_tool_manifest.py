#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from server.owasp_mcp_validation import (
    build_tool_manifest,
    pretty_json,
    tool_snapshots_from_registry,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate the OWASP MCP tool manifest lockfile.")
    parser.add_argument(
        "--output",
        default="security/owasp_mcp/tool_manifest.lock.json",
        help="Path to the manifest lockfile.",
    )
    parser.add_argument(
        "--signing-key",
        help="Optional private key path used to sign the manifest with openssl.",
    )
    parser.add_argument(
        "--signature-output",
        default="security/owasp_mcp/tool_manifest.lock.json.sig",
        help="Detached signature output path when --signing-key is provided.",
    )
    parser.add_argument(
        "--public-key-output",
        default="security/owasp_mcp/tool_manifest.pub.pem",
        help="Public key output path when --signing-key is provided.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    manifest = build_tool_manifest(tool_snapshots_from_registry())
    output.write_text(pretty_json(manifest), encoding="utf-8")
    print(f"Wrote manifest: {output}")
    if args.signing_key:
        signing_key = Path(args.signing_key).resolve()
        signature_output = Path(args.signature_output).resolve()
        public_key_output = Path(args.public_key_output).resolve()
        signature_output.parent.mkdir(parents=True, exist_ok=True)
        public_key_output.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["openssl", "rsa", "-pubout", "-in", str(signing_key), "-out", str(public_key_output)],
            check=True,
        )
        subprocess.run(
            [
                "openssl",
                "dgst",
                "-sha256",
                "-sign",
                str(signing_key),
                "-out",
                str(signature_output),
                str(output),
            ],
            check=True,
        )
        print(f"Wrote public key: {public_key_output}")
        print(f"Wrote detached signature: {signature_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
