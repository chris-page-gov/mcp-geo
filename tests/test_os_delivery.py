from __future__ import annotations

from pathlib import Path

from tools import os_delivery


def test_parse_delivery_and_inline_limits() -> None:
    mode, err = os_delivery.parse_delivery(None, default="auto")
    assert mode == "auto"
    assert err is None

    mode, err = os_delivery.parse_delivery("INLINE")
    assert mode == "inline"
    assert err is None

    mode, err = os_delivery.parse_delivery(123)
    assert mode is None
    assert err is not None

    mode, err = os_delivery.parse_delivery("bad")
    assert mode is None
    assert err is not None

    value, err = os_delivery.parse_inline_max_bytes(None)
    assert value is not None and value > 0
    assert err is None

    value, err = os_delivery.parse_inline_max_bytes(0)
    assert value is None
    assert err is not None


def test_select_delivery_mode_and_payload_bytes() -> None:
    assert os_delivery.select_delivery_mode(
        requested_delivery="resource",
        payload_bytes=10,
        inline_max_bytes=100,
    ) == "resource"
    assert os_delivery.select_delivery_mode(
        requested_delivery="inline",
        payload_bytes=200,
        inline_max_bytes=100,
    ) == "inline"
    assert os_delivery.select_delivery_mode(
        requested_delivery="auto",
        payload_bytes=200,
        inline_max_bytes=100,
    ) == "resource"
    assert os_delivery.select_delivery_mode(
        requested_delivery="auto",
        payload_bytes=50,
        inline_max_bytes=100,
    ) == "inline"
    assert os_delivery.payload_bytes({"a": 1}) > 0


def test_write_resource_payload_and_paths(monkeypatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(
        os_delivery.settings,
        "OS_DATA_CACHE_DIR",
        str(tmp_path / "cache"),
        raising=False,
    )
    assert os_delivery.os_cache_dir() == Path(str(tmp_path / "cache"))

    monkeypatch.setattr(os_delivery, "os_exports_dir", lambda: tmp_path, raising=True)
    meta = os_delivery.write_resource_payload(prefix="demo", payload={"ok": True})
    out_path = Path(meta["path"])
    assert out_path.exists()
    assert meta["resourceUri"].startswith("resource://mcp-geo/os-exports/")
    assert meta["bytes"] > 0
    assert len(meta["sha256"]) == 64
