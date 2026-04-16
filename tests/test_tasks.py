from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.services.task_service import TaskService, task_service


client = TestClient(app)


def setup_function() -> None:
    task_service.reset()


def test_create_task() -> None:
    response = client.post("/tasks", json={"title": "Write tests"})

    assert response.status_code == 201
    assert response.json() == {"id": 1, "title": "Write tests", "completed": False}


def test_list_tasks() -> None:
    client.post("/tasks", json={"title": "First"})
    client.post("/tasks", json={"title": "Second"})

    response = client.get("/tasks")

    assert response.status_code == 200
    assert response.json() == [
        {"id": 1, "title": "First", "completed": False},
        {"id": 2, "title": "Second", "completed": False},
    ]


def test_get_task() -> None:
    created = client.post("/tasks", json={"title": "Fetch me"})

    response = client.get(f"/tasks/{created.json()['id']}")

    assert response.status_code == 200
    assert response.json() == {"id": 1, "title": "Fetch me", "completed": False}


def test_get_task_not_found() -> None:
    response = client.get("/tasks/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found"}


def test_tasks_persist_between_requests_within_app_instance() -> None:
    client.post("/tasks", json={"title": "Persist me"})

    list_response = client.get("/tasks")
    get_response = client.get("/tasks/1")

    assert list_response.status_code == 200
    assert list_response.json() == [{"id": 1, "title": "Persist me", "completed": False}]
    assert get_response.status_code == 200
    assert get_response.json() == {"id": 1, "title": "Persist me", "completed": False}


def test_tasks_persist_across_service_reinstantiation(tmp_path: Path) -> None:
    db_path = tmp_path / "tasks.sqlite"
    first_service = TaskService(str(db_path))
    first_service.reset()
    created = first_service.create_task("Persist after restart")

    second_service = TaskService(str(db_path))

    assert second_service.get_task(created["id"]) == {
        "id": created["id"],
        "title": "Persist after restart",
        "completed": False,
    }


def test_complete_task() -> None:
    created = client.post("/tasks", json={"title": "Ship feature"})

    response = client.post(f"/tasks/{created.json()['id']}/complete")

    assert response.status_code == 200
    assert response.json() == {"id": 1, "title": "Ship feature", "completed": True}


def test_delete_task() -> None:
    created = client.post("/tasks", json={"title": "Remove me"})

    response = client.delete(f"/tasks/{created.json()['id']}")

    assert response.status_code == 204
    assert response.content == b""
    assert client.get("/tasks").json() == []


def test_delete_task_not_found() -> None:
    response = client.delete("/tasks/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found"}


def test_patch_task_updates_name() -> None:
    created = client.post("/tasks", json={"title": "Old title"})

    response = client.patch(f"/tasks/{created.json()['id']}", json={"title": "New title"})

    assert response.status_code == 200
    assert response.json() == {"id": 1, "title": "New title", "completed": False}
    assert client.get("/tasks").json() == [{"id": 1, "title": "New title", "completed": False}]


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
