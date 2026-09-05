/**
 * Generates GeoPedia's static CountryData objects and country registry.
 *
 * Source data:
 *
 *   data/raw/global/countries/rest-countries.json
 *
 * Page-enabled countries are determined by the SVG files present in:
 *
 *   public/data/country-images
 *
 * For every page-enabled country this script creates:
 *
 *   src/countries/data/[iso-a3].ts
 *
 * It also regenerates:
 *
 *   src/countries/index.ts
 *
 * Country IDs and filenames are always normalized to lowercase ISO-A3 codes,
 * matching the IDs used throughout GeoPedia's maps, routes, country data, and
 * quiz configuration.
 */

import fs from "node:fs";
import path from "node:path";

/**
 * Raw country record used by the source country dataset.
 *
 * Only fields required to construct GeoPedia's CountryData objects are
 * represented here.
 */
type SourceCountry = {
  names?: {
    common?: string;
    official?: string;
  };

  codes?: {
    alpha_3?: string;
  };

  capitals?: Array<{
    name?: string;
    attributes?: {
      primary?: boolean;
    };
  }>;

  calling_codes?: string[];

  cars?: {
    driving_side?: string;
  };

  region?: string;
  subregion?: string;

  continents?: string[];

  population?: number;
};

/**
 * Intermediate representation used while generating TypeScript files.
 */
type GeneratedCountry = {
  id: string;
  name: string;
  officialName: string;
  continent: string;
  region: string;
  callingCode: string;
  drivingSide: "left" | "right";
  flagUrl: string;
  imageUrl: string;
  capital: string;
  population: number;

  /**
   * Exact filename found on disk.
   *
   * Keeping the real filename allows asset URLs to remain correct even if the
   * asset files themselves use uppercase ISO codes while GeoPedia's logical
   * IDs use lowercase codes.
   */
  imageFilename: string;
  flagFilename: string;
};

const SOURCE_COUNTRIES_PATH =
  "data/raw/global/countries/rest-countries.json";

const COUNTRY_IMAGES_DIRECTORY =
  "public/data/global/countries/silhouettes";

const COUNTRY_FLAGS_DIRECTORY = "public/data/global/countries/flags";

const COUNTRY_DATA_DIRECTORY = "src/countries/data";

const COUNTRY_INDEX_PATH = "src/countries/index.ts";

/**
 * Reads and parses the source country dataset.
 */
function readSourceCountries(): SourceCountry[] {
  if (!fs.existsSync(SOURCE_COUNTRIES_PATH)) {
    throw new Error(
      `Country source data not found: ${SOURCE_COUNTRIES_PATH}`,
    );
  }

  const rawJson = fs.readFileSync(SOURCE_COUNTRIES_PATH, "utf8");

  const parsed = JSON.parse(rawJson);

  if (!Array.isArray(parsed)) {
    throw new Error(
      `Expected ${SOURCE_COUNTRIES_PATH} to contain an array.`,
    );
  }

  return parsed as SourceCountry[];
}

/**
 * Returns all SVG files inside an asset directory.
 */
function getSvgFilenames(directory: string): string[] {
  if (!fs.existsSync(directory)) {
    throw new Error(`Asset directory not found: ${directory}`);
  }

  return fs
    .readdirSync(directory, {
      withFileTypes: true,
    })
    .filter(
      (entry) =>
        entry.isFile() && entry.name.toLowerCase().endsWith(".svg"),
    )
    .map((entry) => entry.name)
    .sort((first, second) => first.localeCompare(second));
}

/**
 * Converts an asset filename into GeoPedia's canonical country ID.
 *
 * Example:
 *
 *   USA.svg
 *   -> usa
 */
function getCountryIdFromFilename(filename: string): string {
  return path
    .basename(filename, path.extname(filename))
    .toLowerCase();
}

/**
 * Returns the source country's lowercase ISO-A3 ID.
 */
