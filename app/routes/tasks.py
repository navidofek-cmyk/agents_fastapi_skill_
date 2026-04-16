from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, StringConstraints

from app.services.task_service import TaskNotFoundError, task_service


router = APIRouter(tags=["tasks"])


class TaskCreate(BaseModel):
    title: str
    priority: Literal["low", "medium", "high"] = "medium"
    notes: str = ""


class TaskUpdate(BaseModel):
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    priority: Literal["low", "medium", "high"]
    notes: str


class TaskResponse(BaseModel):
    id: int
    title: str
    priority: Literal["low", "medium", "high"]
    notes: str
    completed: bool
    created_at: str
    updated_at: str


@router.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate) -> dict[str, object]:
    return task_service.create_task(payload.title, payload.priority, payload.notes)


@router.get("/tasks", response_model=list[TaskResponse])
def list_tasks() -> list[dict[str, object]]:
    return task_service.list_tasks()


@router.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: int) -> dict[str, object]:
    try:
        return task_service.get_task(task_id)
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found") from exc


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int) -> None:
    try:
        task_service.delete_task(task_id)
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found") from exc


@router.patch("/tasks/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, payload: TaskUpdate) -> dict[str, object]:
    try:
        return task_service.update_task(task_id, payload.title, payload.priority, payload.notes)
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found") from exc


@router.post("/tasks/{task_id}/complete", response_model=TaskResponse)
def complete_task(task_id: int) -> dict[str, object]:
    try:
        return task_service.complete_task(task_id)
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found") from exc
