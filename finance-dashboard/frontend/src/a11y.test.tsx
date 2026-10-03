// Structure checks found by the 2026-10-03 axe audit (see ../ACCESSIBILITY.md): one main
// landmark and one h1 per page, every form control named, no empty table headers.
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, within } from "@testing-library/react";
import type { ReactElement } from "react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import AccountsPage from "./AccountsPage";
import App from "./App";
import BudgetsPage from "./BudgetsPage";
import CategoriesPage from "./CategoriesPage";
import ImportPage from "./ImportPage";
import LoginPage from "./LoginPage";
import { ScrollTable, VisuallyHidden } from "./a11y";

const account = { id: 1, name: "Checking", type: "checking", starting_balance: "0.00", balance: "10.00", is_archived: false, created_at: "" };
const category = { id: 1, name: "Dining", kind: "expense", is_archived: false, created_at: "" };
const tx = { id: 1, account_id: 1, category_id: 1, date: "2026-09-10", amount: "-4.50", description: "Coffee", type: "manual", reverses_transaction_id: null, created_at: "" };
vi.mock("./api/client", async (importOriginal) => ({
  ...(await importOriginal<typeof import("./api/client")>()),
  api: {
    health: async () => ({ db: "connected" }),
    listAccounts: async () => [account],
    listCategories: async () => [category],
    listBudgets: async () => [{ id: 1, category_id: 1, month: "2026-09", amount: "50.00" }],
    listTransactions: async () => [tx],
    listImports: async () => [{ id: 1, filename: "a.csv", account_id: 1, imported_count: 1, skipped_count: 0, rejected_count: 0, created_at: "2026-09-10T00:00:00Z" }],
  },
}));

function renderPage(ui: ReactElement) {
  render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>,
  );
}

const pages: [string, ReactElement, string][] = [
  ["Accounts", <AccountsPage />, "Checking"],
  ["Categories", <CategoriesPage />, "Dining"],
  ["Budgets", <BudgetsPage />, "Dining"],
  ["Import", <ImportPage />, "a.csv"],
  ["Transactions (home)", <App />, "Coffee"],
  ["Login", <LoginPage />, ""],
];

describe.each(pages)("%s page structure", (_name, ui, waitFor) => {
  it("has one main landmark, one h1, named controls and no empty table headers", async () => {
    renderPage(ui);
    if (waitFor) await screen.findByText(waitFor);
    expect(screen.getAllByRole("main")).toHaveLength(1);
    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
    // Query the DOM, not roles: date and month inputs have no role in testing-library.
    for (const el of document.querySelectorAll("input:not([type=hidden]), select, textarea, button")) {
      expect(el).toHaveAccessibleName();
    }
    for (const th of document.querySelectorAll("th")) expect(th.textContent?.trim()).not.toBe("");
  });
});

describe("a11y helpers", () => {
  it("ScrollTable is a focusable, named region", () => {
    render(<ScrollTable label="Things"><table /></ScrollTable>);
    const region = screen.getByRole("region", { name: "Things" });
    expect(region).toHaveAttribute("tabindex", "0");
    expect(region).toHaveStyle({ position: "relative" }); // contains VisuallyHidden's absolute box
  });

  it("VisuallyHidden keeps its text available to screen readers", () => {
    render(<table><thead><tr><th><VisuallyHidden>Actions</VisuallyHidden></th></tr></thead></table>);
    expect(within(screen.getByRole("columnheader")).getByText("Actions")).toBeInTheDocument();
  });
});