function getSourceCountryId(country: SourceCountry): string | null {
  const alpha3 = country.codes?.alpha_3?.trim();

  if (!alpha3) {
    return null;
  }

  if (!/^[A-Za-z]{3}$/.test(alpha3)) {
    return null;
  }

  return alpha3.toLowerCase();
}

/**
 * Finds the source record belonging to one page-enabled country.
 *
 * Most countries are matched directly by ISO-A3 code.
 *
 * Kosovo is the one known special case. GeoPedia assigns it the conventional
 * synthetic ISO-like ID "xkx", while the source country dataset does not expose
 * XKX as a normal alpha-3 code.
 */
function findSourceCountry(
  countryId: string,
  countriesById: Map<string, SourceCountry>,
  sourceCountries: SourceCountry[],
): SourceCountry | undefined {
  const directMatch = countriesById.get(countryId);

  if (directMatch) {
    return directMatch;
  }

  if (countryId === "xkx") {
    return sourceCountries.find(
      (country) =>
        country.names?.common?.trim().toLowerCase() === "kosovo",
    );
  }

  return undefined;
}

/**
 * Returns the preferred capital display string.
 *
 * The source dataset can contain multiple capitals. GeoPedia's CountryData
 * currently stores a single string, so multiple names are retained by joining
 * them rather than silently discarding secondary capitals.
 */
function getCapital(country: SourceCountry): string {
  const capitals = country.capitals ?? [];

  const names = capitals
    .map((capital) => capital.name?.trim())
    .filter((name): name is string => Boolean(name));

  return names.join(", ");
}

/**
 * Returns the country's calling-code display string.
 *
 * Multiple calling codes are preserved rather than discarding data.
 */
function getCallingCode(country: SourceCountry): string {
  return (country.calling_codes ?? [])
    .map((code) => code.trim())
    .filter(Boolean)
    .join(", ");
}

/**
 * Normalizes the source driving-side value into CountryData's supported union.
 */
function getDrivingSide(country: SourceCountry): "left" | "right" {
  const drivingSide = country.cars?.driving_side
    ?.trim()
    .toLowerCase();

  if (drivingSide !== "left" && drivingSide !== "right") {
    throw new Error(
      `Invalid driving side for ${country.names?.common ?? "unknown country"}: ${String(
        country.cars?.driving_side,
      )}`,
    );
  }

  return drivingSide;
}

/**
 * Finds an asset filename by lowercase country ID.
 */
function createAssetFilenameMap(
  filenames: string[],
): Map<string, string> {
  return new Map(
    filenames.map((filename) => [
      getCountryIdFromFilename(filename),
      filename,
    ]),
  );
}

/**
 * Converts one source country into the structure written to a CountryData file.
 */
function createGeneratedCountry(
  countryId: string,
  sourceCountry: SourceCountry,
  imageFilename: string,
  flagFilename: string,
): GeneratedCountry {
  const name = sourceCountry.names?.common?.trim();

  const officialName = sourceCountry.names?.official?.trim();

  if (!name) {
    throw new Error(`Country ${countryId} has no common name.`);
  }

  if (!officialName) {
    throw new Error(`Country ${countryId} has no official name.`);
  }

  const continent = sourceCountry.continents?.[0]?.trim() ?? "";

  /*
   * GeoPedia's "region" field stores the more geographically useful
   * subregional value when available.
   *
   * Example:
   *
   *   continent: "North America"
   *   region: "Northern America"
   */
  const region =
    sourceCountry.subregion?.trim() ||
    sourceCountry.region?.trim() ||
    "";

  const population = sourceCountry.population;

  if (
    typeof population !== "number" ||
    !Number.isFinite(population) ||
    population < 0
  ) {
    throw new Error(
      `Country ${countryId} has an invalid population.`,
    );
  }

  return {
    id: countryId,
    name,
    officialName,
    continent,
    region,
    callingCode: getCallingCode(sourceCountry),
    drivingSide: getDrivingSide(sourceCountry),

    /*
     * Use the exact filenames discovered on disk. Logical country IDs remain
     * lowercase independently of asset filename casing.
     */
    flagUrl: `/data/global/countries/flags/${flagFilename}`,
    imageUrl: `/data/global/countries/silhouettes/${imageFilename}`,

    capital: getCapital(sourceCountry),
    population,

    imageFilename,
    flagFilename,
  };
}

