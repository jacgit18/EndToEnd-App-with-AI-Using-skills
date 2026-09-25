import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { CategoryChart, TrendChart } from "./DashboardCharts";
import type { DashboardCategory } from "./api/client";

const cat = (over: Partial<DashboardCategory> = {}): DashboardCategory => ({
  category_id: 1,
  name: "Groceries",
  actual: "50.00",
  budget: "200.00",
  ...over,
});

describe("CategoryChart", () => {
  it("says so when there is nothing to chart", () => {
    render(<CategoryChart categories={[]} />);
    expect(screen.getByText("No spending or budgets this month.")).toBeInTheDocument();
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
  });

  it("draws a bar per category and a budget mark only where a budget exists", () => {
    render(<CategoryChart categories={[cat(), cat({ category_id: 2, name: "Rent", budget: null })]} />);
    expect(screen.getAllByTestId("actual-bar")).toHaveLength(2);
    expect(screen.getAllByTestId("budget-mark")).toHaveLength(1);
  });

  it("prints every value as text, and 'no budget' rather than zero", () => {
    render(<CategoryChart categories={[cat({ name: "Rent", actual: "12.34", budget: null })]} />);
    expect(screen.getByRole("cell", { name: "Rent" })).toBeInTheDocument();
    expect(screen.getByRole("cell", { name: "12.34" })).toBeInTheDocument();
    expect(screen.getByRole("cell", { name: "no budget" })).toBeInTheDocument();
  });

  it("colours a bar over its budget differently from one within it", () => {
    render(
      <CategoryChart
        categories={[cat({ actual: "250.00" }), cat({ category_id: 2, name: "Fun", actual: "10.00" })]}
      />,
    );
    const [over, within] = screen.getAllByTestId("actual-bar");
    expect(over.getAttribute("fill")).toBe("crimson");
    expect(within.getAttribute("fill")).toBe("steelblue");
  });

  it("makes the longer spend the longer bar", () => {
    render(
      <CategoryChart
        categories={[cat({ actual: "100.00" }), cat({ category_id: 2, name: "Fun", actual: "25.00" })]}
      />,
    );
    const [a, b] = screen.getAllByTestId("actual-bar");
    expect(Number(a.getAttribute("width"))).toBeGreaterThan(Number(b.getAttribute("width")));
  });
});

const points = [
  { month: "2026-04", net: "100.00" },
  { month: "2026-05", net: "-50.00" },
  { month: "2026-06", net: "0.00" },
];

describe("TrendChart", () => {
  it("draws one bar per month, green above zero and red below", () => {
    render(<TrendChart points={points} />);
    const bars = screen.getAllByTestId("trend-bar");
    expect(bars).toHaveLength(3);
    expect(bars[0].getAttribute("fill")).toBe("seagreen");
    expect(bars[1].getAttribute("fill")).toBe("crimson");
  });

  it("gives an empty month a zero-height bar", () => {
    render(<TrendChart points={points} />);
    expect(Number(screen.getAllByTestId("trend-bar")[2].getAttribute("height"))).toBe(0);
  });

  it("prints every month's net as text, in the order given", () => {
    render(<TrendChart points={points} />);
    const rows = screen.getAllByRole("row").slice(1);
    expect(rows.map((r) => r.textContent)).toEqual(["2026-04100.00", "2026-05-50.00", "2026-060.00"]);
  });

  it("does not break when every month is zero", () => {
    render(<TrendChart points={points.map((p) => ({ ...p, net: "0.00" }))} />);
    expect(screen.getAllByTestId("trend-bar")).toHaveLength(3);
  });
});
