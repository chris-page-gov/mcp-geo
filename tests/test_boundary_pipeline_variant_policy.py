from __future__ import annotations

from scripts import boundary_pipeline as pipeline


def test_family_variant_policy_merges_manifest_defaults() -> None:
    manifest = {
        "completion_definition": {
            "require_full_variant_availability": True,
            "required_variants": ["BFC", "BFE", "BGC", "BUC"],
            "allowed_optional_variants": ["BSC"],
            "default_variant_policy": {
                "equivalent_variants": {"BUC": ["BSC"]},
                "derivation": {
                    "enabled": True,
                    "source_priority": ["BFC"],
                    "target_profiles": {
                        "BUC": {
                            "method": "simplify_preserve_topology",
                            "simplify_tolerance": 500.0,
                        }
                    },
                },
                "variant_detection": {
                    "from_title_regex": r"\b(BFC|BSC)\b",
                    "fallback": "BFC",
                },
            },
        }
    }
    template = {
        "variant_policy": {
            "derivation": {
                "source_priority": ["BFC", "BGG"],
                "target_profiles": {"BGC": {"simplify_tolerance": 20.0}},
            }
        }
    }
    family = {
        "variant_policy": {
            "equivalent_variants": {"BGC": ["BGG"]},
            "require_full_variant_availability": False,
        }
    }

    policy = pipeline._family_variant_policy(family, template, manifest)

    assert policy["required_variants"] == ["BFC", "BFE", "BGC", "BUC"]
    assert policy["equivalent_variants"]["BUC"] == ["BSC"]
    assert policy["equivalent_variants"]["BGC"] == ["BGG"]
    assert policy["derivation"]["enabled"] is True
    assert policy["derivation"]["source_priority"] == ["BFC", "BGG"]
    assert policy["derivation"]["target_profiles"]["BUC"]["simplify_tolerance"] == 500.0
    assert policy["derivation"]["target_profiles"]["BGC"]["simplify_tolerance"] == 20.0
    assert policy["variant_detection_regex"] == r"\b(BFC|BSC)\b"
    assert policy["variant_detection_fallback"] == "BFC"
    assert policy["require_full_variant_availability"] is False


def test_resolve_required_variants_supports_equivalent_and_derived(tmp_path) -> None:
    paths = pipeline._ensure_paths(tmp_path)
    family = {"family_id": "example_family"}
    policy = {
        "required_variants": ["BFC", "BUC", "BGC", "BFE"],
        "equivalent_variants": {"BUC": ["BSC"]},
        "derivation": {
            "enabled": True,
            "source_priority": ["BFC"],
            "target_profiles": {
                "BGC": {
                    "method": "simplify_preserve_topology",
                    "simplify_tolerance": 20.0,
                    "accuracy_class": "derived_generalised",
                }
            },
        },
    }
    published_candidates = {
        "BFC": {
            "status": "resolved",
            "download_url": "https://example.com/bfc.gpkg",
            "source_id": "demo",
        },
        "BSC": {
            "status": "resolved",
            "download_url": "https://example.com/bsc.gpkg",
            "source_id": "demo",
        },
    }

    resolved = pipeline._resolve_required_variants(
        family=family,
        policy=policy,
        paths=paths,
        published_candidates=published_candidates,
        missing_reason="variant_not_listed_in_manifest_downloads",
    )

    assert resolved["BFC"]["status"] == "resolved"
    assert resolved["BFC"]["availability"] == "published"
    assert resolved["BUC"]["status"] == "resolved"
    assert resolved["BUC"]["availability"] == "equivalent_variant"
    assert resolved["BUC"]["source_variant"] == "BSC"
    assert resolved["BUC"]["accuracy_class"] == "published_equivalent_variant"
    assert resolved["BGC"]["status"] == "derived"
    assert resolved["BGC"]["source_variant"] == "BFC"
    assert resolved["BGC"]["derivation"]["simplify_tolerance"] == 20.0
    assert resolved["BFE"]["status"] == "derived"
    assert resolved["BFE"]["derivation"]["method"] == "copy"
    assert (paths.root / resolved["BUC"]["published_variant_evidence_ref"]).exists()
    assert (paths.root / resolved["BGC"]["published_variant_evidence_ref"]).exists()
    assert (paths.root / resolved["BFE"]["published_variant_evidence_ref"]).exists()


