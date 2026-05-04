import type { GeoSnapshot } from "@/lib/seed";
import { fmtNum, fmtPct, fmtPctDelta, fmtUsd, fmtUsdSqft } from "@/lib/format";
import { Panel } from "./Panel";
import { MetricRow } from "./MetricRow";
import { PriceTrendChart } from "./PriceTrendChart";

export function PricingPanel({ snap }: { snap: GeoSnapshot }) {
  const p = snap.pricing;
  return (
    <Panel
      title="Pricing & demand"
      question="Where are prices headed and how fast are they moving?"
      rightSlot={`Realtor.com · ${snap.freshness[1].updatedAt}`}
    >
      <div className="px-2 pt-2">
        <PriceTrendChart months={p.salePriceTrend.months} values={p.salePriceTrend.values} height={120} />
      </div>
      <MetricRow
        label="Median sale price"
        value={fmtUsd(p.medianSalePrice)}
        delta={{
          text: fmtPctDelta(p.salePriceYoY) + " YoY",
          tone: p.salePriceYoY > 0.02 ? "good" : p.salePriceYoY < 0 ? "bad" : "neutral",
        }}
      />
      <MetricRow
        label="3-yr CAGR"
        value={fmtPct(p.salePriceCagr3y)}
        delta={{
          text: p.salePriceCagr3y > 0.03 ? "healthy" : "soft",
          tone: p.salePriceCagr3y > 0.03 ? "good" : "neutral",
        }}
      />
      <MetricRow label="Median list price" value={fmtUsd(p.medianListPrice)} />
      <MetricRow
        label="Sale-to-list ratio"
        value={fmtPct(p.saleToListRatio, 1)}
        delta={{
          text: p.saleToListRatio > 0.98 ? "strong" : p.saleToListRatio > 0.95 ? "soft" : "weak",
          tone: p.saleToListRatio > 0.98 ? "good" : p.saleToListRatio > 0.95 ? "neutral" : "bad",
        }}
      />
      <MetricRow label="$/sqft (sold)" value={fmtUsdSqft(p.pricePerSqftSold)} />
      <MetricRow label="$/sqft (list)" value={fmtUsdSqft(p.pricePerSqftList)} />
      <MetricRow label="Pending sales" value={fmtNum(p.pendingSales)} />
      <MetricRow label="Closed sales" value={fmtNum(p.closedSales)} />
    </Panel>
  );
}
