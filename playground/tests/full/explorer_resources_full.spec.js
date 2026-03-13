import { connectPlayground, expect, openWorkbenchTab, test } from "../support/full_playground.js";

const RESOURCE_FIXTURES = [
  {
    name: "ui_route_planner",
    uri: "ui://mcp-geo/route-planner",
    type: "ui",
    assertLoaded: async (frame) => {
      await expect(frame.locator("#statusBadge")).toContainText("Host connected");
    },
  },
  {
    name: "ui_geography_selector",
    uri: "ui://mcp-geo/geography-selector",
    type: "ui",
    assertLoaded: async (frame) => {
      await expect(frame.locator("#status")).toContainText("Host connected");
    },
  },
  {
    name: "ui_feature_inspector",
    uri: "ui://mcp-geo/feature-inspector",
    type: "ui",
    assertLoaded: async (frame) => {
      await expect(frame.locator("#statusBadge")).toContainText("Host connected");
    },
  },
  {
    name: "ui_statistics_dashboard",
    uri: "ui://mcp-geo/statistics-dashboard",
    type: "ui",
    assertLoaded: async (frame) => {
      await expect(frame.locator("#status")).toContainText("Host connected");
    },
  },
  {
    name: "ui_boundary_explorer",
    uri: "ui://mcp-geo/boundary-explorer",
    type: "ui",
    assertLoaded: async (frame) => {
      await expect(frame.locator("#hostStatus")).toContainText(/Host connected/);
    },
  },
  {
    name: "data_stakeholder_benchmark_pack",
    uri: "resource://mcp-geo/stakeholder-benchmark-pack",
    type: "data",
  },
  {
    name: "data_stakeholder_benchmark_live_run_latest",
    uri: "resource://mcp-geo/stakeholder-benchmark-live-run-latest",
    type: "data",
  },
];

async function selectResource(page, resource) {
  await openWorkbenchTab(page, "Explorer");
  await page.getByPlaceholder("Filter resources").fill(resource.name);
  await page.getByRole("button", { name: new RegExp(resource.name, "i") }).click();
  await expect(page.getByRole("heading", { name: resource.name, level: 3 })).toBeVisible();
  const metadataBlock = page
    .locator(".details-block")
    .filter({ has: page.getByText("Resource metadata", { exact: true }) })
    .locator("pre");
  await expect(metadataBlock).toContainText(resource.uri);
}

test("keeps the original Explorer resource flows available for every baseline fixture resource", async ({
  page,
}) => {
  await connectPlayground(page);
  await openWorkbenchTab(page, "Explorer");

  for (const resource of RESOURCE_FIXTURES) {
    await selectResource(page, resource);
    if (resource.type === "ui") {
      await page.getByRole("button", { name: "Load UI HTML" }).click();
      const frame = page.frameLocator("iframe");
      await resource.assertLoaded(frame);
    } else {
      await expect(page.getByRole("button", { name: "Load UI HTML" })).toHaveCount(0);
    }
  }
});
