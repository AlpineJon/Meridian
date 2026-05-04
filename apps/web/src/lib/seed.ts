/**
 * Seed data for the prototype.
 *
 * Numbers are public-source estimates for early-2026 (Census ACS 5-yr 2019-2023,
 * Realtor.com Economic Research monthly, BLS LAUS, Census BPS). These are bootstrap
 * seeds for the demo; production uses live ingestion via the adapter pattern.
 *
 * Sources per metric are documented in docs/METRICS.md.
 */
export type GeoLevel = "state" | "msa" | "place" | "zip";

export type Trend = {
  // Most-recent-month-last; length 12 = trailing twelve months
  values: number[];
  // ISO month strings, parallel array
  months: string[];
};

export type Geography = {
  geoid: string; // FIPS-based canonical key
  level: GeoLevel;
  name: string;
  state: string; // 2-letter
  parent?: string; // parent geoid for rollups
  population?: number;
};

export type MarketTier = "A" | "B" | "C" | "D";

export type CompositeSignals = {
  /** 0-100, higher = more liquid (faster sale, less inventory) */
  liquidityScore: number;
  /** -100..100, positive = demand outpacing supply */
  demandPressure: number;
  /** 0-100, higher = more distress signals (price cuts + DOM expansion + permit slowdown) */
  distressIndicator: number;
  marketTier: MarketTier;
  // human-readable rationale per signal
  rationale: {
    liquidity: string;
    demand: string;
    distress: string;
    tier: string;
  };
};

export type SupplyMetrics = {
  activeListings: number;
  activeListingsTrend: Trend;
  newListingsMonthly: number;
  newListingsYoY: number; // pct delta
  monthsSupply: number;
  monthsSupplyTrend: Trend;
  medianDom: number;
  medianDomTrend: Trend;
  pctPriceReductions: number; // 0..1
  permits1Unit12mo: number;
  permits24Unit12mo: number;
  permits5plus12mo: number;
  permitsTrend: Trend;
};

export type PricingMetrics = {
  medianListPrice: number;
  medianSalePrice: number;
  saleToListRatio: number; // 0..1
  pricePerSqftList: number;
  pricePerSqftSold: number;
  salePriceYoY: number;
  salePriceCagr3y: number;
  pendingSales: number;
  closedSales: number;
  salePriceTrend: Trend;
};

export type DemoMetrics = {
  population: number;
  households: number;
  medianIncome: number;
  ownerOccupiedPct: number;
  renterOccupiedPct: number;
  medianHomeValue: number;
  medianGrossRent: number;
  rentToIncome: number;
  popGrowth5y: number;
  unemploymentRate: number;
};

export type GeoSnapshot = {
  geo: Geography;
  signals: CompositeSignals;
  supply: SupplyMetrics;
  pricing: PricingMetrics;
  demo: DemoMetrics;
  // Last refresh per source — drives the "Last updated" labels
  freshness: { source: string; updatedAt: string }[];
};

/* ------------ helpers ------------ */
const months12 = (endIso: string): string[] => {
  const [y, m] = endIso.split("-").map(Number);
  const out: string[] = [];
  for (let i = 11; i >= 0; i--) {
    const d = new Date(Date.UTC(y, m - 1 - i, 1));
    out.push(`${d.getUTCFullYear()}-${String(d.getUTCMonth() + 1).padStart(2, "0")}`);
  }
  return out;
};

