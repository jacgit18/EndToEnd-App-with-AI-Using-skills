import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// In compose, the dev server runs in the `frontend` container and proxies API
// calls to the `backend` service. The browser only ever talks to :5173.
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      "/api": { target: "http://backend:8000", changeOrigin: true },
      "/health": { target: "http://backend:8000", changeOrigin: true },
    },
  },
});
