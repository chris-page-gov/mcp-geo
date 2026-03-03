import { test, expect } from "@playwright/test";

test("loads the playground", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /MCP Geo Playground/ })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Version matrix" })).toBeVisible();
  await expect(page.getByText("MCP Apps protocol (playground host)")).toBeVisible();
  await page.getByRole("button", { name: "Test" }).click();
  await expect(
    page.getByText("Use Host viewport mode in UI preview to force compact-window rendering tests.")
  ).toBeVisible();
});
