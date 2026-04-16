import os
import sqlite3
from pathlib import Path
from datetime import datetime, timezone


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
                    priority TEXT NOT NULL DEFAULT 'medium',
                    notes TEXT NOT NULL DEFAULT '',
                    due_date TEXT,
                    completed INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(tasks)").fetchall()
            }
            if "created_at" not in columns:
                now = self._now()
                connection.execute("ALTER TABLE tasks ADD COLUMN created_at TEXT")
                connection.execute("UPDATE tasks SET created_at = ?", (now,))
                connection.execute(
                    "CREATE TABLE tasks_new ("
                    "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                    "title TEXT NOT NULL, "
                    "priority TEXT NOT NULL DEFAULT 'medium', "
                    "notes TEXT NOT NULL DEFAULT '', "
                    "due_date TEXT, "
                    "completed INTEGER NOT NULL DEFAULT 0, "
                    "created_at TEXT NOT NULL, "
                    "updated_at TEXT NOT NULL)"
                )
                connection.execute(
                    "INSERT INTO tasks_new (id, title, priority, notes, due_date, completed, created_at, updated_at) "
                    "SELECT id, title, 'medium', '', NULL, completed, created_at, ? FROM tasks",
                    (now,),
                )
                connection.execute("DROP TABLE tasks")
                connection.execute("ALTER TABLE tasks_new RENAME TO tasks")
            elif "updated_at" not in columns:
                now = self._now()
                connection.execute("ALTER TABLE tasks ADD COLUMN updated_at TEXT")
                connection.execute("UPDATE tasks SET updated_at = ?", (now,))
            columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(tasks)").fetchall()
            }
            if "priority" not in columns:
                connection.execute("ALTER TABLE tasks ADD COLUMN priority TEXT NOT NULL DEFAULT 'medium'")
            if "notes" not in columns:
                connection.execute("ALTER TABLE tasks ADD COLUMN notes TEXT NOT NULL DEFAULT ''")
            if "due_date" not in columns:
                connection.execute("ALTER TABLE tasks ADD COLUMN due_date TEXT")
            connection.commit()

    def _now(self) -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    def _serialize_task(self, row: sqlite3.Row) -> dict[str, object]:
        return {
            "id": row["id"],
            "title": row["title"],
            "priority": row["priority"],
            "notes": row["notes"],
            "due_date": row["due_date"],
            "completed": bool(row["completed"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def reset(self) -> None:
        self._initialize_db()
        with self._connect() as connection:
            connection.execute("DELETE FROM tasks")
            connection.execute("DELETE FROM sqlite_sequence WHERE name = 'tasks'")
            connection.commit()

    def create_task(
        self,
        title: str,
        priority: str = "medium",
        notes: str = "",
        due_date: str | None = None,
    ) -> dict[str, object]:
        now = self._now()
        with self._connect() as connection:
            cursor = connection.execute(
                "INSERT INTO tasks (title, priority, notes, due_date, completed, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (title, priority, notes, due_date, False, now, now),
            )
            connection.commit()
            task_id = cursor.lastrowid

        return self.get_task(task_id)

    def list_tasks(self) -> list[dict[str, object]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id, title, priority, notes, due_date, completed, created_at, updated_at FROM tasks ORDER BY id"
            ).fetchall()

        return [self._serialize_task(row) for row in rows]

    def get_task(self, task_id: int) -> dict[str, object]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT id, title, priority, notes, due_date, completed, created_at, updated_at FROM tasks WHERE id = ?",
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

    def update_task(
        self,
        task_id: int,
        title: str,
        priority: str,
        notes: str,
        due_date: str | None,
    ) -> dict[str, object]:
        now = self._now()
        with self._connect() as connection:
            cursor = connection.execute(
                "UPDATE tasks SET title = ?, priority = ?, notes = ?, due_date = ?, updated_at = ? WHERE id = ?",
                (title, priority, notes, due_date, now, task_id),
            )
            connection.commit()

        if cursor.rowcount == 0:
            raise TaskNotFoundError(task_id)

        return self.get_task(task_id)

    def complete_task(self, task_id: int) -> dict[str, object]:
        now = self._now()
        with self._connect() as connection:
            cursor = connection.execute(
                "UPDATE tasks SET completed = 1, updated_at = ? WHERE id = ?",
                (now, task_id),
            )
            connection.commit()

        if cursor.rowcount == 0:
            raise TaskNotFoundError(task_id)

        return self.get_task(task_id)


task_service = TaskService()
