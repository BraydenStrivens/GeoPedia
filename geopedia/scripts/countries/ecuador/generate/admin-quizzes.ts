/**
 * Generates Ecuador's Canton and Parish quizzes from the processed runtime
 * administrative GeoJSON files.
 *
 * Sources:
 *
 *   public/data/countries/ecuador/geojson/cantons.geojson
 *   public/data/countries/ecuador/geojson/parishes.geojson
 *
 * Outputs:
 *
 *   src/quiz/quizzes/countries/ecuador/cantonsQuiz.ts
 *   src/quiz/quizzes/countries/ecuador/parishesQuiz.ts
 *
 * The runtime GeoJSON is treated as the authoritative source for quiz
 * questions and administrative grouping values.
 */

import fs from "node:fs";
import path from "node:path";

/* -------------------------------------------------------------------------- */
/* Paths                                                                      */
/* -------------------------------------------------------------------------- */

const CANTONS_GEOJSON_PATH = path.resolve(
  "public/data/countries/ecuador/geojson/cantons.geojson",
);

const PARISHES_GEOJSON_PATH = path.resolve(
  "public/data/countries/ecuador/geojson/parishes.geojson",
);

const CANTONS_OUTPUT_PATH = path.resolve(
  "src/quiz/quizzes/countries/ecuador/cantonsQuiz.ts",
);

const PARISHES_OUTPUT_PATH = path.resolve(
  "src/quiz/quizzes/countries/ecuador/parishesQuiz.ts",
);

/* -------------------------------------------------------------------------- */
/* Expected source structure                                                  */
/* -------------------------------------------------------------------------- */

const EXPECTED_CANTON_COUNT = 221;
const EXPECTED_PARISH_COUNT = 1_042;

/* -------------------------------------------------------------------------- */
/* GeoJSON types                                                              */
/* -------------------------------------------------------------------------- */

type CantonProperties = {
  canton_id: string;
  canton: string;
  province_id: string;
  province: string;
};

type ParishProperties = {
  parish_id: string;
  parish: string;
  canton_id: string;
  canton: string;
  province_id: string;
  province: string;
};

type GeoJsonFeature<TProperties> = {
  type: "Feature";
  id?: string | number;
  properties: TProperties;
  geometry: unknown;
};

type GeoJsonFeatureCollection<TProperties> = {
  type: "FeatureCollection";
  features: GeoJsonFeature<TProperties>[];
};

/* -------------------------------------------------------------------------- */
/* Quiz-entry types                                                           */
/* -------------------------------------------------------------------------- */

type CantonQuizEntry = {
  answer: string;
  display: string;
  province: string;
};

type ParishQuizEntry = {
  answer: string;
  display: string;
  canton: string;
  province: string;
};

/* -------------------------------------------------------------------------- */
/* Generic helpers                                                            */
/* -------------------------------------------------------------------------- */

/**
 * Escapes a value as a valid TypeScript string literal.
 */
function quote(value: string): string {
  return JSON.stringify(value);
}

/**
 * Loads and parses one JSON file.
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
 * Ensures a required property is a non-empty string.
 */
function requireString(
  value: unknown,
  propertyName: string,
  featureIndex: number,
): string {
  if (typeof value !== "string" || value.trim() === "") {
    throw new Error(
      `Feature ${featureIndex} has invalid ${propertyName}.`,
    );
  }

  return value.trim();
}

/**
 * Writes generated TypeScript source to disk.
 */
function writeGeneratedFile(
  outputPath: string,
  source: string,
): void {
  fs.mkdirSync(path.dirname(outputPath), {
    recursive: true,
  });

  fs.writeFileSync(outputPath, source, "utf8");
}

/* -------------------------------------------------------------------------- */
/* Canton loading                                                             */
/* -------------------------------------------------------------------------- */

/**
 * Loads and validates Ecuador's canton runtime geography.
 */
