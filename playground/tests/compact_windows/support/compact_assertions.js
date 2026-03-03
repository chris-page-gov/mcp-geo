import { expect } from "@playwright/test";

export function trackPageErrors(page) {
  const errors = [];
  page.on("pageerror", (error) => {
    errors.push(String(error && error.message ? error.message : error));
  });
  return errors;
}

export async function assertNoPageErrors(errors, contextLabel = "page") {
  expect(
    errors,
    `${contextLabel} should not raise uncaught runtime exceptions.\n${errors.join("\n")}`
  ).toEqual([]);
}

export async function assertCompactGlobalContract(
  page,
  { ctaSelector = "[data-testid='primary-cta']", statusSelector = "[data-testid='status-strip']" } = {}
) {
  await expect(page.locator(ctaSelector)).toHaveCount(1);
  await expect(page.locator(statusSelector)).toHaveCount(1);

  await expect
    .poll(() =>
      page.evaluate(() => ({
        compact: document.body?.dataset?.compact || null,
        overflowX: document.body?.dataset?.overflowX || null,
        overflowPx: Number(document.body?.dataset?.overflowPx || "0"),
        ctaVisible: document.body?.dataset?.ctaVisible || null,
        statusVisible: document.body?.dataset?.statusVisible || null,
        ctaDockVisible: Boolean(document.querySelector("[data-testid='compact-cta-dock-button']")),
        statusDockVisible: Boolean(document.querySelector("[data-testid='compact-status-dock']")),
      }))
    )
    .toEqual(expect.objectContaining({ compact: "true", overflowX: "false" }));

  await expect
    .poll(() =>
      page.evaluate(() => {
        const statusVisible = document.body?.dataset?.statusVisible === "true";
        const statusDockVisible = Boolean(document.querySelector("[data-testid='compact-status-dock']"));
        const ctaVisible = document.body?.dataset?.ctaVisible === "true";
        const ctaDockVisible = Boolean(document.querySelector("[data-testid='compact-cta-dock-button']"));
        return (ctaVisible || ctaDockVisible) && (statusVisible || statusDockVisible);
      })
    )
    .toBeTruthy();
}

export async function assertKeyboardReachesTarget(page, targetSelector, maxTabs = 24) {
  await page.locator("body").click({ position: { x: 8, y: 8 } });
  for (let index = 0; index < maxTabs; index += 1) {
    await page.keyboard.press("Tab");
    const matched = await page.evaluate((selector) => {
      const active = document.activeElement;
      if (!active) {
        return false;
      }
      if (active.matches(selector)) {
        return true;
      }
      return Boolean(active.closest(selector));
    }, targetSelector);
    if (matched) {
      return;
    }
  }
  throw new Error(`Keyboard focus did not reach ${targetSelector} within ${maxTabs} Tab presses.`);
}

export async function sendHostContextChanged(page, patch) {
  await page.evaluate((value) => {
    window.postMessage(
      {
        jsonrpc: "2.0",
        method: "ui/notifications/host-context-changed",
        params: value,
      },
      "*"
    );
  }, patch);
}

export async function waitForCompactWidthAtMost(page, maxWidth) {
  await expect
    .poll(() => page.evaluate(() => Number(document.body?.dataset?.compactWidth || "0")))
    .toBeLessThanOrEqual(maxWidth);
}

export async function readJsonText(page, selector) {
  return page.locator(selector).evaluate((node) => {
    const text = String(node.textContent || "{}");
    return JSON.parse(text);
  });
}

export async function getSelectOptionValues(page, selector) {
  return page.locator(selector).evaluate((node) => {
    if (!(node instanceof HTMLSelectElement)) {
      return [];
    }
    return Array.from(node.options)
      .map((option) => option.value)
      .filter((value) => String(value).trim().length > 0);
  });
}

export async function setRangeValue(page, selector, value) {
  await page.locator(selector).evaluate(
    (node, nextValue) => {
      if (!(node instanceof HTMLInputElement)) {
        return;
      }
      node.value = String(nextValue);
      node.dispatchEvent(new Event("input", { bubbles: true }));
      node.dispatchEvent(new Event("change", { bubbles: true }));
    },
    String(value)
  );
}

export async function expectToolsCalled(page, toolNames) {
  const calls = await page.evaluate(() => {
    const bridge = window.__MCP_COMPACT_TEST_BRIDGE__;
    if (!bridge || typeof bridge.getToolCalls !== "function") {
      return [];
    }
    return bridge.getToolCalls();
  });
  const calledNames = new Set(calls.map((entry) => entry.name));
  toolNames.forEach((name) => {
    expect(calledNames.has(name), `Expected tool call for ${name}`).toBeTruthy();
  });
}
