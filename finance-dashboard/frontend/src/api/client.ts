// Thin fetch wrapper around the backend API. Every call is a relative path
// ("/api/..." or "/health") — never an absolute origin — so it goes through
// the Vite dev proxy (vite.config.ts) and stays same-origin.
//
// Money fields (Account.balance, Transaction.amount) travel the wire as JSON
// *strings*, not numbers — the backend serializes Decimal with str() rather
// than letting the JSON encoder emit a bare number (ADR-0005,
// app/schemas/_money.py). These types keep that contract on this side too:
// treat balance/amount as `string` here, never `number`. Parse them with a
// real decimal library only when you need to format or add them for display
// — never do money arithmetic in JS floats.

export interface Account {
  id: number;
  name: string;
  balance: string;
  is_archived: boolean;
  created_at: string;
}

export interface AccountCreate {
  name: string;
}

export interface Transaction {
  id: number;
  account_id: number;
  category_id: number | null;
  date: string;
  amount: string;
  description: string;
  type: string;
  reverses_transaction_id: number | null;
  created_at: string;
}

export interface TransactionCreate {
  account_id: number;
  category_id?: number | null;
  date: string;
  amount: string;
  description: string;
}

export interface Health {
  status: string;
  db: "connected" | "unreachable";
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    throw new ApiError(res.status, (await res.text()) || res.statusText);
  }
  return res.json() as Promise<T>;
}

export const api = {
  // Not under /api — main.py mounts /health directly on the app, not a router.
  health: (): Promise<Health> => fetch("/health").then((r) => r.json()),

  listAccounts: () => request<Account[]>("/accounts"),
  createAccount: (body: AccountCreate) =>
    request<Account>("/accounts", { method: "POST", body: JSON.stringify(body) }),

  listTransactions: () => request<Transaction[]>("/transactions"),
  createTransaction: (body: TransactionCreate) =>
    request<Transaction>("/transactions", { method: "POST", body: JSON.stringify(body) }),
};
