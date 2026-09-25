import { AxisBottom, AxisLeft } from "@visx/axis";
import { Group } from "@visx/group";
import { scaleBand, scaleLinear } from "@visx/scale";
import { Bar } from "@visx/shape";

import type { DashboardCategory, TrendPoint } from "./api/client";

// Money travels as strings and is never added or compared for display. Number() is used
// below only to place and colour marks; every value a reader needs is printed as the
// API's own string in the table under each chart.

const WIDTH = 640;
const MARGIN = { top: 8, right: 16, bottom: 28, left: 140 };
const ROW = 28;

export function CategoryChart({ categories }: { categories: DashboardCategory[] }) {
  if (categories.length === 0) return <p>No spending or budgets this month.</p>;

  const height = MARGIN.top + MARGIN.bottom + ROW * categories.length;
  const innerW = WIDTH - MARGIN.left - MARGIN.right;
  const max = Math.max(1, ...categories.flatMap((c) => [Number(c.actual), Number(c.budget ?? 0)]));
  const x = scaleLinear({ domain: [0, max], range: [0, innerW], nice: true });
  const y = scaleBand({
    domain: categories.map((_, i) => String(i)),
    range: [0, ROW * categories.length],
    padding: 0.3,
  });

  return (
    <div>
      <svg
        role="img"
        aria-label="Spending by category against budget"
        viewBox={`0 0 ${WIDTH} ${height}`}
        style={{ width: "100%", maxWidth: WIDTH }}
      >
        <Group left={MARGIN.left} top={MARGIN.top}>
          {categories.map((c, i) => {
            const actual = Number(c.actual);
            const over = c.budget !== null && actual > Number(c.budget);
            const top = y(String(i)) ?? 0;
            return (
              <Group key={c.category_id ?? "uncategorized"}>
                <Bar
                  data-testid="actual-bar"
                  x={0}
                  y={top}
                  width={Math.max(0, x(Math.max(0, actual)))}
                  height={y.bandwidth()}
                  fill={over ? "crimson" : "steelblue"}
                />
                {c.budget !== null && (
                  <line
                    data-testid="budget-mark"
                    x1={x(Number(c.budget))}
                    x2={x(Number(c.budget))}
                    y1={top - 3}
                    y2={top + y.bandwidth() + 3}
                    stroke="black"
                    strokeWidth={2}
                  />
                )}
              </Group>
            );
          })}
          <AxisLeft
            scale={y}
            tickFormat={(i) => categories[Number(i)]?.name ?? ""}
            hideAxisLine
            hideTicks
          />
          <AxisBottom scale={x} top={ROW * categories.length} numTicks={5} />
        </Group>
      </svg>
      <table>
        <thead>
          <tr>
            <th style={{ textAlign: "left" }}>Category</th>
            <th style={{ textAlign: "right" }}>Spent</th>
            <th style={{ textAlign: "right" }}>Budget</th>
          </tr>
        </thead>
        <tbody>
          {categories.map((c) => (
            <tr key={c.category_id ?? "uncategorized"}>
              <td>{c.name}</td>
              <td style={{ textAlign: "right" }}>{c.actual}</td>
              <td style={{ textAlign: "right" }}>{c.budget ?? "no budget"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

const T_HEIGHT = 200;
const T_MARGIN = { top: 12, right: 16, bottom: 28, left: 56 };

export function TrendChart({ points }: { points: TrendPoint[] }) {
  const innerW = WIDTH - T_MARGIN.left - T_MARGIN.right;
  const innerH = T_HEIGHT - T_MARGIN.top - T_MARGIN.bottom;
  const values = points.map((p) => Number(p.net));
  const lo = Math.min(0, ...values);
  const hi = Math.max(0, ...values);
  const x = scaleBand({ domain: points.map((p) => p.month), range: [0, innerW], padding: 0.3 });
  const y = scaleLinear({ domain: [lo, hi === lo ? lo + 1 : hi], range: [innerH, 0], nice: true });

  return (
    <div>
      <svg
        role="img"
        aria-label="Net per month, last six months"
        viewBox={`0 0 ${WIDTH} ${T_HEIGHT}`}
        style={{ width: "100%", maxWidth: WIDTH }}
      >
        <Group left={T_MARGIN.left} top={T_MARGIN.top}>
          {points.map((p) => {
            const v = Number(p.net);
            const barTop = y(Math.max(v, 0));
            return (
              <Bar
                key={p.month}
                data-testid="trend-bar"
                x={x(p.month) ?? 0}
                y={barTop}
                width={x.bandwidth()}
                height={Math.abs(y(v) - y(0))}
                fill={v < 0 ? "crimson" : "seagreen"}
              />
            );
          })}
          <line x1={0} x2={innerW} y1={y(0)} y2={y(0)} stroke="black" />
          <AxisLeft scale={y} numTicks={4} />
          <AxisBottom scale={x} top={innerH} />
        </Group>
      </svg>
      <table>
        <thead>
          <tr>
            <th style={{ textAlign: "left" }}>Month</th>
            <th style={{ textAlign: "right" }}>Net</th>
          </tr>
        </thead>
        <tbody>
          {points.map((p) => (
            <tr key={p.month}>
              <td>{p.month}</td>
              <td style={{ textAlign: "right" }}>{p.net}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
