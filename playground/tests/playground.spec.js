import { test, expect } from "@playwright/test";

test("loads the playground", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("MCP Geo Playground")).toBeVisible();
});
