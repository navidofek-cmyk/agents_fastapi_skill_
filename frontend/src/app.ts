type Task = {
  id: number;
  title: string;
  priority: "low" | "medium" | "high";
  notes: string;
  due_date: string | null;
  completed: boolean;
  created_at: string;
  updated_at: string;
};

type ValidationErrorResponse = {
  detail?: Array<{ msg?: string }>;
};

type TaskFilter = "all" | "active" | "completed";
type TaskSort = "recent" | "due" | "priority" | "created";

const taskList = document.querySelector<HTMLUListElement>("#task-list");
const taskForm = document.querySelector<HTMLFormElement>("#task-form");
const taskTitleInput = document.querySelector<HTMLInputElement>("#task-title");
const taskPriorityInput = document.querySelector<HTMLSelectElement>("#task-priority");
const taskNotesInput = document.querySelector<HTMLTextAreaElement>("#task-notes");
const taskDueDateInput = document.querySelector<HTMLInputElement>("#task-due-date");
const formError = document.querySelector<HTMLParagraphElement>("#form-error");
const statusText = document.querySelector<HTMLParagraphElement>("#status-text");
const refreshButton = document.querySelector<HTMLButtonElement>("#refresh-button");
const searchInput = document.querySelector<HTMLInputElement>("#task-search");
const sortInput = document.querySelector<HTMLSelectElement>("#task-sort");
const taskTemplate = document.querySelector<HTMLTemplateElement>("#task-item-template");
const filterButtons = Array.from(document.querySelectorAll<HTMLButtonElement>(".filter-button"));
const totalCount = document.querySelector<HTMLElement>("#total-count");
const activeCount = document.querySelector<HTMLElement>("#active-count");
const completedCount = document.querySelector<HTMLElement>("#completed-count");
const emptyState = document.querySelector<HTMLDivElement>("#empty-state");

if (
  !taskList ||
  !taskForm ||
  !taskTitleInput ||
  !taskPriorityInput ||
  !taskNotesInput ||
  !taskDueDateInput ||
  !formError ||
  !statusText ||
  !refreshButton ||
  !searchInput ||
  !sortInput ||
  !taskTemplate ||
  !totalCount ||
  !activeCount ||
  !completedCount ||
  !emptyState
) {
  throw new Error("Frontend markup is incomplete.");
}

let currentFilter: TaskFilter = "all";
let currentSort: TaskSort = "recent";
let currentQuery = "";

const getValidationMessage = async (response: Response): Promise<string> => {
  try {
    const payload = (await response.json()) as ValidationErrorResponse;
    return payload.detail?.[0]?.msg ?? "Request failed.";
  } catch {
    return "Request failed.";
  }
};

const setFormBusy = (busy: boolean): void => {
  taskTitleInput.disabled = busy;
  taskPriorityInput.disabled = busy;
  taskNotesInput.disabled = busy;
  taskDueDateInput.disabled = busy;
  const submitButton = taskForm.querySelector<HTMLButtonElement>('button[type="submit"]');
  if (submitButton) {
    submitButton.disabled = busy;
  }
};

const createTask = async (
  title: string,
  priority: Task["priority"],
  notes: string,
  dueDate: string
): Promise<void> => {
  const response = await fetch("/tasks", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, priority, notes, due_date: dueDate || null })
  });

  if (!response.ok) {
    throw new Error(await getValidationMessage(response));
  }
};

