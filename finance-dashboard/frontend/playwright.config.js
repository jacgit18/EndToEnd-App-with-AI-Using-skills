// Playwright E2E config (ADR-0023). Runs against the production build served by
// `vite preview` — never the dev server (rules/web-accessibility-and-lighthouse.md).
// The API is mocked inside the browser (e2e/mock-api.js), so no backend is needed.
import { defineConfig, devices } from "@playwright/test";

const PORT = 4173;

export default defineConfig({
  testDir: "e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["github"], ["html", { open: "never" }]] : [["list"]],
  use: {
    baseURL: `http://127.0.0.1:${PORT}`,
    // The app registers no service worker today; blocking keeps it that way for tests
    // if one is added (a SW would cache responses past page.route()).
    serviceWorkers: "block",
    timezoneId: "America/New_York",
    locale: "en-US",
    trace: "retain-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"], viewport: { width: 1440, height: 900 } },
    },
  ],
  webServer: {
    command: `npm run build && npm run preview -- --host 127.0.0.1 --port ${PORT} --strictPort`,
    url: `http://127.0.0.1:${PORT}`,
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
});
