/**
 * Provides reusable names for US subdivisions identified by postal
 * abbreviation.
 *
 * GeoJSON datasets should prefer two-letter postal abbreviations when
 * practical. This mapping allows those compact identifiers to be converted
 * into user-facing subdivision names without duplicating display information
 * across quiz configurations.
 *
 * The mapping includes:
 *
 * - The 50 states.
 * - The District of Columbia.
 * - US territories represented by standard postal abbreviations.
 */

/**
 * Maps US postal abbreviations to their full subdivision names.
 *
 * This is used when a GeoJSON property stores subdivision identifiers as
 * postal abbreviations while the interface should display their full names.
 */
export const US_SUBDIVISION_NAMES_BY_ABBREVIATION: Record<
  string,
  string
> = {
  // States
  AL: "Alabama",
  AK: "Alaska",
  AZ: "Arizona",
  AR: "Arkansas",
  CA: "California",
  CO: "Colorado",
  CT: "Connecticut",
  DE: "Delaware",
  FL: "Florida",
  GA: "Georgia",
  HI: "Hawaii",
  ID: "Idaho",
  IL: "Illinois",
  IN: "Indiana",
  IA: "Iowa",
  KS: "Kansas",
  KY: "Kentucky",
  LA: "Louisiana",
  ME: "Maine",
  MD: "Maryland",
  MA: "Massachusetts",
  MI: "Michigan",
  MN: "Minnesota",
  MS: "Mississippi",
  MO: "Missouri",
  MT: "Montana",
  NE: "Nebraska",
  NV: "Nevada",
  NH: "New Hampshire",
  NJ: "New Jersey",
  NM: "New Mexico",
  NY: "New York",
  NC: "North Carolina",
  ND: "North Dakota",
  OH: "Ohio",
  OK: "Oklahoma",
  OR: "Oregon",
  PA: "Pennsylvania",
  RI: "Rhode Island",
  SC: "South Carolina",
  SD: "South Dakota",
  TN: "Tennessee",
  TX: "Texas",
  UT: "Utah",
  VT: "Vermont",
  VA: "Virginia",
  WA: "Washington",
  WV: "West Virginia",
  WI: "Wisconsin",
  WY: "Wyoming",

  // District and territories
  AS: "American Samoa",
  DC: "District of Columbia",
  GU: "Guam",
  MP: "Northern Mariana Islands",
  PR: "Puerto Rico",
  VI: "U.S. Virgin Islands",
};
