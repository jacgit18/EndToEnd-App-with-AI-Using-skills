import { useQuery } from "@tanstack/react-query";
import { getHealth } from "./api/client";
import { TransactionsPage } from "./pages/Transactions";

function HealthBadge() {
  const { data, isError, isLoading } = useQuery({
    queryKey: ["health"],
    queryFn: getHealth,
    retry: false,
  });
  const ok = data?.status === "ok" && !isError;
  const label = isLoading ? "checking…" : ok ? "connected" : "unreachable";
  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-sm font-medium ${
        ok ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
      }`}
    >
      <span
        className={`h-2 w-2 rounded-full ${ok ? "bg-green-500" : "bg-red-500"}`}
      />
      API {label}
    </span>
  );
}

export default function App() {
  return (
    <div className="mx-auto max-w-4xl p-6">
      <header className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Finance Dashboard</h1>
        <HealthBadge />
      </header>
      <TransactionsPage />
    </div>
  );
}
