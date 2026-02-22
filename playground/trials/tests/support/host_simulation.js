import fs from "fs";
import path from "path";

function asNumber(value, fallback) {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }
  return fallback;
}

export function loadHostCapabilityProfiles(repoRoot) {
  const fixturePath = path.join(
    repoRoot,
    "playground",
    "trials",
    "fixtures",
    "host_capability_profiles.json"
  );
  const parsed = JSON.parse(fs.readFileSync(fixturePath, "utf-8"));
  const profiles = Array.isArray(parsed.profiles) ? parsed.profiles : [];
  return {
    fixturePath,
    version: parsed.version || "unknown",
    profiles,
  };
}

export function profileById(catalog, profileId) {
  return catalog.profiles.find((entry) => entry.id === profileId) || null;
}

function seededRandom(seed, idx) {
  const raw = Math.sin(seed * 1000 + idx * 97.17) * 10000;
  return raw - Math.floor(raw);
}

function deterministicAddressResults(seed = 7) {
  const rows = [];
  for (let idx = 0; idx < 2; idx += 1) {
    // Keep deterministic points inside the local-layer polygon used by trial-4.
    const latJitter = seededRandom(seed, idx) * 0.00035;
    const lonJitter = seededRandom(seed + 3, idx) * 0.00035;
    rows.push({
      uprn: `10000000${idx + 1}`,
      address: `${idx + 1} Trial Street`,
      lat: 51.5049 + latJitter,
      lon: -0.1208 + lonJitter,
      classificationDescription: "Residential",
    });
  }
  return rows;
}

function deterministicInventory(seed = 7) {
  const points = deterministicAddressResults(seed).map((row) => ({
    uprn: row.uprn,
    lat: row.lat,
    lon: row.lon,
    address: `${row.address}, London SW1A 1AA`,
  }));
  return {
    layers: {
      uprns: { results: points },
      buildings: { features: [] },
      road_links: { features: [] },
      path_links: { features: [] },
    },
  };
}

export async function installDeterministicHostBridge(page, options = {}) {
  const seed = asNumber(options.seed, 7);
  const profile = options.profile || {};
  const inventory = options.inventory || deterministicInventory(seed);

  await page.addInitScript(
    ({ selectedProfile, selectedSeed, selectedInventory }) => {
      const randomValue = (seedValue, idxValue) => {
        const raw = Math.sin(seedValue * 1000 + idxValue * 97.17) * 10000;
        return raw - Math.floor(raw);
      };

      const addressResults = [];
      for (let idx = 0; idx < 2; idx += 1) {
        const latJitter = randomValue(selectedSeed, idx) * 0.00035;
        const lonJitter = randomValue(selectedSeed + 3, idx) * 0.00035;
        addressResults.push({
          uprn: `10000000${idx + 1}`,
          address: `${idx + 1} Trial Street`,
          lat: 51.5049 + latJitter,
          lon: -0.1208 + lonJitter,
          classificationDescription: "Residential",
        });
      }

      const hostContext =
        selectedProfile && typeof selectedProfile.hostContext === "object"
          ? selectedProfile.hostContext
          : {
              displayMode: "inline",
              availableDisplayModes: ["inline"],
              platform: "web",
              userAgent: "playwright",
              containerDimensions: { maxHeight: 700 },
              mcpGeo: { proxyBase: "http://localhost:8000" },
            };

      window.__MCP_HOST_PROFILE__ = selectedProfile;
      window.__MCP_HOST_SEED__ = selectedSeed;

      const handleRequest = (message) => {
        if (!message || message.jsonrpc !== "2.0" || message.id === undefined) {
          return null;
        }
        // Ignore response envelopes and only process request messages.
        if (
          Object.prototype.hasOwnProperty.call(message, "result") ||
          Object.prototype.hasOwnProperty.call(message, "error")
        ) {
          return null;
        }

        const method = typeof message.method === "string" ? message.method : null;
        if (!method) {
          return null;
        }

        const respond = (result) => {
          return { jsonrpc: "2.0", id: message.id, result };
        };

        if (method === "ui/initialize") {
          return respond({
            protocolVersion: "2026-01-26",
            hostContext,
          });
        }

        if (method !== "tools/call") {
          return respond({});
        }

        const name = message.params?.name || message.params?.tool;
        const normalized = typeof name === "string" ? name.replaceAll(".", "_") : "";

        if (name === "os_places.search") {
          return {
            jsonrpc: "2.0",
            id: message.id,
            error: { code: -32000, message: "Tool not found on server: os_places.search" },
          };
        }

        if (normalized === "os_places_search") {
          return respond({ results: addressResults });
        }
        if (normalized === "os_apps_log_event") {
          return respond({ status: "logged" });
        }
        if (normalized === "admin_lookup_containing_areas") {
          return respond({ results: [] });
        }
        if (normalized === "admin_lookup_area_geometry") {
          return respond({});
        }
        if (normalized === "os_map_inventory") {
          return respond(selectedInventory);
        }

        return respond({});
      };

      window.__MCP_HOST_BRIDGE_HANDLE__ = handleRequest;

      window.addEventListener("message", (event) => {
        const response = handleRequest(event.data);
        if (response) {
          window.postMessage(response, "*");
        }
      });
    },
    {
      selectedProfile: profile,
      selectedSeed: seed,
      selectedInventory: inventory,
    }
  );
}

export async function roundTripUiInitialize(page) {
  return page.evaluate(async () => {
    const requestId = `init-${Date.now()}`;
    if (typeof window.__MCP_HOST_BRIDGE_HANDLE__ === "function") {
      const response = window.__MCP_HOST_BRIDGE_HANDLE__({
        jsonrpc: "2.0",
        id: requestId,
        method: "ui/initialize",
        params: {},
      });
      if (!response) {
        throw new Error("Host bridge did not return a response");
      }
      if (response.error) {
        throw new Error(response.error.message || "RPC error");
      }
      return response.result || null;
    }
    return await new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error("Timed out waiting for ui/initialize response"));
      }, 2000);
      const handler = (event) => {
        const data = event.data;
        if (!data || data.jsonrpc !== "2.0" || data.id !== requestId) {
          return;
        }
        if (typeof data.method === "string") {
          return;
        }
        if (
          !Object.prototype.hasOwnProperty.call(data, "result") &&
          !Object.prototype.hasOwnProperty.call(data, "error")
        ) {
          return;
        }
        window.removeEventListener("message", handler);
        clearTimeout(timeout);
        if (data.error) {
          reject(new Error(data.error.message || "RPC error"));
          return;
        }
        resolve(data.result || null);
      };
      window.addEventListener("message", handler);
      window.postMessage(
        {
          jsonrpc: "2.0",
          id: requestId,
          method: "ui/initialize",
          params: {},
        },
        "*"
      );
    });
  });
}
