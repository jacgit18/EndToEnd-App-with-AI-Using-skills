// An in-memory stand-in for the FastAPI backend, served from inside the browser with
// page.route(). It plays the part localStorage seeding plays in an offline app: every
// test starts from the same known state, with no Postgres, no login secret and no
// real data anywhere near a screenshot.
//
// It keeps the contract the frontend relies on, so the specs still exercise it:
// money travels as 2-decimal strings (ADR-0005); every /api call but login needs a
// session (401 otherwise, which client.ts turns into a redirect); writes need the
// X-CSRF-Token from login or /auth/me (403 otherwise, ADR-0010); dashboard totals
// follow backend/app/routers/dashboard.py. It is NOT the backend: the backend's own
// behaviour is covered by its pytest suite against real Postgres.
//
// Real-stack coverage (browser -> Caddy -> FastAPI -> Postgres) is not in this suite.

import { CREDENTIALS, buildSeed } from "./seed.js";

const CSRF = "e2e-csrf-token";
const MONEY = /^-?\d+(\.\d{1,2})?$/;

const cents = (s) => Math.round(Number(s) * 100);
const money = (c) => (c / 100).toFixed(2);
const inMonth = (date, month) => date.startsWith(`${month}-`);

function shiftMonth(month, by) {
  const [y, m] = month.split("-").map(Number);
  const i = y * 12 + (m - 1) + by;
  return `${String(Math.floor(i / 12)).padStart(4, "0")}-${String((i % 12) + 1).padStart(2, "0")}`;
}

