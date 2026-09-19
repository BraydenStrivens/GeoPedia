/**
 * Generates GeoPedia's shared country-name metadata.
 *
 * GeoPedia's processed world-country GeoJSON is authoritative for the 250
 * countries represented by the application. MapTiler place metadata supplies
 * locally used country names.
 *
 * The normal MapTiler inspection contains 240 countries represented as
 * `class="country"`. A small set of GeoPedia countries are represented by
 * MapTiler as states/islands instead and are resolved explicitly below.
 *
 * Multilingual local names are normalized to use " / " between distinct
 * locally used names.
 *
 * Native names that are meaningfully equivalent to GeoPedia's English name
 * are omitted.
 *
 * Generated output:
 * src/data/countries/countryNames.ts
 *
 * Do not edit the generated file manually.
 *
 * Before running this generator, refresh the MapTiler inspection data with:
 * npx tsx scripts/global/countries/inspect/maptiler-country-names.ts
 *
 * Run this generator with:
 * npx tsx scripts/global/countries/generate/country-names.ts
 */

import fs from "node:fs";
import path from "node:path";

import { areDisplayNamesEquivalent } from "../../../tools/nameComparison";

/* -------------------------------------------------------------------------- */
/*                                    Paths                                   */
/* -------------------------------------------------------------------------- */

/**
 * GeoPedia's authoritative set of world-country features.
 */
const WORLD_COUNTRIES_PATH = path.resolve(
  "public/data/global/countries/geojson/world-countries.geojson",
);

/**
 * Temporary MapTiler inspection output containing the 240 countries exposed
 * directly as `class="country"` place features.
 */
const MAPTILER_COUNTRY_NAMES_PATH = path.resolve(
  "scripts/global/countries/inspect/output/maptiler-country-names.json",
);

/**
 * Shared generated country-name metadata.
 */
const OUTPUT_PATH = path.resolve("src/countries/countryNames.ts");

/* -------------------------------------------------------------------------- */
/*                                    Types                                   */
/* -------------------------------------------------------------------------- */

type WorldCountryProperties = {
  name: string;
  iso_a3: string;
};

type WorldCountryFeature = {
  type: "Feature";
  properties: WorldCountryProperties;
};

type WorldCountryFeatureCollection = {
  type: "FeatureCollection";
  features: WorldCountryFeature[];
};

type MapTilerProperties = Record<string, unknown>;

type MapTilerCountryRecord = {
  geoPediaName: string;
  iso_a2: string;
  iso_a3: string;
  rawMapTilerIsoA2Codes: string[];
  firstSeenZoom: number;
  lastSeenZoom: number;
  occurrences: number;
  properties: MapTilerProperties;
  propertyConflicts: Record<string, unknown>;
};

type CountryNameData = {
  name: string;
  nativeName?: string;
};

/* -------------------------------------------------------------------------- */
/*                              Explicit Overrides                            */
/* -------------------------------------------------------------------------- */

/**
 * Countries for which MapTiler's local aggregate name is a longer English
 * identity rather than a useful native-language alternative.
 *
 * GeoPedia intentionally leaves nativeName absent for these countries.
 */
const OMIT_NATIVE_NAME = new Set<string>([
  "ATF",
  "FLK",
  "FSM",
  "HMD",
  "MNP",
  "PYF",
  "SGS",
  "SPM",
  "USA",
  "UMI",
  "VIR",
  "WLF",
]);

/**
 * Native-name overrides for cases where MapTiler's normal country feature
 * cannot directly provide the value GeoPedia needs.
 *
 * Palestine is represented by GeoPedia as a single feature containing both
 * the West Bank and Gaza. MapTiler's corresponding country-class feature is
 * named West Bank, so GeoPedia explicitly uses the Arabic country name.
 */
const NATIVE_NAME_OVERRIDES: Readonly<Record<string, string>> = {
  HKG: "香港",
  MAC: "澳門",
  NPL: "नेपाल",
  PSE: "فلسطين",
};

/**
 * GeoPedia countries that MapTiler does not expose as normal
 * `class="country"` place features.
 *
 * These values were verified separately against MapTiler's state/island place
 * features. Keeping them here makes the exceptional mapping explicit while
 * allowing the normal 240 countries to continue using MapTiler's country
 * metadata automatically.
 *
 * Undefined means MapTiler does not provide a meaningfully different local
 * name from GeoPedia's English name.
 */
