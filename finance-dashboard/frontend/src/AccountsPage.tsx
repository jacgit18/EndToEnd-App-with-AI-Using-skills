import { useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { ACCOUNT_TYPES, api, type Account, type AccountType, type AccountUpdate } from "./api/client";

// Same shape the backend enforces (app/schemas/_money.py): optional minus, up to 12
// integer digits, up to 2 decimals. Checked here so the user sees the problem next to
// the field before submitting; the backend still re-checks and stays the real guard.
// Deliberately a string test, never parseFloat — money stays a string (ADR-0005).
const MONEY = /^-?\d{1,12}(\.\d{1,2})?$/;

export const TYPE_LABELS: Record<AccountType, string> = {
  checking: "Checking",
  savings: "Savings",
  credit_card: "Credit card",
  cash: "Cash",
};

export function moneyError(value: string): string | null {
  if (value.trim() === "") return null; // blank = default 0.00
  return MONEY.test(value.trim())
    ? null
    : "Use plain digits like 1234.56 (max 2 decimals, negative allowed)";
}

export default function AccountsPage() {
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [type, setType] = useState<AccountType>("checking");
  const [startingBalance, setStartingBalance] = useState("");

  const [showArchived, setShowArchived] = useState(false);

  // Own cache key per view so the archived-inclusive list never replaces the plain
  // ["accounts"] list Transactions.tsx uses for its dropdown. Invalidating the bare
  // ["accounts"] prefix still refreshes every variant.
  const accounts = useQuery({
    queryKey: ["accounts", { includeArchived: showArchived }],
    queryFn: () => api.listAccounts({ includeArchived: showArchived }),
  });

  const createAccount = useMutation({
    mutationFn: api.createAccount,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["accounts"] });
      setName("");
      setType("checking");
      setStartingBalance("");
    },
  });

  const balanceError = moneyError(startingBalance);

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (balanceError) return;
    const start = startingBalance.trim();
    createAccount.mutate({
      name: name.trim(),
      type,
      ...(start ? { starting_balance: start } : {}),
    });
  }

  return (
    <section style={{ fontFamily: "system-ui, sans-serif", padding: "2rem" }}>
      <p>
        <Link to="/">← Transactions</Link>
      </p>
      <h2>Accounts</h2>

      <form onSubmit={handleSubmit} style={{ display: "flex", gap: "0.5rem", marginBottom: "0.5rem" }}>
        <label>
          Name <input required value={name} onChange={(e) => setName(e.target.value)} />
        </label>
        <label>
          Type{" "}
          <select value={type} onChange={(e) => setType(e.target.value as AccountType)}>
            {ACCOUNT_TYPES.map((t) => (
              <option key={t} value={t}>
                {TYPE_LABELS[t]}
              </option>
            ))}
          </select>
        </label>
        <label>
          Starting balance{" "}
          <input
            type="text"
            inputMode="decimal"
            placeholder="0.00"
            value={startingBalance}
            aria-invalid={balanceError !== null}
            onChange={(e) => setStartingBalance(e.target.value)}
          />
        </label>
        <button type="submit" disabled={createAccount.isPending || balanceError !== null}>
          Add account
        </button>
      </form>

      {balanceError && <p role="alert" style={{ color: "crimson" }}>{balanceError}</p>}
      {createAccount.isError && (
        <p role="alert" style={{ color: "crimson" }}>{(createAccount.error as Error).message}</p>
      )}

      <label style={{ display: "block", margin: "0.5rem 0" }}>
        <input
          type="checkbox"
          checked={showArchived}
          onChange={(e) => setShowArchived(e.target.checked)}
        />{" "}
        Show archived
      </label>

      <table>
        <thead>
          <tr>
            <th style={{ textAlign: "left" }}>Name</th>
            <th style={{ textAlign: "left" }}>Type</th>
            <th style={{ textAlign: "right" }}>Starting balance</th>
            <th style={{ textAlign: "right" }}>Balance</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {accounts.data?.map((a) => (
            <AccountRow key={a.id} account={a} />
          ))}
        </tbody>
      </table>
    </section>
  );
}

function AccountRow({ account: a }: { account: Account }) {
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState(a.name);
  const [type, setType] = useState<AccountType>(a.type);
  const [start, setStart] = useState(a.starting_balance);

  const update = useMutation({
    mutationFn: (body: AccountUpdate) => api.updateAccount(a.id, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["accounts"] });
      setEditing(false);
    },
  });

  const startError = moneyError(start) ?? (start.trim() === "" ? "Required" : null);

  function startEditing() {
    setName(a.name);
    setType(a.type);
    setStart(a.starting_balance);
    update.reset();
    setEditing(true);
  }

  function save() {
    // PATCH only what changed; the backend rejects an empty body, so no-op = just close.
    const body: AccountUpdate = {};
    if (name.trim() !== a.name) body.name = name.trim();
    if (type !== a.type) body.type = type;
    // Compare as numbers-in-strings would mislead ("5" vs "5.00"), so send whenever the
    // text differs from what the server returned; the server normalizes to 2dp.
    if (start.trim() !== a.starting_balance) body.starting_balance = start.trim();
    if (Object.keys(body).length === 0) return setEditing(false);
    update.mutate(body);
  }

  const muted = a.is_archived ? { opacity: 0.55 } : undefined;

  if (!editing) {
    return (
      <tr style={muted}>
        <td>
          {a.name}
          {a.is_archived && " (archived)"}
        </td>
        <td>{TYPE_LABELS[a.type]}</td>
        <td style={{ textAlign: "right" }}>{a.starting_balance}</td>
        <td style={{ textAlign: "right" }}>{a.balance}</td>
        <td>
          <button onClick={startEditing}>Edit</button>{" "}
          <button
            onClick={() => update.mutate({ is_archived: !a.is_archived })}
            disabled={update.isPending}
          >
            {a.is_archived ? "Unarchive" : "Archive"}
          </button>
          {update.isError && (
            <span role="alert" style={{ color: "crimson" }}> {(update.error as Error).message}</span>
          )}
        </td>
      </tr>
    );
  }

  return (
    <tr>
      <td>
        <input aria-label="Name" value={name} onChange={(e) => setName(e.target.value)} />
      </td>
      <td>
        <select aria-label="Type" value={type} onChange={(e) => setType(e.target.value as AccountType)}>
          {ACCOUNT_TYPES.map((t) => (
            <option key={t} value={t}>
              {TYPE_LABELS[t]}
            </option>
          ))}
        </select>
      </td>
      <td style={{ textAlign: "right" }}>
        <input
          aria-label="Starting balance"
          inputMode="decimal"
          value={start}
          aria-invalid={startError !== null}
          onChange={(e) => setStart(e.target.value)}
        />
      </td>
      <td style={{ textAlign: "right" }}>{a.balance}</td>
      <td>
        <button onClick={save} disabled={update.isPending || startError !== null || name.trim() === ""}>
          Save
        </button>{" "}
        <button onClick={() => setEditing(false)}>Cancel</button>
        {startError && <span role="alert" style={{ color: "crimson" }}> {startError}</span>}
        {update.isError && (
          <span role="alert" style={{ color: "crimson" }}> {(update.error as Error).message}</span>
        )}
      </td>
    </tr>
  );
}
