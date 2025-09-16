import pytest
from fastapi.testclient import TestClient

from server.main import app

@pytest.fixture(scope="session")
def client():
    return TestClient(app)