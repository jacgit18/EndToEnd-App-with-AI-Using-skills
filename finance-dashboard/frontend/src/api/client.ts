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

export const ACCOUNT_TYPES = ["checking", "savings", "credit_card", "cash"] as const;
export type AccountType = (typeof ACCOUNT_TYPES)[number];

export interface Account {
  id: number;
  name: string;
  type: AccountType;
  // Opening balance; editable. `balance` is server-maintained (ADR-0005), never sent.
  starting_balance: string;
  balance: string;
  is_archived: boolean;
  created_at: string;
}

export interface AccountCreate {
  name: string;
  type: AccountType;
  starting_balance?: string; // omitted = "0.00"
}

// PATCH: send only what changes; the server rejects an empty body, nulls and `balance`.
export interface AccountUpdate {
  name?: string;
  type?: AccountType;
  starting_balance?: string;
  is_archived?: boolean;
}

export const CATEGORY_KINDS = ["expense", "income"] as const;
export type CategoryKind = (typeof CATEGORY_KINDS)[number];

export interface Category {
  id: number;
  name: string;
  kind: CategoryKind;
  is_archived: boolean;
  created_at: string;
}

export interface CategoryCreate {
  name: string;
  kind: CategoryKind;
}

// PATCH: rename and/or archive. `kind` is immutable; the server rejects it (422).
export interface CategoryUpdate {
  name?: string;
  is_archived?: boolean;
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

export const DATE_FORMATS = ["iso", "mdy", "dmy"] as const;
export type DateFormat = (typeof DATE_FORMATS)[number];

export interface ImportMapping {
  date_column: string;
  amount_column: string;
  description_column: string;
  date_format: DateFormat; // required, never guessed
  invert_sign: boolean;
  // Multi-account files: which column names the account, and where each of its
  // values goes (account id, or null = leave those rows out). Both or neither.
  account_column?: string;
  account_map?: Record<string, number | null>;
}

export interface ImportPreview {
  headers: string[];
  rows: string[][];
  row_count: number;
  delimiter: string;
  // Columns with few distinct values (<= 50), for the account-column picker.
  distinct_values: Record<string, string[]>;
}

export interface ImportBatchResult {
  batch_id: number;
  account_id: number;
  imported_count: number;
  skipped_count: number;
  rejected_count: number;
}

export interface ImportResult {
  batch_id: number;
  imported_count: number;
  skipped_count: number;
  rejected_count: number;
  excluded_count: number;
  rejected: { line: number; reason: string }[];
  batches: ImportBatchResult[];
}

export interface ImportBatch {
  id: number;
  filename: string;
  account_id: number;
  imported_count: number;
  skipped_count: number;
  rejected_count: number;
  created_at: string;
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

// The CSRF token from the login response (ADR-0010). Held in memory only — not
// localStorage — so page JS on another origin can't lift it; a reload loses it
// until request() re-fetches one from /auth/me before the next write.
let csrfToken: string | null = null;

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const isWrite = init?.method !== undefined && init.method !== "GET";
  if (isWrite && !csrfToken && path !== "/auth/login") {
    // Reloaded page: cookie still valid, token gone. A 401 here redirects to
    // /login like any other call; otherwise we get a fresh token and proceed.
    csrfToken = (await request<{ csrf_token: string }>("/auth/me")).csrf_token;
  }
  // A FormData body (CSV upload) must NOT get a Content-Type: the browser adds
  // multipart/form-data with the boundary itself, and a JSON header would break it.
  const isForm = init?.body instanceof FormData;
  const res = await fetch(`/api${path}`, {
    headers: {
      ...(isForm ? {} : { "Content-Type": "application/json" }),
      ...(isWrite && csrfToken ? { "X-CSRF-Token": csrfToken } : {}),
    },
    ...init,
  });
  if (res.status === 401 && window.location.pathname !== "/login") {
    // Session missing, expired or revoked. client.ts sits outside React, so it
    // can't use the router's navigate(); a full-page redirect also drops every
    // cached query, so nothing from the dead session lingers on screen. Skipped
    // on /login itself, where a 401 just means "wrong email or password" and
    // LoginPage shows that message — redirecting there would wipe it.
    window.location.assign("/login");
  }
  if (!res.ok) {
    throw new ApiError(res.status, (await res.text()) || res.statusText);
  }
  if (res.status === 204) return undefined as T; // e.g. logout: success, no body
  return res.json() as Promise<T>;
}

export const api = {
  // Not under /api — main.py mounts /health directly on the app, not a router.
  health: (): Promise<Health> => fetch("/health").then((r) => r.json()),

  login: async (email: string, password: string) => {
    const { csrf_token } = await request<{ csrf_token: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    csrfToken = csrf_token;
  },

  logout: async () => {
    await request<void>("/auth/logout", { method: "POST" });
    csrfToken = null;
  },

  // Archived accounts are hidden unless asked for (backend default).
  listAccounts: (opts?: { includeArchived?: boolean }) =>
    request<Account[]>(`/accounts${opts?.includeArchived ? "?include_archived=true" : ""}`),
  createAccount: (body: AccountCreate) =>
    request<Account>("/accounts", { method: "POST", body: JSON.stringify(body) }),
  updateAccount: (id: number, body: AccountUpdate) =>
    request<Account>(`/accounts/${id}`, { method: "PATCH", body: JSON.stringify(body) }),

  // Archived categories are hidden unless asked for (backend default).
  listCategories: (opts?: { includeArchived?: boolean }) =>
    request<Category[]>(`/categories${opts?.includeArchived ? "?include_archived=true" : ""}`),
  createCategory: (body: CategoryCreate) =>
    request<Category>("/categories", { method: "POST", body: JSON.stringify(body) }),
  updateCategory: (id: number, body: CategoryUpdate) =>
    request<Category>(`/categories/${id}`, { method: "PATCH", body: JSON.stringify(body) }),

  // month = "YYYY-MM". Both filters optional; the backend ANDs them.
  listTransactions: (opts?: { month?: string; accountId?: number }) => {
    const q = new URLSearchParams();
    if (opts?.month) q.set("month", opts.month);
    if (opts?.accountId) q.set("account_id", String(opts.accountId));
    const qs = q.toString();
    return request<Transaction[]>(`/transactions${qs ? `?${qs}` : ""}`);
  },
  // Append-only ledger: "delete" posts a reversing row; returns that new row.
  voidTransaction: (id: number) =>
    request<Transaction>(`/transactions/${id}/void`, { method: "POST" }),
  createTransaction: (body: TransactionCreate) =>
    request<Transaction>("/transactions", { method: "POST", body: JSON.stringify(body) }),

  previewImport: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<ImportPreview>("/imports/preview", { method: "POST", body: form });
  },
  // Single-account: pass accountId. Multi-account: omit it and set mapping.account_*.
  createImport: (file: File, mapping: ImportMapping, accountId?: number) => {
    const form = new FormData();
    form.append("file", file);
    if (accountId !== undefined) form.append("account_id", String(accountId));
    form.append("mapping", JSON.stringify(mapping));
    return request<ImportResult>("/imports", { method: "POST", body: form });
  },
  listImports: () => request<ImportBatch[]>("/imports"),
};
