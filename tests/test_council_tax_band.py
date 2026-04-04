from __future__ import annotations

from fastapi.testclient import TestClient

from server.config import settings
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


RESULTS_HTML = """
<html>
  <body>
    <h1>Search results</h1>
    <table class="govuk-table">
      <thead>
        <tr>
          <th>Property name</th>
          <th>Street</th>
          <th>Town</th>
          <th>Postcode</th>
          <th>Council Tax band</th>
          <th>Band status</th>
          <th>Local authority</th>
          <th>Local authority reference number</th>
          <th>Court code</th>
          <th>Property use</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><a href="/check-council-tax-band/property/abc123">Flat 1</a></td>
          <td>1 High Street</td>
          <td>London</td>
          <td>SW1A 1AA</td>
          <td>D</td>
          <td>Current</td>
          <td>Westminster</td>
          <td>123456</td>
          <td>VT1</td>
          <td>Domestic</td>
        </tr>
      </tbody>
    </table>
  </body>
</html>
"""


DETAIL_HTML = """
<html>
  <body>
    <dl class="govuk-summary-list">
      <dt>Address</dt><dd>Flat 1, 1 High Street, London, SW1A 1AA</dd>
      <dt>Council Tax band</dt><dd>D</dd>
      <dt>Band status</dt><dd>Current</dd>
      <dt>Local authority</dt><dd>Westminster</dd>
      <dt>Property use</dt><dd>Domestic</dd>
    </dl>
  </body>
</html>
"""


NO_RESULTS_HTML = """
<html>
  <head>
    <title>No results - Check and challenge your Council Tax band - GOV.UK</title>
  </head>
  <body>
    <h1>No results</h1>
    <p>Try entering the details again.</p>
  </body>
</html>
"""


def test_council_tax_band_lookup_requires_search_fields(client: TestClient) -> None:
    response = client.post("/tools/call", json={"tool": "council_tax.band_lookup"})
    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_INPUT"


def test_council_tax_band_lookup_rejects_invalid_postcode(client: TestClient) -> None:
    response = client.post(
        "/tools/call",
        json={"tool": "council_tax.band_lookup", "postcode": "bad-postcode"},
    )
    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_INPUT"


def test_council_tax_band_lookup_rejects_invalid_band(client: TestClient) -> None:
    response = client.post(
        "/tools/call",
        json={"tool": "council_tax.band_lookup", "postcode": "SW1A 1AA", "band": "Z"},
    )
    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_INPUT"


def test_council_tax_band_lookup_rejects_overlong_reference(client: TestClient) -> None:
    response = client.post(
        "/tools/call",
        json={
            "tool": "council_tax.band_lookup",
            "postcode": "SW1A 1AA",
            "billingAuthorityReference": "X" * 65,
        },
    )
    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_INPUT"
    assert "billingAuthorityReference" in response.json()["message"]


def test_council_tax_band_lookup_rejects_overlong_property_use(client: TestClient) -> None:
    response = client.post(
        "/tools/call",
        json={
            "tool": "council_tax.band_lookup",
            "postcode": "SW1A 1AA",
            "propertyUse": "X" * 65,
        },
    )
    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_INPUT"
    assert "propertyUse" in response.json()["message"]


def test_council_tax_band_lookup_live_disabled(monkeypatch) -> None:
    monkeypatch.setattr(settings, "COUNCIL_TAX_BAND_LIVE_ENABLED", False, raising=False)
    client = TestClient(app)
    response = client.post(
        "/tools/call",
        json={"tool": "council_tax.band_lookup", "postcode": "SW1A 1AA"},
    )
    assert response.status_code == 501
    assert response.json()["code"] == "LIVE_DISABLED"


