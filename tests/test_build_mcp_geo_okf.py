from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts import build_mcp_geo_okf as builder
from tools.registry import all_tools


def _record_map(payloads: dict[str, object]) -> dict[str, dict[str, object]]:
    records_payload = payloads["records.json"]
    assert isinstance(records_payload, list)
    return {str(record["id"]): record for record in records_payload}


def test_build_inventory_matches_runtime_and_checked_in_catalog() -> None:
    payloads = builder.build_payloads()
    overview = payloads["overview.json"]
    assert isinstance(overview, dict)
    counts = overview["counts"]
    assert isinstance(counts, dict)

    expected_resources = builder.stable_resource_inventory()
    catalog = json.loads((builder.REPO_ROOT / "resources" / "os_catalog.json").read_text())

    assert counts["mcp_tools"] == len(all_tools())
    assert counts["mcp_resources"] == len(expected_resources)
    assert counts["os_catalog_entries"] == len(catalog["items"])
    assert counts["records"] == sum(
        (counts["mcp_tools"], counts["mcp_resources"], counts["os_catalog_entries"])
    )

    records = _record_map(payloads)
    assert {f"tool:{tool.name}" for tool in all_tools()} <= records.keys()
    assert {f"resource:{resource['uri']}" for resource in expected_resources} <= records.keys()
    assert {f"os-catalog:{item['id']}" for item in catalog["items"]} <= records.keys()
    assert len(records) == counts["records"]
    assert all(isinstance(record.get("name"), str) for record in records.values())


def test_featured_families_have_spatial_profiles_and_read_only_bindings() -> None:
    payloads = builder.build_payloads()
    spatial = payloads["spatial-index.json"]
    bindings_payload = payloads["mcp-bindings.json"]
    assert isinstance(spatial, dict)
    assert isinstance(bindings_payload, dict)
    assert spatial["schema"] == "okf-geospatial.v1"
    assert bindings_payload["schema"] == "okf-mcp-binding.v1"

    expected_tools = {
        tool.name
        for tool in all_tools()
        if tool.name.split(".", 1)[0] in builder.FEATURED_FAMILIES
    }
    profiles = spatial["records"]
    bindings = bindings_payload["bindings"]
    assert isinstance(profiles, list)
    assert isinstance(bindings, list)
    tool_profiles = [
        profile for profile in profiles if str(profile["record_id"]).startswith("tool:")
    ]
    assert {str(profile["record_id"]).removeprefix("tool:") for profile in tool_profiles} == (
        expected_tools
    )
    assert {str(binding["tool_name"]) for binding in bindings} == expected_tools
    assert all(binding["read_only"] is True for binding in bindings)
    assert all(binding["credential_mode"] == "server-managed" for binding in bindings)
    assert all(binding["security"]["secret_values_stored"] is False for binding in bindings)
    assert all(binding["request_template"]["id"] == 1 for binding in bindings)

    profile_by_id = {str(profile["record_id"]): profile for profile in profiles}
    assert profile_by_id["tool:os_places.within"]["filter_inputs"] == ["bbox"]
    assert profile_by_id["tool:os_features.query"]["filter_inputs"] == ["bbox", "polygon"]
    assert profile_by_id["tool:os_linked_ids.get"]["spatially_filterable"] is False
    assert (
        profile_by_id["tool:os_features.collections"]["operation_contract"]["geometry_output"]
        == "not-declared-by-operation-schema"
    )
    assert (
        profile_by_id["tool:os_features.query"]["operation_contract"]["geometry_output"]
        == "optional-via-includeGeometry"
    )
    assert (
        profile_by_id["tool:os_features.query"]["metadata_scope"]["coverage"]
        == "underlying-family-data-capability"
    )
    catalog_profile = profile_by_id[
        "os-catalog:os.features.ngd.collection.bld-fts-building-1.items"
    ]
    assert catalog_profile["operation_contract"]["geometry_output"] == (
        "feature-collection-endpoint"
    )
    assert catalog_profile["map_representation"]["role"] == "demo-query-anchor"
    demo_location = spatial["demo_locations"][0]
    assert demo_location["bbox_role"] == "demonstrator-query-window"
    assert "not an OS site or property boundary" in demo_location["caveat"]


def test_places_uprn_flows_into_follow_up_bindings_without_claiming_a_demo_uprn() -> None:
    payload = builder.build_payloads()["mcp-bindings.json"]
    assert isinstance(payload, dict)
    bindings = payload["bindings"]
    assert isinstance(bindings, list)
    by_tool = {str(binding["tool_name"]): binding for binding in bindings}

    for tool_name in (
        "os_places.by_uprn",
        "os_linked_ids.get",
        "os_linked_ids.identifiers",
    ):
        binding = by_tool[tool_name]
        arguments = binding["example_arguments"]
        value = arguments.get("uprn", arguments.get("identifier"))
        assert value == "<UPRN_FROM_PLACES_RESULT>"
        assert binding["argument_flow"]["source_binding"] == "binding:os_places.by_postcode"

    feature_type_binding = by_tool["os_linked_ids.feature_types"]
    assert feature_type_binding["example_arguments"] == {
        "featureType": "RoadLink",
        "identifier": "osgb5000005158744708",
    }
    assert "argument_flow" not in feature_type_binding
    assert "not asserted to relate to Explorer House" in feature_type_binding["example_context"]
    assert by_tool["os_linked_ids.product_version_info"]["example_arguments"] == {
        "correlationMethod": "BLPU_UPRN_RoadLink_TOID_9"
    }


