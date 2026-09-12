import fs from "node:fs";
import path from "node:path";

type GeoJsonFeature = {
  properties: Record<string, unknown>;
};

type GeoJsonFeatureCollection = {
  type: "FeatureCollection";
  features: GeoJsonFeature[];
};

type Region = {
  id: string;
  name: string;
};

type Province = {
  id: string;
  name: string;
  regionId: string;
};

type District = {
  id: string;
  name: string;
  provinceId: string;
  regionId: string;
};

const ROOT = process.cwd();

const INTERMEDIATE_DIRECTORY = path.join(
  ROOT,
  "data",
  "intermediate",
  "countries",
  "peru",
  "admin",
);

const OUTPUT_DIRECTORY = path.join(
  ROOT,
  "src",
  "quiz",
  "quizzes",
  "countries",
  "peru",
);

const REGIONS_INPUT = path.join(
  INTERMEDIATE_DIRECTORY,
  "regions.geojson",
);

const PROVINCES_INPUT = path.join(
  INTERMEDIATE_DIRECTORY,
  "provinces.geojson",
);

const DISTRICTS_INPUT = path.join(
  INTERMEDIATE_DIRECTORY,
  "districts.geojson",
);

// ---------------------------------------------------------------------------
// GeoJSON loading
// ---------------------------------------------------------------------------

function readGeoJson(filePath: string): GeoJsonFeatureCollection {
  const raw = fs.readFileSync(filePath, "utf8");

  const data = JSON.parse(raw) as GeoJsonFeatureCollection;

  if (
    data.type !== "FeatureCollection" ||
    !Array.isArray(data.features)
  ) {
    throw new Error(
      `${filePath} is not a valid GeoJSON FeatureCollection.`,
    );
  }

  return data;
}

function requireString(
  properties: Record<string, unknown>,
  key: string,
): string {
  const value = properties[key];

  if (typeof value !== "string" || value.trim() === "") {
    throw new Error(`Missing or invalid string property "${key}".`);
  }

  return value.trim();
}

// ---------------------------------------------------------------------------
// Data loading
// ---------------------------------------------------------------------------

function loadRegions(): Region[] {
  const data = readGeoJson(REGIONS_INPUT);

  return data.features.map((feature) => {
    const properties = feature.properties;

    return {
      id: requireString(properties, "region_id"),
      name: requireString(properties, "region"),
    };
  });
}

function loadProvinces(): Province[] {
  const data = readGeoJson(PROVINCES_INPUT);

  return data.features.map((feature) => {
    const properties = feature.properties;

    return {
      id: requireString(properties, "province_id"),
      name: requireString(properties, "province"),
      regionId: requireString(properties, "region_id"),
    };
  });
}

function loadDistricts(): District[] {
  const data = readGeoJson(DISTRICTS_INPUT);

  return data.features.map((feature) => {
    const properties = feature.properties;

    return {
      id: requireString(properties, "district_id"),
      name: requireString(properties, "district"),
      provinceId: requireString(properties, "province_id"),
      regionId: requireString(properties, "region_id"),
    };
  });
}

// ---------------------------------------------------------------------------
// Validation
// ---------------------------------------------------------------------------

function sortById<T extends { id: string }>(values: T[]): T[] {
  return [...values].sort((a, b) => a.id.localeCompare(b.id));
}

function validateUniqueIds<T extends { id: string }>(
  label: string,
  values: T[],
): void {
  const ids = new Set<string>();

  for (const value of values) {
    if (ids.has(value.id)) {
      throw new Error(`Duplicate ${label} ID: ${value.id}`);
    }

    ids.add(value.id);
  }
}

function validateHierarchy(
  regions: Region[],
  provinces: Province[],
  districts: District[],
): void {
  const regionIds = new Set(regions.map((region) => region.id));

  const provinceIds = new Set(
    provinces.map((province) => province.id),
  );

  for (const province of provinces) {
    if (!regionIds.has(province.regionId)) {
      throw new Error(
        `Province ${province.id} references unknown region ` +
          `${province.regionId}.`,
      );
    }
  }

  for (const district of districts) {
    if (!regionIds.has(district.regionId)) {
      throw new Error(
        `District ${district.id} references unknown region ` +
          `${district.regionId}.`,
      );
    }

    if (!provinceIds.has(district.provinceId)) {
      throw new Error(
        `District ${district.id} references unknown province ` +
          `${district.provinceId}.`,
      );
    }
  }
}

