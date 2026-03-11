import { createAuditSmokeSession, getLiveRoutePreflight } from "../support/live_smoke.js";
import {
  connectPlayground,
  expect,
  loadHostedWidget,
  openWorkbenchTab,
  selectScenario,
  test,
} from "../support/full_playground.js";

test("connects and completes the live SG03 route flow when preflight is satisfied", async ({
  page,
  request,
}) => {
  const preflight = await getLiveRoutePreflight(request);
  test.skip(!preflight.ready, preflight.reason || "Live route preflight is not satisfied.");

  await connectPlayground(page);
  await openWorkbenchTab(page, "Routing");
  await selectScenario(page, "SG03");
  await page.getByRole("button", { name: "Load demo guidance" }).click();

  const frame = page.frameLocator("iframe");
  await expect(frame.locator("#startInput")).toHaveValue(/Retford Library/);
  await expect(frame.locator("#endInput")).toHaveValue(/Goodwin Hall/);
  await expect(frame.locator("#routeMode")).toHaveValue("emergency");

  await frame.locator("#calculateRoute").click();
  await expect(frame.locator("#flowStatus")).not.toContainText("RPC timeout");
  await expect(frame.locator("#flowStatus")).toContainText("Route ready");
});

test("runs an audit and FOI smoke flow against the live backend", async ({ page }) => {
  const sessionFixture = await createAuditSmokeSession();
  try {
    await connectPlayground(page);
    await openWorkbenchTab(page, "Audit / FOI");

    await page.getByPlaceholder("/path/to/session").fill(sessionFixture.sessionDir);
    await page.getByRole("button", { name: "Normalise session" }).click();
    await expect(page.getByText("event-ledger.jsonl")).toBeVisible();

    await page.getByRole("button", { name: "Build pack" }).click();
    await expect(page.locator(".list-item").first()).toBeVisible();
    await expect(page.getByRole("button", { name: "Verify integrity" })).toBeVisible();

    await page.getByRole("button", { name: "Verify integrity" }).click();
    await expect(page.getByText('"verified": true')).toBeVisible();

    await page.getByRole("button", { name: "FOI redact" }).click();
    await expect(page.getByText("foi_redacted").first()).toBeVisible();
  } finally {
    await sessionFixture.cleanup();
  }
});

test("renders the benchmark workbench and supports Explorer handoff on the live backend", async ({
  page,
}) => {
  await connectPlayground(page);
  await openWorkbenchTab(page, "Benchmarks");

  await expect(page.locator(".benchmark-list .list-item")).toHaveCount(20);
  await page.getByLabel("Scenario ID").fill("SG03");
  await page.getByRole("button", { name: /SG03/ }).click();
  await page.getByRole("button", { name: "Prefill tool" }).click();

  await expect(page.getByRole("button", { name: "Explorer", exact: true })).toHaveClass(/active/);
  await expect(page.getByText("Details").first()).toBeVisible();
  await expect(page.getByRole("button", { name: /os_apps_render_route_planner|os_apps\\.render_route_planner/i })).toBeVisible();
});

test("hosts an additional live widget preview without bridge or asset failures", async ({ page }) => {
  await connectPlayground(page);
  const frame = await loadHostedWidget(page, "ui_geography_selector");
  await expect(frame.locator("#status")).toContainText("Host connected");
  await expect(frame.locator("body")).not.toContainText("maplibre_missing");
});
