import type { GeoSnapshot } from "@/lib/seed";
import { fmtRelativeDate } from "@/lib/format";

export function FreshnessFooter({ snap }: { snap: GeoSnapshot }) {
  return (
    <footer className="flex flex-wrap items-center gap-x-4 gap-y-1 border-t border-ink-200 bg-ink-50 px-4 py-1.5 text-2xs text-ink-500">
      <span className="font-semibold uppercase tracking-wider">Sources</span>
      {snap.freshness.map((f) => (
        <span key={f.source} className="flex items-center gap-1.5">
          <span>{f.source}</span>
          <span className="font-mono text-ink-400">· {fmtRelativeDate(f.updatedAt)}</span>
        </span>
      ))}
    </footer>
  );
}
