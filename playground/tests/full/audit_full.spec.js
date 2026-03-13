import { connectPlayground, expect, openWorkbenchTab, test } from "../support/full_playground.js";

test("covers audit and FOI pack listing, build, verify, redact, legal hold, and downloads", async ({
  page,
}) => {
  await connectPlayground(page);
  await openWorkbenchTab(page, "Audit / FOI");

  await expect(page.getByRole("button", { name: /pack-demo-001/ })).toBeVisible();
  await page.getByPlaceholder("/path/to/session").fill("/tmp/session-001");

  await page.getByRole("button", { name: "Normalise session" }).click();
  await expect(page.getByText("/tmp/event-ledger.jsonl")).toBeVisible();

  await page.getByRole("button", { name: "Build pack" }).click();
  await expect(page.getByText("/tmp/pack-demo-001")).toBeVisible();

  await page.getByRole("button", { name: "Verify integrity" }).click();
  await expect(page.getByText('"verified": true')).toBeVisible();

  await page.getByRole("button", { name: "FOI redact" }).click();
  await expect(page.getByText("foi_redacted").first()).toBeVisible();

  await page.getByRole("button", { name: "Apply legal hold" }).click();
  await expect(page.getByText('"legalHold": true').first()).toBeVisible();

  await Promise.all([
    page.waitForResponse((response) => response.url().endsWith("/audit/packs/pack-demo-001/bundle") && response.ok()),
    page.getByRole("button", { name: "Download bundle" }).click(),
  ]);
  await Promise.all([
    page.waitForResponse((response) => response.url().endsWith("/audit/packs/pack-demo-001/bundle/hash") && response.ok()),
    page.getByRole("button", { name: "Download hash" }).click(),
  ]);

  await openWorkbenchTab(page, "Debug");
  await expect(page.getByText("/audit/packs/pack-demo-001/legal-hold")).toBeVisible();
  await expect(page.getByText("/audit/packs/pack-demo-001/bundle/hash")).toBeVisible();
});
