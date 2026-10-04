// The ADR-0015 smoke path against the real stack: sign in, make an account, add a
// transaction, see it on the dashboard. Nothing is mocked, so this also covers what the
// mocked suite cannot: Caddy routing /api, the ENV=prod Secure session cookie, CSRF,
// migrations having run, and Postgres actually storing the money as a string.
// Run it on a fresh stack (scripts/real-stack.sh down && up): a second run on the same
// database adds a second "Smoke checking" and the totals no longer match.
import { expect, test } from "@playwright/test";

const email = process.env.REAL_STACK_EMAIL;
const password = process.env.REAL_STACK_PASSWORD;
test.skip(!email || !password, "REAL_STACK_EMAIL / REAL_STACK_PASSWORD not set (run scripts/real-stack.sh up)");

test.describe.configure({ mode: "serial" });

test("the health endpoint reports the database through Caddy", async ({ request }) => {
  const res = await request.get("/health");
  expect(res.ok()).toBe(true);
  expect(await res.json()).toEqual({ status: "ok", db: "connected" });
});

test("a signed-out visit to a data route goes to sign in, and the API says 401", async ({ page, request }) => {
  expect((await request.get("/api/accounts")).status()).toBe(401);
  await page.goto("/accounts");
  await expect(page).toHaveURL(/\/login$/);
});

test("a wrong password is refused", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill("not-the-password");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByRole("alert")).toHaveText("Invalid email or password.");
});

test("sign in, add an account and a transaction, see it on the dashboard", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL("/");
  await expect(page.getByText("Backend: connected")).toBeVisible();

  await page.goto("/accounts");
  await page.getByLabel("Name").fill("Smoke checking");
  await page.getByLabel("Starting balance").fill("100");
  await page.getByRole("button", { name: "Add account" }).click();
  await expect(page.getByRole("cell", { name: "Smoke checking" })).toBeVisible();

  await page.goto("/");
  await page.getByLabel("Account", { exact: true }).selectOption({ label: "Smoke checking" });
  await page.getByLabel("Amount (- for expense)").fill("-12.34");
  await page.getByLabel("Description").fill("Smoke coffee");
  await page.getByRole("button", { name: "Add" }).click();
  const row = page.getByRole("region", { name: "Transactions" }).getByRole("row").filter({ hasText: "Smoke coffee" });
  await expect(row).toContainText("-12.34");

  // A reload proves it reached Postgres and is not just client state.
  await page.reload();
  await expect(row).toContainText("-12.34");

  await page.getByRole("link", { name: "Dashboard" }).click();
  await expect(page.getByTestId("tile-expense")).toHaveText("12.34");
  await expect(page.getByRole("region", { name: "Recent transactions" })).toContainText("Smoke coffee");
});
