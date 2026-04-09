from __future__ import annotations

from types import SimpleNamespace

import pytest

import server.ons_geo_catalog as ons_geo_catalog
from server.ons_geo_catalog import (
    _classify_notice_state,
    _extract_relevant_notice_texts,
    _iso_from_epoch_millis,
    _record_summary,
    _score_geoportal_feature,
    _strip_html,
    build_release_audit,
    fetch_geoportal_dataset_latest,
    fetch_geoportal_rss_status,
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


def test_strip_html_and_epoch_millis_helpers() -> None:
    assert _strip_html("<p>Hello <strong>world</strong></p>") == "Hello world"
    assert _iso_from_epoch_millis(0) == "1970-01-01T00:00:00Z"
    assert _iso_from_epoch_millis("bad") is None


def test_record_summary_normalizes_description() -> None:
    summary = _record_summary(
        {
            "id": "abc",
            "properties": {
                "title": "ONSUD_LATEST",
                "type": "Dataset",
                "owner": "ONS",
                "modified": 0,
                "typeKeywords": ["Data"],
                "description": "<p>UPRN <em>release</em></p>",
            },
        }
    )
    assert summary["recordId"] == "abc"
    assert summary["title"] == "ONSUD_LATEST"
    assert summary["modified"] == "1970-01-01T00:00:00Z"
    assert summary["description"] == "UPRN release"


def test_classify_notice_state_variants() -> None:
    assert _classify_notice_state(["Corrected products will be published shortly."]) == (
        "correction_notice_active"
    )
    assert _classify_notice_state(["General operational message."]) == "notice_active"
    assert _classify_notice_state([]) is None


def test_fetch_geoportal_dataset_latest_selects_best_candidate(monkeypatch) -> None:
    class DummyResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return {
                "features": [
                    {
                        "id": "older",
                        "properties": {
                            "title": "Some other ONSUD item",
                            "modified": 1760538778000,
                            "description": "<p>Older</p>",
                        },
                    },
                    {
                        "id": "best",
                        "properties": {
                            "title": "ONSUD_LATEST",
                            "modified": 1760538777000,
                            "description": "<p>Latest item</p>",
                        },
                    },
                ]
            }

    monkeypatch.setattr(ons_geo_catalog.requests, "get", lambda *args, **kwargs: DummyResponse())

    summary = fetch_geoportal_dataset_latest("ONSUD", timeout=2.0)
    assert summary["recordId"] == "best"
    assert summary["title"] == "ONSUD_LATEST"
    assert summary["description"] == "Latest item"


def test_fetch_geoportal_dataset_latest_raises_when_missing(monkeypatch) -> None:
    class DummyResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return {"features": []}

    monkeypatch.setattr(ons_geo_catalog.requests, "get", lambda *args, **kwargs: DummyResponse())

    with pytest.raises(ValueError, match="No Geoportal dataset item found"):
        fetch_geoportal_dataset_latest("ONSUD", timeout=2.0)


def test_fetch_geoportal_rss_status_parses_relevant_notices(monkeypatch) -> None:
    class DummyResponse:
        text = """
        <rss>
          <channel>
            <description><![CDATA[We are pausing production of ONSUD and NSUL.]]></description>
            <item>
              <title>Unrelated item</title>
              <description>Nothing to see here.</description>
            </item>
            <item>
              <title>ONSUD update</title>
              <description><![CDATA[Corrected products are being prepared.]]></description>
            </item>
          </channel>
        </rss>
        """

        def raise_for_status(self) -> None:
            return None

    monkeypatch.setattr(ons_geo_catalog.requests, "get", lambda *args, **kwargs: DummyResponse())

    status = fetch_geoportal_rss_status(timeout=2.0)
    assert status["status"] == "paused_by_publisher"
    assert len(status["relevantNotices"]) == 2


def test_fetch_geoportal_rss_status_requires_channel(monkeypatch) -> None:
    class DummyResponse:
        text = "<rss></rss>"

        def raise_for_status(self) -> None:
            return None

    monkeypatch.setattr(ons_geo_catalog.requests, "get", lambda *args, **kwargs: DummyResponse())

    with pytest.raises(ValueError, match="channel element"):
        fetch_geoportal_rss_status(timeout=2.0)


def test_build_release_audit_combines_schedule_probe_and_geoportal(monkeypatch) -> None:
    monkeypatch.setattr(
        ons_geo_catalog,
        "load_manifest",
        lambda _path: (
            "2026-04-09",
            [
                SimpleNamespace(dataset_id="ONSUD", title="ONS UPRN Directory"),
                SimpleNamespace(dataset_id="NSUL", title="National Statistics UPRN Lookup"),
            ],
            [],
        ),
    )
    monkeypatch.setattr(
        ons_geo_catalog,
        "load_addressbase_epoch_schedule",
        lambda: [
            {"epoch": 126, "publication_date": "2026-04-02", "scheduled": False},
            {"epoch": 127, "publication_date": "2026-05-14", "scheduled": True},
        ],
    )
    monkeypatch.setattr(
        ons_geo_catalog,
        "fetch_geoportal_rss_status",
        lambda *, timeout: {
            "sourceUrl": "https://example.test/rss",
            "status": "paused_by_publisher",
            "relevantNotices": ["Paused"],
        },
    )
    monkeypatch.setattr(
        ons_geo_catalog,
        "probe_dataset_source",
        lambda dataset, **kwargs: SimpleNamespace(
            resolved_release=f"{dataset.dataset_id} (Epoch 123)",
            resolved_source_url=f"https://example.test/{dataset.dataset_id.lower()}-123.zip",
            schema_probe_status="warning",
        ),
    )
    monkeypatch.setattr(
        ons_geo_catalog,
        "fetch_geoportal_dataset_latest",
        lambda product, *, timeout: {"recordId": product, "title": f"{product}_LATEST"},
    )

    audit = build_release_audit(timeout=5.0)
    assert audit["version"] == "2026-04-09"
    assert audit["addressBaseSchedule"]["latestPublished"]["epoch"] == 126
    assert audit["addressBaseSchedule"]["nextScheduled"]["epoch"] == 127
    assert audit["publisherNotices"]["status"] == "paused_by_publisher"
    assert [row["id"] for row in audit["datasets"]] == ["ONSUD", "NSUL"]
    assert audit["datasets"][0]["geoportalRecord"]["title"] == "ONSUD_LATEST"
