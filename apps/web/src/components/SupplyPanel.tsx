import type { GeoSnapshot } from "@/lib/seed";
import { fmtDays, fmtMonths, fmtNum, fmtPct, fmtPctDelta } from "@/lib/format";
import { Panel } from "./Panel";
import { MetricRow } from "./MetricRow";

export function SupplyPanel({ snap }: { snap: GeoSnapshot }) {
  const s = snap.supply;
  return (
    <Panel
      title="Supply & inventory"
      question="Is inventory loosening or tightening?"
      rightSlot={`Realtor.com · BPS · ${snap.freshness[1].updatedAt}`}
    >
      <MetricRow
        label="Active listings"
        value={fmtNum(s.activeListings)}
        trend={s.activeListingsTrend.values}
        trendDirection="bad"
      />
      <MetricRow
        label="New listings (mo)"
        value={fmtNum(s.newListingsMonthly)}
        delta={{
          text: fmtPctDelta(s.newListingsYoY) + " YoY",
          tone: s.newListingsYoY > 0 ? "neutral" : "neutral",
        }}
      />
      <MetricRow
        label="Months supply"
        value={fmtMonths(s.monthsSupply)}
        trend={s.monthsSupplyTrend.values}
        trendDirection="bad"
        delta={{
          text: s.monthsSupply > 4 ? "loose" : s.monthsSupply > 3 ? "balanced" : "tight",
          tone: s.monthsSupply > 5 ? "bad" : s.monthsSupply > 4 ? "neutral" : "good",
        }}
      />
      <MetricRow
        label="Median DOM"
        value={fmtDays(s.medianDom)}
        trend={s.medianDomTrend.values}
        trendDirection="bad"
      />
      <MetricRow
        label="Price reductions"
        value={fmtPct(s.pctPriceReductions)}
        delta={{
          text: s.pctPriceReductions > 0.4 ? "elevated" : s.pctPriceReductions > 0.3 ? "moderate" : "low",
          tone: s.pctPriceReductions > 0.4 ? "bad" : s.pctPriceReductions > 0.3 ? "neutral" : "good",
        }}
      />
      <MetricRow
        label="Permits 1-unit (12mo)"
        value={fmtNum(s.permits1Unit12mo)}
        trend={s.permitsTrend.values}
        trendDirection="good"
      />
      <MetricRow label="Permits 2-4 unit (12mo)" value={fmtNum(s.permits24Unit12mo)} />
      <MetricRow label="Permits 5+ unit (12mo)" value={fmtNum(s.permits5plus12mo)} />
    </Panel>
  );
}
