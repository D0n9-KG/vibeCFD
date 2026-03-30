// src/components/workspace/submarine-convergence-chart.tsx
"use client";

interface SubmarineConvergenceChartProps {
  /** Array of Cd values; index 0 = first iteration */
  values: number[];
  /** Width of the SVG (CSS, default "100%") */
  width?: string | number;
  /** Height of the SVG in px (default 56) */
  height?: number;
  /** Index at which convergence was detected (-1 = none) */
  convergenceIndex?: number;
}

const VIEW_W = 300;
const VIEW_H = 56;
const PAD_TOP = 4;
const PAD_BTM = 6;
const PLOT_H = VIEW_H - PAD_TOP - PAD_BTM;

function normalize(values: number[]): number[] {
  if (values.length === 0) return [];
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min;
  if (range === 0) return values.map(() => 0.5);
  return values.map((v) => (v - min) / range);
}

export function SubmarineConvergenceChart({
  values,
  width = "100%",
  height = 56,
  convergenceIndex = -1,
}: SubmarineConvergenceChartProps) {
  if (values.length < 2) {
    return (
      <div
        className="flex items-center justify-center text-[10px] text-stone-400"
        style={{ height }}
      >
        暂无收敛数据
      </div>
    );
  }

  const norm = normalize(values);
  const n = norm.length;

  // Build polyline points (inverted Y so high value = tall)
  const points = norm
    .map((v, i) => {
      const x = (i / (n - 1)) * VIEW_W;
      const y = PAD_TOP + (1 - v) * PLOT_H;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");

  // Area path: polyline + bottom-right + bottom-left
  const areaPoints = `${points} ${VIEW_W},${VIEW_H - PAD_BTM} 0,${VIEW_H - PAD_BTM}`;

  // Convergence marker
  const convX =
    convergenceIndex >= 0 && convergenceIndex < n
      ? ((convergenceIndex / (n - 1)) * VIEW_W).toFixed(1)
      : null;

  return (
    <svg
      viewBox={`0 0 ${VIEW_W} ${VIEW_H}`}
      style={{ width, height, display: "block" }}
      aria-hidden
    >
      {/* Area fill */}
      <polygon
        points={areaPoints}
        fill="rgba(59,130,246,0.07)"
        stroke="none"
      />
      {/* Line */}
      <polyline
        points={points}
        fill="none"
        stroke="#3b82f6"
        strokeWidth="1.8"
        strokeLinejoin="round"
      />
      {/* Baseline */}
      <line
        x1={0}
        y1={VIEW_H - PAD_BTM}
        x2={VIEW_W}
        y2={VIEW_H - PAD_BTM}
        stroke="#e7e5e4"
        strokeWidth="0.5"
      />
      {/* Convergence marker */}
      {convX != null && (
        <>
          <line
            x1={convX}
            y1={0}
            x2={convX}
            y2={VIEW_H - PAD_BTM}
            stroke="#22c55e"
            strokeWidth="0.8"
            strokeDasharray="3,3"
          />
          <text
            x={Number(convX) + 3}
            y={10}
            fill="#22c55e"
            fontSize={7}
            fontFamily="sans-serif"
          >
            收敛
          </text>
        </>
      )}
    </svg>
  );
}
