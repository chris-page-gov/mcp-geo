import { connectPlayground, expect, loadHostedWidget, openWorkbenchTab, test } from "../support/full_playground.js";

test("covers hosted widget smoke tests, sanitized tool fallback, rejected bridge events, and debug clearing", async ({
  page,
}) => {
  await connectPlayground(page);

  const routeFrame = await loadHostedWidget(page, "ui_route_planner");
  await expect(routeFrame.locator("#statusBadge")).toContainText("Host connected");

  const geographyFrame = await loadHostedWidget(page, "ui_geography_selector");
  await geographyFrame.locator("#queryInput").fill("Test");
  await geographyFrame.locator("#searchButton").click();
  await expect(geographyFrame.locator("#flowStatus")).toContainText("Found");
  await expect(geographyFrame.locator("#results")).toContainText("1 Test Street");

  const featureFrame = await loadHostedWidget(page, "ui_feature_inspector");
  await expect(featureFrame.locator("#statusBadge")).toContainText("Host connected");

  const statisticsFrame = await loadHostedWidget(page, "ui_statistics_dashboard");
  await expect(statisticsFrame.locator("#status")).toContainText("Host connected");

  const boundaryFrame = await loadHostedWidget(page, "ui_boundary_explorer");
  await expect(boundaryFrame.locator("#hostStatus")).toContainText(/Host connected/);

  await loadHostedWidget(page, "ui_route_planner");
  await page
    .frameLocator("iframe")
    .locator("body")
    .evaluate(() => {
      window.parent.postMessage(
        {
          jsonrpc: "2.0",
          id: 991,
          method: "tools/call",
          params: {
            name: "os_route.get",
            arguments: {
              stops: [{ query: "A" }, { query: "B" }],
              profile: "drive",
            },
          },
        },
        "*"
      );
    });

  await openWorkbenchTab(page, "Debug");
  await expect(page.getByText("TOKEN_INVALID").first()).toBeVisible();
  await expect(page.getByText("ui://mcp-geo/route-planner").first()).toBeVisible();
  await expect(page.getByText("allow-scripts", { exact: true })).toBeVisible();
  await expect(page.getByText("Widget bridge event rejected").first()).toBeVisible();

  await page.getByRole("button", { name: "Clear debug log" }).click();
  await page.getByRole("button", { name: "Clear request history" }).click();
  await expect(page.getByText("No debug entries yet.")).toBeVisible();

  await openWorkbenchTab(page, "Explorer");
  await expect(page.getByText("No MCP or host interactions captured yet.")).toBeVisible();
});