const updateTask = async (
  taskId: number,
  title: string,
  priority: Task["priority"],
  notes: string,
  dueDate: string
): Promise<void> => {
  const response = await fetch(`/tasks/${taskId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, priority, notes, due_date: dueDate || null })
  });

  if (!response.ok) {
    throw new Error(await getValidationMessage(response));
  }
};

const completeTask = async (taskId: number): Promise<void> => {
  const response = await fetch(`/tasks/${taskId}/complete`, { method: "POST" });
  if (!response.ok) {
    throw new Error("Could not complete task.");
  }
};

const deleteTask = async (taskId: number): Promise<void> => {
  const response = await fetch(`/tasks/${taskId}`, { method: "DELETE" });
  if (!response.ok) {
    throw new Error("Could not delete task.");
  }
};

const formatTimestamp = (value: string): string => {
  const date = new Date(value);
  return `${date.toLocaleDateString()} ${date.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit"
  })}`;
};

const formatDueDate = (value: string | null): string => {
  if (!value) {
    return "No due date";
  }

  const date = new Date(`${value}T00:00:00`);
  return `Due ${date.toLocaleDateString()}`;
};

const getDueStatus = (task: Task): "none" | "overdue" | "today" | "upcoming" => {
  if (!task.due_date || task.completed) {
    return "none";
  }

  const today = new Date();
  const todayKey = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;

  if (task.due_date < todayKey) {
    return "overdue";
  }

  if (task.due_date === todayKey) {
    return "today";
  }

  return "upcoming";
};

const updateStats = (tasks: Task[]): void => {
  const completed = tasks.filter((task) => task.completed).length;
  totalCount.textContent = String(tasks.length);
  activeCount.textContent = String(tasks.length - completed);
  completedCount.textContent = String(completed);
};

const getPriorityLabel = (priority: Task["priority"]): string => {
  if (priority === "high") {
    return "High priority";
  }
  if (priority === "low") {
    return "Low priority";
  }
  return "Medium priority";
};

const getPriorityRank = (priority: Task["priority"]): number => {
  if (priority === "high") {
    return 0;
  }

  if (priority === "medium") {
    return 1;
  }

  return 2;
};

const getVisibleTasks = (tasks: Task[]): Task[] => {
  const query = currentQuery.trim().toLowerCase();
  const filteredTasks = tasks.filter((task) => {
    if (currentFilter === "active" && task.completed) {
      return false;
    }

    if (currentFilter === "completed" && !task.completed) {
      return false;
    }

    if (!query) {
      return true;
    }

    return `${task.title} ${task.notes}`.toLowerCase().includes(query);
  });

  return filteredTasks.slice().sort((left: Task, right: Task) => {
    if (currentSort === "due") {
      const leftDue = left.due_date ?? "9999-12-31";
      const rightDue = right.due_date ?? "9999-12-31";
      if (leftDue !== rightDue) {
        return leftDue.localeCompare(rightDue);
      }
    }

    if (currentSort === "priority") {
      const priorityDelta = getPriorityRank(left.priority) - getPriorityRank(right.priority);
      if (priorityDelta !== 0) {
        return priorityDelta;
      }
    }

    if (currentSort === "created") {
      if (left.created_at !== right.created_at) {
        return left.created_at.localeCompare(right.created_at);
      }
      return left.id - right.id;
    }

    if (left.updated_at !== right.updated_at) {
      return right.updated_at.localeCompare(left.updated_at);
    }

    return right.id - left.id;
  });
};

const renderTasks = (tasks: Task[]): void => {
  taskList.replaceChildren();
  updateStats(tasks);
  const visibleTasks = getVisibleTasks(tasks);

  if (tasks.length === 0) {
    emptyState.hidden = false;
    statusText.textContent = "No tasks yet. Add one from the panel on the left.";
    return;
  }

  emptyState.hidden = visibleTasks.length !== 0;
  statusText.textContent =
    visibleTasks.length === 0
      ? "No tasks match the current search or filter."
      : `${visibleTasks.length} of ${tasks.length} task${tasks.length === 1 ? "" : "s"} visible.`;

  for (const task of visibleTasks) {
    const fragment = taskTemplate.content.cloneNode(true) as DocumentFragment;
    const card = fragment.querySelector<HTMLLIElement>(".task-card");
    const badge = fragment.querySelector<HTMLSpanElement>(".task-badge");
    const idLabel = fragment.querySelector<HTMLSpanElement>(".task-id");
    const dueDateLabel = fragment.querySelector<HTMLSpanElement>(".task-due-date");
    const timestampLabel = fragment.querySelector<HTMLSpanElement>(".task-timestamp");
    const editForm = fragment.querySelector<HTMLFormElement>(".task-edit-form");
    const titleInput = fragment.querySelector<HTMLInputElement>(".task-title-input");
    const priorityInput = fragment.querySelector<HTMLSelectElement>(".task-priority-input");
    const notesInput = fragment.querySelector<HTMLTextAreaElement>(".task-notes-input");
    const dueDateInput = fragment.querySelector<HTMLInputElement>(".task-due-date-input");
    const saveButton = fragment.querySelector<HTMLButtonElement>(".save-action");
    const completeButton = fragment.querySelector<HTMLButtonElement>(".complete-action");
    const deleteButton = fragment.querySelector<HTMLButtonElement>(".delete-action");
    const errorNode = fragment.querySelector<HTMLParagraphElement>(".task-error");

    if (
      !card ||
      !badge ||
      !idLabel ||
      !dueDateLabel ||
      !timestampLabel ||
      !editForm ||
      !titleInput ||
      !priorityInput ||
      !notesInput ||
      !dueDateInput ||
      !saveButton ||
      !completeButton ||
      !deleteButton ||
      !errorNode
    ) {
      continue;
    }

    card.dataset.completed = String(task.completed);
    const dueStatus = getDueStatus(task);
    card.dataset.dueStatus = dueStatus;
    badge.dataset.priority = task.priority;
    badge.textContent = task.completed ? `${getPriorityLabel(task.priority)} · Completed` : getPriorityLabel(task.priority);
    idLabel.textContent = `Task #${task.id}`;
    dueDateLabel.textContent = formatDueDate(task.due_date);
    dueDateLabel.dataset.dueStatus = dueStatus;
    timestampLabel.textContent =
      task.created_at === task.updated_at
        ? `Created ${formatTimestamp(task.created_at)}`
        : `Updated ${formatTimestamp(task.updated_at)}`;
    titleInput.value = task.title;
    priorityInput.value = task.priority;
    notesInput.value = task.notes;
    dueDateInput.value = task.due_date ?? "";
    saveButton.disabled = true;
    completeButton.dataset.completed = String(task.completed);
    completeButton.textContent = task.completed ? "Completed" : "Complete";
    completeButton.disabled = task.completed;

    const syncSaveState = (): void => {
      saveButton.disabled =
        titleInput.value.trim() === task.title &&
        priorityInput.value === task.priority &&
        notesInput.value === task.notes &&
        dueDateInput.value === (task.due_date ?? "");
    };

    titleInput.addEventListener("input", syncSaveState);
    priorityInput.addEventListener("change", syncSaveState);
    notesInput.addEventListener("input", syncSaveState);
    dueDateInput.addEventListener("input", syncSaveState);

    editForm.addEventListener("submit", async (event: SubmitEvent) => {
      event.preventDefault();
      errorNode.textContent = "";
      const trimmedTitle = titleInput.value.trim();
      const notes = notesInput.value.trim();
      const dueDate = dueDateInput.value;

      try {
        await updateTask(task.id, trimmedTitle, priorityInput.value as Task["priority"], notes, dueDate);
        await loadTasks();
      } catch (error) {
        errorNode.textContent = error instanceof Error ? error.message : "Could not save task.";
      }
    });

    completeButton.addEventListener("click", async () => {
      errorNode.textContent = "";

      try {
        await completeTask(task.id);
        await loadTasks();
      } catch (error) {
        errorNode.textContent = error instanceof Error ? error.message : "Could not complete task.";
      }
    });

    deleteButton.addEventListener("click", async () => {
      errorNode.textContent = "";

      try {
        await deleteTask(task.id);
        await loadTasks();
      } catch (error) {
        errorNode.textContent = error instanceof Error ? error.message : "Could not delete task.";
      }
    });

    taskList.append(card);
  }
};

