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
    response = client.post("/tasks", json={"title": "Write tests", "due_date": "2026-06-30"})

    assert response.status_code == 201
    payload = response.json()
    assert payload["id"] == 1
    assert payload["title"] == "Write tests"
    assert payload["priority"] == "medium"
    assert payload["notes"] == ""
    assert payload["due_date"] == "2026-06-30"
    assert payload["completed"] is False
    assert_task_timestamps(payload)
    assert payload["created_at"] == payload["updated_at"]


def test_list_tasks() -> None:
    client.post("/tasks", json={"title": "First", "priority": "low", "notes": "Alpha", "due_date": "2026-05-01"})
    client.post("/tasks", json={"title": "Second", "priority": "high", "notes": "Beta"})

    response = client.get("/tasks")

    assert response.status_code == 200
    payload = response.json()
    assert [task["id"] for task in payload] == [1, 2]
    assert [task["title"] for task in payload] == ["First", "Second"]
    assert [task["priority"] for task in payload] == ["low", "high"]
    assert [task["notes"] for task in payload] == ["Alpha", "Beta"]
    assert [task["due_date"] for task in payload] == ["2026-05-01", None]
    assert [task["completed"] for task in payload] == [False, False]
    for task in payload:
        assert_task_timestamps(task)


def test_get_task() -> None:
    created = client.post(
        "/tasks",
        json={"title": "Fetch me", "priority": "high", "notes": "Urgent", "due_date": "2026-07-15"},
    )

    response = client.get(f"/tasks/{created.json()['id']}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == 1
    assert payload["title"] == "Fetch me"
    assert payload["priority"] == "high"
    assert payload["notes"] == "Urgent"
    assert payload["due_date"] == "2026-07-15"
    assert payload["completed"] is False
    assert_task_timestamps(payload)


def test_get_task_not_found() -> None:
    response = client.get("/tasks/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found"}


def test_tasks_persist_between_requests_within_app_instance() -> None:
    client.post("/tasks", json={"title": "Persist me", "priority": "low", "notes": "Save this", "due_date": "2026-08-20"})

    list_response = client.get("/tasks")
    get_response = client.get("/tasks/1")

    assert list_response.status_code == 200
    assert [task["title"] for task in list_response.json()] == ["Persist me"]
    assert get_response.status_code == 200
    assert get_response.json()["title"] == "Persist me"
    assert get_response.json()["priority"] == "low"
    assert get_response.json()["notes"] == "Save this"
    assert get_response.json()["due_date"] == "2026-08-20"


def test_tasks_persist_across_service_reinstantiation(tmp_path: Path) -> None:
    db_path = tmp_path / "tasks.sqlite"
    first_service = TaskService(str(db_path))
    first_service.reset()
    created = first_service.create_task("Persist after restart", "high", "Across restart", "2026-09-01")

    second_service = TaskService(str(db_path))

    payload = second_service.get_task(created["id"])
    assert payload["id"] == created["id"]
    assert payload["title"] == "Persist after restart"
    assert payload["priority"] == "high"
    assert payload["notes"] == "Across restart"
    assert payload["due_date"] == "2026-09-01"
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
    assert payload["priority"] == "medium"
    assert payload["notes"] == ""
    assert payload["due_date"] is None
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
    assert payload["priority"] == "medium"
    assert payload["notes"] == ""
    assert payload["due_date"] is None
    assert payload["completed"] is False
    assert payload["created_at"] == "2026-01-01T00:00:00+00:00"
    assert isinstance(payload["updated_at"], str)
    assert payload["updated_at"]


def test_migrates_sqlite_table_without_priority_notes_and_due_date(tmp_path: Path) -> None:
    db_path = tmp_path / "pre-metadata.sqlite"
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                completed INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            "INSERT INTO tasks (title, completed, created_at, updated_at) VALUES (?, ?, ?, ?)",
            ("Needs metadata", 0, "2026-01-01T00:00:00+00:00", "2026-01-02T00:00:00+00:00"),
        )
        connection.commit()

    migrated_service = TaskService(str(db_path))

    payload = migrated_service.get_task(1)
    assert payload["priority"] == "medium"
    assert payload["notes"] == ""
    assert payload["due_date"] is None
    assert payload["title"] == "Needs metadata"


def test_complete_task() -> None:
    created = client.post(
        "/tasks",
        json={"title": "Ship feature", "priority": "high", "notes": "Ship today", "due_date": "2026-10-10"},
    )

    response = client.post(f"/tasks/{created.json()['id']}/complete")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == 1
    assert payload["title"] == "Ship feature"
    assert payload["priority"] == "high"
    assert payload["notes"] == "Ship today"
    assert payload["due_date"] == "2026-10-10"
    assert payload["completed"] is True
    assert_task_timestamps(payload)


