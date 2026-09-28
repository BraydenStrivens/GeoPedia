/**
 * Generates the data used by Brazil's 2-digit CEP postal-code quiz.
 *
 * Source:
 *   public/data/countries/brazil/geojson/postal-codes.geojson
 *
 * Output:
 *   src/quiz/quizzes/countries/south-america/brazil/data/postalCodes.ts
 *
 * The processed runtime GeoJSON is authoritative for the represented CEP-2
 * answers and is validated before the quiz data is generated.
 */

import fs from "node:fs";
import path from "node:path";

const POSTAL_CODES_GEOJSON_PATH = path.resolve(
  "public/data/countries/brazil/geojson/postal-codes.geojson",
);

const OUTPUT_PATH = path.resolve(
  "src/quiz/quizzes/countries/south-america/brazil/data/postalCodes.ts",
);

const EXPECTED_FEATURE_COUNT = 84;
const EXPECTED_ANSWER_COUNT = 98;
const EXPECTED_MULTI_ANSWER_FEATURE_COUNT = 8;

const VALID_STATE_ABBREVIATIONS = new Set([
  "AC",
  "AL",
  "AP",
  "AM",
  "BA",
  "CE",
  "DF",
  "ES",
  "GO",
  "MA",
  "MT",
  "MS",
  "MG",
  "PA",
  "PB",
  "PR",
  "PE",
  "PI",
  "RJ",
  "RN",
  "RS",
  "RO",
  "RR",
  "SC",
  "SP",
  "SE",
  "TO",
]);

type BrazilPostalCodeProperties = {
  postal_codes: string[];
  first_digits: string[];
  states: string[];
};

type BrazilPostalCodeFeature = {
  type: "Feature";
  id: string;
  properties: BrazilPostalCodeProperties;
  geometry: unknown;
};

type BrazilPostalCodeFeatureCollection = {
  type: "FeatureCollection";
  features: BrazilPostalCodeFeature[];
};

function quote(value: string): string {
  return JSON.stringify(value);
}

function comparePostalCodes(first: string, second: string): number {
  return Number(first) - Number(second);
}

function loadPostalCodeGeoJson(): BrazilPostalCodeFeatureCollection {
  if (!fs.existsSync(POSTAL_CODES_GEOJSON_PATH)) {
    throw new Error(
      `Brazil postal-code GeoJSON was not found: ` +
        POSTAL_CODES_GEOJSON_PATH,
    );
  }

  const rawGeoJson = fs.readFileSync(
    POSTAL_CODES_GEOJSON_PATH,
    "utf8",
  );

  const parsed = JSON.parse(
    rawGeoJson,
  ) as BrazilPostalCodeFeatureCollection;

  if (
    parsed.type !== "FeatureCollection" ||
    !Array.isArray(parsed.features)
  ) {
    throw new Error(
      "Brazil postal-codes.geojson is not a valid FeatureCollection.",
    );
  }

  return parsed;
}

function isStringArray(value: unknown): value is string[] {
  return (
    Array.isArray(value) &&
    value.length > 0 &&
    value.every(
      (item) => typeof item === "string" && item.trim() !== "",
    )
  );
}

function validatePostalCode(value: string, featureId: string): void {
  if (!/^\d{2}$/.test(value)) {
    throw new Error(
      `Feature ${featureId} contains invalid CEP-2 value ` +
        `${JSON.stringify(value)}.`,
    );
  }
}

function validateFirstDigit(value: string, featureId: string): void {
  if (!/^\d$/.test(value)) {
    throw new Error(
      `Feature ${featureId} contains invalid first digit ` +
        `${JSON.stringify(value)}.`,
    );
  }
}

function validateState(value: string, featureId: string): void {
  if (!VALID_STATE_ABBREVIATIONS.has(value)) {
    throw new Error(
      `Feature ${featureId} contains unknown Brazilian state ` +
        `abbreviation ${JSON.stringify(value)}.`,
    );
  }
}

function validateFeature(
  feature: BrazilPostalCodeFeature,
  index: number,
): void {
  if (feature.type !== "Feature") {
    throw new Error(
      `Brazil postal-code feature ${index} is not a GeoJSON Feature.`,
    );
  }

  if (typeof feature.id !== "string" || feature.id.trim() === "") {
    throw new Error(
      `Brazil postal-code feature ${index} has no valid string ID.`,
    );
  }

  const properties = feature.properties;

  if (!properties || typeof properties !== "object") {
    throw new Error(
      `Brazil postal-code feature ${feature.id} has no valid properties.`,
    );
  }

  if (!isStringArray(properties.postal_codes)) {
    throw new Error(
      `Feature ${feature.id} has no valid postal_codes array.`,
    );
  }

  if (!isStringArray(properties.first_digits)) {
    throw new Error(
      `Feature ${feature.id} has no valid first_digits array.`,
    );
  }

  if (!isStringArray(properties.states)) {
    throw new Error(
      `Feature ${feature.id} has no valid states array.`,
    );
  }

  const postalCodes = properties.postal_codes;

  if (new Set(postalCodes).size !== postalCodes.length) {
    throw new Error(
      `Feature ${feature.id} contains duplicate postal-code answers.`,
    );
  }

  for (const postalCode of postalCodes) {
    validatePostalCode(postalCode, feature.id);
  }

  const firstDigits = properties.first_digits;

  if (new Set(firstDigits).size !== firstDigits.length) {
    throw new Error(
      `Feature ${feature.id} contains duplicate first-digit values.`,
    );
  }

  for (const firstDigit of firstDigits) {
    validateFirstDigit(firstDigit, feature.id);
  }

  const expectedFirstDigits = Array.from(
    new Set(postalCodes.map((postalCode) => postalCode[0])),
  ).sort();

  const actualFirstDigits = [...firstDigits].sort();

  if (
    JSON.stringify(actualFirstDigits) !==
    JSON.stringify(expectedFirstDigits)
  ) {
    throw new Error(
      `Feature ${feature.id} has inconsistent first_digits. ` +
        `Expected ${JSON.stringify(expectedFirstDigits)}, ` +
        `found ${JSON.stringify(actualFirstDigits)}.`,
    );
  }

  const states = properties.states;

  if (new Set(states).size !== states.length) {
    throw new Error(
      `Feature ${feature.id} contains duplicate state abbreviations.`,
    );
  }

  for (const state of states) {
    validateState(state, feature.id);
  }
}

