from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from server.main import app
from tools import council_tax


FORM_HTML = """
<html>
  <body>
    <form method="POST" action="/check-council-tax-band/search-council-tax-advanced">
      <input type="hidden" name="csrfToken" value="csrf-123"/>
      <input type="hidden" name="page" value="0"/>
    </form>
  </body>
</html>
"""

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "council_tax"
GOLD_PATH = Path(__file__).parent / "fixtures" / "council_tax_band_gold.json"


def _load_gold_cases() -> list[dict[str, Any]]:
    payload = json.loads(GOLD_PATH.read_text(encoding="utf-8"))
    return list(payload["cases"])


@pytest.mark.parametrize("case", _load_gold_cases(), ids=lambda case: case["id"])
def test_council_tax_band_lookup_gold_cases(monkeypatch, case: dict[str, Any]) -> None:
    fixture_html = (FIXTURE_ROOT / case["fixture"]).read_text(encoding="utf-8")

    def fake_get_search_form():
        return 200, FORM_HTML

    def fake_submit_search(form_data: dict[str, str]):  # noqa: ARG001
        return 200, fixture_html

    monkeypatch.setattr(council_tax.client, "get_search_form", fake_get_search_form)
    monkeypatch.setattr(council_tax.client, "submit_search", fake_submit_search)

    client = TestClient(app)
    response = client.post(
        "/tools/call",
        json={"tool": "council_tax.band_lookup", **case["payload"]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == case["expectedCount"]
    assert body["live"] is True
    assert body["jurisdiction"] == "england_wales"

    matches = body["matches"]
    for expected in case["expectedPresent"]:
        assert any(
            all(match.get(key) == value for key, value in expected.items())
            for match in matches
        ), expected

