"use client";

type Props = {
  values: number[];
  width?: number;
  height?: number;
  /** "good" = up is good, "bad" = up is bad. Drives line color tone. */
  direction?: "good" | "bad" | "neutral";
  className?: string;
};

export function Sparkline({ values, width = 120, height = 32, direction = "neutral", className }: Props) {
  if (values.length < 2) return null;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const stepX = width / (values.length - 1);
  const points = values
    .map((v, i) => {
      const x = i * stepX;
      const y = height - 4 - ((v - min) / range) * (height - 8);
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");

  const last = values[values.length - 1];
  const first = values[0];
  const directionUp = last > first;

  let stroke = "#5d6675"; // ink-500 neutral
  if (direction === "good") stroke = directionUp ? "#16a34a" : "#dc2626";
  else if (direction === "bad") stroke = directionUp ? "#dc2626" : "#16a34a";

  const lastX = (values.length - 1) * stepX;
  const lastY = height - 4 - ((last - min) / range) * (height - 8);

  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      className={className}
      role="img"
      aria-label="trend sparkline"
    >
      <polyline points={points} fill="none" stroke={stroke} strokeWidth={1.5} strokeLinejoin="round" />
      <circle cx={lastX} cy={lastY} r={2} fill={stroke} />
    </svg>
  );
}
