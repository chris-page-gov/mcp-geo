import { connectPlayground, expect, openWorkbenchTab, selectScenario, test } from "../support/full_playground.js";

test("covers SG03 and SG12 routing demos and surfaces explicit backend blockers instead of RPC timeouts", async ({
  page,
}) => {
  await connectPlayground(page);
  await openWorkbenchTab(page, "Routing");
  await expect(page.getByText("2 seeded demos")).toBeVisible();

  await selectScenario(page, "SG03");
  await page.getByRole("button", { name: "Load demo guidance" }).click();

  const frame = page.frameLocator("iframe");
  await expect(frame.locator("#startInput")).toHaveValue(/Retford Library/);
  await expect(frame.locator("#endInput")).toHaveValue(/Goodwin Hall/);
  await expect(frame.locator("#routeMode")).toHaveValue("emergency");

  await frame.locator("#calculateRoute").click();
  await expect(frame.locator("#flowStatus")).toContainText("Route ready");
  await expect(frame.locator("#payload")).toContainText("mrn-fixture-2026-03-11");
  await expect(frame.locator("#flowStatus")).not.toContainText("RPC timeout");

  await selectScenario(page, "SG12");
  await page.getByRole("button", { name: "Load demo guidance" }).click();
  await expect(frame.locator("#startInput")).toHaveValue(/Wharf Road/);
  await expect(frame.locator("#endInput")).toHaveValue(/Goodwin Hall/);
  await expect(page.getByText("Nearest responder candidate")).toBeVisible();

  await frame.locator("#startInput").fill("BLOCK_ROUTE");
  await frame.locator("#calculateRoute").click();
  await expect(frame.locator("#flowStatus")).toContainText("Route graph not ready");
  await expect(frame.locator("#payload")).toContainText("ROUTE_GRAPH_NOT_READY");
  await expect(frame.locator("#flowStatus")).not.toContainText("RPC timeout");
});
