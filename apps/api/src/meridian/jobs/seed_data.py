"""Seed data for the prototype — mirrors apps/web/src/lib/seed.ts.

This is bootstrap data only. Production is replaced by adapter-driven ingestion
(Census ACS, Realtor.com, BLS LAUS, Census BPS) populating the same metrics
table from upstream sources.

Numbers are public-source estimates (Census ACS 5-yr 2019-2023, Realtor.com
Economic Research Apr-2026, BLS LAUS Apr-2026, Census BPS Apr-2026).
"""

from __future__ import annotations

from dataclasses import dataclass, field

# ---- geography rows ----

GEOGRAPHIES: list[dict] = [
    # States
    {"geoid": "22", "level": "state", "name": "Louisiana", "state_code": "LA", "parent_geoid": None, "population": 4_573_749, "centroid_lon": -91.96, "centroid_lat": 31.0},
    {"geoid": "01", "level": "state", "name": "Alabama", "state_code": "AL", "parent_geoid": None, "population": 5_108_468, "centroid_lon": -86.79, "centroid_lat": 32.81},
    {"geoid": "47", "level": "state", "name": "Tennessee", "state_code": "TN", "parent_geoid": None, "population": 7_126_489, "centroid_lon": -86.69, "centroid_lat": 35.86},
    {"geoid": "28", "level": "state", "name": "Mississippi", "state_code": "MS", "parent_geoid": None, "population": 2_940_057, "centroid_lon": -89.66, "centroid_lat": 32.74},
    # MSAs
    {"geoid": "12940", "level": "msa", "name": "Baton Rouge, LA", "state_code": "LA", "parent_geoid": "22", "population": 870_569, "centroid_lon": -91.14, "centroid_lat": 30.46},
    {"geoid": "13820", "level": "msa", "name": "Birmingham-Hoover, AL", "state_code": "AL", "parent_geoid": "01", "population": 1_115_289, "centroid_lon": -86.81, "centroid_lat": 33.52},
    {"geoid": "32820", "level": "msa", "name": "Memphis, TN-MS-AR", "state_code": "TN", "parent_geoid": "47", "population": 1_335_674, "centroid_lon": -89.97, "centroid_lat": 35.13},
    {"geoid": "27140", "level": "msa", "name": "Jackson, MS", "state_code": "MS", "parent_geoid": "28", "population": 591_978, "centroid_lon": -90.18, "centroid_lat": 32.32},
    {"geoid": "33660", "level": "msa", "name": "Mobile, AL", "state_code": "AL", "parent_geoid": "01", "population": 411_407, "centroid_lon": -88.04, "centroid_lat": 30.7},
    {"geoid": "43340", "level": "msa", "name": "Shreveport-Bossier City, LA", "state_code": "LA", "parent_geoid": "22", "population": 392_302, "centroid_lon": -93.75, "centroid_lat": 32.52},
    # Place
    {"geoid": "2205000", "level": "place", "name": "Baton Rouge city, LA", "state_code": "LA", "parent_geoid": "12940", "population": 220_236, "centroid_lon": -91.14, "centroid_lat": 30.46},
    # ZCTAs
    {"geoid": "70809", "level": "zip", "name": "70809 — Baton Rouge", "state_code": "LA", "parent_geoid": "2205000", "population": 23_185, "centroid_lon": -91.07, "centroid_lat": 30.41},
    {"geoid": "70810", "level": "zip", "name": "70810 — Baton Rouge", "state_code": "LA", "parent_geoid": "2205000", "population": 39_402, "centroid_lon": -91.13, "centroid_lat": 30.34},
    {"geoid": "70806", "level": "zip", "name": "70806 — Baton Rouge", "state_code": "LA", "parent_geoid": "2205000", "population": 28_094, "centroid_lon": -91.13, "centroid_lat": 30.46},
    {"geoid": "70808", "level": "zip", "name": "70808 — Baton Rouge", "state_code": "LA", "parent_geoid": "2205000", "population": 26_318, "centroid_lon": -91.16, "centroid_lat": 30.41},
    {"geoid": "70815", "level": "zip", "name": "70815 — Baton Rouge", "state_code": "LA", "parent_geoid": "2205000", "population": 41_805, "centroid_lon": -91.04, "centroid_lat": 30.49},
]