function validateFeatureCollection(
  featureCollection: BrazilPostalCodeFeatureCollection,
): void {
  const features = featureCollection.features;

  if (features.length !== EXPECTED_FEATURE_COUNT) {
    throw new Error(
      `Expected ${EXPECTED_FEATURE_COUNT} Brazil postal-code features, ` +
        `found ${features.length}.`,
    );
  }

  const featureIds = new Set<string>();

  const answerSets = new Set<string>();

  let multiAnswerFeatureCount = 0;

  for (let index = 0; index < features.length; index++) {
    const feature = features[index];

    validateFeature(feature, index);

    if (featureIds.has(feature.id)) {
      throw new Error(
        `Duplicate Brazil postal-code feature ID: ${feature.id}`,
      );
    }

    featureIds.add(feature.id);

    const normalizedAnswerSet = [
      ...feature.properties.postal_codes,
    ].sort(comparePostalCodes);

    const answerSetKey = JSON.stringify(normalizedAnswerSet);

    if (answerSets.has(answerSetKey)) {
      throw new Error(
        `Duplicate complete postal-code answer set: ${answerSetKey}`,
      );
    }

    answerSets.add(answerSetKey);

    if (normalizedAnswerSet.length > 1) {
      multiAnswerFeatureCount++;
    }
  }

  if (
    multiAnswerFeatureCount !== EXPECTED_MULTI_ANSWER_FEATURE_COUNT
  ) {
    throw new Error(
      `Expected ${EXPECTED_MULTI_ANSWER_FEATURE_COUNT} multi-answer ` +
        `features, found ${multiAnswerFeatureCount}.`,
    );
  }
}

function collectPostalCodeAnswers(
  features: BrazilPostalCodeFeature[],
): string[] {
  const answers = new Set<string>();

  for (const feature of features) {
    for (const postalCode of feature.properties.postal_codes) {
      answers.add(postalCode);
    }
  }

  const sortedAnswers = Array.from(answers).sort(comparePostalCodes);

  if (sortedAnswers.length !== EXPECTED_ANSWER_COUNT) {
    throw new Error(
      `Expected ${EXPECTED_ANSWER_COUNT} distinct CEP-2 answers, ` +
        `found ${sortedAnswers.length}.`,
    );
  }

  return sortedAnswers;
}

function createQuestionSource(answer: string): string {
  return (
    `  { answer: ${quote(answer)}, ` +
    `display: ${quote(`${answer}---`)} },`
  );
}

function createDataSource(answers: string[]): string {
  const questions = answers.map(createQuestionSource).join("\n");

  return `/**
 * Generated from Brazil's processed CEP-2 postal-code GeoJSON.
 *
 * Do not edit manually.
 * Regenerate with:
 * npx tsx scripts/countries/brazil/generate/postal-codes-quiz-data.ts
 */

import type { FeatureQuiz } from "@/types/quiz";

export const BRAZIL_POSTAL_CODE_QUESTIONS: FeatureQuiz["questions"] = [
${questions}
];
`;
}

function main(): void {
  console.log("Generating Brazil postal-code quiz data...\n");

  const featureCollection = loadPostalCodeGeoJson();

  validateFeatureCollection(featureCollection);

  const answers = collectPostalCodeAnswers(
    featureCollection.features,
  );

  const generatedSource = createDataSource(answers);

  fs.mkdirSync(path.dirname(OUTPUT_PATH), {
    recursive: true,
  });

  fs.writeFileSync(OUTPUT_PATH, generatedSource, "utf8");

  const representedFirstDigits = new Set<string>();

  const representedStates = new Set<string>();

  for (const feature of featureCollection.features) {
    for (const firstDigit of feature.properties.first_digits) {
      representedFirstDigits.add(firstDigit);
    }

    for (const state of feature.properties.states) {
      representedStates.add(state);
    }
  }

  const multiAnswerFeatureCount = featureCollection.features.filter(
    (feature) => feature.properties.postal_codes.length > 1,
  ).length;

  console.log(
    `Runtime features:      ${featureCollection.features.length}`,
  );

  console.log(`Questions:             ${answers.length}`);

  console.log(`Multi-answer features: ${multiAnswerFeatureCount}`);

  console.log(
    `First-digit groups:    ${representedFirstDigits.size}`,
  );

  console.log(`State groups:          ${representedStates.size}`);

  console.log(`\nGenerated: ${OUTPUT_PATH}`);
}

main();