def test_complete_task_only_updates_target_task() -> None:
    first = client.post("/tasks", json={"title": "First", "priority": "low", "notes": "", "due_date": "2026-11-01"})
    second = client.post("/tasks", json={"title": "Second", "priority": "high", "notes": "Finish"})

    response = client.post(f"/tasks/{second.json()['id']}/complete")

    assert response.status_code == 200
    assert response.json()["completed"] is True
    payload = client.get("/tasks").json()
    assert [(task["title"], task["priority"], task["notes"], task["due_date"], task["completed"]) for task in payload] == [
        ("First", "low", "", "2026-11-01", False),
        ("Second", "high", "Finish", None, True),
    ]


def test_delete_task() -> None:
    created = client.post("/tasks", json={"title": "Remove me"})

    response = client.delete(f"/tasks/{created.json()['id']}")

    assert response.status_code == 204
    assert response.content == b""
    assert client.get("/tasks").json() == []


def test_delete_task_only_removes_target_task() -> None:
    first = client.post("/tasks", json={"title": "Keep me", "priority": "low", "notes": "A", "due_date": "2026-12-01"})
    second = client.post("/tasks", json={"title": "Delete me", "priority": "medium", "notes": "B"})
    third = client.post("/tasks", json={"title": "Keep me too", "priority": "high", "notes": "C", "due_date": "2026-12-31"})

    response = client.delete(f"/tasks/{second.json()['id']}")

    assert response.status_code == 204
    payload = client.get("/tasks").json()
    assert [
        (task["id"], task["title"], task["priority"], task["notes"], task["due_date"], task["completed"])
        for task in payload
    ] == [
        (first.json()["id"], "Keep me", "low", "A", "2026-12-01", False),
        (third.json()["id"], "Keep me too", "high", "C", "2026-12-31", False),
    ]
    for task in payload:
        assert_task_timestamps(task)


def test_delete_task_not_found() -> None:
    response = client.delete("/tasks/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found"}


def test_patch_task_updates_name() -> None:
    created = client.post(
        "/tasks",
        json={"title": "Old title", "priority": "low", "notes": "Original", "due_date": "2026-04-20"},
    )

    response = client.patch(
        f"/tasks/{created.json()['id']}",
        json={"title": "New title", "priority": "high", "notes": "Updated", "due_date": "2026-04-30"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == 1
    assert payload["title"] == "New title"
    assert payload["priority"] == "high"
    assert payload["notes"] == "Updated"
    assert payload["due_date"] == "2026-04-30"
    assert payload["completed"] is False
    assert_task_timestamps(payload)
    assert payload["updated_at"] >= payload["created_at"]
    assert client.get("/tasks").json()[0]["title"] == "New title"


def test_patch_task_only_updates_target_task() -> None:
    first = client.post(
        "/tasks",
        json={"title": "Stay the same", "priority": "low", "notes": "Keep", "due_date": "2026-04-22"},
    )
    second = client.post("/tasks", json={"title": "Rename me", "priority": "medium", "notes": "Change"})

    response = client.patch(
        f"/tasks/{second.json()['id']}",
        json={"title": "Renamed", "priority": "high", "notes": "Changed", "due_date": "2026-05-05"},
    )

    assert response.status_code == 200
    payload = client.get("/tasks").json()
    assert [(task["title"], task["priority"], task["notes"], task["due_date"], task["completed"]) for task in payload] == [
        ("Stay the same", "low", "Keep", "2026-04-22", False),
        ("Renamed", "high", "Changed", "2026-05-05", False),
    ]


def test_patch_completed_task_preserves_completed_state() -> None:
    created = client.post(
        "/tasks",
        json={"title": "Complete then rename", "priority": "medium", "notes": "Before", "due_date": "2026-05-10"},
    )
    completed = client.post(f"/tasks/{created.json()['id']}/complete").json()

    response = client.patch(
        f"/tasks/{created.json()['id']}",
        json={"title": "Renamed after complete", "priority": "high", "notes": "After", "due_date": "2026-05-11"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == created.json()["id"]
    assert payload["title"] == "Renamed after complete"
    assert payload["priority"] == "high"
    assert payload["notes"] == "After"
    assert payload["due_date"] == "2026-05-11"
    assert payload["completed"] is True
    assert payload["created_at"] == completed["created_at"]
    assert payload["updated_at"] >= completed["updated_at"]


def test_patch_task_not_found() -> None:
    response = client.patch(
        "/tasks/999",
        json={"title": "New title", "priority": "medium", "notes": "", "due_date": None},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found"}


def test_patch_task_rejects_empty_name() -> None:
    created = client.post("/tasks", json={"title": "Keep me"})

    response = client.patch(
        f"/tasks/{created.json()['id']}",
        json={"title": "   ", "priority": "medium", "notes": "", "due_date": None},
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "string_too_short"


def test_complete_task_not_found() -> None:
    response = client.post("/tasks/999/complete")

    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found"}


def test_patch_task_can_clear_due_date() -> None:
    created = client.post(
        "/tasks",
        json={"title": "Clear date", "priority": "medium", "notes": "", "due_date": "2026-06-01"},
    )

    response = client.patch(
        f"/tasks/{created.json()['id']}",
        json={"title": "Clear date", "priority": "medium", "notes": "", "due_date": None},
    )

    assert response.status_code == 200
    assert response.json()["due_date"] is None