const NON_COUNTRY_CLASS_NATIVE_NAMES: Readonly<
  Record<string, string | undefined>
> = {
  BVT: "Bouvetøya",
  BES: "Caribisch Nederland",
  CXR: undefined,
  CCK: undefined,
  GUF: "Guyane",
  GLP: undefined,
  MTQ: undefined,
  MYT: undefined,
  REU: "La Réunion",
  SJM: "Svalbard og Jan Mayen",
};

/**
 * Multilingual countries whose MapTiler aggregate name contains multiple
 * locally used names without a consistently usable separator.
 *
 * These overrides preserve MapTiler's local names while normalizing GeoPedia's
 * presentation to " / ".
 *
 * Countries whose MapTiler aggregate already contains "/", "-", or " - " are
 * normalized automatically and therefore do not need to appear here.
 */
const MULTILINGUAL_NATIVE_NAME_OVERRIDES: Readonly<
  Record<string, string>
> = {
  TCD: "Tchad / تشاد",
  COM: "Comores / Komori / جزر القمر",
  DJI: "Djibouti / جيبوتي",
  ERI: "ኤርትራ / Eritrea / إرتريا",
  LKA: "ශ්‍රී ලංකාව / இலங்கை",
  MAR: "Maroc / ⵍⵎⴰⵖⵔⵉⴱ / المغرب",
};

/* -------------------------------------------------------------------------- */
/*                               File Loading                                 */
/* -------------------------------------------------------------------------- */

/**
 * Reads and parses a JSON file.
 */
function readJson<T>(filePath: string): T {
  if (!fs.existsSync(filePath)) {
    throw new Error(`Required file was not found: ${filePath}`);
  }

  return JSON.parse(fs.readFileSync(filePath, "utf8")) as T;
}

/**
 * Loads GeoPedia's authoritative world-country feature collection.
 */
