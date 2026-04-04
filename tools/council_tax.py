from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from html import unescape
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urljoin, urlsplit

try:
    import requests
    from requests import exceptions as req_exc
except ImportError:  # pragma: no cover - optional dependency fallback
    requests = None  # type: ignore[assignment]

    class _ReqExc:
        SSLError = Exception
        ConnectionError = Exception
        Timeout = Exception

    req_exc = _ReqExc()

from server.circuit_breaker import get_circuit_breaker
from server.config import settings
from server.error_taxonomy import classify_error
from server.logging import log_upstream_error
from tools.registry import Tool, ToolResult, register
from tools.typing_utils import is_strict_int

DEFAULT_TIMEOUT = 10.0
DEFAULT_RETRIES = 2
DEFAULT_BASE_URL = "https://www.tax.service.gov.uk/check-council-tax-band"
SEARCH_PATH = "/search-council-tax-advanced"
POSTCODE_REGEX = re.compile(r"^[A-Z]{1,2}[0-9][0-9A-Z]?[0-9][A-Z]{2}$")
CSRF_TOKEN_PATTERN = re.compile(r'name="csrfToken"\s+value="([^"]+)"')
PAGE_PATTERN = re.compile(r'name="page"\s+value="([^"]+)"')
SERVICE_PROBLEM_PATTERN = re.compile(r"Sorry, there is a problem with the service", re.I)

_NO_RESULTS_PATTERNS = (
    "no results - check and challenge your council tax band",
    "no results",
    "no properties found",
    "no properties matched",
    "there are no properties",
    "there are no results",
    "no results found",
)

_FIELD_MAP = {
    "property": "propertyName",
    "property name": "propertyName",
    "address": "address",
    "street": "street",
    "town": "town",
    "postcode": "postcode",
    "council tax band": "band",
    "band": "band",
    "band status": "bandStatus",
    "local authority": "billingAuthority",
    "local authority reference number": "billingAuthorityReference",
    "court code": "courtCode",
    "property use": "propertyUse",
    "effective date": "effectiveDate",
}

_PRIMARY_SEARCH_FIELDS = (
    "propertyName",
    "street",
    "town",
    "postcode",
    "billingAuthority",
    "billingAuthorityReference",
    "courtCode",
)

_FORM_FIELD_MAP = {
    "propertyName": "propertyName",
    "street": "street",
    "town": "town",
    "postcode": "postcode",
    "band": "filters.councilTaxBands",
    "bandStatus": "filters.bandStatus",
    "billingAuthority": "filters.localAuthority",
    "billingAuthorityReference": "filters.localAuthorityReferenceNumber",
    "courtCode": "filters.courtCode",
    "propertyUse": "filters.propertyUse",
}


@dataclass
class _ParsedCell:
    text: str
    href: str | None = None


@dataclass
class _ParsedTable:
    headers: list[str] = field(default_factory=list)
    rows: list[list[_ParsedCell]] = field(default_factory=list)


class _HtmlTableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tables: list[_ParsedTable] = []
        self._table_depth = 0
        self._current_table: _ParsedTable | None = None
        self._current_row: list[tuple[str, _ParsedCell]] | None = None
        self._current_cell_tag: str | None = None
        self._current_cell_parts: list[str] = []
        self._current_cell_href: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "table":
            self._table_depth += 1
            if self._table_depth == 1:
                self._current_table = _ParsedTable()
            return
        if self._table_depth == 0:
            return
        if tag == "tr":
            self._current_row = []
            return
        if tag in {"th", "td"} and self._current_row is not None:
            self._current_cell_tag = tag
            self._current_cell_parts = []
            self._current_cell_href = None
            return
        if tag == "a" and self._current_cell_tag is not None:
            for name, value in attrs:
                if name == "href" and value:
                    self._current_cell_href = value
                    break

    def handle_endtag(self, tag: str) -> None:
        if tag == "table":
            if self._table_depth == 1 and self._current_table is not None:
                if self._current_table.headers or self._current_table.rows:
                    self.tables.append(self._current_table)
                self._current_table = None
            self._table_depth = max(0, self._table_depth - 1)
            return
        if self._table_depth == 0:
            return
        if tag in {"th", "td"} and self._current_cell_tag == tag and self._current_row is not None:
            self._current_row.append((
                tag,
                _ParsedCell(
                    text=_normalize_space("".join(self._current_cell_parts)),
                    href=self._current_cell_href,
                ),
            ))
            self._current_cell_tag = None
            self._current_cell_parts = []
            self._current_cell_href = None
            return
        if tag == "tr" and self._current_table is not None and self._current_row:
            if (
                not self._current_table.headers
                and all(cell_tag == "th" for cell_tag, _ in self._current_row)
            ):
                self._current_table.headers = [cell.text for _, cell in self._current_row]
            else:
                self._current_table.rows.append([cell for _, cell in self._current_row])
            self._current_row = None

    def handle_data(self, data: str) -> None:
        if self._current_cell_tag is not None:
            self._current_cell_parts.append(data)


