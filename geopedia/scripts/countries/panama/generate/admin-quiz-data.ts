/**
 * Generates the administrative quiz data used by GeoPedia's Panama
 * province/comarca, district, and corregimiento quizzes.
 *
 * Inputs:
 *   public/data/countries/panama/geojson/districts.geojson
 *   public/data/countries/panama/geojson/corregimientos.geojson
 *
 * Output:
 *   src/quiz/quizzes/countries/central-america/panama/data/admin.ts
 *
 * Province/comarca names are maintained by this generator and validated
 * against the processed administrative GeoJSON.
 *
 * Districts and corregimientos are generated from the processed GeoJSON.
 * Repeated corregimiento names are disambiguated by district. If the same
 * name occurs more than once within the same district, its stable
 * administrative ID is also included in the display name.
 */

import fs from "node:fs";
import path from "node:path";

const DISTRICTS_PATH =
  "public/data/countries/panama/geojson/districts.geojson";

const CORREGIMIENTOS_PATH =
  "public/data/countries/panama/geojson/corregimientos.geojson";

const OUTPUT_PATH =
  "src/quiz/quizzes/countries/central-america/panama/data/admin.ts";

const EXPECTED_PROVINCE_COMARCA_COUNT = 14;
const EXPECTED_DISTRICT_COUNT = 81;
const EXPECTED_CORREGIMIENTO_COUNT = 698;

const PROVINCES_COMARCAS_BY_ID = {
  "01": "Bocas del Toro",
  "02": "Coclé",
  "03": "Colón",
  "04": "Chiriquí",
  "05": "Darién",
  "06": "Herrera",
  "07": "Los Santos",
  "08": "Panamá",
  "09": "Veraguas",
  "10": "Kuna Yala",
  "11": "Emberá Wounaán",
  "12": "Ngäbe Buglé",
  "13": "Panamá Oeste",
  "14": "Naso Tjër Di",
} as const;

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
  districtId: string;
  provinceId: string;
};

function readJson<T>(filePath: string): T {
  return JSON.parse(fs.readFileSync(filePath, "utf8")) as T;
}

function quote(value: string): string {
  return JSON.stringify(value);
}

function compareIds(left: string, right: string): number {
  return left.localeCompare(right, "en", {
    numeric: true,
  });
}

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

function validateProvinceComarca(
  provinceId: string,
  sourceName: string,
): void {
  if (!(provinceId in PROVINCES_COMARCAS_BY_ID)) {
    throw new Error(
      `${sourceName} references unknown province/comarca ID ` +
        `${quote(provinceId)}.`,
    );
  }
}

function createDistrictEntries(
  collection: GeoJsonFeatureCollection<DistrictProperties>,
): DistrictEntry[] {
  const entries = collection.features
    .filter((feature) => feature.properties.quizEligible === true)
    .map((feature) => {
      const { id, name, provinceId, provinceName } =
        feature.properties;

      if (
        typeof id !== "string" ||
        typeof name !== "string" ||
        typeof provinceId !== "string" ||
        typeof provinceName !== "string"
      ) {
        throw new Error(
          "District GeoJSON contains a feature with invalid quiz properties.",
        );
      }

      validateProvinceComarca(provinceId, provinceName);

      return {
        id,
        name,
        provinceId,
      };
    })
    .sort((left, right) => compareIds(left.id, right.id));

  if (entries.length !== EXPECTED_DISTRICT_COUNT) {
    throw new Error(
      `Expected ${EXPECTED_DISTRICT_COUNT} quiz-eligible districts, ` +
        `found ${entries.length}.`,
    );
  }

  const uniqueIds = new Set(entries.map((entry) => entry.id));

  if (uniqueIds.size !== entries.length) {
    throw new Error("District entries contain duplicate IDs.");
  }

  return entries;
}

