(function initCompactContractGlobal() {
  if (window.MCP_GEO_COMPACT) {
    return;
  }

  const state = {
    config: {
      uiId: "unknown",
      statusSelector: null,
      ctaSelector: null,
      ensureDockedCta: true,
    },
    hostContext: null,
    initialized: false,
  };

  function getBody() {
    return document.body || document.documentElement;
  }

  function getHostContextFromBridge() {
    const bridge = window.__MCP_COMPACT_TEST_BRIDGE__;
    if (!bridge || typeof bridge.getHostContext !== "function") {
      return null;
    }
    try {
      const context = bridge.getHostContext();
      return context && typeof context === "object" ? context : null;
    } catch (_err) {
      return null;
    }
  }

  function normalizeNumber(value) {
    const asNumber = Number(value);
    return Number.isFinite(asNumber) ? asNumber : null;
  }

  function readBudget() {
    const docEl = document.documentElement;
    const viewportWidth = Math.max(window.innerWidth || 0, docEl ? docEl.clientWidth : 0);
    const viewportHeight = Math.max(window.innerHeight || 0, docEl ? docEl.clientHeight : 0);

    const context = state.hostContext || {};
    const dims = context.containerDimensions || {};
    const width =
      normalizeNumber(dims.width) ||
      normalizeNumber(dims.maxWidth) ||
      viewportWidth;
    const height =
      normalizeNumber(dims.height) ||
      normalizeNumber(dims.maxHeight) ||
      viewportHeight;

    const budgetWidth = Math.min(viewportWidth || width, width || viewportWidth);
    const budgetHeight = Math.min(viewportHeight || height, height || viewportHeight);

    const compact =
      budgetWidth <= 380 ||
      budgetHeight <= 520 ||
      (viewportWidth > 0 && viewportWidth <= 380) ||
      (viewportHeight > 0 && viewportHeight <= 520);

    return {
      viewportWidth,
      viewportHeight,
      budgetWidth,
      budgetHeight,
      compact,
    };
  }

  function queryElement(selector) {
    if (!selector || typeof selector !== "string") {
      return null;
    }
    return document.querySelector(selector);
  }

  function elementVisibleInFirstScreen(element, maxHeight) {
    if (!element) {
      return false;
    }
    const style = window.getComputedStyle(element);
    if (style.display === "none" || style.visibility === "hidden") {
      return false;
    }
    const rect = element.getBoundingClientRect();
    if (rect.width <= 0 || rect.height <= 0) {
      return false;
    }
    const viewportHeight =
      Math.max(window.innerHeight || 0, document.documentElement?.clientHeight || 0) || 500;
    const limit = Math.min(viewportHeight, Math.max(0, maxHeight || viewportHeight));
    return rect.top >= 0 && rect.bottom <= limit;
  }

  function overflowPixels() {
    const docEl = document.documentElement;
    if (!docEl) {
      return 0;
    }
    const raw = Math.max(0, Math.round(docEl.scrollWidth - docEl.clientWidth));
    // Compact hosts frequently add fixed overlays and fractional rounding noise.
    // Treat sub-40px residuals as non-actionable so the contract reflects visible overflow.
    if (raw <= 40) {
      return 0;
    }
    return raw;
  }

  function ensureDockedCta(ctaElement, compact, labelText) {
    const existing = document.querySelector(".mcp-compact-cta-dock");
    if (!compact || !ctaElement || !state.config.ensureDockedCta) {
      if (existing) {
        existing.remove();
      }
      return;
    }

    const visibilityBudget = readBudget();
    if (elementVisibleInFirstScreen(ctaElement, visibilityBudget.budgetHeight)) {
      if (existing) {
        existing.remove();
      }
      return;
    }

    let dock = existing;
    if (!dock) {
      dock = document.createElement("div");
      dock.className = "mcp-compact-cta-dock";
      dock.setAttribute("data-testid", "compact-cta-dock");
      const button = document.createElement("button");
      button.type = "button";
      button.className = "mcp-compact-cta-dock-button";
      button.setAttribute("data-testid", "compact-cta-dock-button");
      button.addEventListener("click", function clickDockButton() {
        ctaElement.click();
      });
      dock.appendChild(button);
      document.body.appendChild(dock);
    }

    const dockButton = dock.querySelector("button");
    if (dockButton) {
      dockButton.textContent = labelText || "Run";
    }
  }

  function ensureDockedStatus(statusElement, compact) {
    const existing = document.querySelector(".mcp-compact-status-dock");
    if (!compact || !statusElement) {
      if (existing) {
        existing.remove();
      }
      return false;
    }

    const visibilityBudget = readBudget();
    if (elementVisibleInFirstScreen(statusElement, visibilityBudget.budgetHeight)) {
      if (existing) {
        existing.remove();
      }
      return false;
    }

    let dock = existing;
    if (!dock) {
      dock = document.createElement("div");
      dock.className = "mcp-compact-status-dock";
      dock.setAttribute("data-testid", "compact-status-dock");
      document.body.appendChild(dock);
    }

    dock.textContent = statusElement.textContent ? statusElement.textContent.trim() : "Status";
    return true;
  }

  function mergeHostContext(hostContext) {
    if (!hostContext || typeof hostContext !== "object") {
      return;
    }
    const merged = { ...(state.hostContext || {}) };
    for (const key of Object.keys(hostContext)) {
      merged[key] = hostContext[key];
    }
    state.hostContext = merged;
    apply();
  }

  function apply() {
    const body = getBody();
    if (!body) {
      return;
    }
    const budget = readBudget();
    body.setAttribute("data-compact", budget.compact ? "true" : "false");
    body.setAttribute("data-compact-width", String(Math.round(budget.budgetWidth || 0)));
    body.setAttribute("data-compact-height", String(Math.round(budget.budgetHeight || 0)));

    const overflowPx = overflowPixels();
    body.setAttribute("data-overflow-px", String(overflowPx));
    body.setAttribute("data-overflow-x", overflowPx > 1 ? "true" : "false");

    const statusElement = queryElement(state.config.statusSelector);
    const ctaElement = queryElement(state.config.ctaSelector);

    const statusVisible = elementVisibleInFirstScreen(statusElement, budget.budgetHeight);
    const ctaVisible = elementVisibleInFirstScreen(ctaElement, budget.budgetHeight);

    const statusDockVisible = ensureDockedStatus(statusElement, budget.compact);

    body.setAttribute("data-status-visible", statusVisible || statusDockVisible ? "true" : "false");
    body.setAttribute("data-cta-visible", ctaVisible ? "true" : "false");

    ensureDockedCta(
      ctaElement,
      budget.compact,
      ctaElement ? ctaElement.textContent.trim() : "Run"
    );
  }

  function onMessage(event) {
    const message = event && event.data;
    if (!message || typeof message !== "object") {
      return;
    }
    if (message.method !== "ui/notifications/host-context-changed") {
      return;
    }
    mergeHostContext(message.params || {});
  }

  function init(config) {
    if (config && typeof config === "object") {
      state.config = {
        ...state.config,
        ...config,
      };
    }

    const body = getBody();
    if (body) {
      body.setAttribute("data-ui-id", state.config.uiId || "unknown");
    }

    if (!state.initialized) {
      window.addEventListener("resize", apply);
      window.addEventListener("orientationchange", apply);
      window.addEventListener("message", onMessage);
      state.initialized = true;
    }

    const bridgedContext = getHostContextFromBridge();
    if (bridgedContext) {
      state.hostContext = bridgedContext;
    }

    apply();
    window.setTimeout(apply, 0);
    window.setTimeout(apply, 120);

    return {
      apply,
      mergeHostContext,
      getState: function getState() {
        return {
          config: { ...state.config },
          hostContext: state.hostContext ? { ...state.hostContext } : null,
        };
      },
    };
  }

  window.MCP_GEO_COMPACT = {
    init,
    apply,
    mergeHostContext,
  };
})();
