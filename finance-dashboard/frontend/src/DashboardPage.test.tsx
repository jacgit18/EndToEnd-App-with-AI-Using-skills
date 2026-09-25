import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import DashboardPage from "./DashboardPage";
import { ApiError, type Dashboard, type Transaction } from "./api/client";

const dashboard = vi.fn();
vi.mock("./api/client", async (importOriginal) => ({
  ...(await importOriginal<typeof import("./api/client")>()),
  api: { dashboard: (...a: unknown[]) => dashboard(...a) },
}));

const tx = (over: Partial<Transaction> = {}): Transaction => ({
  id: 1,
  account_id: 1,
  category_id: 1,
  date: "2026-09-10",
  amount: "-40.00",
  description: "Corner shop",
  type: "manual",
  reverses_transaction_id: null,
  created_at: "2026-09-10T00:00:00Z",
  ...over,
});
const data = (over: Partial<Dashboard> = {}): Dashboard => ({
  month: "2026-09",
  income: "1000.00",
  expense: "50.50",
  net: "949.50",
  categories: [],
  recent: [tx()],
  ...over,
});

function renderPage() {
  render(
    <QueryClientProvider
      client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}
    >
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  // Local time on purpose: the page defaults to the local month.
  vi.useFakeTimers({ toFake: ["Date"], now: new Date(2026, 8, 15, 12) });
  dashboard.mockReset().mockResolvedValue(data());
});
afterEach(() => vi.useRealTimers());

describe("DashboardPage", () => {
  it("defaults to the current local month and asks the API for it", async () => {
    renderPage();
    await screen.findByTestId("tile-net");
    expect(screen.getByLabelText("Month")).toHaveValue("2026-09");
    expect(dashboard).toHaveBeenCalledWith("2026-09");
  });

  it("shows income, expense and net exactly as the API sent them", async () => {
    renderPage();
    expect(await screen.findByTestId("tile-income")).toHaveTextContent("1000.00");
    expect(screen.getByTestId("tile-expense")).toHaveTextContent("50.50");
    expect(screen.getByTestId("tile-net")).toHaveTextContent("949.50");
  });

  it("lists the recent transactions", async () => {
    dashboard.mockResolvedValue(
      data({ recent: [tx(), tx({ id: 2, description: "Refund", amount: "15.00", date: "2026-09-11" })] }),
    );
    renderPage();
    expect(await screen.findByText("Corner shop")).toBeInTheDocument();
    expect(screen.getByText("Refund")).toBeInTheDocument();
    expect(screen.getByText("15.00")).toBeInTheDocument();
  });

  it("says so when the month has no transactions", async () => {
    dashboard.mockResolvedValue(data({ income: "0.00", expense: "0.00", net: "0.00", recent: [] }));
    renderPage();
    expect(await screen.findByText("No transactions this month.")).toBeInTheDocument();
    expect(screen.getByTestId("tile-net")).toHaveTextContent("0.00");
  });

  it("refetches when the month changes", async () => {
    renderPage();
    await screen.findByTestId("tile-net");
    dashboard.mockResolvedValue(data({ month: "2026-08", net: "-5.00" }));
    fireEvent.change(screen.getByLabelText("Month"), { target: { value: "2026-08" } });
    await waitFor(() => expect(dashboard).toHaveBeenCalledWith("2026-08"));
    await waitFor(() => expect(screen.getByTestId("tile-net")).toHaveTextContent("-5.00"));
  });

  it("makes no request while the month is cleared", async () => {
    renderPage();
    await screen.findByTestId("tile-net");
    dashboard.mockClear();
    fireEvent.change(screen.getByLabelText("Month"), { target: { value: "" } });
    expect(await screen.findByText("Pick a month.")).toBeInTheDocument();
    expect(dashboard).not.toHaveBeenCalled();
  });

  it("shows the error when the request fails", async () => {
    dashboard.mockRejectedValue(new ApiError(500, "boom"));
    renderPage();
    expect(await screen.findByRole("alert")).toHaveTextContent("boom");
  });
});
