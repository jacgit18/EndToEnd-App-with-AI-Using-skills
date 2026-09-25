import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { api } from "./api/client";
import { CategoryChart, TrendChart } from "./DashboardCharts";

// Local calendar month as YYYY-MM (toISOString would be UTC and can be a day off).
function currentMonth(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
}

export default function DashboardPage() {
  const [month, setMonth] = useState(currentMonth());

  // <input type="month"> reports "" while it is cleared or half-typed; no month, no query.
  const dashboard = useQuery({
    queryKey: ["dashboard", month],
    queryFn: () => api.dashboard(month),
    enabled: month !== "",
  });
  const trend = useQuery({
    queryKey: ["dashboard-trend", month],
    queryFn: () => api.dashboardTrend(month),
    enabled: month !== "",
  });
  const data = dashboard.data;

  return (
    <section style={{ fontFamily: "system-ui, sans-serif", padding: "2rem" }}>
      <p>
        <Link to="/">← Transactions</Link>
      </p>
      <h2>Dashboard</h2>

      <label>
        Month <input type="month" value={month} onChange={(e) => setMonth(e.target.value)} />
      </label>

      {month === "" ? (
        <p>Pick a month.</p>
      ) : dashboard.isError ? (
        <p role="alert" style={{ color: "crimson" }}>{(dashboard.error as Error).message}</p>
      ) : !data ? (
        <p>Loading…</p>
      ) : (
        <>
          <div style={{ display: "flex", gap: "2rem", margin: "1rem 0" }}>
            <Tile label="Income" value={data.income} />
            <Tile label="Expense" value={data.expense} />
            <Tile label="Net" value={data.net} />
          </div>

          <h3>Spending by category</h3>
          <CategoryChart categories={data.categories} />

          <h3>Net, last six months</h3>
          {trend.isError ? (
            <p role="alert" style={{ color: "crimson" }}>{(trend.error as Error).message}</p>
          ) : trend.data ? (
            <TrendChart points={trend.data.points} />
          ) : (
            <p>Loading…</p>
          )}

          <h3>Recent transactions</h3>
          {data.recent.length === 0 ? (
            <p>No transactions this month.</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th style={{ textAlign: "left" }}>Date</th>
                  <th style={{ textAlign: "left" }}>Description</th>
                  <th style={{ textAlign: "right" }}>Amount</th>
                </tr>
              </thead>
              <tbody>
                {data.recent.map((t) => (
                  <tr key={t.id}>
                    <td>{t.date}</td>
                    <td>{t.description}</td>
                    <td style={{ textAlign: "right" }}>{t.amount}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </>
      )}
    </section>
  );
}

function Tile({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div>{label}</div>
      <strong data-testid={`tile-${label.toLowerCase()}`} style={{ fontSize: "1.5rem" }}>{value}</strong>
    </div>
  );
}
