"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import maplibregl, { type ExpressionSpecification } from "maplibre-gl";
import { feature } from "topojson-client";
import type { Feature, FeatureCollection, Geometry } from "geojson";
import { useQuery } from "@tanstack/react-query";

// Loose Topology shape — avoids pulling topojson-specification just for types
type TopoJSON = {
  objects: Record<string, unknown>;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  [k: string]: any;
};
import "maplibre-gl/dist/maplibre-gl.css";

import { GEOGRAPHIES } from "@/lib/seed";
import { fetchSummaries, type GeoSummary } from "@/lib/api";
import { COUNTY_TO_MSA, GEO_CENTROIDS, ZCTA_BBOXES } from "@/lib/geo-crosswalk";
import {
  colorFor,
  legendFor,
  METRIC_LABELS,
  NO_DATA_COLOR,
  type MetricKey,
} from "@/lib/map-styling";
import { cn } from "@/lib/cn";

type Level = "state" | "county" | "city" | "zip";

const STATES_TOPO_URL = "https://cdn.jsdelivr.net/npm/us-atlas@3/states-10m.json";
const COUNTIES_TOPO_URL = "https://cdn.jsdelivr.net/npm/us-atlas@3/counties-10m.json";

// Bare empty style — pure data viz, no basemap tiles needed.
const EMPTY_STYLE: maplibregl.StyleSpecification = {
  version: 8,
  sources: {},
  layers: [
    { id: "background", type: "background", paint: { "background-color": "#f7f8fa" } },
  ],
  glyphs: "https://cdn.jsdelivr.net/npm/@maplibre/maplibre-gl-style-spec/fonts/{fontstack}/{range}.pbf",
};

type Props = {
  selectedGeoid: string;
  onSelect: (geoid: string) => void;
};

