import { expect, test } from "./fixtures.js";

const table = (page) => page.getByRole("region", { name: "Transactions" });
const rowFor = (page, description) => table(page).getByRole("row").filter({ hasText: description });

async function addTransaction(page, { account, amount, category, description }) {
  await page.getByLabel("Account", { exact: true }).selectOption({ label: account });
  await page.getByLabel("Amount (- for expense)").fill(amount);
  if (category) await page.getByLabel("Category").selectOption({ label: category });
  await page.getByLabel("Description").fill(description);
  await page.getByRole("button", { name: "Add" }).click();
}

test("the date field defaults to today in local time", async ({ page }) => {
  await expect(page.getByLabel("Date")).toHaveValue("2026-10-15");
});

test.describe("late evening", () => {
  test.use({ startPath: null });

  // 22:00 in New York is already the next day in UTC; toISOString() used to default to that.
  test("the date field still shows the local day", async ({ page }) => {
    await page.clock.setSystemTime(new Date("2026-10-15T22:00:00-04:00"));
    await page.goto("/");
    await expect(page.getByLabel("Date")).toHaveValue("2026-10-15");
  });
});

test("the backend badge reports the connection", async ({ page, api }) => {
  await expect(page.getByText("Backend: connected")).toBeVisible();

  api.session.backendDown = true;
  await page.reload();
  await expect(page.getByText("Backend: unreachable")).toBeVisible();
});

// The ADR-0015 smoke path, against the mock API: add a transaction, see it on the dashboard.
test("a new expense shows in the list and moves the dashboard totals", async ({ page, api }) => {
  await addTransaction(page, { account: "Credit card", amount: "-45.10", category: "Groceries", description: "Farmers market" });

  await expect(rowFor(page, "Farmers market")).toContainText("-45.10");
  await expect(rowFor(page, "Farmers market")).toContainText("Groceries");
  expect(api.db.transactions.at(-1)).toMatchObject({ account_id: 2, category_id: 1, amount: "-45.10", date: "2026-10-15" });

  await page.getByRole("link", { name: "Dashboard" }).click();
  await expect(page.getByTestId("tile-expense")).toHaveText("1740.44");
  await expect(page.getByTestId("tile-net")).toHaveText("1459.56");
  await expect(page.getByRole("region", { name: "Recent transactions" })).toContainText("Farmers market");
});

test("the form clears after a successful add", async ({ page }) => {
  await addTransaction(page, { account: "Checking", amount: "12", description: "Refund" });

  await expect(rowFor(page, "Refund")).toContainText("12.00");
  await expect(page.getByLabel("Description")).toHaveValue("");
  await expect(page.getByLabel("Amount (- for expense)")).toHaveValue("");
});

test("a rejected amount shows the server's message and adds nothing", async ({ page, api }) => {
  const before = api.db.transactions.length;
  await addTransaction(page, { account: "Checking", amount: "twelve", description: "Typo" });

  await expect(page.getByText("amount must be a money amount")).toBeVisible();
  expect(api.db.transactions).toHaveLength(before);
});

test("voiding asks first; dismissing leaves the row alone", async ({ page, api }) => {
  const before = api.db.transactions.length;
  page.once("dialog", (d) => d.dismiss());
  await rowFor(page, "Streaming service").getByRole("button", { name: "Void" }).click();

  await expect(rowFor(page, "Streaming service")).not.toContainText("(voided)");
  expect(api.db.transactions).toHaveLength(before);
});

test("accepting the void posts a reversal and marks the original voided", async ({ page }) => {
  let message = "";
  page.once("dialog", (d) => {
    message = d.message();
    d.accept();
  });
  await rowFor(page, "Streaming service").getByRole("button", { name: "Void" }).click();

  expect(message).toContain('Void "Streaming service" (-19.99)');
  await expect(rowFor(page, "Streaming service (voided)")).toBeVisible();
  await expect(rowFor(page, "Streaming service (reversal)")).toContainText("19.99");
  await expect(rowFor(page, "Streaming service (voided)").getByRole("button", { name: "Void" })).toHaveCount(0);
});

test("filtering by month and account narrows the list", async ({ page }) => {
  await expect(table(page).getByRole("row")).toHaveCount(18); // header + 17 seeded rows

  await page.getByLabel("Month", { exact: true }).fill("2026-10");
  await expect(table(page).getByRole("row")).toHaveCount(7);

  await page.getByLabel("Filter by account").selectOption({ label: "Checking" });
  await expect(table(page).getByRole("row")).toHaveCount(4);
  await expect(table(page)).not.toContainText("Noodle bar");
});
