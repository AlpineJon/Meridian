import type { GeoSnapshot } from "@/lib/seed";
import { fmtNum, fmtPct, fmtPctDelta, fmtUsd } from "@/lib/format";
import { Panel } from "./Panel";
import { MetricRow } from "./MetricRow";

export function DemoPanel({ snap }: { snap: GeoSnapshot }) {
  const d = snap.demo;
  return (
    <Panel
      title="Demographics & economy"
      question="Is the underlying population and income base supporting demand?"
      rightSlot={`Census ACS · BLS · ${snap.freshness[0]?.updatedAt ?? ""}`}
    >
      <MetricRow label="Population" value={fmtNum(d.population)} />
      <MetricRow
        label="5-yr pop growth"
        value={fmtPctDelta(d.popGrowth5y)}
        delta={{
          text: d.popGrowth5y > 0.01 ? "growing" : d.popGrowth5y > 0 ? "flat" : "shrinking",
          tone: d.popGrowth5y > 0.01 ? "good" : d.popGrowth5y > 0 ? "neutral" : "bad",
        }}
      />
      <MetricRow label="Households" value={fmtNum(d.households)} />
      <MetricRow label="Median household income" value={fmtUsd(d.medianIncome)} />
      <MetricRow
        label="Unemployment"
        value={fmtPct(d.unemploymentRate, 1)}
        delta={{
          text: d.unemploymentRate < 0.035 ? "tight" : d.unemploymentRate < 0.045 ? "normal" : "loose",
          tone: d.unemploymentRate < 0.035 ? "good" : d.unemploymentRate < 0.045 ? "neutral" : "bad",
        }}
      />
      <MetricRow label="Owner-occupied %" value={fmtPct(d.ownerOccupiedPct)} />
      <MetricRow label="Renter-occupied %" value={fmtPct(d.renterOccupiedPct)} />
      <MetricRow label="Median home value" value={fmtUsd(d.medianHomeValue)} />
      <MetricRow label="Median gross rent" value={fmtUsd(d.medianGrossRent)} />
      <MetricRow
        label="Rent-to-income"
        value={fmtPct(d.rentToIncome)}
        delta={{
          text: d.rentToIncome > 0.3 ? "burdened" : "healthy",
          tone: d.rentToIncome > 0.3 ? "bad" : "good",
        }}
      />
    </Panel>
  );
}
