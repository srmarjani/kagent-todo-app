import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    # Each test gets its own temporary DB.
    monkeypatch.setenv("TODO_DB_PATH", str(tmp_path / "test.db"))
    with TestClient(app) as c:
        yield c


def test_healthz(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_todo(client):
    response = client.post("/api/todos", json={"title": "Buy milk"})
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Buy milk"
    assert body["done"] is False
    assert body["due_date"] is None
    assert isinstance(body["id"], int)


def test_create_todo_with_due_date(client):
    response = client.post(
        "/api/todos", json={"title": "Pay rent", "due_date": "2030-01-31"}
    )
    assert response.status_code == 201
    assert response.json()["due_date"] == "2030-01-31"


def test_list_todos_newest_first(client):
    client.post("/api/todos", json={"title": "first"})
    client.post("/api/todos", json={"title": "second"})
    response = client.get("/api/todos")
    assert response.status_code == 200
    assert [t["title"] for t in response.json()] == ["second", "first"]


def test_list_todos_empty(client):
    response = client.get("/api/todos")
    assert response.status_code == 200
    assert response.json() == []


def test_list_todos_status_filter(client):
    open_id = client.post("/api/todos", json={"title": "open one"}).json()["id"]
    done_id = client.post("/api/todos", json={"title": "done one"}).json()["id"]
    client.patch(f"/api/todos/{done_id}", json={"done": True})

    open_ids = [t["id"] for t in client.get("/api/todos?status=open").json()]
    done_ids = [t["id"] for t in client.get("/api/todos?status=done").json()]
    all_ids = [t["id"] for t in client.get("/api/todos?status=all").json()]

    assert open_ids == [open_id]
    assert done_ids == [done_id]
    assert all_ids == [done_id, open_id]


def test_list_todos_invalid_status(client):
    assert client.get("/api/todos?status=bogus").status_code == 422


def test_toggle_done(client):
    todo_id = client.post("/api/todos", json={"title": "toggle me"}).json()["id"]

    response = client.patch(f"/api/todos/{todo_id}", json={"done": True})
    assert response.status_code == 200
    assert response.json()["done"] is True

    response = client.patch(f"/api/todos/{todo_id}", json={"done": False})
    assert response.status_code == 200
    assert response.json()["done"] is False


def test_patch_title_and_due_date(client):
    todo_id = client.post("/api/todos", json={"title": "old"}).json()["id"]

    response = client.patch(
        f"/api/todos/{todo_id}", json={"title": "new", "due_date": "2030-05-05"}
    )
    assert response.status_code == 200
    assert response.json()["title"] == "new"
    assert response.json()["due_date"] == "2030-05-05"

    # Setting due_date to null clears it; other fields are untouched.
    response = client.patch(f"/api/todos/{todo_id}", json={"due_date": None})
    assert response.status_code == 200
    assert response.json()["due_date"] is None
    assert response.json()["title"] == "new"


def test_patch_empty_title_422(client):
    todo_id = client.post("/api/todos", json={"title": "keep"}).json()["id"]
    response = client.patch(f"/api/todos/{todo_id}", json={"title": ""})
    assert response.status_code == 422


def test_patch_missing_id_404(client):
    response = client.patch("/api/todos/9999", json={"done": True})
    assert response.status_code == 404


def test_delete_todo(client):
    todo_id = client.post("/api/todos", json={"title": "delete me"}).json()["id"]

    response = client.delete(f"/api/todos/{todo_id}")
    assert response.status_code == 204
    assert response.content == b""
    assert client.get("/api/todos").json() == []


def test_delete_missing_id_404(client):
    response = client.delete("/api/todos/9999")
    assert response.status_code == 404


def test_create_empty_title_422(client):
    assert client.post("/api/todos", json={"title": ""}).status_code == 422
    assert client.post("/api/todos", json={"title": "   "}).status_code == 422
    assert client.post("/api/todos", json={}).status_code == 422


def test_create_invalid_due_date_422(client):
    response = client.post(
        "/api/todos", json={"title": "bad date", "due_date": "not-a-date"}
    )
    assert response.status_code == 422
