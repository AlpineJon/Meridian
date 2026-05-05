import type { GeoSnapshot } from "@/lib/seed";
import { fmtNum, fmtPct, fmtPctDelta, fmtUsd, fmtUsdSqft } from "@/lib/format";
import { Panel } from "./Panel";
import { MetricRow } from "./MetricRow";
import { PriceTrendChart } from "./PriceTrendChart";

const isNum = (n: unknown): n is number => typeof n === "number" && Number.isFinite(n);

export function PricingPanel({ snap }: { snap: GeoSnapshot }) {
  const p = snap.pricing;
  return (
    <Panel
      title="Pricing & demand"
      question="Where are prices headed and how fast are they moving?"
      rightSlot={`Realtor.com · ${snap.freshness[1]?.updatedAt ?? snap.freshness[0]?.updatedAt ?? ""}`}
    >
      {p.salePriceTrend ? (
        <div className="px-2 pt-2">
          <PriceTrendChart months={p.salePriceTrend.months} values={p.salePriceTrend.values} height={120} />
        </div>
      ) : null}
      <MetricRow
        label="Median sale price"
        value={fmtUsd(p.medianSalePrice)}
        delta={
          isNum(p.salePriceYoY)
            ? {
                text: fmtPctDelta(p.salePriceYoY) + " YoY",
                tone: p.salePriceYoY > 0.02 ? "good" : p.salePriceYoY < 0 ? "bad" : "neutral",
              }
            : undefined
        }
      />
      <MetricRow
        label="3-yr CAGR"
        value={fmtPct(p.salePriceCagr3y)}
        delta={
          isNum(p.salePriceCagr3y)
            ? {
                text: p.salePriceCagr3y > 0.03 ? "healthy" : "soft",
                tone: p.salePriceCagr3y > 0.03 ? "good" : "neutral",
              }
            : undefined
        }
      />
      <MetricRow label="Median list price" value={fmtUsd(p.medianListPrice)} />
      <MetricRow
        label="Sale-to-list ratio"
        value={fmtPct(p.saleToListRatio, 1)}
        delta={
          isNum(p.saleToListRatio)
            ? {
                text:
                  p.saleToListRatio > 0.98 ? "strong" : p.saleToListRatio > 0.95 ? "soft" : "weak",
                tone:
                  p.saleToListRatio > 0.98 ? "good" : p.saleToListRatio > 0.95 ? "neutral" : "bad",
              }
            : undefined
        }
      />
      <MetricRow label="$/sqft (sold)" value={fmtUsdSqft(p.pricePerSqftSold)} />
      <MetricRow label="$/sqft (list)" value={fmtUsdSqft(p.pricePerSqftList)} />
      <MetricRow label="Pending sales" value={fmtNum(p.pendingSales)} />
      <MetricRow label="Closed sales" value={fmtNum(p.closedSales)} />
    </Panel>
  );
}
