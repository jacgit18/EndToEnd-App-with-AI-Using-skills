import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev-only proxy: forwards to wherever the backend actually is. Vite's dev
// server forwards matching requests to it, so the browser only ever talks to
// one origin (Vite's, e.g. localhost:5173) and never sees FastAPI's origin
// directly — that's what makes this a same-origin app in dev with zero CORS
// configuration (ADR-0008).
//
// The target is an env var, not a hardcoded "localhost:8000" — "localhost"
// means something different depending on where this process is running.
// Run natively (npm run dev on the host), Vite and uvicorn are both
// processes on the same host, so localhost:8000 reaches the backend.
// Run inside Docker Compose (compose.yaml), this process is *in the frontend
// container* — localhost there is the frontend container itself, and
// "backend" (the other service's name) is what Compose's DNS resolves to the
// backend container. compose.yaml sets BACKEND_URL=http://backend:8000 for
// exactly this reason; the fallback below is what native dev uses instead.
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
const backendUrl = process.env.BACKEND_URL ?? "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": {
        target: backendUrl,
        changeOrigin: true,
      },
      "/health": {
        target: backendUrl,
        changeOrigin: true,
      },
    },
  },
});
