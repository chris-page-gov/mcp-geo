import { connectPlayground, expect, loadHostedWidget, openWorkbenchTab, test } from "../support/full_playground.js";

test("covers explorer connection, descriptor reload, tool calls, UI previews, same-origin toggle, and prompt logging", async ({
  page,
}) => {
  await connectPlayground(page);

  await openWorkbenchTab(page, "Explorer");
  await page.getByRole("button", { name: "Reload descriptor" }).click();

  await page.getByPlaceholder("Filter tools").fill("descriptor");
  await page.getByRole("button", { name: /os_mcp_descriptor/i }).click();
  await page.getByRole("button", { name: "Run tool" }).click();

  const routeFrame = await loadHostedWidget(page, "ui_route_planner");
  await expect(routeFrame.locator("#statusBadge")).toContainText("Host connected");
  await page.getByTestId("host-viewport-mode").selectOption("compact");
  await page.getByTestId("host-compact-width").fill("360");
  await page.getByTestId("host-compact-height").fill("520");
  const previewToggle = page.locator(".preview-toolbar .icon-button").first();
  await previewToggle.click();
  await previewToggle.click();

  await openWorkbenchTab(page, "Explorer");
  await page.getByPlaceholder("Filter resources").fill("geography");
  await page.getByRole("button", { name: /ui_geography_selector/i }).click();
  await page.getByRole("button", { name: "Load UI HTML" }).click();
  await expect(page.frameLocator("iframe").locator("#status")).toContainText("Host connected");
  const unsafeToggle = page.getByLabel("Allow same-origin for this UI (unsafe)");
  await expect(unsafeToggle).not.toBeChecked();
  await unsafeToggle.click({ force: true });

  const promptBox = page.getByRole("textbox", { name: "Prompt", exact: true });
  await promptBox.fill("Summarise the SG03 route handoff");
  await page.getByLabel("Context (optional)").fill("Explorer full UI coverage");
  await page.getByRole("button", { name: "Log prompt" }).click();
  await expect(promptBox).toHaveValue("");

  await expect(page.getByText('"method": "tools/call"').first()).toBeVisible();
  await expect(page.getByText('"method": "resources/read"').first()).toBeVisible();

  await page.getByRole("button", { name: "Disconnect" }).click();
  await expect(page.getByRole("button", { name: "Connect", exact: true })).toBeEnabled();
});
