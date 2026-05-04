"use client";

import { useMemo, useState } from "react";
import { Search } from "lucide-react";
import { GEOGRAPHIES, type GeoLevel, type Geography } from "@/lib/seed";
import { cn } from "@/lib/cn";

const LEVEL_LABEL: Record<GeoLevel, string> = {
  state: "State",
  msa: "MSA",
  place: "City",
  zip: "ZIP",
};

const LEVEL_ORDER: GeoLevel[] = ["msa", "state", "place", "zip"];

type Props = {
  selectedGeoid: string;
  onSelect: (geoid: string) => void;
  recent: string[];
};

export function LeftRail({ selectedGeoid, onSelect, recent }: Props) {
  const [query, setQuery] = useState("");

  const grouped = useMemo(() => {
    const filt = (g: Geography) => {
      if (!query) return true;
      const q = query.toLowerCase();
      return g.name.toLowerCase().includes(q) || g.geoid.includes(q);
    };
    return LEVEL_ORDER.map((lvl) => ({
      level: lvl,
      items: GEOGRAPHIES.filter((g) => g.level === lvl && filt(g)),
    })).filter((g) => g.items.length > 0);
  }, [query]);

  return (
    <aside className="flex h-screen w-72 shrink-0 flex-col border-r border-ink-200 bg-white">
      <div className="border-b border-ink-200 px-3 py-2">
        <div className="flex items-center gap-2">
          <span className="font-mono text-[13px] font-bold tracking-tightest text-ink-900">
            MERIDIAN
          </span>
          <span className="text-2xs text-ink-400">v0.1</span>
        </div>
        <p className="mt-0.5 text-2xs italic text-ink-500">RE credit intelligence</p>
      </div>

      <div className="border-b border-ink-200 px-3 py-2">
        <div className="relative">
          <Search className="pointer-events-none absolute left-2 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-ink-400" />
          <input
            type="text"
            placeholder="Search geographies…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full rounded border border-ink-200 bg-ink-50 py-1 pl-7 pr-2 text-[12px] outline-none placeholder:text-ink-400 focus:border-accent focus:bg-white"
          />
        </div>
      </div>

      {recent.length > 0 && !query ? (
        <div className="border-b border-ink-200 px-2 py-2">
          <div className="px-1 text-[10px] font-semibold uppercase tracking-wider text-ink-400">
            Recent
          </div>
          <ul className="mt-1 space-y-0.5">
            {recent.map((geoid) => {
              const g = GEOGRAPHIES.find((x) => x.geoid === geoid);
              if (!g) return null;
              return (
                <li key={geoid}>
                  <button
                    type="button"
                    onClick={() => onSelect(geoid)}
                    className={cn(
                      "flex w-full items-center justify-between rounded px-2 py-1 text-left text-[12px] hover:bg-ink-50",
                      selectedGeoid === geoid && "bg-accent/10 text-accent-700",
                    )}
                  >
                    <span className="truncate">{g.name}</span>
                    <span className="font-mono text-2xs text-ink-400">{LEVEL_LABEL[g.level]}</span>
                  </button>
                </li>
              );
            })}
          </ul>
        </div>
      ) : null}

      <nav className="flex-1 overflow-y-auto">
        {grouped.map(({ level, items }) => (
          <div key={level} className="border-b border-ink-100 px-2 py-2">
            <div className="px-1 text-[10px] font-semibold uppercase tracking-wider text-ink-400">
              {LEVEL_LABEL[level]} ({items.length})
            </div>
            <ul className="mt-1 space-y-0.5">
              {items.map((g) => (
                <li key={g.geoid}>
                  <button
                    type="button"
                    onClick={() => onSelect(g.geoid)}
                    className={cn(
                      "flex w-full items-center justify-between gap-2 rounded px-2 py-1 text-left text-[12px] hover:bg-ink-50",
                      selectedGeoid === g.geoid &&
                        "bg-accent/10 text-accent-700 ring-1 ring-inset ring-accent/30",
                    )}
                  >
                    <span className="truncate">{g.name}</span>
                    <span className="shrink-0 font-mono text-2xs text-ink-400">{g.geoid}</span>
                  </button>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </nav>

      <div className="border-t border-ink-200 px-3 py-2 text-2xs text-ink-400">
        <span className="kbd">⌘K</span> open command bar
      </div>
    </aside>
  );
}