/* ------------ geographies ------------ */
export const GEOGRAPHIES: Geography[] = [
  // States
  { geoid: "22", level: "state", name: "Louisiana", state: "LA", population: 4_573_749 },
  { geoid: "01", level: "state", name: "Alabama", state: "AL", population: 5_108_468 },
  { geoid: "47", level: "state", name: "Tennessee", state: "TN", population: 7_126_489 },
  { geoid: "28", level: "state", name: "Mississippi", state: "MS", population: 2_940_057 },
  // MSAs (Census CBSA codes)
  { geoid: "12940", level: "msa", name: "Baton Rouge, LA", state: "LA", parent: "22", population: 870_569 },
  { geoid: "13820", level: "msa", name: "Birmingham-Hoover, AL", state: "AL", parent: "01", population: 1_115_289 },
  { geoid: "32820", level: "msa", name: "Memphis, TN-MS-AR", state: "TN", parent: "47", population: 1_335_674 },
  { geoid: "27140", level: "msa", name: "Jackson, MS", state: "MS", parent: "28", population: 591_978 },
  { geoid: "33660", level: "msa", name: "Mobile, AL", state: "AL", parent: "01", population: 411_407 },
  { geoid: "43340", level: "msa", name: "Shreveport-Bossier City, LA", state: "LA", parent: "22", population: 392_302 },
  // Place
  { geoid: "2205000", level: "place", name: "Baton Rouge city, LA", state: "LA", parent: "12940", population: 220_236 },
  // ZIPs (ZCTA) within Baton Rouge
  { geoid: "70809", level: "zip", name: "70809 — Baton Rouge", state: "LA", parent: "2205000", population: 23_185 },
  { geoid: "70810", level: "zip", name: "70810 — Baton Rouge", state: "LA", parent: "2205000", population: 39_402 },
  { geoid: "70806", level: "zip", name: "70806 — Baton Rouge", state: "LA", parent: "2205000", population: 28_094 },
  { geoid: "70808", level: "zip", name: "70808 — Baton Rouge", state: "LA", parent: "2205000", population: 26_318 },
  { geoid: "70815", level: "zip", name: "70815 — Baton Rouge", state: "LA", parent: "2205000", population: 41_805 },
];

/* ------------ snapshots ------------ */
const MONTHS_END = "2026-04";
const M12 = months12(MONTHS_END);

