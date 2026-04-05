import assert from "node:assert/strict";
import test from "node:test";

const { buildSparklinePath, buildSubmarineTrendSeries } = await import(
  new URL("./submarine-runtime-panel.trends.ts", import.meta.url).href
);

void test("builds submarine trend series from solver metrics histories", () => {
  const series = buildSubmarineTrendSeries({
    force_coefficients_history: [
      { Time: 0, Cd: 0.18, Cl: 0.01 },
      { Time: 200, Cd: 0.12, Cl: 0.0 },
    ],
    forces_history: [
      { Time: 0, total_force: [12, 0, 0], total_moment: [0, 0.9, 0] },
      { Time: 200, total_force: [8, 0, 0], total_moment: [0, 0.5, 0] },
    ],
  });

  assert.deepEqual(
    series.map((item) => item.id),
    ["cd", "cl", "fx", "my"],
  );
  assert.equal(series[0]?.latestValue, 0.12);
  assert.equal(series[2]?.values.at(0)?.value, 12);
  assert.equal(series[3]?.values.at(-1)?.value, 0.5);
});

void test("builds a stable sparkline path from numeric trend values", () => {
  const path = buildSparklinePath(
    [
      { time: 0, value: 12 },
      { time: 100, value: 10 },
      { time: 200, value: 8 },
    ],
    120,
    40,
  );

  assert.match(path, /^M /);
  assert.match(path, /L/);
});
