## Session 2026-04-16: PATCH /tasks/{id}

### Request
Add endpoint `PATCH /tasks/{id}`.

Requirements:
- update task name
- return updated task
- return `404` if task does not exist
- reject empty name
- keep changes minimal
- add tests

Process:
- planner
- coder
- tester
- reviewer

### Summary
Added `PATCH /tasks/{id}` to update a task title with minimal API surface change. The endpoint returns the updated task, maps missing tasks to `404`, and rejects empty or whitespace-only update payloads with standard FastAPI validation errors.

### Plan
1. Review current route and service patterns for task mutation and `404` handling.
2. Define missing tests for successful update, missing task, and empty title validation.
3. Implement the smallest service-layer update method and route handler.
4. Run tests and review for regressions.

### Test Plan
- Add `test_patch_task_updates_name`
- Add `test_patch_task_not_found`
- Add `test_patch_task_rejects_empty_name`
- Run `.venv/bin/pytest tests/test_tasks.py`

### File Ownership
- `planner`: no file changes
- `coder`: `app/routes/tasks.py`, `app/services/task_service.py`
- `tester`: `tests/test_tasks.py`
- main rollout: `docs/ai_sessions.md`

### Files Changed
- `app/routes/tasks.py`
- `app/services/task_service.py`
- `tests/test_tasks.py`
- `docs/ai_sessions.md`

### Implementation
- Added `TaskUpdate` request model with non-empty, whitespace-stripped validation.
- Added `PATCH /tasks/{task_id}` route returning the updated task.
- Added `TaskService.update_task(task_id, title)` in the service layer.
- Kept `POST /tasks` behavior unchanged after reviewer found an unrelated validation scope leak.

### Tests Run
- `.venv/bin/pytest tests/test_tasks.py`
- Result: `9 passed in 0.29s`

### Review
- Reviewer found one medium issue during implementation review: `TaskCreate` validation had been unintentionally tightened while adding PATCH validation.
- Fixed by restoring `TaskCreate.title` to its original unvalidated `str` type and keeping validation only on `TaskUpdate`.
- No remaining findings on the PATCH path itself.

### Residual Risks
- No explicit regression test proves `PATCH` preserves the `completed` field for an already completed task, though the implementation only mutates `title` and is low risk.

## Session 2026-04-16: Docker Run Verification

### Request
Make sure the project runs cleanly through Docker.

Requirements:
- verify Dockerfile
- verify docker-compose.yml
- ensure backend starts on port 8000
- ensure /health works
- update README run instructions if needed
- keep changes minimal

Process:
- planner
- coder
- tester
- reviewer

### Summary
Verified that the project already runs cleanly through Docker without code changes. The container starts `uvicorn` on `0.0.0.0:8000`, Compose exposes the app on `localhost:8001`, and `GET /health` returns `200 {"status":"ok"}`.

### Plan
1. Inspect Dockerfile, compose config, and README.
2. Verify build and runtime behavior through Docker Compose.
3. Confirm the app listens on port `8000` inside the container.
4. Confirm `/health` works through the mapped host port.
5. Change files only if runtime behavior and docs diverge.

### Test Plan
- `docker compose -f docker/docker-compose.yml up --build -d`
- `docker compose -f docker/docker-compose.yml ps`
- `docker logs docker-api-1`
- `curl -i http://localhost:8001/health`
- `.venv/bin/pytest tests/test_tasks.py -q`

### File Ownership
- `planner`: no file changes
- `coder`: `docker/Dockerfile`, `docker/docker-compose.yml`, `README.md`
- `tester`: read-only verification
- `reviewer`: no file changes
- main rollout: `docs/ai_sessions.md`

### Files Changed
- `docs/ai_sessions.md`

### Implementation
- No Docker code or documentation change was needed.
- Verified current behavior matches configuration and README:
  - container command binds `uvicorn` to `0.0.0.0:8000`
  - Compose maps host `8001` to container `8000`
  - README already documents the Docker run command and reachable URL

### Tests Run
- `docker compose -f docker/docker-compose.yml up --build -d`
- `docker compose -f docker/docker-compose.yml ps`
- `docker logs docker-api-1`
- `curl -i http://localhost:8001/health`
- `.venv/bin/pytest tests/test_tasks.py -q`

### Review
- No findings.
- Dockerfile, compose file, and README are aligned with the verified runtime behavior.

### Residual Risks
- Compose does not expose host port `8000` in this environment because that port is already occupied.
- The correct claim is: the app listens on port `8000` inside the container and runs cleanly through Compose on `http://localhost:8001`.

## Session 2026-04-16: SQLite Persistence

### Request
Replace in-memory task storage with SQLite persistence.

Requirements:
- preserve current API behavior
- keep changes minimal
- store tasks in SQLite
- support create, list, get, patch, complete, delete
- add or update tests
- update README if needed

Process:
- planner
- coder
- tester
- reviewer

### Summary
Replaced in-memory storage with SQLite persistence behind the existing service boundary using the standard library `sqlite3`. The API contract stayed the same for create, list, get, patch, complete, and delete, while data now persists to `tasks.db` by default.

### Plan
1. Keep route behavior unchanged and swap persistence behind the service layer.
2. Preserve a simple reset hook for test isolation.
3. Add or adapt tests to cover GET behavior and SQLite-backed persistence.
4. Update README to document SQLite storage and the full API contract.

### Test Plan
- Keep existing CRUD endpoint tests passing.
- Add `test_get_task`.
- Add `test_get_task_not_found`.
- Add `test_tasks_persist_between_requests_within_app_instance`.
- Add a focused check that persistence survives service re-instantiation.
- Run `.venv/bin/pytest tests/test_tasks.py`.

### File Ownership
- `planner`: no file changes
- `coder`: `app/services/task_service.py`
- `tester`: `tests/test_tasks.py`, `tests/conftest.py` only if needed
- main rollout: `README.md`, `docs/ai_sessions.md`

### Files Changed
- `app/services/task_service.py`
- `tests/test_tasks.py`
- `README.md`
- `docs/ai_sessions.md`

### Implementation
- Replaced list-based in-memory storage with SQLite in `TaskService`.
- Added automatic table initialization and kept `task_service.reset()` for per-test cleanup.
- Preserved the existing service API for create, list, get, patch, complete, and delete.
- Default database path is `tasks.db`, overridable via `TASKS_DB_PATH`.

### Tests Run
- `.venv/bin/pytest tests/test_tasks.py`
- Result: `13 passed in 0.44s`

### Review
- Reviewer found README drift after the storage change:
  - it still claimed in-memory storage
  - it omitted `GET /tasks/{id}`, `PATCH /tasks/{id}`, and `DELETE /tasks/{id}`
- Reviewer also noted missing proof of persistence across service/process re-instantiation.
- Fixed by updating README and adding `test_tasks_persist_across_service_reinstantiation`.

### Residual Risks
- Default persistence path is relative (`tasks.db`), so exact file location depends on the working directory unless `TASKS_DB_PATH` is set.
- Under Docker, SQLite data remains in the container filesystem unless a volume is added later.
