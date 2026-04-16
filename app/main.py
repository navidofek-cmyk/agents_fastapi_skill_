from fastapi import FastAPI

from app.routes.tasks import router as tasks_router


app = FastAPI(title="Task API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(tasks_router)
