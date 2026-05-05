/**
 * Thin client for the Meridian FastAPI backend.
 *
 * The response shape from /snapshots/{geoid} mirrors the GeoSnapshot type
 * already defined in seed.ts, so consumers can keep using that type.
 */

import type { GeoSnapshot } from "./seed";

const API_BASE =
  process.env.NEXT_PUBLIC_MERIDIAN_API ?? "http://127.0.0.1:8001";

export async function fetchSnapshot(geoid: string): Promise<GeoSnapshot | null> {
  const res = await fetch(`${API_BASE}/snapshots/${encodeURIComponent(geoid)}`, {
    cache: "no-store",
  });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`snapshot fetch failed: ${res.status}`);
  return (await res.json()) as GeoSnapshot;
}

export async function fetchHealth(): Promise<{ ok: boolean; db: { ok: boolean } }> {
  const res = await fetch(`${API_BASE}/health`, { cache: "no-store" });
  if (!res.ok) throw new Error(`health failed: ${res.status}`);
  return res.json();
}

export type ApiGeography = {
  geoid: string;
  level: "state" | "msa" | "place" | "zip" | "county";
  name: string;
  state: string | null;
  parent: string | null;
  population: number | null;
};

export async function fetchGeographies(): Promise<ApiGeography[]> {
  const res = await fetch(`${API_BASE}/geographies`, { cache: "no-store" });
  if (!res.ok) throw new Error(`geographies failed: ${res.status}`);
  const j = (await res.json()) as { geographies: ApiGeography[] };
  return j.geographies;
}

export type GeoSummary = {
  geoid: string;
  level: "state" | "msa" | "place" | "zip" | "county";
  name: string;
  state: string | null;
  parent: string | null;
  signals: {
    liquidityScore: number | null;
    demandPressure: number | null;
    distressIndicator: number | null;
    marketTier: string | null;
  };
};

export async function fetchSummaries(): Promise<GeoSummary[]> {
  const res = await fetch(`${API_BASE}/summaries`, { cache: "no-store" });
  if (!res.ok) throw new Error(`summaries failed: ${res.status}`);
  const j = (await res.json()) as { summaries: GeoSummary[] };
  return j.summaries;
}
