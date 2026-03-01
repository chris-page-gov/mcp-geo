export async function installBasicMcpBridge(page, hostContext) {
  await page.addInitScript((context) => {
    const listeners = [];

    function dispatch(eventName, payload) {
      for (const fn of listeners) {
        try {
          fn({ eventName, payload });
        } catch {
          // ignore listener errors in test bridge
        }
      }
    }

    window.__MCP_COMPACT_TEST_BRIDGE__ = {
      getHostContext: () => context,
      onEvent: (fn) => {
        if (typeof fn === "function") {
          listeners.push(fn);
        }
      },
    };

    window.addEventListener("message", (event) => {
      const message = event.data;
      if (!message || message.jsonrpc !== "2.0" || message.id === undefined) {
        return;
      }

      const respond = (result) => {
        window.postMessage({ jsonrpc: "2.0", id: message.id, result }, "*");
      };

      dispatch("rpc", message);

      if (message.method === "ui/initialize") {
        respond({ protocolVersion: "2026-01-26", hostContext: context });
        return;
      }

      if (message.method === "ui/request-display-mode") {
        const requested = message.params?.mode;
        const canSet = Array.isArray(context.availableDisplayModes)
          ? context.availableDisplayModes.includes(requested)
          : false;
        const mode = canSet ? requested : context.displayMode || "inline";
        respond({ mode });
        return;
      }

      if (message.method === "tools/call") {
        const name = message.params?.name || message.params?.tool;
        if (name === "os_apps.log_event" || name === "os_apps_log_event") {
          respond({ status: "logged" });
          return;
        }
        respond({});
        return;
      }

      respond({});
    });
  }, hostContext);
}