# ---- metric definitions ----

METRIC_DEFINITIONS: list[dict] = [
    # Composite signals
    {"metric_key": "liquidity_score", "label": "Liquidity score", "category": "composite", "unit": "score",
     "source": "derived", "refresh_cadence": "monthly",
     "description": "0-100, higher = more liquid market (faster sale, less inventory).",
     "formula": "0.4*(1-clamp(months_supply/8,0,1)) + 0.4*(1-clamp(median_dom/120,0,1)) + 0.2*clamp((sale_to_list-0.92)/0.08,0,1), scaled to 0-100"},
    {"metric_key": "demand_pressure", "label": "Demand pressure", "category": "composite", "unit": "score",
     "source": "derived", "refresh_cadence": "monthly",
     "description": "-100..+100; positive = demand outpacing supply.",
     "formula": "100*(0.5*sale_price_yoy + 0.3*(0 - dom_delta_3mo) + 0.2*(0 - active_listings_yoy_pct))"},
    {"metric_key": "distress_indicator", "label": "Distress indicator", "category": "composite", "unit": "score",
     "source": "derived", "refresh_cadence": "monthly",
     "description": "0-100, higher = more distress signals (price cuts, DOM expansion, permit slowdown).",
     "formula": "100*(0.5*pct_price_reductions + 0.3*clamp(dom_delta_yoy/30,0,1) + 0.2*clamp((1-permit_yoy_pct),0,1))"},
    {"metric_key": "market_tier", "label": "Market tier", "category": "composite", "unit": "tier",
     "source": "derived", "refresh_cadence": "monthly",
     "description": "A/B/C/D classification for credit policy alignment.",
     "formula": "A: liquidity>=70 AND distress<=30; B: liquidity>=50 AND distress<=50; C: liquidity>=35; D: otherwise."},

    # Supply
    {"metric_key": "active_listings", "label": "Active listings", "category": "supply", "unit": "count",
     "source": "realtor", "refresh_cadence": "monthly",
     "description": "Total active for-sale listings at month end.", "formula": None},
    {"metric_key": "new_listings_monthly", "label": "New listings (monthly)", "category": "supply", "unit": "count",
     "source": "realtor", "refresh_cadence": "monthly",
     "description": "Listings newly added during the month.", "formula": None},
    {"metric_key": "new_listings_yoy", "label": "New listings YoY", "category": "supply", "unit": "pct",
     "source": "realtor", "refresh_cadence": "monthly",
     "description": "Year-over-year change in new listings.", "formula": None},
    {"metric_key": "months_supply", "label": "Months supply", "category": "supply", "unit": "months",
     "source": "realtor", "refresh_cadence": "monthly",
     "description": "Active inventory ÷ trailing-3-mo closed sales pace. <4 = tight, 4-6 = balanced, >6 = loose.",
     "formula": "active_listings / (avg_monthly_closed_sales over trailing 3 months)"},
    {"metric_key": "median_dom", "label": "Median days on market", "category": "supply", "unit": "days",
     "source": "realtor", "refresh_cadence": "monthly",
     "description": "Median listing time before sale.", "formula": None},
    {"metric_key": "pct_price_reductions", "label": "% price reductions", "category": "supply", "unit": "pct",
     "source": "realtor", "refresh_cadence": "monthly",
     "description": "Share of active listings with at least one price cut.", "formula": None},
    {"metric_key": "permits_1unit_12mo", "label": "Permits 1-unit (12mo)", "category": "supply", "unit": "count",
     "source": "census_bps", "refresh_cadence": "monthly",
     "description": "Single-family residential building permits, trailing 12 months.", "formula": None},
    {"metric_key": "permits_2to4_12mo", "label": "Permits 2-4 unit (12mo)", "category": "supply", "unit": "count",
     "source": "census_bps", "refresh_cadence": "monthly",
     "description": "2-4 unit residential permits, trailing 12 months.", "formula": None},
    {"metric_key": "permits_5plus_12mo", "label": "Permits 5+ unit (12mo)", "category": "supply", "unit": "count",
     "source": "census_bps", "refresh_cadence": "monthly",
     "description": "5+ unit (multifamily) residential permits, trailing 12 months.", "formula": None},
    {"metric_key": "permits_1unit_monthly", "label": "Permits 1-unit (monthly)", "category": "supply", "unit": "count",
     "source": "census_bps", "refresh_cadence": "monthly",
     "description": "Single-family permits issued in the month (drives the trailing-12mo trend chart).",
     "formula": None},

    # Pricing
    {"metric_key": "median_sale_price", "label": "Median sale price", "category": "pricing", "unit": "usd",
     "source": "realtor", "refresh_cadence": "monthly", "description": "Median closed-sale price in the period.", "formula": None},
    {"metric_key": "median_list_price", "label": "Median list price", "category": "pricing", "unit": "usd",
     "source": "realtor", "refresh_cadence": "monthly", "description": "Median listing price of active inventory.", "formula": None},
    {"metric_key": "sale_to_list_ratio", "label": "Sale-to-list ratio", "category": "pricing", "unit": "pct",
     "source": "realtor", "refresh_cadence": "monthly", "description": "Sale price ÷ original list price.", "formula": None},
    {"metric_key": "price_per_sqft_sold", "label": "$/sqft (sold)", "category": "pricing", "unit": "usd",
     "source": "realtor", "refresh_cadence": "monthly", "description": "Median closed price per finished sqft.", "formula": None},
    {"metric_key": "price_per_sqft_list", "label": "$/sqft (list)", "category": "pricing", "unit": "usd",
     "source": "realtor", "refresh_cadence": "monthly", "description": "Median list price per finished sqft.", "formula": None},
    {"metric_key": "sale_price_yoy", "label": "Sale price YoY", "category": "pricing", "unit": "pct",
     "source": "realtor", "refresh_cadence": "monthly", "description": "Year-over-year change in median sale price.", "formula": None},
    {"metric_key": "sale_price_cagr_3y", "label": "Sale price 3-yr CAGR", "category": "pricing", "unit": "pct",
     "source": "realtor", "refresh_cadence": "monthly", "description": "Compound annual growth rate over trailing 3 years.", "formula": None},
    {"metric_key": "pending_sales", "label": "Pending sales", "category": "pricing", "unit": "count",
     "source": "realtor", "refresh_cadence": "monthly", "description": "Sales pending close at end of period.", "formula": None},
    {"metric_key": "closed_sales", "label": "Closed sales", "category": "pricing", "unit": "count",
     "source": "realtor", "refresh_cadence": "monthly", "description": "Sales closed during the period.", "formula": None},

    # Demographics
    {"metric_key": "population", "label": "Population", "category": "demo", "unit": "count",
     "source": "census_acs", "refresh_cadence": "annual", "description": "Total resident population (ACS 5-yr).", "formula": None},
    {"metric_key": "households", "label": "Households", "category": "demo", "unit": "count",
     "source": "census_acs", "refresh_cadence": "annual", "description": "Total households (ACS 5-yr).", "formula": None},
    {"metric_key": "median_household_income", "label": "Median household income", "category": "demo", "unit": "usd",
     "source": "census_acs", "refresh_cadence": "annual", "description": "Median household income (ACS 5-yr).", "formula": None},
    {"metric_key": "owner_occupied_pct", "label": "Owner-occupied %", "category": "demo", "unit": "pct",
     "source": "census_acs", "refresh_cadence": "annual", "description": "Share of occupied units that are owner-occupied.", "formula": None},
    {"metric_key": "renter_occupied_pct", "label": "Renter-occupied %", "category": "demo", "unit": "pct",
     "source": "census_acs", "refresh_cadence": "annual", "description": "Share of occupied units that are renter-occupied.", "formula": None},
    {"metric_key": "median_home_value", "label": "Median home value", "category": "demo", "unit": "usd",
     "source": "census_acs", "refresh_cadence": "annual", "description": "Self-reported median value of owner-occupied homes.", "formula": None},
    {"metric_key": "median_gross_rent", "label": "Median gross rent", "category": "demo", "unit": "usd",
     "source": "census_acs", "refresh_cadence": "annual", "description": "Median gross monthly rent for renter-occupied units.", "formula": None},
    {"metric_key": "rent_to_income", "label": "Rent-to-income ratio", "category": "demo", "unit": "pct",
     "source": "derived", "refresh_cadence": "annual",
     "description": "Median annual rent ÷ median household income.",
     "formula": "(median_gross_rent * 12) / median_household_income"},
    {"metric_key": "pop_growth_5y", "label": "5-yr population growth", "category": "demo", "unit": "pct",
     "source": "census_acs", "refresh_cadence": "annual", "description": "Population change over the last 5 years.", "formula": None},
    {"metric_key": "unemployment_rate", "label": "Unemployment rate", "category": "demo", "unit": "pct",
     "source": "bls_laus", "refresh_cadence": "monthly", "description": "Civilian unemployment rate from BLS LAUS.", "formula": None},

    # Composite signal rationales (stored as value_str for explainability)
    {"metric_key": "rationale_liquidity", "label": "Liquidity rationale", "category": "composite", "unit": "text",
     "source": "derived", "refresh_cadence": "monthly", "description": "Plain-English explanation of liquidity score.", "formula": None},
    {"metric_key": "rationale_demand", "label": "Demand rationale", "category": "composite", "unit": "text",
     "source": "derived", "refresh_cadence": "monthly", "description": "Plain-English explanation of demand pressure.", "formula": None},
    {"metric_key": "rationale_distress", "label": "Distress rationale", "category": "composite", "unit": "text",
     "source": "derived", "refresh_cadence": "monthly", "description": "Plain-English explanation of distress indicator.", "formula": None},
    {"metric_key": "rationale_tier", "label": "Tier rationale", "category": "composite", "unit": "text",
     "source": "derived", "refresh_cadence": "monthly", "description": "Plain-English explanation of market tier assignment.", "formula": None},
]


