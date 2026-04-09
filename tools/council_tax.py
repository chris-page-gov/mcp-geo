from __future__ import annotations

import csv
import re
import time
from dataclasses import dataclass, field
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlsplit

try:
    import duckdb
except ImportError:  # pragma: no cover - optional dependency fallback
    duckdb = None  # type: ignore[assignment]

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
UPRN_REGEX = re.compile(r"^[0-9]{1,12}$")
CSRF_TOKEN_PATTERN = re.compile(r'name="csrfToken"\s+value="([^"]+)"')
PAGE_PATTERN = re.compile(r'name="page"\s+value="([^"]+)"')
SERVICE_PROBLEM_PATTERN = re.compile(r"Sorry, there is a problem with the service", re.I)
ADDRESSBASE_PREMIUM_DOC_URL = (
    "https://docs.os.uk/os-downloads/products/addresses-and-names-portfolio/"
    "addressbase-premium/addressbase-premium-technical-specification"
)
ADDRESSBASE_PREMIUM_XREF_DOC_URL = (
    "https://docs.os.uk/os-downloads/addressing-and-location/addressbase-premium-islands/"
    "addressbase-premium-islands-technical-specification/structured-data-types/"
    "application-cross-reference-type-23-record"
)
ADDRESSBASE_RELEVANT_SOURCES = {
    "7666VC": "Centrally created Council Tax.",
    "7666VN": "Centrally created non-domestic rates.",
}
ADDRESSBASE_XREF_REQUIRED_COLUMNS = {"UPRN", "SOURCE"}
ADDRESSBASE_XREF_COLUMN_ALIASES = {
    "UPRN": ("UPRN", "uprn"),
    "XREF_KEY": ("XREF_KEY", "xRefKey", "xref_key"),
    "CROSS_REFERENCE": ("CROSS_REFERENCE", "crossReference", "cross_reference"),
    "SOURCE": ("SOURCE", "source"),
    "VERSION": ("VERSION", "version"),
    "START_DATE": ("START_DATE", "startDate", "start_date"),
    "END_DATE": ("END_DATE", "endDate", "end_date"),
    "LAST_UPDATE_DATE": ("LAST_UPDATE_DATE", "lastUpdateDate", "last_update_date"),
    "ENTRY_DATE": ("ENTRY_DATE", "entryDate", "entry_date"),
}
ADDRESSBASE_XREF_OPTIONAL_COLUMNS = (
    "XREF_KEY",
    "CROSS_REFERENCE",
    "VERSION",
    "START_DATE",
    "END_DATE",
    "LAST_UPDATE_DATE",
    "ENTRY_DATE",
)
ADDRESSBASE_XREF_SCAN_MAX_UPRNS = 5000

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
    ) -> None:
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


def _normalize_addressbase_column_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


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


def _normalize_uprn(value: Any) -> str | None:
    text = re.sub(r"\s+", "", str(value or ""))
    if not text or not UPRN_REGEX.fullmatch(text):
        return None
    return text


def _resolve_addressbase_column_mapping(fieldnames: list[str]) -> tuple[dict[str, str], list[str]]:
    actual_by_normalized = {
        _normalize_addressbase_column_name(fieldname): fieldname
        for fieldname in fieldnames
        if fieldname
    }
    mapping: dict[str, str] = {}
    missing: list[str] = []
    for canonical, aliases in ADDRESSBASE_XREF_COLUMN_ALIASES.items():
        actual = next(
            (
                actual_by_normalized.get(_normalize_addressbase_column_name(alias))
                for alias in aliases
                if actual_by_normalized.get(_normalize_addressbase_column_name(alias))
            ),
            None,
        )
        if actual is None:
            if canonical in ADDRESSBASE_XREF_REQUIRED_COLUMNS:
                missing.append(canonical)
            continue
        mapping[canonical] = actual
    return mapping, missing


def _score_addressbase_xref_candidate(candidate: Path) -> int:
    name = candidate.name.lower()
    score = 0
    if "xref_voa_os" in name:
        score += 100
    if "application" in name and "cross" in name and "reference" in name:
        score += 50
    if "id23" in name:
        score += 40
    if "type" in name and "23" in name:
        score += 20
    if "xref" in name:
        score += 10
    if candidate.suffix.lower() == ".parquet":
        score += 5
    if "test" in name or "sample" in name:
        score -= 100
    return score


