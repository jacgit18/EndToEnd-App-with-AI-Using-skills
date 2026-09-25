import { useMutation, useQuery } from "@tanstack/react-query";
import { Link, Navigate, Route, Routes } from "react-router-dom";

import { api } from "./api/client";
import AccountsPage from "./AccountsPage";
import CategoriesPage from "./CategoriesPage";
import LoginPage from "./LoginPage";
import Transactions from "./Transactions";

// /login is the only public page. Everything else is the dashboard, and it
// isn't gated here: the API is what enforces auth (every /api call but login
// returns 401 without a session), and api/client.ts turns any 401 into a
// redirect to /login. Gating in the UI would be cosmetic — the server is the
// boundary (ADR-0010).
export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/" element={<Dashboard />} />
      <Route path="/accounts" element={<AccountsPage />} />
      <Route path="/categories" element={<CategoriesPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

// Phase 0's actual proof: this component is the first thing that exercises
// the whole chain end to end — browser -> Vite proxy -> FastAPI -> Postgres
// (spec.md's "controlled-experiment slice"). TanStack Query owns the
// fetch/loading/error/refetch state (ADR-0009) — no useState/useEffect here.
function Dashboard() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["health"],
    queryFn: api.health,
    refetchInterval: 10_000, // keep the badge honest without a manual reload
  });

  // The server deletes the session row; the full-page redirect then drops the
  // query cache so no account data stays in memory after sign-out.
  const logout = useMutation({
    mutationFn: api.logout,
    onSuccess: () => window.location.assign("/login"),
  });

  const status =
    isLoading ? "checking…" : isError || data?.db !== "connected" ? "unreachable" : "connected";

  return (
    <main style={{ fontFamily: "system-ui, sans-serif", padding: "2rem" }}>
      <h1>Finance Dashboard</h1>
      <button onClick={() => logout.mutate()} disabled={logout.isPending}>
        Sign out
      </button>
      <nav style={{ margin: "0.5rem 0" }}>
        <Link to="/">Transactions</Link> · <Link to="/accounts">Accounts</Link> ·{" "}
        <Link to="/categories">Categories</Link>
      </nav>
      <p>
        Backend:{" "}
        <strong style={{ color: status === "connected" ? "seagreen" : "crimson" }}>
          {status}
        </strong>
      </p>
      <Transactions />
    </main>
  );
}
