/**
 * Generates Panama's district and corregimiento quiz configuration files from
 * GeoPedia's processed Panama administrative GeoJSON.
 *
 * Inputs:
 *
 *   public/data/countries/panama/geojson/districts.geojson
 *   public/data/countries/panama/geojson/corregimientos.geojson
 *
 * Outputs:
 *
 *   src/quiz/quizzes/panama/districtsQuiz.ts
 *   src/quiz/quizzes/panama/corregimientosQuiz.ts
 *
 * The Provinces & Comarcas quiz is maintained manually because it contains
 * only 14 questions. The larger district and corregimiento question sets are
 * generated so they stay synchronized with the processed geometry.
 */

import fs from "node:fs";
import path from "node:path";

const DISTRICTS_PATH =
  "public/data/countries/panama/geojson/districts.geojson";

const CORREGIMIENTOS_PATH =
  "public/data/countries/panama/geojson/corregimientos.geojson";

const DISTRICTS_OUTPUT_PATH =
  "src/quiz/quizzes/panama/districtsQuiz.ts";

const CORREGIMIENTOS_OUTPUT_PATH =
  "src/quiz/quizzes/panama/corregimientosQuiz.ts";

type GeoJsonFeature<Properties extends Record<string, unknown>> = {
  type: "Feature";
  properties: Properties;
};

type GeoJsonFeatureCollection<
  Properties extends Record<string, unknown>,
> = {
  type: "FeatureCollection";
  features: GeoJsonFeature<Properties>[];
};

type DistrictProperties = {
  id: string;
  name: string;
  provinceId: string;
  provinceName: string;
  quizEligible: boolean;
};

type CorregimientoProperties = {
  id: string;
  name: string;
  districtId: string;
  districtName: string;
  provinceId: string;
  provinceName: string;
};

type DistrictEntry = {
  id: string;
  name: string;
  provinceId: string;
};

type CorregimientoEntry = {
  id: string;
  name: string;
  display: string;
  districtId: string;
  provinceId: string;
};

/**
 * Reads and parses a JSON file.
 */
function readJson<T>(filePath: string): T {
  return JSON.parse(fs.readFileSync(filePath, "utf8")) as T;
}

/**
 * Escapes a string as a TypeScript string literal.
 */
function quote(value: string): string {
  return JSON.stringify(value);
}

/**
 * Compares administrative IDs numerically while retaining their original
 * zero-padded string representation.
 */
function compareIds(left: string, right: string): number {
  return left.localeCompare(right, "en", {
    numeric: true,
  });
}

/**
 * Validates common GeoJSON FeatureCollection structure.
 */
function validateFeatureCollection(
  value: unknown,
  sourceName: string,
): asserts value is GeoJsonFeatureCollection<
  Record<string, unknown>
> {
  if (
    typeof value !== "object" ||
    value === null ||
    !("type" in value) ||
    value.type !== "FeatureCollection" ||
    !("features" in value) ||
    !Array.isArray(value.features)
  ) {
    throw new Error(
      `${sourceName} is not a valid GeoJSON FeatureCollection.`,
    );
  }
}

/**
 * Creates the quiz-eligible district entries from processed ADM2 GeoJSON.
 */
function createDistrictEntries(
  collection: GeoJsonFeatureCollection<DistrictProperties>,
): DistrictEntry[] {
  const entries = collection.features
    .filter((feature) => feature.properties.quizEligible === true)
    .map((feature) => {
      const { id, name, provinceId } = feature.properties;

      if (
        typeof id !== "string" ||
        typeof name !== "string" ||
        typeof provinceId !== "string"
      ) {
        throw new Error(
          "District GeoJSON contains a feature with invalid quiz properties.",
        );
      }

      return {
        id,
        name,
        provinceId,
      };
    })
    .sort((left, right) => compareIds(left.id, right.id));

  if (entries.length !== 81) {
    throw new Error(
      `Expected 81 quiz-eligible districts, found ${entries.length}.`,
    );
  }

  const uniqueIds = new Set(entries.map((entry) => entry.id));

  if (uniqueIds.size !== entries.length) {
    throw new Error("District quiz entries contain duplicate IDs.");
  }

  return entries;
}

/**
 * Creates display labels for repeated corregimiento names.
 *
 * A unique name is displayed normally:
 *
 *   Alanje
 *
 * A name repeated elsewhere is qualified by district:
 *
 *   Pedregal (David)
 *
 * If the same name occurs more than once inside the same district, the stable
 * source ID is also included because district qualification alone cannot
 * distinguish the questions:
 *
 *   Santa Fe (Santa Fe, 050300)
 *   Santa Fe (Santa Fe, 050316)
 */
