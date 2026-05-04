import { SignalCard } from "./SignalCard";
import type { GeoSnapshot } from "@/lib/seed";

export function CreditSummary({ snap }: { snap: GeoSnapshot }) {
  const s = snap.signals;
  return (
    <section>
      <header className="mb-2 flex items-baseline justify-between">
        <div>
          <h2 className="text-[11px] font-semibold uppercase tracking-wider text-ink-500">
            Credit summary
          </h2>
          <p className="text-2xs italic text-ink-400">
            Composite signals derived from supply, pricing, and demographic inputs.
            Definitions in <span className="font-mono">METRICS.md</span>.
          </p>
        </div>
      </header>
      <div className="grid grid-cols-4 gap-3">
        <SignalCard
          kind="liquidity"
          label="Liquidity score"
          question="How fast does inventory clear?"
          value={s.liquidityScore}
          raw={s.liquidityScore}
          rationale={s.rationale.liquidity}
        />
        <SignalCard
          kind="demand"
          label="Demand pressure"
          question="Is demand outpacing or trailing supply?"
          value={s.demandPressure > 0 ? `+${s.demandPressure}` : `${s.demandPressure}`}
          raw={s.demandPressure}
          rationale={s.rationale.demand}
        />
        <SignalCard
          kind="distress"
          label="Distress indicator"
          question="Are price cuts and DOM expanding?"
          value={s.distressIndicator}
          raw={s.distressIndicator}
          rationale={s.rationale.distress}
        />
        <SignalCard
          kind="tier"
          label="Market tier"
          question="What credit policy applies?"
          value={s.marketTier}
          raw={s.marketTier}
          rationale={s.rationale.tier}
        />
      </div>
    </section>
  );
}
