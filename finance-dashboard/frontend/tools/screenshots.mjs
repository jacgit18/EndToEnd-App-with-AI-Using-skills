// Screenshots of the built app for PR review (npm run screenshots, after npm run build).
// Serves dist/ on a throwaway local port, answers the API from the E2E mock (seed data
// only, never real finances), freezes the clock, and writes PNGs to screenshots/.
//
// The committed screenshots are generated in CI (.github/workflows/screenshots.yml).
// A local run uses your machine's fonts, so it will not match CI pixel for pixel; use
// it to preview, and let CI commit.
import { createServer } from "node:http";
import { mkdir, readFile, rm } from "node:fs/promises";
import { extname, join, normalize, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { chromium } from "@playwright/test";

import { createMockApi } from "../e2e/mock-api.js";
import { CREDENTIALS, FROZEN_NOW } from "../e2e/seed.js";

const root = fileURLToPath(new URL("..", import.meta.url));
const dist = join(root, "dist");
const outDir = resolve(root, process.argv[2] ?? "screenshots");

const VIEWPORTS = {
  desktop: { viewport: { width: 1440, height: 900 } },
  mobile: { viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true },
};

// name, route, viewport, colour scheme, optional interaction before the shot.
const SHOTS = [
  ["transactions-desktop", "/", "desktop", "light"],
  ["dashboard-desktop", "/dashboard", "desktop", "light"],
  ["accounts-desktop", "/accounts", "desktop", "light"],
  ["categories-desktop", "/categories", "desktop", "light"],
  ["budgets-desktop", "/budgets", "desktop", "light"],
  ["import-desktop", "/import", "desktop", "light"],
  ["login-desktop", "/login", "desktop", "light"],
  ["dashboard-mobile", "/dashboard", "mobile", "light"],
  ["transactions-mobile", "/", "mobile", "light"],
  ["login-mobile", "/login", "mobile", "light"],
  // Dark scheme: the app has no dark theme, but chart text/lines follow currentColor and
  // native controls switch; this shot catches a regression in either.
  ["dashboard-desktop-dark", "/dashboard", "desktop", "dark"],
  ["account-edit-desktop", "/accounts", "desktop", "light", async (page) => {
    await page.getByRole("button", { name: "Edit" }).first().click();
    await page.getByRole("button", { name: "Cancel" }).waitFor();
  }],
  ["import-preview-desktop", "/import", "desktop", "light", async (page) => {
    await page.getByLabel("CSV file").setInputFiles({ name: "card.csv", mimeType: "text/csv", buffer: Buffer.from("x\n") });
    await page.getByRole("region", { name: "File preview" }).waitFor();
  }],
  ["login-error-mobile", "/login", "mobile", "light", async (page) => {
    await page.getByLabel("Email").fill(CREDENTIALS.email);
    await page.getByLabel("Password").fill("wrong");
    await page.getByRole("button", { name: "Sign in" }).click();
    await page.getByRole("alert").waitFor();
  }],
  ["budgets-copied-desktop", "/budgets", "desktop", "light", async (page) => {
    await page.getByRole("button", { name: "Copy from last month" }).click();
    await page.getByRole("status").waitFor();
  }],
];

const TYPES = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".svg": "image/svg+xml", ".txt": "text/plain", ".png": "image/png" };

// Static server with the SPA fallback Caddy gives in production (unknown path -> index.html).
function serve() {
  const server = createServer(async (req, res) => {
    const path = normalize(decodeURIComponent(new URL(req.url, "http://x").pathname)).replace(/^(\.\.[/\\])+/, "");
    const file = path === "/" ? "index.html" : path;
    try {
      const body = await readFile(join(dist, file));
      res.writeHead(200, { "content-type": TYPES[extname(file)] ?? "application/octet-stream" }).end(body);
    } catch {
      res.writeHead(200, { "content-type": "text/html" }).end(await readFile(join(dist, "index.html")));
    }
  });
  return new Promise((resolve) => server.listen(0, "127.0.0.1", () => resolve(server)));
}

async function main() {
  await readFile(join(dist, "index.html")).catch(() => {
    throw new Error("dist/ is missing: run `npm run build` first");
  });
  await rm(outDir, { recursive: true, force: true });
  await mkdir(outDir, { recursive: true });

  const server = await serve();
  const baseURL = `http://127.0.0.1:${server.address().port}`;
  const browser = await chromium.launch();
  try {
    for (const [name, route, size, colorScheme, interact] of SHOTS) {
      const context = await browser.newContext({
        ...VIEWPORTS[size],
        baseURL,
        colorScheme,
        deviceScaleFactor: 1, // small PNGs, stable diffs
        timezoneId: "America/New_York",
        locale: "en-US",
        serviceWorkers: "block",
        reducedMotion: "reduce",
      });
      await createMockApi().install(context);
      const page = await context.newPage();
      await page.clock.install({ time: FROZEN_NOW });
      await page.goto(route);
      await page.waitForLoadState("networkidle").catch(() => {});
      await page.evaluate(() => document.fonts.ready);
      if (interact) await interact(page);
      await page.screenshot({ path: join(outDir, `${name}.png`), fullPage: true, animations: "disabled", caret: "hide" });
      await context.close();
      console.log(`  ${name}.png`);
    }
  } finally {
    await browser.close();
    server.close();
  }
  console.log(`${SHOTS.length} screenshots in ${outDir}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