function loadCantons(): CantonQuizEntry[] {
  const featureCollection = readJson<
    GeoJsonFeatureCollection<CantonProperties>
  >(CANTONS_GEOJSON_PATH);

  if (
    featureCollection.type !== "FeatureCollection" ||
    !Array.isArray(featureCollection.features)
  ) {
    throw new Error(
      "Ecuador canton GeoJSON is not a valid FeatureCollection.",
    );
  }

  if (featureCollection.features.length !== EXPECTED_CANTON_COUNT) {
    throw new Error(
      `Expected ${EXPECTED_CANTON_COUNT} Ecuador cantons, got ` +
        `${featureCollection.features.length}.`,
    );
  }

  const entries: CantonQuizEntry[] = [];
  const seenIds = new Set<string>();

  featureCollection.features.forEach((feature, index) => {
    if (!feature.properties) {
      throw new Error(`Canton feature ${index} has no properties.`);
    }

    const cantonId = requireString(
      feature.properties.canton_id,
      "canton_id",
      index,
    );

    const canton = requireString(
      feature.properties.canton,
      "canton",
      index,
    );

    requireString(
      feature.properties.province_id,
      "province_id",
      index,
    );

    const province = requireString(
      feature.properties.province,
      "province",
      index,
    );

    if (seenIds.has(cantonId)) {
      throw new Error(`Duplicate Ecuador canton ID: ${cantonId}`);
    }

    seenIds.add(cantonId);

    if (feature.id !== undefined && String(feature.id) !== cantonId) {
      throw new Error(
        `Canton ${cantonId} has GeoJSON feature ID ` +
          `${String(feature.id)}, which does not match canton_id.`,
      );
    }

    entries.push({
      answer: cantonId,
      display: canton,
      province,
    });
  });

  return entries;
}

/* -------------------------------------------------------------------------- */
/* Parish loading                                                             */
/* -------------------------------------------------------------------------- */

/**
 * Loads and validates Ecuador's parish runtime geography.
 */
function loadParishes(): ParishQuizEntry[] {
  const featureCollection = readJson<
    GeoJsonFeatureCollection<ParishProperties>
  >(PARISHES_GEOJSON_PATH);

  if (
    featureCollection.type !== "FeatureCollection" ||
    !Array.isArray(featureCollection.features)
  ) {
    throw new Error(
      "Ecuador parish GeoJSON is not a valid FeatureCollection.",
    );
  }

  if (featureCollection.features.length !== EXPECTED_PARISH_COUNT) {
    throw new Error(
      `Expected ${EXPECTED_PARISH_COUNT} Ecuador parishes, got ` +
        `${featureCollection.features.length}.`,
    );
  }

  const entries: ParishQuizEntry[] = [];
  const seenIds = new Set<string>();

  featureCollection.features.forEach((feature, index) => {
    if (!feature.properties) {
      throw new Error(`Parish feature ${index} has no properties.`);
    }

    const parishId = requireString(
      feature.properties.parish_id,
      "parish_id",
      index,
    );

    const parish = requireString(
      feature.properties.parish,
      "parish",
      index,
    );

    requireString(feature.properties.canton_id, "canton_id", index);

    const canton = requireString(
      feature.properties.canton,
      "canton",
      index,
    );

    requireString(
      feature.properties.province_id,
      "province_id",
      index,
    );

    const province = requireString(
      feature.properties.province,
      "province",
      index,
    );

    if (seenIds.has(parishId)) {
      throw new Error(`Duplicate Ecuador parish ID: ${parishId}`);
    }

    seenIds.add(parishId);

    if (feature.id !== undefined && String(feature.id) !== parishId) {
      throw new Error(
        `Parish ${parishId} has GeoJSON feature ID ` +
          `${String(feature.id)}, which does not match parish_id.`,
      );
    }

    entries.push({
      answer: parishId,
      display: parish,
      canton,
      province,
    });
  });

  return entries;
}

/* -------------------------------------------------------------------------- */
/* Question generation                                                        */
/* -------------------------------------------------------------------------- */

/**
 * Generates one feature-quiz question.
 */
function createQuestionSource(
  answer: string,
  display: string,
): string {
  return [
    "  {",
    `    answer: ${quote(answer)},`,
    `    display: ${quote(display)},`,
    "  },",
  ].join("\n");
}

/* -------------------------------------------------------------------------- */
/* Canton quiz generation                                                     */
/* -------------------------------------------------------------------------- */

/**
 * Generates the complete Ecuador Cantons quiz module.
 */
function createCantonsQuizSource(entries: CantonQuizEntry[]): string {
  const sortedEntries = [...entries].sort(
    (left, right) =>
      left.display.localeCompare(right.display, "es") ||
      left.answer.localeCompare(right.answer, "en"),
  );

  const questions = sortedEntries
    .map((entry) => createQuestionSource(entry.answer, entry.display))
    .join("\n");

  return `/**
 * AUTO-GENERATED FILE.
 *
 * Generated by:
 *
 *   scripts/countries/ecuador/generate/generate-admin-quizzes.ts
 *
 * Do not edit the question list manually. Update Ecuador's processed
 * administrative GeoJSON or the generator and regenerate this file instead.
 */

import type { FeatureQuiz } from "@/types/quiz";

/**
 * Ecuador's canton quiz questions.
 */
const ECUADOR_CANTON_QUESTIONS: FeatureQuiz["questions"] = [
${questions}
];

/**
 * Description shown for Ecuador's Cantons quiz.
 */
const ECUADOR_CANTONS_DESCRIPTION =
  \`Learn all \${ECUADOR_CANTON_QUESTIONS.length} cantons of Ecuador and \` +
  \`where they are located across the country. Use the Province grouping to \` +
  \`learn the cantons one province at a time.\`;

/**
 * Quiz configuration for Ecuador's cantons.
 */
export const ecuadorCantonsQuiz: FeatureQuiz = {
  id: "ecuador-cantons",
  name: "Cantons",
  description: ECUADOR_CANTONS_DESCRIPTION,

  kind: "feature",
  mapId: "ecuador-cantons",

  answerProperty: "canton_id",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "province",
        label: "Province",
        valueType: "string",
      },
    ],
  },

  baseMapLayers: {
    subdivisionLabels: false,
  },

  questions: ECUADOR_CANTON_QUESTIONS,
};
`;
}

