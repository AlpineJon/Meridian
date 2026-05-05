"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Search } from "lucide-react";
import { fetchGeographies, type ApiGeography } from "@/lib/api";
import { cn } from "@/lib/cn";

type Level = ApiGeography["level"];

const LEVEL_LABEL: Record<Level, string> = {
  state: "State",
  msa: "MSA",
  county: "County",
  place: "City",
  zip: "ZIP",
};

const LEVEL_ORDER: Level[] = ["state", "msa", "county", "place", "zip"];

// Show this many per level by default; full list filters when user types in search.
const DEFAULT_VISIBLE = 25;

type Props = {
  selectedGeoid: string;
  onSelect: (geoid: string) => void;
  recent: string[];
};

export function LeftRail({ selectedGeoid, onSelect, recent }: Props) {
  const [query, setQuery] = useState("");
  const [expandedLevel, setExpandedLevel] = useState<Level | null>(null);

  const geosQuery = useQuery({
    queryKey: ["geographies"],
    queryFn: fetchGeographies,
    staleTime: 5 * 60_000,
  });

  const allGeos = geosQuery.data ?? [];

  // recent items - only those that exist in the fetched list
  const recentGeos = useMemo(
    () => recent.map((g) => allGeos.find((x) => x.geoid === g)).filter(Boolean) as ApiGeography[],
    [recent, allGeos],
  );

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    const matches = (g: ApiGeography) =>
      !q || g.name.toLowerCase().includes(q) || g.geoid.includes(q) || (g.state ?? "").toLowerCase().includes(q);

    const groupedAll: Record<Level, ApiGeography[]> = {
      state: [], msa: [], county: [], place: [], zip: [],
    };
    for (const g of allGeos) {
      if (matches(g)) groupedAll[g.level].push(g);
    }
    // Sort each group by population desc (null last), then name
    for (const lvl of LEVEL_ORDER) {
      groupedAll[lvl].sort((a, b) => {
        const pa = a.population ?? -1;
        const pb = b.population ?? -1;
        if (pa !== pb) return pb - pa;
        return a.name.localeCompare(b.name);
      });
    }
    return groupedAll;
  }, [query, allGeos]);

  return (
    <aside className="flex h-screen w-72 shrink-0 flex-col border-r border-ink-200 bg-white">
      <div className="border-b border-ink-200 px-3 py-2">
        <div className="flex items-center gap-2">
          <span className="font-mono text-[13px] font-bold tracking-tightest text-ink-900">MERIDIAN</span>
          <span className="text-2xs text-ink-400">v0.2</span>
        </div>
        <p className="mt-0.5 text-2xs italic text-ink-500">RE credit intelligence</p>
        {geosQuery.isLoading ? (
          <p className="mt-1 text-2xs text-ink-400">Loading geographies…</p>
        ) : (
          <p className="mt-1 text-2xs text-ink-400">
            {allGeos.length.toLocaleString()} geographies indexed
          </p>
        )}
      </div>

      <div className="border-b border-ink-200 px-3 py-2">
        <div className="relative">
          <Search className="pointer-events-none absolute left-2 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-ink-400" />
          <input
            type="text"
            placeholder="Search 4,200+ geographies…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full rounded border border-ink-200 bg-ink-50 py-1 pl-7 pr-2 text-[12px] outline-none placeholder:text-ink-400 focus:border-accent focus:bg-white"
          />
        </div>
      </div>

      {recentGeos.length > 0 && !query ? (
        <div className="border-b border-ink-200 px-2 py-2">
          <div className="px-1 text-[10px] font-semibold uppercase tracking-wider text-ink-400">
            Recent
          </div>
          <ul className="mt-1 space-y-0.5">
            {recentGeos.map((g) => (
              <li key={g.geoid}>
                <button
                  type="button"
                  onClick={() => onSelect(g.geoid)}
                  className={cn(
                    "flex w-full items-center justify-between rounded px-2 py-1 text-left text-[12px] hover:bg-ink-50",
                    selectedGeoid === g.geoid && "bg-accent/10 text-accent-700",
                  )}
                >
                  <span className="truncate">{g.name}</span>
                  <span className="font-mono text-2xs text-ink-400">{LEVEL_LABEL[g.level]}</span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      <nav className="flex-1 overflow-y-auto">
        {LEVEL_ORDER.map((lvl) => {
          const items = filtered[lvl];
          if (items.length === 0) return null;
          const isExpanded = !!query || expandedLevel === lvl;
          const visible = isExpanded ? items.slice(0, 200) : items.slice(0, DEFAULT_VISIBLE);
          const hidden = items.length - visible.length;
          return (
            <div key={lvl} className="border-b border-ink-100 px-2 py-2">
              <div className="flex items-center justify-between px-1">
                <span className="text-[10px] font-semibold uppercase tracking-wider text-ink-400">
                  {LEVEL_LABEL[lvl]} ({items.length.toLocaleString()})
                </span>
                {!query && hidden > 0 ? (
                  <button
                    type="button"
                    onClick={() => setExpandedLevel(isExpanded ? null : lvl)}
                    className="text-2xs text-accent hover:underline"
                  >
                    {isExpanded ? "show less" : `show ${hidden.toLocaleString()} more`}
                  </button>
                ) : null}
              </div>
              <ul className="mt-1 space-y-0.5">
                {visible.map((g) => (
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
                      <span className="truncate" title={g.name}>{g.name}</span>
                      <span className="shrink-0 font-mono text-2xs text-ink-400">{g.geoid}</span>
                    </button>
                  </li>
                ))}
              </ul>
              {!isExpanded && hidden > 0 && !query ? (
                <p className="mt-1 px-1 text-2xs italic text-ink-400">
                  + {hidden.toLocaleString()} more — type to search
                </p>
              ) : null}
            </div>
          );
        })}
        {!geosQuery.isLoading && allGeos.length === 0 ? (
          <div className="px-3 py-6 text-center text-2xs text-ink-400">
            API returned no geographies. Run the seeder.
          </div>
        ) : null}
      </nav>

      <div className="border-t border-ink-200 px-3 py-2 text-2xs text-ink-400">
        <span className="kbd">⌘K</span> open command bar
      </div>
    </aside>
  );
}
