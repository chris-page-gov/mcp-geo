from tools import os_mcp


def test_stats_routing_defaults_to_ons():
    details = os_mcp._build_stats_routing_explanation("gdp growth", [])
    assert details["provider"] == "ons"
    assert any("Defaulted to ONS" in reason for reason in details["reasons"])


def test_extract_place_name_with_stop_word():
    assert os_mcp._extract_place_name("Find New Town") == "New Town"


def test_level_helpers():
    assert os_mcp._pick_smallest_level([]) is None
    assert os_mcp._pick_largest_level([]) is None
    assert os_mcp._pick_admin_level(["local_auth", "ward"]) == "WARD"
    assert os_mcp._pick_admin_level(["postcode"]) is None
    assert os_mcp._should_route_nomis("gdp", ["lsoa"]) is True


def test_dataset_discovery_prefers_nomis():
    tool, workflow, _ = os_mcp._get_tool_for_intent(
        os_mcp.QueryIntent.DATASET_DISCOVERY,
        {"nomis_preferred": True},
    )
    assert tool == "nomis.datasets"
    assert "nomis.codelists" in workflow


def test_stats_routing_requires_query():
    status, body = os_mcp._stats_routing({"query": "  "})
    assert status == 400
    assert body["code"] == "INVALID_INPUT"


def test_build_interactive_params_search_term_and_multi():
    params = os_mcp._build_interactive_params("Select Westminster list", "Westminster")
    assert params["searchTerm"] == "Westminster"
    assert params["multiSelect"] is True


def test_classify_query_sets_admin_level():
    intent, _, params, _ = os_mcp._classify_query("Find ward Westminster")
    assert intent == os_mcp.QueryIntent.PLACE_LOOKUP
    assert params.get("level") == "WARD"