/* -------------------------------------------------------------------------- */
/* Parish quiz generation                                                     */
/* -------------------------------------------------------------------------- */

/**
 * Generates the complete Ecuador Parishes quiz module.
 */
function createParishesQuizSource(
  entries: ParishQuizEntry[],
): string {
  const sortedEntries = [...entries].sort(
    (left, right) =>
      left.display.localeCompare(right.display, "es") ||
      left.answer.localeCompare(right.answer, "en"),
  );

  const questions = sortedEntries
    .map((entry) => createQuestionSource(entry.answer, entry.display))
    .join("\n");

  return `/**
 * AUTO-GENERATED FILE.
 *
 * Generated by:
 *
 *   scripts/countries/ecuador/generate/generate-admin-quizzes.ts
 *
 * Do not edit the question list manually. Update Ecuador's processed
 * administrative GeoJSON or the generator and regenerate this file instead.
 */

import type { FeatureQuiz } from "@/types/quiz";

/**
 * Ecuador's parish quiz questions.
 */
const ECUADOR_PARISH_QUESTIONS: FeatureQuiz["questions"] = [
${questions}
];

/**
 * Description shown for Ecuador's Parishes quiz.
 */
const ECUADOR_PARISHES_DESCRIPTION =
  \`Learn all \${ECUADOR_PARISH_QUESTIONS.length} parishes of Ecuador and \` +
  \`where they are located across the country. Use the Province or Canton \` +
  \`groupings to break the full quiz into smaller areas.\`;

/**
 * Quiz configuration for Ecuador's parishes.
 */
export const ecuadorParishesQuiz: FeatureQuiz = {
  id: "ecuador-parishes",
  name: "Parishes",
  description: ECUADOR_PARISHES_DESCRIPTION,

  kind: "feature",
  mapId: "ecuador-parishes",

  answerProperty: "parish_id",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "province",
        label: "Province",
        valueType: "string",
      },
      {
        property: "canton",
        label: "Canton",
        valueType: "string",
      },
    ],
  },

  baseMapLayers: {
    subdivisionLabels: false,
  },

  questions: ECUADOR_PARISH_QUESTIONS,
};
`;
}

/* -------------------------------------------------------------------------- */
/* Diagnostics                                                                */
/* -------------------------------------------------------------------------- */

/**
 * Prints useful information about one generated quiz.
 */
function printDiagnostics(
  label: string,
  count: number,
  groupingValues: readonly string[],
): void {
  console.log();
  console.log(label);
  console.log("-".repeat(label.length));
  console.log(`Questions: ${count.toLocaleString()}`);
  console.log(
    `Grouping values: ${new Set(groupingValues).size.toLocaleString()}`,
  );
}

/* -------------------------------------------------------------------------- */
/* Main                                                                       */
/* -------------------------------------------------------------------------- */

/**
 * Generates Ecuador's Canton and Parish quiz modules.
 */
function main(): void {
  console.log("Generating Ecuador administrative quizzes...");

  const cantons = loadCantons();
  const parishes = loadParishes();

  const cantonQuizSource = createCantonsQuizSource(cantons);

  const parishQuizSource = createParishesQuizSource(parishes);

  writeGeneratedFile(CANTONS_OUTPUT_PATH, cantonQuizSource);

  writeGeneratedFile(PARISHES_OUTPUT_PATH, parishQuizSource);

  printDiagnostics(
    "Cantons",
    cantons.length,
    cantons.map((entry) => entry.province),
  );

  console.log(`Output: ${CANTONS_OUTPUT_PATH}`);

  printDiagnostics(
    "Parishes",
    parishes.length,
    parishes.map((entry) => entry.canton),
  );

  console.log(
    `Provinces represented: ${
      new Set(parishes.map((entry) => entry.province)).size
    }`,
  );

  console.log(`Output: ${PARISHES_OUTPUT_PATH}`);

  console.log();
  console.log("Finished Ecuador administrative quiz generation.");
}

main();
