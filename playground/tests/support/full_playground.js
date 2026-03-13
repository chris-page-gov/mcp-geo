import { expect, test as base } from "@playwright/test";

async function attachFailureArtifacts(page, testInfo, consoleEntries, networkEntries) {
  if (testInfo.status === testInfo.expectedStatus) {
    return;
  }
  await testInfo.attach("console-log", {
    body: Buffer.from(JSON.stringify(consoleEntries, null, 2)),
    contentType: "application/json",
  });
  await testInfo.attach("network-log", {
    body: Buffer.from(JSON.stringify(networkEntries, null, 2)),
    contentType: "application/json",
  });
  if (!page.isClosed()) {
    try {
      await page.getByRole("button", { name: "Debug" }).click({ timeout: 2000 });
      const debugText = await page.locator("body").innerText();
      await testInfo.attach("debug-tab-snapshot", {
        body: Buffer.from(debugText),
        contentType: "text/plain",
      });
      await page.screenshot({
        path: testInfo.outputPath("debug-tab.png"),
        fullPage: true,
      });
    } catch (_error) {
      // Best-effort failure capture only.
    }
  }
}

export const test = base.extend({
  page: async ({ page }, use, testInfo) => {
    const consoleEntries = [];
    const networkEntries = [];
    page.on("console", (message) => {
      consoleEntries.push({
        type: message.type(),
        text: message.text(),
      });
    });
    page.on("response", (response) => {
      networkEntries.push({
        url: response.url(),
        status: response.status(),
        ok: response.ok(),
      });
    });
    page.on("requestfailed", (request) => {
      networkEntries.push({
        url: request.url(),
        failed: true,
        method: request.method(),
        errorText: request.failure()?.errorText || "requestfailed",
      });
    });
    await use(page);
    await attachFailureArtifacts(page, testInfo, consoleEntries, networkEntries);
  },
});

export { expect };

export async function openWorkbenchTab(page, name) {
  await page.getByRole("button", { name, exact: true }).click();
}

export async function connectPlayground(page) {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Playground security hardening and demo workbench" })
  ).toBeVisible();
  await expect(page.evaluate(() => !window.__MCP_PLAYGROUND_MOCK__)).resolves.toBe(true);
  await page.getByRole("button", { name: "Connect", exact: true }).click();
  await expect(page.locator("text=/^connected$/").first()).toBeVisible();
  await expect(page.getByRole("button", { name: /os_mcp_descriptor/i })).toBeVisible();
}

export async function loadHostedWidget(page, resourceName) {
  await openWorkbenchTab(page, "Explorer");
  await page.getByRole("button", { name: new RegExp(resourceName, "i") }).click();
  await page.getByRole("button", { name: "Load UI HTML" }).click();
  const frame = page.frameLocator("iframe");
  await expect(frame.locator('[data-testid="status-strip"]').first()).toContainText(
    /Host connected/
  );
  return frame;
}

export async function selectScenario(page, id) {
  const scenarioButton = page
    .locator("button.list-item")
    .filter({ hasText: new RegExp(`\\b${id}\\b`) })
    .first();
  await expect(scenarioButton).toBeVisible();
  await scenarioButton.click();
}
