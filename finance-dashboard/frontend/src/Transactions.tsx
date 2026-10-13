import { useMemo, useState, type FormEvent } from "react";
import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  api,
  TRANSACTIONS_MAX_PAGE_SIZE,
  TRANSACTIONS_PAGE_SIZE,
  type Transaction,
  type TransactionCreate,
} from "./api/client";
import { ERROR_TEXT, MUTED_ROW, ScrollTable, VisuallyHidden } from "./a11y";
import { formatNumberWithCommas, stripCommas } from "./numberFormatting";

// Today as the owner's local calendar date (toISOString would be UTC, a day ahead
// in the evening), read when the form is made so it doesn't go stale overnight.
function emptyForm(): TransactionCreate {
  const d = new Date();
  const pad = (n: number) => String(n).padStart(2, "0");
  return {
    account_id: 0,
    date: `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`,
    amount: "",
    description: "",
  };
}

export default function Transactions() {
  const queryClient = useQueryClient();
  const [form, setForm] = useState(emptyForm);
  // List filters (S4): "" = no filter. month is the <input type="month"> value, YYYY-MM.
  const [month, setMonth] = useState("");
  const [filterAccount, setFilterAccount] = useState(0);
  // Page size: the list is newest-first and capped, so a long ledger never loads at once.
  // "Show more" raises it; changing a filter starts over at one page.
  const [limit, setLimit] = useState(TRANSACTIONS_PAGE_SIZE);

  const accounts = useQuery({ queryKey: ["accounts"], queryFn: () => api.listAccounts() });
  // Archived categories are hidden by the backend default, so they never reach the picker.
  const categories = useQuery({
    queryKey: ["categories", { includeArchived: false }],
    queryFn: () => api.listCategories(),
  });
  // Filters are part of the key, so each view caches separately; invalidating the bare
  // ["transactions"] prefix refreshes all of them.
  const transactions = useQuery({
    queryKey: ["transactions", { month, accountId: filterAccount, limit }],
    queryFn: () =>
      api.listTransactions({
        month: month || undefined,
        accountId: filterAccount || undefined,
        limit,
      }),
    placeholderData: keepPreviousData, // keep the rows on screen while "Show more" loads
  });
  const mayHaveMore = (transactions.data?.length ?? 0) >= limit;

  // A row is voided when a reversal in the list points at it. The reversal keeps the
  // original's date and account, so any month/account filter includes both or neither.
  const voidedIds = useMemo(
    () =>
      new Set(
        transactions.data?.flatMap((t) => (t.reverses_transaction_id ? [t.reverses_transaction_id] : [])),
      ),
    [transactions.data],
  );
  const categoryNames = useMemo(
    () => new Map(categories.data?.map((c) => [c.id, c.name])),
    [categories.data],
  );

  const createTransaction = useMutation({
    mutationFn: (body: TransactionCreate) => api.createTransaction(body),
    onSuccess: () => {
      // A successful POST changes two things server-side at once: the ledger
      // gained a row, and account.balance moved (create_transaction updates
      // it in the same DB transaction, ADR-0005). Invalidating both queries
      // re-fetches the real numbers rather than hand-patching the cache with
      // a guess at the new shape — the source of truth is the database.
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      queryClient.invalidateQueries({ queryKey: ["accounts"] });
      // The dashboard totals and trend are built from the same ledger rows.
      // "dashboard-trend" is a separate key, not a child of "dashboard".
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-trend"] });
      setForm(emptyForm());
    },
  });

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    createTransaction.mutate({
      ...form,
      amount: stripCommas(form.amount),
      description: form.description.trim()
    });
  }

  return (
    <section style={{ fontFamily: "system-ui, sans-serif", padding: "2rem" }}>
      <h2>Transactions</h2>

      <form onSubmit={handleSubmit} style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", marginBottom: "1.5rem" }}>
        <select
          aria-label="Account"
          required
          value={form.account_id || ""}
          onChange={(e) => setForm({ ...form, account_id: Number(e.target.value) })}
        >
          <option value="" disabled>
            Account
          </option>
          {accounts.data?.map((a) => (
            <option key={a.id} value={a.id}>
              {a.name}
            </option>
          ))}
        </select>
        <input
          type="date"
          aria-label="Date"
          required
          value={form.date}
          onChange={(e) => setForm({ ...form, date: e.target.value })}
        />
        {/* Amount stays a string end to end — same money-as-string rule as
            api/client.ts, never coerced to a number here either. */}
        <input
          type="text"
          inputMode="decimal"
          aria-label="Amount (- for expense)"
          placeholder="Amount (- for expense)"
          required
          value={formatNumberWithCommas(form.amount)}
          onChange={(e) => setForm({ ...form, amount: stripCommas(e.target.value) })}
        />
        <select
          aria-label="Category"
          value={form.category_id ?? ""}
          onChange={(e) =>
            setForm({ ...form, category_id: e.target.value ? Number(e.target.value) : null })
          }
        >
          <option value="">No category</option>
          {categories.data?.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
        <input
          type="text"
          aria-label="Description"
          placeholder="Description"
          required
          value={form.description}
          onChange={(e) => setForm({ ...form, description: e.target.value })}
        />
        <button type="submit" disabled={createTransaction.isPending}>
          Add
        </button>
      </form>

      {createTransaction.isError && (
        <p style={{ color: ERROR_TEXT }}>{(createTransaction.error as Error).message}</p>
      )}

      <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", marginBottom: "0.5rem" }}>
        <label>
          Month <input type="month" value={month} onChange={(e) => {
              setMonth(e.target.value);
              setLimit(TRANSACTIONS_PAGE_SIZE);
            }}
          />
        </label>
        <label>
          Account{" "}
          <select
            aria-label="Filter by account"
            value={filterAccount || ""}
            onChange={(e) => {
              setFilterAccount(Number(e.target.value));
              setLimit(TRANSACTIONS_PAGE_SIZE);
            }}
          >
            <option value="">All accounts</option>
            {accounts.data?.map((a) => (
              <option key={a.id} value={a.id}>
                {a.name}
              </option>
            ))}
          </select>
        </label>
      </div>

      <ScrollTable label="Transactions"><table>
        <thead>
          <tr>
            <th style={{ textAlign: "left" }}>Date</th>
            <th style={{ textAlign: "left" }}>Description</th>
            <th style={{ textAlign: "left" }}>Category</th>
            <th style={{ textAlign: "right" }}>Amount</th>
            <th><VisuallyHidden>Actions</VisuallyHidden></th>
          </tr>
        </thead>
        <tbody>
          {transactions.data?.map((t) => (
            <TransactionRow
              key={t.id}
              t={t}
              voided={voidedIds.has(t.id)}
              categoryName={
                t.category_id === null || !categories.data
                  ? ""
                  : (categoryNames.get(t.category_id) ?? "(archived)")
              }
            />
          ))}
        </tbody>
      </table></ScrollTable>
      {mayHaveMore && (
        <p role="status">
          Showing the newest {transactions.data?.length} transactions.{" "}
          {limit < TRANSACTIONS_MAX_PAGE_SIZE ? (
            <button
              type="button"
              onClick={() => setLimit((l) => Math.min(l + TRANSACTIONS_PAGE_SIZE, TRANSACTIONS_MAX_PAGE_SIZE))}
            >
              Show more
            </button>
          ) : (
            "Pick a month or an account to narrow the list."
          )}
        </p>
      )}
    </section>
  );
}