def _resolve_addressbase_xref_path() -> Path | None:
    configured = str(getattr(settings, "ADDRESSBASE_PREMIUM_XREF_PATH", "") or "").strip()
    if not configured:
        return None
    path = Path(configured).expanduser()
    if path.is_file():
        return path
    if not path.is_dir():
        return None

    candidates: list[tuple[int, str, Path]] = []
    for pattern in ("*.parquet", "*.csv"):
        for candidate in path.rglob(pattern):
            if candidate.suffix.lower() == ".parquet" and duckdb is None:
                continue
            score = _score_addressbase_xref_candidate(candidate)
            if score > 0:
                candidates.append((score, str(candidate), candidate))
    if not candidates:
        return None
    candidates.sort(key=lambda item: (-item[0], item[1]))
    return candidates[0][2]


def _derive_uprn_tax_status(*, pays_council_tax: bool, pays_business_rates: bool) -> str:
    if pays_council_tax and pays_business_rates:
        return "both"
    if pays_council_tax:
        return "council_tax"
    if pays_business_rates:
        return "non_domestic_rates"
    return "none"


def _validate_uprn_query(
    payload: dict[str, Any],
) -> tuple[int, dict[str, Any] | dict[str, str | bool | list[str]]]:
    raw_uprns = payload.get("uprns")
    if not isinstance(raw_uprns, list) or not raw_uprns:
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "uprns must be a non-empty array of UPRN strings",
        }
    if len(raw_uprns) > ADDRESSBASE_XREF_SCAN_MAX_UPRNS:
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": f"uprns must contain {ADDRESSBASE_XREF_SCAN_MAX_UPRNS} items or fewer",
        }

    active_only = payload.get("activeOnly", True)
    if not isinstance(active_only, bool):
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "activeOnly must be a boolean",
        }

    normalized_uprns: list[str] = []
    seen: set[str] = set()
    for value in raw_uprns:
        uprn = _normalize_uprn(value)
        if uprn is None:
            return 400, {
                "isError": True,
                "code": "INVALID_INPUT",
                "message": "Each UPRN must be 1 to 12 digits",
            }
        if uprn in seen:
            continue
        seen.add(uprn)
        normalized_uprns.append(uprn)
    return 200, {"uprns": normalized_uprns, "activeOnly": active_only}


def _build_addressbase_accumulators(uprns: list[str]) -> dict[str, dict[str, Any]]:
    return {
        uprn: {
            "matches": [],
            "activeSources": set(),
            "allSources": set(),
            "inactiveSources": set(),
            "inactiveRelevantRecordCount": 0,
        }
        for uprn in uprns
    }


def _append_addressbase_match(
    *,
    accumulators: dict[str, dict[str, Any]],
    uprn: str,
    source: str,
    xref_key: Any,
    cross_reference: Any,
    version: Any,
    start_date: Any,
    end_date: Any,
    last_update_date: Any,
    entry_date: Any,
    active_only: bool,
) -> None:
    accumulator = accumulators[uprn]
    accumulator["allSources"].add(source)
    normalized_end_date = _normalize_space(str(end_date or ""))
    is_active = not normalized_end_date
    if not is_active:
        accumulator["inactiveSources"].add(source)
        accumulator["inactiveRelevantRecordCount"] += 1
        if active_only:
            return

    record = {
        "xrefKey": _clean_optional_text(xref_key, max_length=64),
        "crossReference": _clean_optional_text(cross_reference, max_length=128),
        "version": _clean_optional_text(version, max_length=16),
        "source": source,
        "sourceDescription": ADDRESSBASE_RELEVANT_SOURCES[source],
        "startDate": _clean_optional_text(start_date, max_length=32),
        "endDate": _clean_optional_text(end_date, max_length=32),
        "lastUpdateDate": _clean_optional_text(last_update_date, max_length=32),
        "entryDate": _clean_optional_text(entry_date, max_length=32),
        "active": is_active,
    }
    accumulator["matches"].append(record)
    if is_active:
        accumulator["activeSources"].add(source)


