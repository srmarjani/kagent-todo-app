import re
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path
from typing import Any, Literal, Optional

from fastapi import FastAPI, HTTPException, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator

from app import db

STATIC_DIR = Path(__file__).parent / "static"

DATE_PATTERN = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")


@asynccontextmanager
async def lifespan(_: FastAPI):
    db.init_db()
    yield


app = FastAPI(title="kagent-todo-app", lifespan=lifespan)


def _clean_title(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("title must not be empty")
    return value


def _parse_due_date(value: Any) -> Optional[date]:
    """Accept only null or a real calendar date written exactly as YYYY-MM-DD."""
    if value is None:
        return None
    if not isinstance(value, str) or not DATE_PATTERN.fullmatch(value):
        raise ValueError("due_date must be YYYY-MM-DD or null")
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValueError("due_date must be a valid date in YYYY-MM-DD format")


class TodoCreate(BaseModel):
    title: str
    due_date: Optional[date] = None

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, value: str) -> str:
        return _clean_title(value)

    @field_validator("due_date", mode="before")
    @classmethod
    def due_date_format(cls, value: Any) -> Optional[date]:
        return _parse_due_date(value)


class TodoUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None
    due_date: Optional[date] = None

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            raise ValueError("title must not be null")
        return _clean_title(value)

    @field_validator("done")
    @classmethod
    def done_not_null(cls, value: Optional[bool]) -> Optional[bool]:
        if value is None:
            raise ValueError("done must not be null")
        return value

    @field_validator("due_date", mode="before")
    @classmethod
    def due_date_format(cls, value: Any) -> Optional[date]:
        return _parse_due_date(value)


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}


@app.get("/api/todos")
def list_todos(status: Literal["all", "open", "done"] = "all") -> list:
    return db.list_todos(status)


@app.post("/api/todos", status_code=201)
def create_todo(body: TodoCreate) -> dict:
    due = body.due_date.isoformat() if body.due_date else None
    return db.create_todo(body.title, due)


@app.patch("/api/todos/{todo_id}")
def update_todo(todo_id: int, body: TodoUpdate) -> dict:
    changes = {}
    for name in body.model_fields_set:
        value = getattr(body, name)
        if name == "due_date" and value is not None:
            value = value.isoformat()
        changes[name] = value
    todo = db.update_todo(todo_id, changes)
    if todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo


@app.delete("/api/todos/{todo_id}", status_code=204)
def delete_todo(todo_id: int) -> Response:
    if not db.delete_todo(todo_id):
        raise HTTPException(status_code=404, detail="Todo not found")
    return Response(status_code=204)


# Mounted last so the /api and /healthz routes above take precedence.
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
