(() => {
  "use strict";

  const EXPLORER_HOUSE = Object.freeze({
    id: "demo-location:explorer-house",
    title: "Explorer House, Ordnance Survey",
    postcode: "SO16 0AS",
    coordinates: [-1.470433, 50.937708],
    bbox: [-1.48, 50.93, -1.46, 50.945],
  });
  const FEATURED_FAMILIES = new Set(["os_places", "os_features", "os_linked_ids"]);
  const STATIC_SNAPSHOT_MODE =
    document.documentElement.dataset.staticSnapshot === "true";
  const DATA_BASE = STATIC_SNAPSHOT_MODE ? "./data" : "/okf-discovery/data";
  const RESOURCE_URIS = Object.freeze({
    records: "resource://mcp-geo/okf-discovery-records",
    spatial: "resource://mcp-geo/okf-discovery-spatial-index",
    bindings: "resource://mcp-geo/okf-discovery-mcp-bindings",
  });
  const JSON_FILE_NAMES = Object.freeze({
    records: "records.json",
    spatial: "spatial-index.json",
    bindings: "mcp-bindings.json",
  });

  const elements = {
    snapshotStatus: document.getElementById("snapshot-status"),
    searchForm: document.getElementById("search-form"),
    searchInput: document.getElementById("search-input"),
    family: document.getElementById("family-filter"),
    type: document.getElementById("type-filter"),
    access: document.getElementById("access-filter"),
    geography: document.getElementById("geography-filter"),
    reset: document.getElementById("reset-filters"),
    summary: document.getElementById("result-summary"),
    list: document.getElementById("record-list"),
    empty: document.getElementById("empty-state"),
    listTab: document.getElementById("list-tab"),
    mapTab: document.getElementById("map-tab"),
    listPanel: document.getElementById("list-panel"),
    mapPanel: document.getElementById("map-panel"),
    mapUnavailable: document.getElementById("map-unavailable"),
    mapStatus: document.getElementById("map-status"),
    viewportFilter: document.getElementById("viewport-filter"),
    explorerHouse: document.getElementById("explorer-house"),
    detailPanel: document.getElementById("detail-panel"),
    detailPlaceholder: document.getElementById("detail-placeholder"),
    detailContent: document.getElementById("detail-content"),
  };

  const state = {
    records: [],
    filtered: [],
    selectedId: null,
    query: "",
    family: "",
    type: "",
    access: "",
    geography: "",
    tab: "list",
    filterToViewport: false,
    map: null,
    mapReady: false,
    mapSourceReady: false,
    mapPopup: null,
    demoLocation: EXPLORER_HOUSE,
    dataMode: "",
    candidateCount: 0,
    mapEligibleCount: 0,
  };

  let rpcId = 0;
  const pendingCalls = new Map();

  function postToHost(message) {
    if (window.parent && window.parent !== window) {
      window.parent.postMessage(message, "*");
    }
  }

  function rpcCall(method, params, timeoutMs = 10000) {
    if (!window.parent || window.parent === window) {
      return Promise.reject(new Error("MCP host bridge is unavailable"));
    }
    rpcId += 1;
    const id = `okf-discovery-${rpcId}`;
    postToHost({ jsonrpc: "2.0", id, method, params });
    return new Promise((resolve, reject) => {
      const timeout = window.setTimeout(() => {
        pendingCalls.delete(id);
        reject(new Error(`MCP host RPC timed out: ${method}`));
      }, timeoutMs);
      pendingCalls.set(id, { resolve, reject, timeout });
    });
  }

  window.addEventListener("message", (event) => {
    if (!window.parent || event.source !== window.parent) {
      return;
    }
    const message = event && event.data;
    if (!message || message.jsonrpc !== "2.0" || message.id === undefined) {
      return;
    }
    const pending = pendingCalls.get(message.id);
    if (!pending) {
      return;
    }
    window.clearTimeout(pending.timeout);
    pendingCalls.delete(message.id);
    if (message.error) {
      pending.reject(new Error(message.error.message || "MCP host RPC error"));
      return;
    }
    pending.resolve(message.result);
  });

  function extractWrappedPayload(value) {
    if (!value || typeof value !== "object") {
      return value;
    }
    for (const key of ["structuredContent", "data"]) {
      if (value[key] && typeof value[key] === "object") {
        return extractWrappedPayload(value[key]);
      }
    }
    if (Array.isArray(value.contents)) {
      for (const item of value.contents) {
        if (item && typeof item.text === "string") {
          return parseJsonText(item.text);
        }
        if (item && item.data && typeof item.data === "object") {
          return extractWrappedPayload(item.data);
        }
      }
    }
    if (Array.isArray(value.content)) {
      for (const block of value.content) {
        if (!block || typeof block !== "object") {
          continue;
        }
        if (block.json && typeof block.json === "object") {
          return block.json;
        }
        if (typeof block.text === "string") {
          const parsed = parseJsonText(block.text, false);
          if (parsed !== null) {
            return parsed;
          }
        }
      }
    }
    if (typeof value.text === "string") {
      return parseJsonText(value.text);
    }
    return value;
  }

  function parseJsonText(text, throwOnError = true) {
    try {
      return JSON.parse(text);
    } catch (error) {
      if (throwOnError) {
        throw error;
      }
      return null;
    }
  }

  async function fetchJson(url, timeoutMs = 5000) {
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), timeoutMs);
    try {
      const response = await fetch(url, {
        headers: { Accept: "application/json" },
        signal: controller.signal,
      });
      if (!response.ok) {
        throw new Error(`${response.status} ${response.statusText}`);
      }
      return await response.json();
    } finally {
      window.clearTimeout(timeout);
    }
  }

  async function loadDataSet() {
    const keys = Object.keys(JSON_FILE_NAMES);
    try {
      const values = await Promise.all(
        keys.map((key) => fetchJson(`${DATA_BASE}/${JSON_FILE_NAMES[key]}`))
      );
      state.dataMode = "same-origin HTTP";
      return Object.fromEntries(keys.map((key, index) => [key, values[index]]));
    } catch (httpError) {
      if (!window.parent || window.parent === window) {
        throw new Error(`Static data could not be loaded: ${httpError.message}`);
      }
    }

    const values = await Promise.all(
      keys.map(async (key) => {
        const result = await rpcCall("resources/read", { uri: RESOURCE_URIS[key] });
        return extractWrappedPayload(result);
      })
    );
    state.dataMode = "MCP resources/read bridge";
    return Object.fromEntries(keys.map((key, index) => [key, values[index]]));
  }

  function unwrapArray(payload, keys) {
    if (Array.isArray(payload)) {
      return payload;
    }
    if (!payload || typeof payload !== "object") {
      return [];
    }
    for (const key of keys) {
      if (Array.isArray(payload[key])) {
        return payload[key];
      }
    }
    return [];
  }

  function asStrings(value) {
    if (value === undefined || value === null) {
      return [];
    }
    const values = Array.isArray(value) ? value : [value];
    return values
      .map((item) => {
        if (typeof item === "string" || typeof item === "number") {
          return String(item);
        }
        if (item && typeof item === "object") {
          return item.label || item.name || item.title || item.id || "";
        }
        return "";
      })
      .filter(Boolean);
  }

  function firstString(...values) {
    for (const value of values) {
      if (typeof value === "string" && value.trim()) {
        return value.trim();
      }
    }
    return "";
  }

  function normalizeAccess(record, binding) {
    if (binding && binding.credential_mode === "server-managed") {
      return "Server-managed credential";
    }
    if (typeof record.access === "string") {
      return record.access;
    }
    if (record.access && typeof record.access === "object") {
      return firstString(record.access.label, record.access.mode, record.access.protocol);
    }
    if (record.record_type === "mcp-resource") {
      return "MCP resource";
    }
    if (record.endpoint) {
      return "OS Data Hub API";
    }
    return "Catalogue metadata";
  }

  function normalizeSources(record, spatial) {
    const candidates = [record.documentation, record.provenance, record.source];
    if (spatial && spatial.provenance) {
      candidates.push(spatial.provenance);
    }
    const sources = [];
    const add = (value) => {
      if (!value) {
        return;
      }
      if (Array.isArray(value)) {
        value.forEach(add);
        return;
      }
      if (typeof value === "string") {
        sources.push({ label: value, url: /^https?:\/\//i.test(value) ? value : "" });
        return;
      }
      if (typeof value === "object") {
        const url = firstString(value.url, value.href, value.source);
        const label = firstString(value.label, value.title, value.path, value.kind, url);
        if (label) {
          sources.push({ label, url: /^https?:\/\//i.test(url) ? url : "" });
        }
      }
    };
    candidates.forEach(add);
    const unique = new Map(sources.map((source) => [`${source.label}|${source.url}`, source]));
    return [...unique.values()].slice(0, 6);
  }

  function normalizeCoverage(spatial) {
    if (!spatial || typeof spatial !== "object") {
      return [];
    }
    const coverage = spatial.coverage;
    if (coverage && typeof coverage === "object") {
      return asStrings(coverage.label || coverage.name || coverage);
    }
    return asStrings(coverage || spatial.geographies || spatial.coverage_labels);
  }

  function normalizeData(recordsPayload, spatialPayload, bindingsPayload) {
    const spatialEntries = unwrapArray(spatialPayload, ["records", "entries", "items"]);
    const spatialByRecord = new Map(
      spatialEntries
        .filter((item) => item && item.record_id)
        .map((item) => [String(item.record_id), item])
    );
    const bindings = unwrapArray(bindingsPayload, ["bindings", "records", "items"]);
    const bindingsByRecord = new Map();
    const bindingsByTool = new Map();
    for (const binding of bindings) {
      if (binding && binding.record_id) {
        bindingsByRecord.set(String(binding.record_id), binding);
      }
      if (binding && binding.tool_name) {
        bindingsByTool.set(String(binding.tool_name), binding);
      }
    }

    const demoLocations = unwrapArray(spatialPayload, ["demo_locations"]);
    const explorer = demoLocations.find((item) => item && item.id === EXPLORER_HOUSE.id);
    if (explorer && explorer.geometry && Array.isArray(explorer.geometry.coordinates)) {
      state.demoLocation = {
        ...EXPLORER_HOUSE,
        title: explorer.title || EXPLORER_HOUSE.title,
        postcode: explorer.postcode || EXPLORER_HOUSE.postcode,
        coordinates: explorer.geometry.coordinates.slice(0, 2),
        bbox: Array.isArray(explorer.bbox) ? explorer.bbox : EXPLORER_HOUSE.bbox,
        source: explorer.source || "",
      };
    }

    const rawRecords = unwrapArray(recordsPayload, ["records", "items"]);
    return rawRecords.map((record, index) => {
      const id = firstString(record.id, record.record_id) || `record:${index}`;
      const title = firstString(record.title, record.name, record.tool_name, id);
      const toolName = firstString(
        record.tool_name,
        id.startsWith("tool:") ? id.slice(5) : ""
      );
      const spatial = spatialByRecord.get(id) || null;
      const binding = bindingsByRecord.get(id) || bindingsByTool.get(toolName) || null;
      const family = firstString(
        record.family,
        spatial && spatial.family,
        toolName.includes(".") ? toolName.split(".")[0] : "",
        record.category,
        "other"
      );
      const type = firstString(record.record_type, record.type, record.kind, "knowledge-record");
      const geographies = normalizeCoverage(spatial);
      const keywords = asStrings(record.keywords || record.tags || record.identifiers);
      if (spatial) {
        keywords.push(...asStrings(spatial.identifiers));
        keywords.push(...asStrings(spatial.discovery_modes));
        keywords.push(...asStrings(spatial.geometry_types));
      }
      const featured = Boolean(record.featured || FEATURED_FAMILIES.has(family));
      const hasDemoPoint = Boolean(spatial && FEATURED_FAMILIES.has(family));
      const access = normalizeAccess(record, binding);
      const description = firstString(
        record.description,
        record.summary,
        "No description supplied."
      );
      const searchText = [
        title,
        description,
        toolName,
        family,
        type,
        access,
        ...keywords,
        ...geographies,
        featured ? `Explorer House ${state.demoLocation.postcode}` : "",
      ]
        .join(" ")
        .toLocaleLowerCase("en-GB");
      return {
        id,
        title,
        description,
        family,
        type,
        access,
        toolName,
        keywords: [...new Set(keywords)],
        geographies,
        featured,
        spatial,
        binding,
        sources: normalizeSources(record, spatial),
        searchText,
        mapPoint: hasDemoPoint ? state.demoLocation.coordinates : null,
        raw: record,
      };
    });
  }

  function humanize(value) {
    return String(value || "")
      .replace(/^os_/, "OS ")
      .replace(/[-_]+/g, " ")
      .replace(/\b\w/g, (letter) => letter.toUpperCase());
  }

  function populateSelect(select, values, allLabel) {
    const current = select.value;
    select.replaceChildren(new Option(allLabel, ""));
    [...new Set(values.filter(Boolean))]
      .sort((left, right) => humanize(left).localeCompare(humanize(right), "en-GB"))
      .forEach((value) => select.add(new Option(humanize(value), value)));
    if ([...select.options].some((option) => option.value === current)) {
      select.value = current;
    }
  }

  function populateFacets() {
    populateSelect(elements.family, state.records.map((record) => record.family), "All families");
    populateSelect(elements.type, state.records.map((record) => record.type), "All types");
    populateSelect(
      elements.access,
      state.records.map((record) => record.access),
      "All access modes"
    );
    populateSelect(
      elements.geography,
      state.records.flatMap((record) => record.geographies),
      "All geographies"
    );
  }

  function queryScore(record, query) {
    if (!query) {
      const familyBoost = FEATURED_FAMILIES.has(record.family) ? 30 : 0;
      const featuredBoost = record.featured ? 10 : 0;
      const bindingBoost = record.binding ? 3 : 0;
      return familyBoost + featuredBoost + bindingBoost;
    }
    let score = 0;
    const title = record.title.toLocaleLowerCase("en-GB");
    const tool = record.toolName.toLocaleLowerCase("en-GB");
    if (title === query || tool === query) score += 100;
    if (title.startsWith(query) || tool.startsWith(query)) score += 45;
    if (title.includes(query)) score += 25;
    if (record.family.toLocaleLowerCase("en-GB").includes(query)) score += 18;
    if (record.description.toLocaleLowerCase("en-GB").includes(query)) score += 10;
    if (record.searchText.includes(query)) score += 4;
    if (record.featured) score += 2;
    return score;
  }

  function demoPointInViewport() {
    if (!state.map || !state.mapReady) {
      return true;
    }
    const bounds = state.map.getBounds();
    const [longitude, latitude] = state.demoLocation.coordinates;
    return bounds.contains([longitude, latitude]);
  }

  function applyFilters() {
    const query = state.query.trim().toLocaleLowerCase("en-GB");
    const demoVisible = demoPointInViewport();
    const candidates = state.records
      .filter((record) => !query || record.searchText.includes(query))
      .filter((record) => !state.family || record.family === state.family)
      .filter((record) => !state.type || record.type === state.type)
      .filter((record) => !state.access || record.access === state.access)
      .filter(
        (record) =>
          !state.geography ||
          record.geographies.some((value) => value === state.geography)
      )
      .sort((left, right) => {
        const scoreDifference = queryScore(right, query) - queryScore(left, query);
        return scoreDifference || left.title.localeCompare(right.title, "en-GB");
      });
    state.candidateCount = candidates.length;
    state.mapEligibleCount = candidates.filter((record) => record.mapPoint).length;
    state.filtered = candidates
      .filter((record) => state.tab !== "map" || record.mapPoint)
      .filter(
        (record) =>
          state.tab !== "map" || !state.filterToViewport || demoVisible
      );

    renderResults();
    updateMapData();
    if (state.selectedId && !state.filtered.some((record) => record.id === state.selectedId)) {
      state.selectedId = null;
      renderDetail(null);
    }
  }

  function createBadge(text, className = "") {
    const badge = document.createElement("span");
    badge.className = `badge ${className}`.trim();
    badge.textContent = text;
    return badge;
  }

  function renderResults() {
    elements.list.replaceChildren();
    const total = state.records.length;
    const spatialCount = state.filtered.filter((record) => record.spatial).length;
    const viewportNote = state.tab === "map" && state.filterToViewport
      ? " in this map view"
      : "";
    if (state.tab === "map") {
      elements.summary.textContent =
        `${state.filtered.length.toLocaleString()} spatial records mapped` +
        ` from ${state.candidateCount.toLocaleString()} matches${viewportNote}`;
    } else {
      elements.summary.textContent =
        `${state.filtered.length.toLocaleString()} of ${total.toLocaleString()} records` +
        ` · ${state.mapEligibleCount.toLocaleString()} map-eligible` +
        ` · ${spatialCount.toLocaleString()} spatially described`;
    }
    elements.empty.hidden = state.filtered.length > 0;

    const fragment = document.createDocumentFragment();
    for (const record of state.filtered) {
      const item = document.createElement("li");
      const button = document.createElement("button");
      button.type = "button";
      button.className = "record-card";
      button.dataset.recordId = record.id;
      button.setAttribute("aria-current", String(record.id === state.selectedId));

      const badges = document.createElement("span");
      badges.className = "badge-row";
      badges.append(createBadge(humanize(record.family)));
      badges.append(createBadge(humanize(record.type)));
      if (record.spatial) badges.append(createBadge("Spatial", "badge-spatial"));
      if (record.binding) badges.append(createBadge("MCP ready", "badge-mcp"));

      const heading = document.createElement("h3");
      heading.textContent = record.title;
      const description = document.createElement("p");
      description.textContent = record.description;
      button.append(badges, heading, description);
      item.append(button);
      fragment.append(item);
    }
    elements.list.append(fragment);
  }

  function safeUrl(value) {
    return typeof value === "string" && /^https?:\/\//i.test(value) ? value : "";
  }

  function appendDefinition(list, term, value) {
    if (!value) {
      return;
    }
    const dt = document.createElement("dt");
    dt.textContent = term;
    const dd = document.createElement("dd");
    dd.textContent = value;
    list.append(dt, dd);
  }

  function requestTemplate(record) {
    if (record.binding && record.binding.request_template) {
      return record.binding.request_template;
    }
    if (!record.toolName) {
      return null;
    }
    return {
      jsonrpc: "2.0",
      id: "demo-1",
      method: "tools/call",
      params: { name: record.toolName, arguments: {} },
    };
  }

  function renderDetail(record) {
    elements.detailPlaceholder.hidden = Boolean(record);
    elements.detailContent.hidden = !record;
    elements.detailContent.replaceChildren();
    if (!record) {
      elements.detailPanel.setAttribute("aria-labelledby", "detail-heading");
      return;
    }
    elements.detailPanel.setAttribute("aria-labelledby", "selected-detail-heading");

    const kicker = document.createElement("p");
    kicker.className = "detail-kicker";
    kicker.textContent = `${humanize(record.family)} · ${humanize(record.type)}`;
    const heading = document.createElement("h2");
    heading.id = "selected-detail-heading";
    heading.textContent = record.title;
    const description = document.createElement("p");
    description.className = "detail-description";
    description.textContent = record.description;
    elements.detailContent.append(kicker, heading, description);

    const factsSection = document.createElement("section");
    factsSection.className = "detail-section";
    const factsHeading = document.createElement("h3");
    factsHeading.textContent = "Discovery metadata";
    const facts = document.createElement("dl");
    facts.className = "definition-list";
    appendDefinition(facts, "Record", record.id);
    appendDefinition(facts, "Access", record.access);
    appendDefinition(facts, "Coverage", record.geographies.join(", ") || "Not declared");
    if (record.spatial) {
      appendDefinition(facts, "Identifiers", asStrings(record.spatial.identifiers).join(", "));
      appendDefinition(
        facts,
        "Family geometry potential",
        asStrings(record.spatial.geometry_types).join(", ")
      );
      appendDefinition(
        facts,
        "Family query CRS",
        asStrings(record.spatial.query_crs).join(", ")
      );
      appendDefinition(
        facts,
        "Operation geometry output",
        firstString(record.spatial.operation_contract?.geometry_output)
      );
      appendDefinition(
        facts,
        "Spatial filters",
        asStrings(record.spatial.filter_inputs).join(", ") || "Discovery only"
      );
    }
    if (record.mapPoint) {
      appendDefinition(facts, "Map context", "Explorer House demo query location (not extent)");
    }
    factsSection.append(factsHeading, facts);
    elements.detailContent.append(factsSection);

    if (record.sources.length) {
      const sourceSection = document.createElement("section");
      sourceSection.className = "detail-section";
      const sourceHeading = document.createElement("h3");
      sourceHeading.textContent = "Provenance";
      const sourceList = document.createElement("ul");
      sourceList.className = "source-list";
      for (const source of record.sources) {
        const item = document.createElement("li");
        const url = safeUrl(source.url);
        if (url) {
          const link = document.createElement("a");
          link.href = url;
          link.target = "_blank";
          link.rel = "noreferrer";
          link.textContent = source.label;
          item.append(link);
        } else {
          item.textContent = source.label;
        }
        sourceList.append(item);
      }
      sourceSection.append(sourceHeading, sourceList);
      elements.detailContent.append(sourceSection);
    }

    const request = requestTemplate(record);
    if (request) {
      const panel = document.createElement("section");
      panel.className = "mcp-panel";
      const panelHeading = document.createElement("h3");
      panelHeading.textContent = "Use via MCP";
      const note = document.createElement("p");
      const readOnly = !record.binding || record.binding.read_only !== false;
      note.textContent = readOnly
        ? "Read-only request. The MCP server supplies any upstream credential."
        : "Review this binding before execution.";
      const actions = document.createElement("div");
      actions.className = "mcp-actions";
      const reveal = document.createElement("button");
      reveal.type = "button";
      reveal.className = "button button-primary button-small";
      reveal.textContent = "Show request";
      const copy = document.createElement("button");
      copy.type = "button";
      copy.className = "button button-small";
      copy.textContent = "Copy request";
      const preview = document.createElement("pre");
      preview.className = "request-preview";
      preview.hidden = true;
      const code = document.createElement("code");
      const serialized = JSON.stringify(request, null, 2);
      code.textContent = serialized;
      preview.append(code);
      reveal.addEventListener("click", () => {
        preview.hidden = !preview.hidden;
        reveal.textContent = preview.hidden ? "Show request" : "Hide request";
      });
      copy.addEventListener("click", async () => {
        try {
          await navigator.clipboard.writeText(serialized);
          copy.textContent = "Copied";
          window.setTimeout(() => {
            copy.textContent = "Copy request";
          }, 1500);
        } catch (_error) {
          preview.hidden = false;
          reveal.textContent = "Hide request";
          copy.textContent = "Select request below";
        }
      });
      actions.append(reveal, copy);
      panel.append(panelHeading, note, actions, preview);
      elements.detailContent.append(panel);
    }
  }

  function selectRecord(id, options = {}) {
    const record = state.records.find((candidate) => candidate.id === id) || null;
    state.selectedId = record ? record.id : null;
    renderResults();
    renderDetail(record);
    if (record && options.focusMap && record.mapPoint && state.map) {
      state.map.easeTo({ center: record.mapPoint, zoom: 14, duration: 700 });
    }
  }

  function localMapStyle() {
    return {
      version: 8,
      sources: {},
      layers: [
        {
          id: "background",
          type: "background",
          paint: { "background-color": "#e8efe9" },
        },
      ],
    };
  }

  function osmFallbackStyle() {
    return {
      version: 8,
      sources: {
        osm: {
          type: "raster",
          tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
          tileSize: 256,
          attribution: "© OpenStreetMap contributors",
        },
      },
      layers: [{ id: "osm", type: "raster", source: "osm" }],
    };
  }

  function mcpBaseUrl() {
    const configured = new URL(window.location.href).searchParams.get("mcp");
    if (configured) {
      return configured.replace(/\/$/, "");
    }
    if (window.location.pathname.startsWith("/ui/okf-discovery")) {
      return window.location.origin;
    }
    return "http://127.0.0.1:8000";
  }

  async function chooseMapStyle() {
    if (STATIC_SNAPSHOT_MODE) {
      elements.mapStatus.textContent =
        "Public snapshot · key-free OpenStreetMap context · live execution stays in MCP Geo";
      return osmFallbackStyle();
    }
    const styleUrl =
      `${mcpBaseUrl()}/maps/vector/vts/resources/styles` +
      "?style=OS_VTS_3857_Light.json&srs=3857";
    try {
      const style = await fetchJson(styleUrl, 3500);
      if (!style || style.version !== 8 || !style.sources || !Array.isArray(style.layers)) {
        throw new Error("Unexpected OS style document");
      }
      elements.mapStatus.textContent =
        "OS Vector Tile API light basemap · credentials remain in MCP Geo";
      return style;
    } catch (_error) {
      elements.mapStatus.textContent =
        "Key-free OpenStreetMap context · OS data discovery remains available";
      return osmFallbackStyle();
    }
  }

  function mapFeatures() {
    const grouped = new Map();
    for (const record of state.filtered.filter((candidate) => candidate.mapPoint)) {
      const key = record.mapPoint.join(",");
      if (!grouped.has(key)) {
        grouped.set(key, []);
      }
      grouped.get(key).push(record);
    }
    return {
      type: "FeatureCollection",
      features: [...grouped.values()].map((records) => ({
        type: "Feature",
        geometry: { type: "Point", coordinates: records[0].mapPoint },
        properties: {
          id: state.demoLocation.id,
          title: state.demoLocation.title,
          count: records.length,
          recordIds: JSON.stringify(records.map((record) => record.id)),
        },
      })),
    };
  }

  function installMapData() {
    if (!state.map || !state.map.isStyleLoaded()) {
      return;
    }
    if (state.map.getLayer("discovery-points")) {
      state.map.removeLayer("discovery-points");
    }
    if (state.map.getLayer("discovery-labels")) {
      state.map.removeLayer("discovery-labels");
    }
    if (state.map.getSource("discovery-records")) {
      state.map.removeSource("discovery-records");
    }
    state.map.addSource("discovery-records", {
      type: "geojson",
      data: mapFeatures(),
    });
    state.map.addLayer({
      id: "discovery-points",
      type: "circle",
      source: "discovery-records",
      paint: {
        "circle-radius": ["interpolate", ["linear"], ["get", "count"], 1, 10, 15, 19],
        "circle-color": "#08783e",
        "circle-stroke-color": "#ffffff",
        "circle-stroke-width": 3,
      },
    });
    state.map.addLayer({
      id: "discovery-labels",
      type: "symbol",
      source: "discovery-records",
      layout: {
        "text-field": ["to-string", ["get", "count"]],
        "text-size": 12,
        "text-font": ["Open Sans Semibold"],
      },
      paint: { "text-color": "#ffffff" },
    });
    state.mapSourceReady = true;
  }

  function updateMapData() {
    if (!state.map || !state.mapReady) {
      return;
    }
    const source = state.map.getSource("discovery-records");
    if (source && typeof source.setData === "function") {
      source.setData(mapFeatures());
      return;
    }
    installMapData();
  }

  function showMapPopup(feature) {
    if (!state.map || !feature) {
      return;
    }
    let ids = [];
    try {
      ids = JSON.parse(feature.properties.recordIds || "[]");
    } catch (_error) {
      ids = [];
    }
    const records = ids
      .map((id) => state.records.find((record) => record.id === id))
      .filter(Boolean)
      .slice(0, 6);
    const container = document.createElement("div");
    const strong = document.createElement("strong");
    strong.textContent = state.demoLocation.title;
    const note = document.createElement("p");
    note.textContent = `${ids.length} matching capabilities for this demo query location.`;
    container.append(strong, note);
    for (const record of records) {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = record.title;
      button.addEventListener("click", () => {
        selectRecord(record.id);
        if (state.mapPopup) state.mapPopup.remove();
      });
      container.append(button);
    }
    if (state.mapPopup) state.mapPopup.remove();
    state.mapPopup = new window.maplibregl.Popup({ offset: 18 })
      .setLngLat(feature.geometry.coordinates)
      .setDOMContent(container)
      .addTo(state.map);
  }

  async function initializeMap() {
    if (state.map) {
      state.map.resize();
      return;
    }
    if (!window.maplibregl) {
      elements.mapUnavailable.hidden = false;
      elements.mapStatus.textContent = "MapLibre did not load; spatial facets remain functional";
      return;
    }
    state.map = new window.maplibregl.Map({
      container: "map",
      style: localMapStyle(),
      center: state.demoLocation.coordinates,
      zoom: 11,
      minZoom: 4,
      maxZoom: 19,
      attributionControl: true,
    });
    state.map.addControl(new window.maplibregl.NavigationControl(), "top-right");
    state.map.on("load", async () => {
      state.mapReady = true;
      installMapData();
      const style = await chooseMapStyle();
      state.map.once("style.load", () => {
        installMapData();
      });
      state.map.setStyle(style);
    });
    state.map.on("moveend", () => {
      if (state.filterToViewport) {
        applyFilters();
      }
    });
    state.map.on("click", "discovery-points", (event) => {
      const feature = event.features && event.features[0];
      showMapPopup(feature);
    });
    state.map.on("mouseenter", "discovery-points", () => {
      state.map.getCanvas().style.cursor = "pointer";
    });
    state.map.on("mouseleave", "discovery-points", () => {
      state.map.getCanvas().style.cursor = "";
    });
    state.map.on("error", (event) => {
      const message = String(event && event.error && event.error.message);
      if (/tile|source|network|fetch/i.test(message)) {
        elements.mapStatus.textContent =
          "Basemap tiles unavailable · OKF spatial records are still plotted";
      }
    });
  }

  function setTab(tab) {
    state.tab = tab;
    const showMap = tab === "map";
    elements.listTab.setAttribute("aria-selected", String(!showMap));
    elements.mapTab.setAttribute("aria-selected", String(showMap));
    elements.listTab.tabIndex = showMap ? -1 : 0;
    elements.mapTab.tabIndex = showMap ? 0 : -1;
    elements.listPanel.hidden = showMap;
    elements.mapPanel.hidden = !showMap;
    applyFilters();
    if (showMap) {
      void initializeMap();
      window.setTimeout(() => state.map && state.map.resize(), 0);
    }
  }

  function updateStateFromControls() {
    state.query = elements.searchInput.value;
    state.family = elements.family.value;
    state.type = elements.type.value;
    state.access = elements.access.value;
    state.geography = elements.geography.value;
    applyFilters();
  }

  function installInteractions() {
    elements.searchForm.addEventListener("submit", (event) => {
      event.preventDefault();
      updateStateFromControls();
    });
    elements.searchInput.addEventListener("input", updateStateFromControls);
    for (const select of [elements.family, elements.type, elements.access, elements.geography]) {
      select.addEventListener("change", updateStateFromControls);
    }
    document.querySelectorAll("[data-query]").forEach((button) => {
      button.addEventListener("click", () => {
        elements.searchInput.value = button.dataset.query || "";
        updateStateFromControls();
        elements.searchInput.focus();
      });
    });
    elements.reset.addEventListener("click", () => {
      elements.searchInput.value = "";
      for (const select of [elements.family, elements.type, elements.access, elements.geography]) {
        select.value = "";
      }
      elements.viewportFilter.checked = false;
      state.filterToViewport = false;
      updateStateFromControls();
    });
    elements.list.addEventListener("click", (event) => {
      const button = event.target.closest("[data-record-id]");
      if (button) {
        selectRecord(button.dataset.recordId);
      }
    });
    elements.listTab.addEventListener("click", () => setTab("list"));
    elements.mapTab.addEventListener("click", () => setTab("map"));
    elements.listTab.addEventListener("keydown", (event) => {
      if (event.key === "ArrowRight") {
        setTab("map");
        elements.mapTab.focus();
      }
    });
    elements.mapTab.addEventListener("keydown", (event) => {
      if (event.key === "ArrowLeft") {
        setTab("list");
        elements.listTab.focus();
      }
    });
    elements.viewportFilter.addEventListener("change", () => {
      state.filterToViewport = elements.viewportFilter.checked;
      applyFilters();
    });
    elements.explorerHouse.addEventListener("click", () => {
      if (state.map) {
        state.map.fitBounds(state.demoLocation.bbox, { padding: 70, duration: 700 });
      }
    });
  }

  async function initialize() {
    installInteractions();
    try {
      const data = await loadDataSet();
      state.records = normalizeData(data.records, data.spatial, data.bindings);
      if (!state.records.length) {
        throw new Error("The OKF snapshot contains no records");
      }
      populateFacets();
      applyFilters();
      elements.snapshotStatus.textContent =
        `${state.records.length.toLocaleString()} records · ${state.dataMode}` +
        " · deterministic snapshot";
      const firstFeatured = state.records.find(
        (record) => record.id === "tool:os_places.by_postcode"
      );
      if (firstFeatured) {
        selectRecord(firstFeatured.id);
      }
    } catch (error) {
      elements.snapshotStatus.textContent = "OKF snapshot unavailable";
      elements.summary.textContent = "Data could not be loaded";
      elements.empty.hidden = false;
      elements.empty.textContent =
        `${error.message}. Serve this page through MCP Geo or use the documented ` +
        "static demo command.";
    }
  }

  window.__OKF_DISCOVERY__ = {
    mapFeatures,
    getState() {
      return {
        tab: state.tab,
        filteredIds: state.filtered.map((record) => record.id),
        candidateCount: state.candidateCount,
        mapEligibleCount: state.mapEligibleCount,
      };
    },
  };

  void initialize();
})();
