/**
 * Generates GeoPedia's global Country Names quiz data from the processed
 * world-country GeoJSON and shared country-name metadata.
 *
 * The generated questions:
 *
 * - Contain one question for every mapped world-country feature.
 * - Use each country's ISO alpha-3 code as the quiz answer.
 * - Use the shared English country name as the English display.
 * - Include the shared native/local name as `nativeDisplay` when available.
 *
 * The processed world-country GeoJSON remains authoritative for which
 * geographic features appear in the quiz. GeoPedia's shared country-name
 * metadata supplies the user-facing English and optional native/local names.
 */

import fs from "node:fs";
import path from "node:path";

import { COUNTRY_NAMES } from "../../../../src/countries/countryNames";

/**
 * Processed geographic data used by GeoPedia's world-country map.
 */
const WORLD_COUNTRIES_PATH = path.resolve(
  "public/data/global/countries/geojson/world-countries.geojson",
);

/**
 * Generated Country Names question data.
 */
const OUTPUT_PATH = path.resolve(
  "src/quiz/quizzes/global/data/countryNames.ts",
);

/**
 * Properties required from each world-country GeoJSON feature.
 */
type WorldCountryProperties = {
  name: string;
  iso_a3: string;
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
 * Escapes a string as a safe TypeScript string literal.
 */
function quote(value: string): string {
  return JSON.stringify(value);
}

/**
 * Loads and parses the processed world-country GeoJSON.
 */
function loadWorldCountries(): WorldCountryFeatureCollection {
  if (!fs.existsSync(WORLD_COUNTRIES_PATH)) {
    throw new Error(
      `World country GeoJSON was not found: ${WORLD_COUNTRIES_PATH}`,
    );
  }

  const parsed = JSON.parse(
    fs.readFileSync(WORLD_COUNTRIES_PATH, "utf8"),
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
 * Every mapped feature must also have matching shared country-name metadata so
 * the generated quiz cannot silently fall out of sync with GeoPedia's shared
 * country identity data.
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

  const isoA3 = properties.iso_a3.trim();

  if (!COUNTRY_NAMES[isoA3]) {
    throw new Error(
      `No shared country-name metadata found for ` +
        `${properties.name} (${isoA3}).`,
    );
  }
}

/**
 * Ensures every mapped country has a unique ISO alpha-3 answer.
 */
function validateUniqueIsoCodes(
  features: WorldCountryFeature[],
): void {
  const seenIsoCodes = new Set<string>();

  for (const feature of features) {
    const isoA3 = feature.properties.iso_a3.trim();

    if (seenIsoCodes.has(isoA3)) {
      throw new Error(
        `Duplicate world-country iso_a3 value: ${isoA3}`,
      );
    }

    seenIsoCodes.add(isoA3);
  }
}

/**
 * Creates the generated TypeScript question-data module.
 *
 * Questions are sorted alphabetically by their shared English country name for
 * deterministic, readable output.
 */
function createSource(features: WorldCountryFeature[]): string {
  const sortedFeatures = [...features].sort((left, right) => {
    const leftIsoA3 = left.properties.iso_a3.trim();
    const rightIsoA3 = right.properties.iso_a3.trim();

    return COUNTRY_NAMES[leftIsoA3].name.localeCompare(
      COUNTRY_NAMES[rightIsoA3].name,
      "en",
    );
  });

  const questions = sortedFeatures
    .map((feature) => {
      const isoA3 = feature.properties.iso_a3.trim();
      const countryName = COUNTRY_NAMES[isoA3];

      const lines = [
        "  {",
        `    answer: ${quote(isoA3)},`,
        `    display: ${quote(countryName.name)},`,
      ];

      if (countryName.nativeName !== undefined) {
        lines.push(
          `    nativeDisplay: ${quote(countryName.nativeName)},`,
        );
      }

      lines.push("  },");

      return lines.join("\n");
    })
    .join("\n");

  return `/**
 * Generated Country Names quiz data.
 *
 * English and native/local displays come from GeoPedia's shared country-name
 * metadata. Native displays are included only when the shared metadata
 * provides a distinct native/local name.
 *
 * Do not edit manually.
 * Regenerate with:
 * npx tsx scripts/global/countries/quizzes/generate-country-names-quiz-data.ts
 */

export const COUNTRY_NAME_QUESTIONS = [
${questions}
];
`;
}

/**
 * Generates GeoPedia's global Country Names question data.
 */
function main(): void {
  console.log("Generating Country Names quiz data...");

  const featureCollection = loadWorldCountries();

  for (
    let index = 0;
    index < featureCollection.features.length;
    index++
  ) {
    validateFeature(featureCollection.features[index], index);
  }

  validateUniqueIsoCodes(featureCollection.features);

  const source = createSource(featureCollection.features);

  fs.mkdirSync(path.dirname(OUTPUT_PATH), {
    recursive: true,
  });

  fs.writeFileSync(OUTPUT_PATH, source, "utf8");

  const nativeDisplayCount = featureCollection.features.filter(
    (feature) => {
      const isoA3 = feature.properties.iso_a3.trim();

      return COUNTRY_NAMES[isoA3].nativeName !== undefined;
    },
  ).length;

  console.log(
    `Generated ${featureCollection.features.length} Country Names questions.`,
  );

  console.log(
    `Questions with distinct native displays: ${nativeDisplayCount}`,
  );

  console.log(`Output: ${OUTPUT_PATH}`);
}

main();
