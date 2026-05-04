import { cn } from "@/lib/cn";
import type { MarketTier } from "@/lib/seed";

type Props = {
  label: string;
  question: string;
  value: string | number;
  /** -100..100 for demand pressure, 0..100 for the others, "A"|"B"|"C"|"D" for tier */
  raw: number | MarketTier;
  rationale: string;
  /** "liquidity" | "demand" | "distress" | "tier" — drives interpretation of raw */
  kind: "liquidity" | "demand" | "distress" | "tier";
};

function toneFor(kind: Props["kind"], raw: number | MarketTier): "good" | "warn" | "bad" {
  if (kind === "tier") {
    const t = raw as MarketTier;
    if (t === "A") return "good";
    if (t === "B") return "good";
    if (t === "C") return "warn";
    return "bad";
  }
  const n = raw as number;
  if (kind === "liquidity") {
    if (n >= 60) return "good";
    if (n >= 40) return "warn";
    return "bad";
  }
  if (kind === "demand") {
    if (n >= 5) return "good";
    if (n >= -5) return "warn";
    return "bad";
  }
  // distress: high = bad
  if (n <= 35) return "good";
  if (n <= 55) return "warn";
  return "bad";
}

export function SignalCard({ label, question, value, raw, rationale, kind }: Props) {
  const tone = toneFor(kind, raw);
  const toneClasses = {
    good: "border-signal-good/40 bg-signal-goodBg/30",
    warn: "border-signal-warn/40 bg-signal-warnBg/30",
    bad: "border-signal-bad/40 bg-signal-badBg/30",
  }[tone];
  const dotClasses = {
    good: "bg-signal-good",
    warn: "bg-signal-warn",
    bad: "bg-signal-bad",
  }[tone];
  const valueClasses = {
    good: "text-signal-good",
    warn: "text-signal-warn",
    bad: "text-signal-bad",
  }[tone];

  return (
    <div className={cn("panel border", toneClasses)}>
      <div className="flex items-center justify-between border-b border-current/10 px-3 py-2">
        <div className="flex items-center gap-2">
          <span className={cn("h-1.5 w-1.5 rounded-full", dotClasses)} />
          <span className="text-[11px] font-semibold uppercase tracking-wider text-ink-700">
            {label}
          </span>
        </div>
      </div>
      <div className="px-3 py-3">
        <div className={cn("font-mono text-3xl font-semibold tabular-nums", valueClasses)}>{value}</div>
        <p className="mt-1 text-2xs italic text-ink-500">{question}</p>
        <p className="mt-2 text-[12px] leading-snug text-ink-700">{rationale}</p>
      </div>
    </div>
  );
}