export function createMockApi({ signedIn = true, seed = buildSeed() } = {}) {
  const db = structuredClone(seed);
  const session = { signedIn };
  const overrides = [];
  const nextId = (rows) => Math.max(0, ...rows.map((r) => r.id)) + 1;

  const withBalance = (a) => ({
    ...a,
    balance: money(
      db.transactions
        .filter((t) => t.account_id === a.id)
        .reduce((sum, t) => sum + cents(t.amount), cents(a.starting_balance)),
    ),
  });

  function dashboard(month) {
    const rows = db.transactions.filter((t) => inMonth(t.date, month));
    const kindOf = (t) => db.categories.find((c) => c.id === t.category_id)?.kind ?? null;
    const sum = (list) => list.reduce((s, t) => s + cents(t.amount), 0);
    const income = sum(rows.filter((t) => kindOf(t) === "income"));
    const expense = -sum(rows.filter((t) => kindOf(t) === "expense"));
    const uncategorized = sum(rows.filter((t) => kindOf(t) === null));
    const incomeTotal = income + Math.max(uncategorized, 0);
    const expenseTotal = expense + Math.max(-uncategorized, 0);

    const categories = db.categories
      .filter((c) => c.kind === "expense")
      .map((c) => {
        const actual = -sum(rows.filter((t) => t.category_id === c.id));
        const budget = db.budgets.find((b) => b.category_id === c.id && b.month === month);
        return { category_id: c.id, name: c.name, actual, budget: budget?.amount ?? null };
      })
      .filter((c) => c.budget !== null || c.actual !== 0)
      .sort((a, b) => b.actual - a.actual || a.category_id - b.category_id)
      .map((c) => ({ ...c, actual: money(c.actual) }));
    if (uncategorized < 0) {
      categories.push({ category_id: null, name: "Uncategorized", actual: money(-uncategorized), budget: null });
    }

    const recent = [...rows].sort((a, b) => b.date.localeCompare(a.date) || b.id - a.id).slice(0, 10);
    return {
      month,
      income: money(incomeTotal),
      expense: money(expenseTotal),
      net: money(incomeTotal - expenseTotal),
      categories,
      recent,
    };
  }

  // Each handler returns [status, body]; body undefined = empty response.
  const routes = [
    ["POST", /^\/auth\/login$/, ({ body }) => {
      if (body.email !== CREDENTIALS.email || body.password !== CREDENTIALS.password) {
        return [401, { detail: "Invalid email or password" }];
      }
      session.signedIn = true;
      return [200, { csrf_token: CSRF }];
    }],
    ["GET", /^\/auth\/me$/, () => [200, { csrf_token: CSRF }]],
    ["POST", /^\/auth\/logout$/, () => {
      session.signedIn = false;
      return [204];
    }],

    ["GET", /^\/accounts$/, ({ query }) => [200, db.accounts
      .filter((a) => query.get("include_archived") === "true" || !a.is_archived)
      .sort((a, b) => a.name.localeCompare(b.name))
      .map(withBalance)]],
    ["POST", /^\/accounts$/, ({ body }) => {
      const start = body.starting_balance ?? "0.00";
      if (!MONEY.test(start)) return [422, { detail: "starting_balance must be a money amount" }];
      const a = { id: nextId(db.accounts), name: body.name, type: body.type,
        starting_balance: money(cents(start)), is_archived: false, created_at: new Date().toISOString() };
      db.accounts.push(a);
      return [201, withBalance(a)];
    }],
    ["PATCH", /^\/accounts\/(\d+)$/, ({ body, params: [id] }) => {
      const a = db.accounts.find((x) => x.id === Number(id));
      if (!a) return [404, { detail: "Account not found" }];
      Object.assign(a, body);
      return [200, withBalance(a)];
    }],

    ["GET", /^\/categories$/, ({ query }) => [200, db.categories
      .filter((c) => query.get("include_archived") === "true" || !c.is_archived)
      .sort((a, b) => a.kind.localeCompare(b.kind) || a.name.localeCompare(b.name))]],
    ["POST", /^\/categories$/, ({ body }) => {
      if (db.categories.some((c) => c.name.toLowerCase() === body.name.toLowerCase())) {
        return [409, { detail: "A category with that name already exists" }];
      }
      const c = { id: nextId(db.categories), name: body.name, kind: body.kind, is_archived: false,
        created_at: new Date().toISOString() };
      db.categories.push(c);
      return [201, c];
    }],
    ["PATCH", /^\/categories\/(\d+)$/, ({ body, params: [id] }) => {
      const c = db.categories.find((x) => x.id === Number(id));
      if (!c) return [404, { detail: "Category not found" }];
      Object.assign(c, body);
      return [200, c];
    }],

    ["GET", /^\/budgets$/, ({ query }) => [200, db.budgets.filter((b) => b.month === query.get("month"))]],
    ["POST", /^\/budgets\/(\d{4}-\d{2})\/copy-forward$/, ({ params: [month] }) => {
      let copied = 0;
      let skipped = 0;
      for (const prev of db.budgets.filter((b) => b.month === shiftMonth(month, -1))) {
        const category = db.categories.find((c) => c.id === prev.category_id);
        const taken = db.budgets.some((b) => b.month === month && b.category_id === prev.category_id);
        if (taken || category.is_archived) skipped++;
        else {
          db.budgets.push({ ...prev, id: nextId(db.budgets), month });
          copied++;
        }
      }
      return [200, { copied, skipped }];
    }],
    ["PUT", /^\/budgets\/(\d{4}-\d{2})\/(\d+)$/, ({ body, params: [month, cid] }) => {
      if (!MONEY.test(body.amount) || cents(body.amount) < 0) return [422, { detail: "amount must be a non-negative money amount" }];
      const existing = db.budgets.find((b) => b.month === month && b.category_id === Number(cid));
      const b = existing ?? { id: nextId(db.budgets), month, category_id: Number(cid) };
      b.amount = money(cents(body.amount));
      if (!existing) db.budgets.push(b);
      return [200, b];
    }],
    ["DELETE", /^\/budgets\/(\d{4}-\d{2})\/(\d+)$/, ({ params: [month, cid] }) => {
      const i = db.budgets.findIndex((b) => b.month === month && b.category_id === Number(cid));
      if (i === -1) return [404, { detail: "No budget for that month" }];
      db.budgets.splice(i, 1);
      return [204];
    }],

    ["GET", /^\/transactions$/, ({ query }) => {
      const month = query.get("month");
      const account = Number(query.get("account_id"));
      return [200, db.transactions
        .filter((t) => (!month || inMonth(t.date, month)) && (!account || t.account_id === account))
        .sort((a, b) => b.date.localeCompare(a.date) || b.id - a.id)];
    }],
    ["POST", /^\/transactions$/, ({ body }) => {
      if (!MONEY.test(body.amount)) return [422, { detail: "amount must be a money amount like -12.34" }];
      const t = { id: nextId(db.transactions), account_id: body.account_id, category_id: body.category_id ?? null,
        date: body.date, amount: money(cents(body.amount)), description: body.description, type: "normal",
        reverses_transaction_id: null, created_at: new Date().toISOString() };
      db.transactions.push(t);
      return [201, t];
    }],
    ["POST", /^\/transactions\/(\d+)\/void$/, ({ params: [id] }) => {
      const original = db.transactions.find((t) => t.id === Number(id));
      if (!original) return [404, { detail: "Transaction not found" }];
      if (db.transactions.some((t) => t.reverses_transaction_id === original.id)) {
        return [409, { detail: "Transaction is already voided" }];
      }
      const reversal = { ...original, id: nextId(db.transactions), amount: money(-cents(original.amount)),
        type: "reversal", reverses_transaction_id: original.id, created_at: new Date().toISOString() };
      db.transactions.push(reversal);
      return [201, reversal];
    }],

    ["GET", /^\/dashboard$/, ({ query }) => [200, dashboard(query.get("month"))]],
    ["GET", /^\/dashboard\/trend$/, ({ query }) => {
      const month = query.get("month");
      const points = [-5, -4, -3, -2, -1, 0].map((by) => shiftMonth(month, by)).map((m) => ({
        month: m,
        net: money(db.transactions.filter((t) => inMonth(t.date, m)).reduce((s, t) => s + cents(t.amount), 0)),
      }));
      return [200, { month, points }];
    }],

    ["GET", /^\/imports$/, () => [200, db.imports]],
    ["POST", /^\/imports\/preview$/, () => [200, db.importPreview]],
    ["POST", /^\/imports$/, () => [201, { batch_id: nextId(db.imports), imported_count: 2, skipped_count: 0,
      rejected_count: 1, excluded_count: 0, rejected: [{ line: 4, reason: "amount is not a number" }],
      batches: [{ batch_id: nextId(db.imports), account_id: 1, imported_count: 2, skipped_count: 0, rejected_count: 1 }] }]],
  ];

  async function handle(route) {
    const request = route.request();
    const url = new URL(request.url());
    const method = request.method();
    const path = url.pathname.replace(/^\/api/, "");
    const reply = (status, body) =>
      route.fulfill({ status, contentType: "application/json", body: body === undefined ? "" : JSON.stringify(body) });

    const forced = overrides.find((o) => o.method === method && o.path.test(path));
    if (forced) return reply(forced.status, forced.body);

    if (path !== "/auth/login" && !session.signedIn) return reply(401, { detail: "Not authenticated" });
    if (method !== "GET" && path !== "/auth/login" && request.headers()["x-csrf-token"] !== CSRF) {
      return reply(403, { detail: "CSRF token missing or invalid" });
    }

    for (const [m, pattern, handler] of routes) {
      const match = m === method && path.match(pattern);
      if (!match) continue;
      const isJson = (request.headers()["content-type"] ?? "").includes("application/json");
      const body = isJson ? request.postDataJSON() : {};
      const [status, payload] = handler({ body, query: url.searchParams, params: match.slice(1) });
      return reply(status, payload);
    }
    return reply(404, { detail: `No mock for ${method} ${path}` });
  }

  return {
    db,
    session,
    // Force one endpoint to answer with an error (or anything else) for the rest of the test.
    override(method, path, status, body) {
      overrides.unshift({ method, path, status, body });
    },
    // Works on a Page or a BrowserContext (screenshots.mjs uses a context).
    async install(target) {
      await target.route("**/api/**", handle);
      await target.route("**/health", (route) =>
        route.fulfill({ json: session.backendDown ? { status: "error", db: "unreachable" } : { status: "ok", db: "connected" } }),
      );
    },
  };
}
