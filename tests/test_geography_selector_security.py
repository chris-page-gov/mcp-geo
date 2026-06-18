from pathlib import Path


def test_geography_selector_avoids_html_sinks_for_tool_payloads() -> None:
    source = Path("ui/geography_selector.html").read_text(encoding="utf-8")

    assert ".innerHTML" not in source
    assert "replaceChildren" in source
    assert "textContent" in source
