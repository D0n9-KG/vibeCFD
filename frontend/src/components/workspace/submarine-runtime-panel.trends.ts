export type ForceCoefficientHistoryEntry = Record<string, number | null>;

export type ForceHistoryEntry = {
  Time?: number | null;
  total_force?: number[] | null;
  total_moment?: number[] | null;
};

export type SolverMetricsTrendSource = {
  force_coefficients_history?: ForceCoefficientHistoryEntry[] | null;
  forces_history?: ForceHistoryEntry[] | null;
};

export type TrendValue = {
  time: number;
  value: number;
};

export type SubmarineTrendSeries = {
  id: string;
  label: string;
  unit: string;
  values: TrendValue[];
  latestValue: number | null;
};

function isFiniteNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

function buildScalarSeries(
  id: string,
  label: string,
  unit: string,
  history: ForceCoefficientHistoryEntry[] | null | undefined,
  field: string,
): SubmarineTrendSeries | null {
  const values =
    history
      ?.map((entry) => {
        const time = entry.Time;
        const value = entry[field];
        if (!isFiniteNumber(time) || !isFiniteNumber(value)) {
          return null;
        }
        return { time, value };
      })
      .filter((entry): entry is TrendValue => entry != null) ?? [];

  if (values.length === 0) {
    return null;
  }

  return {
    id,
    label,
    unit,
    latestValue: values.at(-1)?.value ?? null,
    values,
  };
}

function buildVectorSeries(
  id: string,
  label: string,
  unit: string,
  history: ForceHistoryEntry[] | null | undefined,
  field: "total_force" | "total_moment",
  axisIndex: number,
): SubmarineTrendSeries | null {
  const values =
    history
      ?.map((entry) => {
        const time = entry.Time;
        const vector = entry[field];
        const value = vector?.[axisIndex];
        if (!isFiniteNumber(time) || !isFiniteNumber(value)) {
          return null;
        }
        return { time, value };
      })
      .filter((entry): entry is TrendValue => entry != null) ?? [];

  if (values.length === 0) {
    return null;
  }

  return {
    id,
    label,
    unit,
    latestValue: values.at(-1)?.value ?? null,
    values,
  };
}

export function buildSubmarineTrendSeries(
  metrics: SolverMetricsTrendSource | null | undefined,
): SubmarineTrendSeries[] {
  if (!metrics) {
    return [];
  }

  return [
    buildScalarSeries(
      "cd",
      "阻力系数 Cd",
      "",
      metrics.force_coefficients_history,
      "Cd",
    ),
    buildScalarSeries(
      "cl",
      "升力系数 Cl",
      "",
      metrics.force_coefficients_history,
      "Cl",
    ),
    buildVectorSeries(
      "fx",
      "总阻力 Fx",
      "N",
      metrics.forces_history,
      "total_force",
      0,
    ),
    buildVectorSeries(
      "my",
      "总俯仰力矩 My",
      "N·m",
      metrics.forces_history,
      "total_moment",
      1,
    ),
  ].filter((series): series is SubmarineTrendSeries => series != null);
}

export function buildSparklinePath(
  values: TrendValue[],
  width: number,
  height: number,
  padding = 6,
): string {
  if (values.length === 0) {
    return "";
  }

  if (values.length === 1) {
    const y = height / 2;
    return `M ${padding} ${y} L ${width - padding} ${y}`;
  }

  const times = values.map((point) => point.time);
  const data = values.map((point) => point.value);
  const minTime = Math.min(...times);
  const maxTime = Math.max(...times);
  const minValue = Math.min(...data);
  const maxValue = Math.max(...data);
  const usableWidth = Math.max(width - padding * 2, 1);
  const usableHeight = Math.max(height - padding * 2, 1);
  const timeSpan = maxTime - minTime || 1;
  const valueSpan = maxValue - minValue || 1;
  const flatLine = maxValue === minValue;

  const points = values.map((point) => {
    const x = padding + ((point.time - minTime) / timeSpan) * usableWidth;
    const normalizedY = flatLine ? 0.5 : (point.value - minValue) / valueSpan;
    const y = padding + (1 - normalizedY) * usableHeight;
    return `${x.toFixed(2)} ${y.toFixed(2)}`;
  });

  return `M ${points[0]} ${points.slice(1).map((point) => `L ${point}`).join(" ")}`;
}
