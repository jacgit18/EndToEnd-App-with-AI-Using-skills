// Real-stack smoke (npm run e2e:real): the browser hits the production stack that
// scripts/real-stack.sh brings up (Caddy -> FastAPI -> Postgres), no mocks. Separate from
// playwright.config.js, which is the fast mocked suite that runs on every PR (ADR-0023).
// Login comes from REAL_STACK_EMAIL / REAL_STACK_PASSWORD (written by the script).
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "e2e-real",
  // One shared database, and the specs build on each other's rows: run in order.
  workers: 1,
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: 0,
  reporter: process.env.CI ? [["github"], ["html", { open: "never", outputFolder: "playwright-report-real" }]] : [["list"]],
  outputDir: "test-results-real",
  use: {
    baseURL: process.env.REAL_STACK_URL ?? "http://127.0.0.1:8081",
    serviceWorkers: "block",
    trace: "retain-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"], viewport: { width: 1440, height: 900 } } }],
});
