/**
 * Generates GeoPedia's global Calling Codes quiz from the processed world
 * country GeoJSON and CountryData source records.
 *
 * The generated quiz:
 *
 * - Uses `world-countries.geojson` as the authoritative clickable geography.
 * - Matches each mapped country to its CountryData record by ISO alpha-3 code.
 * - Displays calling codes with a leading `+`.
 * - Uses the country's ISO alpha-3 code as the clickable map answer.
 * - Uses the existing `world-countries` MapConfig.
 * - Supports continent, region, and subregion grouping.
 *
 * Example:
 *
 *   +81
 *     -> user clicks Japan
 *
 * Generated question:
 *
 *   {
 *     answer: "JPN",
 *     display: "+81",
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
 * Source CountryData records containing calling-code metadata.
 */
const COUNTRIES_PATH = path.resolve(
  "data/raw/global/countries/rest-countries.json",
);

/**
 * Generated quiz module.
 */
const OUTPUT_PATH = path.resolve(
  "src/quiz/quizzes/global/callingCodes.ts",
);

/**
 * Properties required from each world-country map feature.
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

  /**
   * Country calling codes without their leading `+`.
   *
   * Example:
   *
   *   ["81"]
   *
   * becomes:
   *
   *   +81
   */
  calling_codes?: string[];
};

/**
 * Resolved quiz entry before TypeScript source is generated.
 */
type CallingCodeQuizEntry = {
  /** ISO alpha-3 map answer. */
  answer: string;

  /** Calling code displayed to the user, including its leading `+`. */
  display: string;

  /** Country name used for sorting and diagnostics. */
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
 *
 * @param filePath - JSON file to load.
 * @returns Parsed JSON contents.
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
 * Returns the canonical world-map ISO alpha-3 value for one CountryData
 * record.
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
 * Normalizes one raw calling code for display.
 *
 * CountryData stores codes without `+`, while the quiz should show normal
 * international dialing notation.
 *
 * Examples:
 *
 *   "81"  -> "+81"
 *   "+81" -> "+81"
 *
 * @param callingCode - Raw CountryData calling code.
 * @returns Normalized display value or `null` for empty input.
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
 * Returns all usable calling codes belonging to one CountryData record.
 *
 * Duplicate values inside the same country record are removed.
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
 * Resolves mapped world countries into Calling Codes quiz entries.
 *
 * Countries with multiple calling codes receive one question for each code.
 *
 * Countries without a CountryData match or without any calling code are
 * reported rather than silently disappearing from the generated quiz.
 */
function createCallingCodeQuizEntries(
  features: WorldCountryFeature[],
  countryLookup: Map<string, CountryDataRecord>,
): CallingCodeQuizEntry[] {
  const entries: CallingCodeQuizEntry[] = [];

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
 * Reports calling codes shared by multiple countries.
 *
 * These are important because a single-answer quiz cannot determine which
 * country the user should select from the calling code alone.
 *
 * Example:
 *
 *   +1
 *     Canada
 *     United States
 *
 * Shared codes are currently retained in the generated quiz so the source data
 * can be inspected before deciding how GeoPedia should treat ambiguous
 * questions.
 */
function reportSharedCallingCodes(
  entries: CallingCodeQuizEntry[],
): void {
  const countriesByCode = new Map<string, CallingCodeQuizEntry[]>();

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

  console.warn(
    "\nThese questions are ambiguous in the current single-answer quiz model.",
  );
}

/**
 * Creates generated TypeScript for one Calling Codes question.
 */
function createQuestionSource(entry: CallingCodeQuizEntry): string {
  return [
    "    {",
    `      answer: ${quote(entry.answer)},`,
    `      display: ${quote(entry.display)},`,
    "    },",
  ].join("\n");
}

/**
 * Creates the complete generated Calling Codes quiz module.
 *
 * The quiz contains exactly one question for each distinct calling code.
 *
 * Individual world-country features store their own `calling_codes` arrays,
 * allowing several geographic features to resolve to the same quiz answer.
 */
function createQuizSource(entries: CallingCodeQuizEntry[]): string {
  /**
   * Collapse country/code assignments into one entry per calling code.
   *
   * Example:
   *
   * USA -> +1
   * CAN -> +1
   * JAM -> +1
   *
   * becomes one quiz question:
   *
   * +1
   */
  const distinctCallingCodes = Array.from(
    new Set(entries.map((entry) => entry.display)),
  ).sort((left, right) =>
    left.localeCompare(right, "en", {
      numeric: true,
    }),
  );

  const questions = distinctCallingCodes
    .map((callingCode) =>
      [
        "    {",
        `      answer: ${quote(callingCode)},`,
        `      display: ${quote(callingCode)},`,
        "    },",
      ].join("\n"),
    )
    .join("\n");

  return `/**
 * AUTO-GENERATED FILE.
 *
 * Generated by:
 *
 *   scripts/generateCallingCodesQuiz.ts
 *
 * Do not edit the question list manually. Update CountryData or the generator
 * and rerun the script instead.
 */

import type { Quiz } from "@/types/quiz";

/**
 * Tests recognition of countries and territories from their international
 * calling codes.
 *
 * A calling code may belong to more than one geographic feature. Selecting any
 * feature whose \`calling_codes\` property contains the current answer is
 * considered a valid selection.
 */
export const callingCodesQuiz: Quiz = {
  id: "calling-codes",
  name: "Calling Codes",

  mapId: "world-countries",

  answerProperty: "calling_codes",
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
 * Generates GeoPedia's Calling Codes quiz.
 */
function main(): void {
  console.log("Generating Calling Codes quiz...");

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

  const entries = createCallingCodeQuizEntries(
    worldCountries.features,
    countryLookup,
  );

  reportSharedCallingCodes(entries);

  const source = createQuizSource(entries);

  fs.mkdirSync(path.dirname(OUTPUT_PATH), {
    recursive: true,
  });

  fs.writeFileSync(OUTPUT_PATH, source, "utf8");

  console.log("");

  const distinctCallingCodeCount = new Set(
    entries.map((entry) => entry.display),
  ).size;

  console.log(
    `Generated ${distinctCallingCodeCount} distinct Calling Codes questions.`,
  );

  console.log(
    `World map features: ${worldCountries.features.length}`,
  );

  console.log(`Output: ${OUTPUT_PATH}`);
}

main();