def test_resolve_required_variants_marks_coarser_source_derivation(tmp_path) -> None:
    paths = pipeline._ensure_paths(tmp_path)
    family = {"family_id": "coarse_source_family"}
    policy = {
        "required_variants": ["BFC"],
        "equivalent_variants": {},
        "derivation": {
            "enabled": True,
            "source_priority": ["BGG"],
            "target_profiles": {},
        },
    }
    published_candidates = {
        "BGG": {
            "status": "resolved",
            "download_url": "https://example.com/bgg.gpkg",
            "source_id": "demo",
        }
    }

    resolved = pipeline._resolve_required_variants(
        family=family,
        policy=policy,
        paths=paths,
        published_candidates=published_candidates,
        missing_reason="no_ckan_resource_match",
    )

    assert resolved["BFC"]["status"] == "derived"
    assert resolved["BFC"]["source_variant"] == "BGG"
    assert resolved["BFC"]["derivation"]["accuracy_class"] == "derived_from_coarser_source"
    assert resolved["BFC"]["derivation"]["source_resolution_rank"] > resolved["BFC"]["derivation"][
        "target_resolution_rank"
    ]


def test_evaluate_pipeline_fails_not_published_when_full_availability_required() -> None:
    manifest = {
        "completion_definition": {
            "require_full_variant_availability": True,
            "required_variants": ["BFC", "BUC"],
            "allowed_optional_variants": [],
        },
        "templates": {
            "default": {
                "variant_policy": {
                    "required_variants": ["BFC", "BUC"],
                    "optional_variants": [],
                }
            }
        },
        "boundary_families": [{"family_id": "fam", "template": "default"}],
    }
    checklist = {
        "final_status_values": {
            "pass": "COMPLETE_BOUNDARIES_INGESTED_AND_VALIDATED",
            "fail": "INCOMPLETE_BOUNDARIES_INGEST_OR_VALIDATION_FAILED",
        }
    }
    report = {
        "resolved_resources": {
            "fam": {
                "BFC": {"status": "resolved", "download_url": "https://example.com/bfc.gpkg"},
                "BUC": {"status": "not_published", "evidence_ref": "evidence.json"},
            }
        },
        "downloads": {"fam": {}},
        "ingestions": {"fam": {}},
        "validations": {"fam": {}},
        "exceptions": [],
        "source_verification": {"fam": {}},
        "family_status": {},
    }

    pipeline._evaluate_pipeline(
        report,
        manifest,
        checklist,
        mode="resolve",
        require_source_verification=False,
    )

    assert report["pipeline_status"] == "INCOMPLETE_BOUNDARIES_SOURCE_RESOLUTION_FAILED"
    assert report["errors"]
    assert "required_variant_unavailable:BUC" in report["errors"][0]["errors"]


def test_evaluate_pipeline_accepts_derived_variants_in_resolve_verify_mode() -> None:
    manifest = {
        "completion_definition": {
            "require_full_variant_availability": True,
            "required_variants": ["BFC", "BUC"],
            "allowed_optional_variants": [],
        },
        "templates": {
            "default": {
                "variant_policy": {
                    "required_variants": ["BFC", "BUC"],
                    "optional_variants": [],
                }
            }
        },
        "boundary_families": [{"family_id": "fam", "template": "default"}],
    }
    checklist = {
        "final_status_values": {
            "pass": "COMPLETE_BOUNDARIES_INGESTED_AND_VALIDATED",
            "fail": "INCOMPLETE_BOUNDARIES_INGEST_OR_VALIDATION_FAILED",
        }
    }
    report = {
        "resolved_resources": {
            "fam": {
                "BFC": {"status": "resolved", "download_url": "https://example.com/bfc.gpkg"},
                "BUC": {
                    "status": "derived",
                    "download_url": "https://example.com/bfc.gpkg",
                    "source_variant": "BFC",
                    "derivation": {"method": "simplify_preserve_topology"},
                },
            }
        },
        "downloads": {"fam": {}},
        "ingestions": {"fam": {}},
        "validations": {"fam": {}},
        "exceptions": [],
        "source_verification": {
            "fam": {
                "BFC": {"status": "ok", "verified": True},
                "BUC": {"status": "ok", "verified": True},
            }
        },
        "family_status": {},
    }

    pipeline._evaluate_pipeline(
        report,
        manifest,
        checklist,
        mode="resolve",
        require_source_verification=True,
    )

    assert report["pipeline_status"] == "COMPLETE_BOUNDARIES_RESOLVED_AND_VERIFIED"
    assert report["errors"] == []
