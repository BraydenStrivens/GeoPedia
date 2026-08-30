/**
 * Generates GeoPedia's global Country Flags quiz.
 *
 * The generator combines:
 *
 * - `public/data/geojson/world/world-countries.geojson`
 * - `public/data/country-flags/*.svg`
 *
 * The world-country GeoJSON is treated as the authoritative list of quiz
 * answers because the same dataset is rendered by the Country Flags map.
 *
 * Each GeoJSON feature becomes one QuizQuestion whose:
 *
 * - answer is the feature's raw ISO-A3 value.
 * - display value is the country's user-facing name.
 * - prompt displays the corresponding country flag.
 *
 * Keeping the generated answers identical to the GeoJSON's `iso_a3` property
 * allows the existing map-quiz interaction system to compare selected features
 * directly against quiz answers without special-case normalization.
 *
 * Run from the project root with:
 *
 *   npx tsx scripts/generate/generate-global-country-flags-quiz.ts
 */

import {
  existsSync,
  mkdirSync,
  readdirSync,
  readFileSync,
  writeFileSync,
} from "node:fs";
import path from "node:path";

/**
 * Location of the world-country GeoJSON used by the global quiz map.
 */
const WORLD_GEOJSON_PATH = path.join(
  process.cwd(),
  "public",
  "data",
  "geojson",
  "world",
  "world-countries.geojson",
);

/**
 * Directory containing the SVG flag assets displayed by quiz questions.
 */
const FLAG_DIRECTORY_PATH = path.join(
  process.cwd(),
  "public",
  "data",
  "country-flags",
);

/**
 * Generated Country Flags quiz file.
 */
const OUTPUT_PATH = path.join(
  process.cwd(),
  "src",
  "quiz",
  "quizzes",
  "global",
  "countryFlags.ts",
);

/**
 * Properties required from each world-country GeoJSON feature.
 */
type WorldCountryProperties = {
  /** User-facing country or territory name. */
  name?: unknown;

  /** ISO 3166-1 alpha-3-style identifier used by GeoPedia's world dataset. */
  iso_a3?: unknown;
};

/**
 * Minimal feature shape required by this generator.
 */
type WorldCountryFeature = {
  type?: unknown;
  properties?: WorldCountryProperties | null;
};

/**
 * Minimal FeatureCollection shape required by this generator.
 */
type WorldCountryFeatureCollection = {
  type?: unknown;
  features?: unknown;
};

/**
 * Fully validated country entry used to generate one quiz question.
 */
type CountryFlagQuestionData = {
  /** Raw ISO-A3 value stored by the GeoJSON. */
  isoA3: string;

  /** User-facing country name stored by the GeoJSON. */
  name: string;

  /** Exact SVG filename discovered in the flag directory. */
  flagFilename: string;
};

/**
 * Reads and parses the world-country GeoJSON.
 *
 * @returns Parsed FeatureCollection object.
 * @throws When the file does not exist, contains invalid JSON, or is not a
 * valid GeoJSON FeatureCollection.
 */
function readWorldCountries(): WorldCountryFeature[] {
  if (!existsSync(WORLD_GEOJSON_PATH)) {
    throw new Error(
      `World-country GeoJSON was not found:\n${WORLD_GEOJSON_PATH}`,
    );
  }

  const rawJson = readFileSync(WORLD_GEOJSON_PATH, "utf8");

  const parsed = JSON.parse(rawJson) as WorldCountryFeatureCollection;

  if (
    parsed.type !== "FeatureCollection" ||
    !Array.isArray(parsed.features)
  ) {
    throw new Error(
      "world-countries.geojson is not a valid GeoJSON FeatureCollection.",
    );
  }

  return parsed.features as WorldCountryFeature[];
}

/**
 * Creates a lookup from uppercase ISO-A3 code to the exact flag filename
 * stored on disk.
 *
 * Asset lookup is case-insensitive, while the discovered filename itself is
 * preserved so generated public URLs always match the real asset.
 *
 * @returns Map keyed by uppercase ISO-A3 code.
 * @throws When the flag directory does not exist or contains duplicate codes.
 */
function getFlagFiles(): Map<string, string> {
  if (!existsSync(FLAG_DIRECTORY_PATH)) {
    throw new Error(
      `Country flag directory was not found:\n${FLAG_DIRECTORY_PATH}`,
    );
  }

  const flagFiles = new Map<string, string>();

  const filenames = readdirSync(FLAG_DIRECTORY_PATH).filter(
    (filename) => filename.toLowerCase().endsWith(".svg"),
  );

  for (const filename of filenames) {
    const isoA3 = path.parse(filename).name.toUpperCase();

    if (flagFiles.has(isoA3)) {
      throw new Error(
        `Duplicate country flag detected for ISO-A3 code "${isoA3}".`,
      );
    }

    flagFiles.set(isoA3, filename);
  }

  return flagFiles;
}

