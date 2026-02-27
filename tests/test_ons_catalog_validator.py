import json
from pathlib import Path

from tools.ons_catalog_validator import (
    validate_catalog_file,
    validate_catalog_payload,
    validate_entry_fields,
)


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


def test_validate_entry_fields_reports_optional_metadata_errors():
    entry = {
        "id": "dataset-1",
        "title": "Dataset",
        "description": "Description",
        "keywords": ["keyword"],
        "state": "published",
        "links": {
            "editions": {"href": "https://example.test/editions"},
            "latest_version": {"href": ""},
            "self": {"href": "https://example.test/datasets/dataset-1"},
        },
        "themes": [1],
        "topics": 123,
        "geography": {"levels": "not-a-list"},
        "time": {"granularity": 1, "alignableTo": "year"},
        "comparability": {
            "denominator": 7,
            "timeTransforms": [1, 2],
            "geographyMapping": 123,
        },
        "quality": {"revisionStatus": 99, "revisionNote": 101},
        "releaseDate": 20260101,
        "last_updated": 20260101,
    }
    errors = validate_entry_fields(entry)
    assert "links.latest_version.href must be a non-empty string" in errors
    assert "themes must contain strings only" in errors
    assert "topics must be string or list of strings" in errors
    assert "geography.levels must be a list of strings" in errors
    assert "time.granularity must be a string" in errors
    assert "time.alignableTo must be a list of strings" in errors
    assert "comparability.denominator must be a string" in errors
    assert "comparability.timeTransforms must be a list of strings" in errors
    assert "comparability.geographyMapping must be dict/list/string" in errors
    assert "quality.revisionStatus must be a string" in errors
    assert "quality.revisionNote must be a string" in errors
    assert "releaseDate must be a string" in errors
    assert "last_updated must be a string" in errors


def test_validate_catalog_payload_reports_top_level_and_duplicate_errors():
    payload = {
        "placeholder": "no",
        "generatedAt": 123,
        "source": 456,
        "items": [
            {
                "id": "dup",
                "title": "A",
                "description": "A",
                "keywords": ["x"],
                "state": "published",
                "links": {
                    "editions": {"href": "https://example.test/editions"},
                    "latest_version": {"href": "https://example.test/version/1"},
                    "self": {"href": "https://example.test/datasets/dup"},
                },
            },
            {
                "id": "dup",
                "title": "B",
                "description": "B",
                "keywords": ["y"],
                "state": "published",
                "links": {
                    "editions": {"href": "https://example.test/editions"},
                    "latest_version": {"href": "https://example.test/version/1"},
                    "self": {"href": "https://example.test/datasets/dup"},
                },
            },
            "invalid-item",
        ],
    }
    errors = validate_catalog_payload(payload, min_items=4)
    assert "placeholder must be boolean" in errors
    assert "generatedAt must be a string" in errors
    assert "source must be a string" in errors
    assert "items must contain at least 4 entries" in errors
    assert "duplicate dataset id 'dup'" in errors
    assert "items[2] must be an object" in errors


def test_validate_catalog_file_missing_path_and_non_object_root(tmp_path: Path):
    missing_path = tmp_path / "missing.json"
    payload, errors = validate_catalog_file(missing_path)
    assert payload is None
    assert errors and "catalog file not found" in errors[0]

    list_root_path = tmp_path / "list_root.json"
    list_root_path.write_text(json.dumps([{"id": "x"}]), encoding="utf-8")
    payload, errors = validate_catalog_file(list_root_path)
    assert payload is None
    assert errors == ["catalog root must be an object"]