const SNAPSHOTS: Record<string, GeoSnapshot> = {
  // ===== Baton Rouge MSA =====
  "12940": {
    geo: GEOGRAPHIES.find((g) => g.geoid === "12940")!,
    signals: {
      liquidityScore: 42,
      demandPressure: -8,
      distressIndicator: 58,
      marketTier: "C",
      rationale: {
        liquidity: "Months supply 5.2 (above 4.0 balanced threshold) and median DOM 52d trending up.",
        demand: "Sale price growth slowing to +1.4% YoY; new listings up 6% YoY but pending sales flat.",
        distress: "Price reductions on 38% of active listings — elevated. Permits down 11% YoY.",
        tier:
          "Tier C: stable demographic base but credit caution warranted; haircut ARV 8-12% vs. comp set.",
      },
    },
    supply: {
      activeListings: 3812,
      activeListingsTrend: {
        months: M12,
        values: [3050, 3120, 3210, 3290, 3380, 3470, 3590, 3640, 3690, 3740, 3780, 3812],
      },
      newListingsMonthly: 1418,
      newListingsYoY: 0.06,
      monthsSupply: 5.2,
      monthsSupplyTrend: {
        months: M12,
        values: [3.6, 3.8, 4.0, 4.2, 4.3, 4.5, 4.7, 4.8, 5.0, 5.1, 5.1, 5.2],
      },
      medianDom: 52,
      medianDomTrend: {
        months: M12,
        values: [38, 39, 41, 42, 44, 45, 47, 48, 49, 50, 51, 52],
      },
      pctPriceReductions: 0.38,
      permits1Unit12mo: 3186,
      permits24Unit12mo: 124,
      permits5plus12mo: 942,
      permitsTrend: {
        months: M12,
        values: [298, 312, 295, 270, 264, 251, 248, 232, 219, 210, 198, 189],
      },
    },
    pricing: {
      medianListPrice: 285_000,
      medianSalePrice: 272_400,
      saleToListRatio: 0.972,
      pricePerSqftList: 152,
      pricePerSqftSold: 147,
      salePriceYoY: 0.014,
      salePriceCagr3y: 0.038,
      pendingSales: 728,
      closedSales: 689,
      salePriceTrend: {
        months: M12,
        values: [
          268_500, 269_200, 270_100, 270_800, 271_300, 271_700, 272_000, 272_100, 272_200, 272_300,
          272_350, 272_400,
        ],
      },
    },
    demo: {
      population: 870_569,
      households: 332_410,
      medianIncome: 62_414,
      ownerOccupiedPct: 0.628,
      renterOccupiedPct: 0.372,
      medianHomeValue: 220_300,
      medianGrossRent: 1_054,
      rentToIncome: 0.203,
      popGrowth5y: 0.018,
      unemploymentRate: 0.041,
    },
    freshness: [
      { source: "Census ACS 5-yr (2019-2023)", updatedAt: "2025-12-19" },
      { source: "Realtor.com Economic Research", updatedAt: "2026-04-15" },
      { source: "BLS LAUS", updatedAt: "2026-04-22" },
      { source: "Census BPS", updatedAt: "2026-04-10" },
    ],
  },
  // ===== Birmingham-Hoover MSA =====
  "13820": {
    geo: GEOGRAPHIES.find((g) => g.geoid === "13820")!,
    signals: {
      liquidityScore: 58,
      demandPressure: 6,
      distressIndicator: 41,
      marketTier: "B",
      rationale: {
        liquidity: "Months supply 3.9 (balanced); median DOM 41d holding steady.",
        demand: "Sale prices +3.1% YoY, sale-to-list 98.4%; pending sales +4% QoQ.",
        distress: "Price reductions 28% of active — moderate; permits flat YoY.",
        tier: "Tier B: solid mid-tier; standard ARV haircuts apply.",
      },
    },
    supply: {
      activeListings: 4920,
      activeListingsTrend: { months: M12, values: [4200, 4280, 4350, 4420, 4500, 4580, 4660, 4720, 4780, 4830, 4880, 4920] },
      newListingsMonthly: 1865,
      newListingsYoY: 0.03,
      monthsSupply: 3.9,
      monthsSupplyTrend: { months: M12, values: [3.5, 3.5, 3.6, 3.6, 3.7, 3.7, 3.8, 3.8, 3.8, 3.9, 3.9, 3.9] },
      medianDom: 41,
      medianDomTrend: { months: M12, values: [39, 39, 40, 40, 40, 41, 41, 41, 41, 41, 41, 41] },
      pctPriceReductions: 0.28,
      permits1Unit12mo: 4218,
      permits24Unit12mo: 198,
      permits5plus12mo: 1380,
      permitsTrend: { months: M12, values: [365, 350, 348, 352, 360, 358, 355, 348, 352, 360, 354, 358] },
    },
    pricing: {
      medianListPrice: 308_000,
      medianSalePrice: 296_300,
      saleToListRatio: 0.984,
      pricePerSqftList: 168,
      pricePerSqftSold: 164,
      salePriceYoY: 0.031,
      salePriceCagr3y: 0.052,
      pendingSales: 1102,
      closedSales: 1058,
      salePriceTrend: {
        months: M12,
        values: [287_400, 288_100, 289_300, 290_500, 291_700, 292_500, 293_400, 294_200, 295_000, 295_500, 295_900, 296_300],
      },
    },
    demo: {
      population: 1_115_289,
      households: 449_872,
      medianIncome: 65_207,
      ownerOccupiedPct: 0.681,
      renterOccupiedPct: 0.319,
      medianHomeValue: 234_500,
      medianGrossRent: 1_098,
      rentToIncome: 0.202,
      popGrowth5y: 0.005,
      unemploymentRate: 0.029,
    },
    freshness: [
      { source: "Census ACS 5-yr (2019-2023)", updatedAt: "2025-12-19" },
      { source: "Realtor.com Economic Research", updatedAt: "2026-04-15" },
      { source: "BLS LAUS", updatedAt: "2026-04-22" },
      { source: "Census BPS", updatedAt: "2026-04-10" },
    ],
  },
  // ===== Memphis MSA =====
  "32820": {
    geo: GEOGRAPHIES.find((g) => g.geoid === "32820")!,
    signals: {
      liquidityScore: 36,
      demandPressure: -14,
      distressIndicator: 64,
      marketTier: "C",
      rationale: {
        liquidity: "Months supply 5.7; DOM 58d and rising.",
        demand: "Sale prices flat YoY; pending sales -6% QoQ.",
        distress: "42% price reductions; permits -15% YoY.",
        tier: "Tier C: caution — price cut frequency elevated, permit pullback signals builder pessimism.",
      },
    },
    supply: {
      activeListings: 5610,
      activeListingsTrend: { months: M12, values: [4400, 4520, 4650, 4790, 4910, 5050, 5180, 5290, 5400, 5490, 5560, 5610] },
      newListingsMonthly: 1962,
      newListingsYoY: 0.09,
      monthsSupply: 5.7,
      monthsSupplyTrend: { months: M12, values: [4.0, 4.2, 4.4, 4.6, 4.8, 5.0, 5.2, 5.4, 5.5, 5.6, 5.6, 5.7] },
      medianDom: 58,
      medianDomTrend: { months: M12, values: [42, 44, 46, 48, 50, 52, 54, 55, 56, 57, 57, 58] },
      pctPriceReductions: 0.42,
      permits1Unit12mo: 3892,
      permits24Unit12mo: 165,
      permits5plus12mo: 1124,
      permitsTrend: { months: M12, values: [380, 365, 348, 335, 322, 308, 295, 282, 270, 258, 245, 232] },
    },
    pricing: {
      medianListPrice: 268_000,
      medianSalePrice: 254_800,
      saleToListRatio: 0.951,
      pricePerSqftList: 138,
      pricePerSqftSold: 132,
      salePriceYoY: 0.002,
      salePriceCagr3y: 0.027,
      pendingSales: 932,
      closedSales: 868,
      salePriceTrend: {
        months: M12,
        values: [254_300, 254_500, 254_400, 254_700, 254_900, 254_800, 254_900, 255_000, 254_900, 254_800, 254_800, 254_800],
      },
    },
    demo: {
      population: 1_335_674,
      households: 502_311,
      medianIncome: 58_148,
      ownerOccupiedPct: 0.602,
      renterOccupiedPct: 0.398,
      medianHomeValue: 186_400,
      medianGrossRent: 1_022,
      rentToIncome: 0.211,
      popGrowth5y: -0.004,
      unemploymentRate: 0.046,
    },
    freshness: [
      { source: "Census ACS 5-yr (2019-2023)", updatedAt: "2025-12-19" },
      { source: "Realtor.com Economic Research", updatedAt: "2026-04-15" },
      { source: "BLS LAUS", updatedAt: "2026-04-22" },
      { source: "Census BPS", updatedAt: "2026-04-10" },
    ],
  },
  // ===== Jackson MSA =====
  "27140": {
    geo: GEOGRAPHIES.find((g) => g.geoid === "27140")!,
    signals: {
      liquidityScore: 34,
      demandPressure: -11,
      distressIndicator: 61,
      marketTier: "D",
      rationale: {
        liquidity: "Thin liquidity — months supply 6.1, DOM 64d.",
        demand: "Sale price -0.9% YoY; population -0.3% 5-yr.",
        distress: "44% price reductions, permits -18% YoY.",
        tier: "Tier D: elevated credit risk. Recommend stricter LTC and ARV haircut > 12%.",
      },
    },
    supply: {
      activeListings: 2410,
      activeListingsTrend: { months: M12, values: [1980, 2030, 2080, 2120, 2170, 2210, 2260, 2300, 2340, 2370, 2390, 2410] },
      newListingsMonthly: 798,
      newListingsYoY: 0.08,
      monthsSupply: 6.1,
      monthsSupplyTrend: { months: M12, values: [4.4, 4.6, 4.8, 5.0, 5.2, 5.4, 5.5, 5.7, 5.8, 5.9, 6.0, 6.1] },
      medianDom: 64,
      medianDomTrend: { months: M12, values: [48, 50, 52, 54, 56, 58, 59, 60, 61, 62, 63, 64] },
      pctPriceReductions: 0.44,
      permits1Unit12mo: 1742,
      permits24Unit12mo: 58,
      permits5plus12mo: 312,
      permitsTrend: { months: M12, values: [172, 165, 158, 150, 142, 135, 128, 122, 116, 110, 104, 98] },
    },
    pricing: {
      medianListPrice: 232_000,
      medianSalePrice: 218_500,
      saleToListRatio: 0.942,
      pricePerSqftList: 122,
      pricePerSqftSold: 117,
      salePriceYoY: -0.009,
      salePriceCagr3y: 0.014,
      pendingSales: 412,
      closedSales: 388,
      salePriceTrend: {
        months: M12,
        values: [221_000, 220_500, 220_200, 219_800, 219_400, 219_200, 219_000, 218_800, 218_700, 218_600, 218_550, 218_500],
      },
    },
    demo: {
      population: 591_978,
      households: 222_018,
      medianIncome: 53_802,
      ownerOccupiedPct: 0.671,
      renterOccupiedPct: 0.329,
      medianHomeValue: 168_900,
      medianGrossRent: 962,
      rentToIncome: 0.214,
      popGrowth5y: -0.003,
      unemploymentRate: 0.038,
    },
    freshness: [
      { source: "Census ACS 5-yr (2019-2023)", updatedAt: "2025-12-19" },
      { source: "Realtor.com Economic Research", updatedAt: "2026-04-15" },
      { source: "BLS LAUS", updatedAt: "2026-04-22" },
      { source: "Census BPS", updatedAt: "2026-04-10" },
    ],
  },
  // ===== Mobile MSA =====
  "33660": {
    geo: GEOGRAPHIES.find((g) => g.geoid === "33660")!,
    signals: {
      liquidityScore: 49,
      demandPressure: -2,
      distressIndicator: 47,
      marketTier: "C",
      rationale: {
        liquidity: "Months supply 4.6; DOM 47d steady.",
        demand: "Sale prices +1.8% YoY; pending sales flat.",
        distress: "33% price reductions; permits -4% YoY.",
        tier: "Tier C: borderline B/C — improving demographics offset by softening pricing.",
      },
    },
    supply: {
      activeListings: 2240,
      activeListingsTrend: { months: M12, values: [1860, 1900, 1950, 1990, 2030, 2070, 2110, 2150, 2180, 2210, 2230, 2240] },
      newListingsMonthly: 798,
      newListingsYoY: 0.04,
      monthsSupply: 4.6,
      monthsSupplyTrend: { months: M12, values: [3.8, 3.9, 4.0, 4.1, 4.2, 4.3, 4.4, 4.4, 4.5, 4.5, 4.6, 4.6] },
      medianDom: 47,
      medianDomTrend: { months: M12, values: [43, 43, 44, 44, 45, 45, 46, 46, 46, 47, 47, 47] },
      pctPriceReductions: 0.33,
      permits1Unit12mo: 1612,
      permits24Unit12mo: 42,
      permits5plus12mo: 286,
      permitsTrend: { months: M12, values: [148, 142, 138, 138, 140, 142, 138, 134, 132, 132, 134, 132] },
    },
    pricing: {
      medianListPrice: 254_000,
      medianSalePrice: 244_100,
      saleToListRatio: 0.961,
      pricePerSqftList: 134,
      pricePerSqftSold: 129,
      salePriceYoY: 0.018,
      salePriceCagr3y: 0.034,
      pendingSales: 392,
      closedSales: 376,
      salePriceTrend: {
        months: M12,
        values: [240_100, 240_700, 241_300, 241_900, 242_400, 242_800, 243_100, 243_400, 243_700, 243_900, 244_000, 244_100],
      },
    },
    demo: {
      population: 411_407,
      households: 162_018,
      medianIncome: 56_321,
      ownerOccupiedPct: 0.691,
      renterOccupiedPct: 0.309,
      medianHomeValue: 174_200,
      medianGrossRent: 962,
      rentToIncome: 0.205,
      popGrowth5y: 0.003,
      unemploymentRate: 0.035,
    },
    freshness: [
      { source: "Census ACS 5-yr (2019-2023)", updatedAt: "2025-12-19" },
      { source: "Realtor.com Economic Research", updatedAt: "2026-04-15" },
      { source: "BLS LAUS", updatedAt: "2026-04-22" },
      { source: "Census BPS", updatedAt: "2026-04-10" },
    ],
  },
  // ===== Shreveport MSA =====
  "43340": {
    geo: GEOGRAPHIES.find((g) => g.geoid === "43340")!,
    signals: {
      liquidityScore: 31,
      demandPressure: -16,
      distressIndicator: 67,
      marketTier: "D",
      rationale: {
        liquidity: "Months supply 6.4; DOM 71d and climbing.",
        demand: "Sale price -1.4% YoY; population -0.6% 5-yr.",
        distress: "47% price reductions; permits -22% YoY — material builder pullback.",
        tier:
          "Tier D: avoid speculative flips; restrict to under-median acquisitions with conservative ARV.",
      },
    },
    supply: {
      activeListings: 1820,
      activeListingsTrend: { months: M12, values: [1480, 1520, 1560, 1600, 1640, 1680, 1720, 1750, 1780, 1800, 1810, 1820] },
      newListingsMonthly: 612,
      newListingsYoY: 0.07,
      monthsSupply: 6.4,
      monthsSupplyTrend: { months: M12, values: [4.6, 4.8, 5.0, 5.2, 5.4, 5.6, 5.8, 5.9, 6.1, 6.2, 6.3, 6.4] },
      medianDom: 71,
      medianDomTrend: { months: M12, values: [54, 56, 58, 60, 62, 64, 65, 67, 68, 69, 70, 71] },
      pctPriceReductions: 0.47,
      permits1Unit12mo: 1108,
      permits24Unit12mo: 38,
      permits5plus12mo: 184,
      permitsTrend: { months: M12, values: [110, 102, 96, 90, 84, 80, 76, 72, 68, 64, 60, 56] },
    },
    pricing: {
      medianListPrice: 198_000,
      medianSalePrice: 186_400,
      saleToListRatio: 0.941,
      pricePerSqftList: 108,
      pricePerSqftSold: 104,
      salePriceYoY: -0.014,
      salePriceCagr3y: 0.009,
      pendingSales: 318,
      closedSales: 296,
      salePriceTrend: {
        months: M12,
        values: [189_500, 189_000, 188_400, 188_000, 187_600, 187_200, 187_000, 186_800, 186_700, 186_600, 186_500, 186_400],
      },
    },
    demo: {
      population: 392_302,
      households: 152_811,
      medianIncome: 51_204,
      ownerOccupiedPct: 0.654,
      renterOccupiedPct: 0.346,
      medianHomeValue: 154_700,
      medianGrossRent: 924,
      rentToIncome: 0.217,
      popGrowth5y: -0.006,
      unemploymentRate: 0.044,
    },
    freshness: [
      { source: "Census ACS 5-yr (2019-2023)", updatedAt: "2025-12-19" },
      { source: "Realtor.com Economic Research", updatedAt: "2026-04-15" },
      { source: "BLS LAUS", updatedAt: "2026-04-22" },
      { source: "Census BPS", updatedAt: "2026-04-10" },
    ],
  },
};