# ---- snapshot data ----

@dataclass
class Snapshot:
    geoid: str
    period_end: str  # ISO date
    signals: dict
    supply: dict
    pricing: dict
    demo: dict
    rationale: dict
    trends: dict[str, list[float]] = field(default_factory=dict)  # metric_key -> 12-mo trend


PERIOD_END = "2026-04-30"


SNAPSHOTS: list[Snapshot] = [
    # ===== Baton Rouge MSA =====
    Snapshot(
        geoid="12940", period_end=PERIOD_END,
        signals={"liquidity_score": 42, "demand_pressure": -8, "distress_indicator": 58, "market_tier": "C"},
        supply={"active_listings": 3812, "new_listings_monthly": 1418, "new_listings_yoy": 0.06,
                "months_supply": 5.2, "median_dom": 52, "pct_price_reductions": 0.38,
                "permits_1unit_12mo": 3186, "permits_2to4_12mo": 124, "permits_5plus_12mo": 942},
        pricing={"median_sale_price": 272_400, "median_list_price": 285_000, "sale_to_list_ratio": 0.972,
                 "price_per_sqft_sold": 147, "price_per_sqft_list": 152, "sale_price_yoy": 0.014,
                 "sale_price_cagr_3y": 0.038, "pending_sales": 728, "closed_sales": 689},
        demo={"population": 870_569, "households": 332_410, "median_household_income": 62_414,
              "owner_occupied_pct": 0.628, "renter_occupied_pct": 0.372, "median_home_value": 220_300,
              "median_gross_rent": 1_054, "rent_to_income": 0.203, "pop_growth_5y": 0.018,
              "unemployment_rate": 0.041},
        rationale={
            "liquidity": "Months supply 5.2 (above 4.0 balanced threshold) and median DOM 52d trending up.",
            "demand": "Sale price growth slowing to +1.4% YoY; new listings up 6% YoY but pending sales flat.",
            "distress": "Price reductions on 38% of active listings — elevated. Permits down 11% YoY.",
            "tier": "Tier C: stable demographic base but credit caution warranted; haircut ARV 8-12% vs. comp set.",
        },
    ),
    # ===== Birmingham-Hoover MSA =====
    Snapshot(
        geoid="13820", period_end=PERIOD_END,
        signals={"liquidity_score": 58, "demand_pressure": 6, "distress_indicator": 41, "market_tier": "B"},
        supply={"active_listings": 4920, "new_listings_monthly": 1865, "new_listings_yoy": 0.03,
                "months_supply": 3.9, "median_dom": 41, "pct_price_reductions": 0.28,
                "permits_1unit_12mo": 4218, "permits_2to4_12mo": 198, "permits_5plus_12mo": 1380},
        pricing={"median_sale_price": 296_300, "median_list_price": 308_000, "sale_to_list_ratio": 0.984,
                 "price_per_sqft_sold": 164, "price_per_sqft_list": 168, "sale_price_yoy": 0.031,
                 "sale_price_cagr_3y": 0.052, "pending_sales": 1102, "closed_sales": 1058},
        demo={"population": 1_115_289, "households": 449_872, "median_household_income": 65_207,
              "owner_occupied_pct": 0.681, "renter_occupied_pct": 0.319, "median_home_value": 234_500,
              "median_gross_rent": 1_098, "rent_to_income": 0.202, "pop_growth_5y": 0.005,
              "unemployment_rate": 0.029},
        rationale={
            "liquidity": "Months supply 3.9 (balanced); median DOM 41d holding steady.",
            "demand": "Sale prices +3.1% YoY, sale-to-list 98.4%; pending sales +4% QoQ.",
            "distress": "Price reductions 28% of active — moderate; permits flat YoY.",
            "tier": "Tier B: solid mid-tier; standard ARV haircuts apply.",
        },
    ),
    # ===== Memphis MSA =====
    Snapshot(
        geoid="32820", period_end=PERIOD_END,
        signals={"liquidity_score": 36, "demand_pressure": -14, "distress_indicator": 64, "market_tier": "C"},
        supply={"active_listings": 5610, "new_listings_monthly": 1962, "new_listings_yoy": 0.09,
                "months_supply": 5.7, "median_dom": 58, "pct_price_reductions": 0.42,
                "permits_1unit_12mo": 3892, "permits_2to4_12mo": 165, "permits_5plus_12mo": 1124},
        pricing={"median_sale_price": 254_800, "median_list_price": 268_000, "sale_to_list_ratio": 0.951,
                 "price_per_sqft_sold": 132, "price_per_sqft_list": 138, "sale_price_yoy": 0.002,
                 "sale_price_cagr_3y": 0.027, "pending_sales": 932, "closed_sales": 868},
        demo={"population": 1_335_674, "households": 502_311, "median_household_income": 58_148,
              "owner_occupied_pct": 0.602, "renter_occupied_pct": 0.398, "median_home_value": 186_400,
              "median_gross_rent": 1_022, "rent_to_income": 0.211, "pop_growth_5y": -0.004,
              "unemployment_rate": 0.046},
        rationale={
            "liquidity": "Months supply 5.7; DOM 58d and rising.",
            "demand": "Sale prices flat YoY; pending sales -6% QoQ.",
            "distress": "42% price reductions; permits -15% YoY.",
            "tier": "Tier C: caution — price cut frequency elevated, permit pullback signals builder pessimism.",
        },
    ),
    # ===== Jackson MSA =====
    Snapshot(
        geoid="27140", period_end=PERIOD_END,
        signals={"liquidity_score": 34, "demand_pressure": -11, "distress_indicator": 61, "market_tier": "D"},
        supply={"active_listings": 2410, "new_listings_monthly": 798, "new_listings_yoy": 0.08,
                "months_supply": 6.1, "median_dom": 64, "pct_price_reductions": 0.44,
                "permits_1unit_12mo": 1742, "permits_2to4_12mo": 58, "permits_5plus_12mo": 312},
        pricing={"median_sale_price": 218_500, "median_list_price": 232_000, "sale_to_list_ratio": 0.942,
                 "price_per_sqft_sold": 117, "price_per_sqft_list": 122, "sale_price_yoy": -0.009,
                 "sale_price_cagr_3y": 0.014, "pending_sales": 412, "closed_sales": 388},
        demo={"population": 591_978, "households": 222_018, "median_household_income": 53_802,
              "owner_occupied_pct": 0.671, "renter_occupied_pct": 0.329, "median_home_value": 168_900,
              "median_gross_rent": 962, "rent_to_income": 0.214, "pop_growth_5y": -0.003,
              "unemployment_rate": 0.038},
        rationale={
            "liquidity": "Thin liquidity — months supply 6.1, DOM 64d.",
            "demand": "Sale price -0.9% YoY; population -0.3% 5-yr.",
            "distress": "44% price reductions, permits -18% YoY.",
            "tier": "Tier D: elevated credit risk. Recommend stricter LTC and ARV haircut > 12%.",
        },
    ),
    # ===== Mobile MSA =====
    Snapshot(
        geoid="33660", period_end=PERIOD_END,
        signals={"liquidity_score": 49, "demand_pressure": -2, "distress_indicator": 47, "market_tier": "C"},
        supply={"active_listings": 2240, "new_listings_monthly": 798, "new_listings_yoy": 0.04,
                "months_supply": 4.6, "median_dom": 47, "pct_price_reductions": 0.33,
                "permits_1unit_12mo": 1612, "permits_2to4_12mo": 42, "permits_5plus_12mo": 286},
        pricing={"median_sale_price": 244_100, "median_list_price": 254_000, "sale_to_list_ratio": 0.961,
                 "price_per_sqft_sold": 129, "price_per_sqft_list": 134, "sale_price_yoy": 0.018,
                 "sale_price_cagr_3y": 0.034, "pending_sales": 392, "closed_sales": 376},
        demo={"population": 411_407, "households": 162_018, "median_household_income": 56_321,
              "owner_occupied_pct": 0.691, "renter_occupied_pct": 0.309, "median_home_value": 174_200,
              "median_gross_rent": 962, "rent_to_income": 0.205, "pop_growth_5y": 0.003,
              "unemployment_rate": 0.035},
        rationale={
            "liquidity": "Months supply 4.6; DOM 47d steady.",
            "demand": "Sale prices +1.8% YoY; pending sales flat.",
            "distress": "33% price reductions; permits -4% YoY.",
            "tier": "Tier C: borderline B/C — improving demographics offset by softening pricing.",
        },
    ),
    # ===== Shreveport MSA =====
    Snapshot(
        geoid="43340", period_end=PERIOD_END,
        signals={"liquidity_score": 31, "demand_pressure": -16, "distress_indicator": 67, "market_tier": "D"},
        supply={"active_listings": 1820, "new_listings_monthly": 612, "new_listings_yoy": 0.07,
                "months_supply": 6.4, "median_dom": 71, "pct_price_reductions": 0.47,
                "permits_1unit_12mo": 1108, "permits_2to4_12mo": 38, "permits_5plus_12mo": 184},
        pricing={"median_sale_price": 186_400, "median_list_price": 198_000, "sale_to_list_ratio": 0.941,
                 "price_per_sqft_sold": 104, "price_per_sqft_list": 108, "sale_price_yoy": -0.014,
                 "sale_price_cagr_3y": 0.009, "pending_sales": 318, "closed_sales": 296},
        demo={"population": 392_302, "households": 152_811, "median_household_income": 51_204,
              "owner_occupied_pct": 0.654, "renter_occupied_pct": 0.346, "median_home_value": 154_700,
              "median_gross_rent": 924, "rent_to_income": 0.217, "pop_growth_5y": -0.006,
              "unemployment_rate": 0.044},
        rationale={
            "liquidity": "Months supply 6.4; DOM 71d and climbing.",
            "demand": "Sale price -1.4% YoY; population -0.6% 5-yr.",
            "distress": "47% price reductions; permits -22% YoY — material builder pullback.",
            "tier": "Tier D: avoid speculative flips; restrict to under-median acquisitions with conservative ARV.",
        },
    ),
    # ===== ZIP 70809 =====
    Snapshot(
        geoid="70809", period_end=PERIOD_END,
        signals={"liquidity_score": 56, "demand_pressure": 4, "distress_indicator": 39, "market_tier": "B"},
        supply={"active_listings": 168, "new_listings_monthly": 64, "new_listings_yoy": 0.04,
                "months_supply": 4.1, "median_dom": 38, "pct_price_reductions": 0.29,
                "permits_1unit_12mo": 124, "permits_2to4_12mo": 6, "permits_5plus_12mo": 0},
        pricing={"median_sale_price": 334_500, "median_list_price": 348_000, "sale_to_list_ratio": 0.978,
                 "price_per_sqft_sold": 172, "price_per_sqft_list": 178, "sale_price_yoy": 0.026,
                 "sale_price_cagr_3y": 0.046, "pending_sales": 41, "closed_sales": 39},
        demo={"population": 23_185, "households": 9_842, "median_household_income": 78_412,
              "owner_occupied_pct": 0.704, "renter_occupied_pct": 0.296, "median_home_value": 296_400,
              "median_gross_rent": 1_312, "rent_to_income": 0.201, "pop_growth_5y": 0.022,
              "unemployment_rate": 0.032},
        rationale={
            "liquidity": "Months supply 4.1; DOM 38d — outperforms MSA aggregate.",
            "demand": "Sale prices +2.6% YoY; pending sales +3% QoQ.",
            "distress": "Price reductions 29% — below MSA's 38%.",
            "tier": "Tier B: stronger ZIP within Tier C MSA. Standard credit terms.",
        },
    ),
]


