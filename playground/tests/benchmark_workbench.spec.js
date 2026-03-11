import { expect, test } from "@playwright/test";

import { installAuditMocks, installPlaygroundMocks } from "./support/mock_playground.js";

test("renders the benchmark workbench with filtering, blocked scenarios, and tool prefill", async ({
  page,
}) => {
  await installPlaygroundMocks(page);
  await installAuditMocks(page);

  await page.goto("/");
  await page.getByRole("button", { name: "Connect", exact: true }).click();
  await page.getByRole("button", { name: "Benchmarks" }).click();

  await expect(page.getByText("SG20")).toBeVisible();
  await page.getByLabel("Support level").selectOption("blocked");
  await page.getByRole("button", { name: /SG20/ }).click();
  await expect(page.getByText("Evidence-first blocked scenario")).toBeVisible();

  await page.getByLabel("Support level").selectOption("all");
  await page.getByLabel("Scenario ID").fill("SG03");
  await page.getByText("SG03").first().click();
  await page.getByRole("button", { name: "Prefill tool" }).click();

  await expect(page.getByRole("button", { name: "Explorer" })).toHaveClass(/active/);
  await expect(page.locator("textarea").first()).toHaveValue(/Retford Library/);
});
