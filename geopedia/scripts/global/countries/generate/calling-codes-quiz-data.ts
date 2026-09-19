/**
 * Generates GeoPedia's global Calling Codes quiz data from the processed
 * world-country GeoJSON and CountryData source records.
 *
 * The generated question data:
 *
 * - Uses `world-countries.geojson` as the authoritative mapped geography.
 * - Matches mapped countries to CountryData by ISO alpha-3 code.
 * - Normalizes calling codes with a leading `+`.
 * - Produces one question for each distinct calling code.
 *
 * Shared calling codes are intentionally collapsed into one question because
 * the world-country GeoJSON stores calling-code arrays on each feature.
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
 * Source CountryData records containing calling-code metadata.
 */
const COUNTRIES_PATH = path.resolve(
  "data/raw/global/countries/rest-countries.json",
);

/**
 * Generated Calling Codes question data.
 */
const OUTPUT_PATH = path.resolve(
  "src/quiz/quizzes/global/data/callingCodes.ts",
);

/**
 * Properties required from each world-country map feature.
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
 * Minimal FeatureCollection representation required by this generator.
 */
type WorldCountryFeatureCollection = {
  type: "FeatureCollection";
  features: WorldCountryFeature[];
};

/**
 * CountryData fields required by the Calling Codes generator.
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
 * Resolved country/calling-code assignment used during generation.
 */
type CallingCodeEntry = {
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
 * Returns the canonical world-map ISO alpha-3 value for a CountryData record.
 *
 * Kosovo is normalized to `XKX` so it matches GeoPedia's generated world
 * geography.
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
 * Normalizes a calling code for display.
 */
function normalizeCallingCode(callingCode: string): string | null {
  const trimmedCode = callingCode.trim();

  if (!trimmedCode) {
    return null;
  }

  if (trimmedCode.startsWith("+")) {
    return trimmedCode;
  }

  return `+${trimmedCode}`;
}

/**
 * Returns the unique usable calling codes for one country.
 */
function getCallingCodes(
  callingCodes: CountryDataRecord["calling_codes"] | undefined,
): string[] {
  if (!Array.isArray(callingCodes)) {
    return [];
  }

  const normalizedCodes = callingCodes
    .map(normalizeCallingCode)
    .filter((code): code is string => code !== null);

  return Array.from(new Set(normalizedCodes));
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
 * Resolves mapped world countries into country/calling-code assignments.
 */
function createCallingCodeEntries(
  features: WorldCountryFeature[],
  countryLookup: Map<string, CountryDataRecord>,
): CallingCodeEntry[] {
  const entries: CallingCodeEntry[] = [];

  const missingCountryData: string[] = [];
  const missingCallingCodes: string[] = [];

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

    const callingCodes = getCallingCodes(country.calling_codes);

    if (callingCodes.length === 0) {
      missingCallingCodes.push(`${countryName} (${isoA3})`);

      continue;
    }

    for (const callingCode of callingCodes) {
      entries.push({
        answer: isoA3,
        display: callingCode,
        countryName,
      });
    }
  }

  if (missingCountryData.length > 0) {
    console.warn("\nMapped countries without matching CountryData:");

    for (const country of missingCountryData) {
      console.warn(`  - ${country}`);
    }
  }

  if (missingCallingCodes.length > 0) {
    console.warn("\nMapped countries without calling codes:");

    for (const country of missingCallingCodes) {
      console.warn(`  - ${country}`);
    }
  }

  return entries;
}

/**
 * Reports calling codes shared by multiple mapped countries.
 */
function reportSharedCallingCodes(entries: CallingCodeEntry[]): void {
  const countriesByCode = new Map<string, CallingCodeEntry[]>();

  for (const entry of entries) {
    const existing = countriesByCode.get(entry.display);

    if (existing) {
      existing.push(entry);
    } else {
      countriesByCode.set(entry.display, [entry]);
    }
  }

  const sharedCodes = Array.from(countriesByCode.entries())
    .filter(([, codeEntries]) => {
      const countryAnswers = new Set(
        codeEntries.map((entry) => entry.answer),
      );

      return countryAnswers.size > 1;
    })
    .sort(([leftCode], [rightCode]) =>
      leftCode.localeCompare(rightCode, "en", {
        numeric: true,
      }),
    );

  if (sharedCodes.length === 0) {
    console.log(
      "\nNo calling codes are shared by multiple mapped countries.",
    );

    return;
  }

  console.warn("\nShared calling codes:");

  for (const [callingCode, codeEntries] of sharedCodes) {
    console.warn(`\n  ${callingCode}`);

    const uniqueCountries = Array.from(
      new Map(
        codeEntries.map((entry) => [entry.answer, entry]),
      ).values(),
    );

    for (const entry of uniqueCountries) {
      console.warn(`    - ${entry.countryName} (${entry.answer})`);
    }
  }
}

/**
 * Creates one question for each distinct calling code.
 */
function createQuestions(entries: CallingCodeEntry[]): string[] {
  return Array.from(
    new Set(entries.map((entry) => entry.display)),
  ).sort((left, right) =>
    left.localeCompare(right, "en", {
      numeric: true,
    }),
  );
}

/**
 * Creates the generated TypeScript question-data module.
 */
function createSource(questions: string[]): string {
  const questionSource = questions
    .map((callingCode) => `  { answer: ${quote(callingCode)} },`)
    .join("\n");

  return `/**
 * Generated Calling Codes quiz data.
 *
 * Do not edit manually.
 * Regenerate with:
 * npx tsx scripts/global/countries/quizzes/generate-calling-codes-quiz-data.ts
 */

export const CALLING_CODE_QUESTIONS = [
${questionSource}
];
`;
}

/**
 * Generates GeoPedia's global Calling Codes question data.
 */
function main(): void {
  console.log("Generating Calling Codes quiz data...");

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

  const entries = createCallingCodeEntries(
    worldCountries.features,
    countryLookup,
  );

  reportSharedCallingCodes(entries);

  const questions = createQuestions(entries);

  const source = createSource(questions);

  fs.mkdirSync(path.dirname(OUTPUT_PATH), {
    recursive: true,
  });

  fs.writeFileSync(OUTPUT_PATH, source, "utf8");

  console.log("");

  console.log(
    `Generated ${questions.length} distinct Calling Codes questions.`,
  );

  console.log(
    `World map features: ${worldCountries.features.length}`,
  );

  console.log(`Output: ${OUTPUT_PATH}`);
}

main();
