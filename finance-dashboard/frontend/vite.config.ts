import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// The dev server proxies API calls to the backend; the browser only talks to :5173.
// Native dev  -> http://localhost:8000 (default)
// In compose  -> VITE_API_PROXY=http://backend:8000 (set in compose.yaml)
const apiTarget = process.env.VITE_API_PROXY ?? "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      "/api": { target: apiTarget, changeOrigin: true },
      "/health": { target: apiTarget, changeOrigin: true },
    },
  },
});
