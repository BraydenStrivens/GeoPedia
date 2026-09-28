/**
 * Generates the administrative data used by Ecuador's quiz configurations.
 *
 * Sources:
 *   public/data/countries/ecuador/geojson/provinces.geojson
 *   public/data/countries/ecuador/geojson/cantons.geojson
 *   public/data/countries/ecuador/geojson/parishes.geojson
 *
 * Output:
 *   src/quiz/quizzes/countries/south-america/ecuador/data/admin.ts
 */

import fs from "node:fs";
import path from "node:path";

type ProvinceProperties = {
  province_id: string;
  province: string;
};

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

type Province = {
  id: string;
  name: string;
};

type Canton = {
  id: string;
  name: string;
  provinceId: string;
};

type Parish = {
  id: string;
  name: string;
  cantonId: string;
  provinceId: string;
};

const PROVINCES_GEOJSON_PATH = path.resolve(
  "public/data/countries/ecuador/geojson/provinces.geojson",
);

const CANTONS_GEOJSON_PATH = path.resolve(
  "public/data/countries/ecuador/geojson/cantons.geojson",
);

const PARISHES_GEOJSON_PATH = path.resolve(
  "public/data/countries/ecuador/geojson/parishes.geojson",
);

const OUTPUT_PATH = path.resolve(
  "src/quiz/quizzes/countries/south-america/ecuador/data/admin.ts",
);

const EXPECTED_PROVINCE_COUNT = 24;
const EXPECTED_CANTON_COUNT = 221;
const EXPECTED_PARISH_COUNT = 1_042;

function quote(value: string): string {
  return JSON.stringify(value);
}

function readJson<T>(filePath: string): T {
  if (!fs.existsSync(filePath)) {
    throw new Error(
      `Required source file was not found: ${filePath}`,
    );
  }

  return JSON.parse(fs.readFileSync(filePath, "utf8")) as T;
}

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

function loadProvinces(): Province[] {
  const featureCollection = readJson<
    GeoJsonFeatureCollection<ProvinceProperties>
  >(PROVINCES_GEOJSON_PATH);

  if (
    featureCollection.type !== "FeatureCollection" ||
    !Array.isArray(featureCollection.features)
  ) {
    throw new Error(
      "Ecuador province GeoJSON is not a valid FeatureCollection.",
    );
  }

  if (featureCollection.features.length !== EXPECTED_PROVINCE_COUNT) {
    throw new Error(
      `Expected ${EXPECTED_PROVINCE_COUNT} Ecuador provinces, got ` +
        `${featureCollection.features.length}.`,
    );
  }

  const provinces: Province[] = [];
  const seenIds = new Set<string>();

  featureCollection.features.forEach((feature, index) => {
    if (!feature.properties) {
      throw new Error(`Province feature ${index} has no properties.`);
    }

    const id = requireString(
      feature.properties.province_id,
      "province_id",
      index,
    );

    const name = requireString(
      feature.properties.province,
      "province",
      index,
    );

    if (seenIds.has(id)) {
      throw new Error(`Duplicate Ecuador province ID: ${id}`);
    }

    seenIds.add(id);

    if (feature.id !== undefined && String(feature.id) !== id) {
      throw new Error(
        `Province ${id} has GeoJSON feature ID ` +
          `${String(feature.id)}, which does not match province_id.`,
      );
    }

    provinces.push({
      id,
      name,
    });
  });

  return provinces;
}

function loadCantons(): Canton[] {
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

  const cantons: Canton[] = [];
  const seenIds = new Set<string>();

  featureCollection.features.forEach((feature, index) => {
    if (!feature.properties) {
      throw new Error(`Canton feature ${index} has no properties.`);
    }

    const id = requireString(
      feature.properties.canton_id,
      "canton_id",
      index,
    );

    const name = requireString(
      feature.properties.canton,
      "canton",
      index,
    );

    const provinceId = requireString(
      feature.properties.province_id,
      "province_id",
      index,
    );

    requireString(feature.properties.province, "province", index);

    if (seenIds.has(id)) {
      throw new Error(`Duplicate Ecuador canton ID: ${id}`);
    }

    seenIds.add(id);

    if (feature.id !== undefined && String(feature.id) !== id) {
      throw new Error(
        `Canton ${id} has GeoJSON feature ID ` +
          `${String(feature.id)}, which does not match canton_id.`,
      );
    }

    cantons.push({
      id,
      name,
      provinceId,
    });
  });

  return cantons;
}