/**
 * Serializes a string as a TypeScript string literal.
 *
 * JSON.stringify correctly escapes quotes, slashes, Unicode-sensitive
 * characters, and other content that could otherwise produce invalid source.
 */
function tsString(value: string): string {
  return JSON.stringify(value);
}

/**
 * Generates one static CountryData module.
 */
function createCountryFile(country: GeneratedCountry): string {
  return `import type { CountryData } from "@/types/country";
  
/**
 * Static country metadata for ${country.name}.
 *
 * This file is generated by:
 *
 *   scripts/generate/generate-country-data-objects.ts
 *
 * Do not edit this file manually.
 */
export const ${country.id}: CountryData = {
  id: ${tsString(country.id)},
  name: ${tsString(country.name)},
  officialName: ${tsString(country.officialName)},
  continent: ${tsString(country.continent)},
  region: ${tsString(country.region)},
  callingCode: ${tsString(country.callingCode)},
  drivingSide: ${tsString(country.drivingSide)},
  flagUrl: ${tsString(country.flagUrl)},
  imageUrl: ${tsString(country.imageUrl)},
  capital: ${tsString(country.capital)},
  population: ${country.population},
};
`;
}

/**
 * Generates src/countries/index.ts.
 *
 * Imports and registry entries are sorted by country ID so regeneration remains
 * deterministic and produces clean Git diffs.
 */
function createCountryIndex(countries: GeneratedCountry[]): string {
  const sortedCountries = [...countries].sort((first, second) =>
    first.id.localeCompare(second.id),
  );

  const imports = sortedCountries
    .map(
      (country) =>
        `import { ${country.id} } from "./data/${country.id}";`,
    )
    .join("\n");

  const registryEntries = sortedCountries
    .map((country) => `  ${country.id},`)
    .join("\n");

  return `/**
 * Registry and lookup helpers for GeoPedia country metadata.
 *
 * The country imports and registry entries in this file are generated by:
 *
 *   scripts/generate/generate-country-data-objects.ts
 *
 * Do not add generated country imports manually.
 */

import { CountryData } from "@/types/country";

${imports}

/**
 * Static country metadata keyed by lowercase ISO-A3 country ID.
 */
const countries: Partial<Record<string, CountryData>> = {
${registryEntries}
};

/**
 * Returns country metadata for an ISO-A3 country ID.
 *
 * Country IDs are normalized to lowercase so callers may safely provide IDs
 * from routes, map features, or other external sources without duplicating
 * normalization logic.
 */
export function getCountry(
  countryId: string,
): CountryData | undefined {
  return countries[countryId.toLowerCase()];
}

/**
 * Returns every country represented by a GeoPedia country page.
 */
export function getCountries(): CountryData[] {
  return Object.values(countries).filter(
    (country): country is CountryData =>
      country !== undefined,
  );
}
`;
}

/**
 * Removes previously generated country modules.
 *
 * Only `.ts` files inside src/countries/data are removed. The directory is
 * dedicated entirely to generated CountryData modules.
 */
function clearGeneratedCountryFiles(): void {
  fs.mkdirSync(COUNTRY_DATA_DIRECTORY, {
    recursive: true,
  });

  for (const filename of fs.readdirSync(COUNTRY_DATA_DIRECTORY)) {
    if (!filename.toLowerCase().endsWith(".ts")) {
      continue;
    }

    fs.unlinkSync(path.join(COUNTRY_DATA_DIRECTORY, filename));
  }
}

/**
 * Generates every country module and the country registry.
 */
