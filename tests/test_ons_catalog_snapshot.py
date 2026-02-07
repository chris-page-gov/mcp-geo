import json
import os
from pathlib import Path
import time

import pytest

from server.config import settings
from tools.ons_common import ONSClient

REQUIRED_ENTRY_FIELDS = ("id", "title", "description", "keywords", "state", "links")
OPTIONAL_LIST_FIELDS = ("themes", "topics", "taxonomies")
REQUIRED_LINK_KEYS = ("editions", "latest_version", "self")


def _validate_entry_fields(entry: dict[str, object]) -> list[str]:
    errors: list[str] = []
    missing = [field for field in REQUIRED_ENTRY_FIELDS if field not in entry]
    if missing:
        errors.append(f"missing fields {missing}")
        return errors
    dataset_id = entry.get("id")
    if not isinstance(dataset_id, str) or not dataset_id.strip():
        errors.append("id must be a non-empty string")
    for field in ("title", "description", "state"):
        value = entry.get(field)
        if value is not None and not isinstance(value, str):
            errors.append(f"{field} must be string or null")
    keywords = entry.get("keywords")
    if not isinstance(keywords, list):
        errors.append("keywords must be a list")
    else:
        for keyword in keywords:
            if not isinstance(keyword, str):
                errors.append("keywords must contain strings only")
                break
    links = entry.get("links")
    if not isinstance(links, dict):
        errors.append("links must be a dict")
    else:
        missing_links = [key for key in REQUIRED_LINK_KEYS if key not in links]
        if missing_links:
            errors.append(f"links missing keys {missing_links}")
        latest = links.get("latest_version")
        if isinstance(latest, dict):
            href = latest.get("href")
            if not isinstance(href, str) or not href.strip():
                errors.append("links.latest_version.href must be a non-empty string")
        else:
            errors.append("links.latest_version must be an object")
    for field in OPTIONAL_LIST_FIELDS:
        value = entry.get(field)
        if value is None:
            continue
        if isinstance(value, list):
            if any(not isinstance(item, str) for item in value):
                errors.append(f"{field} must contain strings only")
        elif not isinstance(value, str):
            errors.append(f"{field} must be string or list of strings")
    return errors


def _validate_live_response(resp: dict[str, object]) -> list[str]:
    errors: list[str] = []
    missing = [field for field in ("id", "title", "description", "state", "links") if field not in resp]
    if missing:
        errors.append(f"missing fields {missing}")
        return errors
    dataset_id = resp.get("id")
    if not isinstance(dataset_id, str) or not dataset_id.strip():
        errors.append("id must be a non-empty string")
    for field in ("title", "description", "state"):
        value = resp.get(field)
        if value is not None and not isinstance(value, str):
            errors.append(f"{field} must be string or null")
    links = resp.get("links")
    if not isinstance(links, dict):
        errors.append("links must be a dict")
    else:
        missing_links = [key for key in REQUIRED_LINK_KEYS if key not in links]
        if missing_links:
            errors.append(f"links missing keys {missing_links}")
        latest = links.get("latest_version")
        if isinstance(latest, dict):
            href = latest.get("href")
            if not isinstance(href, str) or not href.strip():
                errors.append("links.latest_version.href must be a non-empty string")
        else:
            errors.append("links.latest_version must be an object")
    keywords = resp.get("keywords")
    if keywords is not None:
        if isinstance(keywords, list):
            if any(not isinstance(item, str) for item in keywords):
                errors.append("keywords must contain strings only")
        elif not isinstance(keywords, str):
            errors.append("keywords must be list or string")
    for field in OPTIONAL_LIST_FIELDS:
        value = resp.get(field)
        if value is None:
            continue
        if isinstance(value, list):
            if any(not isinstance(item, str) for item in value):
                errors.append(f"{field} must contain strings only")
        elif not isinstance(value, str):
            errors.append(f"{field} must be string or list of strings")
    return errors


