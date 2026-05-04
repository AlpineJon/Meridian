/**
 * Color scales for choropleth shading. Reds reserved for distress (high = bad);
 * greens reserved for liquidity/demand (high = good); diverging for demand pressure.
 */

export type MetricKey = "liquidityScore" | "demandPressure" | "distressIndicator" | "marketTier";

export const METRIC_LABELS: Record<MetricKey, string> = {
  liquidityScore: "Liquidity score",
  demandPressure: "Demand pressure",
  distressIndicator: "Distress indicator",
  marketTier: "Market tier",
};

const NO_DATA = "#e6e7eb"; // ink-100 (slightly warmer)

// Sequential green scale (low -> high = bad -> good)
const GREEN_SCALE = ["#dcfce7", "#bbf7d0", "#86efac", "#4ade80", "#22c55e", "#16a34a"];
// Sequential red scale (low -> high = good -> bad)
const RED_SCALE = ["#fee2e2", "#fecaca", "#fca5a5", "#f87171", "#ef4444", "#dc2626"];
// Diverging blue/red around 0 (positive = good blue/green, negative = red)
const DIVERGING = ["#b91c1c", "#dc2626", "#fca5a5", "#e5e7eb", "#86efac", "#22c55e", "#15803d"];

/** 0..100 -> color from green scale */
function greenForLiquidity(v: number): string {
  if (v < 25) return GREEN_SCALE[0];
  if (v < 40) return GREEN_SCALE[1];
  if (v < 50) return GREEN_SCALE[2];
  if (v < 60) return GREEN_SCALE[3];
  if (v < 75) return GREEN_SCALE[4];
  return GREEN_SCALE[5];
}

/** 0..100 -> color from red scale (high = bad) */
function redForDistress(v: number): string {
  if (v < 25) return RED_SCALE[0];
  if (v < 40) return RED_SCALE[1];
  if (v < 50) return RED_SCALE[2];
  if (v < 60) return RED_SCALE[3];
  if (v < 75) return RED_SCALE[4];
  return RED_SCALE[5];
}

/** -100..100 -> diverging color */
function divergingForDemand(v: number): string {
  if (v < -15) return DIVERGING[0];
  if (v < -8) return DIVERGING[1];
  if (v < -3) return DIVERGING[2];
  if (v < 3) return DIVERGING[3];
  if (v < 8) return DIVERGING[4];
  if (v < 15) return DIVERGING[5];
  return DIVERGING[6];
}

function colorForTier(t: string): string {
  switch (t) {
    case "A":
      return "#15803d";
    case "B":
      return "#22c55e";
    case "C":
      return "#d97706";
    case "D":
      return "#dc2626";
    default:
      return NO_DATA;
  }
}

export function colorFor(metric: MetricKey, value: number | string | undefined | null): string {
  if (value === undefined || value === null) return NO_DATA;
  if (metric === "marketTier") return colorForTier(value as string);
  const v = value as number;
  if (metric === "liquidityScore") return greenForLiquidity(v);
  if (metric === "demandPressure") return divergingForDemand(v);
  if (metric === "distressIndicator") return redForDistress(v);
  return NO_DATA;
}

export const NO_DATA_COLOR = NO_DATA;

export type LegendStop = { color: string; label: string };

export function legendFor(metric: MetricKey): LegendStop[] {
  if (metric === "liquidityScore")
    return [
      { color: GREEN_SCALE[0], label: "<25" },
      { color: GREEN_SCALE[1], label: "25-39" },
      { color: GREEN_SCALE[2], label: "40-49" },
      { color: GREEN_SCALE[3], label: "50-59" },
      { color: GREEN_SCALE[4], label: "60-74" },
      { color: GREEN_SCALE[5], label: "75+" },
    ];
  if (metric === "distressIndicator")
    return [
      { color: RED_SCALE[0], label: "<25" },
      { color: RED_SCALE[1], label: "25-39" },
      { color: RED_SCALE[2], label: "40-49" },
      { color: RED_SCALE[3], label: "50-59" },
      { color: RED_SCALE[4], label: "60-74" },
      { color: RED_SCALE[5], label: "75+" },
    ];
  if (metric === "demandPressure")
    return [
      { color: DIVERGING[0], label: "<-15" },
      { color: DIVERGING[1], label: "-15..-8" },
      { color: DIVERGING[2], label: "-8..-3" },
      { color: DIVERGING[3], label: "-3..+3" },
      { color: DIVERGING[4], label: "+3..+8" },
      { color: DIVERGING[5], label: "+8..+15" },
      { color: DIVERGING[6], label: "+15+" },
    ];
  return [
    { color: "#15803d", label: "A" },
    { color: "#22c55e", label: "B" },
    { color: "#d97706", label: "C" },
    { color: "#dc2626", label: "D" },
  ];
}
