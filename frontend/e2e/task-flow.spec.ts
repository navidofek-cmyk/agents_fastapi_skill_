import { expect, test } from "@playwright/test";

test("user can create, complete, filter, and delete a task", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "Task Flow" })).toBeVisible();
  await expect(page.locator("#empty-state")).toBeVisible();

  await page.getByPlaceholder("Add a task that matters").fill("Ship frontend smoke test");
  await page.locator("#task-due-date").fill("2026-04-20");
  await page.getByRole("button", { name: "Create" }).click();

  await expect(page.locator(".task-card")).toHaveCount(1);
  await expect(page.locator("#total-count")).toHaveText("1");
  await expect(page.locator("#active-count")).toHaveText("1");
  await expect(page.locator(".task-title-input")).toHaveValue("Ship frontend smoke test");
  await expect(page.locator(".task-due-date")).toContainText("Due");

  await page.locator("#task-search").fill("frontend");
  await expect(page.locator(".task-card")).toHaveCount(1);

  await page.locator("#task-search").fill("missing");
  await expect(page.locator(".task-card")).toHaveCount(0);
  await expect(page.locator("#status-text")).toContainText("No tasks match");

  await page.locator("#task-search").fill("");
  await page.locator("#task-sort").selectOption("due");
  await expect(page.locator(".task-card")).toHaveCount(1);

  await page.getByRole("button", { name: "Complete" }).click();

  await expect(page.locator("#active-count")).toHaveText("0");
  await expect(page.locator("#completed-count")).toHaveText("1");
  await expect(page.getByRole("button", { name: "Completed" })).toBeDisabled();

  await page.getByRole("button", { name: "Done" }).click();
  await expect(page.locator(".task-card")).toHaveCount(1);

  await page.getByRole("button", { name: "Delete" }).click();

  await expect(page.locator(".task-card")).toHaveCount(0);
  await expect(page.locator("#total-count")).toHaveText("0");
  await expect(page.locator("#empty-state")).toBeVisible();
});
