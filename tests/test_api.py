import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    # Each test gets its own temporary DB path (used once app/db.py exists).
    monkeypatch.setenv("TODO_DB_PATH", str(tmp_path / "test.db"))
    with TestClient(app) as c:
        yield c


def test_healthz(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
