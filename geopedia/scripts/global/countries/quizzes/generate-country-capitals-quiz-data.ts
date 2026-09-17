/**
 * Generates GeoPedia's global Country Capitals quiz data from the processed
 * world-country GeoJSON and CountryData source records.
 *
 * The generated questions:
 *
 * - Use `world-countries.geojson` as the authoritative mapped geography.
 * - Match each mapped country to its CountryData record.
 * - Display the country's capital or capitals.
 * - Use the country's ISO alpha-3 code as the map answer.
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
 * Generated Country Capitals question data.
 */
const OUTPUT_PATH = path.resolve(
  "src/quiz/quizzes/global/data/countryCapitals.ts",
);

/**
 * Properties required from each mapped world-country feature.
 */
type WorldCountryProperties = {
  name: string;
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
 * Resolved Country Capitals question before TypeScript is generated.
 */
type CapitalQuizEntry = {
  answer: string;
  display: string;
  countryName: string;
};

/**
 * Escapes a string as a safe TypeScript string literal.
 */
function quote(value: string): string {
  return JSON.stringify(value);
}

/**
 * Reads and parses a JSON file.
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
 * Kosovo is normalized to `XKX` to match GeoPedia's world-country geometry.
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
 * Normalizes CountryData's capital records into quiz display text.
 *
 * Countries with multiple capital entries are displayed using ` / `.
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
 * Builds an ISO-alpha-3 lookup for CountryData.
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
 * Resolves mapped countries into Country Capitals questions.
 *
 * Countries without matching CountryData or without a usable capital are
 * reported so omissions can be audited.
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
 * Validates that each question points to a unique mapped country.
 */
function validateAnswers(entries: CapitalQuizEntry[]): void {
  const answers = new Set<string>();

  for (const entry of entries) {
    if (answers.has(entry.answer)) {
      throw new Error(
        `Duplicate capital quiz answer: ${entry.answer}`,
      );
    }

    answers.add(entry.answer);
  }
}

/**
 * Creates the generated TypeScript question-data module.
 */
function createSource(entries: CapitalQuizEntry[]): string {
  const sortedEntries = [...entries].sort((left, right) =>
    left.countryName.localeCompare(right.countryName, "en"),
  );

  const questions = sortedEntries
    .map((entry) =>
      [
        "  {",
        `    answer: ${quote(entry.answer)},`,
        `    display: ${quote(entry.display)},`,
        "  },",
      ].join("\n"),
    )
    .join("\n");

  return `/**
 * Generated Country Capitals quiz data.
 *
 * Do not edit manually.
 * Regenerate with:
 * npx tsx scripts/global/countries/quizzes/generate-country-capitals-quiz-data.ts
 */

export const COUNTRY_CAPITAL_QUESTIONS = [
${questions}
];
`;
}

/**
 * Generates GeoPedia's global Country Capitals question data.
 */
function main(): void {
  console.log("Generating Country Capitals quiz data...");

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
      "rest-countries.json must contain an array of CountryData records.",
    );
  }

  const countryLookup = createCountryDataLookup(countries);

  const entries = createCapitalQuizEntries(
    worldCountries.features,
    countryLookup,
  );

  validateAnswers(entries);

  const source = createSource(entries);

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
