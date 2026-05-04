"use client";

import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { fmtMonthShort, fmtUsd } from "@/lib/format";

type Props = {
  months: string[];
  values: number[];
  height?: number;
};

export function PriceTrendChart({ months, values, height = 140 }: Props) {
  const data = months.map((m, i) => ({ month: m, value: values[i] }));
  return (
    <div style={{ width: "100%", height }}>
      <ResponsiveContainer>
        <AreaChart data={data} margin={{ top: 8, right: 12, left: 12, bottom: 4 }}>
          <defs>
            <linearGradient id="priceFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.18} />
              <stop offset="100%" stopColor="#3b82f6" stopOpacity={0} />
            </linearGradient>
          </defs>
          <XAxis
            dataKey="month"
            tickFormatter={fmtMonthShort}
            tick={{ fontSize: 10, fill: "#5d6675" }}
            axisLine={{ stroke: "#dde1e8" }}
            tickLine={false}
            interval={1}
          />
          <YAxis
            tickFormatter={(v) => fmtUsd(v as number, { compact: true })}
            tick={{ fontSize: 10, fill: "#5d6675" }}
            axisLine={false}
            tickLine={false}
            domain={["dataMin - 5000", "dataMax + 5000"]}
            width={48}
          />
          <Tooltip
            cursor={{ stroke: "#bbc2cd", strokeDasharray: "2 2" }}
            contentStyle={{
              fontSize: 11,
              border: "1px solid #dde1e8",
              borderRadius: 4,
              padding: "4px 8px",
              background: "#fff",
            }}
            labelFormatter={(l) => fmtMonthShort(l as string)}
            formatter={(v) => [fmtUsd(v as number), "Median sale"]}
          />
          <Area
            type="monotone"
            dataKey="value"
            stroke="#3b82f6"
            strokeWidth={1.5}
            fill="url(#priceFill)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
