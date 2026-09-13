import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev-only proxy: the backend runs on :8000 (see backend/Dockerfile's EXPOSE
// 8000). Vite's dev server forwards matching requests to it, so the browser
// only ever talks to one origin (Vite's, e.g. localhost:5173) and never sees
// FastAPI's origin directly — that's what makes this a same-origin app in dev
// with zero CORS configuration (ADR-0008).
//
// Two separate paths need forwarding, not one: the accounts/transactions
// routers mount under "/api/..." (app/main.py's include_router calls), but
// "/health" is a bare route on the app itself, outside that prefix — so it
// needs its own proxy entry, or the health badge would hit Vite's own dev
// server instead of FastAPI and get a 404. Neither path is rewritten; both
// forward unchanged.
//
// In production there's no Vite dev server at all; Caddy takes over this same
// job (reverse-proxying /api and /health to the backend container) once
// ADR-0012's deployment lands in a later phase.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/health": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
