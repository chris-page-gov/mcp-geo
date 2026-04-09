from __future__ import annotations

from server.ons_geo_catalog import (
    _classify_notice_state,
    _extract_relevant_notice_texts,
    _score_geoportal_feature,
)


def test_extract_relevant_notice_texts_filters_uprn_messages() -> None:
    notices = _extract_relevant_notice_texts(
        (
            "We have identified issues in NSUL and ONSUD and are pausing production. "
            "Another unrelated note."
        ),
        [],
    )
    assert any("pausing production" in item.lower() for item in notices)


def test_classify_notice_state_detects_pause() -> None:
    status = _classify_notice_state(
        ["We are pausing production of these and will keep users updated."]
    )
    assert status == "paused_by_publisher"


def test_score_geoportal_feature_prefers_latest_title() -> None:
    latest = {
        "id": "1",
        "properties": {"title": "ONSUD_LATEST", "modified": 1760538778000},
    }
    other = {
        "id": "2",
        "properties": {"title": "Some other ONSUD item", "modified": 1760538779000},
    }
    assert _score_geoportal_feature("ONSUD", latest) > _score_geoportal_feature("ONSUD", other)
