from __future__ import annotations

from fastapi.testclient import TestClient

from server.main import app

client = TestClient(app)


def test_os_downloads_list_products_paging(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from tools import os_downloads

    os_downloads._EXPORT_STORE.clear()

    def fake_get_json(url: str, params=None):
        if url.endswith("/downloads/v1/products"):
            return 200, [{"id": "a"}, {"id": "b"}, {"id": "c"}]
        return 200, []

    monkeypatch.setattr(os_downloads.client, "get_json", fake_get_json, raising=True)

    resp = client.post(
        "/tools/call",
        json={"tool": "os_downloads.list_products", "limit": 2, "pageToken": 1},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 2
    assert body["total"] == 3
    assert body["products"][0]["id"] == "b"
    assert body["nextPageToken"] is None


def test_os_downloads_prepare_and_get_export(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from tools import os_downloads

    os_downloads._EXPORT_STORE.clear()

    def fake_get_json(url: str, params=None):
        if url.endswith("/downloads/v1/products/openroads/downloads"):
            return 200, [
                {"id": "d1", "fileName": "openroads-1.zip"},
                {"id": "d2", "fileName": "openroads-2.zip"},
            ]
        return 200, []

    def fake_write_resource_payload(prefix: str, payload: dict):
        return {
            "resourceUri": f"resource://mcp-geo/os-exports/{prefix}.json",
            "bytes": 123,
            "sha256": "abc123",
            "path": "/tmp/fake-os-export.json",
        }

    monkeypatch.setattr(os_downloads.client, "get_json", fake_get_json, raising=True)
    monkeypatch.setattr(
        os_downloads,
        "write_resource_payload",
        fake_write_resource_payload,
        raising=True,
    )

    prepare = client.post(
        "/tools/call",
        json={
            "tool": "os_downloads.prepare_export",
            "productId": "openroads",
            "delivery": "resource",
        },
    )
    assert prepare.status_code == 200
    prepare_body = prepare.json()
    assert prepare_body["delivery"] == "resource"
    assert prepare_body["resourceUri"].startswith("resource://mcp-geo/os-exports/")
    export_id = prepare_body["exportId"]

    get_inline = client.post(
        "/tools/call",
        json={"tool": "os_downloads.get_export", "exportId": export_id, "delivery": "inline"},
    )
    assert get_inline.status_code == 200
    get_inline_body = get_inline.json()
    assert get_inline_body["delivery"] == "inline"
    assert get_inline_body["export"]["productId"] == "openroads"


def test_os_downloads_product_downloads_resource_fallback(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from tools import os_downloads

    def fake_get_json(url: str, params=None):
        if url.endswith("/downloads/v1/products/openroads/downloads"):
            return 200, [{"id": "d1", "fileName": "openroads-1.zip"}]
        return 200, []

    def fake_write_resource_payload(prefix: str, payload: dict):
        return {
            "resourceUri": f"resource://mcp-geo/os-exports/{prefix}.json",
            "bytes": 123,
            "sha256": "abc123",
            "path": "/tmp/fake-os-export.json",
        }

    monkeypatch.setattr(os_downloads.client, "get_json", fake_get_json, raising=True)
    monkeypatch.setattr(
        os_downloads,
        "write_resource_payload",
        fake_write_resource_payload,
        raising=True,
    )

    resp = client.post(
        "/tools/call",
        json={
            "tool": "os_downloads.list_product_downloads",
            "productId": "openroads",
            "delivery": "resource",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["delivery"] == "resource"
    assert body["resourceUri"].startswith("resource://mcp-geo/os-exports/")


def test_os_downloads_list_data_packages_inline_and_invalid(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from tools import os_downloads

    def fake_get_json(url: str, params=None):
        if url.endswith("/downloads/v1/dataPackages"):
            return 200, [{"id": "pkg-1"}]
        return 200, []

    monkeypatch.setattr(os_downloads.client, "get_json", fake_get_json, raising=True)

    ok = client.post("/tools/call", json={"tool": "os_downloads.list_data_packages"})
    assert ok.status_code == 200
    ok_body = ok.json()
    assert ok_body["delivery"] == "inline"
    assert ok_body["count"] == 1

    bad = client.post(
        "/tools/call",
        json={"tool": "os_downloads.list_data_packages", "delivery": "bad-mode"},
    )
    assert bad.status_code == 400
    assert bad.json()["code"] == "INVALID_INPUT"


def test_os_downloads_internal_list_products_branches(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from tools import os_downloads

    def fake_get_json(_url: str, _params=None):
        return 200, [
            {"id": "openroads", "name": "Open Roads"},
            {"id": "openuprn", "description": "UPRN source"},
            "skip-me",
        ]

    monkeypatch.setattr(os_downloads.client, "get_json", fake_get_json, raising=True)

    code, body = os_downloads._list_products({"q": "roads", "limit": 1, "pageToken": ""})
    assert code == 200
    assert body["count"] == 1
    assert body["products"][0]["id"] == "openroads"

    code, body = os_downloads._list_products({"limit": 0})
    assert code == 400
    assert body["code"] == "INVALID_INPUT"

    code, body = os_downloads._list_products({"limit": 1, "pageToken": "bad-token"})
    assert code == 400
    assert body["code"] == "INVALID_INPUT"


def test_os_downloads_internal_error_paths(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from tools import os_downloads

    os_downloads._EXPORT_STORE.clear()

    monkeypatch.setattr(
        os_downloads.client,
        "get_json",
        lambda _url, _params=None: (503, {"isError": True, "code": "UPSTREAM_CONNECT_ERROR"}),
        raising=True,
    )
    code, body = os_downloads._list_products({})
    assert code == 503
    assert body["code"] == "UPSTREAM_CONNECT_ERROR"

    monkeypatch.setattr(
        os_downloads.client,
        "get_json",
        lambda _url, _params=None: (200, {}),
        raising=True,
    )
    code, body = os_downloads._list_products({})
    assert code == 500
    assert body["code"] == "INTEGRATION_ERROR"

    code, body = os_downloads._get_product({})
    assert code == 400
    assert body["code"] == "INVALID_INPUT"

    monkeypatch.setattr(
        os_downloads.client,
        "get_json",
        lambda _url, _params=None: (200, []),
        raising=True,
    )
    code, body = os_downloads._get_product({"productId": "openroads"})
    assert code == 500
    assert body["code"] == "INTEGRATION_ERROR"

    monkeypatch.setattr(
        os_downloads.client,
        "get_json",
        lambda _url, _params=None: (200, {}),
        raising=True,
    )
    code, body = os_downloads._list_product_downloads({"productId": "openroads"})
    assert code == 500
    assert body["code"] == "INTEGRATION_ERROR"

    monkeypatch.setattr(
        os_downloads.client,
        "get_json",
        lambda _url, _params=None: (200, []),
        raising=True,
    )
    code, body = os_downloads._list_product_downloads(
        {"productId": "openroads", "delivery": "bad"}
    )
    assert code == 400
    assert body["code"] == "INVALID_INPUT"

    code, body = os_downloads._list_product_downloads(
        {"productId": "openroads", "inlineMaxBytes": 0}
    )
    assert code == 400
    assert body["code"] == "INVALID_INPUT"

    code, body = os_downloads._list_product_downloads({"productId": "openroads", "offset": -1})
    assert code == 400
    assert body["code"] == "INVALID_INPUT"

    monkeypatch.setattr(
        os_downloads.client,
        "get_json",
        lambda _url, _params=None: (200, {}),
        raising=True,
    )
    code, body = os_downloads._list_data_packages({})
    assert code == 500
    assert body["code"] == "INTEGRATION_ERROR"


def test_os_downloads_prepare_and_get_export_internal_paths(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from tools import os_downloads

    os_downloads._EXPORT_STORE.clear()

    code, body = os_downloads._prepare_export({})
    assert code == 400
    assert body["code"] == "INVALID_INPUT"

    code, body = os_downloads._prepare_export({"productId": "openroads", "filenameContains": 123})
    assert code == 400
    assert body["code"] == "INVALID_INPUT"

    monkeypatch.setattr(
        os_downloads.client,
        "get_json",
        lambda _url, _params=None: (200, {"not": "list"}),
        raising=True,
    )
    code, body = os_downloads._prepare_export({"productId": "openroads"})
    assert code == 500
    assert body["code"] == "INTEGRATION_ERROR"

    monkeypatch.setattr(
        os_downloads.client,
        "get_json",
        lambda _url, _params=None: (200, [{"id": "d1", "fileName": "roads.zip"}, "skip"]),
        raising=True,
    )
    code, body = os_downloads._prepare_export(
        {
            "productId": "openroads",
            "filenameContains": "roads",
            "delivery": "inline",
            "inlineMaxBytes": 999999,
        }
    )
    assert code == 200
    assert body["delivery"] == "inline"
    assert body["bytes"] > 0
    export_id = body["exportId"]

    code, body = os_downloads._get_export({})
    assert code == 400
    assert body["code"] == "INVALID_INPUT"

    code, body = os_downloads._get_export({"exportId": "missing-id"})
    assert code == 404
    assert body["code"] == "NOT_FOUND"

    os_downloads._EXPORT_STORE["bad-export"] = {"payload": "not-a-dict"}
    code, body = os_downloads._get_export({"exportId": "bad-export"})
    assert code == 500
    assert body["code"] == "INTEGRATION_ERROR"

    calls = {"n": 0}

    def fake_write_resource_payload(prefix: str, payload: dict):
        calls["n"] += 1
        return {
            "resourceUri": f"resource://mcp-geo/os-exports/{prefix}.json",
            "bytes": 120,
            "sha256": "abc",
            "path": "/tmp/export.json",
        }

    monkeypatch.setattr(
        os_downloads,
        "write_resource_payload",
        fake_write_resource_payload,
        raising=True,
    )
    code, body = os_downloads._get_export(
        {"exportId": export_id, "delivery": "resource", "inlineMaxBytes": 1}
    )
    assert code == 200
    assert body["delivery"] == "resource"
    assert body["resourceUri"].startswith("resource://mcp-geo/os-exports/")
    assert calls["n"] == 1

    code, body = os_downloads._get_export({"exportId": export_id, "delivery": "bad"})
    assert code == 400
    assert body["code"] == "INVALID_INPUT"

    code, body = os_downloads._get_export({"exportId": export_id, "inlineMaxBytes": 0})
    assert code == 400
    assert body["code"] == "INVALID_INPUT"


def test_os_downloads_expiry_iso_none_when_ttl_not_positive(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from tools import os_downloads

    monkeypatch.setattr(os_downloads.settings, "OS_DATA_CACHE_TTL", 0, raising=False)
    assert os_downloads._expiry_iso(1700000000.0) is None
