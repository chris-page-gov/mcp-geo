import json
from typing import Any


def resource_contents(resp) -> list[dict[str, Any]]:
    body = resp.json()
    contents = body.get("contents")
    if not isinstance(contents, list) or not contents:
        raise AssertionError("Expected non-empty contents in resource response")
    return contents


def resource_json(resp) -> dict[str, Any]:
    contents = resource_contents(resp)
    text = contents[0].get("text")
    if not isinstance(text, str):
        raise AssertionError("Expected text content in resource response")
    return json.loads(text)
