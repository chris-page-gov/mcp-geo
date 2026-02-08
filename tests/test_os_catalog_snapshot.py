from __future__ import annotations

import json
import os
import statistics
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pytest

from server.config import settings

_REQUIRED_ITEM_FIELDS = ("id", "kind", "category", "title", "description", "required", "request")
_REQUIRED_REQUEST_FIELDS = ("method", "url", "params")
_ALLOWED_METHODS = {"GET", "POST"}


def _resolve_catalog_path() -> Path:
    raw = getattr(settings, "OS_CATALOG_PATH", "resources/os_catalog.json")
    path = Path(raw)
    if not path.is_absolute():
        root = Path(__file__).resolve().parent.parent
        path = root / raw
    return path


def _load_catalog() -> tuple[Path, str, dict[str, Any]]:
    path = _resolve_catalog_path()
    assert path.exists(), f"OS catalog not found at {path}"
    text = path.read_text(encoding="utf-8")
    data = json.loads(text)
    assert isinstance(data, dict)
    return path, text, data


def _validate_item(entry: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = [field for field in _REQUIRED_ITEM_FIELDS if field not in entry]
    if missing:
        errors.append(f"missing fields {missing}")
        return errors

    item_id = entry.get("id")
    if not isinstance(item_id, str) or not item_id.strip():
        errors.append("id must be a non-empty string")

    for field in ("kind", "category", "title", "description"):
        value = entry.get(field)
        if not isinstance(value, str):
            errors.append(f"{field} must be a string")

    required = entry.get("required")
    if not isinstance(required, bool):
        errors.append("required must be boolean")

    request = entry.get("request")
    if not isinstance(request, dict):
        errors.append("request must be an object")
        return errors

    missing_req = [field for field in _REQUIRED_REQUEST_FIELDS if field not in request]
    if missing_req:
        errors.append(f"request missing fields {missing_req}")
        return errors

    method = request.get("method")
    if not isinstance(method, str) or method.upper() not in _ALLOWED_METHODS:
        errors.append(f"request.method must be one of {sorted(_ALLOWED_METHODS)}")

    url = request.get("url")
    if not isinstance(url, str) or not url.strip():
        errors.append("request.url must be a non-empty string")
    elif not url.startswith("https://api.os.uk/"):
        errors.append("request.url must start with https://api.os.uk/")

    params = request.get("params")
    if not isinstance(params, dict):
        errors.append("request.params must be an object")

    expects = entry.get("expects")
    if expects is not None:
        if not isinstance(expects, dict):
            errors.append("expects must be an object")
        else:
            statuses = expects.get("status")
            if not (isinstance(statuses, list) and statuses and all(isinstance(s, int) for s in statuses)):
                errors.append("expects.status must be a non-empty list of ints")
            ctp = expects.get("contentTypePrefix")
            if ctp is not None and not isinstance(ctp, str):
                errors.append("expects.contentTypePrefix must be a string when present")
            min_bytes = expects.get("minBytes")
            if min_bytes is not None and not isinstance(min_bytes, int):
                errors.append("expects.minBytes must be an int when present")

    docs = entry.get("docs")
    if docs is not None:
        if not isinstance(docs, list) or any(not isinstance(u, str) for u in docs):
            errors.append("docs must be a list of strings when present")
    return errors


def test_os_catalog_snapshot_structure() -> None:
    path, text, data = _load_catalog()
    assert "key=" not in text, f"OS catalog at {path} must not contain key= query params"
    assert data.get("placeholder") is False
    items = data.get("items")
    assert isinstance(items, list)

    min_items = int(os.getenv("OS_CATALOG_MIN_ITEMS", "150"))
    assert len(items) >= min_items

    ids: list[str] = []
    errors: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            errors.append("item is not an object")
            continue
        item_id = item.get("id")
        if isinstance(item_id, str) and item_id.strip():
            ids.append(item_id)
        errs = _validate_item(item)
        if errs:
            errors.append(f"{item_id}: {', '.join(errs)}")

    assert ids and len(set(ids)) == len(ids)
    assert not errors, f"OS catalog item validation failed: {errors[:10]}"


RUN_LIVE = os.getenv("RUN_LIVE_API_TESTS") == "1"
pytestmark_live = pytest.mark.skipif(not RUN_LIVE, reason="RUN_LIVE_API_TESTS=1 required")


def _call_os(
    url: str,
    *,
    api_key: str,
    method: str = "GET",
    params: dict[str, Any] | None = None,
    body: Any | None = None,
    timeout: float = 10.0,
) -> tuple[int, str, bytes, float]:
    merged = dict(params or {})
    if api_key:
        merged["key"] = api_key
    full_url = url
    if merged:
        full_url = f"{url}?{urlencode(merged)}"

    headers = {"User-Agent": "mcp-geo-os-catalog-live/0"}
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = Request(full_url, data=data, method=method, headers=headers)

    started = time.perf_counter()
    try:
        with urlopen(req, timeout=timeout) as resp:
            content = resp.read()
            elapsed = time.perf_counter() - started
            return resp.status, resp.headers.get("Content-Type", ""), content, elapsed
    except HTTPError as exc:
        content = exc.read()
        elapsed = time.perf_counter() - started
        return exc.code, exc.headers.get("Content-Type", ""), content, elapsed
    except (URLError, TimeoutError, OSError) as exc:
        elapsed = time.perf_counter() - started
        # Represent connection failures as a synthetic status code to avoid leaking full exception strings.
        return 0, "error/connection", str(exc).encode("utf-8")[:200], elapsed


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    if pct <= 0:
        return min(values)
    if pct >= 100:
        return max(values)
    values_sorted = sorted(values)
    k = (len(values_sorted) - 1) * (pct / 100.0)
    f = int(k)
    c = min(f + 1, len(values_sorted) - 1)
    if f == c:
        return values_sorted[f]
    d0 = values_sorted[f] * (c - k)
    d1 = values_sorted[c] * (k - f)
    return d0 + d1


@pytestmark_live
def test_os_catalog_covers_live_download_products() -> None:
    _path, _text, data = _load_catalog()
    items = data.get("items", [])
    snapshot_product_ids = {
        entry.get("meta", {}).get("productId")
        for entry in items
        if isinstance(entry, dict)
        and isinstance(entry.get("meta"), dict)
        and isinstance(entry.get("id"), str)
        and entry["id"].startswith("os.downloads.product.")
        and entry["id"].endswith(".meta")
    }
    snapshot_product_ids = {pid for pid in snapshot_product_ids if isinstance(pid, str) and pid.strip()}

    api_key = (getattr(settings, "OS_API_KEY", "") or os.getenv("OS_API_KEY", "")).strip()
    assert api_key, "OS_API_KEY is required for live OS catalog validation"

    status, _ct, body, _elapsed = _call_os(
        "https://api.os.uk/downloads/v1/products", api_key=api_key, method="GET"
    )
    assert status == 200
    live_products = json.loads(body)
    assert isinstance(live_products, list)
    live_ids = {
        item.get("id") for item in live_products if isinstance(item, dict) and item.get("id")
    }
    min_coverage = float(os.getenv("OS_LIVE_PRODUCTS_COVERAGE_MIN", "0.99"))
    missing = live_ids - snapshot_product_ids
    coverage = 1 - (len(missing) / max(len(live_ids), 1))
    assert (
        coverage >= min_coverage
    ), f"Downloads products coverage {coverage:.2%} < {min_coverage:.2%}; missing={sorted(list(missing))[:25]}"


@pytestmark_live
def test_os_catalog_covers_live_ngd_collections() -> None:
    _path, _text, data = _load_catalog()
    items = data.get("items", [])
    snapshot_collection_ids = {
        entry.get("meta", {}).get("collectionId")
        for entry in items
        if isinstance(entry, dict)
        and isinstance(entry.get("meta"), dict)
        and isinstance(entry.get("id"), str)
        and entry["id"].startswith("os.features.ngd.collection.")
        and entry["id"].endswith(".items")
    }
    snapshot_collection_ids = {
        cid for cid in snapshot_collection_ids if isinstance(cid, str) and cid.strip()
    }

    api_key = (getattr(settings, "OS_API_KEY", "") or os.getenv("OS_API_KEY", "")).strip()
    assert api_key, "OS_API_KEY is required for live OS catalog validation"

    status, _ct, body, _elapsed = _call_os(
        "https://api.os.uk/features/ngd/ofa/v1/collections", api_key=api_key, method="GET"
    )
    assert status == 200
    resp = json.loads(body)
    assert isinstance(resp, dict)
    collections = resp.get("collections", [])
    assert isinstance(collections, list)
    live_ids = {
        item.get("id") for item in collections if isinstance(item, dict) and item.get("id")
    }

    min_coverage = float(os.getenv("OS_LIVE_COLLECTIONS_COVERAGE_MIN", "0.99"))
    missing = live_ids - snapshot_collection_ids
    coverage = 1 - (len(missing) / max(len(live_ids), 1))
    assert (
        coverage >= min_coverage
    ), f"NGD collections coverage {coverage:.2%} < {min_coverage:.2%}; missing={sorted(list(missing))[:25]}"


@pytestmark_live
def test_os_live_catalog_probes_resolve() -> None:
    _path, _text, data = _load_catalog()
    items = [item for item in data.get("items", []) if isinstance(item, dict)]

    api_key = (getattr(settings, "OS_API_KEY", "") or os.getenv("OS_API_KEY", "")).strip()
    assert api_key, "OS_API_KEY is required for live OS catalog validation"

    throttle_seconds = float(os.getenv("OS_LIVE_THROTTLE_SECONDS", "0.2"))
    max_retries = int(os.getenv("OS_LIVE_MAX_RETRIES", "6"))
    backoff_base = float(os.getenv("OS_LIVE_BACKOFF_BASE", "2.0"))
    connect_max_retries = int(os.getenv("OS_LIVE_CONNECT_MAX_RETRIES", "2"))
    connect_backoff_base = float(os.getenv("OS_LIVE_CONNECT_BACKOFF_BASE", "0.5"))

    errors_required: list[str] = []
    errors_optional: list[str] = []
    rate_limits = 0
    auth_errors = 0
    connect_errors = 0
    other_errors = 0
    durations: list[float] = []
    ok_items = 0

    for entry in items:
        item_id = entry.get("id")
        if not isinstance(item_id, str) or not item_id.strip():
            continue
        request = entry.get("request")
        if not isinstance(request, dict):
            continue
        method = request.get("method") if isinstance(request.get("method"), str) else "GET"
        url = request.get("url")
        params = request.get("params") if isinstance(request.get("params"), dict) else {}
        body = request.get("body")
        required = entry.get("required") if isinstance(entry.get("required"), bool) else True

        expects = entry.get("expects") if isinstance(entry.get("expects"), dict) else {}
        expected_statuses = expects.get("status") if isinstance(expects.get("status"), list) else [200]
        content_type_prefix = expects.get("contentTypePrefix")
        min_bytes = expects.get("minBytes")

        if not isinstance(url, str) or not url.startswith("https://api.os.uk/"):
            continue

        last_status: int | None = None
        last_ct: str | None = None
        last_len: int | None = None
        ok = False

        for attempt in range(1, max_retries + 1):
            status, ct, content, elapsed = _call_os(
                url,
                api_key=api_key,
                method=method.upper(),
                params=params,
                body=body if "body" in request else None,
            )
            durations.append(elapsed)
            last_status = status
            last_ct = ct
            last_len = len(content)

            if status in expected_statuses:
                ok = True
                ok_items += 1
                if isinstance(content_type_prefix, str) and content_type_prefix:
                    if not (ct or "").startswith(content_type_prefix):
                        msg = f"{item_id}: content-type {ct!r} does not start with {content_type_prefix!r}"
                        (errors_required if required else errors_optional).append(msg)
                if isinstance(min_bytes, int) and min_bytes > 0:
                    if len(content) < min_bytes:
                        msg = f"{item_id}: body too small ({len(content)} bytes < {min_bytes})"
                        (errors_required if required else errors_optional).append(msg)
                # Light structure checks for JSON endpoints without leaking payload content.
                if (ct or "").startswith("application/json") or (ct or "").startswith(
                    "application/geo+json"
                ):
                    try:
                        parsed = json.loads(content)
                    except json.JSONDecodeError:
                        msg = f"{item_id}: invalid JSON payload"
                        (errors_required if required else errors_optional).append(msg)
                    else:
                        if item_id == "os.downloads.products":
                            if not isinstance(parsed, list) or len(parsed) < 10:
                                msg = f"{item_id}: unexpected products payload shape"
                                (errors_required if required else errors_optional).append(msg)
                        if item_id == "os.features.ngd.collections":
                            if not (
                                isinstance(parsed, dict)
                                and isinstance(parsed.get("collections"), list)
                                and len(parsed.get("collections", [])) >= 50
                            ):
                                msg = f"{item_id}: unexpected NGD collections payload shape"
                                (errors_required if required else errors_optional).append(msg)
                        if item_id.startswith("os.features.ngd.collection.") and item_id.endswith(
                            ".items"
                        ):
                            features = parsed.get("features") if isinstance(parsed, dict) else None
                            if features is None or not isinstance(features, list):
                                msg = f"{item_id}: unexpected NGD items payload shape"
                                (errors_required if required else errors_optional).append(msg)
                        if item_id == "os.maps.vector.vts.metadata":
                            tiles = parsed.get("tiles") if isinstance(parsed, dict) else None
                            if not (
                                isinstance(tiles, list)
                                and any(
                                    isinstance(tile, str) and "/vts/tile/{z}/{y}/{x}.pbf" in tile
                                    for tile in tiles
                                )
                            ):
                                msg = f"{item_id}: missing expected VTS tile template"
                                (errors_required if required else errors_optional).append(msg)
                break

            if status == 429:
                rate_limits += 1
                time.sleep(backoff_base * (2 ** (attempt - 1)))
                continue
            if status == 0 and attempt < min(max_retries, connect_max_retries):
                # Connection/read timeouts should be retried a couple of times, but avoid long backoffs
                # to keep unattended runs bounded.
                delay = min(connect_backoff_base * (2 ** (attempt - 1)), 2.0)
                time.sleep(delay)
                continue
            break

        if not ok:
            if last_status in (401, 403):
                auth_errors += 1
            elif last_status == 0:
                connect_errors += 1
            else:
                other_errors += 1
            msg = f"{item_id}: {last_status} ({last_ct}), bytes={last_len}"
            (errors_required if required else errors_optional).append(msg)

        if throttle_seconds > 0:
            time.sleep(throttle_seconds)

    total = len(items)
    p50 = _percentile(durations, 50)
    p95 = _percentile(durations, 95)
    mean = statistics.mean(durations) if durations else 0.0
    print(
        "OS live catalog probe summary: "
        f"items={total} ok={ok_items} rate_limits={rate_limits} auth_errors={auth_errors} "
        f"connect_errors={connect_errors} other_errors={other_errors} "
        f"latency_s(mean/p50/p95)={mean:.3f}/{p50:.3f}/{p95:.3f}"
    )

    if errors_required:
        pytest.fail(f"Required OS probe failures: {errors_required[:10]}")
