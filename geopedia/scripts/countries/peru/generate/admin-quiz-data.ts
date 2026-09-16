/**
 * Generates the administrative data used by Peru's quiz configurations.
 *
 * Inputs:
 *   data/intermediate/countries/peru/admin/departments.geojson
 *   data/intermediate/countries/peru/admin/provinces.geojson
 *   data/intermediate/countries/peru/admin/districts.geojson
 *
 * Output:
 *   src/quiz/quizzes/countries/south-america/peru/data/admin.ts
 */

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

const OUTPUT_PATH = path.join(
  ROOT,
  "src",
  "quiz",
  "quizzes",
  "countries",
  "south-america",
  "peru",
  "data",
  "admin.ts",
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
// TypeScript formatting
// ---------------------------------------------------------------------------

function formatRegions(regions: Region[]): string {
  const lines = regions.map(
    (region) =>
      `  ${JSON.stringify(region.id)}: ` +
      `${JSON.stringify(region.name)},`,
  );

  return [
    "export const PERU_REGIONS_BY_ID = {",
    ...lines,
    "} as const;",
  ].join("\n");
}

function formatProvinces(provinces: Province[]): string {
  const lines = provinces.map(
    (province) =>
      `  ${JSON.stringify(province.id)}: { ` +
      `name: ${JSON.stringify(province.name)}, ` +
      `regionId: ${JSON.stringify(province.regionId)} ` +
      `},`,
  );

  return [
    "export const PERU_PROVINCES_BY_ID = {",
    ...lines,
    "} as const;",
  ].join("\n");
}

function formatDistricts(districts: District[]): string {
  const lines = districts.map(
    (district) =>
      `  ${JSON.stringify(district.id)}: { ` +
      `name: ${JSON.stringify(district.name)}, ` +
      `provinceId: ${JSON.stringify(district.provinceId)}, ` +
      `regionId: ${JSON.stringify(district.regionId)} ` +
      `},`,
  );

  return [
    "export const PERU_DISTRICTS_BY_ID = {",
    ...lines,
    "} as const;",
  ].join("\n");
}

// ---------------------------------------------------------------------------
// Output
// ---------------------------------------------------------------------------

function buildOutput(
  regions: Region[],
  provinces: Province[],
  districts: District[],
): string {
  return `/**
 * Generated from Peru's processed administrative GeoJSON.
 *
 * Do not edit manually.
 * Regenerate with:
 * npx tsx scripts/countries/peru/generate/admin-quiz-data.ts
 */

${formatRegions(regions)}

${formatProvinces(provinces)}

${formatDistricts(districts)}
`;
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

function main(): void {
  console.log("Generating Peru administrative quiz data...\n");

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

  const output = buildOutput(regions, provinces, districts);

  fs.mkdirSync(path.dirname(OUTPUT_PATH), {
    recursive: true,
  });

  fs.writeFileSync(OUTPUT_PATH, output, "utf8");

  console.log(`Regions:   ${regions.length}`);
  console.log(`Provinces: ${provinces.length}`);
  console.log(`Districts: ${districts.length}`);

  console.log(`\nGenerated: ${OUTPUT_PATH}`);
}

main();
