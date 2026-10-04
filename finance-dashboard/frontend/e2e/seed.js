// Seed data for the E2E suite and tools/screenshots.mjs. It is made up: no real
// account, payee or amount. The browser never reaches the real backend in these runs;
// e2e/mock-api.js serves this data from inside the page (see that file for why).
//
// The clock is frozen at FROZEN_NOW (fixtures.js), so "this month" is 2026-10 and the
// six-month trend runs 2026-05 to 2026-10. October totals, which specs assert on:
//   income 3200.00, expense 1695.34 (1675.35 categorized + 19.99 uncategorized), net 1504.66

// Thursday mid-month, noon in the suite's timezone (playwright.config.js timezoneId).
// Noon keeps the UTC date and the local date the same day.
export const FROZEN_NOW = new Date("2026-10-15T12:00:00-04:00");
export const MONTH = "2026-10";

export const CREDENTIALS = { email: "owner@example.com", password: "correct-horse-battery" };

const CREATED = "2026-05-01T09:00:00Z";

export function buildSeed() {
  const accounts = [
    { id: 1, name: "Checking", type: "checking", starting_balance: "2500.00" },
    { id: 2, name: "Credit card", type: "credit_card", starting_balance: "0.00" },
    { id: 3, name: "Savings", type: "savings", starting_balance: "10000.00" },
    { id: 4, name: "Old wallet", type: "cash", starting_balance: "40.00", is_archived: true },
  ].map((a) => ({ is_archived: false, created_at: CREATED, ...a }));

  const categories = [
    { id: 1, name: "Groceries", kind: "expense" },
    { id: 2, name: "Rent", kind: "expense" },
    { id: 3, name: "Dining", kind: "expense" },
    { id: 4, name: "Utilities", kind: "expense" },
    { id: 5, name: "Salary", kind: "income" },
    { id: 6, name: "Gym", kind: "expense", is_archived: true },
  ].map((c) => ({ is_archived: false, created_at: CREATED, ...c }));

  // [date, account_id, category_id, amount, description]
  const rows = [
    ["2026-08-01", 1, 5, "3200.00", "Paycheck"],
    ["2026-08-01", 1, 2, "-1450.00", "August rent"],
    ["2026-08-09", 2, 1, "-190.55", "Corner market"],
    ["2026-08-22", 2, 3, "-120.00", "Birthday dinner"],
    ["2026-09-01", 1, 5, "3200.00", "Paycheck"],
    ["2026-09-01", 1, 2, "-1450.00", "September rent"],
    ["2026-09-10", 2, 1, "-212.30", "Corner market"],
    ["2026-09-12", 1, 4, "-88.10", "Electric bill"],
    ["2026-09-18", 2, 3, "-64.00", "Noodle bar"],
    ["2026-09-20", 2, 3, "-30.00", "Double charge"], // voided below
    ["2026-10-01", 1, 5, "3200.00", "Paycheck"],
    ["2026-10-01", 1, 2, "-1450.00", "October rent"],
    ["2026-10-04", 2, 1, "-86.40", "Corner market"],
    ["2026-10-08", 2, 3, "-42.75", "Noodle bar"],
    ["2026-10-12", 1, 4, "-96.20", "Electric bill"],
    ["2026-10-13", 2, null, "-19.99", "Streaming service"],
  ];
  const transactions = rows.map(([date, account_id, category_id, amount, description], i) => ({
    id: i + 1,
    account_id,
    category_id,
    date,
    amount,
    description,
    type: "normal",
    reverses_transaction_id: null,
    created_at: `${date}T15:00:00Z`,
  }));
  const voided = transactions.find((t) => t.description === "Double charge");
  transactions.push({
    ...voided,
    id: transactions.length + 1,
    amount: "30.00",
    type: "reversal",
    reverses_transaction_id: voided.id,
  });

  // October is missing Dining, so "Copy from last month" copies 1 and skips 2.
  const budgets = [
    ["2026-09", 1, "250.00"],
    ["2026-09", 2, "1450.00"],
    ["2026-09", 3, "100.00"],
    ["2026-10", 1, "250.00"],
    ["2026-10", 2, "1450.00"],
  ].map(([month, category_id, amount], i) => ({ id: i + 1, month, category_id, amount }));

  const imports = [
    {
      id: 1,
      filename: "card-september.csv",
      account_id: 2,
      imported_count: 4,
      skipped_count: 1,
      rejected_count: 0,
      created_at: "2026-10-02T14:30:00Z",
    },
  ];

  // What POST /api/imports/preview returns for any uploaded file.
  const importPreview = {
    headers: ["Date", "Amount", "Description", "Card"],
    rows: [
      ["2026-10-02", "-12.50", "Coffee", "Visa"],
      ["2026-10-03", "-64.10", "Hardware store", "Visa"],
      ["2026-10-05", "-8.00", "Parking", "Amex"],
    ],
    row_count: 3,
    delimiter: ",",
    distinct_values: { Card: ["Amex", "Visa"] },
  };

  return { accounts, categories, transactions, budgets, imports, importPreview };
}
