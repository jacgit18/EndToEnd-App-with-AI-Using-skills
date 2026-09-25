import { useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { api, type Budget, type Category } from "./api/client";

// Local calendar month as YYYY-MM (toISOString would be UTC and can be a day off).
function currentMonth(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
}

export default function BudgetsPage() {
  const queryClient = useQueryClient();
  const [month, setMonth] = useState(currentMonth());

  // <input type="month"> reports "" while it is cleared or half-typed; no month, no queries.
  const categories = useQuery({ queryKey: ["categories", { includeArchived: false }], queryFn: () => api.listCategories() });
  const budgets = useQuery({
    queryKey: ["budgets", month],
    queryFn: () => api.listBudgets(month),
    enabled: month !== "",
  });

  const copyForward = useMutation({
    mutationFn: () => api.copyBudgetsForward(month),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["budgets", month] }),
  });

  // Budgets are spending plans, so only expense categories get a line (archived are
  // already hidden by the list default, and the API refuses them anyway).
  const expense = (categories.data ?? []).filter((c) => c.kind === "expense");
  const byCategory = new Map<number, Budget>((budgets.data ?? []).map((b) => [b.category_id, b]));

  function handleCopy(e: FormEvent) {
    e.preventDefault();
    copyForward.mutate();
  }

  return (
    <section style={{ fontFamily: "system-ui, sans-serif", padding: "2rem" }}>
      <p>
        <Link to="/">← Transactions</Link>
      </p>
      <h2>Budgets</h2>

      <form onSubmit={handleCopy} style={{ display: "flex", gap: "0.5rem", marginBottom: "0.5rem" }}>
        <label>
          Month <input type="month" value={month} onChange={(e) => setMonth(e.target.value)} />
        </label>
        <button type="submit" disabled={month === "" || copyForward.isPending}>
          Copy from last month
        </button>
      </form>

      {copyForward.isError && (
        <p role="alert" style={{ color: "crimson" }}>{(copyForward.error as Error).message}</p>
      )}
      {copyForward.isSuccess && (
        <p role="status">
          Copied {copyForward.data.copied} line(s); {copyForward.data.skipped} not copied (already set or archived).
        </p>
      )}

      {month === "" ? (
        <p>Pick a month.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th style={{ textAlign: "left" }}>Category</th>
              <th style={{ textAlign: "left" }}>Budget</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {expense.map((c) => {
              const budget = byCategory.get(c.id);
              // Keyed on the saved amount so the input resets to the server's value when
              // the month changes or a copy-forward fills the line.
              return <BudgetRow key={`${month}:${c.id}:${budget?.amount ?? ""}`} month={month} category={c} budget={budget} />;
            })}
          </tbody>
        </table>
      )}
    </section>
  );
}

function BudgetRow({ month, category: c, budget }: { month: string; category: Category; budget?: Budget }) {
  const queryClient = useQueryClient();
  const [amount, setAmount] = useState(budget?.amount ?? "");

  const refresh = () => queryClient.invalidateQueries({ queryKey: ["budgets", month] });
  const save = useMutation({
    mutationFn: () => api.setBudget(month, c.id, amount.trim()),
    onSuccess: refresh,
  });
  const clear = useMutation({
    mutationFn: () => api.clearBudget(month, c.id),
    onSuccess: refresh,
  });

  const error = save.isError ? save.error : clear.isError ? clear.error : null;
  const busy = save.isPending || clear.isPending;

  return (
    <tr>
      <td>{c.name}</td>
      <td>
        <input
          aria-label={`Budget for ${c.name}`}
          inputMode="decimal"
          placeholder="none"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
        />
      </td>
      <td>
        <button onClick={() => save.mutate()} disabled={busy || amount.trim() === "" || amount.trim() === budget?.amount}>
          Save
        </button>{" "}
        <button onClick={() => clear.mutate()} disabled={busy || budget === undefined}>
          Clear
        </button>
        {error && <span role="alert" style={{ color: "crimson" }}> {(error as Error).message}</span>}
      </td>
    </tr>
  );
}
