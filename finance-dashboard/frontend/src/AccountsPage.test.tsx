import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import AccountsPage, { moneyError } from "./AccountsPage";
import type { Account } from "./api/client";

// Only the api object is faked; ACCOUNT_TYPES etc. stay real.
const listAccounts = vi.fn();
const createAccount = vi.fn();
const updateAccount = vi.fn();
vi.mock("./api/client", async (importOriginal) => ({
  ...(await importOriginal<typeof import("./api/client")>()),
  api: {
    listAccounts: (...a: unknown[]) => listAccounts(...a),
    createAccount: (...a: unknown[]) => createAccount(...a),
    updateAccount: (...a: unknown[]) => updateAccount(...a),
  },
}));

const acct = (over: Partial<Account> = {}): Account => ({
  id: 1,
  name: "Everyday",
  type: "checking",
  starting_balance: "100.00",
  balance: "150.00",
  is_archived: false,
  created_at: "2026-01-01T00:00:00Z",
  ...over,
});

function renderPage() {
  render(
    <QueryClientProvider
      client={new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })}
    >
      <MemoryRouter>
        <AccountsPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  listAccounts.mockReset().mockResolvedValue([acct()]);
  createAccount.mockReset().mockResolvedValue(acct());
  updateAccount.mockReset().mockResolvedValue(acct());
});

// Opens the (only) row's editor and returns that row, so queries can't hit the create form.
async function editRow() {
  fireEvent.click(await screen.findByRole("button", { name: "Edit" }));
  return screen.getByRole("button", { name: "Save" }).closest("tr")!;
}

describe("moneyError", () => {
  it.each(["", "  ", "0", "12.5", "-3.25", "999999999999.99"])("accepts %j", (v) => {
    expect(moneyError(v)).toBeNull();
  });
  it.each(["1.234", "abc", "1e3", "+5", "5.", "1,000", "1000000000000", "-"])("rejects %j", (v) => {
    expect(moneyError(v)).not.toBeNull();
  });
});

describe("AccountsPage", () => {
  it("lists accounts with type and balances", async () => {
    renderPage();
    expect(await screen.findByText("Everyday")).toBeInTheDocument();
    expect(screen.getByText("150.00")).toBeInTheDocument();
    expect(screen.getByText("100.00")).toBeInTheDocument();
  });

  it("create sends the type and omits a blank starting balance", async () => {
    renderPage();
    fireEvent.change(screen.getByLabelText(/^Name/), { target: { value: " Savings pot " } });
    fireEvent.change(screen.getByLabelText(/^Type/), { target: { value: "savings" } });
    fireEvent.click(screen.getByRole("button", { name: "Add account" }));
    await waitFor(() => expect(createAccount).toHaveBeenCalled());
    expect(createAccount.mock.calls[0][0]).toEqual({ name: "Savings pot", type: "savings" });
  });

  it("create sends a valid starting balance as a string", async () => {
    renderPage();
    fireEvent.change(screen.getByLabelText(/^Name/), { target: { value: "Card" } });
    fireEvent.change(screen.getByLabelText(/^Starting balance/), { target: { value: "-25.5" } });
    fireEvent.click(screen.getByRole("button", { name: "Add account" }));
    await waitFor(() => expect(createAccount).toHaveBeenCalled());
    expect(createAccount.mock.calls[0][0]).toEqual({
      name: "Card",
      type: "checking",
      starting_balance: "-25.5",
    });
  });

  it("a bad starting balance shows an error and blocks submit", () => {
    renderPage();
    fireEvent.change(screen.getByLabelText(/^Name/), { target: { value: "Card" } });
    fireEvent.change(screen.getByLabelText(/^Starting balance/), { target: { value: "1.234" } });
    expect(screen.getByRole("alert")).toHaveTextContent(/plain digits/);
    const btn = screen.getByRole("button", { name: "Add account" });
    expect(btn).toBeDisabled();
    fireEvent.submit(btn.closest("form")!);
    expect(createAccount).not.toHaveBeenCalled();
  });

  it("shows the server's error when create fails", async () => {
    createAccount.mockRejectedValue(new Error("name taken"));
    renderPage();
    fireEvent.change(screen.getByLabelText(/^Name/), { target: { value: "Dup" } });
    fireEvent.click(screen.getByRole("button", { name: "Add account" }));
    expect(await screen.findByText("name taken")).toBeInTheDocument();
  });

  it("edit sends only the changed fields", async () => {
    renderPage();
    const row = await editRow();
    fireEvent.change(within(row).getByLabelText("Name"), { target: { value: "Main" } });
    fireEvent.click(within(row).getByRole("button", { name: "Save" }));
    await waitFor(() => expect(updateAccount).toHaveBeenCalled());
    expect(updateAccount).toHaveBeenCalledWith(1, { name: "Main" });
  });

  it("edit with no changes sends nothing", async () => {
    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "Edit" }));
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    expect(updateAccount).not.toHaveBeenCalled();
    expect(screen.getByRole("button", { name: "Edit" })).toBeInTheDocument();
  });

  it("edit blocks a bad or blank starting balance", async () => {
    renderPage();
    const row = await editRow();
    const save = within(row).getByRole("button", { name: "Save" });
    const input = within(row).getByLabelText("Starting balance");
    fireEvent.change(input, { target: { value: "1.234" } });
    expect(save).toBeDisabled();
    fireEvent.change(input, { target: { value: "" } });
    expect(save).toBeDisabled();
    expect(screen.getByRole("alert")).toHaveTextContent("Required");
  });

  it("archive sends is_archived true; unarchive sends false", async () => {
    listAccounts.mockResolvedValue([acct(), acct({ id: 2, name: "Old", is_archived: true })]);
    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "Archive" }));
    await waitFor(() => expect(updateAccount).toHaveBeenCalledWith(1, { is_archived: true }));
    fireEvent.click(screen.getByRole("button", { name: "Unarchive" }));
    await waitFor(() => expect(updateAccount).toHaveBeenCalledWith(2, { is_archived: false }));
  });

  it("show archived re-queries with includeArchived", async () => {
    renderPage();
    await screen.findByText("Everyday");
    expect(listAccounts).toHaveBeenLastCalledWith({ includeArchived: false });
    fireEvent.click(screen.getByLabelText("Show archived"));
    await waitFor(() => expect(listAccounts).toHaveBeenLastCalledWith({ includeArchived: true }));
  });

  it("a failed archive shows the error on that row", async () => {
    updateAccount.mockRejectedValue(new Error("boom"));
    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "Archive" }));
    const row = (await screen.findByText(/boom/)).closest("tr")!;
    expect(within(row).getByText("Everyday")).toBeInTheDocument();
  });
});
