"use client";

import { useQueries } from "@tanstack/react-query";
import type { GeoSnapshot } from "@/lib/seed";
import { fetchSnapshot } from "@/lib/api";
import { fmtDays, fmtMonths, fmtPct, fmtPctDelta, fmtUsd } from "@/lib/format";
import { cn } from "@/lib/cn";

const COMPARE_GEOIDS = ["12940", "13820", "32820", "27140", "33660", "43340"];

const tierTone = (t: string) =>
  t === "A" || t === "B"
    ? "text-signal-good"
    : t === "C"
      ? "text-signal-warn"
      : "text-signal-bad";

const liqTone = (n: number) =>
  n >= 60 ? "text-signal-good" : n >= 40 ? "text-signal-warn" : "text-signal-bad";

const distressTone = (n: number) =>
  n <= 35 ? "text-signal-good" : n <= 55 ? "text-signal-warn" : "text-signal-bad";

const yoyTone = (n: number) =>
  n > 0.02 ? "text-signal-good" : n < 0 ? "text-signal-bad" : "text-ink-700";

export function ComparisonView({ highlightGeoid }: { highlightGeoid: string }) {
  const queries = useQueries({
    queries: COMPARE_GEOIDS.map((geoid) => ({
      queryKey: ["snapshot", geoid],
      queryFn: () => fetchSnapshot(geoid),
    })),
  });

  const rows = queries
    .map((q) => q.data)
    .filter((d): d is GeoSnapshot => d !== null && d !== undefined);

  const isLoading = queries.some((q) => q.isLoading);
  const error = queries.find((q) => q.isError)?.error;

  const cell = "px-3 py-1.5 font-mono text-[12px] tabular-nums whitespace-nowrap";
  const label = "px-3 py-1.5 text-[11px] font-semibold uppercase tracking-wider text-ink-500 sticky left-0 bg-white";

  if (isLoading && rows.length === 0) {
    return (
      <section className="panel p-6 text-center text-[12px] text-ink-500">
        Loading comparison snapshots…
      </section>
    );
  }
  if (error) {
    return (
      <section className="panel p-6 text-center">
        <h3 className="text-[14px] font-semibold text-signal-bad">API error</h3>
        <p className="mt-2 font-mono text-2xs text-ink-400">{String(error)}</p>
      </section>
    );
  }

  return (
    <section className="panel">
      <header className="panel-header">
        <div>
          <h3 className="panel-title">Comparison — Baton Rouge MSA vs. similar-tier Southeast metros</h3>
          <p className="panel-question mt-0.5">
            Which markets are stronger comps for ARV haircut calibration?
          </p>
        </div>
      </header>
      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr className="border-b border-ink-200">
              <th className={cn(label, "text-left")}>Metric</th>
              {rows.map((r) => (
                <th
                  key={r.geo.geoid}
                  className={cn(
                    "px-3 py-2 text-left text-[11px] font-semibold",
                    r.geo.geoid === highlightGeoid && "bg-accent/5",
                  )}
                >
                  <div className="text-ink-900">{r.geo.name.replace(", LA", "").replace(", AL", "").replace(", TN-MS-AR", "").replace(", MS", "")}</div>
                  <div className="font-mono text-2xs font-normal text-ink-400">{r.geo.geoid}</div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-ink-100">
            <tr>
              <td className={label}>Market tier</td>
              {rows.map((r) => (
                <td
                  key={r.geo.geoid}
                  className={cn(cell, tierTone(r.signals.marketTier), r.geo.geoid === highlightGeoid && "bg-accent/5")}
                >
                  {r.signals.marketTier}
                </td>
              ))}
            </tr>
            <tr>
              <td className={label}>Liquidity score</td>
              {rows.map((r) => (
                <td
                  key={r.geo.geoid}
                  className={cn(cell, liqTone(r.signals.liquidityScore), r.geo.geoid === highlightGeoid && "bg-accent/5")}
                >
                  {r.signals.liquidityScore}
                </td>
              ))}
            </tr>
            <tr>
              <td className={label}>Demand pressure</td>
              {rows.map((r) => (
                <td
                  key={r.geo.geoid}
                  className={cn(cell, r.geo.geoid === highlightGeoid && "bg-accent/5")}
                >
                  {r.signals.demandPressure > 0 ? `+${r.signals.demandPressure}` : r.signals.demandPressure}
                </td>
              ))}
            </tr>
            <tr>
              <td className={label}>Distress indicator</td>
              {rows.map((r) => (
                <td
                  key={r.geo.geoid}
                  className={cn(cell, distressTone(r.signals.distressIndicator), r.geo.geoid === highlightGeoid && "bg-accent/5")}
                >
                  {r.signals.distressIndicator}
                </td>
              ))}
            </tr>
            <tr>
              <td className={label}>Median sale</td>
              {rows.map((r) => (
                <td
                  key={r.geo.geoid}
                  className={cn(cell, r.geo.geoid === highlightGeoid && "bg-accent/5")}
                >
                  {fmtUsd(r.pricing.medianSalePrice)}
                </td>
              ))}
            </tr>
            <tr>
              <td className={label}>Sale price YoY</td>
              {rows.map((r) => (
                <td
                  key={r.geo.geoid}
                  className={cn(cell, yoyTone(r.pricing.salePriceYoY), r.geo.geoid === highlightGeoid && "bg-accent/5")}
                >
                  {fmtPctDelta(r.pricing.salePriceYoY)}
                </td>
              ))}
            </tr>
            <tr>
              <td className={label}>Sale-to-list</td>
              {rows.map((r) => (
                <td
                  key={r.geo.geoid}
                  className={cn(cell, r.geo.geoid === highlightGeoid && "bg-accent/5")}
                >
                  {fmtPct(r.pricing.saleToListRatio)}
                </td>
              ))}
            </tr>
            <tr>
              <td className={label}>Months supply</td>
              {rows.map((r) => (
                <td
                  key={r.geo.geoid}
                  className={cn(cell, r.geo.geoid === highlightGeoid && "bg-accent/5")}
                >
                  {fmtMonths(r.supply.monthsSupply)}
                </td>
              ))}
            </tr>
            <tr>
              <td className={label}>Median DOM</td>
              {rows.map((r) => (
                <td
                  key={r.geo.geoid}
                  className={cn(cell, r.geo.geoid === highlightGeoid && "bg-accent/5")}
                >
                  {fmtDays(r.supply.medianDom)}
                </td>
              ))}
            </tr>
            <tr>
              <td className={label}>Price reductions</td>
              {rows.map((r) => (
                <td
                  key={r.geo.geoid}
                  className={cn(cell, r.geo.geoid === highlightGeoid && "bg-accent/5")}
                >
                  {fmtPct(r.supply.pctPriceReductions)}
                </td>
              ))}
            </tr>
            <tr>
              <td className={label}>Unemployment</td>
              {rows.map((r) => (
                <td
                  key={r.geo.geoid}
                  className={cn(cell, r.geo.geoid === highlightGeoid && "bg-accent/5")}
                >
                  {fmtPct(r.demo.unemploymentRate, 1)}
                </td>
              ))}
            </tr>
            <tr>
              <td className={label}>Pop growth (5yr)</td>
              {rows.map((r) => (
                <td
                  key={r.geo.geoid}
                  className={cn(cell, r.geo.geoid === highlightGeoid && "bg-accent/5")}
                >
                  {fmtPctDelta(r.demo.popGrowth5y)}
                </td>
              ))}
            </tr>
            <tr>
              <td className={label}>Median income</td>
              {rows.map((r) => (
                <td
                  key={r.geo.geoid}
                  className={cn(cell, r.geo.geoid === highlightGeoid && "bg-accent/5")}
                >
                  {fmtUsd(r.demo.medianIncome)}
                </td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  );
}