function main(): void {
  console.log("Generating GeoPedia CountryData objects...");

  const sourceCountries = readSourceCountries();

  const imageFilenames = getSvgFilenames(COUNTRY_IMAGES_DIRECTORY);

  const flagFilenames = getSvgFilenames(COUNTRY_FLAGS_DIRECTORY);

  const imageFilenameByCountryId =
    createAssetFilenameMap(imageFilenames);

  const flagFilenameByCountryId =
    createAssetFilenameMap(flagFilenames);

  /*
   * Build direct ISO-A3 lookup table for normal countries.
   */
  const countriesById = new Map<string, SourceCountry>();

  for (const country of sourceCountries) {
    const countryId = getSourceCountryId(country);

    if (!countryId) {
      continue;
    }

    if (countriesById.has(countryId)) {
      throw new Error(`Duplicate source country ID: ${countryId}`);
    }

    countriesById.set(countryId, country);
  }

  const generatedCountries: GeneratedCountry[] = [];

  const missingSourceCountries: string[] = [];

  const missingFlags: string[] = [];

  /*
   * Country images intentionally define which countries receive GeoPedia
   * country pages and therefore which CountryData objects are generated.
   */
  for (const [countryId, imageFilename] of imageFilenameByCountryId) {
    const sourceCountry = findSourceCountry(
      countryId,
      countriesById,
      sourceCountries,
    );

    if (!sourceCountry) {
      missingSourceCountries.push(countryId);
      continue;
    }

    const flagFilename = flagFilenameByCountryId.get(countryId);

    if (!flagFilename) {
      missingFlags.push(countryId);
      continue;
    }

    generatedCountries.push(
      createGeneratedCountry(
        countryId,
        sourceCountry,
        imageFilename,
        flagFilename,
      ),
    );
  }

  if (missingSourceCountries.length > 0) {
    throw new Error(
      [
        "Page-enabled countries missing source records:",
        ...missingSourceCountries.map(
          (countryId) => `  ${countryId}`,
        ),
      ].join("\n"),
    );
  }

  if (missingFlags.length > 0) {
    throw new Error(
      [
        "Page-enabled countries missing flags:",
        ...missingFlags.map((countryId) => `  ${countryId}`),
      ].join("\n"),
    );
  }

  generatedCountries.sort((first, second) =>
    first.id.localeCompare(second.id),
  );

  clearGeneratedCountryFiles();

  for (const country of generatedCountries) {
    const outputPath = path.join(
      COUNTRY_DATA_DIRECTORY,
      `${country.id}.ts`,
    );

    fs.writeFileSync(outputPath, createCountryFile(country), "utf8");
  }

  fs.writeFileSync(
    COUNTRY_INDEX_PATH,
    createCountryIndex(generatedCountries),
    "utf8",
  );

  /*
   * Final validation ensures our generated registry represents every
   * page-enabled country image exactly once.
   */
  const generatedIds = new Set(
    generatedCountries.map((country) => country.id),
  );

  if (generatedIds.size !== generatedCountries.length) {
    throw new Error("Duplicate generated country IDs detected.");
  }

  if (generatedCountries.length !== imageFilenames.length) {
    throw new Error(
      `Generated ${generatedCountries.length} countries from ${imageFilenames.length} page images.`,
    );
  }

  console.log("");
  console.log("COUNTRY DATA GENERATION COMPLETE");
  console.log("--------------------------------");
  console.log(`Source country records: ${sourceCountries.length}`);
  console.log(`Country page images: ${imageFilenames.length}`);
  console.log(`Country flags available: ${flagFilenames.length}`);
  console.log(
    `CountryData objects generated: ${generatedCountries.length}`,
  );
  console.log(
    `Country registry entries: ${generatedCountries.length}`,
  );
  console.log("");
  console.log(`Country data directory: ${COUNTRY_DATA_DIRECTORY}`);
  console.log(`Country registry: ${COUNTRY_INDEX_PATH}`);
}

main();
