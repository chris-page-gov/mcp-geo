import json

from server.config import settings


def _write_catalog(tmp_path, items):
    path = tmp_path / "ons_catalog.json"
    payload = {
        "generatedAt": "2026-02-07T00:00:00Z",
        "source": "test",
        "placeholder": False,
        "items": items,
    }
    path.write_text(json.dumps(payload))
    return path


def test_ons_select_missing_query(client):
    resp = client.post("/tools/call", json={"tool": "ons_select.search"})
    assert resp.status_code == 400
    data = resp.json()
    assert data["code"] == "INVALID_INPUT"


def test_ons_select_ranks_from_catalog(client, monkeypatch, tmp_path):
    catalog = _write_catalog(
        tmp_path,
        [
            {
                "id": "housing-affordability",
                "title": "Housing affordability index",
                "description": "Housing affordability for local areas.",
                "keywords": ["housing", "affordability"],
                "geography": {"levels": ["local_authority"]},
                "time": {"granularity": "year"},
                "state": "published",
            },
            {
                "id": "inflation-prices",
                "title": "Inflation and prices",
                "description": "Price indices over time.",
                "keywords": ["inflation", "prices"],
                "geography": {"levels": ["nation"]},
                "time": {"granularity": "month"},
                "state": "published",
            },
        ],
    )
    monkeypatch.setattr(settings, "ONS_CATALOG_PATH", str(catalog), raising=False)
    monkeypatch.setattr(settings, "ONS_SELECT_LIVE_ENABLED", False, raising=False)

    resp = client.post(
        "/tools/call",
        json={
            "tool": "ons_select.search",
            "query": "housing affordability",
            "geographyLevel": "local_authority",
            "timeGranularity": "year",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["candidates"][0]["datasetId"] == "housing-affordability"
    assert data["needsElicitation"] is False


def test_ons_select_returns_elicitation_questions(client, monkeypatch, tmp_path):
    catalog = _write_catalog(
        tmp_path,
        [
            {
                "id": "inflation-prices",
                "title": "Inflation and prices",
                "description": "Price indices over time.",
                "keywords": ["inflation", "prices"],
                "geography": {"levels": ["nation"]},
                "time": {"granularity": "month"},
                "state": "published",
            }
        ],
    )
    monkeypatch.setattr(settings, "ONS_CATALOG_PATH", str(catalog), raising=False)
    monkeypatch.setattr(settings, "ONS_SELECT_LIVE_ENABLED", False, raising=False)

    resp = client.post(
        "/tools/call",
        json={"tool": "ons_select.search", "query": "inflation"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["needsElicitation"] is True
    assert any("geography" in q.lower() for q in data["elicitationQuestions"])
    assert any("time" in q.lower() for q in data["elicitationQuestions"])


def test_ons_select_related_datasets_with_gating(client, monkeypatch, tmp_path):
    catalog = _write_catalog(
        tmp_path,
        [
            {
                "id": "housing-affordability",
                "title": "Housing affordability index",
                "description": "Housing affordability for local areas.",
                "keywords": ["housing", "affordability"],
                "geography": {"levels": ["local_authority"]},
                "time": {"granularity": "year"},
                "state": "published",
            },
            {
                "id": "housing-prices",
                "title": "Housing prices by local authority",
                "description": "House prices by local authority.",
                "keywords": ["housing", "prices"],
                "geography": {"levels": ["local_authority"]},
                "time": {"granularity": "year"},
                "state": "published",
            },
            {
                "id": "employment-rate",
                "title": "Employment rate",
                "description": "Employment for regions.",
                "keywords": ["employment"],
                "geography": {"levels": ["region"]},
                "time": {"granularity": "month"},
                "state": "published",
            },
        ],
    )
    monkeypatch.setattr(settings, "ONS_CATALOG_PATH", str(catalog), raising=False)
    monkeypatch.setattr(settings, "ONS_SELECT_LIVE_ENABLED", False, raising=False)

    resp = client.post(
        "/tools/call",
        json={
            "tool": "ons_select.search",
            "query": "housing affordability",
            "includeRelated": True,
            "relatedLimit": 5,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    related = data.get("relatedDatasets", [])
    assert any(item.get("datasetId") == "housing-prices" for item in related)
    assert all(item.get("datasetId") != "employment-rate" for item in related)


def test_ons_select_related_comparability_rules_and_explainability(client, monkeypatch, tmp_path):
    catalog = _write_catalog(
        tmp_path,
        [
            {
                "id": "housing-affordability",
                "title": "Housing affordability index",
                "description": "Housing affordability for local areas.",
                "keywords": ["housing", "affordability"],
                "intentTags": ["housing", "affordability"],
                "geography": {"levels": ["local_authority"]},
                "time": {"granularity": "year"},
                "comparability": {"denominator": "per_household"},
                "quality": {"revisionStatus": "published"},
                "releaseDate": "2025-06-01T00:00:00Z",
                "state": "published",
                "links": {"self": {"href": "https://example.test/housing-affordability"}},
            },
            {
                "id": "housing-prices",
                "title": "Housing prices by local authority",
                "description": "House prices and affordability context.",
                "keywords": ["housing", "prices"],
                "intentTags": ["housing"],
                "geography": {"levels": ["local_authority"]},
                "time": {"granularity": "year"},
                "comparability": {"denominator": "per_household"},
                "quality": {"revisionStatus": "published"},
                "releaseDate": "2025-05-01T00:00:00Z",
                "state": "published",
                "links": {"self": {"href": "https://example.test/housing-prices"}},
            },
            {
                "id": "housing-nowcast",
                "title": "Housing affordability nowcast",
                "description": "Provisional affordability estimate.",
                "keywords": ["housing", "affordability", "nowcast"],
                "intentTags": ["housing", "affordability"],
                "geography": {"levels": ["local_authority"]},
                "time": {"granularity": "year"},
                "comparability": {"denominator": "per_household"},
                "quality": {
                    "revisionStatus": "provisional",
                    "revisionNote": "Provisional estimate subject to revision.",
                },
                "releaseDate": "2025-07-01T00:00:00Z",
                "state": "published",
                "links": {"self": {"href": "https://example.test/housing-nowcast"}},
            },
            {
                "id": "housing-regional",
                "title": "Housing affordability by region",
                "description": "Regional view of affordability.",
                "keywords": ["housing", "affordability", "region"],
                "intentTags": ["housing", "affordability"],
                "geography": {"levels": ["region"]},
                "time": {"granularity": "year"},
                "comparability": {"denominator": "per_household"},
                "quality": {"revisionStatus": "published"},
                "state": "published",
                "links": {"self": {"href": "https://example.test/housing-regional"}},
            },
            {
                "id": "housing-monthly",
                "title": "Housing affordability monthly tracker",
                "description": "Monthly signal for affordability.",
                "keywords": ["housing", "affordability", "monthly"],
                "intentTags": ["housing", "affordability"],
                "geography": {"levels": ["local_authority"]},
                "time": {"granularity": "month"},
                "comparability": {"denominator": "per_household"},
                "quality": {"revisionStatus": "published"},
                "state": "published",
                "links": {"self": {"href": "https://example.test/housing-monthly"}},
            },
            {
                "id": "housing-per-person",
                "title": "Housing affordability per person",
                "description": "Affordability denominator differs.",
                "keywords": ["housing", "affordability"],
                "intentTags": ["housing", "affordability"],
                "geography": {"levels": ["local_authority"]},
                "time": {"granularity": "year"},
                "comparability": {"denominator": "per_person"},
                "quality": {"revisionStatus": "published"},
                "state": "published",
                "links": {"self": {"href": "https://example.test/housing-per-person"}},
            },
            {
                "id": "housing-revision-mismatch",
                "title": "Housing affordability provisional mismatch",
                "description": "Provisional without note should be rejected.",
                "keywords": ["housing", "affordability"],
                "intentTags": ["housing", "affordability"],
                "geography": {"levels": ["local_authority"]},
                "time": {"granularity": "year"},
                "comparability": {"denominator": "per_household"},
                "quality": {"revisionStatus": "provisional"},
                "state": "published",
                "links": {"self": {"href": "https://example.test/housing-revision-mismatch"}},
            },
        ],
    )
    monkeypatch.setattr(settings, "ONS_CATALOG_PATH", str(catalog), raising=False)
    monkeypatch.setattr(settings, "ONS_SELECT_LIVE_ENABLED", False, raising=False)

    resp = client.post(
        "/tools/call",
        json={"tool": "ons_select.search", "query": "housing affordability index", "includeRelated": True},
    )
    assert resp.status_code == 200
    data = resp.json()
    related = data.get("relatedDatasets", [])
    ids = {item.get("datasetId") for item in related}
    assert "housing-prices" in ids
    assert "housing-nowcast" in ids
    assert "housing-regional" not in ids
    assert "housing-monthly" not in ids
    assert "housing-per-person" not in ids
    assert "housing-revision-mismatch" not in ids

    for item in related:
        assert item.get("linkType")
        assert isinstance(item.get("linkReason"), str)
        assert "provenance" in item
        assert "warnings" in item
        assert "comparability" in item

    nowcast = next((item for item in related if item.get("datasetId") == "housing-nowcast"), None)
    assert nowcast is not None
    assert nowcast.get("linkType") == "quality_or_revision_context"
    assert any("Revision mismatch" in warning for warning in nowcast.get("warnings", []))


def test_ons_select_catalog_missing_returns_error(client, monkeypatch, tmp_path):
    missing = tmp_path / "missing.json"
    monkeypatch.setattr(settings, "ONS_CATALOG_PATH", str(missing), raising=False)
    monkeypatch.setattr(settings, "ONS_SELECT_LIVE_ENABLED", False, raising=False)

    resp = client.post(
        "/tools/call",
        json={"tool": "ons_select.search", "query": "inflation"},
    )
    assert resp.status_code == 501
    data = resp.json()
    assert data["code"] == "CATALOG_NOT_FOUND"