def _finalize_addressbase_results(
    *,
    uprns: list[str],
    accumulators: dict[str, dict[str, Any]],
    active_only: bool,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for uprn in uprns:
        accumulator = accumulators[uprn]
        relevant_sources = (
            sorted(accumulator["activeSources"])
            if active_only
            else sorted(accumulator["allSources"])
        )
        pays_council_tax = "7666VC" in relevant_sources
        pays_business_rates = "7666VN" in relevant_sources
        results.append({
            "uprn": uprn,
            "paysCouncilTax": pays_council_tax,
            "paysBusinessRates": pays_business_rates,
            "status": _derive_uprn_tax_status(
                pays_council_tax=pays_council_tax,
                pays_business_rates=pays_business_rates,
            ),
            "sourceCodes": relevant_sources,
            "inactiveSourceCodes": sorted(accumulator["inactiveSources"]),
            "matchedRecordCount": len(accumulator["matches"]),
            "inactiveRelevantRecordCount": int(accumulator["inactiveRelevantRecordCount"]),
            "matches": accumulator["matches"],
        })
    return results


def _scan_addressbase_xref_csv(
    *,
    path: Path,
    uprns: list[str],
    active_only: bool,
) -> tuple[int, dict[str, Any] | list[dict[str, Any]]]:
    requested = set(uprns)
    accumulators = _build_addressbase_accumulators(uprns)

    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            fieldnames = [
                fieldname
                for fieldname in (reader.fieldnames or [])
                if isinstance(fieldname, str)
            ]
            column_mapping, missing = _resolve_addressbase_column_mapping(fieldnames)
            if missing:
                return 502, {
                    "isError": True,
                    "code": "INVALID_DATA_SOURCE",
                    "message": (
                        "AddressBase Premium Application Cross Reference CSV is missing "
                        f"required columns: {', '.join(missing)}"
                    ),
                }

            for row in reader:
                if not isinstance(row, dict):
                    continue
                uprn = _normalize_uprn(row.get(column_mapping["UPRN"]))
                if uprn is None or uprn not in requested:
                    continue
                source = _normalize_space(str(row.get(column_mapping["SOURCE"]) or "")).upper()
                if source not in ADDRESSBASE_RELEVANT_SOURCES:
                    continue

                _append_addressbase_match(
                    accumulators=accumulators,
                    uprn=uprn,
                    source=source,
                    xref_key=row.get(column_mapping.get("XREF_KEY", "")),
                    cross_reference=row.get(column_mapping.get("CROSS_REFERENCE", "")),
                    version=row.get(column_mapping.get("VERSION", "")),
                    start_date=row.get(column_mapping.get("START_DATE", "")),
                    end_date=row.get(column_mapping.get("END_DATE", "")),
                    last_update_date=row.get(column_mapping.get("LAST_UPDATE_DATE", "")),
                    entry_date=row.get(column_mapping.get("ENTRY_DATE", "")),
                    active_only=active_only,
                )
    except OSError as exc:
        return 502, {
            "isError": True,
            "code": "INVALID_DATA_SOURCE",
            "message": f"Unable to read AddressBase Premium xref CSV: {exc}",
        }

    return 200, _finalize_addressbase_results(
        uprns=uprns,
        accumulators=accumulators,
        active_only=active_only,
    )


def _duckdb_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def _duckdb_addressbase_expression(
    column_mapping: dict[str, str],
    canonical: str,
    *,
    relation_alias: str | None = None,
    normalize_source: bool = False,
) -> str:
    actual = column_mapping.get(canonical)
    if actual is None:
        return "CAST(NULL AS VARCHAR)"
    qualified_identifier = _duckdb_identifier(actual)
    if relation_alias:
        qualified_identifier = f"{relation_alias}.{qualified_identifier}"
    expression = f"CAST({qualified_identifier} AS VARCHAR)"
    if normalize_source:
        return f"UPPER(TRIM({expression}))"
    return expression


def _configure_addressbase_duckdb_connection(connection: Any) -> None:
    threads = max(1, int(getattr(settings, "ADDRESSBASE_PREMIUM_DUCKDB_THREADS", 1) or 1))
    memory_limit = str(
        getattr(settings, "ADDRESSBASE_PREMIUM_DUCKDB_MEMORY_LIMIT", "512MB") or ""
    ).strip()
    connection.execute(f"PRAGMA threads={threads}")
    if memory_limit:
        quoted_memory_limit = memory_limit.replace("'", "''")
        connection.execute(f"SET memory_limit='{quoted_memory_limit}'")


def _scan_addressbase_xref_parquet(
    *,
    path: Path,
    uprns: list[str],
    active_only: bool,
) -> tuple[int, dict[str, Any] | list[dict[str, Any]]]:
    if duckdb is None:
        return 501, {
            "isError": True,
            "code": "MISSING_DEPENDENCY",
            "message": "duckdb is required to query AddressBase Premium parquet sources",
        }

    accumulators = _build_addressbase_accumulators(uprns)
    connection = duckdb.connect(database=":memory:")  # type: ignore[union-attr]
    try:
        _configure_addressbase_duckdb_connection(connection)
        schema_rows = connection.execute(
            "DESCRIBE SELECT * FROM read_parquet(?)",
            [str(path)],
        ).fetchall()
        column_mapping, missing = _resolve_addressbase_column_mapping(
            [str(row[0]) for row in schema_rows if row and row[0]]
        )
        if missing:
            return 502, {
                "isError": True,
                "code": "INVALID_DATA_SOURCE",
                "message": (
                    "AddressBase Premium parquet is missing required columns: "
                    f"{', '.join(missing)}"
                ),
            }

        connection.execute("CREATE TEMP TABLE requested_uprns (uprn VARCHAR)")
        connection.executemany(
            "INSERT INTO requested_uprns VALUES (?)",
            [(uprn,) for uprn in uprns],
        )

        source_expr = _duckdb_addressbase_expression(
            column_mapping,
            "SOURCE",
            relation_alias="xref",
            normalize_source=True,
        )
        end_date_expr = _duckdb_addressbase_expression(
            column_mapping,
            "END_DATE",
            relation_alias="xref",
        )
        rows = connection.execute(
            f"""
            SELECT
                req.uprn AS requested_uprn,
                {source_expr} AS source,
                {_duckdb_addressbase_expression(
                    column_mapping,
                    "XREF_KEY",
                    relation_alias="xref",
                )} AS xref_key,
                {_duckdb_addressbase_expression(
                    column_mapping,
                    "CROSS_REFERENCE",
                    relation_alias="xref",
                )} AS cross_reference,
                {_duckdb_addressbase_expression(
                    column_mapping,
                    "VERSION",
                    relation_alias="xref",
                )} AS version,
                {_duckdb_addressbase_expression(
                    column_mapping,
                    "START_DATE",
                    relation_alias="xref",
                )} AS start_date,
                {end_date_expr} AS end_date,
                {_duckdb_addressbase_expression(
                    column_mapping,
                    "LAST_UPDATE_DATE",
                    relation_alias="xref",
                )} AS last_update_date,
                {_duckdb_addressbase_expression(
                    column_mapping,
                    "ENTRY_DATE",
                    relation_alias="xref",
                )} AS entry_date
            FROM read_parquet(?) AS xref
            INNER JOIN requested_uprns AS req
                ON {_duckdb_addressbase_expression(
                    column_mapping,
                    "UPRN",
                    relation_alias="xref",
                )} = req.uprn
            WHERE {source_expr} IN ('7666VC', '7666VN')
              AND (? = FALSE OR COALESCE(TRIM({end_date_expr}), '') = '')
            """,
            [str(path), active_only],
        ).fetchall()
    except Exception as exc:
        return 502, {
            "isError": True,
            "code": "INVALID_DATA_SOURCE",
            "message": f"Unable to query AddressBase Premium parquet: {exc}",
        }
    finally:
        connection.close()

    for (
        requested_uprn,
        source,
        xref_key,
        cross_reference,
        version,
        start_date,
        end_date,
        last_update_date,
        entry_date,
    ) in rows:
        normalized_uprn = _normalize_uprn(requested_uprn)
        normalized_source = _normalize_space(str(source or "")).upper()
        if normalized_uprn is None or normalized_source not in ADDRESSBASE_RELEVANT_SOURCES:
            continue
        _append_addressbase_match(
            accumulators=accumulators,
            uprn=normalized_uprn,
            source=normalized_source,
            xref_key=xref_key,
            cross_reference=cross_reference,
            version=version,
            start_date=start_date,
            end_date=end_date,
            last_update_date=last_update_date,
            entry_date=entry_date,
            active_only=active_only,
        )

    return 200, _finalize_addressbase_results(
        uprns=uprns,
        accumulators=accumulators,
        active_only=active_only,
    )


def _scan_addressbase_xref(
    *,
    path: Path,
    uprns: list[str],
    active_only: bool,
) -> tuple[int, dict[str, Any] | list[dict[str, Any]]]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return _scan_addressbase_xref_csv(path=path, uprns=uprns, active_only=active_only)
    if suffix == ".parquet":
        return _scan_addressbase_xref_parquet(path=path, uprns=uprns, active_only=active_only)
    return 502, {
        "isError": True,
        "code": "INVALID_DATA_SOURCE",
        "message": f"Unsupported AddressBase Premium xref file type: {path.suffix or '<none>'}",
    }


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
    record = dict(parser.entries)
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
    for field_name, max_length in field_specs.items():
        field_status, field_value = _validate_optional_text(
            payload,
            field_name,
            max_length=max_length,
        )
        if field_status != 200:
            return field_status, field_value
        validated_fields[field_name] = field_value

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


def _uprn_query(payload: dict[str, Any]) -> ToolResult:
    status, validated = _validate_uprn_query(payload)
    if status != 200:
        return status, validated

    uprns = list(validated["uprns"])
    active_only = bool(validated["activeOnly"])
    xref_path = _resolve_addressbase_xref_path()
    if xref_path is None:
        return 501, {
            "isError": True,
            "code": "NO_ADDRESSBASE_PREMIUM_DATA",
            "message": (
                "AddressBase Premium Application Cross Reference data is not configured. "
                "Set ADDRESSBASE_PREMIUM_XREF_PATH to an AddressBase Premium xref CSV/parquet "
                "file or to a directory containing one."
            ),
        }

    scan_status, results_or_error = _scan_addressbase_xref(
        path=xref_path,
        uprns=uprns,
        active_only=active_only,
    )
    if scan_status != 200:
        assert isinstance(results_or_error, dict)
        return scan_status, results_or_error

    results = list(results_or_error)
    summary = {
        "queriedCount": len(results),
        "councilTaxCount": sum(1 for item in results if item["paysCouncilTax"]),
        "businessRatesCount": sum(1 for item in results if item["paysBusinessRates"]),
        "bothCount": sum(1 for item in results if item["status"] == "both"),
        "noneCount": sum(1 for item in results if item["status"] == "none"),
        "activeOnly": active_only,
    }
    provenance_method = (
        "duckdb_parquet_query"
        if xref_path.suffix.lower() == ".parquet"
        else "streaming_csv_scan"
    )
    return 200, {
        "results": results,
        "summary": summary,
        "provenance": {
            "source": "addressbase_premium_application_cross_reference",
            "method": provenance_method,
            "configuredPath": str(xref_path),
            "documentation": {
                "product": ADDRESSBASE_PREMIUM_DOC_URL,
                "applicationCrossReference": ADDRESSBASE_PREMIUM_XREF_DOC_URL,
            },
            "sourceValues": ADDRESSBASE_RELEVANT_SOURCES,
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


register(
    Tool(
        name="council_tax.query",
        description=(
            "Query AddressBase Premium Application Cross Reference records by UPRN to "
            "identify Council Tax and non-domestic rates flags."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "council_tax.query"},
                "uprns": {
                    "type": "array",
                    "items": {"type": "string", "pattern": "^[0-9]{1,12}$"},
                    "minItems": 1,
                    "maxItems": ADDRESSBASE_XREF_SCAN_MAX_UPRNS,
                    "description": "One or more UPRNs to inspect in AddressBase Premium.",
                },
                "activeOnly": {
                    "type": "boolean",
                    "description": (
                        "When true, only treat Type 23 cross references with a blank END_DATE "
                        "as current. Defaults to true."
                    ),
                },
            },
            "required": ["uprns"],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "results": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "uprn": {"type": "string"},
                            "paysCouncilTax": {"type": "boolean"},
                            "paysBusinessRates": {"type": "boolean"},
                            "status": {
                                "type": "string",
                                "enum": [
                                    "none",
                                    "council_tax",
                                    "non_domestic_rates",
                                    "both",
                                ],
                            },
                            "sourceCodes": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "inactiveSourceCodes": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "matchedRecordCount": {"type": "integer"},
                            "inactiveRelevantRecordCount": {"type": "integer"},
                            "matches": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "xrefKey": {"type": ["string", "null"]},
                                        "crossReference": {"type": ["string", "null"]},
                                        "version": {"type": ["string", "null"]},
                                        "source": {"type": "string"},
                                        "sourceDescription": {"type": "string"},
                                        "startDate": {"type": ["string", "null"]},
                                        "endDate": {"type": ["string", "null"]},
                                        "lastUpdateDate": {"type": ["string", "null"]},
                                        "entryDate": {"type": ["string", "null"]},
                                        "active": {"type": "boolean"},
                                    },
                                    "required": ["source", "sourceDescription", "active"],
                                    "additionalProperties": False,
                                },
                            },
                        },
                        "required": [
                            "uprn",
                            "paysCouncilTax",
                            "paysBusinessRates",
                            "status",
                            "sourceCodes",
                            "inactiveSourceCodes",
                            "matchedRecordCount",
                            "inactiveRelevantRecordCount",
                            "matches",
                        ],
                        "additionalProperties": False,
                    },
                },
                "summary": {"type": "object"},
                "provenance": {"type": "object"},
            },
            "required": ["results", "summary", "provenance"],
            "additionalProperties": False,
        },
        handler=_uprn_query,
    )
)
