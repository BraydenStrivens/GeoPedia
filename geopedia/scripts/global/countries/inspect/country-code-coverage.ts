/**
 * Compares GeoPedia's world-country GeoJSON coverage with the downloaded
 * REST Countries dataset using ISO-3 country codes.
 *
 * This inspection verifies that the two sources contain the same country-code
 * set before REST Countries metadata is joined onto GeoPedia's authoritative
 * world-country features.
 *
 * The script reports:
 *
 * - total and unique ISO-3 codes in each source
 * - GeoPedia country codes missing from REST Countries
 * - REST Countries codes missing from GeoPedia
 * - records in either source that do not provide an ISO-3 code
 *
 * Run from the repository root with:
 *
 *   npx tsx scripts/global/countries/inspect/country-code-coverage.ts
 */

import { readFile } from "node:fs/promises";
import path from "node:path";

const GEOJSON_PATH = path.resolve(
  "public/data/global/countries/geojson/world-countries.geojson",
);

const REST_COUNTRIES_PATH = path.resolve(
  "data/raw/global/countries/rest-countries-v5.json",
);

/**
 * Maps REST Countries source-specific country codes to GeoPedia's canonical
 * ISO-3-style identifiers.
 *
 * REST Countries represents Kosovo with the alpha-3 value `UNK`, while
 * GeoPedia intentionally uses `XKX`.
 */
const REST_COUNTRY_CODE_ALIASES: Readonly<Record<string, string>> = {
  UNK: "XKX",
};

interface WorldCountryFeature {
  properties?: {
    iso_a3?: string | null;
  };
}

interface WorldCountriesGeoJson {
  features?: WorldCountryFeature[];
}

interface RestCountry {
  names?: {
    common?: string;
  };
  codes?: {
    alpha_2?: string | null;
    alpha_3?: string | null;
  };
}

/**
 * Returns a sorted array containing the values present in the first set but
 * absent from the second.
 */
function getSetDifference(
  first: Set<string>,
  second: Set<string>,
): string[] {
  return [...first]
    .filter((value) => !second.has(value))
    .sort((a, b) => a.localeCompare(b));
}

/**
 * Prints a labeled list, or "none" when the list is empty.
 */
function printList(label: string, values: string[]): void {
  console.log(`\n${label}:`);

  if (values.length === 0) {
    console.log("  none");
    return;
  }

  for (const value of values) {
    console.log(`  ${value}`);
  }
}

/**
 * Loads both country datasets and compares their ISO-3 coverage.
 */
async function main(): Promise<void> {
  const [geoJsonText, restCountriesText] = await Promise.all([
    readFile(GEOJSON_PATH, "utf8"),
    readFile(REST_COUNTRIES_PATH, "utf8"),
  ]);

  const geoJson = JSON.parse(geoJsonText) as WorldCountriesGeoJson;

  const restCountries = JSON.parse(
    restCountriesText,
  ) as RestCountry[];

  if (!Array.isArray(geoJson.features)) {
    throw new Error(
      "World-country GeoJSON does not contain a features array.",
    );
  }

  if (!Array.isArray(restCountries)) {
    throw new Error("REST Countries raw data is not an array.");
  }

  const geoJsonCodes: string[] = [];
  let geoJsonMissingCodeCount = 0;

  for (const feature of geoJson.features) {
    const code = feature.properties?.iso_a3;

    if (typeof code === "string" && code.length > 0) {
      geoJsonCodes.push(code);
    } else {
      geoJsonMissingCodeCount += 1;
    }
  }

  const restCodes: string[] = [];
  let restMissingCodeCount = 0;

  const restCountriesWithoutCodes: RestCountry[] = [];

  for (const country of restCountries) {
    const rawCode = country.codes?.alpha_3;

    if (typeof rawCode === "string" && rawCode.length > 0) {
      const code = REST_COUNTRY_CODE_ALIASES[rawCode] ?? rawCode;
      restCodes.push(code);
    } else {
      restMissingCodeCount += 1;
      restCountriesWithoutCodes.push(country);
    }
  }

  const geoJsonCodeSet = new Set(geoJsonCodes);
  const restCodeSet = new Set(restCodes);

  const missingFromRest = getSetDifference(
    geoJsonCodeSet,
    restCodeSet,
  );

  const missingFromGeoJson = getSetDifference(
    restCodeSet,
    geoJsonCodeSet,
  );

  console.log("Country code coverage");
  console.log("=====================");

  console.log(
    `GeoPedia GeoJSON features: ${geoJson.features.length}`,
  );
  console.log(`GeoPedia GeoJSON ISO-3 codes: ${geoJsonCodes.length}`);
  console.log(
    `GeoPedia GeoJSON unique ISO-3 codes: ${geoJsonCodeSet.size}`,
  );
  console.log(
    `GeoPedia GeoJSON records without ISO-3: ${geoJsonMissingCodeCount}`,
  );

  console.log("");

  console.log(`REST Countries records: ${restCountries.length}`);
  console.log(`REST Countries ISO-3 codes: ${restCodes.length}`);
  console.log(
    `REST Countries unique ISO-3 codes: ${restCodeSet.size}`,
  );
  console.log(
    `REST Countries records without ISO-3: ${restMissingCodeCount}`,
  );

  printList(
    "GeoPedia codes missing from REST Countries",
    missingFromRest,
  );

  printList(
    "REST Countries codes missing from GeoPedia",
    missingFromGeoJson,
  );

  console.log("");

  console.log("\nREST Countries records without ISO-3:");

  for (const country of restCountriesWithoutCodes) {
    console.log(
      `  ${country.names?.common ?? "(unknown name)"} ` +
        `(ISO-2: ${country.codes?.alpha_2 ?? "none"})`,
    );
  }

  console.log("\nREST Countries UNK record:");

  for (const country of restCountries) {
    if (country.codes?.alpha_3 === "UNK") {
      console.log(
        `  ${country.names?.common ?? "(unknown name)"} ` +
          `(ISO-2: ${country.codes?.alpha_2 ?? "none"})`,
      );
    }
  }

  if (
    missingFromRest.length === 0 &&
    missingFromGeoJson.length === 0
  ) {
    console.log(
      "ISO-3 coverage matches exactly between the two datasets.",
    );
  } else {
    console.log("ISO-3 coverage differs between the two datasets.");
  }
}

main().catch((error: unknown) => {
  console.error(error instanceof Error ? error.message : error);

  process.exitCode = 1;
});