/**
 * Validates the world-country features and joins them to their flag assets.
 *
 * @param features - Features loaded from world-countries.geojson.
 * @param flagFiles - Available SVG flags keyed by uppercase ISO-A3 code.
 * @returns Validated quiz-question source data.
 * @throws When required properties are missing, ISO-A3 values are duplicated,
 * or a corresponding flag cannot be found.
 */
function createQuestionData(
  features: WorldCountryFeature[],
  flagFiles: Map<string, string>,
): CountryFlagQuestionData[] {
  const questions: CountryFlagQuestionData[] = [];

  const seenIsoA3Codes = new Set<string>();

  for (const feature of features) {
    if (!feature.properties) {
      throw new Error(
        "A world-country feature is missing its properties object.",
      );
    }

    const rawName = feature.properties.name;
    const rawIsoA3 = feature.properties.iso_a3;

    if (typeof rawName !== "string" || rawName.trim().length === 0) {
      throw new Error(
        "A world-country feature is missing a valid `name` property.",
      );
    }

    if (
      typeof rawIsoA3 !== "string" ||
      rawIsoA3.trim().length === 0
    ) {
      throw new Error(
        `World-country feature "${rawName}" is missing a valid ` +
          "`iso_a3` property.",
      );
    }

    /*
     * Preserve the raw GeoJSON answer for the generated QuizQuestion.
     *
     * Asset discovery still normalizes to uppercase because flag filenames are
     * matched independently of their filesystem casing.
     */
    const isoA3 = rawIsoA3.trim();
    const normalizedIsoA3 = isoA3.toUpperCase();

    if (seenIsoA3Codes.has(normalizedIsoA3)) {
      throw new Error(
        `Duplicate world-country ISO-A3 value "${isoA3}" detected.`,
      );
    }

    seenIsoA3Codes.add(normalizedIsoA3);

    const flagFilename = flagFiles.get(normalizedIsoA3);

    if (!flagFilename) {
      throw new Error(
        `No flag SVG was found for ${rawName} (${isoA3}).`,
      );
    }

    questions.push({
      isoA3,
      name: rawName.trim(),
      flagFilename,
    });
  }

  /*
   * Stable alphabetical output makes generated diffs predictable and keeps the
   * file easy to inspect manually.
   */
  return questions.sort((first, second) =>
    first.name.localeCompare(second.name),
  );
}

/**
 * Converts an arbitrary JavaScript string into its TypeScript string-literal
 * representation.
 *
 * JSON.stringify correctly escapes quotes, slashes, Unicode control
 * characters, and other values that could otherwise break generated source.
 *
 * @param value - Text to serialize.
 * @returns Safe TypeScript/JavaScript string literal.
 */
function quote(value: string): string {
  return JSON.stringify(value);
}

/**
 * Creates the source code for one generated QuizQuestion.
 *
 * The image alt text intentionally does not contain the country name because
 * doing so would reveal the answer during an image-identification quiz.
 *
 * @param country - Validated country and flag information.
 * @returns TypeScript source representing one QuizQuestion.
 */
function createQuestionSource(
  country: CountryFlagQuestionData,
): string {
  return `    {
      answer: ${quote(country.isoA3)},
      display: ${quote(country.name)},
      prompt: {
        type: "image",
        imageUrl: ${quote(
          `/data/country-flags/${country.flagFilename}`,
        )},
        alt: "Country flag",
      },
    }`;
}

/**
 * Creates the complete generated Country Flags quiz module.
 *
 * @param countries - Validated question data.
 * @returns Complete TypeScript source file.
 */
function createQuizSource(
  countries: CountryFlagQuestionData[],
): string {
  const questions = countries.map(createQuestionSource).join(",\n");

  return `/**
 * Global quiz for identifying countries and territories by their flags.
 *
 * This file is generated from GeoPedia's world-country GeoJSON and country
 * flag assets by:
 *
 *   scripts/generate/generate-global-country-flags-quiz.ts
 */

import type { Quiz } from "@/types/quiz";

/**
 * Global map quiz that displays a country flag and asks the player to select
 * its corresponding geographic feature on the world map.
 *
 * Quiz answers intentionally preserve the raw \`iso_a3\` values stored by
 * world-countries.geojson because that same property is used by the map's
 * feature interactions.
 */
export const countryFlagsQuiz: Quiz = {
  id: "country-flags",
  name: "Country Flags",

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
 * Generates and writes the Country Flags quiz.
 */
function main(): void {
  console.log("Generating global Country Flags quiz...\\n");

  const features = readWorldCountries();

  const flagFiles = getFlagFiles();

  const countries = createQuestionData(features, flagFiles);

  mkdirSync(path.dirname(OUTPUT_PATH), {
    recursive: true,
  });

  writeFileSync(OUTPUT_PATH, createQuizSource(countries), "utf8");

  console.log("GLOBAL COUNTRY FLAGS QUIZ GENERATION COMPLETE");
  console.log("---------------------------------------------");
  console.log(`World map features: ${features.length}`);
  console.log(`Country flags available: ${flagFiles.size}`);
  console.log(`Quiz questions generated: ${countries.length}`);
  console.log("");
  console.log("Quiz file: src/quiz/quizzes/global/countryFlags.ts");
}

main();
