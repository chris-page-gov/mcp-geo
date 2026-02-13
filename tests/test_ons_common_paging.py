from typing import Any, Dict, Tuple

from tools.ons_common import ONSClient


def test_get_all_pages_with_next_link(monkeypatch):
    client = ONSClient()
    calls = {"n": 0}

    def fake_get_json(url: str, params: Dict[str, Any] | None = None, use_cache: bool = True) -> Tuple[int, Dict[str, Any]]:  # noqa: ARG001
        calls["n"] += 1
        if calls["n"] == 1:
            return 200, {
                "items": [{"id": "a"}],
                "links": [{"rel": "next", "href": "/next"}],
            }
        return 200, {"items": [{"id": "b"}]}

    monkeypatch.setattr(client, "get_json", fake_get_json)
    status, items = client.get_all_pages("https://example.com/base", params={"limit": 1, "page": 1})
    assert status == 200
    assert [i["id"] for i in items] == ["a", "b"]


def test_get_all_pages_limit_break(monkeypatch):
    client = ONSClient()

    def fake_get_json(url: str, params: Dict[str, Any] | None = None, use_cache: bool = True) -> Tuple[int, Dict[str, Any]]:  # noqa: ARG001
        return 200, {"items": [{"id": "a"}], "total": 1, "limit": 10}

    monkeypatch.setattr(client, "get_json", fake_get_json)
    status, items = client.get_all_pages("https://example.com/base", params={"limit": 10, "page": 1})
    assert status == 200
    assert items[0]["id"] == "a"
