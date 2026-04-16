# Task API

Simple FastAPI backend with SQLite task persistence, pytest coverage, Docker support, and Codex agent workflow files.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API will be available at `http://localhost:8000`.

By default, tasks are stored in a local SQLite database file at `tasks.db`. You can override the path with the `TASKS_DB_PATH` environment variable.

## Run tests

```bash
pytest
```

## Run tests in Docker

```bash
docker compose -f docker/docker-compose.yml run --rm api pytest
```

## Run with Docker

```bash
docker compose -f docker/docker-compose.yml up --build
```

With the provided compose file, the API is exposed on `http://localhost:8001`.

The app listens on port `8000` inside the container. The default Docker run stores data in the container filesystem unless you add a volume.

## Endpoints

- `GET /health`
- `POST /tasks`
- `GET /tasks`
- `GET /tasks/{id}`
- `PATCH /tasks/{id}`
- `DELETE /tasks/{id}`
- `POST /tasks/{id}/complete`
