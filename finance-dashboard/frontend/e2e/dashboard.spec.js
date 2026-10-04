import { expect, test } from "./fixtures.js";

test.use({ startPath: "/dashboard" });

const tile = (page, name) => page.getByTestId(`tile-${name}`);

test("opens on the current month with income, expense and net", async ({ page }) => {
  await expect(page.getByLabel("Month", { exact: true })).toHaveValue("2026-10");
  await expect(tile(page, "income")).toHaveText("3200.00");
  await expect(tile(page, "expense")).toHaveText("1695.34");
  await expect(tile(page, "net")).toHaveText("1504.66");
});

test("recent transactions list this month's rows, newest first", async ({ page }) => {
  const rows = page.getByRole("region", { name: "Recent transactions" }).getByRole("row");
  await expect(rows).toHaveCount(7);
  await expect(rows.nth(1)).toContainText("Streaming service");
  await expect(rows.last()).toContainText("Paycheck");
});

test("both charts render, each with a text name", async ({ page }) => {
  await expect(page.getByRole("img", { name: "Spending by category against budget" })).toBeVisible();
  await expect(page.getByRole("img", { name: "Net per month, last six months" })).toBeVisible();
});

test("an earlier month shows that month's totals", async ({ page }) => {
  await page.getByLabel("Month", { exact: true }).fill("2026-09");
  await expect(tile(page, "net")).toHaveText("1385.60");
});

test("a month with no activity says so", async ({ page }) => {
  await page.getByLabel("Month", { exact: true }).fill("2025-01");
  await expect(tile(page, "net")).toHaveText("0.00");
  await expect(page.getByText("No transactions this month.")).toBeVisible();
});

test("clearing the month asks for one instead of querying", async ({ page }) => {
  await page.getByLabel("Month", { exact: true }).fill("");
  await expect(page.getByText("Pick a month.")).toBeVisible();
});

test("an API error is shown, not a blank page", async ({ page, api }) => {
  api.override("GET", /^\/dashboard$/, 500, { detail: "database unavailable" });
  await page.getByLabel("Month", { exact: true }).fill("2026-08");
  // React Query retries a failed query 3 times with backoff (~7s of real time); skip ahead.
  await expect(async () => {
    await page.clock.fastForward(5_000);
    await expect(page.getByRole("alert")).toContainText("database unavailable", { timeout: 500 });
  }).toPass();
});
