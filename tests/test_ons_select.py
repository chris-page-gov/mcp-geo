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