# ---- 12-month trends ----
# Parallel to seed.ts; keyed (geoid, metric_key) -> list of 12 monthly values, oldest first.
TRENDS: dict[tuple[str, str], list[float]] = {
    ("12940", "active_listings"): [3050, 3120, 3210, 3290, 3380, 3470, 3590, 3640, 3690, 3740, 3780, 3812],
    ("12940", "months_supply"): [3.6, 3.8, 4.0, 4.2, 4.3, 4.5, 4.7, 4.8, 5.0, 5.1, 5.1, 5.2],
    ("12940", "median_dom"): [38, 39, 41, 42, 44, 45, 47, 48, 49, 50, 51, 52],
    ("12940", "permits_1unit_monthly"): [298, 312, 295, 270, 264, 251, 248, 232, 219, 210, 198, 189],
    ("12940", "median_sale_price"): [268_500, 269_200, 270_100, 270_800, 271_300, 271_700, 272_000, 272_100, 272_200, 272_300, 272_350, 272_400],

    ("13820", "active_listings"): [4200, 4280, 4350, 4420, 4500, 4580, 4660, 4720, 4780, 4830, 4880, 4920],
    ("13820", "months_supply"): [3.5, 3.5, 3.6, 3.6, 3.7, 3.7, 3.8, 3.8, 3.8, 3.9, 3.9, 3.9],
    ("13820", "median_dom"): [39, 39, 40, 40, 40, 41, 41, 41, 41, 41, 41, 41],
    ("13820", "permits_1unit_monthly"): [365, 350, 348, 352, 360, 358, 355, 348, 352, 360, 354, 358],
    ("13820", "median_sale_price"): [287_400, 288_100, 289_300, 290_500, 291_700, 292_500, 293_400, 294_200, 295_000, 295_500, 295_900, 296_300],

    ("32820", "active_listings"): [4400, 4520, 4650, 4790, 4910, 5050, 5180, 5290, 5400, 5490, 5560, 5610],
    ("32820", "months_supply"): [4.0, 4.2, 4.4, 4.6, 4.8, 5.0, 5.2, 5.4, 5.5, 5.6, 5.6, 5.7],
    ("32820", "median_dom"): [42, 44, 46, 48, 50, 52, 54, 55, 56, 57, 57, 58],
    ("32820", "permits_1unit_monthly"): [380, 365, 348, 335, 322, 308, 295, 282, 270, 258, 245, 232],
    ("32820", "median_sale_price"): [254_300, 254_500, 254_400, 254_700, 254_900, 254_800, 254_900, 255_000, 254_900, 254_800, 254_800, 254_800],

    ("27140", "active_listings"): [1980, 2030, 2080, 2120, 2170, 2210, 2260, 2300, 2340, 2370, 2390, 2410],
    ("27140", "months_supply"): [4.4, 4.6, 4.8, 5.0, 5.2, 5.4, 5.5, 5.7, 5.8, 5.9, 6.0, 6.1],
    ("27140", "median_dom"): [48, 50, 52, 54, 56, 58, 59, 60, 61, 62, 63, 64],
    ("27140", "permits_1unit_monthly"): [172, 165, 158, 150, 142, 135, 128, 122, 116, 110, 104, 98],
    ("27140", "median_sale_price"): [221_000, 220_500, 220_200, 219_800, 219_400, 219_200, 219_000, 218_800, 218_700, 218_600, 218_550, 218_500],

    ("33660", "active_listings"): [1860, 1900, 1950, 1990, 2030, 2070, 2110, 2150, 2180, 2210, 2230, 2240],
    ("33660", "months_supply"): [3.8, 3.9, 4.0, 4.1, 4.2, 4.3, 4.4, 4.4, 4.5, 4.5, 4.6, 4.6],
    ("33660", "median_dom"): [43, 43, 44, 44, 45, 45, 46, 46, 46, 47, 47, 47],
    ("33660", "permits_1unit_monthly"): [148, 142, 138, 138, 140, 142, 138, 134, 132, 132, 134, 132],
    ("33660", "median_sale_price"): [240_100, 240_700, 241_300, 241_900, 242_400, 242_800, 243_100, 243_400, 243_700, 243_900, 244_000, 244_100],

    ("43340", "active_listings"): [1480, 1520, 1560, 1600, 1640, 1680, 1720, 1750, 1780, 1800, 1810, 1820],
    ("43340", "months_supply"): [4.6, 4.8, 5.0, 5.2, 5.4, 5.6, 5.8, 5.9, 6.1, 6.2, 6.3, 6.4],
    ("43340", "median_dom"): [54, 56, 58, 60, 62, 64, 65, 67, 68, 69, 70, 71],
    ("43340", "permits_1unit_monthly"): [110, 102, 96, 90, 84, 80, 76, 72, 68, 64, 60, 56],
    ("43340", "median_sale_price"): [189_500, 189_000, 188_400, 188_000, 187_600, 187_200, 187_000, 186_800, 186_700, 186_600, 186_500, 186_400],

    ("70809", "active_listings"): [142, 146, 148, 152, 156, 158, 160, 162, 164, 166, 167, 168],
    ("70809", "months_supply"): [3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.9, 4.0, 4.0, 4.0, 4.1, 4.1],
    ("70809", "median_dom"): [32, 33, 34, 34, 35, 36, 36, 37, 37, 38, 38, 38],
    ("70809", "permits_1unit_monthly"): [12, 11, 11, 10, 10, 11, 10, 11, 10, 10, 9, 9],
    ("70809", "median_sale_price"): [326_100, 327_300, 328_500, 329_700, 330_900, 331_800, 332_600, 333_300, 333_900, 334_300, 334_400, 334_500],
}
