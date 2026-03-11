import { expect, test } from "@playwright/test";

import { installAuditMocks, installPlaygroundMocks } from "./support/mock_playground.js";

test("rejects widget bridge calls without the active preview token and keeps same-origin off by default", async ({
  page,
}) => {
  await installPlaygroundMocks(page);
  await installAuditMocks(page);

  await page.goto("/");
  await page.getByRole("button", { name: "Connect", exact: true }).click();
  await page.getByRole("button", { name: "Routing" }).click();
  await page.getByRole("button", { name: "Load demo guidance" }).click();

  const frame = page.frameLocator("iframe");
  await expect(frame.locator("#widgetStatus")).toHaveText("Host connected");

  await frame.locator("#callBadTool").click();
  await frame.locator("#readBadResource").click();

  await page.getByRole("button", { name: "Debug" }).click();
  await expect(page.locator("strong").filter({ hasText: "TOKEN_INVALID" }).first()).toBeVisible();
  await expect(page.getByText("allow-same-origin")).toHaveCount(0);
  await expect(page.getByText("allow-scripts", { exact: true })).toBeVisible();
});
