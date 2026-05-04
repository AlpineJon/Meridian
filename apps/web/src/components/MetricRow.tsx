import { cn } from "@/lib/cn";
import { Sparkline } from "./Sparkline";

type Props = {
  label: string;
  value: string;
  /** Secondary value, e.g. YoY delta */
  delta?: { text: string; tone: "good" | "bad" | "neutral" };
  trend?: number[];
  /** Direction interpretation for sparkline color */
  trendDirection?: "good" | "bad" | "neutral";
  className?: string;
};

export function MetricRow({ label, value, delta, trend, trendDirection = "neutral", className }: Props) {
  return (
    <div className={cn("grid grid-cols-[1fr_auto_auto_auto] items-center gap-3 px-3 py-1.5", className)}>
      <div className="text-[12px] text-ink-700">{label}</div>
      <div className="font-mono text-[13px] font-medium tabular-nums text-ink-900">{value}</div>
      {delta ? (
        <div
          className={cn(
            "font-mono text-[11px] tabular-nums",
            delta.tone === "good" && "text-signal-good",
            delta.tone === "bad" && "text-signal-bad",
            delta.tone === "neutral" && "text-ink-500",
          )}
        >
          {delta.text}
        </div>
      ) : (
        <div />
      )}
      {trend ? <Sparkline values={trend} width={88} height={22} direction={trendDirection} /> : <div />}
    </div>
  );
}