function loadParishes(): Parish[] {
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

  const parishes: Parish[] = [];
  const seenIds = new Set<string>();

  featureCollection.features.forEach((feature, index) => {
    if (!feature.properties) {
      throw new Error(`Parish feature ${index} has no properties.`);
    }

    const id = requireString(
      feature.properties.parish_id,
      "parish_id",
      index,
    );

    const name = requireString(
      feature.properties.parish,
      "parish",
      index,
    );

    const cantonId = requireString(
      feature.properties.canton_id,
      "canton_id",
      index,
    );

    requireString(feature.properties.canton, "canton", index);

    const provinceId = requireString(
      feature.properties.province_id,
      "province_id",
      index,
    );

    requireString(feature.properties.province, "province", index);

    if (seenIds.has(id)) {
      throw new Error(`Duplicate Ecuador parish ID: ${id}`);
    }

    seenIds.add(id);

    if (feature.id !== undefined && String(feature.id) !== id) {
      throw new Error(
        `Parish ${id} has GeoJSON feature ID ` +
          `${String(feature.id)}, which does not match parish_id.`,
      );
    }

    parishes.push({
      id,
      name,
      cantonId,
      provinceId,
    });
  });

  return parishes;
}

function validateHierarchy(
  provinces: Province[],
  cantons: Canton[],
  parishes: Parish[],
): void {
  const provinceIds = new Set(
    provinces.map((province) => province.id),
  );

  const cantonIds = new Set(cantons.map((canton) => canton.id));

  for (const canton of cantons) {
    if (!provinceIds.has(canton.provinceId)) {
      throw new Error(
        `Canton ${canton.id} references unknown province ` +
          `${canton.provinceId}.`,
      );
    }
  }

  for (const parish of parishes) {
    if (!provinceIds.has(parish.provinceId)) {
      throw new Error(
        `Parish ${parish.id} references unknown province ` +
          `${parish.provinceId}.`,
      );
    }

    if (!cantonIds.has(parish.cantonId)) {
      throw new Error(
        `Parish ${parish.id} references unknown canton ` +
          `${parish.cantonId}.`,
      );
    }
  }
}

function formatProvinces(provinces: Province[]): string {
  const lines = [...provinces]
    .sort((a, b) => a.id.localeCompare(b.id))
    .map(
      (province) =>
        `  ${quote(province.id)}: ${quote(province.name)},`,
    );

  return [
    "export const ECUADOR_PROVINCES_BY_ID = {",
    ...lines,
    "} as const;",
  ].join("\n");
}

function formatCantons(cantons: Canton[]): string {
  const lines = [...cantons]
    .sort((a, b) => a.id.localeCompare(b.id))
    .map(
      (canton) =>
        `  ${quote(canton.id)}: { ` +
        `name: ${quote(canton.name)}, ` +
        `provinceId: ${quote(canton.provinceId)} ` +
        `},`,
    );

  return [
    "export const ECUADOR_CANTONS_BY_ID = {",
    ...lines,
    "} as const;",
  ].join("\n");
}

function formatParishes(parishes: Parish[]): string {
  const lines = [...parishes]
    .sort((a, b) => a.id.localeCompare(b.id))
    .map(
      (parish) =>
        `  ${quote(parish.id)}: { ` +
        `name: ${quote(parish.name)}, ` +
        `cantonId: ${quote(parish.cantonId)}, ` +
        `provinceId: ${quote(parish.provinceId)} ` +
        `},`,
    );

  return [
    "export const ECUADOR_PARISHES_BY_ID = {",
    ...lines,
    "} as const;",
  ].join("\n");
}

function buildOutput(
  provinces: Province[],
  cantons: Canton[],
  parishes: Parish[],
): string {
  return `/**
 * Generated from Ecuador's processed administrative GeoJSON.
 *
 * Do not edit manually.
 * Regenerate with:
 * npx tsx scripts/countries/ecuador/generate/admin-quiz-data.ts
 */

${formatProvinces(provinces)}

${formatCantons(cantons)}

${formatParishes(parishes)}
`;
}

function main(): void {
  console.log("Generating Ecuador administrative quiz data...\n");

  const provinces = loadProvinces();
  const cantons = loadCantons();
  const parishes = loadParishes();

  validateHierarchy(provinces, cantons, parishes);

  const output = buildOutput(provinces, cantons, parishes);

  fs.mkdirSync(path.dirname(OUTPUT_PATH), { recursive: true });

  fs.writeFileSync(OUTPUT_PATH, output, "utf8");

  console.log(`Provinces: ${provinces.length}`);
  console.log(`Cantons:   ${cantons.length}`);
  console.log(`Parishes:  ${parishes.length}`);
  console.log(`\nGenerated: ${OUTPUT_PATH}`);
}

main();
