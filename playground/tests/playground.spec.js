import { expect, test } from "@playwright/test";

import { installAuditMocks, installPlaygroundMocks } from "./support/mock_playground.js";

test("loads the playground shell and connects to the mocked MCP host", async ({ page }) => {
  await installPlaygroundMocks(page);
  await installAuditMocks(page);

  await page.goto("/");

  await expect(
    page.getByRole("heading", { name: "Playground security hardening and demo workbench" })
  ).toBeVisible();
  await expect(page.getByRole("button", { name: "Explorer" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Routing" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Audit / FOI" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Benchmarks" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Debug" })).toBeVisible();

  await page.getByRole("button", { name: "Connect", exact: true }).click();
  await expect(page.getByText("test-playground", { exact: true })).toBeVisible();
  await expect(page.getByText("Stakeholder Benchmark Pack")).toBeVisible();
  await expect(page.getByRole("button", { name: /benchmark_prompt/ })).toBeVisible();
});
