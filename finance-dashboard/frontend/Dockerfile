FROM node:20-slim

WORKDIR /app

# Copy dependency files first so this layer is cached across builds that only
# change application code, not dependencies — same reasoning as the backend
# Dockerfile.
COPY package.json package-lock.json ./
RUN npm ci

# Now the actual application code.
COPY . .

EXPOSE 5173

# Phase 0 runs the Vite dev server in this container (docs/spec.md's walking
# skeleton) — not a production build. --host is required so the dev server
# accepts connections from outside the container, not just localhost inside
# it. The eventual production image (multi-stage build -> static files
# served by Caddy, ADR-0012) is a deferred decision for when Phase 1
# deployment actually needs it; this intentionally isn't that yet.
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