function createCorregimientoEntries(
  collection: GeoJsonFeatureCollection<CorregimientoProperties>,
): CorregimientoEntry[] {
  const rawEntries = collection.features.map((feature) => {
    const {
      id,
      name,
      districtId,
      districtName,
      provinceId,
      provinceName,
    } = feature.properties;

    if (
      typeof id !== "string" ||
      typeof name !== "string" ||
      typeof districtId !== "string" ||
      typeof districtName !== "string" ||
      typeof provinceId !== "string" ||
      typeof provinceName !== "string"
    ) {
      throw new Error(
        "Corregimiento GeoJSON contains a feature with invalid quiz properties.",
      );
    }

    validateProvinceComarca(provinceId, provinceName);

    return {
      id,
      name,
      districtId,
      districtName,
      provinceId,
    };
  });

  if (rawEntries.length !== EXPECTED_CORREGIMIENTO_COUNT) {
    throw new Error(
      `Expected ${EXPECTED_CORREGIMIENTO_COUNT} corregimientos, ` +
        `found ${rawEntries.length}.`,
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
        districtId: entry.districtId,
        provinceId: entry.provinceId,
      };
    }

    const nameDistrictKey = `${entry.name}\u0000${entry.districtId}`;

    const repeatedWithinDistrict =
      (nameDistrictCounts.get(nameDistrictKey) ?? 0) > 1;

    const name = repeatedWithinDistrict
      ? `${entry.name} (${entry.districtName}, ${entry.id})`
      : `${entry.name} (${entry.districtName})`;

    return {
      id: entry.id,
      name,
      districtId: entry.districtId,
      provinceId: entry.provinceId,
    };
  });

  entries.sort((left, right) => compareIds(left.id, right.id));

  const uniqueIds = new Set(entries.map((entry) => entry.id));

  if (uniqueIds.size !== entries.length) {
    throw new Error("Corregimiento entries contain duplicate IDs.");
  }

  const generatedNames = new Set<string>();

  for (const entry of entries) {
    if (generatedNames.has(entry.name)) {
      throw new Error(
        `Corregimiento display name is still duplicated: ${quote(entry.name)}.`,
      );
    }

    generatedNames.add(entry.name);
  }

  return entries;
}

function renderProvincesComarcas(): string {
  const lines = ["export const PANAMA_PROVINCES_COMARCAS_BY_ID = {"];

  for (const [id, name] of Object.entries(PROVINCES_COMARCAS_BY_ID)) {
    lines.push(`  ${quote(id)}: ${quote(name)},`);
  }

  lines.push("} as const;", "");

  return lines.join("\n");
}

function renderDistricts(entries: DistrictEntry[]): string {
  const lines = ["export const PANAMA_DISTRICTS_BY_ID = {"];

  for (const entry of entries) {
    lines.push(
      `  ${quote(entry.id)}: { ` +
        `name: ${quote(entry.name)}, ` +
        `provinceComarcaId: ${quote(entry.provinceId)} ` +
        "},",
    );
  }

  lines.push("} as const;", "");

  return lines.join("\n");
}

function renderCorregimientos(entries: CorregimientoEntry[]): string {
  const lines = ["export const PANAMA_CORREGIMIENTOS_BY_ID = {"];

  for (const entry of entries) {
    lines.push(
      `  ${quote(entry.id)}: { ` +
        `name: ${quote(entry.name)}, ` +
        `districtId: ${quote(entry.districtId)}, ` +
        `provinceComarcaId: ${quote(entry.provinceId)} ` +
        "},",
    );
  }

  lines.push("} as const;", "");

  return lines.join("\n");
}

function createSource(
  districts: DistrictEntry[],
  corregimientos: CorregimientoEntry[],
): string {
  return `/**
 * Generated administrative data for Panama.
 *
 * District and corregimiento data is generated from GeoPedia's processed
 * administrative GeoJSON. Province and comarca names are maintained by
 * this generator and validated against the processed GeoJSON.
 *
 * Do not edit manually.
 * Regenerate with:
 * npx tsx scripts/countries/panama/generate/admin-quiz-data.ts
 */

${renderProvincesComarcas()}${renderDistricts(districts)}${renderCorregimientos(corregimientos)}`;
}

function main(): void {
  console.log("Generating Panama administrative quiz data...");
  console.log("");

  if (
    Object.keys(PROVINCES_COMARCAS_BY_ID).length !==
    EXPECTED_PROVINCE_COMARCA_COUNT
  ) {
    throw new Error(
      `Expected ${EXPECTED_PROVINCE_COMARCA_COUNT} provinces/comarcas.`,
    );
  }

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

  fs.mkdirSync(path.dirname(OUTPUT_PATH), {
    recursive: true,
  });

  fs.writeFileSync(
    OUTPUT_PATH,
    createSource(districtEntries, corregimientoEntries),
    "utf8",
  );

  console.log(
    `Provinces / comarcas: ${Object.keys(PROVINCES_COMARCAS_BY_ID).length}`,
  );

  console.log(`Districts: ${districtEntries.length}`);

  console.log(`Corregimientos: ${corregimientoEntries.length}`);

  console.log("");
  console.log(`Generated: ${OUTPUT_PATH}`);
}

main();
