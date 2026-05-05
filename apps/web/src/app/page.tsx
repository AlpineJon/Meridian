"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { LeftRail } from "@/components/LeftRail";
import { TopBar } from "@/components/TopBar";
import { CreditSummary } from "@/components/CreditSummary";
import { SupplyPanel } from "@/components/SupplyPanel";
import { PricingPanel } from "@/components/PricingPanel";
import { DemoPanel } from "@/components/DemoPanel";
import { ComparisonView } from "@/components/ComparisonView";
import { FreshnessFooter } from "@/components/FreshnessFooter";
import { MapView } from "@/components/MapView";
import { fetchGeographies, fetchSnapshot, type ApiGeography } from "@/lib/api";

const TABS = [
  { id: "credit", label: "Credit summary" },
  { id: "supply", label: "Supply & inventory" },
  { id: "pricing", label: "Pricing & demand" },
  { id: "demo", label: "Demographics" },
  { id: "compare", label: "Comparison" },
  { id: "map", label: "Map" },
];

export default function Page() {
  const [selectedGeoid, setSelectedGeoid] = useState("12940"); // Baton Rouge MSA
  const [recent, setRecent] = useState<string[]>(["12940", "70809", "13820"]);
  const [tab, setTab] = useState("credit");

  const geosQuery = useQuery({
    queryKey: ["geographies"],
    queryFn: fetchGeographies,
    staleTime: 5 * 60_000,
  });
  const allGeos = geosQuery.data ?? [];
  const geoById = useMemo(() => {
    const m = new Map<string, ApiGeography>();
    for (const g of allGeos) m.set(g.geoid, g);
    return m;
  }, [allGeos]);

  const geo = geoById.get(selectedGeoid);

  const snapQuery = useQuery({
    queryKey: ["snapshot", selectedGeoid],
    queryFn: () => fetchSnapshot(selectedGeoid),
    enabled: !!geo,
  });
  const snap = snapQuery.data ?? null;

  const parentChain = useMemo(() => {
    if (!geo) return [];
    const chain: { name: string; geoid: string }[] = [];
    let cur: ApiGeography | undefined = geo;
    while (cur?.parent) {
      const parent = geoById.get(cur.parent);
      if (!parent) break;
      chain.unshift({ name: parent.name, geoid: parent.geoid });
      cur = parent;
    }
    return chain;
  }, [geo, geoById]);

  const handleSelect = (geoid: string) => {
    setSelectedGeoid(geoid);
    setRecent((prev) => [geoid, ...prev.filter((x) => x !== geoid)].slice(0, 5));
  };

  return (
    <div className="flex h-screen overflow-hidden">
      <LeftRail selectedGeoid={selectedGeoid} onSelect={handleSelect} recent={recent} />
      <main className="flex flex-1 flex-col overflow-hidden">
        <TopBar
          geoName={geo?.name ?? "Loading…"}
          geoLevel={geo?.level ?? ""}
          geoid={geo?.geoid ?? selectedGeoid}
          parentChain={parentChain}
          tabs={TABS}
          activeTab={tab}
          onTabChange={setTab}
        />
        <div className="flex-1 overflow-y-auto bg-ink-50 p-4">
          {tab === "map" ? (
            <MapView selectedGeoid={selectedGeoid} onSelect={handleSelect} />
          ) : tab === "compare" ? (
            <ComparisonView highlightGeoid={selectedGeoid} />
          ) : snapQuery.isLoading ? (
            <div className="panel mx-auto mt-12 max-w-md p-8 text-center">
              <div className="text-[12px] text-ink-500">Loading snapshot from Meridian API…</div>
            </div>
          ) : snapQuery.isError ? (
            <div className="panel mx-auto mt-12 max-w-md p-8 text-center">
              <h2 className="text-[14px] font-semibold text-signal-bad">API error</h2>
              <p className="mt-2 text-[12px] text-ink-500">
                Could not reach the Meridian API at{" "}
                <span className="font-mono">localhost:8001</span>.
              </p>
              <p className="mt-2 font-mono text-2xs text-ink-400">
                {String(snapQuery.error)}
              </p>
            </div>
          ) : !snap ? (
            <div className="panel mx-auto mt-12 max-w-md p-8 text-center">
              <h2 className="text-[14px] font-semibold text-ink-900">No snapshot for this geo yet</h2>
              <p className="mt-2 text-[12px] text-ink-500">
                Seeded data covers Baton Rouge MSA, comparison MSAs (Birmingham, Memphis,
                Jackson, Mobile, Shreveport), and ZIP 70809. Phase 2 ingestion will populate every
                geography from upstream sources.
              </p>
              <p className="mt-3 text-[11px] text-ink-400">
                Try the <span className="font-semibold">Comparison</span> tab — it works regardless
                of selection.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {tab === "credit" && (
                <>
                  <CreditSummary snap={snap} />
                  <div className="grid grid-cols-3 gap-4">
                    <SupplyPanel snap={snap} />
                    <PricingPanel snap={snap} />
                    <DemoPanel snap={snap} />
                  </div>
                </>
              )}
              {tab === "supply" && (
                <div className="grid grid-cols-2 gap-4">
                  <SupplyPanel snap={snap} />
                </div>
              )}
              {tab === "pricing" && (
                <div className="grid grid-cols-2 gap-4">
                  <PricingPanel snap={snap} />
                </div>
              )}
              {tab === "demo" && (
                <div className="grid grid-cols-2 gap-4">
                  <DemoPanel snap={snap} />
                </div>
              )}
            </div>
          )}
        </div>
        {snap && tab !== "compare" && tab !== "map" ? <FreshnessFooter snap={snap} /> : null}
      </main>
    </div>
  );
}
