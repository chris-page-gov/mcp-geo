from __future__ import annotations

from scripts.trace_utils import classify_tool_search_usage


def test_classify_tool_search_usage_ignores_limit_only_tools_list() -> None:
    requests = [
        {"method": "initialize", "params": {}},
        {"method": "tools/list", "params": {"limit": 10}},
    ]

    assert classify_tool_search_usage(requests) == "unused"


def test_classify_tool_search_usage_counts_scoped_tools_list() -> None:
    requests = [
        {"method": "initialize", "params": {}},
        {"method": "tools/list", "params": {"query": "postcode", "limit": 10}},
    ]

    assert classify_tool_search_usage(requests) == "supported"
