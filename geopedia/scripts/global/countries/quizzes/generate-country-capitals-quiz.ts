/**
 * Generates GeoPedia's global Country Capitals quiz from the processed world
 * country GeoJSON and CountryData source records.
 *
 * The generated quiz:
 *
 * - Uses `world-countries.geojson` as the authoritative clickable geography.
 * - Matches each mapped country to its CountryData record.
 * - Uses the country's capital as the displayed quiz question.
 * - Uses the country's ISO alpha-3 code as the map answer.
 * - Uses the existing `world-countries` MapConfig.
 * - Supports the same continent, region, and subregion grouping properties as
 *   GeoPedia's other world-country quizzes.
 *
 * Example:
 *
 *   Tokyo
 *     -> user clicks Japan
 *
 * Generated question:
 *
 *   {
 *     answer: "JPN",
 *     display: "Tokyo",
 *   }
 */

import fs from "node:fs";
import path from "node:path";

/**
 * Processed geographic data used by GeoPedia's world-country map.
 */
const WORLD_COUNTRIES_PATH = path.resolve(
  "public/data/global/countries/geojson/world-countries.geojson",
);

/**
 * Source CountryData records containing country metadata such as capitals.
 */
const COUNTRIES_PATH = path.resolve(
  "data/raw/global/countries/rest-countries.json",
);

/**
 * Generated quiz module.
 */
const OUTPUT_PATH = path.resolve(
  "src/quiz/quizzes/global/countryCapitals.ts",
);

/**
 * Properties required from each mapped world-country feature.
 */
type WorldCountryProperties = {
  /** User-facing country name. */
  name: string;

  /** Canonical ISO alpha-3 identifier used by the quiz map. */
  iso_a3: string;
};

/**
 * Minimal world-country GeoJSON feature representation.
 */
type WorldCountryFeature = {
  type: "Feature";

  properties: WorldCountryProperties;
};

/**
 * Minimal world-country FeatureCollection representation.
 */
type WorldCountryFeatureCollection = {
  type: "FeatureCollection";

  features: WorldCountryFeature[];
};

/**
 * CountryData fields needed by this generator.
 *
 * `capital` accepts either a single string or an array so the generator remains
 * safe if the source represents countries with multiple capitals explicitly.
 */
type CountryDataRecord = {
  names?: {
    common?: string;
  };

  codes?: {
    alpha_3?: string;
  };

  capitals?: Array<{
    name?: string;
  }>;
};

/**
 * Fully resolved question data before it is converted into generated
 * TypeScript source.
 */
type CapitalQuizEntry = {
  /** ISO alpha-3 value clicked on the map. */
  answer: string;

  /** Capital or capitals displayed to the user. */
  display: string;

  /** Country name used for deterministic sorting and diagnostics. */
  countryName: string;
};

/**
 * Escapes a string as a valid TypeScript string literal.
 *
 * JSON.stringify safely handles quotation marks, Unicode characters,
 * backslashes, and other characters that may occur in geographic names.
 */
function quote(value: string): string {
  return JSON.stringify(value);
}

/**
 * Reads and parses a JSON file.
 *
 * @param filePath - JSON file to load.
 * @returns Parsed JSON value.
 */
function readJson<T>(filePath: string): T {
  if (!fs.existsSync(filePath)) {
    throw new Error(
      `Required source file was not found: ${filePath}`,
    );
  }

  return JSON.parse(fs.readFileSync(filePath, "utf8")) as T;
}

/**
 * Returns the canonical ISO alpha-3 ID represented by one CountryData record.
 *
 * Kosovo is normalized to `XKX`, matching GeoPedia's generated world-country
 * geometry and other country assets.
 */
function getCountryDataIsoA3(
  country: CountryDataRecord,
): string | null {
  const commonName = country.names?.common?.trim();

  if (commonName === "Kosovo") {
    return "XKX";
  }

  const alpha3 = country.codes?.alpha_3?.trim();

  if (!alpha3) {
    return null;
  }

  return alpha3.toUpperCase();
}

/**
 * Normalizes CountryData's capital records into readable quiz text.
 *
 * Most countries contain one capital:
 *
 *   [
 *     {
 *       name: "Tokyo",
 *     },
 *   ]
 *
 * Countries with multiple capital entries are displayed together using ` / `.
 *
 * Missing or empty capital names return `null`.
 *
 * @param capitals - Capital records stored on one CountryData object.
 * @returns User-facing capital text, or `null` when no usable capital exists.
 */
function getCapitalDisplay(
  capitals: CountryDataRecord["capitals"],
): string | null {
  if (!Array.isArray(capitals)) {
    return null;
  }

  const capitalNames = capitals
    .map((capital) => capital.name?.trim())
    .filter(
      (name): name is string =>
        typeof name === "string" && name.length > 0,
    );

  if (capitalNames.length === 0) {
    return null;
  }

  return capitalNames.join(" / ");
}

/**
 * Builds an ISO-alpha-3 lookup for the CountryData source.
 *
 * Duplicate canonical IDs are rejected because one mapped country must resolve
 * to exactly one source record.
 */