function TransactionRow({
  t,
  voided,
  categoryName,
}: {
  t: Transaction;
  voided: boolean;
  categoryName: string;
}) {
  const queryClient = useQueryClient();
  const voidTx = useMutation({
    mutationFn: () => api.voidTransaction(t.id),
    onSuccess: () => {
      // A void adds a ledger row and moves the account's balance, like a create.
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      queryClient.invalidateQueries({ queryKey: ["accounts"] });
      // The dashboard totals and trend are built from the same ledger rows.
      // "dashboard-trend" is a separate key, not a child of "dashboard".
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-trend"] });
    },
  });

  const isReversal = t.type === "reversal";

  function handleVoid() {
    // Voiding is permanent (a reversal row can't be undone, only re-posted), so confirm.
    if (window.confirm(`Void "${t.description}" (${t.amount})? This posts a reversing entry.`)) {
      voidTx.mutate();
    }
  }

  return (
    <tr style={voided || isReversal ? MUTED_ROW : undefined}>
      <td>{t.date}</td>
      <td style={voided ? { textDecoration: "line-through" } : undefined}>
        {t.description}
        {voided && " (voided)"}
        {isReversal && " (reversal)"}
      </td>
      {/* Archived categories aren't in the picker list, so the parent labels them "(archived)". */}
      <td>{categoryName}</td>
      <td style={{ textAlign: "right" }}>{t.amount}</td>
      <td>
        {!voided && !isReversal && (
          <button onClick={handleVoid} disabled={voidTx.isPending}>
            Void
          </button>
        )}
        {voidTx.isError && (
          <span role="alert" style={{ color: ERROR_TEXT }}> {(voidTx.error as Error).message}</span>
        )}
      </td>
    </tr>
  );
}
