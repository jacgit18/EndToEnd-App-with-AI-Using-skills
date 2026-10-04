import { CREDENTIALS, expect, test } from "./fixtures.js";

const email = (page) => page.getByLabel("Email");
const password = (page) => page.getByLabel("Password");
const signIn = (page) => page.getByRole("button", { name: "Sign in" });

test.describe("signed out", () => {
  test.use({ signedIn: false, startPath: "/login" });

  test("signing in with the right credentials opens the transactions page", async ({ page }) => {
    await email(page).fill(CREDENTIALS.email);
    await password(page).fill(CREDENTIALS.password);
    await signIn(page).click();

    await expect(page).toHaveURL("/");
    await expect(page.getByRole("heading", { level: 1, name: "Finance Dashboard" })).toBeVisible();
    await expect(page.getByRole("region", { name: "Transactions" }).getByRole("row")).toHaveCount(18);
  });

  test("a wrong password shows one message that does not say which field was wrong", async ({ page }) => {
    await email(page).fill(CREDENTIALS.email);
    await password(page).fill("not-the-password");
    await signIn(page).click();

    await expect(page.getByRole("alert")).toHaveText("Invalid email or password.");
    await expect(page).toHaveURL("/login");
  });

  test("too many attempts tells the owner to wait", async ({ page, api }) => {
    api.override("POST", /^\/auth\/login$/, 429, { detail: "Too many attempts" });
    await email(page).fill(CREDENTIALS.email);
    await password(page).fill(CREDENTIALS.password);
    await signIn(page).click();

    await expect(page.getByRole("alert")).toContainText("Too many attempts");
  });

  test("opening any app page without a session sends you to sign in", async ({ page }) => {
    await page.goto("/accounts");
    await expect(page).toHaveURL("/login");
  });
});

test("signing out returns to the sign-in page and the session stops working", async ({ page, api }) => {
  await page.getByRole("button", { name: "Sign out" }).click();

  await expect(page).toHaveURL("/login");
  expect(api.session.signedIn).toBe(false);
  await page.goto("/budgets");
  await expect(page).toHaveURL("/login");
});