export function MapView({ selectedGeoid, onSelect }: Props) {
  const mapRef = useRef<maplibregl.Map | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [level, setLevel] = useState<Level>("county");
  const [metric, setMetric] = useState<MetricKey>("liquidityScore");
  const [hover, setHover] = useState<{
    name: string;
    fips: string;
    msaName?: string;
    metric?: number | string;
    metricKey: MetricKey;
    x: number;
    y: number;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Pull lightweight summaries from /summaries — one row per geography.
  const summariesQuery = useQuery({
    queryKey: ["summaries"],
    queryFn: fetchSummaries,
  });

  // geoid -> signals lookup, built from API summaries
  const summaryByGeoid = useMemo(() => {
    const m = new Map<string, GeoSummary>();
    for (const s of summariesQuery.data ?? []) m.set(s.geoid, s);
    return m;
  }, [summariesQuery.data]);

  // ---- init map (once on mount; summaries are applied via setData in the next effect) ----
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: EMPTY_STYLE,
      center: [-95.5, 38.5],
      zoom: 3.4,
      minZoom: 2.8,
      maxZoom: 12,
      attributionControl: false,
    });
    map.addControl(new maplibregl.NavigationControl({ visualizePitch: false }), "top-right");
    map.addControl(new maplibregl.AttributionControl({ compact: true, customAttribution: "US Atlas / Census TIGER" }), "bottom-right");

    map.on("load", async () => {
      try {
        const [statesTopoRes, countiesTopoRes] = await Promise.all([
          fetch(STATES_TOPO_URL),
          fetch(COUNTIES_TOPO_URL),
        ]);
        if (!statesTopoRes.ok || !countiesTopoRes.ok) throw new Error("topo fetch failed");
        const statesTopo = (await statesTopoRes.json()) as TopoJSON;
        const countiesTopo = (await countiesTopoRes.json()) as TopoJSON;

        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const statesGeo = feature(statesTopo as any, statesTopo.objects.states as any) as unknown as FeatureCollection<
          Geometry,
          { name: string }
        >;
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const countiesGeo = feature(countiesTopo as any, countiesTopo.objects.counties as any) as unknown as FeatureCollection<
          Geometry,
          { name: string }
        >;

        // Annotate each county feature with msaGeoid + metric values from API summaries
        for (const f of countiesGeo.features) {
          const fips = String((f as unknown as { id: string }).id).padStart(5, "0");
          const msaGeoid = COUNTY_TO_MSA[fips];
          (f.properties as Record<string, unknown>).fips = fips;
          (f.properties as Record<string, unknown>).msaGeoid = msaGeoid ?? null;
          if (msaGeoid && summaryByGeoid.has(msaGeoid)) {
            const summ = summaryByGeoid.get(msaGeoid)!;
            (f.properties as Record<string, unknown>).liquidityScore = summ.signals.liquidityScore;
            (f.properties as Record<string, unknown>).demandPressure = summ.signals.demandPressure;
            (f.properties as Record<string, unknown>).distressIndicator = summ.signals.distressIndicator;
            (f.properties as Record<string, unknown>).marketTier = summ.signals.marketTier;
            (f.properties as Record<string, unknown>).msaName = summ.name;
          }
        }
        for (const f of statesGeo.features) {
          const fips = String((f as unknown as { id: string }).id).padStart(2, "0");
          (f.properties as Record<string, unknown>).fips = fips;
        }

        // Synthesize ZCTA polygon features from approx bboxes (seed-only — replaced by TIGER)
        const zctaFeatures: Feature[] = Object.entries(ZCTA_BBOXES).map(([z, [w, s, e, n]]) => ({
          type: "Feature",
          id: z,
          properties: { fips: z, zcta: z, name: `ZCTA ${z}` },
          geometry: {
            type: "Polygon",
            coordinates: [[[w, s], [e, s], [e, n], [w, n], [w, s]]],
          },
        }));
        const zctaGeo: FeatureCollection = { type: "FeatureCollection", features: zctaFeatures };

        map.addSource("states", { type: "geojson", data: statesGeo });
        map.addSource("counties", { type: "geojson", data: countiesGeo });
        map.addSource("zctas", { type: "geojson", data: zctaGeo });
        // Stash so the summaries-effect can re-annotate without re-fetching TIGER
        (map as unknown as { _meridianCountiesGeo?: FeatureCollection })
          ._meridianCountiesGeo = countiesGeo;

        // ---- COUNTY fill ----
        map.addLayer({
          id: "counties-fill",
          type: "fill",
          source: "counties",
          paint: {
            "fill-color": colorExpression("liquidityScore"),
            "fill-opacity": 0.85,
          },
        });
        map.addLayer({
          id: "counties-line",
          type: "line",
          source: "counties",
          paint: { "line-color": "#bbc2cd", "line-width": 0.4 },
        });
        map.addLayer({
          id: "counties-hover",
          type: "line",
          source: "counties",
          paint: { "line-color": "#1d4ed8", "line-width": 1.5 },
          filter: ["==", ["get", "fips"], "___none___"],
        });

        // ---- STATE fill (initially hidden via layout) ----
        map.addLayer({
          id: "states-fill",
          type: "fill",
          source: "states",
          paint: { "fill-color": "#dde1e8", "fill-opacity": 0.0 },
        });
        map.addLayer({
          id: "states-line",
          type: "line",
          source: "states",
          paint: { "line-color": "#5d6675", "line-width": 0.7 },
        });

        // ---- ZCTA fill (visible only at zip level) ----
        map.addLayer({
          id: "zctas-fill",
          type: "fill",
          source: "zctas",
          paint: { "fill-color": "#3b82f6", "fill-opacity": 0.55 },
          layout: { visibility: "none" },
        });
        map.addLayer({
          id: "zctas-line",
          type: "line",
          source: "zctas",
          paint: { "line-color": "#1d4ed8", "line-width": 1.2 },
          layout: { visibility: "none" },
        });

        // ---- Click handlers ----
        map.on("click", "counties-fill", (e) => {
          const f = e.features?.[0];
          if (!f) return;
          const msaGeoid = f.properties?.msaGeoid as string | null;
          if (msaGeoid) onSelect(msaGeoid);
        });
        map.on("click", "states-fill", (e) => {
          const f = e.features?.[0];
          if (!f) return;
          const fips = f.properties?.fips as string | undefined;
          if (fips && GEOGRAPHIES.find((g) => g.geoid === fips)) onSelect(fips);
        });
        map.on("click", "zctas-fill", (e) => {
          const f = e.features?.[0];
          if (!f) return;
          const z = f.properties?.zcta as string | undefined;
          if (z) onSelect(z);
        });

        // ---- Hover handlers ----
        const hoverHandler = (layerId: string, kind: "county" | "state" | "zcta") => {
          map.on("mousemove", layerId, (e) => {
            map.getCanvas().style.cursor = "pointer";
            const f = e.features?.[0];
            if (!f) return;
            const props = f.properties as Record<string, unknown>;
            const fips = (props.fips as string) ?? "";
            map.setFilter("counties-hover", ["==", ["get", "fips"], kind === "county" ? fips : "___none___"]);
            const name = (props.name as string) ?? (kind === "zcta" ? `ZCTA ${fips}` : fips);
            const metricVal = props[metric] as number | string | undefined;
            setHover({
              name,
              fips,
              msaName: props.msaName as string | undefined,
              metric: metricVal,
              metricKey: metric,
              x: e.point.x,
              y: e.point.y,
            });
          });
          map.on("mouseleave", layerId, () => {
            map.getCanvas().style.cursor = "";
            map.setFilter("counties-hover", ["==", ["get", "fips"], "___none___"]);
            setHover(null);
          });
        };
        hoverHandler("counties-fill", "county");
        hoverHandler("states-fill", "state");
        hoverHandler("zctas-fill", "zcta");
      } catch (err) {
        console.error(err);
        setError("Failed to load TIGER boundaries from CDN. Check network connectivity.");
      }
    });

    mapRef.current = map;
    return () => {
      map.remove();
      mapRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ---- re-annotate counties source whenever summaries change ----
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !summariesQuery.data) return;
    const src = map.getSource("counties") as maplibregl.GeoJSONSource | undefined;
    if (!src) return;
    // Get the existing GeoJSON (we stored it on the map under _meridianCountiesGeo)
    const geo = (map as unknown as { _meridianCountiesGeo?: FeatureCollection }).
      _meridianCountiesGeo;
    if (!geo) return;
    for (const f of geo.features) {
      const fips = String((f as unknown as { id: string }).id ?? f.properties?.fips ?? "").padStart(5, "0");
      const msaGeoid = COUNTY_TO_MSA[fips];
      const props = (f.properties as Record<string, unknown>) ?? {};
      props.fips = fips;
      props.msaGeoid = msaGeoid ?? null;
      const summ = msaGeoid ? summaryByGeoid.get(msaGeoid) : undefined;
      if (summ) {
        props.liquidityScore = summ.signals.liquidityScore;
        props.demandPressure = summ.signals.demandPressure;
        props.distressIndicator = summ.signals.distressIndicator;
        props.marketTier = summ.signals.marketTier;
        props.msaName = summ.name;
      } else {
        delete props.liquidityScore;
        delete props.demandPressure;
        delete props.distressIndicator;
        delete props.marketTier;
        delete props.msaName;
      }
      f.properties = props;
    }
    src.setData(geo);
  }, [summariesQuery.data, summaryByGeoid]);

  // ---- update fill color when metric changes ----
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.getLayer("counties-fill")) return;
    map.setPaintProperty("counties-fill", "fill-color", colorExpression(metric));
  }, [metric]);

  // ---- update visibility when level changes ----
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.getLayer("counties-fill")) return;
    const show = (id: string, v: boolean) => map.setLayoutProperty(id, "visibility", v ? "visible" : "none");
    if (level === "county") {
      show("counties-fill", true);
      show("counties-line", true);
      show("states-fill", false);
      show("zctas-fill", false);
      show("zctas-line", false);
    } else if (level === "state") {
      show("counties-fill", false);
      show("counties-line", false);
      // Use states layer as the clickable click-target with a near-transparent fill,
      // colored by the *first* MSA fully inside it (proxy heuristic).
      map.setPaintProperty("states-fill", "fill-opacity", 0.001);
      show("states-fill", true);
      show("zctas-fill", false);
      show("zctas-line", false);
    } else if (level === "zip") {
      show("counties-fill", true);
      show("counties-line", true);
      show("zctas-fill", true);
      show("zctas-line", true);
      show("states-fill", false);
      // Auto-zoom into Baton Rouge ZIPs region
      map.flyTo({ center: [-91.13, 30.43], zoom: 10.5, duration: 800 });
    } else if (level === "city") {
      show("counties-fill", true);
      show("counties-line", true);
      show("states-fill", false);
      show("zctas-fill", false);
      show("zctas-line", false);
    }
  }, [level]);

  // ---- fly to the currently selected geography ----
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.getLayer("counties-fill")) return;
    const c = GEO_CENTROIDS[selectedGeoid];
    if (!c) return;
    const g = GEOGRAPHIES.find((x) => x.geoid === selectedGeoid);
    const zoom = g?.level === "zip" ? 12 : g?.level === "place" ? 10 : g?.level === "msa" ? 8 : 5.5;
    map.flyTo({ center: c, zoom, duration: 700 });
  }, [selectedGeoid]);

  return (
    <div className="relative h-[calc(100vh-8.5rem)] w-full overflow-hidden rounded border border-ink-200">
      <div ref={containerRef} className="h-full w-full" />

      {/* Controls overlay */}
      <div className="absolute left-3 top-3 z-10 flex flex-col gap-2">
        <div className="panel px-2 py-1.5 shadow-sm">
          <div className="text-[10px] font-semibold uppercase tracking-wider text-ink-500">Level</div>
          <div className="mt-1 inline-flex rounded border border-ink-200 bg-ink-50 p-0.5">
            {(["state", "county", "city", "zip"] as Level[]).map((l) => (
              <button
                key={l}
                type="button"
                onClick={() => setLevel(l)}
                className={cn(
                  "rounded px-2 py-0.5 text-[11px] font-medium capitalize transition-colors",
                  level === l ? "bg-white text-ink-900 shadow-sm" : "text-ink-500 hover:text-ink-700",
                )}
              >
                {l}
              </button>
            ))}
          </div>
          {level === "city" ? (
            <p className="mt-1.5 max-w-[220px] text-2xs italic text-ink-400">
              City layer pending — Census Place TIGER ingest in Phase 3.
            </p>
          ) : null}
          {level === "zip" ? (
            <p className="mt-1.5 max-w-[220px] text-2xs italic text-ink-400">
              ZIPs shown for seeded Baton Rouge area only. Full nationwide ZCTA layer in Phase 3.
            </p>
          ) : null}
        </div>

        <div className="panel px-2 py-1.5 shadow-sm">
          <div className="text-[10px] font-semibold uppercase tracking-wider text-ink-500">Shade by</div>
          <div className="mt-1 flex flex-col gap-0.5">
            {(Object.keys(METRIC_LABELS) as MetricKey[]).map((m) => (
              <label key={m} className="flex cursor-pointer items-center gap-2 text-[11px] text-ink-700">
                <input
                  type="radio"
                  name="metric"
                  checked={metric === m}
                  onChange={() => setMetric(m)}
                  className="h-3 w-3 accent-accent"
                />
                {METRIC_LABELS[m]}
              </label>
            ))}
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="absolute bottom-3 left-3 z-10 panel px-2 py-1.5 shadow-sm">
        <div className="text-[10px] font-semibold uppercase tracking-wider text-ink-500">
          {METRIC_LABELS[metric]}
        </div>
        <div className="mt-1 flex items-center gap-1">
          {legendFor(metric).map((s) => (
            <div key={s.label} className="flex flex-col items-center">
              <div
                className="h-3 w-6 border border-ink-200"
                style={{ backgroundColor: s.color }}
              />
              <span className="font-mono text-2xs text-ink-500">{s.label}</span>
            </div>
          ))}
          <div className="ml-2 flex flex-col items-center">
            <div className="h-3 w-6 border border-ink-200" style={{ backgroundColor: NO_DATA_COLOR }} />
            <span className="font-mono text-2xs text-ink-400">no data</span>
          </div>
        </div>
      </div>

      {/* Hover tooltip */}
      {hover ? (
        <div
          className="pointer-events-none absolute z-20 panel px-2 py-1.5 text-[11px] shadow-md"
          style={{ left: hover.x + 12, top: hover.y + 12 }}
        >
          <div className="font-semibold text-ink-900">{hover.name}</div>
          <div className="font-mono text-2xs text-ink-400">FIPS {hover.fips}</div>
          {hover.msaName ? (
            <div className="mt-0.5 text-2xs text-ink-500">in {hover.msaName} MSA</div>
          ) : null}
          {hover.metric !== undefined ? (
            <div className="mt-1 font-mono text-[12px] tabular-nums text-ink-700">
              {METRIC_LABELS[hover.metricKey]}:{" "}
              <span className="font-semibold">{hover.metric}</span>
            </div>
          ) : (
            <div className="mt-1 text-2xs italic text-ink-400">no data for this geography</div>
          )}
        </div>
      ) : null}

      {error ? (
        <div className="absolute inset-0 z-30 flex items-center justify-center bg-white/80">
          <div className="panel max-w-sm p-4 text-[12px] text-signal-bad">{error}</div>
        </div>
      ) : null}

      {summariesQuery.isLoading ? (
        <div className="absolute inset-0 z-20 flex items-center justify-center bg-ink-50">
          <div className="panel px-4 py-3 text-[12px] text-ink-500">
            Loading geographies from Meridian API…
          </div>
        </div>
      ) : null}
    </div>
  );
}

