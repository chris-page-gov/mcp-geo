from __future__ import annotations

import re
import time
from html import unescape
from typing import Any
from xml.etree import ElementTree

import requests

from scripts.ons_geo_cache_refresh import DEFAULT_SOURCES_PATH, load_manifest, probe_dataset_source
from server.ons_geo_freshness import (
    latest_published_epoch,
    load_addressbase_epoch_schedule,
    next_scheduled_epoch,
    summarize_uprn_dataset_freshness,
)

GEO_SEARCH_COLLECTION_ITEMS_URL = (
    "https://geoportal.statistics.gov.uk/api/search/v1/collections/dataset/items"
)
GEO_RSS_FEED_URL = "https://geoportal.statistics.gov.uk/api/feed/rss/2.0"

_UPRN_PRODUCTS = ("ONSUD", "NSUL")
_NOTICE_KEYWORDS = ("uprn", "onsud", "nsul")
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_SPACE_RE = re.compile(r"\s+")


def _strip_html(text: str | None) -> str:
    raw = unescape(str(text or ""))
    without_tags = _HTML_TAG_RE.sub(" ", raw)
    return _SPACE_RE.sub(" ", without_tags).strip()


def _iso_from_epoch_millis(value: Any) -> str | None:
    if not isinstance(value, (int, float)):
        return None
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(float(value) / 1000.0))


def _record_summary(feature: dict[str, Any]) -> dict[str, Any]:
    properties = feature.get("properties", {}) if isinstance(feature, dict) else {}
    return {
        "recordId": feature.get("id"),
        "title": properties.get("title"),
        "type": properties.get("type"),
        "owner": properties.get("owner"),
        "modified": _iso_from_epoch_millis(properties.get("modified")),
        "keywords": properties.get("typeKeywords", []),
        "description": _strip_html(properties.get("description")),
    }


def _score_geoportal_feature(product: str, feature: dict[str, Any]) -> tuple[int, int, str]:
    properties = feature.get("properties", {}) if isinstance(feature, dict) else {}
    title = str(properties.get("title") or "").strip()
    lowered = title.lower()
    score = 0
    if lowered == f"{product.lower()}_latest":
        score += 100
    elif product.lower() in lowered:
        score += 20
    modified = _iso_from_epoch_millis(properties.get("modified")) or ""
    return (score, int(properties.get("modified") or 0), modified)


def fetch_geoportal_dataset_latest(product: str, *, timeout: float) -> dict[str, Any]:
    response = requests.get(
        GEO_SEARCH_COLLECTION_ITEMS_URL,
        params={"q": product, "limit": "10"},
        timeout=timeout,
    )
    response.raise_for_status()
    payload = response.json()
    features = payload.get("features", []) if isinstance(payload, dict) else []
    candidates = [item for item in features if isinstance(item, dict)]
    if not candidates:
        raise ValueError(f"No Geoportal dataset item found for {product}")
    chosen = sorted(
        candidates,
        key=lambda item: _score_geoportal_feature(product, item),
        reverse=True,
    )[0]
    return _record_summary(chosen)


def _extract_relevant_notice_texts(
    channel_description: str, items: list[dict[str, Any]]
) -> list[str]:
    notices: list[str] = []
    description_text = _strip_html(channel_description)
    for sentence in re.split(r"(?<=[.!?])\s+", description_text):
        lowered = sentence.lower()
        if any(keyword in lowered for keyword in _NOTICE_KEYWORDS):
            notices.append(sentence.strip())
    for item in items:
        combined = " ".join(
            _strip_html(item.get(key)) for key in ("title", "description") if item.get(key)
        )
        lowered = combined.lower()
        if combined and any(keyword in lowered for keyword in _NOTICE_KEYWORDS):
            notices.append(combined)
    deduped: list[str] = []
    seen: set[str] = set()
    for notice in notices:
        normalized = notice.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(normalized)
    return deduped


def _classify_notice_state(notices: list[str]) -> str | None:
    lowered = " ".join(notice.lower() for notice in notices)
    if not lowered:
        return None
    if "paused regular updates" in lowered or "pausing production" in lowered:
        return "paused_by_publisher"
    if "corrected" in lowered or "updated products" in lowered or "investigating" in lowered:
        return "correction_notice_active"
    return "notice_active"


def fetch_geoportal_rss_status(*, timeout: float) -> dict[str, Any]:
    response = requests.get(GEO_RSS_FEED_URL, timeout=timeout)
    response.raise_for_status()
    xml_text = response.text
    root = ElementTree.fromstring(xml_text)
    channel = root.find("channel")
    if channel is None:
        raise ValueError("RSS feed did not contain a channel element")

    description = channel.findtext("description", default="")
    items: list[dict[str, Any]] = []
    for item in channel.findall("item"):
        items.append(
            {
                "title": item.findtext("title", default=""),
                "description": item.findtext("description", default=""),
                "pubDate": item.findtext("pubDate", default=""),
                "link": item.findtext("link", default=""),
            }
        )

    relevant_notices = _extract_relevant_notice_texts(description, items)
    return {
        "sourceUrl": GEO_RSS_FEED_URL,
        "status": _classify_notice_state(relevant_notices),
        "relevantNotices": relevant_notices,
    }


def build_release_audit(*, timeout: float) -> dict[str, Any]:
    version, products, _support_products = load_manifest(DEFAULT_SOURCES_PATH)
    schedule = load_addressbase_epoch_schedule()
    rss_status = fetch_geoportal_rss_status(timeout=timeout)
    results: list[dict[str, Any]] = []

    for dataset_id in _UPRN_PRODUCTS:
        dataset = next((item for item in products if item.dataset_id == dataset_id), None)
        if dataset is None:
            continue
        probe = probe_dataset_source(
            dataset,
            timeout=timeout,
            file_overrides={},
            url_overrides={},
        )
        freshness = summarize_uprn_dataset_freshness(
            dataset_id=dataset.dataset_id,
            resolved_release=probe.resolved_release,
            resolved_source_url=probe.resolved_source_url,
            schedule=schedule,
        )
        results.append(
            {
                "id": dataset.dataset_id,
                "title": dataset.title,
                "resolvedRelease": probe.resolved_release,
                "resolvedSourceUrl": probe.resolved_source_url,
                "schemaProbeStatus": probe.schema_probe_status,
                "freshness": freshness,
                "publisherNoticeStatus": rss_status.get("status"),
                "geoportalRecord": fetch_geoportal_dataset_latest(
                    dataset.dataset_id,
                    timeout=timeout,
                ),
            }
        )

    latest_published = latest_published_epoch(schedule)
    next_scheduled = next_scheduled_epoch(schedule)

    return {
        "version": version,
        "addressBaseSchedule": {
            "latestPublished": latest_published,
            "nextScheduled": next_scheduled,
            "source": "resources/addressbase_epoch_schedule.json",
        },
        "publisherNotices": rss_status,
        "datasets": results,
    }
