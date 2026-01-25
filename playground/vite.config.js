import { svelte } from "@sveltejs/vite-plugin-svelte";

export default {
  plugins: [svelte()],
  server: {
    host: true,
    port: 5173
  }
};
