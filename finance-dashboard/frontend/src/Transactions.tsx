import { useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, type TransactionCreate } from "./api/client";

const emptyForm: TransactionCreate = {
  account_id: 0,
  date: new Date().toISOString().slice(0, 10),
  amount: "",
  description: "",
};

export default function Transactions() {
  const queryClient = useQueryClient();
  const [form, setForm] = useState(emptyForm);

  const accounts = useQuery({ queryKey: ["accounts"], queryFn: api.listAccounts });
  const transactions = useQuery({ queryKey: ["transactions"], queryFn: api.listTransactions });

  const createTransaction = useMutation({
    mutationFn: api.createTransaction,
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
    createTransaction.mutate(form);
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

      <table>
        <thead>
          <tr>
            <th style={{ textAlign: "left" }}>Date</th>
            <th style={{ textAlign: "left" }}>Description</th>
            <th style={{ textAlign: "right" }}>Amount</th>
          </tr>
        </thead>
        <tbody>
          {transactions.data?.map((t) => (
            <tr key={t.id}>
              <td>{t.date}</td>
              <td>{t.description}</td>
              <td style={{ textAlign: "right" }}>{t.amount}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
