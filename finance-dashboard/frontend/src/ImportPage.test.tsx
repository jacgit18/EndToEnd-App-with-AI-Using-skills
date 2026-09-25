import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import ImportPage from "./ImportPage";
import type { Account, ImportPreview, ImportResult } from "./api/client";

const listAccounts = vi.fn();
const listImports = vi.fn();
const previewImport = vi.fn();
const createImport = vi.fn();
vi.mock("./api/client", async (importOriginal) => ({
  ...(await importOriginal<typeof import("./api/client")>()),
  api: {
    listAccounts: (...a: unknown[]) => listAccounts(...a),
    listImports: (...a: unknown[]) => listImports(...a),
    previewImport: (...a: unknown[]) => previewImport(...a),
    createImport: (...a: unknown[]) => createImport(...a),
  },
}));

const acct = (id: number, name: string): Account => ({
  id, name, type: "checking", starting_balance: "0.00", balance: "0.00", is_archived: false, created_at: "2026-01-01T00:00:00Z",
});
const PREVIEW: ImportPreview = {
  headers: ["Posted Date", "Account Name", "Description", "Amount"],
  rows: [["2026-08-30", "Checking - 5219", "ELAN", "-180.00"]],
  row_count: 2,
  delimiter: ",",
  distinct_values: { "Account Name": ["Checking - 5219", "PayPal"] },
};
const RESULT: ImportResult = {
  batch_id: 1, imported_count: 1, skipped_count: 0, rejected_count: 1, excluded_count: 1,
  rejected: [{ line: 3, reason: "bad amount" }], batches: [],
};

function renderPage() {
  render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })}>
      <MemoryRouter>
        <ImportPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

const pick = (label: string, value: string) => fireEvent.change(screen.getByLabelText(label), { target: { value } });

async function uploadAndMapColumns() {
  renderPage();
  fireEvent.change(screen.getByLabelText(/CSV file/), { target: { files: [new File(["x"], "s.csv")] } });
  await screen.findByText(/2 rows/);
  pick("Date column", "Posted Date");
  pick("Amount column", "Amount");
  pick("Description column", "Description");
  pick("Date format", "iso");
  await screen.findByRole("option", { name: "Checking" });
}

beforeEach(() => {
  listAccounts.mockReset().mockResolvedValue([acct(1, "Checking"), acct(2, "PayPal acct")]);
  listImports.mockReset().mockResolvedValue([]);
  previewImport.mockReset().mockResolvedValue(PREVIEW);
  createImport.mockReset().mockResolvedValue(RESULT);
});

describe("ImportPage", () => {
  it("keeps Import disabled until columns, a date format and an account are chosen (format is never defaulted)", async () => {
    renderPage();
    fireEvent.change(screen.getByLabelText(/CSV file/), { target: { files: [new File(["x"], "s.csv")] } });
    await screen.findByText(/2 rows/);
    const button = screen.getByRole("button", { name: "Import" });
    expect(button).toBeDisabled();
    pick("Date column", "Posted Date");
    pick("Amount column", "Amount");
    pick("Description column", "Description");
    await screen.findByRole("option", { name: "Checking" });
    pick("Account", "1");
    expect(button).toBeDisabled(); // still no date format
    pick("Date format", "iso");
    expect(button).toBeEnabled();
  });

  it("single-account import sends the account id and the mapping", async () => {
    await uploadAndMapColumns();
    pick("Account", "1");
    fireEvent.click(screen.getByRole("button", { name: "Import" }));
    await screen.findByText(/Import finished/);
    const [, mapping, accountId] = createImport.mock.calls[0];
    expect(accountId).toBe(1);
    expect(mapping).toEqual({
      date_column: "Posted Date", amount_column: "Amount", description_column: "Description",
      date_format: "iso", invert_sign: false,
    });
    expect(screen.getByText(/Line 3: bad amount/)).toBeInTheDocument();
  });

  it("multi-account import needs every value decided, and sends null for excluded ones", async () => {
    await uploadAndMapColumns();
    fireEvent.click(screen.getByLabelText(/has an account column/));
    pick("Account column", "Account Name");
    const button = screen.getByRole("button", { name: "Import" });
    pick("Account for Checking - 5219", "1");
    expect(button).toBeDisabled(); // PayPal still undecided
    pick("Account for PayPal", "exclude");
    expect(button).toBeEnabled();
    fireEvent.click(button);
    await waitFor(() => expect(createImport).toHaveBeenCalled());
    const [, mapping, accountId] = createImport.mock.calls[0];
    expect(accountId).toBeUndefined();
    expect(mapping.account_column).toBe("Account Name");
    expect(mapping.account_map).toEqual({ "Checking - 5219": 1, PayPal: null });
    expect(await screen.findByText(/left out 1/)).toBeInTheDocument();
  });

  it("refuses an account column that is also the date/amount/description column", async () => {
    await uploadAndMapColumns();
    fireEvent.click(screen.getByLabelText(/has an account column/));
    pick("Account column", "Account Name");
    pick("Account for Checking - 5219", "1");
    pick("Account for PayPal", "1");
    expect(screen.getByRole("button", { name: "Import" })).toBeEnabled();
    pick("Description column", "Account Name");
    expect(screen.getByRole("button", { name: "Import" })).toBeDisabled();
  });

  it("blocks Import and warns when the chosen amount column has no numbers in the sample", async () => {
    await uploadAndMapColumns();
    expect(screen.queryByRole("alert")).toBeNull();
    pick("Account", "1");
    expect(screen.getByRole("button", { name: "Import" })).toBeEnabled();
    pick("Amount column", "Account Name");
    expect(screen.getByRole("alert")).toHaveTextContent(/None of the 1 sample rows/);
    expect(screen.getByRole("button", { name: "Import" })).toBeDisabled();
    pick("Amount column", "Amount");
    expect(screen.queryByRole("alert")).toBeNull();
  });

  it("shows the server's error when the import fails", async () => {
    createImport.mockRejectedValue(new Error("account is archived"));
    await uploadAndMapColumns();
    pick("Account", "1");
    fireEvent.click(screen.getByRole("button", { name: "Import" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("account is archived");
  });
});
