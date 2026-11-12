from fastapi import FastAPI

app = FastAPI(title="kagent-todo-app")


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}