/* ZIP-level snapshot for 70809 (East Baton Rouge — affluent suburban core) */
SNAPSHOTS["70809"] = {
  geo: GEOGRAPHIES.find((g) => g.geoid === "70809")!,
  signals: {
    liquidityScore: 56,
    demandPressure: 4,
    distressIndicator: 39,
    marketTier: "B",
    rationale: {
      liquidity: "Months supply 4.1; DOM 38d — outperforms MSA aggregate.",
      demand: "Sale prices +2.6% YoY; pending sales +3% QoQ.",
      distress: "Price reductions 29% — below MSA's 38%.",
      tier: "Tier B: stronger ZIP within Tier C MSA. Standard credit terms.",
    },
  },
  supply: {
    activeListings: 168,
    activeListingsTrend: { months: M12, values: [142, 146, 148, 152, 156, 158, 160, 162, 164, 166, 167, 168] },
    newListingsMonthly: 64,
    newListingsYoY: 0.04,
    monthsSupply: 4.1,
    monthsSupplyTrend: { months: M12, values: [3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.9, 4.0, 4.0, 4.0, 4.1, 4.1] },
    medianDom: 38,
    medianDomTrend: { months: M12, values: [32, 33, 34, 34, 35, 36, 36, 37, 37, 38, 38, 38] },
    pctPriceReductions: 0.29,
    permits1Unit12mo: 124,
    permits24Unit12mo: 6,
    permits5plus12mo: 0,
    permitsTrend: { months: M12, values: [12, 11, 11, 10, 10, 11, 10, 11, 10, 10, 9, 9] },
  },
  pricing: {
    medianListPrice: 348_000,
    medianSalePrice: 334_500,
    saleToListRatio: 0.978,
    pricePerSqftList: 178,
    pricePerSqftSold: 172,
    salePriceYoY: 0.026,
    salePriceCagr3y: 0.046,
    pendingSales: 41,
    closedSales: 39,
    salePriceTrend: {
      months: M12,
      values: [326_100, 327_300, 328_500, 329_700, 330_900, 331_800, 332_600, 333_300, 333_900, 334_300, 334_400, 334_500],
    },
  },
  demo: {
    population: 23_185,
    households: 9_842,
    medianIncome: 78_412,
    ownerOccupiedPct: 0.704,
    renterOccupiedPct: 0.296,
    medianHomeValue: 296_400,
    medianGrossRent: 1_312,
    rentToIncome: 0.201,
    popGrowth5y: 0.022,
    unemploymentRate: 0.032,
  },
  freshness: [
    { source: "Census ACS 5-yr (2019-2023)", updatedAt: "2025-12-19" },
    { source: "Realtor.com Economic Research", updatedAt: "2026-04-15" },
    { source: "BLS LAUS", updatedAt: "2026-04-22" },
    { source: "Census BPS", updatedAt: "2026-04-10" },
  ],
};

export const getSnapshot = (geoid: string): GeoSnapshot | undefined => SNAPSHOTS[geoid];
export const allSnapshots = (): GeoSnapshot[] => Object.values(SNAPSHOTS);
export const findGeo = (geoid: string): Geography | undefined =>
  GEOGRAPHIES.find((g) => g.geoid === geoid);
