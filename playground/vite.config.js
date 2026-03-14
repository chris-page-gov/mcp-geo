import { svelte } from "@sveltejs/vite-plugin-svelte";
import { defineConfig } from "vite";

const hmrHost = process.env.VITE_HMR_HOST || "localhost";
const hmrClientPort = Number(process.env.VITE_HMR_CLIENT_PORT || 5173);
const proxyTarget = process.env.VITE_PROXY_TARGET || "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [svelte()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      "/health": proxyTarget,
      "/audit": proxyTarget,
      "/mcp": proxyTarget,
      "/playground": proxyTarget,
      "/maps": proxyTarget,
      "/resources": proxyTarget,
      "/tools": proxyTarget,
      "/ui": proxyTarget,
    },
    hmr: {
      protocol: "ws",
      host: hmrHost,
      clientPort: hmrClientPort
    }
  }
});