// ---------------------------------------------------------------------------
// Source formatting
// ---------------------------------------------------------------------------

function formatStringDictionary(
  entries: Array<{
    id: string;
    value: string;
  }>,
): string {
  const lines = entries.map(
    ({ id, value }) =>
      `  ${JSON.stringify(id)}: ${JSON.stringify(value)},`,
  );

  return ["{", ...lines, "} as const"].join("\n");
}

function formatProvinceDictionary(provinces: Province[]): string {
  const lines = provinces.map(
    (province) =>
      `  ${JSON.stringify(province.id)}: { ` +
      `name: ${JSON.stringify(province.name)}, ` +
      `regionId: ${JSON.stringify(province.regionId)} },`,
  );

  return ["{", ...lines, "} as const"].join("\n");
}

function formatDistrictDictionary(districts: District[]): string {
  const lines = districts.map(
    (district) =>
      `  ${JSON.stringify(district.id)}: { ` +
      `name: ${JSON.stringify(district.name)}, ` +
      `provinceId: ${JSON.stringify(district.provinceId)}, ` +
      `regionId: ${JSON.stringify(district.regionId)} },`,
  );

  return ["{", ...lines, "} as const"].join("\n");
}

function writeFile(filename: string, contents: string): void {
  fs.mkdirSync(OUTPUT_DIRECTORY, {
    recursive: true,
  });

  const outputPath = path.join(OUTPUT_DIRECTORY, filename);

  fs.writeFileSync(outputPath, contents, "utf8");

  console.log(`Wrote ${outputPath}`);
}

// ---------------------------------------------------------------------------
// Regions quiz
// ---------------------------------------------------------------------------

function generateRegionsQuiz(regions: Region[]): void {
  const regionsById = formatStringDictionary(
    regions.map((region) => ({
      id: region.id,
      value: region.name,
    })),
  );

  const source = `import type { FeatureQuiz } from "@/types/quiz";


export const PERU_REGIONS_BY_ID = ${regionsById};

export const PERU_REGION_VALUE_LABELS = PERU_REGIONS_BY_ID;

const PERU_REGION_QUESTIONS = Object.entries(
  PERU_REGIONS_BY_ID,
).map(([regionId, region]) => ({
  answer: regionId,
  display: region,
}));

const PERU_REGIONS_DESCRIPTION =
  \`Learn all \${PERU_REGION_QUESTIONS.length} first-level administrative \` +
  \`regions of Peru, including the Constitutional Province of Callao.\`;


export const peruRegionsQuiz: FeatureQuiz = {
  id: "peru-regions",
  name: "Regions",
  description: PERU_REGIONS_DESCRIPTION,
  kind: "feature",
  mapId: "peru-regions",
  answerProperty: "region_id",
  answerType: "single",
  baseMapLayers: {
    subdivisionLabels: false,
  },
  questions: PERU_REGION_QUESTIONS,
};
`;

  writeFile("regionsQuiz.ts", source);
}

// ---------------------------------------------------------------------------
// Provinces quiz
// ---------------------------------------------------------------------------

