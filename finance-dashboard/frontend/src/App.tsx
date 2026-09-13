import { useQuery } from "@tanstack/react-query";

import { api } from "./api/client";
import Transactions from "./Transactions";

// Phase 0's actual proof: this component is the first thing that exercises
// the whole chain end to end — browser -> Vite proxy -> FastAPI -> Postgres
// (spec.md's "controlled-experiment slice"). TanStack Query owns the
// fetch/loading/error/refetch state (ADR-0009) — no useState/useEffect here.
export default function App() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["health"],
    queryFn: api.health,
    refetchInterval: 10_000, // keep the badge honest without a manual reload
  });

  const status =
    isLoading ? "checking…" : isError || data?.db !== "connected" ? "unreachable" : "connected";

  return (
    <main style={{ fontFamily: "system-ui, sans-serif", padding: "2rem" }}>
      <h1>Finance Dashboard</h1>
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