const loadTasks = async (): Promise<void> => {
  statusText.textContent = "Loading tasks...";
  const response = await fetch("/tasks");

  if (!response.ok) {
    emptyState.hidden = true;
    statusText.textContent = "Could not load tasks.";
    return;
  }

  const tasks = (await response.json()) as Task[];
  renderTasks(tasks);
};

taskForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const title = taskTitleInput.value.trim();
  const notes = taskNotesInput.value.trim();
  const dueDate = taskDueDateInput.value;
  formError.textContent = "";
  setFormBusy(true);

  try {
    await createTask(title, taskPriorityInput.value as Task["priority"], notes, dueDate);
    taskForm.reset();
    taskPriorityInput.value = "medium";
    await loadTasks();
  } catch (error) {
    formError.textContent = error instanceof Error ? error.message : "Could not create task.";
  } finally {
    setFormBusy(false);
  }
});

refreshButton.addEventListener("click", () => {
  void loadTasks();
});

searchInput.addEventListener("input", () => {
  currentQuery = searchInput.value;
  void loadTasks();
});

sortInput.addEventListener("change", () => {
  currentSort = (sortInput.value as TaskSort | undefined) ?? "recent";
  void loadTasks();
});

for (const button of filterButtons) {
  button.addEventListener("click", () => {
    currentFilter = (button.dataset.filter as TaskFilter | undefined) ?? "all";
    for (const candidate of filterButtons) {
      candidate.classList.toggle("is-active", candidate === button);
    }
    void loadTasks();
  });
}

void loadTasks();