def _validate_live_latest_version_response(resp: dict[str, object]) -> list[str]:
    errors: list[str] = []
    edition = resp.get("edition")
    version = resp.get("version")
    dims = resp.get("dimensions")
    if not isinstance(edition, str) or not edition.strip():
        errors.append("edition must be a non-empty string")
    if version is None:
        errors.append("version is missing")
    elif not isinstance(version, (str, int)):
        errors.append("version must be string or int")
    if not isinstance(dims, list) or not dims:
        errors.append("dimensions must be a non-empty list")
    else:
        for dim in dims:
            if not isinstance(dim, dict):
                errors.append("dimensions must contain objects only")
                break
            dim_id = dim.get("id") or dim.get("name")
            if not isinstance(dim_id, str) or not dim_id.strip():
                errors.append("dimensions entries must have id/name string")
                break
    return errors


def _resolve_catalog_path() -> Path:
    raw = getattr(settings, "ONS_CATALOG_PATH", "resources/ons_catalog.json")
    path = Path(raw)
    if not path.is_absolute():
        root = Path(__file__).resolve().parent.parent
        path = root / raw
    return path


def _load_catalog():
    path = _resolve_catalog_path()
    assert path.exists(), f"ONS catalog not found at {path}"
    data = json.loads(path.read_text(encoding="utf-8"))
    return data


def test_catalog_snapshot_structure():
    data = _load_catalog()
    assert data.get("placeholder") is False
    items = data.get("items")
    assert isinstance(items, list)
    assert len(items) >= 300
    ids = [item.get("id") for item in items if isinstance(item, dict)]
    assert all(ids)
    assert len(set(ids)) == len(ids)
    field_errors = []
    for entry in items:
        if not isinstance(entry, dict):
            field_errors.append("entry is not a dict")
            continue
        errors = _validate_entry_fields(entry)
        if errors:
            field_errors.append(f"{entry.get('id')}: {', '.join(errors)}")
    assert not field_errors, f"Catalog field validation failed: {field_errors[:10]}"


def test_catalog_snapshot_field_coverage():
    data = _load_catalog()
    items = data.get("items", [])
    titles = [item.get("title") for item in items if isinstance(item, dict)]
    descriptions = [item.get("description") for item in items if isinstance(item, dict)]
    title_ratio = sum(1 for t in titles if isinstance(t, str) and t.strip()) / max(len(titles), 1)
    desc_ratio = sum(1 for d in descriptions if isinstance(d, str) and d.strip()) / max(len(descriptions), 1)
    assert title_ratio >= 0.9
    assert desc_ratio >= 0.7


RUN_LIVE = os.getenv("RUN_LIVE_API_TESTS") == "1"
pytestmark_live = pytest.mark.skipif(not RUN_LIVE, reason="RUN_LIVE_API_TESTS=1 required")


@pytestmark_live
def test_catalog_covers_live_datasets():
    data = _load_catalog()
    catalog_ids = {
        item.get("id")
        for item in data.get("items", [])
        if isinstance(item, dict) and item.get("id")
    }
    client = ONSClient()
    base_api = getattr(settings, "ONS_DATASET_API_BASE", "https://api.beta.ons.gov.uk/v1")
    min_coverage = float(os.getenv("ONS_LIVE_COVERAGE_MIN", "0.99"))
    cooldown_seconds = float(os.getenv("ONS_LIVE_COOLDOWN_SECONDS", "10.0"))
    max_retries = int(os.getenv("ONS_LIVE_MAX_RETRIES", "6"))
    backoff_base = float(os.getenv("ONS_LIVE_BACKOFF_BASE", "5.0"))
    if cooldown_seconds > 0:
        time.sleep(cooldown_seconds)
    status = None
    items = None
    for attempt in range(1, max_retries + 1):
        status, items = client.get_all_pages(
            f"{base_api}/datasets",
            params={"limit": 1000, "page": 1},
        )
        if status == 200:
            break
        if status == 429:
            time.sleep(backoff_base * (2 ** (attempt - 1)))
            continue
        break
    assert status == 200
    live_ids = {
        item.get("id")
        for item in items
        if isinstance(item, dict) and item.get("id")
    }
    missing = live_ids - catalog_ids
    coverage = 1 - (len(missing) / max(len(live_ids), 1))
    assert (
        coverage >= min_coverage
    ), f"Catalog coverage {coverage:.2%} < {min_coverage:.2%}; missing {sorted(list(missing))[:25]}"


