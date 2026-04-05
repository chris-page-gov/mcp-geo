from __future__ import annotations

import tools.os_resources  # noqa: F401
from server.mcp import prompts, resource_catalog, tool_search
from tools.registry import get


def test_landis_resources_appear_in_catalog() -> None:
    resources = resource_catalog.list_data_resources()
    uris = {entry["uri"] for entry in resources}
    assert "resource://mcp-geo/landis-products" in uris
    assert "resource://mcp-geo/landis-docs-soil-data-structures" in uris
    assert "resource://mcp-geo/landis-docs-soil-classification" in uris
    assert "resource://mcp-geo/landis-licence-current" in uris
    assert "resource://mcp-geo/landis-portal-inventory" in uris
    assert "resource://mcp-geo/landis-archive-triage" in uris
    assert "resource://mcp-geo/landis-full-release-manifest" in uris


def test_landis_resource_content_is_readable_through_resource_catalog() -> None:
    entry = resource_catalog.resolve_data_resource("resource://mcp-geo/landis-docs-soil-data-structures")
    assert entry is not None
    content, etag, meta = resource_catalog.load_data_content(entry)
    assert content.startswith("# LandIS Soil Data Structures")
    assert etag
    assert meta is None


def test_landis_resource_is_readable_through_os_resources_get() -> None:
    tool = get("os_resources.get")
    assert tool is not None
    status, body = tool.call({"uri": "resource://mcp-geo/landis-licence-current"})
    assert status == 200
    assert body["mimeType"] == "text/markdown"
    assert "Open Access Status" in body["text"]


def test_landis_prompts_are_listed_and_fetchable() -> None:
    prompts._load_prompt_file.cache_clear()
    names = {entry["name"] for entry in prompts.list_prompts()}
    assert "landis_planner_soil_constraints_brief" in names
    prompt = prompts.get_prompt("landis_water_utility_pipe_risk_brief")
    assert prompt is not None
    assert "verification checklist" in prompt["messages"][0]["content"]["text"].lower()


def test_landis_tools_are_discoverable_in_tool_search() -> None:
    names = {item["name"] for item in tool_search.search_tools("landis soil corrosion", mode="token")}
    assert "landis_derive.pipe_risk" in names
    assert "landis_soilscapes.area_summary" in names

    natmap_names = {
        item["name"] for item in tool_search.search_tools("landis natmap texture", mode="token")
    }
    assert "landis_natmap.area_summary" in natmap_names

    nsi_names = {item["name"] for item in tool_search.search_tools("landis nsi evidence", mode="token")}
    assert "landis_nsi.nearest_sites" in nsi_names


def test_landis_archive_resources_are_readable() -> None:
    for uri in (
        "resource://mcp-geo/landis-portal-inventory",
        "resource://mcp-geo/landis-archive-triage",
        "resource://mcp-geo/landis-full-release-manifest",
    ):
        entry = resource_catalog.resolve_data_resource(uri)
        assert entry is not None
        content, etag, meta = resource_catalog.load_data_content(entry)
        assert content.startswith("{")
        assert etag
        assert meta is None
