/**
 * ISO-A3 codes for countries currently included in GeoGuessr's standard
 * country coverage.
 *
 * These values use the same uppercase ISO-A3 format stored by the
 * `iso_a3` property in world-countries.geojson.
 *
 * The list is intentionally maintained separately from geographic source data
 * because GeoGuessr availability can change independently of country geometry.
 */
export const GEOGUESSR_COUNTRY_CODES = new Set<string>([
  // Africa
  "BWA",
  "SWZ",
  "GHA",
  "KEN",
  "LSO",
  "NGA",
  "RWA",
  "SEN",
  "ZAF",
  "UGA",

  // Asia
  "BGD",
  "BTN",
  "KHM",
  "HKG",
  "IND",
  "IDN",
  "ISR",
  "JPN",
  "JOR",
  "KGZ",
  "LAO",
  "MYS",
  "MNG",
  "PHL",
  "QAT",
  "SGP",
  "KOR",
  "LKA",
  "TWN",
  "THA",
  "TUR",
  "ARE",

  // Europe
  "ALB",
  "AND",
  "AUT",
  "BEL",
  "BIH",
  "BGR",
  "HRV",
  "CZE",
  "DNK",
  "EST",
  "FIN",
  "FRA",
  "DEU",
  "GRC",
  "HUN",
  "ISL",
  "IRL",
  "ITA",
  "LVA",
  "LTU",
  "LUX",
  "MLT",
  "MDA",
  "MCO",
  "MNE",
  "NLD",
  "MKD",
  "NOR",
  "POL",
  "PRT",
  "ROU",
  "SMR",
  "SRB",
  "SVK",
  "SVN",
  "ESP",
  "SWE",
  "CHE",
  "UKR",
  "GBR",
  "XKX",

  // North America / Caribbean
  "CAN",
  "CRI",
  "DOM",
  "GEO",
  "GTM",
  "MEX",
  "PAN",
  "PRI",
  "USA",

  // South America
  "ARG",
  "BOL",
  "BRA",
  "CHL",
  "COL",
  "ECU",
  "PER",
  "URY",

  // Oceania
  "AUS",
  "NZL",
]);
