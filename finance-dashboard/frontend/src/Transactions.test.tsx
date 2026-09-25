import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import Transactions from "./Transactions";
import type { Account, Category, Transaction } from "./api/client";

const listAccounts = vi.fn();
const listCategories = vi.fn();
const listTransactions = vi.fn();
const createTransaction = vi.fn();
const voidTransaction = vi.fn();
vi.mock("./api/client", async (importOriginal) => ({
  ...(await importOriginal<typeof import("./api/client")>()),
  api: {
    listAccounts: (...a: unknown[]) => listAccounts(...a),
    listCategories: (...a: unknown[]) => listCategories(...a),
    listTransactions: (...a: unknown[]) => listTransactions(...a),
    createTransaction: (...a: unknown[]) => createTransaction(...a),
    voidTransaction: (...a: unknown[]) => voidTransaction(...a),
  },
}));

const acct = (over: Partial<Account> = {}): Account => ({
  id: 1,
  name: "Everyday",
  type: "checking",
  starting_balance: "0.00",
  balance: "0.00",
  is_archived: false,
  created_at: "2026-01-01T00:00:00Z",
  ...over,
});
const cat = (over: Partial<Category> = {}): Category => ({
  id: 7,
  name: "Groceries",
  kind: "expense",
  is_archived: false,
  created_at: "2026-01-01T00:00:00Z",
  ...over,
});
const tx = (over: Partial<Transaction> = {}): Transaction => ({
  id: 10,
  account_id: 1,
  category_id: null,
  date: "2026-09-10",
  amount: "-5.00",
  description: "Coffee",
  type: "normal",
  reverses_transaction_id: null,
  created_at: "2026-09-10T00:00:00Z",
  ...over,
});

function renderIt() {
  render(
    <QueryClientProvider
      client={new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })}
    >
      <Transactions />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  listAccounts.mockReset().mockResolvedValue([acct()]);
  listCategories.mockReset().mockResolvedValue([cat()]);
  listTransactions.mockReset().mockResolvedValue([tx()]);
  createTransaction.mockReset().mockResolvedValue(tx());
  voidTransaction.mockReset().mockResolvedValue(tx({ id: 11, type: "reversal", reverses_transaction_id: 10, amount: "5.00" }));
  vi.spyOn(window, "confirm").mockReturnValue(true);
});
afterEach(() => vi.restoreAllMocks());

describe("Transactions", () => {
  it("offers only the categories the API returns (archived are hidden server-side)", async () => {
    renderIt();
    const picker = await screen.findByLabelText("Category");
    await within(picker).findByRole("option", { name: "Groceries" });
    expect(listCategories).toHaveBeenCalledWith(); // default = no archived
  });

  it("posts the chosen category and a trimmed description", async () => {
    renderIt();
    await screen.findByText("Coffee");
    await within(screen.getByLabelText("Category")).findByRole("option", { name: "Groceries" });
    fireEvent.change(screen.getAllByRole("combobox")[0], { target: { value: "1" } });
    fireEvent.change(screen.getByPlaceholderText(/Amount/), { target: { value: "-12.50" } });
    fireEvent.change(screen.getByLabelText("Category"), { target: { value: "7" } });
    fireEvent.change(screen.getByPlaceholderText("Description"), { target: { value: "  Milk  " } });
    fireEvent.click(screen.getByRole("button", { name: "Add" }));
    await waitFor(() =>
      expect(createTransaction).toHaveBeenCalledWith(
        expect.objectContaining({ account_id: 1, category_id: 7, amount: "-12.50", description: "Milk" }),
      ),
    );
  });

  it("passes the month and account filters to the API", async () => {
    renderIt();
    await screen.findByText("Coffee");
    fireEvent.change(screen.getByLabelText("Month"), { target: { value: "2026-09" } });
    await waitFor(() =>
      expect(listTransactions).toHaveBeenLastCalledWith({ month: "2026-09", accountId: undefined }),
    );
    fireEvent.change(screen.getByLabelText("Filter by account"), { target: { value: "1" } });
    await waitFor(() =>
      expect(listTransactions).toHaveBeenLastCalledWith({ month: "2026-09", accountId: 1 }),
    );
  });

  it("voids after confirmation", async () => {
    renderIt();
    fireEvent.click(await screen.findByRole("button", { name: "Void" }));
    expect(window.confirm).toHaveBeenCalled();
    await waitFor(() => expect(voidTransaction).toHaveBeenCalledWith(10));
  });

  it("does not void when the confirmation is declined", async () => {
    vi.spyOn(window, "confirm").mockReturnValue(false);
    renderIt();
    fireEvent.click(await screen.findByRole("button", { name: "Void" }));
    // react-query calls the mutation function asynchronously; let it run before asserting.
    await new Promise((r) => setTimeout(r, 20));
    expect(window.confirm).toHaveBeenCalled();
    expect(voidTransaction).not.toHaveBeenCalled();
  });

  it("marks a voided row and its reversal, and offers Void on neither", async () => {
    listTransactions.mockResolvedValue([
      tx({ id: 11, type: "reversal", reverses_transaction_id: 10, amount: "5.00", description: "Void: Coffee" }),
      tx(),
    ]);
    renderIt();
    expect(await screen.findByText(/Coffee \(voided\)/)).toBeInTheDocument();
    expect(screen.getByText(/Void: Coffee \(reversal\)/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Void" })).not.toBeInTheDocument();
  });

  it("shows the server's error when a void is refused", async () => {
    voidTransaction.mockRejectedValue(new Error("account is archived"));
    renderIt();
    fireEvent.click(await screen.findByRole("button", { name: "Void" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("account is archived");
  });

  it("labels a category missing from the picker list as archived", async () => {
    listTransactions.mockResolvedValue([tx({ category_id: 99 })]);
    renderIt();
    expect(await screen.findByText("(archived)")).toBeInTheDocument();
  });
});
