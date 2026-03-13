import { expect, test } from "@playwright/test";

import { installAuditMocks, installPlaygroundMocks } from "./support/mock_playground.js";

test("drives the audit and FOI workbench against the DSAP REST mocks", async ({ page }) => {
  await installPlaygroundMocks(page);
  await installAuditMocks(page);

  await page.goto("/");
  await page.getByRole("button", { name: "Connect", exact: true }).click();
  await page.getByRole("button", { name: "Audit / FOI" }).click();

  await expect(page.getByRole("button", { name: /pack-demo-001/ })).toBeVisible();
  await page.getByPlaceholder("/path/to/session").fill("/tmp/session-001");
  await page.getByRole("button", { name: "Normalise session" }).click();
  await expect(page.getByText("/tmp/event-ledger.jsonl")).toBeVisible();

  await page.getByRole("button", { name: "Build pack" }).click();
  await expect(page.getByText("/tmp/pack-demo-001")).toBeVisible();

  await page.getByRole("button", { name: "Verify integrity" }).click();
  await expect(page.getByText('"verified": true')).toBeVisible();

  await page.getByRole("button", { name: "FOI redact" }).click();
  await expect(page.getByText("foi_redacted")).toBeVisible();
});
