/**
 * Generates GeoPedia's Brazil 2-Digit Postal Codes quiz from the processed
 * runtime CEP-2 GeoJSON.
 *
 * Runtime source:
 *
 *   public/data/countries/brazil/geojson/postal-codes.geojson
 *
 * Generated quiz:
 *
 *   src/quiz/quizzes/countries/brazil/postalCodesQuiz.ts
 *
 * The runtime GeoJSON is authoritative for which CEP-2 answers exist.
 *
 * Each geographic feature stores:
 *
 *   postal_codes: string[]
 *   first_digits: string[]
 *   states: string[]
 *
 * Most features contain one postal-code answer:
 *
 *   ["77"]
 *
 * Some municipalities contain several valid CEP-2 answers:
 *
 *   ["20", "21", "22", "23"]
 *
 * Because a single quiz answer may therefore be valid for more than one
 * geographic feature, the generated quiz uses:
 *
 *   answerProperty: "postal_codes"
 *   answerType: "multiple"
 *
 * Questions are generated from the union of every `postal_codes` array in the
 * runtime GeoJSON and sorted numerically.
 */

import fs from "node:fs";
import path from "node:path";

/* -------------------------------------------------------------------------- */
/* Paths                                                                      */
/* -------------------------------------------------------------------------- */

const POSTAL_CODES_GEOJSON_PATH = path.resolve(
  "public/data/countries/brazil/geojson/postal-codes.geojson",
);

const OUTPUT_PATH = path.resolve(
  "src/quiz/quizzes/country/brazil/postalCodesQuiz.ts",
);

/* -------------------------------------------------------------------------- */
/* Expected dataset structure                                                 */
/* -------------------------------------------------------------------------- */

const EXPECTED_FEATURE_COUNT = 84;
const EXPECTED_ANSWER_COUNT = 98;
const EXPECTED_MULTI_ANSWER_FEATURE_COUNT = 8;

/* -------------------------------------------------------------------------- */
/* Brazil state metadata                                                      */
/* -------------------------------------------------------------------------- */

/**
 * User-facing Brazilian state names keyed by the two-letter UF abbreviations
 * stored in the runtime postal-code GeoJSON.
 */
const BRAZIL_STATE_NAMES_BY_ABBREVIATION = {
  AC: "Acre",
  AL: "Alagoas",
  AP: "Amapá",
  AM: "Amazonas",
  BA: "Bahia",
  CE: "Ceará",
  DF: "Distrito Federal",
  ES: "Espírito Santo",
  GO: "Goiás",
  MA: "Maranhão",
  MT: "Mato Grosso",
  MS: "Mato Grosso do Sul",
  MG: "Minas Gerais",
  PA: "Pará",
  PB: "Paraíba",
  PR: "Paraná",
  PE: "Pernambuco",
  PI: "Piauí",
  RJ: "Rio de Janeiro",
  RN: "Rio Grande do Norte",
  RS: "Rio Grande do Sul",
  RO: "Rondônia",
  RR: "Roraima",
  SC: "Santa Catarina",
  SP: "São Paulo",
  SE: "Sergipe",
  TO: "Tocantins",
} as const;

/* -------------------------------------------------------------------------- */
/* GeoJSON types                                                              */
/* -------------------------------------------------------------------------- */

/**
 * Runtime properties required by the Brazil postal-code quiz.
 */
type BrazilPostalCodeProperties = {
  /**
   * Complete set of valid two-digit CEP answers represented by the feature.
   */
  postal_codes: string[];

  /**
   * First digits represented by the feature's postal-code answer set.
   *
   * This is an array because a multi-answer feature may cross first-digit
   * groups. For example, one feature could theoretically contain both a 7x
   * and an 8x answer.
   */
  first_digits: string[];

  /**
   * Brazilian state / Federal District abbreviations intersected by the
   * feature.
   */
  states: string[];
};

/**
 * Minimal runtime feature representation required by this generator.
 */
type BrazilPostalCodeFeature = {
  type: "Feature";

  /**
   * Stable logical feature ID written by the Brazil postal runtime processor.
   */
  id: string;

  properties: BrazilPostalCodeProperties;

  geometry: unknown;
};

/**
 * Runtime Brazil CEP-2 FeatureCollection.
 */
type BrazilPostalCodeFeatureCollection = {
  type: "FeatureCollection";

  features: BrazilPostalCodeFeature[];
};

/* -------------------------------------------------------------------------- */
/* General helpers                                                            */
/* -------------------------------------------------------------------------- */

/**
 * Converts a string into a safe TypeScript string literal.
 */
function quote(value: string): string {
  return JSON.stringify(value);
}

/**
 * Sorts two two-digit postal-code strings numerically.
 */
function comparePostalCodes(first: string, second: string): number {
  return Number(first) - Number(second);
}

/**
 * Reads and parses the runtime Brazil postal-code GeoJSON.
 */
