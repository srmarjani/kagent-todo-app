import os
import sqlite3
from contextlib import closing
from typing import Optional


def get_db_path() -> str:
    return os.environ.get("TODO_DB_PATH", "./todo.db")


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with closing(_connect()) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                done INTEGER NOT NULL DEFAULT 0,
                due_date TEXT
            )
            """
        )
        conn.commit()


def _row_to_todo(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "title": row["title"],
        "done": bool(row["done"]),
        "due_date": row["due_date"],
    }


def list_todos(status: str = "all") -> list:
    query = "SELECT id, title, done, due_date FROM todos"
    if status == "open":
        query += " WHERE done = 0"
    elif status == "done":
        query += " WHERE done = 1"
    query += " ORDER BY id DESC"
    with closing(_connect()) as conn:
        rows = conn.execute(query).fetchall()
    return [_row_to_todo(r) for r in rows]


def get_todo(todo_id: int) -> Optional[dict]:
    with closing(_connect()) as conn:
        row = conn.execute(
            "SELECT id, title, done, due_date FROM todos WHERE id = ?", (todo_id,)
        ).fetchone()
    return _row_to_todo(row) if row else None


def create_todo(title: str, due_date: Optional[str] = None) -> dict:
    with closing(_connect()) as conn:
        cur = conn.execute(
            "INSERT INTO todos (title, done, due_date) VALUES (?, 0, ?)",
            (title, due_date),
        )
        conn.commit()
        todo_id = cur.lastrowid
    return get_todo(todo_id)


def update_todo(todo_id: int, changes: dict) -> Optional[dict]:
    """Apply the given column changes (title, done, due_date). Returns the
    updated todo, or None if the id does not exist."""
    if get_todo(todo_id) is None:
        return None
    allowed = {"title", "done", "due_date"}
    columns = [c for c in changes if c in allowed]
    if columns:
        values = [int(changes[c]) if c == "done" else changes[c] for c in columns]
        assignments = ", ".join(f"{c} = ?" for c in columns)
        with closing(_connect()) as conn:
            conn.execute(
                f"UPDATE todos SET {assignments} WHERE id = ?",
                (*values, todo_id),
            )
            conn.commit()
    return get_todo(todo_id)


def delete_todo(todo_id: int) -> bool:
    with closing(_connect()) as conn:
        cur = conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
        conn.commit()
        return cur.rowcount > 0


def delete_done_todos() -> int:
    """Delete every todo with done = 1. Returns how many rows were deleted."""
    with closing(_connect()) as conn:
        cur = conn.execute("DELETE FROM todos WHERE done = 1")
        conn.commit()
        return cur.rowcount
