/**
 * Generates GeoPedia's global Country Names quiz from the processed world
 * country GeoJSON.
 *
 * The generated quiz:
 *
 * - Contains one question for every geographic feature in
 *   `world-countries.geojson`.
 * - Uses each country's ISO alpha-3 code as the quiz answer.
 * - Uses the country's user-facing name as the displayed question.
 * - Uses the same `world-countries` MapConfig as the Country Flags quiz.
 * - Supports the same continent, region, and subregion grouping properties.
 *
 * The processed world GeoJSON is used as the authoritative country list
 * because it represents the exact geographic features that can be selected on
 * the quiz map.
 */

import fs from "node:fs";
import path from "node:path";

/**
 * Input GeoJSON containing every country represented by the world quiz map.
 */
const WORLD_COUNTRIES_PATH = path.resolve(
  "public/data/geojson/world/world-countries.geojson",
);

/**
 * Generated TypeScript quiz definition.
 */
const OUTPUT_PATH = path.resolve(
  "src/quiz/quizzes/global/countryNames.ts",
);

/**
 * Properties required from each world-country GeoJSON feature.
 */
type WorldCountryProperties = {
  /** User-facing country name. */
  name: string;

  /** ISO alpha-3 identifier used by the world quiz map. */
  iso_a3: string;

  /** Broad continent used by property-based quiz grouping. */
  continent?: string;

  /** Geographic region used by property-based quiz grouping. */
  region?: string;

  /** Geographic subregion used by property-based quiz grouping. */
  subregion?: string;

  /** Whether this geography is included by GeoPedia's GeoGuessr filter. */
  geoguessr?: boolean;
};

/**
 * Minimal GeoJSON feature representation required by this generator.
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
 * Escapes a value so it can safely be written inside a generated TypeScript
 * string literal.
 *
 * JSON.stringify is used rather than manually escaping quotation marks,
 * backslashes, Unicode characters, or other special characters.
 *
 * @param value - String written into generated TypeScript.
 * @returns Valid double-quoted TypeScript string literal.
 */
function quote(value: string): string {
  return JSON.stringify(value);
}

/**
 * Loads and parses the processed world-country GeoJSON.
 *
 * @returns Parsed world country FeatureCollection.
 */
function loadWorldCountries(): WorldCountryFeatureCollection {
  if (!fs.existsSync(WORLD_COUNTRIES_PATH)) {
    throw new Error(
      `World country GeoJSON was not found: ${WORLD_COUNTRIES_PATH}`,
    );
  }

  const rawGeoJson = fs.readFileSync(WORLD_COUNTRIES_PATH, "utf8");

  const parsed = JSON.parse(
    rawGeoJson,
  ) as WorldCountryFeatureCollection;

  if (
    parsed.type !== "FeatureCollection" ||
    !Array.isArray(parsed.features)
  ) {
    throw new Error(
      "world-countries.geojson is not a valid GeoJSON FeatureCollection.",
    );
  }

  return parsed;
}

/**
 * Validates one world-country feature before it becomes a quiz question.
 *
 * Country Names requires only:
 *
 * - `name`
 * - `iso_a3`
 *
 * The ISO code is used as the quiz answer because the world map exposes that
 * property through `answerProperty: "iso_a3"`.
 *
 * @param feature - World-country feature to validate.
 * @param index - Feature position used to produce useful error messages.
 */
function validateFeature(
  feature: WorldCountryFeature,
  index: number,
): void {
  const { properties } = feature;

  if (!properties) {
    throw new Error(
      `World country feature ${index} has no properties.`,
    );
  }

  if (
    typeof properties.name !== "string" ||
    properties.name.trim() === ""
  ) {
    throw new Error(
      `World country feature ${index} has no valid name.`,
    );
  }

  if (
    typeof properties.iso_a3 !== "string" ||
    properties.iso_a3.trim() === ""
  ) {
    throw new Error(
      `World country "${properties.name}" has no valid iso_a3 value.`,
    );
  }
}

/**
 * Generates one Country Names quiz question.
 *
 * Example:
 *
 * {
 *   answer: "USA",
 *   display: "United States",
 * }
 *
 * `display` becomes the question presented to the user, while `answer`
 * corresponds to the selected map feature's `iso_a3` value.
 *
 * @param feature - Country represented by the generated question.
 * @returns Generated TypeScript source for one question object.
 */
function createQuestionSource(feature: WorldCountryFeature): string {
  const { name, iso_a3 } = feature.properties;

  return [
    "    {",
    `      answer: ${quote(iso_a3)},`,
    `      display: ${quote(name)},`,
    "    },",
  ].join("\n");
}

/**
 * Generates the complete Country Names quiz TypeScript module.
 *
 * Questions are sorted alphabetically by country name so regenerated files
 * produce deterministic, readable Git diffs.
 *
 * @param features - Valid world-country features.
 * @returns Complete generated TypeScript source.
 */
function createQuizSource(features: WorldCountryFeature[]): string {
  const sortedFeatures = [...features].sort((left, right) =>
    left.properties.name.localeCompare(right.properties.name, "en"),
  );

  const questions = sortedFeatures
    .map(createQuestionSource)
    .join("\n");

  return `/**
 * AUTO-GENERATED FILE.
 *
 * Generated by:
 *
 *   scripts/generateCountryNamesQuiz.ts
 *
 * Do not edit the question list manually. Update the source world-country
 * data or generator and rerun the script instead.
 */

import type { Quiz } from "@/types/quiz";

/**
 * Tests recognition of countries by name on GeoPedia's global country map.
 *
 * Each question displays a country name and expects the user to select the
 * corresponding geographic country.
 */
export const countryNamesQuiz: Quiz = {
  id: "country-names",
  name: "Country Names",

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
 * Generates and writes the Country Names quiz.
 */
function main(): void {
  console.log("Generating Country Names quiz...");

  const featureCollection = loadWorldCountries();

  for (
    let index = 0;
    index < featureCollection.features.length;
    index++
  ) {
    validateFeature(featureCollection.features[index], index);
  }

  /**
   * Ensure ISO alpha-3 values are unique. Duplicate answers would cause two
   * geographic features to represent the same quiz question.
   */
  const seenIsoCodes = new Set<string>();

  for (const feature of featureCollection.features) {
    const isoA3 = feature.properties.iso_a3;

    if (seenIsoCodes.has(isoA3)) {
      throw new Error(
        `Duplicate world-country iso_a3 value: ${isoA3}`,
      );
    }

    seenIsoCodes.add(isoA3);
  }

  const source = createQuizSource(featureCollection.features);

  fs.mkdirSync(path.dirname(OUTPUT_PATH), {
    recursive: true,
  });

  fs.writeFileSync(OUTPUT_PATH, source, "utf8");

  console.log(
    `Generated ${featureCollection.features.length} Country Names questions.`,
  );

  console.log(`Output: ${OUTPUT_PATH}`);
}

main();