function createCorregimientoEntries(
  collection: GeoJsonFeatureCollection<CorregimientoProperties>,
): CorregimientoEntry[] {
  const rawEntries = collection.features.map((feature) => {
    const { id, name, districtId, districtName, provinceId } =
      feature.properties;

    if (
      typeof id !== "string" ||
      typeof name !== "string" ||
      typeof districtId !== "string" ||
      typeof districtName !== "string" ||
      typeof provinceId !== "string"
    ) {
      throw new Error(
        "Corregimiento GeoJSON contains a feature with invalid quiz properties.",
      );
    }

    return {
      id,
      name,
      districtId,
      districtName,
      provinceId,
    };
  });

  if (rawEntries.length !== 698) {
    throw new Error(
      `Expected 698 corregimientos, found ${rawEntries.length}.`,
    );
  }

  const nameCounts = new Map<string, number>();

  for (const entry of rawEntries) {
    nameCounts.set(entry.name, (nameCounts.get(entry.name) ?? 0) + 1);
  }

  const nameDistrictCounts = new Map<string, number>();

  for (const entry of rawEntries) {
    const key = `${entry.name}\u0000${entry.districtId}`;

    nameDistrictCounts.set(
      key,
      (nameDistrictCounts.get(key) ?? 0) + 1,
    );
  }

  const entries: CorregimientoEntry[] = rawEntries.map((entry) => {
    const repeatedName = (nameCounts.get(entry.name) ?? 0) > 1;

    if (!repeatedName) {
      return {
        id: entry.id,
        name: entry.name,
        display: entry.name,
        districtId: entry.districtId,
        provinceId: entry.provinceId,
      };
    }

    const nameDistrictKey = `${entry.name}\u0000${entry.districtId}`;

    const repeatedWithinDistrict =
      (nameDistrictCounts.get(nameDistrictKey) ?? 0) > 1;

    const display = repeatedWithinDistrict
      ? `${entry.name} (${entry.districtName}, ${entry.id})`
      : `${entry.name} (${entry.districtName})`;

    return {
      id: entry.id,
      name: entry.name,
      display,
      districtId: entry.districtId,
      provinceId: entry.provinceId,
    };
  });

  entries.sort((left, right) => compareIds(left.id, right.id));

  const uniqueIds = new Set(entries.map((entry) => entry.id));

  if (uniqueIds.size !== entries.length) {
    throw new Error(
      "Corregimiento quiz entries contain duplicate IDs.",
    );
  }

  return entries;
}

/**
 * Creates a TypeScript ID-to-name dictionary.
 */
function createNameDictionarySource(
  entries: {
    id: string;
    name: string;
  }[],
): string {
  return entries
    .map((entry) => `  ${quote(entry.id)}: ${quote(entry.name)},`)
    .join("\n");
}

/**
 * Creates TypeScript question entries from generated corregimiento data.
 */
function createCorregimientoQuestionSource(
  entries: CorregimientoEntry[],
): string {
  return entries
    .map((entry) => {
      if (entry.display === entry.name) {
        return [
          "  {",
          `    answer: ${quote(entry.id)},`,
          `    display: ${quote(entry.name)},`,
          "  },",
        ].join("\n");
      }

      return [
        "  {",
        `    answer: ${quote(entry.id)},`,
        `    display: ${quote(entry.display)},`,
        "  },",
      ].join("\n");
    })
    .join("\n");
}

/**
 * Creates the generated Panama districts quiz module.
 */
function createDistrictQuizSource(entries: DistrictEntry[]): string {
  const dictionary = createNameDictionarySource(entries);

  return `/**
 * AUTO-GENERATED FILE.
 *
 * Generated by:
 *
 *   scripts/countries/panama/generate/admin-quizzes.ts
 *
 * Do not edit the district dictionary manually. Update the processed Panama
 * district GeoJSON or generator and rerun the script instead.
 */

import type { FeatureQuiz } from "@/types/quiz";

import {
  PANAMA_PROVINCE_COMARCA_NAMES_BY_ID,
} from "./provincesComarcasQuiz";

/**
 * Panama's quiz-eligible districts by stable administrative ID.
 *
 * Kuna Yala's non-administrative \`1000 / No asignado\` hierarchy placeholder
 * is intentionally excluded.
 */
export const PANAMA_DISTRICT_NAMES_BY_ID = {
${dictionary}
} as const;

/**
 * Questions for Panama's Districts quiz.
 */
const PANAMA_DISTRICT_QUESTIONS = Object.entries(
  PANAMA_DISTRICT_NAMES_BY_ID,
).map(([answer, display]) => ({
  answer,
  display,
}));

/**
 * Quiz configuration for Panama's districts.
 */
export const panamaDistrictsQuiz: FeatureQuiz = {
  id: "panama-districts",
  name: "Districts",
  description: \`Learn all \${PANAMA_DISTRICT_QUESTIONS.length} districts of Panama, with filters that let you practice districts by province or comarca.\`,

  kind: "feature",
  mapId: "panama-districts",

  answerProperty: "id",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
  },

  grouping: {
    properties: [
      {
        property: "provinceId",
        label: "Province / Comarca",
        valueType: "string",
        valueLabels: PANAMA_PROVINCE_COMARCA_NAMES_BY_ID,
      },
    ],
  },

  questions: PANAMA_DISTRICT_QUESTIONS,
};
`;
}

