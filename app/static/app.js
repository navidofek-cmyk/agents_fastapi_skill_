"use strict";
const taskList = document.querySelector("#task-list");
const taskForm = document.querySelector("#task-form");
const taskTitleInput = document.querySelector("#task-title");
const taskPriorityInput = document.querySelector("#task-priority");
const taskNotesInput = document.querySelector("#task-notes");
const taskDueDateInput = document.querySelector("#task-due-date");
const formError = document.querySelector("#form-error");
const statusText = document.querySelector("#status-text");
const refreshButton = document.querySelector("#refresh-button");
const taskTemplate = document.querySelector("#task-item-template");
const filterButtons = Array.from(document.querySelectorAll(".filter-button"));
const totalCount = document.querySelector("#total-count");
const activeCount = document.querySelector("#active-count");
const completedCount = document.querySelector("#completed-count");
const emptyState = document.querySelector("#empty-state");
if (!taskList ||
    !taskForm ||
    !taskTitleInput ||
    !taskPriorityInput ||
    !taskNotesInput ||
    !taskDueDateInput ||
    !formError ||
    !statusText ||
    !refreshButton ||
    !taskTemplate ||
    !totalCount ||
    !activeCount ||
    !completedCount ||
    !emptyState) {
    throw new Error("Frontend markup is incomplete.");
}
let currentFilter = "all";
const getValidationMessage = async (response) => {
    try {
        const payload = (await response.json());
        return payload.detail?.[0]?.msg ?? "Request failed.";
    }
    catch {
        return "Request failed.";
    }
};
const setFormBusy = (busy) => {
    taskTitleInput.disabled = busy;
    taskPriorityInput.disabled = busy;
    taskNotesInput.disabled = busy;
    taskDueDateInput.disabled = busy;
    const submitButton = taskForm.querySelector('button[type="submit"]');
    if (submitButton) {
        submitButton.disabled = busy;
    }
};
const createTask = async (title, priority, notes, dueDate) => {
    const response = await fetch("/tasks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, priority, notes, due_date: dueDate || null })
    });
    if (!response.ok) {
        throw new Error(await getValidationMessage(response));
    }
};
const updateTask = async (taskId, title, priority, notes, dueDate) => {
    const response = await fetch(`/tasks/${taskId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, priority, notes, due_date: dueDate || null })
    });
    if (!response.ok) {
        throw new Error(await getValidationMessage(response));
    }
};
const completeTask = async (taskId) => {
    const response = await fetch(`/tasks/${taskId}/complete`, { method: "POST" });
    if (!response.ok) {
        throw new Error("Could not complete task.");
    }
};
const deleteTask = async (taskId) => {
    const response = await fetch(`/tasks/${taskId}`, { method: "DELETE" });
    if (!response.ok) {
        throw new Error("Could not delete task.");
    }
};
const formatTimestamp = (value) => {
    const date = new Date(value);
    return `${date.toLocaleDateString()} ${date.toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit"
    })}`;
};
const formatDueDate = (value) => {
    if (!value) {
        return "No due date";
    }
    const date = new Date(`${value}T00:00:00`);
    return `Due ${date.toLocaleDateString()}`;
};
const updateStats = (tasks) => {
    const completed = tasks.filter((task) => task.completed).length;
    totalCount.textContent = String(tasks.length);
    activeCount.textContent = String(tasks.length - completed);
    completedCount.textContent = String(completed);
};
const getPriorityLabel = (priority) => {
    if (priority === "high") {
        return "High priority";
    }
    if (priority === "low") {
        return "Low priority";
    }
    return "Medium priority";
};
const getVisibleTasks = (tasks) => {
    if (currentFilter === "active") {
        return tasks.filter((task) => !task.completed);
    }
    if (currentFilter === "completed") {
        return tasks.filter((task) => task.completed);
    }
    return tasks;
};
const renderTasks = (tasks) => {
    taskList.replaceChildren();
    updateStats(tasks);
    const visibleTasks = getVisibleTasks(tasks);
    if (tasks.length === 0) {
        emptyState.hidden = false;
        statusText.textContent = "No tasks yet. Add one from the panel on the left.";
        return;
    }
    emptyState.hidden = visibleTasks.length !== 0;
    statusText.textContent = `${visibleTasks.length} of ${tasks.length} task${tasks.length === 1 ? "" : "s"} visible.`;
    for (const task of visibleTasks) {
        const fragment = taskTemplate.content.cloneNode(true);
        const card = fragment.querySelector(".task-card");
        const badge = fragment.querySelector(".task-badge");
        const idLabel = fragment.querySelector(".task-id");
        const dueDateLabel = fragment.querySelector(".task-due-date");
        const timestampLabel = fragment.querySelector(".task-timestamp");
        const editForm = fragment.querySelector(".task-edit-form");
        const titleInput = fragment.querySelector(".task-title-input");
        const priorityInput = fragment.querySelector(".task-priority-input");
        const notesInput = fragment.querySelector(".task-notes-input");
        const dueDateInput = fragment.querySelector(".task-due-date-input");
        const saveButton = fragment.querySelector(".save-action");
        const completeButton = fragment.querySelector(".complete-action");
        const deleteButton = fragment.querySelector(".delete-action");
        const errorNode = fragment.querySelector(".task-error");
        if (!card ||
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
            !errorNode) {
            continue;
        }
        card.dataset.completed = String(task.completed);
        badge.dataset.priority = task.priority;
        badge.textContent = task.completed ? `${getPriorityLabel(task.priority)} · Completed` : getPriorityLabel(task.priority);
        idLabel.textContent = `Task #${task.id}`;
        dueDateLabel.textContent = formatDueDate(task.due_date);
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
        const syncSaveState = () => {
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
        editForm.addEventListener("submit", async (event) => {
            event.preventDefault();
            errorNode.textContent = "";
            const trimmedTitle = titleInput.value.trim();
            const notes = notesInput.value.trim();
            const dueDate = dueDateInput.value;
            try {
                await updateTask(task.id, trimmedTitle, priorityInput.value, notes, dueDate);
                await loadTasks();
            }
            catch (error) {
                errorNode.textContent = error instanceof Error ? error.message : "Could not save task.";
            }
        });
        completeButton.addEventListener("click", async () => {
            errorNode.textContent = "";
            try {
                await completeTask(task.id);
                await loadTasks();
            }
            catch (error) {
                errorNode.textContent = error instanceof Error ? error.message : "Could not complete task.";
            }
        });
        deleteButton.addEventListener("click", async () => {
            errorNode.textContent = "";
            try {
                await deleteTask(task.id);
                await loadTasks();
            }
            catch (error) {
                errorNode.textContent = error instanceof Error ? error.message : "Could not delete task.";
            }
        });
        taskList.append(card);
    }
};
const loadTasks = async () => {
    statusText.textContent = "Loading tasks...";
    const response = await fetch("/tasks");
    if (!response.ok) {
        emptyState.hidden = true;
        statusText.textContent = "Could not load tasks.";
        return;
    }
    const tasks = (await response.json());
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
        await createTask(title, taskPriorityInput.value, notes, dueDate);
        taskForm.reset();
        taskPriorityInput.value = "medium";
        await loadTasks();
    }
    catch (error) {
        formError.textContent = error instanceof Error ? error.message : "Could not create task.";
    }
    finally {
        setFormBusy(false);
    }
});
refreshButton.addEventListener("click", () => {
    void loadTasks();
});
for (const button of filterButtons) {
    button.addEventListener("click", () => {
        currentFilter = button.dataset.filter ?? "all";
        for (const candidate of filterButtons) {
            candidate.classList.toggle("is-active", candidate === button);
        }
        void loadTasks();
    });
}
void loadTasks();