class _DefinitionListParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.entries: list[tuple[str, str]] = []
        self._current_label: str | None = None
        self._current_tag: str | None = None
        self._current_parts: list[str] = []

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:  # noqa: ARG002
        if tag in {"dt", "dd"}:
            self._current_tag = tag
            self._current_parts = []

    def handle_endtag(self, tag: str) -> None:
        if tag not in {"dt", "dd"} or self._current_tag != tag:
            return
        text = _normalize_space("".join(self._current_parts))
        if tag == "dt":
            self._current_label = text or None
        elif self._current_label and text:
            self.entries.append((self._current_label, text))
        self._current_tag = None
        self._current_parts = []

    def handle_data(self, data: str) -> None:
        if self._current_tag is not None:
            self._current_parts.append(data)


def _normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", unescape(value or "")).strip()


def _normalize_label(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _normalize_postcode(value: Any) -> str | None:
    raw = str(value or "").strip().upper().replace(" ", "")
    if not raw:
        return None
    if not POSTCODE_REGEX.match(raw):
        return None
    return raw


def _clean_optional_text(value: Any, *, max_length: int = 120) -> str | None:
    text = _normalize_space(str(value or ""))
    if not text:
        return None
    if len(text) > max_length:
        return None
    return text


def _validate_optional_text(
    payload: dict[str, Any],
    field: str,
    *,
    max_length: int,
) -> tuple[int, str | None | dict[str, Any]]:
    text = _normalize_space(str(payload.get(field) or ""))
    if not text:
        return 200, None
    if len(text) > max_length:
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": f"{field} must be {max_length} characters or fewer",
        }
    return 200, text


def _origin_from_base_url(base_url: str) -> str | None:
    parts = urlsplit(base_url)
    if not parts.scheme or not parts.netloc:
        return None
    return f"{parts.scheme}://{parts.netloc}"


def _build_address(match: dict[str, Any]) -> str | None:
    address = _normalize_space(str(match.get("address") or ""))
    if address:
        return address
    parts = [
        _normalize_space(str(match.get("propertyName") or "")),
        _normalize_space(str(match.get("street") or "")),
        _normalize_space(str(match.get("town") or "")),
        _normalize_space(str(match.get("postcode") or "")),
    ]
    joined = ", ".join(part for part in parts if part)
    return joined or None


def _looks_like_no_results(html_text: str) -> bool:
    lowered = _normalize_space(re.sub(r"<[^>]+>", " ", html_text)).lower()
    return any(pattern in lowered for pattern in _NO_RESULTS_PATTERNS)


def _parse_csrf_token(html_text: str) -> str | None:
    match = CSRF_TOKEN_PATTERN.search(html_text)
    return match.group(1) if match else None


def _parse_page_value(html_text: str) -> str:
    match = PAGE_PATTERN.search(html_text)
    return match.group(1) if match else "0"


def _normalize_result_record(
    record: dict[str, str],
    *,
    hrefs: list[str],
    base_url: str,
) -> dict[str, Any] | None:
    normalized: dict[str, Any] = {}
    for label, value in record.items():
        mapped = _FIELD_MAP.get(_normalize_label(label))
        if mapped and value:
            normalized[mapped] = value
    if not normalized:
        return None
    address = _build_address(normalized)
    if address:
        normalized["address"] = address
    if hrefs:
        normalized["detailUrl"] = urljoin(f"{base_url.rstrip('/')}/", hrefs[0])
    normalized["jurisdiction"] = "england_wales"
    normalized["provider"] = "hmrc_voa"
    return normalized


