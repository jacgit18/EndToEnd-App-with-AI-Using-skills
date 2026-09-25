import { useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, type Transaction, type TransactionCreate } from "./api/client";

const emptyForm: TransactionCreate = {
  account_id: 0,
  date: new Date().toISOString().slice(0, 10),
  amount: "",
  description: "",
};

export default function Transactions() {
  const queryClient = useQueryClient();
  const [form, setForm] = useState(emptyForm);
  // List filters (S4): "" = no filter. month is the <input type="month"> value, YYYY-MM.
  const [month, setMonth] = useState("");
  const [filterAccount, setFilterAccount] = useState(0);

  const accounts = useQuery({ queryKey: ["accounts"], queryFn: () => api.listAccounts() });
  // Archived categories are hidden by the backend default, so they never reach the picker.
  const categories = useQuery({
    queryKey: ["categories", { includeArchived: false }],
    queryFn: () => api.listCategories(),
  });
  // Filters are part of the key, so each view caches separately; invalidating the bare
  // ["transactions"] prefix refreshes all of them.
  const transactions = useQuery({
    queryKey: ["transactions", { month, accountId: filterAccount }],
    queryFn: () =>
      api.listTransactions({ month: month || undefined, accountId: filterAccount || undefined }),
  });

  // A row is voided when a reversal in the list points at it. The reversal keeps the
  // original's date and account, so any month/account filter includes both or neither.
  const voidedIds = new Set(
    transactions.data?.flatMap((t) => (t.reverses_transaction_id ? [t.reverses_transaction_id] : [])),
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
      setForm(emptyForm);
    },
  });

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    createTransaction.mutate({ ...form, description: form.description.trim() });
  }

  return (
    <section style={{ fontFamily: "system-ui, sans-serif", padding: "2rem" }}>
      <h2>Transactions</h2>

      <form onSubmit={handleSubmit} style={{ display: "flex", gap: "0.5rem", marginBottom: "1.5rem" }}>
        <select
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
          required
          value={form.date}
          onChange={(e) => setForm({ ...form, date: e.target.value })}
        />
        {/* Amount stays a string end to end — same money-as-string rule as
            api/client.ts, never coerced to a number here either. */}
        <input
          type="text"
          inputMode="decimal"
          placeholder="Amount (- for expense)"
          required
          value={form.amount}
          onChange={(e) => setForm({ ...form, amount: e.target.value })}
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
        <p style={{ color: "crimson" }}>{(createTransaction.error as Error).message}</p>
      )}

      <div style={{ display: "flex", gap: "0.5rem", marginBottom: "0.5rem" }}>
        <label>
          Month <input type="month" value={month} onChange={(e) => setMonth(e.target.value)} />
        </label>
        <label>
          Account{" "}
          <select
            aria-label="Filter by account"
            value={filterAccount || ""}
            onChange={(e) => setFilterAccount(Number(e.target.value))}
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

      <table>
        <thead>
          <tr>
            <th style={{ textAlign: "left" }}>Date</th>
            <th style={{ textAlign: "left" }}>Description</th>
            <th style={{ textAlign: "left" }}>Category</th>
            <th style={{ textAlign: "right" }}>Amount</th>
            <th />
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
                  : (categories.data.find((c) => c.id === t.category_id)?.name ?? "(archived)")
              }
            />
          ))}
        </tbody>
      </table>
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
    <tr style={voided || isReversal ? { opacity: 0.55 } : undefined}>
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
          <span role="alert" style={{ color: "crimson" }}> {(voidTx.error as Error).message}</span>
        )}
      </td>
    </tr>
  );
}
