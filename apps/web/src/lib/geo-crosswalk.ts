/**
 * Subset crosswalks for the seeded MSAs. Maps Census FIPS codes for counties,
 * states, and ZCTAs to our MSA/MSA-equivalent geoid.
 *
 * Production: this is replaced by HUD USPS ZIP↔county↔CBSA crosswalk and Census
 * CBSA-to-FIPS-county delineation files (loaded into Postgres as dimension tables).
 */

/** 5-digit county FIPS (state + county) -> MSA geoid */
export const COUNTY_TO_MSA: Record<string, string> = {
  // Baton Rouge MSA (12940) — full delineation
  "22005": "12940", // Ascension
  "22033": "12940", // East Baton Rouge
  "22037": "12940", // East Feliciana
  "22047": "12940", // Iberville
  "22063": "12940", // Livingston
  "22077": "12940", // Pointe Coupee
  "22091": "12940", // St. Helena
  "22121": "12940", // West Baton Rouge
  "22125": "12940", // West Feliciana

  // Birmingham-Hoover MSA (13820)
  "01007": "13820", // Bibb
  "01009": "13820", // Blount
  "01073": "13820", // Jefferson
  "01115": "13820", // St. Clair
  "01117": "13820", // Shelby
  "01125": "13820", // Tuscaloosa (delineation varies; included for visual coverage)
  "01133": "13820", // Walker

  // Memphis MSA (32820)
  "47157": "32820", // Shelby TN
  "47167": "32820", // Tipton TN
  "28033": "32820", // DeSoto MS
  "28093": "32820", // Marshall MS
  "28137": "32820", // Tate MS
  "28143": "32820", // Tunica MS
  "05035": "32820", // Crittenden AR

  // Jackson MSA (27140)
  "28021": "27140", // Claiborne (excluded officially but included for coverage)
  "28049": "27140", // Hinds
  "28051": "27140", // Holmes
  "28089": "27140", // Madison
  "28121": "27140", // Rankin
  "28127": "27140", // Simpson
  "28163": "27140", // Yazoo

  // Mobile MSA (33660)
  "01097": "33660", // Mobile
  "01129": "33660", // Washington

  // Shreveport-Bossier City MSA (43340)
  "22015": "43340", // Bossier
  "22017": "43340", // Caddo
  "22031": "43340", // De Soto
  "22119": "43340", // Webster
};

/** State FIPS -> state geoid (same for our purposes; just for clarity) */
export const STATE_FIPS_TO_GEOID: Record<string, string> = {
  "01": "01",
  "22": "22",
  "28": "28",
  "47": "47",
};

/** Approximate centroids (lon, lat) for our seeded geographies — used for fly-to */
export const GEO_CENTROIDS: Record<string, [number, number]> = {
  // States
  "22": [-91.96, 31.0], // LA
  "01": [-86.79, 32.81], // AL
  "47": [-86.69, 35.86], // TN
  "28": [-89.66, 32.74], // MS
  // MSAs
  "12940": [-91.14, 30.46], // Baton Rouge
  "13820": [-86.81, 33.52], // Birmingham
  "32820": [-89.97, 35.13], // Memphis
  "27140": [-90.18, 32.32], // Jackson
  "33660": [-88.04, 30.7], // Mobile
  "43340": [-93.75, 32.52], // Shreveport
  // City
  "2205000": [-91.14, 30.46], // Baton Rouge city
  // ZCTAs
  "70809": [-91.07, 30.41],
  "70810": [-91.13, 30.34],
  "70806": [-91.13, 30.46],
  "70808": [-91.16, 30.41],
  "70815": [-91.04, 30.49],
};

/** Approximate ZCTA polygons — bounding box approximations for the 5 seeded BR ZIPs.
 * Production replaces these with Census ZCTA TIGER shapefiles.
 */
export const ZCTA_BBOXES: Record<string, [number, number, number, number]> = {
  // [west, south, east, north]
  "70809": [-91.105, 30.385, -91.04, 30.435],
  "70810": [-91.18, 30.31, -91.085, 30.385],
  "70806": [-91.155, 30.435, -91.105, 30.485],
  "70808": [-91.19, 30.39, -91.13, 30.43],
  "70815": [-91.07, 30.46, -91.005, 30.515],
};
