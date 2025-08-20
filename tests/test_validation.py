import httpx
import pytest

BASE_URL = "http://localhost:8000"

def call(endpoint, method="get", **kwargs):
    url = f"{BASE_URL}{endpoint}"
    resp = getattr(httpx, method)(url, **kwargs)
    return resp

# Example: test harness for validation

def test_healthz():
    resp = call("/healthz")
    assert resp.status_code == 200
    assert resp.json().get("ok") is True

def test_tools_list():
    resp = call("/tools/list")
    assert resp.status_code == 200
    data = resp.json()
    assert "tools" in data
    assert isinstance(data["tools"], list)
    assert "nextPageToken" in data

def test_resources_list():
    resp = call("/resources/list")
    assert resp.status_code == 200
    data = resp.json()
    assert "resources" in data
    assert isinstance(data["resources"], list)
    assert "nextPageToken" in data

def test_error_model():
    # Simulate error by calling a non-existent endpoint
    resp = call("/nonexistent")
    assert resp.status_code == 404 or resp.json().get("isError")

# Add more validation tests for each epic before implementation
