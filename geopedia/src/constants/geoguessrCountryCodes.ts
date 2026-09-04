/**
 * ISO-A3 codes for countries/territories currently included in GeoGuessr's standard
 * country coverage as of September 4, 2026.
 *
 * These values use the same uppercase ISO-A3 format stored by the
 * `iso_a3` property in world-countries.geojson.
 *
 * The list is intentionally maintained separately from geographic source data
 * because GeoGuessr availability can change independently of country geometry.
 */
export const GEOGUESSR_COUNTRY_CODES = new Set<string>([
  // Africa
  "BWA", // Botswana
  "EGY", // Egypt
  "SWZ", // Eswatini
  "GHA", // Ghana
  "KEN", // Kenya
  "LSO", // Lesotho
  "MDG", // Madagascar
  "NAM", // Namibia
  "NGA", // Nigeria
  "REU", // Réunion
  "RWA", // Rwanda
  "SEN", // Senegal
  "ZAF", // South Africa
  "TUN", // Tunisia
  "UGA", // Uganda

  // Asia
  "BGD", // Bangladesh
  "BTN", // Bhutan
  "KHM", // Cambodia
  "CXR", // Christmas Island
  "CYP", // Cyprus
  "GEO", // Georgia
  "HKG", // Hong Kong
  "IND", // India
  "IDN", // Indonesia
  "ISR", // Israel
  "JPN", // Japan
  "JOR", // Jordan
  "KAZ", // Kazakhstan
  "KGZ", // Kyrgyzstan
  "LAO", // Laos
  "LBN", // Lebanon
  "MAC", // Macau
  "MYS", // Malaysia
  "MNG", // Mongolia
  "NPL", // Nepal
  "OMN", // Oman
  "PSE", // Palestine
  "PHL", // Philippines
  "QAT", // Qatar
  "SGP", // Singapore
  "KOR", // South Korea
  "LKA", // Sri Lanka
  "TWN", // Taiwan
  "THA", // Thailand
  "TUR", // Turkey
  "ARE", // United Arab Emirates
  "VNM", // Vietnam

  // Europe
  "ALB", // Albania
  "AND", // Andorra
  "AUT", // Austria
  "BEL", // Belgium
  "BIH", // Bosnia and Herzegovina
  "BGR", // Bulgaria
  "HRV", // Croatia
  "CZE", // Czechia
  "DNK", // Denmark
  "EST", // Estonia
  "FRO", // Faroe Islands
  "FIN", // Finland
  "FRA", // France
  "DEU", // Germany
  "GIB", // Gibraltar
  "GRC", // Greece
  "HUN", // Hungary
  "IMN", // Isle of Man
  "ISL", // Iceland
  "IRL", // Ireland
  "ITA", // Italy
  "XKX", // Kosovo
  "LVA", // Latvia
  "LTU", // Lithuania
  "LUX", // Luxembourg
  "MLT", // Malta
  "MCO", // Monaco
  "MNE", // Montenegro
  "NLD", // Netherlands
  "MKD", // North Macedonia
  "NOR", // Norway
  "POL", // Poland
  "PRT", // Portugal
  "ROU", // Romania
  "RUS", // Russia
  "SMR", // San Marino
  "SRB", // Serbia
  "SVK", // Slovakia
  "SVN", // Slovenia
  "ESP", // Spain
  "SWE", // Sweden
  "CHE", // Switzerland
  "UKR", // Ukraine
  "GBR", // United Kingdom

  // North America / Caribbean
  "BMU", // Bermuda
  "CAN", // Canada
  "CRI", // Costa Rica
  "CUW", // Curaçao
  "DOM", // Dominican Republic
  "GRL", // Greenland
  "GTM", // Guatemala
  "MEX", // Mexico
  "PAN", // Panama
  "PRI", // Puerto Rico
  "USA", // United States

  // South America
  "ARG", // Argentina
  "BOL", // Bolivia
  "BRA", // Brazil
  "CHL", // Chile
  "COL", // Colombia
  "ECU", // Ecuador
  "PRY", // Paraguay
  "PER", // Peru
  "URY", // Uruguay

  // Oceania
  "ASM", // American Samoa
  "AUS", // Australia
  "PYF", // French Polynesia
  "GUM", // Guam
  "MNP", // Northern Mariana Islands
  "NZL", // New Zealand
]);
