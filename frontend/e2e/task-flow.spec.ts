import { expect, test } from "@playwright/test";

test("user can create, complete, filter, and delete a task", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "Task Flow" })).toBeVisible();
  await expect(page.locator("#empty-state")).toBeVisible();

  await page.getByPlaceholder("Add a task that matters").fill("Ship frontend smoke test");
  await page.getByRole("button", { name: "Create" }).click();

  await expect(page.locator(".task-card")).toHaveCount(1);
  await expect(page.locator("#total-count")).toHaveText("1");
  await expect(page.locator("#active-count")).toHaveText("1");
  await expect(page.locator(".task-title-input")).toHaveValue("Ship frontend smoke test");

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