def _parse_table_matches(html_text: str, *, base_url: str) -> list[dict[str, Any]]:
    parser = _HtmlTableParser()
    parser.feed(html_text)
    matches: list[dict[str, Any]] = []
    for table in parser.tables:
        headers = [_normalize_space(header) for header in table.headers]
        normalized_headers = {_normalize_label(header) for header in headers}
        if not ({"council tax band", "band"} & normalized_headers):
            continue
        for row in table.rows:
            record: dict[str, str] = {}
            hrefs: list[str] = []
            for index, header in enumerate(headers):
                if index >= len(row):
                    continue
                cell = row[index]
                if header and cell.text:
                    record[header] = cell.text
                if cell.href:
                    hrefs.append(cell.href)
            match = _normalize_result_record(record, hrefs=hrefs, base_url=base_url)
            if match is not None:
                matches.append(match)
    return matches


def _parse_definition_list_match(html_text: str, *, base_url: str) -> list[dict[str, Any]]:
    parser = _DefinitionListParser()
    parser.feed(html_text)
    if not parser.entries:
        return []
    record = {label: value for label, value in parser.entries}
    match = _normalize_result_record(record, hrefs=[], base_url=base_url)
    if match is None or not match.get("band"):
        return []
    return [match]


def _parse_matches(html_text: str, *, base_url: str) -> list[dict[str, Any]]:
    if SERVICE_PROBLEM_PATTERN.search(html_text):
        raise ValueError("service_problem")
    matches = _parse_table_matches(html_text, base_url=base_url)
    if matches:
        return matches
    matches = _parse_definition_list_match(html_text, base_url=base_url)
    if matches:
        return matches
    if _looks_like_no_results(html_text):
        return []
    raise ValueError("unparseable_results")


class CouncilTaxBandClient:
    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout: float | None = None,
        retries: int | None = None,
        user_agent: str | None = None,
        session: requests.Session | Any | None = None,
    ) -> None:
        configured_base_url = (
            base_url
            or getattr(settings, "COUNCIL_TAX_BASE_URL", "")
            or DEFAULT_BASE_URL
        )
        self.base_url = configured_base_url.rstrip("/")
        self.search_url = f"{self.base_url}{SEARCH_PATH}"
        configured_timeout = timeout
        if configured_timeout is None:
            configured_timeout = getattr(
                settings,
                "COUNCIL_TAX_HTTP_TIMEOUT_SECONDS",
                DEFAULT_TIMEOUT,
            )
        configured_retries = retries
        if configured_retries is None:
            configured_retries = getattr(settings, "COUNCIL_TAX_HTTP_RETRIES", DEFAULT_RETRIES)
        self.timeout = float(configured_timeout)
        self.retries = max(1, int(configured_retries))
        self.user_agent = (
            user_agent
            or getattr(settings, "COUNCIL_TAX_USER_AGENT", "")
            or "mcp-geo-council-tax-pilot/0.1"
        )
        self.session = (
            session
            if session is not None
            else (requests.Session() if requests is not None else None)
        )
        self._breaker = get_circuit_breaker("council_tax")

    def _headers(self, *, referer: str | None = None) -> dict[str, str]:
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-GB,en;q=0.9",
            "User-Agent": self.user_agent,
        }
        if referer:
            headers["Referer"] = referer
            origin = _origin_from_base_url(self.base_url)
            if origin:
                headers["Origin"] = origin
        return headers

    def _request(
        self,
        method: str,
        url: str,
        *,
        data: dict[str, str] | None = None,
        referer: str | None = None,
    ) -> tuple[int, str | dict[str, Any]]:
        if requests is None or self.session is None:
            return 501, {
                "isError": True,
                "code": "MISSING_DEPENDENCY",
                "message": "requests is not installed",
            }
        if not self._breaker.allow():
            return 503, {
                "isError": True,
                "code": "CIRCUIT_OPEN",
                "message": "Council Tax upstream circuit breaker is open.",
            }
        last_exc: Exception | None = None
        for attempt in range(1, self.retries + 1):
            try:
                response = self.session.request(
                    method,
                    url,
                    data=data,
                    headers=self._headers(referer=referer),
                    timeout=self.timeout,
                    allow_redirects=True,
                )
                if response.status_code != 200:
                    if response.status_code >= 500:
                        self._breaker.record_failure()
                    log_upstream_error(
                        service="council_tax",
                        code="COUNCIL_TAX_API_ERROR",
                        status_code=response.status_code,
                        url=getattr(response, "url", url),
                        params=data,
                        detail=response.text[:200],
                        attempt=attempt,
                        error_category=classify_error("COUNCIL_TAX_API_ERROR"),
                    )
                    return response.status_code, {
                        "isError": True,
                        "code": "COUNCIL_TAX_API_ERROR",
                        "message": f"Council Tax band service error: {response.text[:200]}",
                    }
                self._breaker.record_success()
                return 200, response.text
            except req_exc.SSLError as exc:
                self._breaker.record_failure()
                log_upstream_error(
                    service="council_tax",
                    code="UPSTREAM_TLS_ERROR",
                    url=url,
                    params=data,
                    detail=str(exc),
                    attempt=attempt,
                    error_category=classify_error("UPSTREAM_TLS_ERROR"),
                )
                return 501, {
                    "isError": True,
                    "code": "UPSTREAM_TLS_ERROR",
                    "message": str(exc),
                }
            except (req_exc.ConnectionError, req_exc.Timeout) as exc:
                last_exc = exc
                self._breaker.record_failure()
                if attempt == self.retries:
                    log_upstream_error(
                        service="council_tax",
                        code="UPSTREAM_CONNECT_ERROR",
                        url=url,
                        params=data,
                        detail=str(exc),
                        attempt=attempt,
                        error_category=classify_error("UPSTREAM_CONNECT_ERROR"),
                    )
                    return 501, {
                        "isError": True,
                        "code": "UPSTREAM_CONNECT_ERROR",
                        "message": str(exc),
                    }
            except Exception as exc:  # pragma: no cover - defensive
                self._breaker.record_failure()
                log_upstream_error(
                    service="council_tax",
                    code="INTEGRATION_ERROR",
                    url=url,
                    params=data,
                    detail=str(exc),
                    attempt=attempt,
                    error_category=classify_error("INTEGRATION_ERROR"),
                )
                return 500, {
                    "isError": True,
                    "code": "INTEGRATION_ERROR",
                    "message": str(exc),
                }
        return 501, {
            "isError": True,
            "code": "UPSTREAM_CONNECT_ERROR",
            "message": f"Failed after retries: {last_exc}",
        }

    def get_search_form(self) -> tuple[int, str | dict[str, Any]]:
        return self._request("GET", self.search_url)

    def submit_search(self, form_data: dict[str, str]) -> tuple[int, str | dict[str, Any]]:
        return self._request("POST", self.search_url, data=form_data, referer=self.search_url)


