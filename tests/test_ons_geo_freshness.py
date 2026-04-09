from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from server.ons_geo_freshness import (
    latest_published_epoch,
    load_addressbase_epoch_schedule,
    next_scheduled_epoch,
    parse_epoch_from_text,
    summarize_uprn_dataset_freshness,
)


def _schedule() -> list[dict[str, object]]:
    return [
        {"epoch": 123, "publication_date": "2025-11-27"},
        {"epoch": 124, "publication_date": "2026-01-08"},
        {"epoch": 125, "publication_date": "2026-02-19"},
        {"epoch": 126, "publication_date": "2026-04-02"},
        {"epoch": 127, "publication_date": "2026-05-14", "scheduled": True},
    ]


def test_parse_epoch_from_text_prefers_epoch_marker() -> None:
    assert parse_epoch_from_text("ONS UPRN Directory (December 2025) (Epoch 123)") == 123
    assert parse_epoch_from_text(None, "https://example.test/epoch-126") == 126


def test_latest_and_next_epoch_helpers() -> None:
    schedule = _schedule()
    latest = latest_published_epoch(schedule, today=date(2026, 4, 9))
    upcoming = next_scheduled_epoch(schedule, today=date(2026, 4, 9))
    assert latest == {"epoch": 126, "publication_date": "2026-04-02"}
    assert upcoming == {
        "epoch": 127,
        "publication_date": "2026-05-14",
        "scheduled": True,
    }


def test_summarize_uprn_dataset_freshness_flags_lagging_epoch() -> None:
    freshness = summarize_uprn_dataset_freshness(
        dataset_id="ONSUD",
        resolved_release="December 2025 (Epoch 123)",
        schedule=_schedule(),
        today=date(2026, 4, 9),
    )
    assert freshness is not None
    assert freshness["status"] == "lagging"
    assert freshness["resolvedEpoch"] == 123
    assert freshness["latestPublishedEpoch"] == 126
    assert freshness["lagEpochs"] == 3


def test_summarize_uprn_dataset_freshness_current_epoch() -> None:
    freshness = summarize_uprn_dataset_freshness(
        dataset_id="NSUL",
        resolved_release="National Statistics UPRN Lookup (April 2026) (Epoch 126)",
        schedule=_schedule(),
        today=date(2026, 4, 9),
    )
    assert freshness is not None
    assert freshness["status"] == "current"
    assert freshness["lagEpochs"] == 0


def test_summarize_uprn_dataset_freshness_not_applicable_for_postcodes() -> None:
    assert (
        summarize_uprn_dataset_freshness(
            dataset_id="ONSPD",
            resolved_release="February 2026",
            schedule=_schedule(),
            today=date(2026, 4, 9),
        )
        is None
    )


def test_load_addressbase_epoch_schedule_filters_invalid_entries(tmp_path: Path) -> None:
    path = tmp_path / "schedule.json"
    path.write_text(
        json.dumps(
            {
                "epochs": [
                    {"epoch": 125, "publication_date": "2026-02-19"},
                    {"epoch": "bad", "publication_date": "2026-04-02"},
                    {"epoch": 126, "publication_date": ""},
                    "skip",
                ]
            }
        ),
        encoding="utf-8",
    )
    assert load_addressbase_epoch_schedule(path) == [
        {"epoch": 125, "publication_date": "2026-02-19", "scheduled": False}
    ]


def test_summarize_uprn_dataset_freshness_handles_schedule_unavailable() -> None:
    freshness = summarize_uprn_dataset_freshness(
        dataset_id="ONSUD",
        resolved_release="Epoch 126",
        schedule=[],
        today=date(2026, 4, 9),
    )
    assert freshness is not None
    assert freshness["status"] == "schedule_unavailable"


def test_summarize_uprn_dataset_freshness_handles_unknown_epoch() -> None:
    freshness = summarize_uprn_dataset_freshness(
        dataset_id="NSUL",
        resolved_release="December 2025 release",
        resolved_source_url="https://example.test/no-epoch-here",
        schedule=_schedule(),
        today=date(2026, 4, 9),
    )
    assert freshness is not None
    assert freshness["status"] == "epoch_unknown"


def test_summarize_uprn_dataset_freshness_handles_epoch_ahead_of_schedule() -> None:
    freshness = summarize_uprn_dataset_freshness(
        dataset_id="ONSUD",
        resolved_release="Future release (Epoch 130)",
        schedule=_schedule(),
        today=date(2026, 4, 9),
    )
    assert freshness is not None
    assert freshness["status"] == "ahead_of_schedule"
    assert freshness["lagEpochs"] == 0
