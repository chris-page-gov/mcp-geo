export const HOST_PROFILES = {
  vscode_inline_only_500: {
    displayMode: "inline",
    availableDisplayModes: ["inline"],
    platform: "desktop",
    userAgent: "playwright-vscode-inline",
    containerDimensions: { maxHeight: 500, maxWidth: 360 },
    mcpGeo: { proxyBase: "http://localhost:8000" },
  },
  claude_inline_500: {
    displayMode: "inline",
    availableDisplayModes: ["inline", "fullscreen"],
    platform: "desktop",
    userAgent: "playwright-claude-inline",
    containerDimensions: { maxHeight: 500, maxWidth: 360 },
    mcpGeo: { proxyBase: "http://localhost:8000" },
  },
  fullscreen_capable_desktop: {
    displayMode: "inline",
    availableDisplayModes: ["inline", "fullscreen"],
    platform: "desktop",
    userAgent: "playwright-fullscreen",
    containerDimensions: { maxHeight: 760, maxWidth: 1280 },
    mcpGeo: { proxyBase: "http://localhost:8000" },
  },
};
