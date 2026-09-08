import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import {
  createTransaction,
  listAccounts,
  listTransactions,
} from "../api/client";

const today = () => new Date().toISOString().slice(0, 10);

export function TransactionsPage() {
  const qc = useQueryClient();

  const { data: transactions = [], isLoading } = useQuery({
    queryKey: ["transactions"],
    queryFn: listTransactions,
  });
  const { data: accounts = [] } = useQuery({
    queryKey: ["accounts"],
    queryFn: listAccounts,
  });

  const [form, setForm] = useState({
    account_id: "",
    date: today(),
    amount: "",
    description: "",
  });

  const create = useMutation({
    mutationFn: () =>
      createTransaction({
        account_id: Number(form.account_id),
        date: form.date,
        amount: form.amount,
        description: form.description,
        category_id: null,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["transactions"] });
      setForm((f) => ({ ...f, amount: "", description: "" }));
    },
  });

  const accountName = (id: number) =>
    accounts.find((a) => a.id === id)?.name ?? `#${id}`;

  return (
    <section>
      <form
        className="mb-6 grid grid-cols-2 gap-3 rounded-lg border border-gray-200 p-4 sm:grid-cols-5"
        onSubmit={(e) => {
          e.preventDefault();
          create.mutate();
        }}
      >
        <select
          className="rounded border border-gray-300 px-2 py-1"
          value={form.account_id}
          onChange={(e) => setForm({ ...form, account_id: e.target.value })}
          required
        >
          <option value="" disabled>
            Account…
          </option>
          {accounts.map((a) => (
            <option key={a.id} value={a.id}>
              {a.name}
            </option>
          ))}
        </select>
        <input
          className="rounded border border-gray-300 px-2 py-1"
          type="date"
          value={form.date}
          onChange={(e) => setForm({ ...form, date: e.target.value })}
        />
        <input
          className="rounded border border-gray-300 px-2 py-1"
          type="number"
          step="0.01"
          value={form.amount}
          onChange={(e) => setForm({ ...form, amount: e.target.value })}
          placeholder="Amount (− out)"
          required
        />
        <input
          className="rounded border border-gray-300 px-2 py-1"
          value={form.description}
          onChange={(e) => setForm({ ...form, description: e.target.value })}
          placeholder="Description"
        />
        <button
          className="rounded bg-blue-600 px-3 py-1 font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          type="submit"
          disabled={create.isPending}
        >
          Add
        </button>
      </form>

      {accounts.length === 0 && (
        <p className="mb-4 rounded bg-amber-50 px-3 py-2 text-sm text-amber-800">
          No accounts yet. Create one:{" "}
          <code className="font-mono">
            curl -X POST localhost:8000/api/accounts -H 'content-type:
            application/json' -d {"'"}
            {'{"name":"Checking","type":"checking"}'}
            {"'"}
          </code>
        </p>
      )}

      {create.isError && (
        <p className="mb-4 text-sm text-red-600">Could not save the transaction.</p>
      )}

      {isLoading ? (
        <p>Loading…</p>
      ) : (
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-gray-300 text-gray-500">
              <th className="py-2 font-medium">Date</th>
              <th className="font-medium">Description</th>
              <th className="font-medium">Account</th>
              <th className="text-right font-medium">Amount</th>
            </tr>
          </thead>
          <tbody>
            {transactions.map((t) => (
              <tr key={t.id} className="border-b border-gray-100">
                <td className="py-2">{t.date}</td>
                <td>
                  {t.description || (
                    <span className="text-gray-400">—</span>
                  )}
                </td>
                <td>{accountName(t.account_id)}</td>
                <td className="text-right font-mono tabular-nums">{t.amount}</td>
              </tr>
            ))}
            {transactions.length === 0 && (
              <tr>
                <td colSpan={4} className="py-6 text-center text-gray-400">
                  No transactions yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      )}
    </section>
  );
}