function loadPostalCodeGeoJson(): BrazilPostalCodeFeatureCollection {
  if (!fs.existsSync(POSTAL_CODES_GEOJSON_PATH)) {
    throw new Error(
      `Brazil postal-code GeoJSON was not found: ${POSTAL_CODES_GEOJSON_PATH}`,
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

/**
 * Returns whether a value is a non-empty array containing only strings.
 */
function isStringArray(value: unknown): value is string[] {
  return (
    Array.isArray(value) &&
    value.length > 0 &&
    value.every(
      (item) => typeof item === "string" && item.trim() !== "",
    )
  );
}

/**
 * Validates one two-digit CEP prefix.
 */
function validatePostalCode(value: string, featureId: string): void {
  if (!/^\d{2}$/.test(value)) {
    throw new Error(
      `Feature ${featureId} contains invalid CEP-2 value ${JSON.stringify(
        value,
      )}.`,
    );
  }
}

/**
 * Validates one first-digit grouping value.
 */
function validateFirstDigit(value: string, featureId: string): void {
  if (!/^\d$/.test(value)) {
    throw new Error(
      `Feature ${featureId} contains invalid first digit ${JSON.stringify(
        value,
      )}.`,
    );
  }
}

/**
 * Validates one Brazilian state abbreviation.
 */
function validateState(value: string, featureId: string): void {
  if (
    !Object.prototype.hasOwnProperty.call(
      BRAZIL_STATE_NAMES_BY_ABBREVIATION,
      value,
    )
  ) {
    throw new Error(
      `Feature ${featureId} contains unknown Brazilian state abbreviation ` +
        `${JSON.stringify(value)}.`,
    );
  }
}

/* -------------------------------------------------------------------------- */
/* Feature validation                                                         */
/* -------------------------------------------------------------------------- */

/**
 * Validates one runtime postal-code feature.
 */
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

/* -------------------------------------------------------------------------- */
/* Dataset validation                                                         */
/* -------------------------------------------------------------------------- */

/**
 * Validates the complete runtime dataset before generating quiz source.
 */
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

/* -------------------------------------------------------------------------- */
/* Question extraction                                                        */
/* -------------------------------------------------------------------------- */

/**
 * Collects every distinct two-digit CEP answer represented anywhere in the
 * runtime map.
 */
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

/* -------------------------------------------------------------------------- */
/* Generated TypeScript                                                       */
/* -------------------------------------------------------------------------- */

/**
 * Creates the TypeScript source for one quiz question.
 */
function createQuestionSource(answer: string): string {
  return `  { answer: ${quote(answer)}, display: ${quote(`${answer}---`)} },`;
}

/**
 * Creates the generated state-label mapping.
 */
function createStateLabelSource(): string {
  const entries = Object.entries(BRAZIL_STATE_NAMES_BY_ABBREVIATION);

  const lines = entries.map(
    ([abbreviation, name]) =>
      `  ${quote(abbreviation)}: ${quote(name)},`,
  );

  return [
    "const BRAZIL_STATE_NAMES_BY_ABBREVIATION: Record<string, string> = {",
    ...lines,
    "};",
  ].join("\n");
}

/**
 * Generates the complete Brazil postal-code quiz module.
 */
function createQuizSource(answers: string[]): string {
  const questions = answers.map(createQuestionSource).join("\n");

  const stateLabels = createStateLabelSource();

  return `/**
 * AUTO-GENERATED FILE.
 *
 * Generated by:
 *
 *   scripts/countries/brazil/generate/generate-postal-codes-quiz.ts
 *
 * Do not edit the question list manually. Update Brazil's processed runtime
 * postal-code GeoJSON or this generator and rerun the script instead.
 */

import type { FeatureQuiz } from "@/types/quiz";

/**
 * Brazilian state and Federal District names keyed by the UF abbreviations
 * stored in the postal-code GeoJSON.
 */
${stateLabels}

/**
 * Every distinct two-digit CEP prefix represented by the processed Brazil
 * postal-code map.
 */
const BRAZIL_POSTAL_CODE_QUESTIONS: FeatureQuiz["questions"] = [
${questions}
];

/**
 * Tests recognition of Brazil's geographic two-digit CEP postal-code prefixes.
 *
 * Some geographic features contain several valid CEP prefixes, so the quiz
 * uses GeoPedia's multiple-answer feature semantics. Selecting any feature
 * whose \`postal_codes\` array contains the current question is valid.
 */
export const brazilPostalCodesQuiz: FeatureQuiz = {
  id: "brazil-postal-codes",
  name: "2 Digit Postal Codes",
  description: \`Learn Brazil's \${BRAZIL_POSTAL_CODE_QUESTIONS.length} represented 2-digit CEP postal-code prefixes, with filters to practice prefixes by first digit or state.\`,

  kind: "feature",
  mapId: "brazil-postal-codes",

  answerProperty: "postal_codes",
  answerType: "multiple",

  grouping: {
    properties: [
      {
        property: "first_digits",
        label: "First Digit",
        valueType: "string-array",
      },
      {
        property: "states",
        label: "State",
        valueType: "string-array",
        valueLabels: BRAZIL_STATE_NAMES_BY_ABBREVIATION,
      },
    ],
  },

  questions: BRAZIL_POSTAL_CODE_QUESTIONS,
};
`;
}

/* -------------------------------------------------------------------------- */
/* Generation                                                                 */
/* -------------------------------------------------------------------------- */

/**
 * Generates and writes GeoPedia's Brazil 2-Digit Postal Codes quiz.
 */
function main(): void {
  console.log("Generating Brazil 2-Digit Postal Codes quiz...");

  const featureCollection = loadPostalCodeGeoJson();

  validateFeatureCollection(featureCollection);

  const answers = collectPostalCodeAnswers(
    featureCollection.features,
  );

  const generatedSource = createQuizSource(answers);

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

  console.log("");
  console.log(
    `Runtime features:          ${featureCollection.features.length}`,
  );
  console.log(`Generated questions:       ${answers.length}`);
  console.log(
    `Multi-answer features:     ${multiAnswerFeatureCount}`,
  );
  console.log(
    `First-digit groups:        ${representedFirstDigits.size}`,
  );
  console.log(`State groups:              ${representedStates.size}`);
  console.log(`Answers:                   ${answers.join(", ")}`);
  console.log("");
  console.log(`Output: ${OUTPUT_PATH}`);
}

main();
