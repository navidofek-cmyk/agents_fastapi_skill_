import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.services.task_service import TaskService, task_service


client = TestClient(app)


def setup_function() -> None:
    task_service.reset()


def assert_task_timestamps(task: dict[str, object]) -> None:
    assert isinstance(task["created_at"], str)
    assert isinstance(task["updated_at"], str)
    assert task["created_at"]
    assert task["updated_at"]


def test_create_task() -> None:
    response = client.post("/tasks", json={"title": "Write tests"})

    assert response.status_code == 201
    payload = response.json()
    assert payload["id"] == 1
    assert payload["title"] == "Write tests"
    assert payload["completed"] is False
    assert_task_timestamps(payload)
    assert payload["created_at"] == payload["updated_at"]


def test_list_tasks() -> None:
    client.post("/tasks", json={"title": "First"})
    client.post("/tasks", json={"title": "Second"})

    response = client.get("/tasks")

    assert response.status_code == 200
    payload = response.json()
    assert [task["id"] for task in payload] == [1, 2]
    assert [task["title"] for task in payload] == ["First", "Second"]
    assert [task["completed"] for task in payload] == [False, False]
    for task in payload:
        assert_task_timestamps(task)


def test_get_task() -> None:
    created = client.post("/tasks", json={"title": "Fetch me"})

    response = client.get(f"/tasks/{created.json()['id']}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == 1
    assert payload["title"] == "Fetch me"
    assert payload["completed"] is False
    assert_task_timestamps(payload)


def test_get_task_not_found() -> None:
    response = client.get("/tasks/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found"}


def test_tasks_persist_between_requests_within_app_instance() -> None:
    client.post("/tasks", json={"title": "Persist me"})

    list_response = client.get("/tasks")
    get_response = client.get("/tasks/1")

    assert list_response.status_code == 200
    assert [task["title"] for task in list_response.json()] == ["Persist me"]
    assert get_response.status_code == 200
    assert get_response.json()["title"] == "Persist me"


def test_tasks_persist_across_service_reinstantiation(tmp_path: Path) -> None:
    db_path = tmp_path / "tasks.sqlite"
    first_service = TaskService(str(db_path))
    first_service.reset()
    created = first_service.create_task("Persist after restart")

    second_service = TaskService(str(db_path))

    payload = second_service.get_task(created["id"])
    assert payload["id"] == created["id"]
    assert payload["title"] == "Persist after restart"
    assert payload["completed"] is False
    assert_task_timestamps(payload)


def test_migrates_legacy_sqlite_table_without_timestamps(tmp_path: Path) -> None:
    db_path = tmp_path / "legacy.sqlite"
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                completed INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        connection.execute(
            "INSERT INTO tasks (title, completed) VALUES (?, ?)",
            ("Legacy task", 1),
        )
        connection.commit()

    migrated_service = TaskService(str(db_path))

    payload = migrated_service.get_task(1)
    assert payload["title"] == "Legacy task"
    assert payload["completed"] is True
    assert_task_timestamps(payload)
    assert payload["created_at"] == payload["updated_at"]


def test_migrates_sqlite_table_with_created_at_but_missing_updated_at(tmp_path: Path) -> None:
    db_path = tmp_path / "partial-legacy.sqlite"
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                completed INTEGER NOT NULL DEFAULT 0,
                created_at TEXT
            )
            """
        )
        connection.execute(
            "INSERT INTO tasks (title, completed, created_at) VALUES (?, ?, ?)",
            ("Partially migrated task", 0, "2026-01-01T00:00:00+00:00"),
        )
        connection.commit()

    migrated_service = TaskService(str(db_path))

    payload = migrated_service.get_task(1)
    assert payload["title"] == "Partially migrated task"
    assert payload["completed"] is False
    assert payload["created_at"] == "2026-01-01T00:00:00+00:00"
    assert isinstance(payload["updated_at"], str)
    assert payload["updated_at"]


def test_complete_task() -> None:
    created = client.post("/tasks", json={"title": "Ship feature"})

    response = client.post(f"/tasks/{created.json()['id']}/complete")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == 1
    assert payload["title"] == "Ship feature"
    assert payload["completed"] is True
    assert_task_timestamps(payload)


def test_complete_task_only_updates_target_task() -> None:
    first = client.post("/tasks", json={"title": "First"})
    second = client.post("/tasks", json={"title": "Second"})

    response = client.post(f"/tasks/{second.json()['id']}/complete")

    assert response.status_code == 200
    assert response.json()["completed"] is True
    payload = client.get("/tasks").json()
    assert [(task["title"], task["completed"]) for task in payload] == [
        ("First", False),
        ("Second", True),
    ]


def test_delete_task() -> None:
    created = client.post("/tasks", json={"title": "Remove me"})

    response = client.delete(f"/tasks/{created.json()['id']}")

    assert response.status_code == 204
    assert response.content == b""
    assert client.get("/tasks").json() == []


def test_delete_task_only_removes_target_task() -> None:
    first = client.post("/tasks", json={"title": "Keep me"})
    second = client.post("/tasks", json={"title": "Delete me"})
    third = client.post("/tasks", json={"title": "Keep me too"})

    response = client.delete(f"/tasks/{second.json()['id']}")

    assert response.status_code == 204
    payload = client.get("/tasks").json()
    assert [(task["id"], task["title"], task["completed"]) for task in payload] == [
        (first.json()["id"], "Keep me", False),
        (third.json()["id"], "Keep me too", False),
    ]
    for task in payload:
        assert_task_timestamps(task)


def test_delete_task_not_found() -> None:
    response = client.delete("/tasks/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found"}


def test_patch_task_updates_name() -> None:
    created = client.post("/tasks", json={"title": "Old title"})

    response = client.patch(f"/tasks/{created.json()['id']}", json={"title": "New title"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == 1
    assert payload["title"] == "New title"
    assert payload["completed"] is False
    assert_task_timestamps(payload)
    assert payload["updated_at"] >= payload["created_at"]
    assert client.get("/tasks").json()[0]["title"] == "New title"


def test_patch_task_only_updates_target_task() -> None:
    first = client.post("/tasks", json={"title": "Stay the same"})
    second = client.post("/tasks", json={"title": "Rename me"})

    response = client.patch(f"/tasks/{second.json()['id']}", json={"title": "Renamed"})

    assert response.status_code == 200
    payload = client.get("/tasks").json()
    assert [(task["title"], task["completed"]) for task in payload] == [
        ("Stay the same", False),
        ("Renamed", False),
    ]


def test_patch_completed_task_preserves_completed_state() -> None:
    created = client.post("/tasks", json={"title": "Complete then rename"})
    completed = client.post(f"/tasks/{created.json()['id']}/complete").json()

    response = client.patch(f"/tasks/{created.json()['id']}", json={"title": "Renamed after complete"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == created.json()["id"]
    assert payload["title"] == "Renamed after complete"
    assert payload["completed"] is True
    assert payload["created_at"] == completed["created_at"]
    assert payload["updated_at"] >= completed["updated_at"]


def test_patch_task_not_found() -> None:
    response = client.patch("/tasks/999", json={"title": "New title"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found"}


def test_patch_task_rejects_empty_name() -> None:
    created = client.post("/tasks", json={"title": "Keep me"})

    response = client.patch(f"/tasks/{created.json()['id']}", json={"title": "   "})

    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "string_too_short"


def test_complete_task_not_found() -> None:
    response = client.post("/tasks/999/complete")

    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found"}
