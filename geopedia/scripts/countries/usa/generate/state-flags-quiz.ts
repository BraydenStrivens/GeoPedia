/**
 * Generates GeoPedia's U.S. State Flags feature quiz.
 *
 * State names and postal abbreviations are derived from GeoPedia's canonical
 * U.S. subdivision-name mapping rather than duplicated in this generator.
 *
 * Each question uses:
 *
 * - The full state name as the map answer because the U.S. states map quizzes
 *   identify features through their `name` property.
 * - The full state name as the display value.
 * - The state's two-letter postal abbreviation to locate its flag SVG.
 *
 * State flag assets are expected at:
 *
 * public/data/countries/usa/flags/{state-abbreviation}.svg
 *
 * Output:
 *
 * src/quiz/quizzes/usa/usStatesFlags.ts
 *
 * Run with:
 *
 * npx tsx scripts/countries/usa/generate/generate-state-flags-quiz.ts
 */

import fs from "node:fs";
import path from "node:path";

import { US_SUBDIVISION_NAMES_BY_ABBREVIATION } from "@/constants/usSubdivisions";

/* -------------------------------------------------------------------------- */
/* Paths                                                                      */
/* -------------------------------------------------------------------------- */

/**
 * Directory containing the downloaded U.S. state flag SVGs.
 */
const STATE_FLAGS_DIRECTORY = path.resolve(
  "public/data/countries/usa/flags",
);

/**
 * Generated U.S. State Flags quiz configuration.
 */
const OUTPUT_PATH = path.resolve(
  "src/quiz/quizzes/usa/usStatesFlags.ts",
);

/* -------------------------------------------------------------------------- */
/* State data                                                                 */
/* -------------------------------------------------------------------------- */

/**
 * U.S. subdivision abbreviations that should not appear in the State Flags
 * quiz.
 *
 * The canonical subdivision-name mapping includes the 50 states along with
 * Washington, D.C. and U.S. territories. These entries are excluded so this
 * quiz contains exactly the 50 states.
 */
const NON_STATE_ABBREVIATIONS = new Set([
  "AS",
  "DC",
  "GU",
  "MP",
  "PR",
  "VI",
]);

/**
 * State metadata required to construct one State Flags quiz question.
 */
type StateDefinition = {
  /** Full state name used by the U.S. states map's `name` property. */
  name: string;

  /** Two-letter postal abbreviation used to locate the state's flag asset. */
  abbreviation: string;
};

/**
 * The 50 U.S. states derived from GeoPedia's canonical subdivision-name map.
 *
 * Object insertion order is preserved, so the generated quiz follows the same
 * state ordering as US_SUBDIVISION_NAMES_BY_ABBREVIATION.
 */
const STATES: StateDefinition[] = Object.entries(
  US_SUBDIVISION_NAMES_BY_ABBREVIATION,
)
  .filter(
    ([abbreviation]) => !NON_STATE_ABBREVIATIONS.has(abbreviation),
  )
  .map(([abbreviation, name]) => ({
    abbreviation,
    name,
  }));

/* -------------------------------------------------------------------------- */
/* Validation                                                                 */
/* -------------------------------------------------------------------------- */

/**
 * Verifies that the canonical subdivision mapping produces exactly the 50
 * expected states.
 */
function validateStates(): void {
  if (STATES.length !== 50) {
    throw new Error(
      `Expected 50 U.S. states but found ${STATES.length}.`,
    );
  }

  const abbreviations = new Set(
    STATES.map((state) => state.abbreviation),
  );

  if (abbreviations.size !== STATES.length) {
    throw new Error(
      "State definitions contain duplicate postal abbreviations.",
    );
  }

  const names = new Set(STATES.map((state) => state.name));

  if (names.size !== STATES.length) {
    throw new Error(
      "State definitions contain duplicate state names.",
    );
  }

  for (const state of STATES) {
    if (!/^[A-Z]{2}$/.test(state.abbreviation)) {
      throw new Error(
        `Invalid postal abbreviation for ${state.name}: ${state.abbreviation}`,
      );
    }

    if (!state.name.trim()) {
      throw new Error(
        `State ${state.abbreviation} is missing a name.`,
      );
    }
  }
}

