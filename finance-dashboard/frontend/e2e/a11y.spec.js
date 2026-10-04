// axe on every route and the main non-default states, at desktop and 320px widths, in
// light and dark colour schemes (dark renders the same as light until the app declares a
// color-scheme; the runs are there so a dark theme is scanned from its first commit).
// Tag set follows rules/web-accessibility-and-lighthouse.md (AAA target), wider than the
// usual AA-only set. A pass here is regression evidence,
// not a conformance claim: the manual checklist lives in
// .claude/records/finance-dashboard-accessibility.md.
import AxeBuilder from "@axe-core/playwright";

import { expect, test } from "./fixtures.js";

const TAGS = ["wcag2a", "wcag2aa", "wcag2aaa", "wcag21a", "wcag21aa", "wcag22aa", "best-practice"];

const scan = (page) => new AxeBuilder({ page }).withTags(TAGS).analyze();

async function expectAccessible(page) {
  const { violations } = await scan(page);
  expect(violations.map((v) => `${v.id}: ${v.nodes.map((n) => n.target.join(" ")).join(", ")}`)).toEqual([]);
  // WCAG 1.4.10 reflow: the page itself never scrolls sideways (tables scroll in their own box).
  const width = await page.evaluate(() => [document.documentElement.scrollWidth, window.innerWidth]);
  expect(width[0], "page scroll width vs viewport").toBeLessThanOrEqual(width[1]);
}

// [name, route, setup] — setup puts the page into a non-default state before the scan.
const views = [
  ["transactions", "/"],
  ["dashboard", "/dashboard"],
  ["accounts", "/accounts"],
  ["categories", "/categories"],
  ["budgets", "/budgets"],
  ["import", "/import"],
  ["login", "/login"],
  ["login error", "/login", async (page) => {
    await page.getByLabel("Email").fill("owner@example.com");
    await page.getByLabel("Password").fill("wrong");
    await page.getByRole("button", { name: "Sign in" }).click();
    await expect(page.getByRole("alert")).toBeVisible();
  }],
  ["transaction error", "/", async (page) => {
    await page.getByLabel("Account", { exact: true }).selectOption({ label: "Checking" });
    await page.getByLabel("Amount (- for expense)").fill("abc");
    await page.getByLabel("Description").fill("x");
    await page.getByRole("button", { name: "Add" }).click();
    await expect(page.getByText("amount must be")).toBeVisible();
  }],
  ["dashboard empty month", "/dashboard", async (page) => {
    await page.getByLabel("Month", { exact: true }).fill("2025-01");
    await expect(page.getByText("No transactions this month.")).toBeVisible();
  }],
  ["account edit row", "/accounts", async (page) => {
    await page.getByRole("button", { name: "Edit" }).first().click();
    await expect(page.getByRole("button", { name: "Cancel" })).toBeVisible();
  }],
  ["accounts with archived", "/accounts", async (page) => {
    await page.getByLabel("Show archived").check();
    await expect(page.getByText("Old wallet (archived)")).toBeVisible();
  }],
  ["categories with archived", "/categories", async (page) => {
    await page.getByLabel("Show archived").check();
    await expect(page.getByText("Gym (archived)")).toBeVisible();
  }],
  ["import preview", "/import", async (page) => {
    await page.getByLabel("CSV file").setInputFiles({ name: "card.csv", mimeType: "text/csv", buffer: Buffer.from("Date,Amount\n") });
    await expect(page.getByRole("region", { name: "File preview" })).toBeVisible();
  }],
];

const sizes = [
  ["desktop", { width: 1440, height: 900 }],
  ["320px", { width: 320, height: 720 }],
];

for (const scheme of ["light", "dark"]) {
  for (const [sizeName, viewport] of sizes) {
    test.describe(`${scheme}, ${sizeName}`, () => {
      test.use({ startPath: null, colorScheme: scheme, viewport });

      for (const [name, route, setup] of views) {
        test(`${name} has no accessibility violations`, async ({ page }) => {
          await page.goto(route);
          await page.waitForLoadState("networkidle").catch(() => {});
          if (setup) await setup(page);
          await expectAccessible(page);
        });
      }
    });
  }
}