@pytestmark_live
def test_live_dataset_endpoints_resolve():
    data = _load_catalog()
    items = [item for item in data.get("items", []) if isinstance(item, dict) and item.get("id")]
    client = ONSClient()
    base_api = getattr(settings, "ONS_DATASET_API_BASE", "https://api.beta.ons.gov.uk/v1")
    throttle_seconds = float(os.getenv("ONS_LIVE_THROTTLE_SECONDS", "0.5"))
    max_retries = int(os.getenv("ONS_LIVE_MAX_RETRIES", "6"))
    backoff_base = float(os.getenv("ONS_LIVE_BACKOFF_BASE", "5.0"))
    errors: list[str] = []
    rate_limits = 0
    timeouts = 0
    other_errors = 0
    version_validations = 0
    for entry in items:
        dataset_id = entry.get("id")
        dataset_ok = False
        last_status = None
        last_resp = None
        latest_href = None
        for attempt in range(1, max_retries + 1):
            status, resp = client.get_json(
                f"{base_api}/datasets/{dataset_id}", params=None, use_cache=False
            )
            if status == 200:
                assert isinstance(resp, dict)
                assert resp.get("id") == dataset_id
                dataset_ok = True
                field_errors = _validate_live_response(resp)
                if field_errors:
                    errors.append(f"{dataset_id}: {', '.join(field_errors)}")
                links = resp.get("links")
                if isinstance(links, dict):
                    latest = links.get("latest_version")
                    if isinstance(latest, dict):
                        href = latest.get("href")
                        if isinstance(href, str) and href.strip():
                            latest_href = href
                last_status = None
                last_resp = None
                break
            last_status = status
            last_resp = resp
            if status == 429:
                rate_limits += 1
                time.sleep(backoff_base * (2 ** (attempt - 1)))
                continue
            if isinstance(resp, dict) and resp.get("code") == "UPSTREAM_CONNECT_ERROR":
                timeouts += 1
            else:
                other_errors += 1
            break
        if last_status is not None:
            errors.append(f"{dataset_id}: {last_status} ({last_resp})")

        if not dataset_ok:
            if throttle_seconds > 0:
                time.sleep(throttle_seconds)
            continue

        if latest_href and f"/datasets/{dataset_id}/" in latest_href:
            last_status = None
            last_resp = None
            for attempt in range(1, max_retries + 1):
                status, resp = client.get_json(latest_href, params=None, use_cache=False)
                if status == 200:
                    assert isinstance(resp, dict)
                    version_validations += 1
                    field_errors = _validate_live_latest_version_response(resp)
                    if field_errors:
                        errors.append(f"{dataset_id} latest_version: {', '.join(field_errors)}")
                    last_status = None
                    last_resp = None
                    break
                last_status = status
                last_resp = resp
                if status == 429:
                    rate_limits += 1
                    time.sleep(backoff_base * (2 ** (attempt - 1)))
                    continue
                if isinstance(resp, dict) and resp.get("code") == "UPSTREAM_CONNECT_ERROR":
                    timeouts += 1
                else:
                    other_errors += 1
                break
            if last_status is not None:
                errors.append(f"{dataset_id} latest_version: {last_status} ({last_resp})")
        elif latest_href:
            errors.append(f"{dataset_id} latest_version: href mismatch ({latest_href})")
        else:
            errors.append(f"{dataset_id} latest_version: missing href")

        if throttle_seconds > 0:
            time.sleep(throttle_seconds)
    print(
        "Live dataset check summary: "
        f"datasets={len(items)} version_validations={version_validations}/{len(items)} "
        f"rate_limits={rate_limits} timeouts={timeouts} other_errors={other_errors}"
    )
    if errors:
        pytest.fail(f"Live dataset validation errors: {errors[:10]}")