client = CouncilTaxBandClient()


def _validate_and_build_query(
    payload: dict[str, Any],
) -> tuple[int, dict[str, str] | dict[str, Any]]:
    postcode = payload.get("postcode")
    normalized_postcode = None
    if _normalize_space(str(postcode or "")):
        normalized_postcode = _normalize_postcode(postcode)
        if normalized_postcode is None:
            return 400, {
                "isError": True,
                "code": "INVALID_INPUT",
                "message": "postcode must be a valid UK postcode",
            }

    page = payload.get("page", 0)
    if not is_strict_int(page) or int(page) < 0:
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "page must be a non-negative integer",
        }

    band_status, band_value = _validate_optional_text(payload, "band", max_length=2)
    if band_status != 200:
        return band_status, band_value
    band = band_value
    if band is not None:
        band = band.upper()
        if band not in {"A", "B", "C", "D", "E", "F", "G", "H", "I"}:
            return 400, {
                "isError": True,
                "code": "INVALID_INPUT",
                "message": "band must be a single letter between A and I",
            }

    field_specs = {
        "propertyName": 120,
        "street": 120,
        "town": 120,
        "bandStatus": 64,
        "billingAuthority": 120,
        "billingAuthorityReference": 64,
        "courtCode": 32,
        "propertyUse": 64,
    }
    validated_fields: dict[str, str | None] = {}
    for field, max_length in field_specs.items():
        field_status, field_value = _validate_optional_text(
            payload,
            field,
            max_length=max_length,
        )
        if field_status != 200:
            return field_status, field_value
        validated_fields[field] = field_value

    query = {
        "propertyName": validated_fields["propertyName"],
        "street": validated_fields["street"],
        "town": validated_fields["town"],
        "postcode": normalized_postcode,
        "band": band,
        "bandStatus": validated_fields["bandStatus"],
        "billingAuthority": validated_fields["billingAuthority"],
        "billingAuthorityReference": validated_fields["billingAuthorityReference"],
        "courtCode": validated_fields["courtCode"],
        "propertyUse": validated_fields["propertyUse"],
        "page": str(int(page)),
    }

    if not any(query.get(field) for field in _PRIMARY_SEARCH_FIELDS):
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": (
                "Provide at least one search field: postcode, propertyName, street, town, "
                "billingAuthority, billingAuthorityReference, or courtCode"
            ),
        }
    return 200, {key: value for key, value in query.items() if value}


