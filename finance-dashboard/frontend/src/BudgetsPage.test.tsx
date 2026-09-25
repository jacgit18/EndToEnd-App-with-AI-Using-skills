import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import BudgetsPage from "./BudgetsPage";
import { ApiError, type Budget, type Category } from "./api/client";

const listCategories = vi.fn();
const listBudgets = vi.fn();
const setBudget = vi.fn();
const clearBudget = vi.fn();
const copyBudgetsForward = vi.fn();
vi.mock("./api/client", async (importOriginal) => ({
  ...(await importOriginal<typeof import("./api/client")>()),
  api: {
    listCategories: (...a: unknown[]) => listCategories(...a),
    listBudgets: (...a: unknown[]) => listBudgets(...a),
    setBudget: (...a: unknown[]) => setBudget(...a),
    clearBudget: (...a: unknown[]) => clearBudget(...a),
    copyBudgetsForward: (...a: unknown[]) => copyBudgetsForward(...a),
  },
}));

const cat = (over: Partial<Category> = {}): Category => ({
  id: 1,
  name: "Groceries",
  kind: "expense",
  is_archived: false,
  created_at: "2026-01-01T00:00:00Z",
  ...over,
});
const budget = (over: Partial<Budget> = {}): Budget => ({
  id: 1,
  category_id: 1,
  month: "2026-09",
  amount: "250.00",
  ...over,
});

function renderPage() {
  render(
    <QueryClientProvider
      client={new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })}
    >
      <MemoryRouter>
        <BudgetsPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  // Local time on purpose: the page defaults to the local month.
  vi.useFakeTimers({ toFake: ["Date"], now: new Date(2026, 8, 15, 12) });
  listCategories.mockReset().mockResolvedValue([cat(), cat({ id: 2, name: "Salary", kind: "income" })]);
  listBudgets.mockReset().mockResolvedValue([]);
  setBudget.mockReset().mockResolvedValue(budget());
  clearBudget.mockReset().mockResolvedValue(undefined);
  copyBudgetsForward.mockReset().mockResolvedValue({ copied: 0, skipped: 0 });
});
afterEach(() => vi.useRealTimers());

describe("BudgetsPage", () => {
  it("defaults to the current local month and lists only expense categories", async () => {
    renderPage();
    expect(await screen.findByLabelText("Budget for Groceries")).toBeInTheDocument();
    expect(screen.queryByLabelText("Budget for Salary")).not.toBeInTheDocument();
    expect(screen.getByLabelText("Month")).toHaveValue("2026-09");
    expect(listBudgets).toHaveBeenCalledWith("2026-09");
  });

  it("shows the saved amount, and none for a category without a line", async () => {
    listCategories.mockResolvedValue([cat(), cat({ id: 3, name: "Rent" })]);
    listBudgets.mockResolvedValue([budget()]);
    renderPage();
    await waitFor(() => expect(screen.getByLabelText("Budget for Groceries")).toHaveValue("250.00"));
    expect(screen.getByLabelText("Budget for Rent")).toHaveValue("");
  });

  it("saves a trimmed amount for that category and month", async () => {
    renderPage();
    fireEvent.change(await screen.findByLabelText("Budget for Groceries"), { target: { value: " 300.50 " } });
    fireEvent.click(screen.getAllByRole("button", { name: "Save" })[0]);
    await waitFor(() => expect(setBudget).toHaveBeenCalledWith("2026-09", 1, "300.50"));
  });

  it("keeps Save disabled for an empty or unchanged amount", async () => {
    listBudgets.mockResolvedValue([budget()]);
    renderPage();
    const input = await screen.findByLabelText("Budget for Groceries");
    await waitFor(() => expect(input).toHaveValue("250.00"));
    const save = screen.getByRole("button", { name: "Save" });
    expect(save).toBeDisabled();
    fireEvent.change(input, { target: { value: "" } });
    expect(save).toBeDisabled();
    fireEvent.change(input, { target: { value: "251" } });
    expect(save).toBeEnabled();
  });

  it("shows the server's error when a save is refused", async () => {
    setBudget.mockRejectedValue(new ApiError(409, "category is archived"));
    renderPage();
    fireEvent.change(await screen.findByLabelText("Budget for Groceries"), { target: { value: "5" } });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("category is archived");
  });

  it("clears an existing line, and disables Clear when there is none", async () => {
    listBudgets.mockResolvedValue([budget()]);
    listCategories.mockResolvedValue([cat(), cat({ id: 3, name: "Rent" })]);
    renderPage();
    await waitFor(() => expect(screen.getByLabelText("Budget for Groceries")).toHaveValue("250.00"));
    const [clearGroceries, clearRent] = screen.getAllByRole("button", { name: "Clear" });
    expect(clearRent).toBeDisabled();
    fireEvent.click(clearGroceries);
    await waitFor(() => expect(clearBudget).toHaveBeenCalledWith("2026-09", 1));
  });

  it("copies from last month and reports copied and skipped", async () => {
    copyBudgetsForward.mockResolvedValue({ copied: 3, skipped: 1 });
    renderPage();
    await screen.findByLabelText("Budget for Groceries");
    // A month other than the default, so "copies into the month on screen" is tested.
    fireEvent.change(screen.getByLabelText("Month"), { target: { value: "2026-11" } });
    fireEvent.click(screen.getByRole("button", { name: "Copy from last month" }));
    expect(await screen.findByRole("status")).toHaveTextContent("Copied 3 line(s); 1 not copied");
    expect(copyBudgetsForward).toHaveBeenCalledWith("2026-11");
  });

  it("re-reads the budgets when the month changes", async () => {
    renderPage();
    await screen.findByLabelText("Budget for Groceries");
    fireEvent.change(screen.getByLabelText("Month"), { target: { value: "2026-10" } });
    await waitFor(() => expect(listBudgets).toHaveBeenCalledWith("2026-10"));
  });

  it("does not query or offer copy while the month is cleared", async () => {
    renderPage();
    await screen.findByLabelText("Budget for Groceries");
    listBudgets.mockClear();
    fireEvent.change(screen.getByLabelText("Month"), { target: { value: "" } });
    expect(await screen.findByText("Pick a month.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Copy from last month" })).toBeDisabled();
    expect(listBudgets).not.toHaveBeenCalled();
  });
});
