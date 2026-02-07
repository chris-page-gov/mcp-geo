import json
import os
from pathlib import Path

import pytest

from server.config import settings
from tools.ons_common import ONSClient


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
    status, items = client.get_all_pages(f"{base_api}/datasets", params={"limit": 1000, "page": 1})
    assert status == 200
    live_ids = {
        item.get("id")
        for item in items
        if isinstance(item, dict) and item.get("id")
    }
    missing = live_ids - catalog_ids
    coverage = 1 - (len(missing) / max(len(live_ids), 1))
    assert coverage >= 0.95, f"Catalog coverage {coverage:.2%}; missing {sorted(list(missing))[:10]}"


@pytestmark_live
def test_live_dataset_endpoints_resolve():
    data = _load_catalog()
    items = [item for item in data.get("items", []) if isinstance(item, dict) and item.get("id")]
    sample = items[:5]
    client = ONSClient()
    base_api = getattr(settings, "ONS_DATASET_API_BASE", "https://api.beta.ons.gov.uk/v1")
    for entry in sample:
        dataset_id = entry.get("id")
        status, resp = client.get_json(f"{base_api}/datasets/{dataset_id}", params=None)
        assert status == 200, f"Dataset {dataset_id} returned {status}"
        assert isinstance(resp, dict)
        assert resp.get("id") == dataset_id