/**
 * Verifies that every generated State Flags question has a corresponding SVG
 * in GeoPedia's public runtime assets.
 */
function validateFlagAssets(): void {
  const missingFlags: string[] = [];

  for (const state of STATES) {
    const fileName = `${state.abbreviation.toLowerCase()}.svg`;

    const filePath = path.join(STATE_FLAGS_DIRECTORY, fileName);

    if (!fs.existsSync(filePath)) {
      missingFlags.push(`${state.name} (${fileName})`);
    }
  }

  if (missingFlags.length === 0) {
    return;
  }

  throw new Error(
    [
      "Missing U.S. state flag assets:",
      "",
      ...missingFlags.map((flag) => `  - ${flag}`),
    ].join("\n"),
  );
}

/* -------------------------------------------------------------------------- */
/* Source generation                                                          */
/* -------------------------------------------------------------------------- */

/**
 * Serializes a string as a valid TypeScript string literal.
 */
function quote(value: string): string {
  return JSON.stringify(value);
}

/**
 * Creates the TypeScript source for one State Flags quiz question.
 */
function createQuestionSource(state: StateDefinition): string {
  const flagUrl = `/data/countries/usa/flags/${state.abbreviation.toLowerCase()}.svg`;

  return [
    "  {",
    `    answer: ${quote(state.name)},`,
    `    display: ${quote(state.name)},`,
    "    prompt: {",
    '      type: "image",',
    `      imageUrl: ${quote(flagUrl)},`,
    '      alt: "State flag",',
    "    },",
    "  },",
  ].join("\n");
}

/**
 * Creates the complete generated U.S. State Flags quiz module.
 */
function createQuizSource(): string {
  const questions = STATES.map(createQuestionSource).join("\n");

  return `/**
 * AUTO-GENERATED FILE.
 *
 * Generated by:
 *
 *   scripts/countries/usa/generate/generate-state-flags-quiz.ts
 *
 * Do not edit the question list manually. Update the canonical U.S.
 * subdivision-name mapping, state flag assets, or generator and rerun the
 * script instead.
 */

import type { FeatureQuiz } from "@/types/quiz";

/**
 * Description shown for the U.S. State Flags quiz.
 */
const US_STATES_FLAGS_DESCRIPTION =
  "Learn the flags of all 50 U.S. states by identifying each state on the map.";

/**
 * Questions used by the U.S. State Flags quiz.
 *
 * Each answer is the full state name because the shared U.S. states map
 * identifies features through its \`name\` property. Postal abbreviations are
 * used only to resolve the corresponding flag SVG.
 */
const US_STATE_FLAG_QUESTIONS: FeatureQuiz["questions"] = [
${questions}
];

/**
 * Tests recognition of the flags of all 50 U.S. states.
 */
export const usStateFlagsQuiz: FeatureQuiz = {
  id: "us-state-flags",

  name: "US State Flags",

  description: US_STATES_FLAGS_DESCRIPTION,

  kind: "feature",

  mapId: "us-states",

  answerProperty: "name",

  answerType: "single",

  grouping: {
    properties: [
      {
        property: "region",
        label: "Region",
        valueType: "string",
      },
    ],
  },

  questions: US_STATE_FLAG_QUESTIONS,
};
`;
}

/* -------------------------------------------------------------------------- */
/* Main                                                                       */
/* -------------------------------------------------------------------------- */

/**
 * Validates the source data and assets before generating the State Flags quiz.
 */
function main(): void {
  console.log("Generating U.S. State Flags quiz...");

  validateStates();
  validateFlagAssets();

  const source = createQuizSource();

  fs.mkdirSync(path.dirname(OUTPUT_PATH), {
    recursive: true,
  });

  fs.writeFileSync(OUTPUT_PATH, source, "utf8");

  console.log("");

  console.log(
    `Generated ${STATES.length} U.S. State Flags questions.`,
  );

  console.log(`Output: ${OUTPUT_PATH}`);
}

main();
