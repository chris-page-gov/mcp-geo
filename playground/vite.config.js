import { svelte } from "@sveltejs/vite-plugin-svelte";

const hmrHost = process.env.VITE_HMR_HOST || "localhost";
const hmrClientPort = Number(process.env.VITE_HMR_CLIENT_PORT || 5173);

export default {
  plugins: [svelte()],
  server: {
    host: true,
    port: 5173,
    hmr: {
      protocol: "ws",
      host: hmrHost,
      clientPort: hmrClientPort
    }
  }
};
