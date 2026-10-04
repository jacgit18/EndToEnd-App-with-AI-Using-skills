// Accounts, categories and budgets: the pages that edit reference data.
import { expect, test } from "./fixtures.js";

const rowIn = (page, region, text) => page.getByRole("region", { name: region }).getByRole("row").filter({ hasText: text });
const budgetBox = (page, category) => page.getByLabel(`Budget for ${category}`);
const budgetRow = (page, category) => rowIn(page, "Budgets", category);

test.describe("accounts", () => {
  test.use({ startPath: "/accounts" });

  test("balances include every posted transaction", async ({ page }) => {
    await expect(rowIn(page, "Accounts", "Checking")).toContainText("7565.70");
    await expect(rowIn(page, "Accounts", "Credit card")).toContainText("-735.99");
  });

  test("a new account starts at its opening balance", async ({ page }) => {
    await page.getByLabel("Name").fill("Brokerage");
    await page.getByLabel("Type").selectOption("savings");
    await page.getByLabel("Starting balance").fill("1200.5");
    await page.getByRole("button", { name: "Add account" }).click();

    await expect(rowIn(page, "Accounts", "Brokerage")).toContainText("1200.50");
  });

  test("an invalid opening balance is caught before submitting", async ({ page }) => {
    await page.getByLabel("Starting balance").fill("12.345");
    await expect(page.getByRole("alert")).toBeVisible();
    await expect(page.getByRole("button", { name: "Add account" })).toBeDisabled();
  });

  test("archived accounts are hidden until asked for", async ({ page }) => {
    const showArchived = page.getByLabel("Show archived");
    await expect(rowIn(page, "Accounts", "Old wallet")).toHaveCount(0);

    await showArchived.check();
    await expect(showArchived).toBeChecked();
    await expect(rowIn(page, "Accounts", "Old wallet (archived)")).toBeVisible();

    await showArchived.uncheck();
    await expect(rowIn(page, "Accounts", "Old wallet")).toHaveCount(0);
  });

  test("archiving an account removes it from the default list", async ({ page }) => {
    await rowIn(page, "Accounts", "Savings").getByRole("button", { name: "Archive" }).click();
    await expect(rowIn(page, "Accounts", "Savings")).toHaveCount(0);
  });
});

test.describe("categories", () => {
  test.use({ startPath: "/categories" });

  test("a duplicate name is refused with the server's reason", async ({ page }) => {
    await page.getByLabel("Name").fill("groceries");
    await page.getByRole("button", { name: "Add category" }).click();
    await expect(page.getByRole("alert")).toContainText("already exists");
  });

  test("renaming a category updates its row", async ({ page }) => {
    await rowIn(page, "Categories", "Dining").getByRole("button", { name: "Rename" }).click();
    await page.getByRole("region", { name: "Categories" }).getByLabel("Name").fill("Eating out");
    await page.getByRole("button", { name: "Save" }).click();
    await expect(rowIn(page, "Categories", "Eating out")).toBeVisible();
  });
});

test.describe("budgets", () => {
  test.use({ startPath: "/budgets" });

  test("only active expense categories get a budget line", async ({ page }) => {
    await expect(page.getByRole("region", { name: "Budgets" }).getByRole("row")).toHaveCount(5);
    await expect(budgetBox(page, "Salary")).toHaveCount(0);
    await expect(budgetBox(page, "Gym")).toHaveCount(0);
  });

  test("a saved budget survives a reload", async ({ page }) => {
    await budgetBox(page, "Dining").fill("120");
    await budgetRow(page, "Dining").getByRole("button", { name: "Save" }).click();
    await expect(budgetRow(page, "Dining").getByRole("button", { name: "Clear" })).toBeEnabled();

    await page.reload();
    await expect(budgetBox(page, "Dining")).toHaveValue("120.00");
  });

  test("clearing a budget empties the line", async ({ page }) => {
    await budgetRow(page, "Groceries").getByRole("button", { name: "Clear" }).click();
    await expect(budgetBox(page, "Groceries")).toHaveValue("");
    await expect(budgetRow(page, "Groceries").getByRole("button", { name: "Clear" })).toBeDisabled();
  });

  test("copy from last month fills only the missing lines and reports the counts", async ({ page }) => {
    await page.getByRole("button", { name: "Copy from last month" }).click();
    await expect(page.getByRole("status")).toHaveText("Copied 1 line(s); 2 not copied (already set or archived).");
    await expect(budgetBox(page, "Dining")).toHaveValue("100.00");
  });
});
