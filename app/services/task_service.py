import os
import sqlite3
from pathlib import Path


class TaskNotFoundError(Exception):
    pass


class TaskService:
    def __init__(self, db_path: str | None = None) -> None:
        self._db_path = Path(db_path or os.getenv("TASKS_DB_PATH", "tasks.db"))
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize_db(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    completed INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            connection.commit()

    def _serialize_task(self, row: sqlite3.Row) -> dict[str, object]:
        return {
            "id": row["id"],
            "title": row["title"],
            "completed": bool(row["completed"]),
        }

    def reset(self) -> None:
        self._initialize_db()
        with self._connect() as connection:
            connection.execute("DELETE FROM tasks")
            connection.execute("DELETE FROM sqlite_sequence WHERE name = 'tasks'")
            connection.commit()

    def create_task(self, title: str) -> dict[str, object]:
        with self._connect() as connection:
            cursor = connection.execute(
                "INSERT INTO tasks (title, completed) VALUES (?, ?)",
                (title, False),
            )
            connection.commit()
            task_id = cursor.lastrowid

        return self.get_task(task_id)

    def list_tasks(self) -> list[dict[str, object]]:
        with self._connect() as connection:
            rows = connection.execute("SELECT id, title, completed FROM tasks ORDER BY id").fetchall()

        return [self._serialize_task(row) for row in rows]

    def get_task(self, task_id: int) -> dict[str, object]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT id, title, completed FROM tasks WHERE id = ?",
                (task_id,),
            ).fetchone()

        if row is None:
            raise TaskNotFoundError(task_id)

        return self._serialize_task(row)

    def delete_task(self, task_id: int) -> None:
        with self._connect() as connection:
            cursor = connection.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            connection.commit()

        if cursor.rowcount == 0:
            raise TaskNotFoundError(task_id)

    def update_task(self, task_id: int, title: str) -> dict[str, object]:
        with self._connect() as connection:
            cursor = connection.execute(
                "UPDATE tasks SET title = ? WHERE id = ?",
                (title, task_id),
            )
            connection.commit()

        if cursor.rowcount == 0:
            raise TaskNotFoundError(task_id)

        return self.get_task(task_id)

    def complete_task(self, task_id: int) -> dict[str, object]:
        with self._connect() as connection:
            cursor = connection.execute(
                "UPDATE tasks SET completed = 1 WHERE id = ?",
                (task_id,),
            )
            connection.commit()

        if cursor.rowcount == 0:
            raise TaskNotFoundError(task_id)

        return self.get_task(task_id)


task_service = TaskService()
