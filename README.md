# kagent-todo-app

A small todo app built by a kagent agent team (`team-lead`, `backend-dev`, `frontend-dev`, `devops`)
through pull requests a human reviews. This README is the spec. Issues are the backlog.

## What it does

A single-user todo list in the browser: add a todo, mark it done or open, delete it, set an optional due date,
filter by done/open. No login.

## Stack and layout

| Path | What |
|---|---|
| `app/main.py` | FastAPI app: the API under `/api`, `GET /healthz`, and the static frontend at `/` |
| `app/db.py` | SQLite access (standard library `sqlite3`); DB file path from env `TODO_DB_PATH`, default `./todo.db` |
| `app/static/index.html`, `app/static/app.js` | Plain HTML + JavaScript, no framework, no build step |
| `tests/test_api.py` | `pytest` + FastAPI `TestClient`, each test uses a temporary DB |
| `requirements.txt` | Pinned: `fastapi`, `uvicorn`, `pytest`, `httpx` |
| `Dockerfile` | `python:3.12-slim`, runs `uvicorn app.main:app --host 0.0.0.0 --port 8000` |
| `k8s/` | Namespace `todo`, Deployment, Service type NodePort `30080` → container port 8000 |
| `.github/workflows/build.yml` | On push to `master`: run tests, build and push `ghcr.io/srmarjani/kagent-todo-app:<sha>` and `:latest` |

## API

A todo is `{"id": int, "title": str, "done": bool, "due_date": "YYYY-MM-DD" | null}`.

| Method and path | Body | Returns |
|---|---|---|
| `GET /healthz` | | `200 {"status": "ok"}` |
| `GET /api/todos?status=all\|open\|done` | | `200` list, newest first; default `all` |
| `POST /api/todos` | `{"title": str, "due_date"?: str}` | `201` the new todo; `422` if title empty |
| `PATCH /api/todos/{id}` | any of `title`, `done`, `due_date` | `200` the updated todo; `404` if missing |
| `DELETE /api/todos/{id}` | | `204`; `404` if missing |

## Run locally

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload     # http://localhost:8000
pytest -q
```

## Rules for agents (and humans)

- One pull request per issue; the PR body says `Closes #<n>`, lists the files changed, and says how to test.
- Write complete files, never partial snippets or diffs.
- Never commit to `master` directly. Never merge your own PR.
- Keep it small: no new dependencies or files beyond what the issue asks for, unless the PR explains why.
- Every API change comes with a test in `tests/test_api.py`.