def test_descriptor_uses_string_entrypoints_with_verifiable_integrity() -> None:
    payloads = builder.build_payloads()
    descriptor = payloads["descriptor.json"]
    assert isinstance(descriptor, dict)
    assert descriptor["schema"] == "okf-explorer-large-corpus.v1"
    assert descriptor["kind"] == "okf-large-corpus"
    entrypoints = descriptor["entrypoints"]
    integrity = descriptor["entrypoint_integrity"]
    assert isinstance(entrypoints, dict)
    assert isinstance(integrity, dict)
    assert all(isinstance(path, str) for path in entrypoints.values())

    for key, path in entrypoints.items():
        reference = integrity[key]
        assert reference["path"] == path
        rendered = builder._json_text(payloads[path])
        assert reference["sha256"] == hashlib.sha256(rendered.encode()).hexdigest()

    assert descriptor["extensions"]["okf-geospatial.v1"] == {
        "entrypoint": "spatial_index",
        "mode": "external",
    }
    assert descriptor["extensions"]["okf-mcp-binding.v1"] == {
        "entrypoint": "mcp_bindings",
        "mode": "external",
    }

    manifest = payloads["manifest.json"]
    assert isinstance(manifest, dict)
    assert manifest["indexes"]["overview"] == "overview.json"
    assert manifest["chunks"]["datasets"] == ["records.json"]
    assert manifest["chunks"]["publishers"] == []


def test_descriptor_delivery_map_keeps_portable_paths_and_resolves_live_transports() -> None:
    descriptor = builder.build_payloads()["descriptor.json"]
    assert isinstance(descriptor, dict)
    entrypoints = descriptor["entrypoints"]
    delivery = descriptor["delivery"]
    assert isinstance(entrypoints, dict)
    assert delivery["schema"] == "okf-delivery-map.v1"
    assert set(delivery["artifacts"]) == set(builder.DELIVERY_FILES)

    for key, filename in builder.DELIVERY_FILES.items():
        artifact = delivery["artifacts"][key]
        assert artifact == {
            "path": filename,
            "mcp_resource_uri": f"resource://mcp-geo/okf-discovery-{Path(filename).stem}",
            "http_path": f"/okf-discovery/data/{filename}",
        }
        if key != "descriptor":
            assert entrypoints[key] == filename

    assert "descriptor" not in entrypoints
    assert "descriptor" not in descriptor["entrypoint_integrity"]


def test_generator_writes_checks_and_detects_drift(tmp_path: Path, capsys) -> None:
    assert builder.write_or_check(tmp_path, check=False) == 0
    first = {path.name: path.read_bytes() for path in tmp_path.iterdir()}
    assert builder.write_or_check(tmp_path, check=False) == 0
    second = {path.name: path.read_bytes() for path in tmp_path.iterdir()}
    assert first == second
    assert builder.write_or_check(tmp_path, check=True) == 0

    records_path = tmp_path / "records.json"
    records_path.write_text("{}\n", encoding="utf-8")
    assert builder.write_or_check(tmp_path, check=True) == 1
    assert "out of date" in capsys.readouterr().err


def test_self_resources_are_excluded_to_avoid_circular_pack_drift(monkeypatch) -> None:
    monkeypatch.setattr(
        builder,
        "_build_resource_list",
        lambda: [
            {
                "uri": "resource://mcp-geo/os-catalog",
                "name": "data_os_catalog",
                "title": "OS API Catalog",
                "description": "Stable packaged resource",
                "mimeType": "application/json",
                "type": "data",
            },
            {
                "uri": "resource://mcp-geo/okf-discovery-records",
                "name": "okf_discovery_records",
                "title": "Generated OKF records",
                "description": "The pack cannot inventory itself.",
                "mimeType": "application/json",
                "type": "data",
            },
        ],
    )

    payloads = builder.build_payloads()
    records = _record_map(payloads)
    assert "resource:resource://mcp-geo/os-catalog" in records
    assert "resource:resource://mcp-geo/okf-discovery-records" not in records
    overview = payloads["overview.json"]
    assert isinstance(overview, dict)
    assert overview["counts"]["mcp_resources"] == 1


def test_ephemeral_local_resources_do_not_change_the_pack(monkeypatch) -> None:
    base_resources = [
        {
            "uri": "resource://mcp-geo/os-catalog",
            "name": "data_os_catalog",
            "title": "OS API Catalog",
            "description": "Stable packaged resource",
            "mimeType": "application/json",
            "type": "data",
        }
    ]
    ephemeral = [
        {
            "uri": "resource://mcp-geo/ons-cache/local-only.json",
            "name": "local_only",
            "title": "Local cache",
            "description": "Environment-specific resource",
            "mimeType": "application/json",
            "type": "data",
        },
        {
            "uri": "resource://mcp-geo/boundary-latest-report",
            "name": "latest_report",
            "title": "Latest local report",
            "description": "Environment-specific report",
            "mimeType": "application/json",
            "type": "data",
        },
    ]
    monkeypatch.setattr(builder, "_build_resource_list", lambda: base_resources)
    baseline = builder.build_payloads()
    monkeypatch.setattr(builder, "_build_resource_list", lambda: base_resources + ephemeral)
    with_ephemeral = builder.build_payloads()
    assert baseline == with_ephemeral