function loadWorldCountries(): WorldCountryFeatureCollection {
  const parsed = readJson<WorldCountryFeatureCollection>(
    WORLD_COUNTRIES_PATH,
  );

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
 * Loads the merged MapTiler country-name inspection output.
 */
function loadMapTilerCountries(): MapTilerCountryRecord[] {
  const parsed = readJson<unknown>(MAPTILER_COUNTRY_NAMES_PATH);

  if (!Array.isArray(parsed)) {
    throw new Error(
      "maptiler-country-names.json does not contain a JSON array.",
    );
  }

  return parsed as MapTilerCountryRecord[];
}

/* -------------------------------------------------------------------------- */
/*                                 Validation                                 */
/* -------------------------------------------------------------------------- */

/**
 * Validates one authoritative GeoPedia world-country feature.
 */
function validateWorldCountry(
  feature: WorldCountryFeature,
  index: number,
): void {
  const properties = feature.properties;

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
}

/**
 * Ensures GeoPedia's authoritative world-country data contains unique ISO-3
 * identifiers.
 */
function validateUniqueWorldCountryIds(
  features: WorldCountryFeature[],
): void {
  const seen = new Set<string>();

  for (const feature of features) {
    const isoA3 = feature.properties.iso_a3.trim();

    if (seen.has(isoA3)) {
      throw new Error(
        `Duplicate world-country iso_a3 value: ${isoA3}`,
      );
    }

    seen.add(isoA3);
  }
}

/**
 * Validates that the MapTiler inspection did not find conflicting property
 * values while merging repeated tile occurrences.
 */
function validateMapTilerConflicts(
  records: MapTilerCountryRecord[],
): void {
  for (const record of records) {
    const conflicts = Object.keys(record.propertyConflicts ?? {});

    if (conflicts.length > 0) {
      throw new Error(
        `${record.geoPediaName} (${record.iso_a3}) has conflicting ` +
          `MapTiler properties: ${conflicts.join(", ")}`,
      );
    }
  }
}

/* -------------------------------------------------------------------------- */
/*                              MapTiler Helpers                              */
/* -------------------------------------------------------------------------- */

/**
 * Returns a trimmed string property from one MapTiler feature.
 */
function getStringProperty(
  properties: MapTilerProperties,
  key: string,
): string | undefined {
  const value = properties[key];

  if (typeof value !== "string") {
    return undefined;
  }

  const trimmed = value.trim();

  return trimmed === "" ? undefined : trimmed;
}

/**
 * Builds the MapTiler lookup used for the normal 240 country-class records.
 */
function createMapTilerLookup(
  records: MapTilerCountryRecord[],
): Map<string, MapTilerCountryRecord> {
  const lookup = new Map<string, MapTilerCountryRecord>();

  for (const record of records) {
    const isoA3 = record.iso_a3?.trim();

    if (!isoA3) {
      throw new Error(
        "A MapTiler country record has no valid GeoPedia ISO-3 code.",
      );
    }

    if (lookup.has(isoA3)) {
      throw new Error(
        `Duplicate MapTiler GeoPedia ISO-3 code: ${isoA3}`,
      );
    }

    lookup.set(isoA3, record);
  }

  return lookup;
}

/* -------------------------------------------------------------------------- */
/*                           Native-Name Resolution                           */
/* -------------------------------------------------------------------------- */

/**
 * Normalizes explicit separators used by MapTiler when one country has
 * multiple locally used names.
 *
 * GeoPedia consistently displays those names using " / ".
 */
function normalizeMultilingualSeparators(value: string): string {
  return value
    .replace(/\s*\/\s*/g, " / ")
    .replace(/\s+-\s+/g, " / ")
    .replace(/\s{2,}/g, " ")
    .trim();
}

/**
 * Resolves the candidate local/native name from one normal MapTiler country
 * record.
 *
 * MapTiler's plain `name` property is preferred because it represents the
 * locally oriented aggregate label. It can contain multiple locally used
 * names, whereas `name:latin` and `name:nonlatin` can each contain only part
 * of the complete label.
 */
function resolveMapTilerNativeName(
  isoA3: string,
  record: MapTilerCountryRecord,
): string | undefined {
  const multilingualOverride =
    MULTILINGUAL_NATIVE_NAME_OVERRIDES[isoA3];

  if (multilingualOverride !== undefined) {
    return multilingualOverride;
  }

  const aggregateName = getStringProperty(record.properties, "name");

  if (!aggregateName) {
    return undefined;
  }

  return normalizeMultilingualSeparators(aggregateName);
}

/**
 * Resolves GeoPedia's optional native name for one country.
 *
 * Explicit identity exceptions are applied first. The ten countries not
 * represented by MapTiler's country class use their separately verified
 * state/island values. All remaining countries use the normal MapTiler
 * country record.
 *
 * Names meaningfully equivalent to the English display are omitted.
 */
function resolveNativeName(
  isoA3: string,
  englishName: string,
  mapTilerLookup: ReadonlyMap<string, MapTilerCountryRecord>,
): string | undefined {
  if (OMIT_NATIVE_NAME.has(isoA3)) {
    return undefined;
  }

  const explicitOverride = NATIVE_NAME_OVERRIDES[isoA3];

  if (explicitOverride !== undefined) {
    return areDisplayNamesEquivalent(englishName, explicitOverride)
      ? undefined
      : explicitOverride;
  }

  if (
    Object.prototype.hasOwnProperty.call(
      NON_COUNTRY_CLASS_NATIVE_NAMES,
      isoA3,
    )
  ) {
    const exceptionalName = NON_COUNTRY_CLASS_NATIVE_NAMES[isoA3];

    if (
      exceptionalName === undefined ||
      areDisplayNamesEquivalent(englishName, exceptionalName)
    ) {
      return undefined;
    }

    return exceptionalName;
  }

  const mapTilerRecord = mapTilerLookup.get(isoA3);

  if (!mapTilerRecord) {
    throw new Error(
      `No MapTiler country-name metadata found for ` +
        `${englishName} (${isoA3}).`,
    );
  }

  const nativeName = resolveMapTilerNativeName(isoA3, mapTilerRecord);

  if (
    nativeName === undefined ||
    areDisplayNamesEquivalent(englishName, nativeName)
  ) {
    return undefined;
  }

  return nativeName;
}

/* -------------------------------------------------------------------------- */
/*                            Country-Name Dataset                            */
/* -------------------------------------------------------------------------- */

/**
 * Creates reusable country-name metadata for all authoritative GeoPedia
 * countries.
 */
function createCountryNames(
  features: WorldCountryFeature[],
  mapTilerRecords: MapTilerCountryRecord[],
): Map<string, CountryNameData> {
  const mapTilerLookup = createMapTilerLookup(mapTilerRecords);

  const countryNames = new Map<string, CountryNameData>();

  for (const feature of features) {
    const isoA3 = feature.properties.iso_a3.trim();
    const name = feature.properties.name.trim();

    const nativeName = resolveNativeName(isoA3, name, mapTilerLookup);

    countryNames.set(isoA3, {
      name,
      ...(nativeName !== undefined ? { nativeName } : {}),
    });
  }

  return countryNames;
}

/**
 * Ensures every authoritative GeoPedia country was resolved exactly once.
 */
function validateCountryNameCoverage(
  features: WorldCountryFeature[],
  countryNames: ReadonlyMap<string, CountryNameData>,
): void {
  if (countryNames.size !== features.length) {
    throw new Error(
      `Expected ${features.length} generated country-name records, ` +
        `but resolved ${countryNames.size}.`,
    );
  }

  for (const feature of features) {
    const isoA3 = feature.properties.iso_a3.trim();

    if (!countryNames.has(isoA3)) {
      throw new Error(
        `Country-name metadata is missing ${feature.properties.name} ` +
          `(${isoA3}).`,
      );
    }
  }
}

/* -------------------------------------------------------------------------- */
/*                              Source Generation                             */
/* -------------------------------------------------------------------------- */

/**
 * Escapes a value as a TypeScript string literal.
 */
function quote(value: string): string {
  return JSON.stringify(value);
}

/**
 * Creates the generated shared country-name TypeScript module.
 *
 * Countries are sorted alphabetically by English name so the generated file
 * remains deterministic and easy to inspect.
 */
function createSource(
  countryNames: ReadonlyMap<string, CountryNameData>,
): string {
  const entries = [...countryNames.entries()].sort(
    ([, left], [, right]) =>
      left.name.localeCompare(right.name, "en"),
  );

  const lines = entries.map(([isoA3, country]) => {
    const properties = [`    name: ${quote(country.name)},`];

    if (country.nativeName !== undefined) {
      properties.push(
        `    nativeName: ${quote(country.nativeName)},`,
      );
    }

    return [`  ${quote(isoA3)}: {`, ...properties, "  },"].join("\n");
  });

  return `/**
 * Generated country-name metadata shared across GeoPedia.
 *
 * English names come from GeoPedia's authoritative world-country data.
 * Native names are derived from MapTiler local-name metadata and are omitted
 * when they are meaningfully equivalent to the English name.
 *
 * Countries with multiple locally used names separate those names with " / ".
 *
 * Do not edit manually.
 *
 * Regenerate with:
 * npx tsx scripts/global/countries/generate/country-names.ts
 */

export type CountryNameData = {
  name: string;
  nativeName?: string;
};

export const COUNTRY_NAMES: Readonly<
  Record<string, CountryNameData>
> = {
${lines.join("\n")}
};
`;
}

/* -------------------------------------------------------------------------- */
/*                                    Main                                    */
/* -------------------------------------------------------------------------- */

/**
 * Generates GeoPedia's shared country-name metadata.
 */
function main(): void {
  console.log("Generating shared country-name metadata...");

  const featureCollection = loadWorldCountries();
  const mapTilerRecords = loadMapTilerCountries();

  for (
    let index = 0;
    index < featureCollection.features.length;
    index++
  ) {
    validateWorldCountry(featureCollection.features[index], index);
  }

  validateUniqueWorldCountryIds(featureCollection.features);

  validateMapTilerConflicts(mapTilerRecords);

  if (mapTilerRecords.length !== 240) {
    throw new Error(
      `Expected 240 normal MapTiler country records, ` +
        `but found ${mapTilerRecords.length}.`,
    );
  }

  const countryNames = createCountryNames(
    featureCollection.features,
    mapTilerRecords,
  );

  validateCountryNameCoverage(
    featureCollection.features,
    countryNames,
  );

  fs.mkdirSync(path.dirname(OUTPUT_PATH), {
    recursive: true,
  });

  fs.writeFileSync(OUTPUT_PATH, createSource(countryNames), "utf8");

  const nativeNameCount = [...countryNames.values()].filter(
    (country) => country.nativeName !== undefined,
  ).length;

  console.log(`Generated ${countryNames.size} country-name records.`);

  console.log(
    `Countries with distinct native names: ${nativeNameCount}`,
  );

  console.log(
    `Countries without distinct native names: ` +
      `${countryNames.size - nativeNameCount}`,
  );

  console.log(`Output: ${OUTPUT_PATH}`);
}

main();