def test_council_tax_band_lookup_success(monkeypatch) -> None:
    submitted: dict[str, str] = {}

    def fake_get_search_form():
        return 200, FORM_HTML

    def fake_submit_search(form_data: dict[str, str]):
        submitted.update(form_data)
        return 200, RESULTS_HTML

    monkeypatch.setattr(council_tax.client, "get_search_form", fake_get_search_form)
    monkeypatch.setattr(council_tax.client, "submit_search", fake_submit_search)

    client = TestClient(app)
    response = client.post(
        "/tools/call",
        json={
            "tool": "council_tax.band_lookup",
            "postcode": "SW1A 1AA",
            "propertyName": "Flat 1",
            "band": "d",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    match = body["matches"][0]
    assert match["band"] == "D"
    assert match["bandStatus"] == "Current"
    assert match["billingAuthority"] == "Westminster"
    assert match["address"] == "Flat 1, 1 High Street, London, SW1A 1AA"
    assert (
        match["detailUrl"]
        == "https://www.tax.service.gov.uk/check-council-tax-band/property/abc123"
    )
    assert submitted["csrfToken"] == "csrf-123"
    assert submitted["postcode"] == "SW1A1AA"
    assert submitted["propertyName"] == "Flat 1"
    assert submitted["filters.councilTaxBands"] == "D"
    assert submitted["Search"] == "Search"


def test_council_tax_band_lookup_definition_list_parse() -> None:
    matches = council_tax._parse_matches(  # noqa: SLF001
        DETAIL_HTML,
        base_url="https://www.tax.service.gov.uk/check-council-tax-band",
    )
    assert len(matches) == 1
    assert matches[0]["band"] == "D"
    assert matches[0]["address"] == "Flat 1, 1 High Street, London, SW1A 1AA"


def test_council_tax_band_lookup_service_problem_page(monkeypatch) -> None:
    def fake_get_search_form():
        return 200, FORM_HTML

    def fake_submit_search(form_data: dict[str, str]):  # noqa: ARG001
        return 200, "<html><h1>Sorry, there is a problem with the service</h1></html>"

    monkeypatch.setattr(council_tax.client, "get_search_form", fake_get_search_form)
    monkeypatch.setattr(council_tax.client, "submit_search", fake_submit_search)

    client = TestClient(app)
    response = client.post(
        "/tools/call",
        json={"tool": "council_tax.band_lookup", "postcode": "SW1A 1AA"},
    )
    assert response.status_code == 502
    assert response.json()["code"] == "COUNCIL_TAX_API_ERROR"


def test_council_tax_band_lookup_no_results_page(monkeypatch) -> None:
    def fake_get_search_form():
        return 200, FORM_HTML

    def fake_submit_search(form_data: dict[str, str]):  # noqa: ARG001
        return 200, NO_RESULTS_HTML

    monkeypatch.setattr(council_tax.client, "get_search_form", fake_get_search_form)
    monkeypatch.setattr(council_tax.client, "submit_search", fake_submit_search)

    client = TestClient(app)
    response = client.post(
        "/tools/call",
        json={"tool": "council_tax.band_lookup", "postcode": "LS1 4AP"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 0
    assert body["matches"] == []


def test_council_tax_band_lookup_endpoint_contract() -> None:
    calls: list[tuple[str, str, dict[str, str] | None, dict[str, str] | None]] = []

    class _Response:
        def __init__(self, text: str, status_code: int = 200, url: str = "") -> None:
            self.text = text
            self.status_code = status_code
            self.url = url

    class _Session:
        def request(
            self,
            method: str,
            url: str,
            *,
            data: dict[str, str] | None = None,
            headers: dict[str, str] | None = None,
            timeout: float | None = None,  # noqa: ARG002
            allow_redirects: bool = True,  # noqa: ARG002
        ) -> _Response:
            calls.append((method, url, data, headers))
            assert headers and headers["User-Agent"]
            if method == "GET":
                return _Response(FORM_HTML, url=url)
            return _Response(RESULTS_HTML, url=url)

    session_client = council_tax.CouncilTaxBandClient(
        base_url="https://example.test/check-council-tax-band",
        session=_Session(),
    )

    get_status, get_body = session_client.get_search_form()
    assert get_status == 200
    form_payload = council_tax._build_form_payload(  # noqa: SLF001
        {"postcode": "SW1A1AA", "page": "0"},
        str(get_body),
    )
    post_status, post_body = session_client.submit_search(form_payload)
    assert post_status == 200
    assert isinstance(post_body, str)

    assert calls[0][0] == "GET"
    assert calls[0][1].endswith("/check-council-tax-band/search-council-tax-advanced")
    assert calls[1][0] == "POST"
    assert calls[1][1].endswith("/check-council-tax-band/search-council-tax-advanced")
    assert calls[1][3] is not None
    assert calls[1][3]["Origin"] == "https://example.test"


def test_council_tax_band_lookup_root_base_url_origin_header() -> None:
    calls: list[dict[str, str] | None] = []

    class _Response:
        def __init__(self, text: str, status_code: int = 200, url: str = "") -> None:
            self.text = text
            self.status_code = status_code
            self.url = url

    class _Session:
        def request(
            self,
            method: str,
            url: str,
            *,
            data: dict[str, str] | None = None,  # noqa: ARG002
            headers: dict[str, str] | None = None,
            timeout: float | None = None,  # noqa: ARG002
            allow_redirects: bool = True,  # noqa: ARG002
        ) -> _Response:
            calls.append(headers)
            if method == "GET":
                return _Response(FORM_HTML, url=url)
            return _Response(RESULTS_HTML, url=url)

    session_client = council_tax.CouncilTaxBandClient(
        base_url="https://example.test",
        session=_Session(),
    )

    get_status, get_body = session_client.get_search_form()
    assert get_status == 200
    form_payload = council_tax._build_form_payload(  # noqa: SLF001
        {"postcode": "SW1A1AA", "page": "0"},
        str(get_body),
    )
    post_status, _post_body = session_client.submit_search(form_payload)
    assert post_status == 200
    assert calls[1] is not None
    assert calls[1]["Origin"] == "https://example.test"