/**
 * Creates the generated Panama corregimientos quiz module.
 */
function createCorregimientosQuizSource(
  entries: CorregimientoEntry[],
): string {
  const questions = createCorregimientoQuestionSource(entries);

  return `/**
 * AUTO-GENERATED FILE.
 *
 * Generated by:
 *
 *   scripts/countries/panama/generate/admin-quizzes.ts
 *
 * Do not edit the question list manually. Update the processed Panama
 * corregimiento GeoJSON or generator and rerun the script instead.
 */

import type { FeatureQuiz } from "@/types/quiz";

import {
  PANAMA_DISTRICT_NAMES_BY_ID,
} from "./districtsQuiz";

import {
  PANAMA_PROVINCE_COMARCA_NAMES_BY_ID,
} from "./provincesComarcasQuiz";

/**
 * Questions for Panama's Corregimientos quiz.
 *
 * Repeated corregimiento names are qualified by district. If the same name
 * occurs more than once within the same district, its stable administrative
 * ID is also included in the display label.
 */
const PANAMA_CORREGIMIENTO_QUESTIONS = [
${questions}
];

/**
 * Quiz configuration for Panama's corregimientos.
 */
export const panamaCorregimientosQuiz: FeatureQuiz = {
  id: "panama-corregimientos",
  name: "Corregimientos",
  description: \`Learn all \${PANAMA_CORREGIMIENTO_QUESTIONS.length} corregimientos of Panama, with filters that let you practice corregimientos by district, province, or comarca.\`,

  kind: "feature",
  mapId: "panama-corregimientos",

  answerProperty: "id",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
  },

  grouping: {
    properties: [
      {
        property: "districtId",
        label: "District",
        valueType: "string",
        valueLabels: PANAMA_DISTRICT_NAMES_BY_ID,
      },
      {
        property: "provinceId",
        label: "Province / Comarca",
        valueType: "string",
        valueLabels: PANAMA_PROVINCE_COMARCA_NAMES_BY_ID,
      },
    ],
  },

  questions: PANAMA_CORREGIMIENTO_QUESTIONS,
};
`;
}

/**
 * Generates both Panama administrative quiz modules.
 */
function main(): void {
  console.log("Generating Panama administrative quizzes...");
  console.log("");

  const districts =
    readJson<GeoJsonFeatureCollection<DistrictProperties>>(
      DISTRICTS_PATH,
    );

  const corregimientos = readJson<
    GeoJsonFeatureCollection<CorregimientoProperties>
  >(CORREGIMIENTOS_PATH);

  validateFeatureCollection(districts, DISTRICTS_PATH);

  validateFeatureCollection(corregimientos, CORREGIMIENTOS_PATH);

  const districtEntries = createDistrictEntries(districts);

  const corregimientoEntries =
    createCorregimientoEntries(corregimientos);

  const districtSource = createDistrictQuizSource(districtEntries);

  const corregimientoSource = createCorregimientosQuizSource(
    corregimientoEntries,
  );

  fs.mkdirSync(path.dirname(DISTRICTS_OUTPUT_PATH), {
    recursive: true,
  });

  fs.writeFileSync(DISTRICTS_OUTPUT_PATH, districtSource, "utf8");

  fs.writeFileSync(
    CORREGIMIENTOS_OUTPUT_PATH,
    corregimientoSource,
    "utf8",
  );

  const repeatedNameCount = new Set(
    corregimientoEntries
      .filter((entry) => entry.display !== entry.name)
      .map((entry) => entry.name),
  ).size;

  console.log(`District questions: ${districtEntries.length}`);

  console.log(
    `Corregimiento questions: ${corregimientoEntries.length}`,
  );

  console.log(
    `Repeated corregimiento names disambiguated: ${repeatedNameCount}`,
  );

  console.log("");
  console.log(`District output: ${DISTRICTS_OUTPUT_PATH}`);

  console.log(`Corregimiento output: ${CORREGIMIENTOS_OUTPUT_PATH}`);

  console.log("");
  console.log("Done.");
}

main();