function generateProvincesQuiz(provinces: Province[]): void {
  const provincesById = formatProvinceDictionary(provinces);

  const source = `import type { FeatureQuiz } from "@/types/quiz";

import {
  PERU_REGION_VALUE_LABELS,
} from "./regionsQuiz";


export const PERU_PROVINCES_BY_ID = ${provincesById};

export const PERU_PROVINCE_VALUE_LABELS = Object.fromEntries(
  Object.entries(
    PERU_PROVINCES_BY_ID,
  ).map(([provinceId, province]) => [
    provinceId,
    province.name,
  ]),
);

const PERU_PROVINCE_QUESTIONS = Object.entries(
  PERU_PROVINCES_BY_ID,
).map(([provinceId, province]) => ({
  answer: provinceId,
  display: province.name,
}));

const PERU_PROVINCES_DESCRIPTION =
  \`Learn all \${PERU_PROVINCE_QUESTIONS.length} provinces of Peru. \` +
  \`Use region groups to study the provinces in smaller geographic sets.\`;


export const peruProvincesQuiz: FeatureQuiz = {
  id: "peru-provinces",
  name: "Provinces",
  description: PERU_PROVINCES_DESCRIPTION,
  kind: "feature",
  mapId: "peru-provinces",
  answerProperty: "province_id",
  answerType: "single",
  grouping: {
    properties: [
      {
        property: "region_id",
        label: "Region",
        valueType: "string",
        valueLabels: PERU_REGION_VALUE_LABELS,
      },
    ],
  },
  baseMapLayers: {
    subdivisionLabels: false,
  },
  questions: PERU_PROVINCE_QUESTIONS,
};
`;

  writeFile("provincesQuiz.ts", source);
}

// ---------------------------------------------------------------------------
// Districts quiz
// ---------------------------------------------------------------------------

function generateDistrictsQuiz(districts: District[]): void {
  const districtsById = formatDistrictDictionary(districts);

  const source = `import type { FeatureQuiz } from "@/types/quiz";

import {
  PERU_REGION_VALUE_LABELS,
} from "./regionsQuiz";

import {
  PERU_PROVINCE_VALUE_LABELS,
} from "./provincesQuiz";


export const PERU_DISTRICTS_BY_ID = ${districtsById};

const PERU_DISTRICT_QUESTIONS = Object.entries(
  PERU_DISTRICTS_BY_ID,
).map(([districtId, district]) => ({
  answer: districtId,
  display: district.name,
}));

const PERU_DISTRICTS_DESCRIPTION =
  \`Learn all \${PERU_DISTRICT_QUESTIONS.length} districts of Peru. \` +
  \`Use region and province groups to break the country into smaller study sets.\`;


export const peruDistrictsQuiz: FeatureQuiz = {
  id: "peru-districts",
  name: "Districts",
  description: PERU_DISTRICTS_DESCRIPTION,
  kind: "feature",
  mapId: "peru-districts",
  answerProperty: "district_id",
  answerType: "single",
  grouping: {
    properties: [
      {
        property: "region_id",
        label: "Region",
        valueType: "string",
        valueLabels: PERU_REGION_VALUE_LABELS,
      },
      {
        property: "province_id",
        label: "Province",
        valueType: "string",
        valueLabels: PERU_PROVINCE_VALUE_LABELS,
      },
    ],
  },
  baseMapLayers: {
    subdivisionLabels: false,
  },
  questions: PERU_DISTRICT_QUESTIONS,
};
`;

  writeFile("districtsQuiz.ts", source);
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

function main(): void {
  console.log("Generating Peru administrative quizzes...\n");

  const regions = sortById(loadRegions());

  const provinces = sortById(loadProvinces());

  const districts = sortById(loadDistricts());

  validateUniqueIds("region", regions);

  validateUniqueIds("province", provinces);

  validateUniqueIds("district", districts);

  validateHierarchy(regions, provinces, districts);

  if (regions.length !== 25) {
    throw new Error(
      `Expected 25 regions but found ${regions.length}.`,
    );
  }

  if (provinces.length !== 196) {
    throw new Error(
      `Expected 196 provinces but found ${provinces.length}.`,
    );
  }

  if (districts.length !== 1873) {
    throw new Error(
      `Expected 1,873 districts but found ${districts.length}.`,
    );
  }

  generateRegionsQuiz(regions);

  generateProvincesQuiz(provinces);

  generateDistrictsQuiz(districts);

  console.log("");
  console.log(`Regions:   ${regions.length}`);
  console.log(`Provinces: ${provinces.length}`);
  console.log(`Districts: ${districts.length}`);

  console.log("\nPeru administrative quiz generation complete.");
}

main();
