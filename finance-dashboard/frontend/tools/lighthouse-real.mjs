// Lighthouse against the real production stack (scripts/real-stack.sh up), every route,
// mobile and desktop. Policy: 100 in all four categories (rules/web-accessibility-and-lighthouse.md).
//
//   npm run lighthouse:real [-- --routes /,/dashboard] [-- --out lighthouse-reports]
//
// Login-gated routes: Playwright's Chromium signs in, then Lighthouse attaches to that same
// browser over the debugging port with storage reset disabled, so the session cookie stays.
// /login is audited first, while signed out. Seed rows come from the smoke spec (run it first)
// so the pages render real data, not empty states.
//
// A score under 100 is retried twice and the median is judged: simulated-throttling mobile
// Performance has moved between 99 and 100 on identical builds (accessibility record,
// "Run-to-run variation"). A real regression stays below 100 on every run.
// Results apply to this build and this machine only, not to the live HTTPS site.
import { mkdir, writeFile } from "node:fs/promises";
import { join } from "node:path";

import { chromium } from "@playwright/test";
import lighthouse from "lighthouse";

const BASE = process.env.REAL_STACK_URL ?? "http://127.0.0.1:8081";
const PORT = 9333;
const CATEGORIES = ["performance", "accessibility", "best-practices", "seo"];
const ALL_ROUTES = ["/login", "/", "/dashboard", "/accounts", "/categories", "/budgets", "/import"];

const arg = (name, fallback) => {
  const i = process.argv.indexOf(`--${name}`);
  return i > -1 ? process.argv[i + 1] : fallback;
};
const routes = arg("routes", ALL_ROUTES.join(",")).split(",");
const outDir = arg("out", "lighthouse-reports");
const email = process.env.REAL_STACK_EMAIL;
const password = process.env.REAL_STACK_PASSWORD;
if (!email || !password) {
  console.error("REAL_STACK_EMAIL / REAL_STACK_PASSWORD not set (run scripts/real-stack.sh up)");
  process.exit(2);
}

const median = (xs) => [...xs].sort((a, b) => a - b)[Math.floor(xs.length / 2)];
const slug = (route, factor) => `${route === "/" ? "transactions" : route.slice(1)}-${factor}`;

async function audit(route, factor, runIndex) {
  const flags = { port: PORT, output: ["json", "html"], onlyCategories: CATEGORIES, disableStorageReset: true, logLevel: "error" };
  const config = factor === "desktop" ? (await import("lighthouse/core/config/desktop-config.js")).default : undefined;
  const result = await lighthouse(`${BASE}${route}`, flags, config);
  const scores = Object.fromEntries(CATEGORIES.map((c) => [c, Math.round((result.lhr.categories[c].score ?? 0) * 100)]));
  const base = join(outDir, `${slug(route, factor)}${runIndex ? `-retry${runIndex}` : ""}`);
  await writeFile(`${base}.json`, result.report[0]);
  await writeFile(`${base}.html`, result.report[1]);
  return { scores, lhr: result.lhr };
}

async function auditStable(route, factor) {
  const runs = [await audit(route, factor, 0)];
  const perfect = (r) => CATEGORIES.every((c) => r.scores[c] === 100);
  for (let i = 1; i <= 2 && !perfect(runs[0]) && runs.length <= i; i++) runs.push(await audit(route, factor, i));
  const scores = Object.fromEntries(CATEGORIES.map((c) => [c, median(runs.map((r) => r.scores[c]))]));
  return { scores, runs: runs.length, lhr: runs[0].lhr };
}

await mkdir(outDir, { recursive: true });
const context = await chromium.launchPersistentContext("", {
  headless: true,
  viewport: null,
  args: [`--remote-debugging-port=${PORT}`],
});
const page = context.pages()[0] ?? (await context.newPage());

const rows = [];
let failed = false;
let lhVersion = "";
const run = async (route) => {
  for (const factor of ["mobile", "desktop"]) {
    const { scores, runs, lhr } = await auditStable(route, factor);
    const ok = CATEGORIES.every((c) => scores[c] === 100);
    if (!ok) failed = true;
    lhVersion = lhr.lighthouseVersion;
    rows.push({ route, factor, ...scores, runs, ok });
    if (!ok) {
      const bad = Object.values(lhr.audits).filter((a) => a.score !== null && a.score < 1 && a.scoreDisplayMode !== "informative" && a.scoreDisplayMode !== "notApplicable");
      for (const a of bad.slice(0, 8)) console.error(`  ${route} ${factor}: ${a.id} (${a.score})`);
    }
  }
};

try {
  if (routes.includes("/login")) await run("/login");
  const gated = routes.filter((r) => r !== "/login");
  if (gated.length) {
    await page.goto(`${BASE}/login`);
    await page.getByLabel("Email").fill(email);
    await page.getByLabel("Password").fill(password);
    await page.getByRole("button", { name: "Sign in" }).click();
    await page.waitForURL(`${BASE}/`);
    for (const route of gated) await run(route);
  }
} finally {
  await context.close();
}

console.log(`Lighthouse ${lhVersion} against ${BASE}, simulated throttling, Playwright Chromium ${chromium.name()}`);
console.table(rows.map(({ ok, ...r }) => r));
await writeFile(join(outDir, "summary.json"), JSON.stringify(rows, null, 2));
process.exit(failed ? 1 : 0);
