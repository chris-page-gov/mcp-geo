import { expect, test } from "@playwright/test";

import { installAuditMocks, installPlaygroundMocks } from "./support/mock_playground.js";

test("shows seeded routing demos and loads the route preview with scenario config", async ({ page }) => {
  await installPlaygroundMocks(page);
  await installAuditMocks(page);

  await page.goto("/");
  await page.getByRole("button", { name: "Connect", exact: true }).click();
  await page.getByRole("button", { name: "Routing" }).click();

  await expect(page.getByRole("button", { name: /SG03/ })).toBeVisible();
  await expect(page.getByRole("button", { name: /SG12/ })).toBeVisible();

  await page.getByRole("button", { name: "Load demo guidance" }).click();
  await expect(page.locator("pre").filter({ hasText: "benchmark-v1" }).first()).toContainText(
    "benchmark-v1"
  );

  const frame = page.frameLocator("iframe");
  await expect(frame.locator("#widgetStatus")).toHaveText("Host connected");
  await expect(frame.locator("#receivedConfig")).toContainText("Retford Library");
});