def _build_form_payload(query: dict[str, str], html_text: str) -> dict[str, str]:
    csrf_token = _parse_csrf_token(html_text)
    if not csrf_token:
        raise ValueError("missing_csrf_token")
    page = query.get("page") or _parse_page_value(html_text)
    form_payload = {
        "csrfToken": csrf_token,
        "page": page,
        "Search": "Search",
    }
    for query_key, form_key in _FORM_FIELD_MAP.items():
        value = query.get(query_key)
        if value:
            form_payload[form_key] = value
    return form_payload


def _band_lookup(payload: dict[str, Any]) -> ToolResult:
    if not bool(getattr(settings, "COUNCIL_TAX_BAND_LIVE_ENABLED", True)):
        return 501, {
            "isError": True,
            "code": "LIVE_DISABLED",
            "message": (
                "Council Tax band lookup live mode is disabled. "
                "Set COUNCIL_TAX_BAND_LIVE_ENABLED=true."
            ),
        }
    status, query = _validate_and_build_query(payload)
    if status != 200:
        return status, query

    form_status, form_html = client.get_search_form()
    if form_status != 200 or not isinstance(form_html, str):
        return form_status, form_html

    try:
        form_payload = _build_form_payload(query, form_html)
    except ValueError:
        return 502, {
            "isError": True,
            "code": "UPSTREAM_INVALID_RESPONSE",
            "message": "Council Tax band service form did not include an expected CSRF token.",
        }

    result_status, result_html = client.submit_search(form_payload)
    if result_status != 200 or not isinstance(result_html, str):
        return result_status, result_html

    try:
        matches = _parse_matches(result_html, base_url=client.base_url)
    except ValueError as exc:
        code = str(exc)
        if code == "service_problem":
            return 502, {
                "isError": True,
                "code": "COUNCIL_TAX_API_ERROR",
                "message": "Council Tax band service returned a service error page.",
            }
        return 502, {
            "isError": True,
            "code": "UPSTREAM_INVALID_RESPONSE",
            "message": "Council Tax band service returned HTML in an unexpected format.",
        }

    return 200, {
        "matches": matches,
        "count": len(matches),
        "page": int(query.get("page", "0")),
        "live": True,
        "jurisdiction": "england_wales",
        "warnings": ["experimental_html_scrape"],
        "provenance": {
            "source": "hmrc_check_council_tax_band",
            "method": "html_form",
            "searchUrl": client.search_url,
            "timestamp": time.time(),
        },
    }


register(
    Tool(
        name="council_tax.band_lookup",
        description=(
            "Experimental England/Wales Council Tax band lookup via the public GOV.UK service."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "council_tax.band_lookup"},
                "propertyName": {"type": "string"},
                "street": {"type": "string"},
                "town": {"type": "string"},
                "postcode": {"type": "string"},
                "band": {"type": "string", "description": "Optional A-I band filter."},
                "bandStatus": {"type": "string"},
                "billingAuthority": {"type": "string"},
                "billingAuthorityReference": {"type": "string"},
                "courtCode": {"type": "string"},
                "propertyUse": {"type": "string"},
                "page": {"type": "integer", "minimum": 0},
            },
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "matches": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "address": {"type": ["string", "null"]},
                            "propertyName": {"type": ["string", "null"]},
                            "street": {"type": ["string", "null"]},
                            "town": {"type": ["string", "null"]},
                            "postcode": {"type": ["string", "null"]},
                            "band": {"type": ["string", "null"]},
                            "bandStatus": {"type": ["string", "null"]},
                            "billingAuthority": {"type": ["string", "null"]},
                            "billingAuthorityReference": {"type": ["string", "null"]},
                            "courtCode": {"type": ["string", "null"]},
                            "propertyUse": {"type": ["string", "null"]},
                            "effectiveDate": {"type": ["string", "null"]},
                            "detailUrl": {"type": ["string", "null"]},
                            "jurisdiction": {"type": "string"},
                            "provider": {"type": "string"},
                        },
                        "required": ["jurisdiction", "provider"],
                        "additionalProperties": True,
                    },
                },
                "count": {"type": "integer"},
                "page": {"type": "integer"},
                "live": {"type": "boolean"},
                "jurisdiction": {"type": "string"},
                "warnings": {"type": "array", "items": {"type": "string"}},
                "provenance": {"type": "object"},
            },
            "required": ["matches", "count", "live", "jurisdiction"],
            "additionalProperties": True,
        },
        handler=_band_lookup,
    )
)
