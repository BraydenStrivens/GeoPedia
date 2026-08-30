/**
 * Adds normalized international calling codes from CountryData to GeoPedia's
 * generated world-country GeoJSON.
 *
 * This script intentionally modifies feature properties only. It does not
 * change, dissolve, combine, simplify, or otherwise alter country geometry.
 *
 * Example output feature properties:
 *
 * {
 *   name: "United States",
 *   iso_a3: "USA",
 *   calling_codes: ["+1"],
 *   continent: "North America",
 *   ...
 * }
 *
 * Shared calling codes remain attached independently to every country that
 * uses them. This allows a quiz question such as "+1" to match every +1
 * country while preserving normal country borders.
 */

import fs from "node:fs";
import path from "node:path";

/**
 * CountryData source.
 */
const COUNTRIES_PATH = path.resolve("data/source/countries.json");

/**
 * Existing generated world-country GeoJSON.
 *
 * This file is read and then overwritten with enriched feature properties.
 */
const WORLD_COUNTRIES_PATH = path.resolve(
  "public/data/geojson/world/world-countries.geojson",
);

/**
 * CountryData fields required by this enrichment step.
 */
type CountryDataRecord = {
  names?: {
    common?: string;
  };

  codes?: {
    alpha_3?: string;
  };

  calling_codes?: string[];
};

/**
 * World-country properties required by this script.
 *
 * Other existing feature properties are retained through the index signature.
 */
type WorldCountryProperties = {
  name?: string;
  iso_a3?: string;

  calling_codes?: string[];

  [key: string]: unknown;
};

type WorldCountryFeature = {
  type: "Feature";

  properties: WorldCountryProperties;

  geometry: unknown;

  [key: string]: unknown;
};

type WorldCountryFeatureCollection = {
  type: "FeatureCollection";

  features: WorldCountryFeature[];

  [key: string]: unknown;
};

/**
 * Reads and parses a JSON file.
 */
function readJson<T>(filePath: string): T {
  if (!fs.existsSync(filePath)) {
    throw new Error(`Required file was not found: ${filePath}`);
  }

  return JSON.parse(fs.readFileSync(filePath, "utf8")) as T;
}

/**
 * Returns GeoPedia's canonical ISO alpha-3 code for a CountryData record.
 *
 * Kosovo is represented by `XKX` in GeoPedia's world geography even though
 * the CountryData source does not provide a normal alpha-3 code for it.
 */
function getCountryDataIsoA3(
  country: CountryDataRecord,
): string | null {
  const countryName = country.names?.common?.trim();

  if (countryName === "Kosovo") {
    return "XKX";
  }

  const alpha3 = country.codes?.alpha_3?.trim().toUpperCase();

  return alpha3 || null;
}

/**
 * Normalizes one calling code into standard international display notation.
 *
 * Examples:
 *
 * "1"   -> "+1"
 * "81"  -> "+81"
 * "+44" -> "+44"
 */
function normalizeCallingCode(callingCode: string): string | null {
  const trimmed = callingCode.trim();

  if (!trimmed) {
    return null;
  }

  return trimmed.startsWith("+") ? trimmed : `+${trimmed}`;
}

/**
 * Returns all usable calling codes for one CountryData record.
 *
 * Duplicate codes inside an individual source record are removed.
 */
function getCallingCodes(country: CountryDataRecord): string[] {
  if (!Array.isArray(country.calling_codes)) {
    return [];
  }

  return Array.from(
    new Set(
      country.calling_codes
        .map(normalizeCallingCode)
        .filter((code): code is string => code !== null),
    ),
  );
}

/**
 * Builds an ISO-alpha-3 -> calling-codes lookup.
 */
function createCallingCodeLookup(
  countries: CountryDataRecord[],
): Map<string, string[]> {
  const lookup = new Map<string, string[]>();

  for (const country of countries) {
    const isoA3 = getCountryDataIsoA3(country);

    if (!isoA3) {
      continue;
    }

    if (lookup.has(isoA3)) {
      throw new Error(
        `Duplicate CountryData ISO alpha-3 code: ${isoA3}`,
      );
    }

    lookup.set(isoA3, getCallingCodes(country));
  }

  return lookup;
}

/**
 * Adds calling-code arrays to every mapped world-country feature.
 */
function enrichWorldCountries(
  worldCountries: WorldCountryFeatureCollection,
  callingCodeLookup: Map<string, string[]>,
): void {
  const missingCountryData: string[] = [];

  const missingCallingCodes: string[] = [];

  let enrichedCount = 0;

  for (const feature of worldCountries.features) {
    const isoA3 = feature.properties.iso_a3?.trim().toUpperCase();

    const countryName =
      feature.properties.name?.trim() ?? "Unknown country";

    if (!isoA3) {
      throw new Error(
        `World feature is missing iso_a3: ${countryName}`,
      );
    }

    const callingCodes = callingCodeLookup.get(isoA3);

    if (!callingCodes) {
      missingCountryData.push(`${countryName} (${isoA3})`);

      feature.properties.calling_codes = [];

      continue;
    }

    feature.properties.calling_codes = callingCodes;

    if (callingCodes.length === 0) {
      missingCallingCodes.push(`${countryName} (${isoA3})`);
    } else {
      enrichedCount += 1;
    }
  }

  console.log(`Features with calling codes: ${enrichedCount}`);

  if (missingCountryData.length > 0) {
    console.warn("\nWorld features without matching CountryData:");

    for (const country of missingCountryData) {
      console.warn(`  - ${country}`);
    }
  }

  if (missingCallingCodes.length > 0) {
    console.warn("\nWorld features without calling codes:");

    for (const country of missingCallingCodes) {
      console.warn(`  - ${country}`);
    }
  }
}

/**
 * Runs the enrichment step.
 */
function main(): void {
  console.log("Adding calling codes to world-countries.geojson...");

  const countries = readJson<CountryDataRecord[]>(COUNTRIES_PATH);

  const worldCountries = readJson<WorldCountryFeatureCollection>(
    WORLD_COUNTRIES_PATH,
  );

  if (!Array.isArray(countries)) {
    throw new Error("countries.json must contain an array.");
  }

  if (
    worldCountries.type !== "FeatureCollection" ||
    !Array.isArray(worldCountries.features)
  ) {
    throw new Error(
      "world-countries.geojson must be a valid FeatureCollection.",
    );
  }

  const callingCodeLookup = createCallingCodeLookup(countries);

  enrichWorldCountries(worldCountries, callingCodeLookup);

  /**
   * Pretty-print with two-space indentation.
   *
   * Geometry coordinates are preserved exactly as parsed; only serialization
   * formatting and feature properties change.
   */
  fs.writeFileSync(
    WORLD_COUNTRIES_PATH,
    `${JSON.stringify(worldCountries, null, 2)}\n`,
    "utf8",
  );

  console.log("");

  console.log(
    `Updated ${worldCountries.features.length} world features.`,
  );

  console.log(`Output: ${WORLD_COUNTRIES_PATH}`);
}

main();
