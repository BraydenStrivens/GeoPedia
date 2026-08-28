/**
 * Defines the raw and processed data structures used by GeoPedia's GeoNames
 * town-processing pipeline.
 *
 * The processing code is intentionally country-agnostic so the same pipeline
 * can consume:
 *
 * - Individual GeoNames country files such as `US.txt`.
 * - The complete `allCountries.txt` dataset.
 */

/**
 * Parsed representation of one row from GeoNames' main geoname table.
 *
 * Only fields currently useful to GeoPedia's town system are retained.
 */
export type GeoNamesRecord = {
  /** Stable GeoNames identifier. */
  geonameId: string;

  /** Primary UTF-8 place name. */
  name: string;

  /** ASCII representation of the place name. */
  asciiName: string;

  /** Latitude in decimal WGS84 degrees. */
  latitude: number;

  /** Longitude in decimal WGS84 degrees. */
  longitude: number;

  /** GeoNames feature class. Populated places use `P`. */
  featureClass: string;

  /** GeoNames feature code such as `PPL`, `PPLA`, or `PPLC`. */
  featureCode: string;

  /** ISO 3166-1 alpha-2 country code. */
  countryCode: string;

  /** First-order administrative subdivision code. */
  admin1Code: string;

  /** Second-order administrative subdivision code. */
  admin2Code: string;

  /** Population reported by GeoNames. */
  population: number;
};

/**
 * Properties written to GeoPedia's processed town GeoJSON features.
 */
export type ProcessedTownProperties = {
  /** Stable GeoNames identifier. */
  geonameId: string;

  /** User-facing town name. */
  name: string;

  /** ISO country code containing the town. */
  countryCode: string;

  /** First-order administrative subdivision code. */
  admin1Code?: string;

  /** Second-order administrative subdivision code. */
  admin2Code?: string;

  /** Population supplied by GeoNames. */
  population: number;

  /** Original GeoNames populated-place feature code. */
  featureCode: string;

  /**
   * Population rank within the town's country.
   *
   * Rank 1 represents the highest-population eligible town after GeoPedia's
   * filtering and correction rules have been applied.
   */
  countryRank: number;

  /**
   * Population rank across the complete processed world dataset.
   *
   * This remains optional while processing individual country files. It can be
   * populated when the pipeline is run against `allCountries.txt`.
   */
  worldRank?: number;
};

/**
 * GeoJSON Point feature representing one processed GeoPedia town.
 */
export type ProcessedTownFeature = {
  type: "Feature";

  id: string;

  geometry: {
    type: "Point";

    coordinates: [longitude: number, latitude: number];
  };

  properties: ProcessedTownProperties;
};

/**
 * GeoJSON FeatureCollection produced by the town processor.
 */
export type ProcessedTownFeatureCollection = {
  type: "FeatureCollection";

  features: ProcessedTownFeature[];
};