/** Build a MapLibre data-driven `match` expression for a given metric. */
function colorExpression(metric: MetricKey): ExpressionSpecification {
  if (metric === "marketTier") {
    return [
      "match",
      ["get", "marketTier"],
      "A",
      "#15803d",
      "B",
      "#22c55e",
      "C",
      "#d97706",
      "D",
      "#dc2626",
      NO_DATA_COLOR,
    ] as ExpressionSpecification;
  }
  // Step expression keyed off the metric numeric value
  if (metric === "liquidityScore") {
    return [
      "step",
      ["coalesce", ["get", "liquidityScore"], -1],
      NO_DATA_COLOR, // < 0 (i.e. missing)
      0,
      "#dcfce7",
      25,
      "#bbf7d0",
      40,
      "#86efac",
      50,
      "#4ade80",
      60,
      "#22c55e",
      75,
      "#16a34a",
    ] as ExpressionSpecification;
  }
  if (metric === "distressIndicator") {
    return [
      "step",
      ["coalesce", ["get", "distressIndicator"], -1],
      NO_DATA_COLOR,
      0,
      "#fee2e2",
      25,
      "#fecaca",
      40,
      "#fca5a5",
      50,
      "#f87171",
      60,
      "#ef4444",
      75,
      "#dc2626",
    ] as ExpressionSpecification;
  }
  if (metric === "demandPressure") {
    return [
      "step",
      ["coalesce", ["get", "demandPressure"], -999],
      NO_DATA_COLOR,
      -100,
      "#b91c1c",
      -15,
      "#dc2626",
      -8,
      "#fca5a5",
      -3,
      "#e5e7eb",
      3,
      "#86efac",
      8,
      "#22c55e",
      15,
      "#15803d",
    ] as ExpressionSpecification;
  }
  return ["literal", NO_DATA_COLOR] as unknown as ExpressionSpecification;
}

// Avoid unused-imports lint error for `colorFor` (used implicitly by inline expressions above)
void colorFor;
