#!/usr/bin/env python3
"""Build a deterministic OKF discovery pack from the live MCP Geo registries.

The pack deliberately separates three concerns:

* ``records.json`` is the portable discovery inventory;
* ``spatial-index.json`` adds geospatial discovery semantics; and
* ``mcp-bindings.json`` describes how selected records become MCP calls.

No network calls, credentials, or build timestamps are used. Run with ``--check``
to detect drift between the checked-in pack and the current registries.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "resources" / "okf_geo_discovery"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Importing the HTTP tool surface performs the same explicit registration used by
# the running server. Keep registry access separate so the source of the inventory
# remains clear.
import server.mcp.tools  # noqa: E402,F401
from server.mcp.resource_catalog import DATA_RESOURCE_DEFS  # noqa: E402
from server.mcp.resources import _build_resource_list  # noqa: E402
from tools.registry import Tool, all_tools  # noqa: E402

PACK_VERSION = "0.1.0"
SNAPSHOT_AT = "2026-07-15T00:00:00Z"
FEATURED_FAMILIES = ("os_places", "os_features", "os_linked_ids")
SELF_RESOURCE_PREFIX = "resource://mcp-geo/okf-discovery-"
PACKAGED_RESOURCE_ROOT = (REPO_ROOT / "resources").resolve()
EXPLORER_HOUSE_POINT = [-1.470433, 50.937708]
EXPLORER_HOUSE_BBOX = [-1.48, 50.93, -1.46, 50.945]

OPTIONAL_RESOURCE_FAMILIES = [
    "resource://mcp-geo/exports/{filename}",
    "resource://mcp-geo/map-scenario-packs/{filename}",
    "resource://mcp-geo/offline-packs/{filename}",
    "resource://mcp-geo/ons-cache/{filename}",
    "resource://mcp-geo/ons-exports/{filename}",
    "resource://mcp-geo/os-cache/{filename}",
    "resource://mcp-geo/os-exports/{filename}",
]

DELIVERY_FILES = {
    "descriptor": "descriptor.json",
    "data_manifest": "manifest.json",
    "overview_index": "overview.json",
    "records": "records.json",
    "spatial_index": "spatial-index.json",
    "mcp_bindings": "mcp-bindings.json",
}


FAMILY_PROFILES: dict[str, dict[str, Any]] = {
    "os_places": {
        "title": "OS Places: addresses, postcodes and UPRNs",
        "coverage": {"type": "named", "label": "Great Britain"},
        "query_crs": ["OGC:CRS84"],
        "response_crs": ["OGC:CRS84"],
        "geometry_types": ["Point"],
        "identifiers": ["UPRN", "postcode"],
        "discovery_modes": [
            "address-text",
            "postcode",
            "UPRN",
            "nearest-point",
            "radius",
            "bbox",
            "polygon",
        ],
        "source": "https://osdatahub.os.uk/docs/places/overview",
    },
    "os_features": {
        "title": "OS NGD API: feature collections and geometry",
        "coverage": {"type": "named", "label": "Great Britain"},
        "query_crs": ["OGC:CRS84"],
        "response_crs": ["OGC:CRS84"],
        "geometry_types": ["Point", "LineString", "Polygon"],
        "identifiers": ["TOID", "feature identifier"],
        "discovery_modes": [
            "collection",
            "bbox",
            "polygon",
            "attribute-filter",
            "queryables",
        ],
        "source": "https://osdatahub.os.uk/docs/ofa/overview",
    },
    "os_linked_ids": {
        "title": "OS Linked Identifiers: joins across products",
        "coverage": {"type": "named", "label": "Great Britain"},
        "query_crs": [],
        "response_crs": [],
        "geometry_types": [],
        "identifiers": ["UPRN", "USRN", "TOID"],
        "discovery_modes": ["identifier", "identifier-type", "feature-type"],
        "source": "https://osdatahub.os.uk/docs/linkedIdentifiers/overview",
    },
}


EXAMPLE_ARGUMENTS: dict[str, dict[str, Any]] = {
    "os_places.by_postcode": {"postcode": "SO16 0AS"},
    "os_places.by_uprn": {"uprn": "<UPRN_FROM_PLACES_RESULT>"},
    "os_places.nearest": {"lat": 50.937708, "lon": -1.470433},
    "os_places.polygon": {
        "polygon": {
            "type": "Polygon",
            "coordinates": [[
                [-1.48, 50.93],
                [-1.46, 50.93],
                [-1.46, 50.945],
                [-1.48, 50.945],
                [-1.48, 50.93],
            ]],
        },
        "limit": 20,
    },
    "os_places.radius": {
        "lat": 50.937708,
        "lon": -1.470433,
        "radiusMeters": 500,
        "limit": 20,
    },
    "os_places.search": {"text": "Explorer House Southampton", "limit": 20},
    "os_places.within": {"bbox": EXPLORER_HOUSE_BBOX},
    "os_features.collections": {"q": "building"},
    "os_features.query": {
        "collection": "buildings",
        "bbox": EXPLORER_HOUSE_BBOX,
        "includeGeometry": True,
        "limit": 20,
    },
    "os_features.wfs_archive_capabilities": {"version": "2.0.0"},
    "os_features.wfs_capabilities": {"version": "2.0.0"},
    "os_linked_ids.feature_types": {
        "featureType": "RoadLink",
        "identifier": "osgb5000005158744708",
    },
    "os_linked_ids.get": {
        "identifier": "<UPRN_FROM_PLACES_RESULT>",
        "identifierType": "uprn",
    },
    "os_linked_ids.identifiers": {"identifier": "<UPRN_FROM_PLACES_RESULT>"},
    "os_linked_ids.product_version_info": {
        "correlationMethod": "BLPU_UPRN_RoadLink_TOID_9"
    },
}


def _json_text(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _family_for_tool(name: str) -> str:
    return name.split(".", 1)[0]


def _packaged_data_resource_uris() -> set[str]:
    uris: set[str] = set()
    for entry in DATA_RESOURCE_DEFS:
        path = entry.get("path")
        slug = entry.get("slug")
        if not isinstance(path, Path) or not isinstance(slug, str):
            continue
        try:
            path.resolve().relative_to(PACKAGED_RESOURCE_ROOT)
        except ValueError:
            continue
        uris.add(f"resource://mcp-geo/{slug}")
    return uris


PACKAGED_DATA_RESOURCE_URIS = _packaged_data_resource_uris()


def stable_resource_inventory() -> list[dict[str, Any]]:
    """Return resource descriptors whose presence is independent of local cache state."""
    stable_virtual_uris = {"resource://mcp-geo/boundary-cache-status"}
    resources = []
    for resource in _build_resource_list():
        uri = str(resource.get("uri", ""))
        if uri.startswith(SELF_RESOURCE_PREFIX):
            continue
        if (
            uri.startswith("skills://")
            or uri.startswith("ui://")
            or uri in PACKAGED_DATA_RESOURCE_URIS
            or uri in stable_virtual_uris
        ):
            resources.append(resource)
    resources.sort(key=lambda resource: str(resource.get("uri", "")))
    return resources


def _catalog_family(item_id: str) -> str | None:
    if item_id.startswith("os.search.places."):
        return "os_places"
    if item_id.startswith("os.search.links."):
        return "os_linked_ids"
    if item_id.startswith("os.features.ngd."):
        return "os_features"
    return None


def _property_names(schema: dict[str, Any]) -> list[str]:
    properties = schema.get("properties")
    if not isinstance(properties, dict):
        return []
    return sorted(str(name) for name in properties if name != "tool")


def _keywords(*parts: str, schema: dict[str, Any] | None = None) -> list[str]:
    words: set[str] = set()
    for part in parts:
        normalized = part.lower().replace("_", " ").replace(".", " ").replace("-", " ")
        words.update(word for word in normalized.split() if len(word) > 2)
    if schema is not None:
        words.update(name.lower() for name in _property_names(schema))
    return sorted(words)


def _tool_record(tool: Tool) -> dict[str, Any]:
    family = _family_for_tool(tool.name)
    record_id = f"tool:{tool.name}"
    record: dict[str, Any] = {
        "id": record_id,
        "name": tool.name,
        "route": record_id,
        "record_type": "mcp-tool",
        "title": tool.name,
        "description": tool.description,
        "notes": tool.description,
        "publisher": "mcp-geo",
        "publisher_title": "MCP Geo",
        "family": family,
        "version": tool.version,
        "keywords": _keywords(tool.name, tool.description, schema=tool.input_schema),
        "input_schema": tool.input_schema,
        "output_schema": tool.output_schema,
        "access": {
            "protocol": "MCP",
            "discovery_method": "tools/list",
            "call_method": "tools/call",
        },
        "source": {"kind": "runtime-registry", "path": "server/mcp/tools.py"},
    }
    if family in FEATURED_FAMILIES:
        record["spatial_profile_id"] = f"spatial:{tool.name}"
        record["mcp_binding_id"] = f"binding:{tool.name}"
        record["featured"] = True
    return record


def _resource_record(resource: dict[str, Any]) -> dict[str, Any]:
    uri = str(resource.get("uri", ""))
    annotations = resource.get("annotations")
    if not isinstance(annotations, dict):
        annotations = {}
    title = str(resource.get("title") or resource.get("name") or uri)
    description = str(resource.get("description") or "")
    return {
        "id": f"resource:{uri}",
        "route": f"resource:{uri}",
        "record_type": "mcp-resource",
        "title": title,
        "description": description,
        "notes": description,
        "publisher": "mcp-geo",
        "publisher_title": "MCP Geo",
        "resource_type": str(resource.get("type") or "resource"),
        "uri": uri,
        "name": uri,
        "mcp_resource_name": str(resource.get("name") or ""),
        "mime_type": str(resource.get("mimeType") or "application/octet-stream"),
        "annotations": annotations,
        "keywords": _keywords(uri, title, description, " ".join(map(str, annotations.values()))),
        "access": {"protocol": "MCP", "read_method": "resources/read"},
        "source": {"kind": "runtime-resource-list", "path": "server/mcp/resources.py"},
    }


def _catalog_record(item: dict[str, Any], family_tool_ids: dict[str, list[str]]) -> dict[str, Any]:
    item_id = str(item.get("id") or "")
    request_value = item.get("request")
    request: dict[str, Any] = request_value if isinstance(request_value, dict) else {}
    params_value = request.get("params")
    params: dict[str, Any] = params_value if isinstance(params_value, dict) else {}
    expects_value = item.get("expects")
    expects: dict[str, Any] = expects_value if isinstance(expects_value, dict) else {}
    docs_value = item.get("docs")
    docs: list[Any] = docs_value if isinstance(docs_value, list) else []
    family = _catalog_family(item_id)
    record: dict[str, Any] = {
        "id": f"os-catalog:{item_id}",
        "name": item_id,
        "route": f"os-catalog:{item_id}",
        "record_type": "os-api-catalog-entry",
        "title": str(item.get("title") or item_id),
        "description": str(item.get("description") or ""),
        "notes": str(item.get("description") or ""),
        "publisher": "ordnance-survey",
        "publisher_title": "Ordnance Survey",
        "catalog_id": item_id,
        "catalog_kind": str(item.get("kind") or ""),
        "category": str(item.get("category") or ""),
        "required": bool(item.get("required")),
        "endpoint": {
            "method": str(request.get("method") or ""),
            "url": str(request.get("url") or ""),
            "parameter_names": sorted(str(name) for name in params),
            "expected_status": expects.get("status", []),
            "content_type_prefix": str(expects.get("contentTypePrefix") or ""),
        },
        "documentation": sorted(str(url) for url in docs),
        "keywords": _keywords(
            item_id,
            str(item.get("title") or ""),
            str(item.get("description") or ""),
        ),
        "source": {"kind": "checked-in-catalog", "path": "resources/os_catalog.json"},
    }
    if family is not None:
        record["family"] = family
        record["related_tool_records"] = family_tool_ids[family]
        record["spatial_profile_id"] = f"spatial:os-catalog:{item_id}"
        record["featured"] = True
    return record


def _spatial_profile(tool: Tool) -> dict[str, Any]:
    family = _family_for_tool(tool.name)
    family_profile = FAMILY_PROFILES[family]
    input_properties = set(_property_names(tool.input_schema))
    spatial_input_names = {"bbox", "lat", "lon", "polygon", "radiusMeters"}
    filterable = bool(input_properties & spatial_input_names)
    output_schema_text = json.dumps(tool.output_schema, sort_keys=True)
    if "includeGeometry" in input_properties:
        geometry_output_mode = "optional-via-includeGeometry"
    elif '"lat"' in output_schema_text and '"lon"' in output_schema_text:
        geometry_output_mode = "declared-coordinate-result"
    else:
        geometry_output_mode = "not-declared-by-operation-schema"
    return {
        "id": f"spatial:{tool.name}",
        "record_id": f"tool:{tool.name}",
        "family": family,
        "coverage": family_profile["coverage"],
        "spatially_filterable": filterable,
        "filter_inputs": sorted(input_properties & spatial_input_names),
        "query_crs": family_profile["query_crs"],
        "response_crs": family_profile["response_crs"],
        "geometry_types": family_profile["geometry_types"],
        "identifiers": family_profile["identifiers"],
        "discovery_modes": family_profile["discovery_modes"],
        "metadata_scope": {
            "coverage": "underlying-family-data-capability",
            "query_crs": "family-default-for-spatial-operations",
            "response_crs": "family-default-for-geometric-results",
            "geometry_types": "potential-family-types-not-an-operation-output-guarantee",
        },
        "operation_contract": {
            "spatial_inputs": sorted(input_properties & spatial_input_names),
            "geometry_output": geometry_output_mode,
        },
        "provenance": {
            "basis": "curated-family-profile-and-runtime-schema",
            "source": family_profile["source"],
        },
    }


def _binding(tool: Tool) -> dict[str, Any]:
    family = _family_for_tool(tool.name)
    required = tool.input_schema.get("required")
    if not isinstance(required, list):
        required = []
    arguments = EXAMPLE_ARGUMENTS[tool.name]
    binding: dict[str, Any] = {
        "id": f"binding:{tool.name}",
        "record_id": f"tool:{tool.name}",
        "tool_name": tool.name,
        "family": family,
        "read_only": True,
        "credential_mode": "server-managed",
        "required_arguments": sorted(str(name) for name in required if name != "tool"),
        "example_arguments": arguments,
        "request_template": {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": tool.name, "arguments": arguments},
        },
        "failure_contract": {
            "missing_os_api_key": {"http_status": 501, "code": "NO_API_KEY"},
            "error_shape": {
                "isError": True,
                "code": "string",
                "message": "string",
                "correlationId": "string (optional)",
            },
        },
        "security": {
            "secret_values_stored": False,
            "client_supplies_upstream_key": False,
        },
    }
    if tool.name in {"os_places.by_uprn", "os_linked_ids.get", "os_linked_ids.identifiers"}:
        binding["argument_flow"] = {
            "placeholder": "<UPRN_FROM_PLACES_RESULT>",
            "source_binding": "binding:os_places.by_postcode",
            "source_path": "$.uprns[*].uprn",
        }
    if tool.name == "os_linked_ids.feature_types":
        binding["example_context"] = (
            "Verified RoadLink contract example; not asserted to relate to Explorer House."
        )
    return binding


def _catalog_spatial_profile(item: dict[str, Any]) -> dict[str, Any] | None:
    item_id = str(item.get("id") or "")
    family = _catalog_family(item_id)
    if family is None:
        return None
    family_profile = FAMILY_PROFILES[family]
    request_value = item.get("request")
    request: dict[str, Any] = request_value if isinstance(request_value, dict) else {}
    params_value = request.get("params")
    params: dict[str, Any] = params_value if isinstance(params_value, dict) else {}
    spatial_input_names = {"bbox", "lat", "lon", "polygon", "radius", "radiusMeters"}
    spatial_inputs = sorted(str(name) for name in params if name in spatial_input_names)
    if item_id.endswith(".items"):
        geometry_output = "feature-collection-endpoint"
    elif item_id.endswith(".queryables"):
        geometry_output = "metadata-only-endpoint"
    else:
        geometry_output = "not-declared-by-catalog-probe"
    return {
        "id": f"spatial:os-catalog:{item_id}",
        "record_id": f"os-catalog:{item_id}",
        "family": family,
        "coverage": family_profile["coverage"],
        "spatially_filterable": bool(spatial_inputs),
        "filter_inputs": spatial_inputs,
        "query_crs": family_profile["query_crs"],
        "response_crs": family_profile["response_crs"],
        "geometry_types": family_profile["geometry_types"],
        "identifiers": family_profile["identifiers"],
        "discovery_modes": family_profile["discovery_modes"],
        "metadata_scope": {
            "coverage": "underlying-family-data-capability",
            "query_crs": "family-default-for-spatial-operations",
            "response_crs": "family-default-for-geometric-results",
            "geometry_types": "potential-family-types-not-an-endpoint-output-guarantee",
        },
        "operation_contract": {
            "spatial_inputs": spatial_inputs,
            "geometry_output": geometry_output,
        },
        "map_representation": {
            "role": "demo-query-anchor",
            "caveat": "Explorer House is a query location, not this record's geometry or extent.",
        },
        "provenance": {
            "basis": "curated-family-profile-and-checked-in-os-catalog",
            "source": family_profile["source"],
        },
    }


def _load_catalog() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    path = REPO_ROOT / "resources" / "os_catalog.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    items = payload.get("items")
    if not isinstance(items, list):
        raise ValueError("resources/os_catalog.json must contain an items array")
    normalized = [item for item in items if isinstance(item, dict)]
    return payload, normalized


def build_payloads() -> dict[str, Any]:
    tools = sorted(all_tools(), key=lambda tool: tool.name)
    # The generated pack is itself exposed as MCP resources. Exclude those six
    # self-resources from the source inventory to avoid first-run and --check
    # behaviour depending on whether the output files already exist.
    resources = stable_resource_inventory()
    catalog, catalog_items = _load_catalog()
    catalog_items.sort(key=lambda item: str(item.get("id", "")))

    family_tool_ids = {
        family: [f"tool:{tool.name}" for tool in tools if _family_for_tool(tool.name) == family]
        for family in FEATURED_FAMILIES
    }
    records = [_tool_record(tool) for tool in tools]
    records.extend(_resource_record(resource) for resource in resources)
    records.extend(_catalog_record(item, family_tool_ids) for item in catalog_items)
    records.sort(key=lambda record: str(record["id"]))

    featured_tools = [tool for tool in tools if _family_for_tool(tool.name) in FEATURED_FAMILIES]
    spatial_profiles = [_spatial_profile(tool) for tool in featured_tools]
    spatial_profiles.extend(
        profile
        for item in catalog_items
        if (profile := _catalog_spatial_profile(item)) is not None
    )
    spatial_profiles.sort(key=lambda profile: str(profile["id"]))
    bindings = [_binding(tool) for tool in featured_tools]
    bindings.sort(key=lambda binding: str(binding["id"]))

    record_type_counts = Counter(str(record["record_type"]) for record in records)
    family_counts = Counter(_family_for_tool(tool.name) for tool in tools)
    resource_type_counts = Counter(
        str(resource.get("type") or "resource") for resource in resources
    )
    category_counts = Counter(
        str(item.get("category") or "uncategorized") for item in catalog_items
    )
    counts = {
        "records": len(records),
        "mcp_tools": len(tools),
        "mcp_resources": len(resources),
        "os_catalog_entries": len(catalog_items),
        "spatial_profiles": len(spatial_profiles),
        "mcp_bindings": len(bindings),
    }

    records_payload = records
    spatial_payload = {
        "schema": "okf-geospatial.v1",
        "version": "1.0.0",
        "description": (
            "Typed spatial coverage, filter, CRS, geometry and identifier metadata "
            "for the first OS discovery vertical slice."
        ),
        "crs_policy": {
            "web_query_and_geojson": "OGC:CRS84",
            "web_display": "EPSG:3857",
            "analysis_when_required": "EPSG:27700",
            "axis_order": "longitude, latitude",
        },
        "family_profiles": [
            {"family": family, **FAMILY_PROFILES[family]} for family in FEATURED_FAMILIES
        ],
        "records": spatial_profiles,
        "demo_locations": [
            {
                "id": "demo-location:explorer-house",
                "title": "Explorer House, Ordnance Survey",
                "postcode": "SO16 0AS",
                "geometry": {"type": "Point", "coordinates": EXPLORER_HOUSE_POINT},
                "bbox": EXPLORER_HOUSE_BBOX,
                "bbox_role": "demonstrator-query-window",
                "caveat": (
                    "The bbox is a derived query window around the published point, "
                    "not an OS site or property boundary."
                ),
                "crs": "OGC:CRS84",
                "source": "https://www.ordnancesurvey.co.uk/about/contact-us",
            }
        ],
    }
    bindings_payload = {
        "schema": "okf-mcp-binding.v1",
        "version": "1.0.0",
        "description": (
            "Read-only discovery-to-action bindings for OS Places, OS NGD Features "
            "and OS Linked Identifiers."
        ),
        "transport": {
            "protocol": "MCP",
            "http_path": "/mcp",
            "stdio_entrypoint": "server/stdio_adapter.py",
            "discover_tools": "tools/list",
            "discover_resources": "resources/list",
            "call_tool": "tools/call",
        },
        "credential_policy": {
            "upstream_credentials": "server-managed",
            "secret_values_stored": False,
            "missing_os_api_key": {"http_status": 501, "code": "NO_API_KEY"},
        },
        "bindings": bindings,
    }
    overview_payload = {
        "schema": "okf-discovery-overview.v1",
        "version": PACK_VERSION,
        "title": "MCP Geo + OKF discovery demonstrator",
        "generated_at": SNAPSHOT_AT,
        "counts": counts,
        "record_types": dict(sorted(record_type_counts.items())),
        "tool_families": dict(sorted(family_counts.items())),
        "resource_types": dict(sorted(resource_type_counts.items())),
        "os_catalog_categories": dict(sorted(category_counts.items())),
        "featured_families": list(FEATURED_FAMILIES),
        "optional_runtime_resource_families": OPTIONAL_RESOURCE_FAMILIES,
        "source": {
            "runtime_tools": "tools.registry.all_tools after server.mcp.tools registration",
            "runtime_resources": (
                "Stable packaged data, skill, UI, and boundary status descriptors from "
                "server.mcp.resources._build_resource_list"
            ),
            "resource_inventory_scope": "packaged-stable",
            "os_catalog": "resources/os_catalog.json",
            "os_catalog_source": str(catalog.get("source") or "https://api.os.uk"),
            "excluded_self_resource_prefix": SELF_RESOURCE_PREFIX,
        },
    }
    data_payloads: dict[str, Any] = {
        "overview.json": overview_payload,
        "records.json": records_payload,
        "spatial-index.json": spatial_payload,
        "mcp-bindings.json": bindings_payload,
    }
    rendered_data = {name: _json_text(payload) for name, payload in data_payloads.items()}
    entrypoints = {
        "data_manifest": "manifest.json",
        "overview_index": "overview.json",
        "records": "records.json",
        "spatial_index": "spatial-index.json",
        "mcp_bindings": "mcp-bindings.json",
    }
    manifest_payload = {
        "schema": "okf-discovery-manifest.v1",
        "version": PACK_VERSION,
        "title": "MCP Geo + OKF discovery demonstrator",
        "generated_at": SNAPSHOT_AT,
        "entrypoints": entrypoints,
        "indexes": {"overview": "overview.json"},
        "chunks": {
            "datasets": ["records.json"],
            "publishers": [],
            "relationships": [],
            "resources": [],
        },
        "performance": {
            "startup_mode": "overview-first",
            "full_record_hydration": "single static file",
        },
        "files": [
            {
                "path": name,
                "bytes": len(text.encode("utf-8")),
                "sha256": _sha256(text),
            }
            for name, text in sorted(rendered_data.items())
        ],
        "counts": counts,
    }
    manifest_text = _json_text(manifest_payload)
    integrity_text = {**rendered_data, "manifest.json": manifest_text}
    descriptor_payload = {
        "schema": "okf-explorer-large-corpus.v1",
        "kind": "okf-large-corpus",
        "version": PACK_VERSION,
        "status": "demonstrator",
        "generated_at": SNAPSHOT_AT,
        "title": "MCP Geo + OKF discovery demonstrator",
        "description": (
            "A deterministic discovery inventory joining MCP Geo tools and resources "
            "to the Ordnance Survey API catalogue, with spatial and MCP bindings."
        ),
        "entrypoints": entrypoints,
        "entrypoint_integrity": {
            key: {"path": path, "sha256": _sha256(integrity_text[path])}
            for key, path in sorted(entrypoints.items())
        },
        "delivery": {
            "schema": "okf-delivery-map.v1",
            "artifacts": {
                key: {
                    "path": filename,
                    "mcp_resource_uri": (
                        "resource://mcp-geo/okf-discovery-"
                        f"{Path(filename).stem}"
                    ),
                    "http_path": f"/okf-discovery/data/{filename}",
                }
                for key, filename in sorted(DELIVERY_FILES.items())
            },
        },
        "counts": counts,
        "performance": {
            "startup_mode": "overview-first",
            "full_record_hydration": "single static file",
            "search": "deterministic client-side text and facet filtering",
            "spatial_filtering": "static sidecar joined by record_id",
        },
        "vocabulary": {
            "record_singular": "tool, resource or OS API record",
            "record_plural": "tools, resources and OS API records",
            "search_placeholder": "Search OS data, identifiers, geography and MCP tools",
        },
        "extensions": {
            "okf-discovery-records.v1": {
                "entrypoint": "records",
                "container": "array",
            },
            "okf-geospatial.v1": {"mode": "external", "entrypoint": "spatial_index"},
            "okf-mcp-binding.v1": {"mode": "external", "entrypoint": "mcp_bindings"},
        },
        "source": {
            "mode": "checked-in-and-runtime-registry",
            "network_calls": False,
            "secret_values_stored": False,
            "excluded_self_resource_prefix": SELF_RESOURCE_PREFIX,
        },
    }

    payloads: dict[str, Any] = {
        "descriptor.json": descriptor_payload,
        **data_payloads,
        "manifest.json": manifest_payload,
    }
    return payloads


def write_or_check(output_dir: Path, *, check: bool) -> int:
    payloads = build_payloads()
    mismatches: list[str] = []
    if check:
        for name, payload in sorted(payloads.items()):
            path = output_dir / name
            expected = _json_text(payload)
            if not path.exists():
                mismatches.append(f"missing: {path}")
            elif path.read_text(encoding="utf-8") != expected:
                mismatches.append(f"out of date: {path}")
        if mismatches:
            print("OKF discovery pack is out of date:", file=sys.stderr)
            for mismatch in mismatches:
                print(f"- {mismatch}", file=sys.stderr)
            return 1
        print(f"OKF discovery pack is current: {output_dir}")
        return 0

    output_dir.mkdir(parents=True, exist_ok=True)
    for name, payload in sorted(payloads.items()):
        (output_dir / name).write_text(_json_text(payload), encoding="utf-8")
    counts = payloads["overview.json"]["counts"]
    print(
        "Wrote OKF discovery pack "
        f"({counts['mcp_tools']} tools, {counts['mcp_resources']} resources, "
        f"{counts['os_catalog_entries']} OS catalogue entries) to {output_dir}"
    )
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Pack output directory (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail when generated output differs from the files on disk.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    return write_or_check(args.output_dir, check=args.check)


if __name__ == "__main__":
    raise SystemExit(main())
