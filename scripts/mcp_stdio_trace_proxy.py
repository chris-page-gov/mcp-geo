#!/usr/bin/env python3
"""MCP stdio proxy that logs JSON-RPC traffic.

This proxy sits between an MCP client and an MCP stdio server, forwarding bytes
unaltered while extracting best-effort JSON-RPC messages for logging.

It supports both:
- JSON lines framing (one JSON-RPC object per line)
- Content-Length framing (LSP-style headers + body)

Usage:
  python scripts/mcp_stdio_trace_proxy.py --log logs/mcp-trace.jsonl -- mcp-geo-stdio
"""
from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional


_CONTENT_LENGTH_RE = re.compile(r"^content-length\s*:\s*(\d+)\s*$", re.IGNORECASE)


def _maybe_parse_json(text: str) -> tuple[Optional[dict[str, Any] | list[Any]], Optional[str]]:
    stripped = text.strip()
    if not stripped.startswith("{") and not stripped.startswith("["):
        return None, None
    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError as exc:
        return None, str(exc)
    return payload, None


class _FrameExtractor:
    def __init__(self) -> None:
        self._buffer = bytearray()

    def feed(self, data: bytes) -> list[dict[str, Any]]:
        self._buffer.extend(data)
        frames: list[dict[str, Any]] = []

        # Parse as many frames as possible. We intentionally never block the
        # byte-forwarding path on decoding/logging.
        while self._buffer:
            # Skip leading blank lines.
            while self._buffer and self._buffer[0] in (ord("\r"), ord("\n")):
                del self._buffer[:1]
                if not self._buffer:
                    return frames

            # Content-Length framing (headers then body).
            if self._buffer[:15].lower() == b"content-length:":
                header_end = self._buffer.find(b"\r\n\r\n")
                sep_len = 4
                if header_end == -1:
                    header_end = self._buffer.find(b"\n\n")
                    sep_len = 2
                if header_end == -1:
                    break

                header_bytes = bytes(self._buffer[:header_end])
                header_text = header_bytes.decode("utf-8", errors="replace")
                length: Optional[int] = None
                for line in header_text.replace("\r", "").split("\n"):
                    line = line.strip()
                    if not line:
                        continue
                    match = _CONTENT_LENGTH_RE.match(line)
                    if match:
                        length = int(match.group(1))
                        break
                if length is None:
                    # Malformed header; fall back to line parsing to avoid stalling.
                    newline = self._buffer.find(b"\n")
                    if newline == -1:
                        break
                    line = bytes(self._buffer[: newline + 1])
                    del self._buffer[: newline + 1]
                    frames.append(
                        {
                            "frame": "line",
                            "raw": line.decode("utf-8", errors="replace").rstrip("\r\n"),
                        }
                    )
                    continue

                body_start = header_end + sep_len
                total = body_start + length
                if len(self._buffer) < total:
                    break

                body_bytes = bytes(self._buffer[body_start:total])
                del self._buffer[:total]
                frames.append(
                    {
                        "frame": "content-length",
                        "headers": header_text,
                        "content_length": length,
                        "raw": body_bytes.decode("utf-8", errors="replace"),
                    }
                )
                continue

            # Line framing (or stderr logs): parse up to newline.
            newline = self._buffer.find(b"\n")
            if newline == -1:
                break
            line = bytes(self._buffer[: newline + 1])
            del self._buffer[: newline + 1]
            frames.append(
                {
                    "frame": "line",
                    "raw": line.decode("utf-8", errors="replace").rstrip("\r\n"),
                }
            )

        return frames


def _write_record(log_fh, direction: str, payload: dict[str, Any]) -> None:
    record: Dict[str, Any] = {"ts": time.time(), "direction": direction}
    record.update(payload)
    raw = payload.get("raw")
    if isinstance(raw, str) and direction in {"client->server", "server->client"}:
        parsed, parse_error = _maybe_parse_json(raw)
        if parse_error:
            record["parse_error"] = parse_error
        elif parsed is not None:
            record["json"] = parsed
            if isinstance(parsed, dict):
                record["method"] = parsed.get("method")
                record["id"] = parsed.get("id")
    log_fh.write(json.dumps(record) + "\n")
    log_fh.flush()


def _write_bytes(target, data: bytes) -> None:
    target.write(data)
    flush = getattr(target, "flush", None)
    if callable(flush):
        flush()


async def _pump_bytes(
    reader: asyncio.StreamReader,
    writer,
    log_fh,
    direction: str,
    extractor: _FrameExtractor,
    *,
    close_writer_on_eof: bool = False,
) -> None:
    while True:
        chunk = await reader.read(4096)
        if not chunk:
            break
        if writer is not None:
            if hasattr(writer, "drain"):
                writer.write(chunk)
                await writer.drain()
            else:
                _write_bytes(writer, chunk)
        for frame in extractor.feed(chunk):
            _write_record(log_fh, direction, frame)

    if close_writer_on_eof:
        # If the input side of the proxy closes (e.g., client exits), close the
        # downstream stdin so the wrapped server can terminate cleanly.
        close = getattr(writer, "close", None)
        if callable(close):
            close()
            wait_closed = getattr(writer, "wait_closed", None)
            if callable(wait_closed):
                try:
                    await wait_closed()
                except Exception:
                    pass


async def main() -> int:
    parser = argparse.ArgumentParser(description="MCP stdio trace proxy")
    parser.add_argument("--log", default="logs/mcp-trace.jsonl", help="Path to JSONL log file")
    parser.add_argument("cmd", nargs=argparse.REMAINDER, help="Command to run (prefix with --)")
    args = parser.parse_args()

    if not args.cmd or args.cmd[0] != "--":
        parser.error("Command must be provided after --")

    cmd = args.cmd[1:]
    log_path = Path(args.log)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    if proc.stdin is None or proc.stdout is None or proc.stderr is None:
        raise RuntimeError("Failed to open subprocess pipes")

    loop = asyncio.get_running_loop()
    stdin_reader = asyncio.StreamReader()
    stdin_protocol = asyncio.StreamReaderProtocol(stdin_reader)
    await loop.connect_read_pipe(lambda: stdin_protocol, sys.stdin.buffer)

    with log_path.open("a", encoding="utf-8") as log_fh:
        tasks = [
            asyncio.create_task(
                _pump_bytes(
                    reader=stdin_reader,
                    writer=proc.stdin,
                    log_fh=log_fh,
                    direction="client->server",
                    extractor=_FrameExtractor(),
                    close_writer_on_eof=True,
                )
            ),
            asyncio.create_task(
                _pump_bytes(
                    reader=proc.stdout,
                    writer=sys.stdout.buffer,
                    log_fh=log_fh,
                    direction="server->client",
                    extractor=_FrameExtractor(),
                    close_writer_on_eof=False,
                )
            ),
            asyncio.create_task(
                _pump_bytes(
                    reader=proc.stderr,
                    writer=sys.stderr.buffer,
                    log_fh=log_fh,
                    direction="server->stderr",
                    extractor=_FrameExtractor(),
                    close_writer_on_eof=False,
                )
            ),
        ]

        _done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            task.cancel()

    return await proc.wait()

def cli() -> None:
    raise SystemExit(asyncio.run(main()))


if __name__ == "__main__":
    cli()