function createCountryDataLookup(
  countries: CountryDataRecord[],
): Map<string, CountryDataRecord> {
  const lookup = new Map<string, CountryDataRecord>();

  for (const country of countries) {
    const isoA3 = getCountryDataIsoA3(country);

    if (!isoA3) {
      continue;
    }

    if (lookup.has(isoA3)) {
      throw new Error(
        `Duplicate CountryData ISO alpha-3 value: ${isoA3}`,
      );
    }

    lookup.set(isoA3, country);
  }

  return lookup;
}

/**
 * Resolves mapped countries into Country Capitals quiz entries.
 *
 * Countries without matching CountryData or without a usable capital are not
 * silently discarded: they are reported so the generated quiz can be audited.
 */
function createCapitalQuizEntries(
  features: WorldCountryFeature[],
  countryLookup: Map<string, CountryDataRecord>,
): CapitalQuizEntry[] {
  const entries: CapitalQuizEntry[] = [];

  const missingCountryData: string[] = [];
  const missingCapitals: string[] = [];

  for (const feature of features) {
    const countryName = feature.properties?.name?.trim();

    const isoA3 = feature.properties?.iso_a3?.trim().toUpperCase();

    if (!countryName || !isoA3) {
      throw new Error(
        "A world-country feature is missing name or iso_a3.",
      );
    }

    const country = countryLookup.get(isoA3);

    if (!country) {
      missingCountryData.push(`${countryName} (${isoA3})`);

      continue;
    }

    const capital = getCapitalDisplay(country.capitals);

    if (!capital) {
      missingCapitals.push(`${countryName} (${isoA3})`);

      continue;
    }

    entries.push({
      answer: isoA3,
      display: capital,
      countryName,
    });
  }

  if (missingCountryData.length > 0) {
    console.warn("\nMapped countries without matching CountryData:");

    for (const country of missingCountryData) {
      console.warn(`  - ${country}`);
    }
  }

  if (missingCapitals.length > 0) {
    console.warn("\nMapped countries without a usable capital:");

    for (const country of missingCapitals) {
      console.warn(`  - ${country}`);
    }
  }

  return entries;
}

/**
 * Creates generated TypeScript source for one capital question.
 */
function createQuestionSource(entry: CapitalQuizEntry): string {
  return [
    "    {",
    `      answer: ${quote(entry.answer)},`,
    `      display: ${quote(entry.display)},`,
    "    },",
  ].join("\n");
}

/**
 * Creates the complete generated Country Capitals quiz module.
 *
 * Questions are sorted by country name rather than capital name so regeneration
 * remains predictable alongside GeoPedia's other country-based datasets.
 */
function createQuizSource(entries: CapitalQuizEntry[]): string {
  const sortedEntries = [...entries].sort((left, right) =>
    left.countryName.localeCompare(right.countryName, "en"),
  );

  const questions = sortedEntries
    .map(createQuestionSource)
    .join("\n");

  return `/**
 * AUTO-GENERATED FILE.
 *
 * Generated by:
 *
 *   scripts/generateCountryCapitalsQuiz.ts
 *
 * Do not edit the question list manually. Update CountryData or the generator
 * and rerun the script instead.
 */

import type { Quiz } from "@/types/quiz";

/**
 * Tests recognition of countries from their capitals.
 *
 * Each question displays a capital and expects the user to select the country
 * to which that capital belongs.
 */
export const countryCapitalsQuiz: Quiz = {
  id: "country-capitals",
  name: "Country Capitals",

  mapId: "world-countries",

  answerProperty: "iso_a3",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "continent",
        label: "Continent",
        valueType: "string",
      },
      {
        property: "region",
        label: "Region",
        valueType: "string",
      },
      {
        property: "subregion",
        label: "Subregion",
        valueType: "string",
      },
    ],
  },

  questions: [
${questions}
  ],
};
`;
}

/**
 * Generates GeoPedia's Country Capitals quiz.
 */
function main(): void {
  console.log("Generating Country Capitals quiz...");

  const worldCountries = readJson<WorldCountryFeatureCollection>(
    WORLD_COUNTRIES_PATH,
  );

  const countries = readJson<CountryDataRecord[]>(COUNTRIES_PATH);

  if (
    worldCountries.type !== "FeatureCollection" ||
    !Array.isArray(worldCountries.features)
  ) {
    throw new Error(
      "world-countries.geojson is not a valid FeatureCollection.",
    );
  }

  if (!Array.isArray(countries)) {
    throw new Error(
      "countries.json must contain an array of CountryData records.",
    );
  }

  const countryLookup = createCountryDataLookup(countries);

  const entries = createCapitalQuizEntries(
    worldCountries.features,
    countryLookup,
  );

  /**
   * Duplicate quiz answers would cause multiple questions to point at the same
   * map geography, which the current quiz engine does not require here.
   */
  const answers = new Set<string>();

  for (const entry of entries) {
    if (answers.has(entry.answer)) {
      throw new Error(
        `Duplicate capital quiz answer: ${entry.answer}`,
      );
    }

    answers.add(entry.answer);
  }

  const source = createQuizSource(entries);

  fs.mkdirSync(path.dirname(OUTPUT_PATH), {
    recursive: true,
  });

  fs.writeFileSync(OUTPUT_PATH, source, "utf8");

  console.log("");

  console.log(
    `Generated ${entries.length} Country Capitals questions.`,
  );

  console.log(
    `World map features: ${worldCountries.features.length}`,
  );

  console.log(`Output: ${OUTPUT_PATH}`);
}

main();
