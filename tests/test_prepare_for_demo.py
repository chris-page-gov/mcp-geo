from __future__ import annotations

from datetime import UTC, datetime

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
