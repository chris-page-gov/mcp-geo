import json
from pathlib import Path

from tools.ons_catalog_validator import validate_catalog_file, validate_catalog_payload


def _valid_catalog_payload() -> dict:
    return {
        "generatedAt": "2026-02-11T00:00:00Z",
        "source": "test",
        "placeholder": False,
        "items": [
            {
                "id": "housing-affordability",
                "title": "Housing affordability index",
                "description": "Affordability by area.",
                "keywords": ["housing", "affordability"],
                "state": "published",
                "links": {
                    "editions": {"href": "https://example.test/editions"},
                    "latest_version": {"href": "https://example.test/version/1"},
                    "self": {"href": "https://example.test/datasets/housing-affordability"},
                },
                "geography": {"levels": ["local_authority"]},
                "time": {"granularity": "year", "alignableTo": ["quarter"]},
                "comparability": {"denominator": "per_household"},
                "quality": {"revisionStatus": "published"},
            }
        ],
    }


def test_validate_catalog_payload_accepts_valid_shape():
    payload = _valid_catalog_payload()
    errors = validate_catalog_payload(payload, min_items=1)
    assert errors == []


def test_validate_catalog_payload_rejects_missing_required_fields():
    payload = _valid_catalog_payload()
    payload["items"][0].pop("links")
    errors = validate_catalog_payload(payload, min_items=1)
    assert any("missing fields" in error for error in errors)


def test_validate_catalog_payload_rejects_invalid_comparability():
    payload = _valid_catalog_payload()
    payload["items"][0]["comparability"] = {"denominator": 123, "timeTransforms": "year->month"}
    errors = validate_catalog_payload(payload, min_items=1)
    assert any("comparability.denominator must be a string" in error for error in errors)
    assert any("comparability.timeTransforms must be a list of strings" in error for error in errors)


def test_validate_catalog_file_invalid_json(tmp_path: Path):
    path = tmp_path / "ons_catalog.json"
    path.write_text("{bad json", encoding="utf-8")
    payload, errors = validate_catalog_file(path, min_items=1)
    assert payload is None
    assert errors
    assert "invalid JSON" in errors[0]


def test_validate_catalog_file_end_to_end(tmp_path: Path):
    path = tmp_path / "ons_catalog.json"
    payload = _valid_catalog_payload()
    path.write_text(json.dumps(payload), encoding="utf-8")
    loaded, errors = validate_catalog_file(path, min_items=1)
    assert errors == []
    assert loaded is not None
    assert loaded["items"][0]["id"] == "housing-affordability"
