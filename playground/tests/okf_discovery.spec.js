import { expect, test } from "@playwright/test";

const backendUrl = process.env.OKF_DISCOVERY_BASE_URL || "http://127.0.0.1:8000";
const expectedBuildingIds = [
  "os-catalog:os.features.ngd.collection.bld-fts-building-1.items",
  "os-catalog:os.features.ngd.collection.bld-fts-buildingline-1.items",
].sort();

function sorted(values) {
  return [...values].sort();
}

test("keeps an OS Features building result set identical from List to Map", async ({
  page,
}) => {
  await page.route("https://tile.openstreetmap.org/**", (route) => route.abort());

  await page.goto(`${backendUrl}/okf-discovery`);

  await expect(page).toHaveURL(`${backendUrl}/ui/okf-discovery`);
  await expect(
    page.getByRole("heading", { name: "Find the data behind the map." })
  ).toBeVisible();
  await expect(page.getByRole("status").first()).toContainText(
    "404 records · same-origin HTTP · deterministic snapshot"
  );

  await page.getByLabel("Search data, identifiers or places").fill("buildings");
  await page.getByLabel("Capability family").selectOption("os_features");

  const listState = await page.evaluate(() => window.__OKF_DISCOVERY__.getState());
  const listIds = await page.locator("#record-list [data-record-id]").evaluateAll((cards) =>
    cards.map((card) => card.dataset.recordId)
  );

  expect(sorted(listIds)).toEqual(expectedBuildingIds);
  expect(sorted(listState.filteredIds)).toEqual(expectedBuildingIds);
  expect(listState.candidateCount).toBe(expectedBuildingIds.length);
  expect(listState.mapEligibleCount).toBe(expectedBuildingIds.length);

  const selectedTitle = "OS NGD items: bld-fts-building-1";
  await page
    .locator(`[data-record-id="${expectedBuildingIds[0]}"]`)
    .click();
  await expect(
    page.getByRole("heading", { level: 2, name: selectedTitle })
  ).toBeVisible();

  await page.getByRole("tab", { name: "Map" }).click();
  await expect(page.getByRole("tabpanel", { name: "Map" })).toBeVisible();
  await expect(page.locator("#result-summary")).toHaveText(
    "2 spatial records mapped from 2 matches"
  );

  const mapSnapshot = await page.evaluate(() => ({
    state: window.__OKF_DISCOVERY__.getState(),
    features: window.__OKF_DISCOVERY__.mapFeatures(),
  }));
  const mappedIds = mapSnapshot.features.features.flatMap((feature) =>
    JSON.parse(feature.properties.recordIds)
  );

  expect(mapSnapshot.state.tab).toBe("map");
  expect(sorted(mapSnapshot.state.filteredIds)).toEqual(sorted(listIds));
  expect(sorted(mappedIds)).toEqual(sorted(listIds));
  expect(mappedIds).toHaveLength(listIds.length);
  await expect(
    page.getByRole("heading", { level: 2, name: selectedTitle })
  ).toBeVisible();
});
