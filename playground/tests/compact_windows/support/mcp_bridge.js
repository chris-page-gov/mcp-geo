function normalizeHostContext(input) {
  if (!input || typeof input !== "object") {
    return {
      displayMode: "inline",
      availableDisplayModes: ["inline"],
      containerDimensions: { maxHeight: 500, maxWidth: 360 },
    };
  }
  const merged = { ...input };
  if (!Array.isArray(merged.availableDisplayModes) || !merged.availableDisplayModes.length) {
    merged.availableDisplayModes = ["inline"];
  }
  if (!merged.displayMode || !merged.availableDisplayModes.includes(merged.displayMode)) {
    merged.displayMode = merged.availableDisplayModes[0] || "inline";
  }
  if (!merged.containerDimensions || typeof merged.containerDimensions !== "object") {
    merged.containerDimensions = { maxHeight: 500, maxWidth: 360 };
  }
  return merged;
}

export async function installMcpBridge(
  page,
  {
    hostContext,
    toolRules = [],
    defaultToolResult = {},
    strictToolMatching = false,
  } = {}
) {
  await page.addInitScript(
    ({ hostContext: initialHostContext, toolRules: scriptedToolRules, defaultToolResult, strictToolMatching }) => {
      const listeners = [];
      const rpcLog = [];
      const toolCalls = [];

      function deepClone(value) {
        if (value === undefined) {
          return undefined;
        }
        try {
          return JSON.parse(JSON.stringify(value));
        } catch (_err) {
          return value;
        }
      }

      function mergeObjects(baseValue, patchValue) {
        const base =
          baseValue && typeof baseValue === "object" && !Array.isArray(baseValue)
            ? { ...baseValue }
            : {};
        const patch =
          patchValue && typeof patchValue === "object" && !Array.isArray(patchValue)
            ? patchValue
            : {};
        const out = { ...base };
        Object.keys(patch).forEach((key) => {
          const nextValue = patch[key];
          const currentValue = out[key];
          if (
            nextValue &&
            typeof nextValue === "object" &&
            !Array.isArray(nextValue) &&
            currentValue &&
            typeof currentValue === "object" &&
            !Array.isArray(currentValue)
          ) {
            out[key] = mergeObjects(currentValue, nextValue);
            return;
          }
          out[key] = nextValue;
        });
        return out;
      }

      function normalizeContext(rawInput) {
        const normalized =
          rawInput && typeof rawInput === "object" ? { ...rawInput } : {};
        if (
          !Array.isArray(normalized.availableDisplayModes) ||
          !normalized.availableDisplayModes.length
        ) {
          normalized.availableDisplayModes = ["inline"];
        }
        if (
          typeof normalized.displayMode !== "string" ||
          !normalized.availableDisplayModes.includes(normalized.displayMode)
        ) {
          normalized.displayMode = normalized.availableDisplayModes[0] || "inline";
        }
        if (
          !normalized.containerDimensions ||
          typeof normalized.containerDimensions !== "object"
        ) {
          normalized.containerDimensions = { maxHeight: 500, maxWidth: 360 };
        }
        return normalized;
      }

      function dispatch(eventName, payload) {
        listeners.forEach((fn) => {
          try {
            fn({ eventName, payload: deepClone(payload) });
          } catch (_err) {
            // Ignore listener failures in the bridge.
          }
        });
      }

      function sanitizeToolName(toolName) {
        if (typeof toolName !== "string") {
          return "";
        }
        return toolName.replace(/[^A-Za-z0-9_-]/g, "_").slice(0, 64);
      }

      function argsMatch(matchers, args) {
        if (!matchers || typeof matchers !== "object") {
          return true;
        }
        return Object.entries(matchers).every(([key, expected]) => {
          const actual = args && typeof args === "object" ? args[key] : undefined;
          if (Array.isArray(expected)) {
            return expected.includes(actual);
          }
          return actual === expected;
        });
      }

      function findToolRule(name, args) {
        const sanitized = sanitizeToolName(name);
        for (const rule of scriptedToolRules || []) {
          if (!rule || typeof rule !== "object") {
            continue;
          }
          const ruleName = String(rule.name || "");
          const ruleAliases = Array.isArray(rule.aliases)
            ? rule.aliases.map((alias) => String(alias))
            : [];
          const namesToMatch = [ruleName, ...ruleAliases].filter(Boolean);
          const matchedName = namesToMatch.some((candidate) => {
            if (candidate === name || candidate === sanitized) {
              return true;
            }
            const candidateSanitized = sanitizeToolName(candidate);
            return candidateSanitized && (candidateSanitized === name || candidateSanitized === sanitized);
          });
          if (!matchedName) {
            continue;
          }
          if (!argsMatch(rule.when, args)) {
            continue;
          }
          return rule;
        }
        return null;
      }

      let activeHostContext = normalizeContext(initialHostContext);

      window.__MCP_COMPACT_TEST_BRIDGE__ = {
        getHostContext: () => deepClone(activeHostContext),
        setHostContext: (patch) => {
          activeHostContext = normalizeContext(mergeObjects(activeHostContext, patch));
          dispatch("host_context_set", activeHostContext);
          return deepClone(activeHostContext);
        },
        onEvent: (fn) => {
          if (typeof fn === "function") {
            listeners.push(fn);
          }
        },
        getRpcLog: () => deepClone(rpcLog),
        getToolCalls: () => deepClone(toolCalls),
        clearLogs: () => {
          rpcLog.length = 0;
          toolCalls.length = 0;
        },
      };

      window.addEventListener("message", (event) => {
        const message = event.data;
        if (!message || message.jsonrpc !== "2.0") {
          return;
        }

        if (
          message.method === "ui/notifications/host-context-changed" &&
          message.params &&
          typeof message.params === "object"
        ) {
          activeHostContext = normalizeContext(mergeObjects(activeHostContext, message.params));
          dispatch("host_context_changed", activeHostContext);
        }

        if (message.id === undefined) {
          return;
        }

        const requestRecord = {
          id: message.id,
          method: message.method,
          params: deepClone(message.params || null),
        };
        rpcLog.push(requestRecord);
        dispatch("rpc", requestRecord);

        const respondWithResult = (result) => {
          window.postMessage({ jsonrpc: "2.0", id: message.id, result: deepClone(result) }, "*");
        };

        const respondWithError = (error) => {
          const payload =
            error && typeof error === "object"
              ? error
              : { code: -32000, message: String(error || "Bridge error") };
          window.postMessage({ jsonrpc: "2.0", id: message.id, error: payload }, "*");
        };

        if (message.method === "ui/initialize") {
          respondWithResult({
            protocolVersion: "2026-01-26",
            hostContext: activeHostContext,
          });
          return;
        }

        if (message.method === "ui/request-display-mode") {
          const requested = message.params?.mode;
          const available = Array.isArray(activeHostContext.availableDisplayModes)
            ? activeHostContext.availableDisplayModes
            : ["inline"];
          if (typeof requested === "string" && available.includes(requested)) {
            activeHostContext = normalizeContext({ ...activeHostContext, displayMode: requested });
          }
          respondWithResult({ mode: activeHostContext.displayMode || "inline" });
          return;
        }

        if (message.method === "tools/call") {
          const toolName = String(message.params?.name || message.params?.tool || "");
          const toolArgs = message.params?.arguments || message.params?.args || {};
          toolCalls.push({
            name: toolName,
            args: deepClone(toolArgs),
          });
          const rule = findToolRule(toolName, toolArgs);
          if (rule) {
            if (rule.error) {
              respondWithError(rule.error);
            } else {
              respondWithResult(rule.result || {});
            }
            return;
          }

          if (toolName === "os_apps.log_event" || toolName === "os_apps_log_event") {
            respondWithResult({ status: "logged" });
            return;
          }

          if (strictToolMatching) {
            respondWithError({
              code: -32000,
              message: `Tool not stubbed in test bridge: ${toolName}`,
            });
            return;
          }

          respondWithResult(defaultToolResult || {});
          return;
        }

        respondWithResult({});
      });
    },
    {
      hostContext: normalizeHostContext(hostContext),
      toolRules,
      defaultToolResult,
      strictToolMatching,
    }
  );
}

export async function installBasicMcpBridge(page, hostContext) {
  await installMcpBridge(page, {
    hostContext,
    toolRules: [],
    defaultToolResult: {},
    strictToolMatching: false,
  });
}
