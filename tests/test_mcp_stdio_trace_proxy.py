from __future__ import annotations

from scripts.mcp_stdio_trace_proxy import _FrameExtractor


def test_frame_extractor_skips_leading_blank_lines() -> None:
    extractor = _FrameExtractor()

    frames = extractor.feed(b"\n\n{\"jsonrpc\":\"2.0\"}\n")

    assert frames == [{"frame": "line", "raw": '{"jsonrpc":"2.0"}'}]
