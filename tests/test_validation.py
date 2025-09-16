
def call(client, endpoint, method="get", **kwargs):
    return getattr(client, method)(endpoint, **kwargs)

# Example: test harness for validation

def test_healthz(client):
    resp = call(client, "/healthz")
    assert resp.status_code == 200
    assert resp.json().get("status") == "OK"

def test_tools_list(client):
    resp = call(client, "/tools/list")
    assert resp.status_code == 200
    data = resp.json()
    assert "tools" in data
    assert isinstance(data["tools"], list)
    assert "nextPageToken" in data

def test_resources_list(client):
    resp = call(client, "/resources/list")
    assert resp.status_code == 200
    data = resp.json()
    assert "resources" in data
    assert isinstance(data["resources"], list)
    assert "nextPageToken" in data

def test_error_model(client):
    resp = call(client, "/nonexistent")
    assert resp.status_code == 404 or resp.json().get("isError")

# Add more validation tests for each epic before implementation
