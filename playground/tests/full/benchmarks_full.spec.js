import { connectPlayground, expect, openWorkbenchTab, test } from "../support/full_playground.js";

test("covers benchmark filtering, blocked scenarios, tool prefill, widget handoff, and latest evidence views", async ({
  page,
}) => {
  await connectPlayground(page);
  await openWorkbenchTab(page, "Benchmarks");

  await expect(page.locator(".benchmark-list .list-item")).toHaveCount(20);

  await page.getByLabel("Support level").selectOption("blocked");
  await expect(page.locator(".benchmark-list .list-item")).toHaveCount(2);
  await page.getByRole("button", { name: /SG20/ }).click();
  await expect(page.getByText("Evidence-first blocked scenario")).toBeVisible();

  await page.getByLabel("Support level").selectOption("all");
  await page.getByLabel("Tool family").selectOption("routing");
  await page.getByLabel("Scenario ID").fill("SG03");
  await page.getByRole("button", { name: /SG03/ }).click();
  await expect(page.getByText('"scenarioId": "SG03"').first()).toBeVisible();

  await page.getByRole("button", { name: "Prefill tool" }).click();
  await expect(page.getByRole("button", { name: "Explorer", exact: true })).toHaveClass(/active/);
  await expect(page.locator('textarea[rows="10"]').first()).toHaveValue(/Retford Library/);

  await openWorkbenchTab(page, "Benchmarks");
  await page.getByRole("button", { name: /SG03/ }).click();
  await page.getByRole("button", { name: "Open widget" }).click();
  await expect(page.getByRole("button", { name: "Routing", exact: true })).toHaveClass(/active/);
  await expect(page.frameLocator("iframe").locator("#statusBadge")).toContainText("Host connected");
});
