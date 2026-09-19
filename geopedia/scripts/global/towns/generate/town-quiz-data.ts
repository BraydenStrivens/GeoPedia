/**
 * Generates GeoPedia's per-country town quiz datasets by combining:
 *
 * - GeoNames:
 *     population
 *     country code
 *     national-capital status
 *     stable GeoNames ID
 *
 * - GeoPedia's processed OSM towns.geojson:
 *     OSM settlement classification
 *     ("city", "town", "village", "hamlet", "suburb", etc.)
 *
 * OSM `city` and `town` settlements form the primary quiz pool. `village`
 * settlements may supplement countries that do not reach the configured quiz
 * maximum with primary settlements alone.
 *
 * Source files:
 *
 *   data/raw/global/towns/geonames/allCountries.txt
 *   public/data/global/towns/towns.geojson
 *   public/data/global/countries/geojson/world-countries.geojson
 *
 * Output:
 *
 *   public/data/global/towns/countries/{countryId}.json
 *
 * Example:
 *
 *   public/data/global/towns/countries/usa.json
 *   public/data/global/towns/countries/fra.json
 *   public/data/global/towns/countries/jpn.json
 */

import fs from "node:fs";
import { createRequire } from "node:module";
import path from "node:path";
import readline from "node:readline";

import { parser } from "stream-json";

const require = createRequire(import.meta.url);

const { pick } = require("stream-json/filters/pick.js") as {
  pick: {
    asStream: (options: { filter: string }) => NodeJS.ReadWriteStream;
  };
};

const { streamArray } =
  require("stream-json/streamers/stream-array.js") as {
    streamArray: {
      asStream: () => NodeJS.ReadWriteStream;
    };
  };

/* -------------------------------------------------------------------------- */
/* Paths                                                                      */
/* -------------------------------------------------------------------------- */

const GEONAMES_PATH =
  "data/raw/global/towns/geonames/allCountries.txt";

const OSM_TOWNS_PATH = "public/data/global/towns/towns.geojson";

const WORLD_COUNTRIES_PATH =
  "public/data/global/countries/geojson/world-countries.geojson";

const OUTPUT_DIRECTORY = "public/data/global/towns/countries/";

/* -------------------------------------------------------------------------- */
/* Generation settings                                                        */
/* -------------------------------------------------------------------------- */

/**
 * Maximum number of towns stored for one country.
 *
 * Large countries may expose up to 300 settlements so advanced GeoGuessr
 * players can study a substantially deeper set of useful town names.
 */
const MAX_TOWN_COUNT = 300;

/**
 * Number of high-population GeoNames settlements retained per country before
 * OSM matching.
 *
 * The candidate pool is intentionally several times larger than the final quiz
 * limit because some GeoNames records cannot be matched reliably to an OSM
 * settlement or represent place types unsuitable for quizzes.
 *
 * Retaining 1,500 candidates provides headroom for up to 300 primary and
 * supplemental quiz settlements without retaining every populated place in
 * large countries.
 */
const GEONAMES_CANDIDATE_COUNT = 1_500;

/**
 * Maximum distance allowed when the GeoNames primary or ASCII name matches
 * the OSM settlement name.
 *
 * Primary and ASCII names are strong identity signals, so they can tolerate
 * a larger coordinate offset between the two source datasets.
 */
const PRIMARY_NAME_MATCH_MAX_DISTANCE_KM = 20;

/**
 * Maximum distance allowed when an OSM settlement name matches only one of
 * the GeoNames alternate names.
 *
 * Alternate names are weaker identity signals because GeoNames alternate-name
 * lists can contain names associated with nearby or administratively related
 * places. Keeping this threshold small prevents cases such as Aihara matching
 * Sagamihara through an alternate name several kilometers away.
 */
const ALTERNATE_NAME_MATCH_MAX_DISTANCE_KM = 2;

/**
 * Maximum distance allowed when no usable name match exists and the two
 * records are matched solely by coordinates.
 */
const COORDINATE_ONLY_MATCH_MAX_DISTANCE_KM = 1;

/**
 * Primary OSM settlement classifications used by town quizzes.
 *
 * Cities and towns form the core quiz dataset and always take priority over
 * supplemental settlements.
 */
const PRIMARY_OSM_PLACE_TYPES = new Set<SettlementPlaceType>([
  "city",
  "town",
]);

/**
 * Smaller OSM settlement classifications that may supplement a country's quiz
 * when fewer than the configured maximum number of primary settlements exist.
 *
 * Villages provide useful additional GeoGuessr place-name coverage without
 * broadening quizzes to suburbs, hamlets, or isolated dwellings.
 */
const SUPPLEMENTAL_OSM_PLACE_TYPES = new Set<SettlementPlaceType>([
  "village",
]);

/**
 * All OSM settlement classifications that must be retained in the spatial
 * index for town-quiz generation.
 */
const INDEXED_OSM_PLACE_TYPES = new Set<SettlementPlaceType>([
  ...PRIMARY_OSM_PLACE_TYPES,
  ...SUPPLEMENTAL_OSM_PLACE_TYPES,
]);

/**
 * GeoNames populated-place classifications eligible for town quizzes.
 *
 * PPLG is included because some important government seats, such as La Paz,
 * are classified separately from conventional national capitals.
 */
const INCLUDED_GEONAMES_FEATURE_CODES = new Set([
  "PPL",
  "PPLA",
  "PPLA2",
  "PPLA3",
  "PPLA4",
  "PPLC",
  "PPLG",
]);

/**
 * GeoNames feature codes treated as capital-level settlements in runtime quiz
 * data. PPLG is included so seats of government such as La Paz can receive the
 * same capital-specific map treatment as conventional national capitals.
 */
const CAPITAL_GEONAMES_FEATURE_CODES = new Set(["PPLC", "PPLG"]);

/* -------------------------------------------------------------------------- */
/* Types                                                                      */
/* -------------------------------------------------------------------------- */

/**
 * One object emitted by stream-json's StreamArray transform.
 *
 * `key` is the zero-based array index and `value` is the parsed array item.
 */
type StreamArrayItem<T> = {
  key: number;
  value: T;
};

type SettlementPlaceType =
  | "city"
  | "town"
  | "village"
  | "hamlet"
  | "suburb"
  | "isolated_dwelling";

type GeoNamesTown = {
  id: string;

  name: string;
  asciiName: string;

  alternateNames: string[];

  latitude: number;
  longitude: number;

  featureCode: string;

  countryCode: string;

  population: number;
};

type OsmTown = {
  /**
   * Stable OpenStreetMap identifier retained so multiple GeoNames records
   * matched to the same OSM settlement can be detected.
   */
  osmId: string;

  /**
   * Primary locally used OSM settlement name.
   */
  name: string;

  /**
   * Explicit English/international OSM settlement name when available.
   */
  englishName?: string;

  place: SettlementPlaceType;

  latitude: number;
  longitude: number;
};

/**
 * Describes which GeoNames name field established identity with an OSM
 * settlement.
 *
 * An alternate name matching OSM's explicit English name is treated more
 * strongly than an alternate name matching OSM's primary/local name because
 * `englishName` is an intentional international-name field rather than an
 * arbitrary nearby or historical alias.
 */
type NameMatchType =
  "primary" | "ascii" | "alternateEnglish" | "alternate" | null;

type MatchedTown = {
  geoNamesTown: GeoNamesTown;

  osmTown: OsmTown;

  matchType: "name" | "coordinates";

  nameMatchType: NameMatchType;

  distanceKm: number;
};

type TownQuizTown = {
  id: string;

  /**
   * Preferred quiz-display name.
   *
   * Genuine translations prefer the English/international form, while
   * equivalent native and English spellings collapse to the cleaner locally
   * appropriate representation.
   */
  name: string;

  /**
   * Native/local settlement name when meaningfully different from `name`.
   */
  nativeName?: string;

  latitude: number;
  longitude: number;

  population: number;

  populationRank: number;

  isCapital: boolean;
};

type TownQuizData = {
  towns: TownQuizTown[];
};

type WorldCountryFeature = {
  properties?: {
    iso_a2?: string;
    iso_a3?: string;
    name?: string;
  };
};

type WorldCountriesGeoJson = {
  features?: WorldCountryFeature[];
};

type OsmTownFeature = {
  type?: string;

  geometry?: {
    type?: string;
    coordinates?: unknown;
  };

  properties?: {
    osmId?: unknown;

    name?: unknown;
    englishName?: unknown;

    place?: unknown;
  };
};

type CountryGenerationStats = {
  countryCode: string;

  countryId: string;

  geoNamesCandidates: number;

  matchedCitiesAndTowns: number;

  matchedVillages: number;

  nameMatches: number;

  coordinateMatches: number;

  generatedTowns: number;
};

/* -------------------------------------------------------------------------- */
/* GeoNames column indexes                                                    */
/* -------------------------------------------------------------------------- */

/**
 * GeoNames allCountries.txt is tab-delimited.
 *
 * Full format documentation:
 *
 *   0  geonameid
 *   1  name
 *   2  asciiname
 *   3  alternatenames
 *   4  latitude
 *   5  longitude
 *   6  feature class
 *   7  feature code
 *   8  country code
 *   ...
 *   14 population
 */
const GEONAMES_COLUMNS = {
  geonameId: 0,
  name: 1,
  asciiName: 2,
  alternateNames: 3,

  latitude: 4,
  longitude: 5,

  featureClass: 6,
  featureCode: 7,

  countryCode: 8,

  population: 14,
} as const;

/* -------------------------------------------------------------------------- */
/* General helpers                                                            */
/* -------------------------------------------------------------------------- */

/**
 * Normalizes a settlement name for cross-dataset comparison.
 *
 * The normalization deliberately ignores:
 *
 * - capitalization
 * - accents/diacritics
 * - punctuation
 * - whitespace
 *
 * Unicode letters and numbers are preserved so names written in Cyrillic,
 * Greek, Japanese, Bengali, Georgian, Armenian, and other scripts can
 * participate in name-based matching rather than falling back unnecessarily
 * to coordinate-only matching.
 *
 * This function does not transliterate between scripts or attempt fuzzy
 * spelling correction.
 *
 * @param value - Settlement name to normalize.
 * @returns Comparable Unicode settlement-name key.
 */
function normalizeTownName(value: string): string {
  return value
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "")
    .toLowerCase()
    .replace(/[^\p{Letter}\p{Number}]+/gu, "");
}

/**
 * Converts degrees to radians.
 */
function degreesToRadians(value: number): number {
  return (value * Math.PI) / 180;
}

/**
 * Calculates great-circle distance between two geographic points.
 *
 * @returns Distance in kilometers.
 */
function getDistanceKm(
  firstLatitude: number,
  firstLongitude: number,
  secondLatitude: number,
  secondLongitude: number,
): number {
  const earthRadiusKm = 6_371.0088;

  const latitudeDifference = degreesToRadians(
    secondLatitude - firstLatitude,
  );

  const longitudeDifference = degreesToRadians(
    secondLongitude - firstLongitude,
  );

  const firstLatitudeRadians = degreesToRadians(firstLatitude);

  const secondLatitudeRadians = degreesToRadians(secondLatitude);

  const haversine =
    Math.sin(latitudeDifference / 2) ** 2 +
    Math.cos(firstLatitudeRadians) *
      Math.cos(secondLatitudeRadians) *
      Math.sin(longitudeDifference / 2) ** 2;

  const angularDistance =
    2 * Math.atan2(Math.sqrt(haversine), Math.sqrt(1 - haversine));

  return earthRadiusKm * angularDistance;
}

/* -------------------------------------------------------------------------- */
/* Country IDs                                                                */
/* -------------------------------------------------------------------------- */

/**
 * Loads GeoPedia's ISO-2 -> lowercase ISO-3 country mapping.
 */
function loadCountryIdMap(): Map<string, string> {
  const rawGeoJson = fs.readFileSync(WORLD_COUNTRIES_PATH, "utf8");

  const geoJson = JSON.parse(rawGeoJson) as WorldCountriesGeoJson;

  const countryIds = new Map<string, string>();

  for (const feature of geoJson.features ?? []) {
    const isoA2 = feature.properties?.iso_a2?.trim().toUpperCase();

    const isoA3 = feature.properties?.iso_a3?.trim().toLowerCase();

    if (!isoA2 || !isoA3) {
      continue;
    }

    countryIds.set(isoA2, isoA3);
  }

  return countryIds;
}

/* -------------------------------------------------------------------------- */
/* GeoNames                                                                   */
/* -------------------------------------------------------------------------- */

/**
 * Maximum distance between a zero-population populated place and an
 * administrative record whose population may be used as a fallback.
 *
 * The fallback also requires an exact normalized-name match and the same
 * country, so this radius only accommodates modest coordinate differences
 * between GeoNames representations of the same place.
 */
const ADMIN_POPULATION_FALLBACK_MAX_DISTANCE_KM = 10;

/**
 * Spatial-cell size used for nearby administrative-population lookups.
 */
const ADMIN_POPULATION_SPATIAL_CELL_SIZE = 0.1;

/**
 * Compact positive-population administrative record retained during the first
 * GeoNames pass.
 */
type GeoNamesAdministrativePopulation = {
  countryCode: string;

  normalizedNames: string[];

  latitude: number;
  longitude: number;

  population: number;
};

/**
 * Parses one positive GeoNames population.
 */
function parsePopulation(value: string | undefined): number | null {
  if (!value) {
    return null;
  }

  const population = Number(value);

  if (!Number.isFinite(population) || population <= 0) {
    return null;
  }

  return Math.round(population);
}

/**
 * Parses one GeoNames alternate-name column into trimmed source names.
 */
function parseGeoNamesAlternateNames(
  value: string | undefined,
): string[] {
  return (value ?? "")
    .split(",")
    .map((alternateName) => alternateName.trim())
    .filter(Boolean);
}

/**
 * Parses the shared identity and coordinate fields required by a GeoNames
 * populated-place candidate.
 */
function parseGeoNamesTownIdentity(
  columns: string[],
  population: number,
): GeoNamesTown | null {
  if (columns[GEONAMES_COLUMNS.featureClass] !== "P") {
    return null;
  }

  const featureCode = columns[GEONAMES_COLUMNS.featureCode];

  if (!INCLUDED_GEONAMES_FEATURE_CODES.has(featureCode)) {
    return null;
  }

  const id = columns[GEONAMES_COLUMNS.geonameId]?.trim();

  const name = columns[GEONAMES_COLUMNS.name]?.trim();

  const asciiName = columns[GEONAMES_COLUMNS.asciiName]?.trim() ?? "";

  const countryCode = columns[GEONAMES_COLUMNS.countryCode]
    ?.trim()
    .toUpperCase();

  const latitude = Number(columns[GEONAMES_COLUMNS.latitude]);

  const longitude = Number(columns[GEONAMES_COLUMNS.longitude]);

  if (
    !id ||
    !name ||
    !countryCode ||
    !Number.isFinite(latitude) ||
    !Number.isFinite(longitude)
  ) {
    return null;
  }

  return {
    id,

    name,
    asciiName,

    alternateNames: parseGeoNamesAlternateNames(
      columns[GEONAMES_COLUMNS.alternateNames],
    ),

    latitude,
    longitude,

    featureCode,

    countryCode,

    population,
  };
}

/**
 * Parses one normal positive-population GeoNames populated-place row.
 */
function parseGeoNamesTown(columns: string[]): GeoNamesTown | null {
  const population = parsePopulation(
    columns[GEONAMES_COLUMNS.population],
  );

  if (population === null) {
    return null;
  }

  return parseGeoNamesTownIdentity(columns, population);
}

/**
 * Parses one zero-population GeoNames populated place that may be rescued by a
 * nearby administrative population during the second GeoNames pass.
 *
 * Missing, malformed, and negative populations are deliberately rejected. Only
 * an explicit source population of zero participates in this fallback.
 */
function parseZeroPopulationGeoNamesTown(
  columns: string[],
): GeoNamesTown | null {
  const populationValue = Number(
    columns[GEONAMES_COLUMNS.population],
  );

  if (!Number.isFinite(populationValue) || populationValue !== 0) {
    return null;
  }

  return parseGeoNamesTownIdentity(columns, 0);
}

/**
 * Returns normalized names that can establish identity between two GeoNames
 * representations of the same place.
 */
function getNormalizedGeoNamesNames(
  name: string,
  asciiName: string,
  alternateNames: string[],
): string[] {
  return Array.from(
    new Set(
      [name, asciiName, ...alternateNames]
        .map((candidateName) => normalizeTownName(candidateName))
        .filter(Boolean),
    ),
  );
}

/**
 * Creates a geographic lookup key for an administrative population record.
 */
function getAdminPopulationSpatialCellKey(
  countryCode: string,
  latitude: number,
  longitude: number,
): string {
  const latitudeCell = Math.floor(
    latitude / ADMIN_POPULATION_SPATIAL_CELL_SIZE,
  );

  const longitudeCell = Math.floor(
    longitude / ADMIN_POPULATION_SPATIAL_CELL_SIZE,
  );

  return `${countryCode}:${latitudeCell}:${longitudeCell}`;
}

/**
 * Parses one positive-population GeoNames administrative record.
 *
 * Administrative records never become quiz questions directly. They are kept
 * only as possible population donors for nearby zero-population populated-place
 * records representing the same named place.
 */
function parseGeoNamesAdministrativePopulation(
  columns: string[],
): GeoNamesAdministrativePopulation | null {
  if (columns[GEONAMES_COLUMNS.featureClass] !== "A") {
    return null;
  }

  const population = parsePopulation(
    columns[GEONAMES_COLUMNS.population],
  );

  if (population === null) {
    return null;
  }

  const name = columns[GEONAMES_COLUMNS.name]?.trim();

  const asciiName = columns[GEONAMES_COLUMNS.asciiName]?.trim() ?? "";

  const countryCode = columns[GEONAMES_COLUMNS.countryCode]
    ?.trim()
    .toUpperCase();

  const latitude = Number(columns[GEONAMES_COLUMNS.latitude]);

  const longitude = Number(columns[GEONAMES_COLUMNS.longitude]);

  if (
    !name ||
    !countryCode ||
    !Number.isFinite(latitude) ||
    !Number.isFinite(longitude)
  ) {
    return null;
  }

  const normalizedNames = getNormalizedGeoNamesNames(
    name,
    asciiName,
    parseGeoNamesAlternateNames(
      columns[GEONAMES_COLUMNS.alternateNames],
    ),
  );

  if (normalizedNames.length === 0) {
    return null;
  }

  return {
    countryCode,
    normalizedNames,
    latitude,
    longitude,
    population,
  };
}

/**
 * Inserts one administrative population into the compact spatial lookup used
 * by the zero-population rescue pass.
 */
function addAdministrativePopulation(
  index: Map<string, GeoNamesAdministrativePopulation[]>,
  administrativePopulation: GeoNamesAdministrativePopulation,
): void {
  const key = getAdminPopulationSpatialCellKey(
    administrativePopulation.countryCode,
    administrativePopulation.latitude,
    administrativePopulation.longitude,
  );

  const bucket = index.get(key);

  if (bucket) {
    bucket.push(administrativePopulation);
  } else {
    index.set(key, [administrativePopulation]);
  }
}

/**
 * Returns nearby administrative-population records in the same country.
 */
function getNearbyAdministrativePopulations(
  town: GeoNamesTown,
  index: Map<string, GeoNamesAdministrativePopulation[]>,
): GeoNamesAdministrativePopulation[] {
  const latitudeCell = Math.floor(
    town.latitude / ADMIN_POPULATION_SPATIAL_CELL_SIZE,
  );

  const longitudeCell = Math.floor(
    town.longitude / ADMIN_POPULATION_SPATIAL_CELL_SIZE,
  );

  const nearby: GeoNamesAdministrativePopulation[] = [];

  /*
   * A 5x5 window provides comfortable coverage for the 10 km fallback radius,
   * including records lying near cell edges.
   */
  for (
    let latitudeOffset = -2;
    latitudeOffset <= 2;
    latitudeOffset += 1
  ) {
    for (
      let longitudeOffset = -2;
      longitudeOffset <= 2;
      longitudeOffset += 1
    ) {
      const key = `${town.countryCode}:${
        latitudeCell + latitudeOffset
      }:${longitudeCell + longitudeOffset}`;

      const bucket = index.get(key);

      if (bucket) {
        nearby.push(...bucket);
      }
    }
  }

  return nearby;
}

/**
 * Finds the best administrative population that can safely rescue one
 * zero-population populated-place record.
 *
 * Identity requires at least one exact normalized GeoNames name in common,
 * plus the same country and close coordinates. The nearest valid record wins;
 * population breaks an exact distance tie deterministically.
 */
function findAdministrativePopulationFallback(
  town: GeoNamesTown,
  index: Map<string, GeoNamesAdministrativePopulation[]>,
): GeoNamesAdministrativePopulation | null {
  const townNames = new Set(
    getNormalizedGeoNamesNames(
      town.name,
      town.asciiName,
      town.alternateNames,
    ),
  );

  let bestMatch:
    | {
        administrativePopulation: GeoNamesAdministrativePopulation;
        distanceKm: number;
      }
    | undefined;

  for (const administrativePopulation of getNearbyAdministrativePopulations(
    town,
    index,
  )) {
    const namesMatch = administrativePopulation.normalizedNames.some(
      (normalizedName) => townNames.has(normalizedName),
    );

    if (!namesMatch) {
      continue;
    }

    const distanceKm = getDistanceKm(
      town.latitude,
      town.longitude,
      administrativePopulation.latitude,
      administrativePopulation.longitude,
    );

    if (distanceKm > ADMIN_POPULATION_FALLBACK_MAX_DISTANCE_KM) {
      continue;
    }

    if (
      !bestMatch ||
      distanceKm < bestMatch.distanceKm ||
      (distanceKm === bestMatch.distanceKm &&
        administrativePopulation.population >
          bestMatch.administrativePopulation.population)
    ) {
      bestMatch = {
        administrativePopulation,
        distanceKm,
      };
    }
  }

  return bestMatch?.administrativePopulation ?? null;
}

/**
 * Inserts a GeoNames candidate into a country's population-sorted candidate
 * collection while limiting memory usage.
 */
function addGeoNamesCandidate(
  candidates: GeoNamesTown[],
  town: GeoNamesTown,
): void {
  candidates.push(town);

  /*
   * Sorting only when the temporary candidate array grows past the configured
   * capacity avoids storing every GeoNames settlement worldwide.
   */
  if (candidates.length > GEONAMES_CANDIDATE_COUNT * 2) {
    candidates.sort(
      (first, second) => second.population - first.population,
    );

    candidates.length = GEONAMES_CANDIDATE_COUNT;
  }
}

/**
 * Reads GeoNames in two streaming passes while retaining only bounded quiz
 * candidate collections and a compact spatial index of populated
 * administrative records.
 *
 * Pass 1 keeps the normal positive-population populated places and indexes
 * positive-population administrative records. Pass 2 revisits only explicit
 * zero-population populated places and allows one to borrow population when a
 * nearby same-country administrative record has an exact normalized name in
 * common.
 *
 * This preserves GeoNames populated-place identity while recovering important
 * settlements whose population is stored only on an administrative record,
 * such as El Alto. Administrative records never become quiz towns directly.
 */
async function readGeoNamesCandidates(
  countryIdMap: Map<string, string>,
): Promise<Map<string, GeoNamesTown[]>> {
  const candidatesByCountry = new Map<string, GeoNamesTown[]>();

  const administrativePopulationIndex = new Map<
    string,
    GeoNamesAdministrativePopulation[]
  >();

  const firstPassStream = fs.createReadStream(GEONAMES_PATH, {
    encoding: "utf8",
  });

  const firstPassReader = readline.createInterface({
    input: firstPassStream,
    crlfDelay: Infinity,
  });

  let firstPassLinesRead = 0;
  let retainedAdministrativePopulations = 0;

  for await (const line of firstPassReader) {
    firstPassLinesRead += 1;

    const columns = line.split("\t");

    const town = parseGeoNamesTown(columns);

    if (town && countryIdMap.has(town.countryCode)) {
      let candidates = candidatesByCountry.get(town.countryCode);

      if (!candidates) {
        candidates = [];
        candidatesByCountry.set(town.countryCode, candidates);
      }

      addGeoNamesCandidate(candidates, town);
    }

    const administrativePopulation =
      parseGeoNamesAdministrativePopulation(columns);

    if (
      administrativePopulation &&
      countryIdMap.has(administrativePopulation.countryCode)
    ) {
      addAdministrativePopulation(
        administrativePopulationIndex,
        administrativePopulation,
      );

      retainedAdministrativePopulations += 1;
    }

    if (firstPassLinesRead % 1_000_000 === 0) {
      console.log(
        `GeoNames pass 1: read ${firstPassLinesRead.toLocaleString()} records...`,
      );
    }
  }

  console.log(
    `GeoNames pass 1 complete: ${firstPassLinesRead.toLocaleString()} records read; ${retainedAdministrativePopulations.toLocaleString()} populated administrative records indexed.`,
  );

  const secondPassStream = fs.createReadStream(GEONAMES_PATH, {
    encoding: "utf8",
  });

  const secondPassReader = readline.createInterface({
    input: secondPassStream,
    crlfDelay: Infinity,
  });

  let secondPassLinesRead = 0;
  let rescuedPopulationCount = 0;

  for await (const line of secondPassReader) {
    secondPassLinesRead += 1;

    const columns = line.split("\t");

    const zeroPopulationTown =
      parseZeroPopulationGeoNamesTown(columns);

    if (
      !zeroPopulationTown ||
      !countryIdMap.has(zeroPopulationTown.countryCode)
    ) {
      if (secondPassLinesRead % 1_000_000 === 0) {
        console.log(
          `GeoNames pass 2: read ${secondPassLinesRead.toLocaleString()} records...`,
        );
      }

      continue;
    }

    const administrativePopulation =
      findAdministrativePopulationFallback(
        zeroPopulationTown,
        administrativePopulationIndex,
      );

    if (administrativePopulation) {
      const rescuedTown: GeoNamesTown = {
        ...zeroPopulationTown,
        population: administrativePopulation.population,
      };

      let candidates = candidatesByCountry.get(
        rescuedTown.countryCode,
      );

      if (!candidates) {
        candidates = [];
        candidatesByCountry.set(rescuedTown.countryCode, candidates);
      }

      addGeoNamesCandidate(candidates, rescuedTown);
      rescuedPopulationCount += 1;
    }

    if (secondPassLinesRead % 1_000_000 === 0) {
      console.log(
        `GeoNames pass 2: read ${secondPassLinesRead.toLocaleString()} records...`,
      );
    }
  }

  /*
   * Final population ordering and truncation after both passes finish ensures
   * rescued settlements compete normally with positive-population candidates.
   */
  for (const candidates of candidatesByCountry.values()) {
    candidates.sort(
      (first, second) => second.population - first.population,
    );

    candidates.length = Math.min(
      candidates.length,
      GEONAMES_CANDIDATE_COUNT,
    );
  }

  console.log(
    `GeoNames pass 2 complete: ${secondPassLinesRead.toLocaleString()} records read; ${rescuedPopulationCount.toLocaleString()} zero-population populated places rescued.`,
  );

  return candidatesByCountry;
}

/* -------------------------------------------------------------------------- */
/* OSM towns.geojson                                                          */
/* -------------------------------------------------------------------------- */

/**
 * Streams GeoPedia's processed worldwide OSM settlement GeoJSON directly into
 * a lightweight spatial index.
 *
 * The source file is intentionally never loaded into memory as one string or
 * retained as one giant settlement array. Each valid settlement is parsed,
 * converted to the compact representation required by town-quiz matching, and
 * immediately inserted into its geographic lookup bucket.
 *
 * Retained fields:
 *
 * - stable OSM ID
 * - settlement name
 * - OSM place classification
 * - latitude
 * - longitude
 *
 * Building the spatial index during streaming avoids simultaneously retaining
 * both millions of OSM settlement objects and a second world-scale collection
 * used only for lookup.
 *
 * @returns OSM settlements grouped into geographic lookup cells.
 */
async function readOsmTownSpatialIndex(): Promise<
  Map<string, OsmTown[]>
> {
  console.log(`Reading ${OSM_TOWNS_PATH}...`);

  const index = new Map<string, OsmTown[]>();

  const pipeline = fs
    .createReadStream(OSM_TOWNS_PATH)
    .pipe(parser.asStream())
    .pipe(
      pick.asStream({
        filter: "features",
      }),
    )
    .pipe(streamArray.asStream());

  let processedFeatures = 0;
  let retainedSettlements = 0;

  for await (const item of pipeline as unknown as AsyncIterable<
    StreamArrayItem<OsmTownFeature>
  >) {
    processedFeatures += 1;

    const feature = item.value;

    if (feature.geometry?.type !== "Point") {
      continue;
    }

    const osmId = feature.properties?.osmId;

    const name = feature.properties?.name;

    const englishNameValue = feature.properties?.englishName;

    const englishName =
      typeof englishNameValue === "string"
        ? englishNameValue.trim() || undefined
        : undefined;

    const place = feature.properties?.place;

    if (
      typeof osmId !== "string" ||
      typeof name !== "string" ||
      typeof place !== "string"
    ) {
      continue;
    }

    if (!INDEXED_OSM_PLACE_TYPES.has(place as SettlementPlaceType)) {
      continue;
    }

    const coordinates = feature.geometry.coordinates;

    if (!Array.isArray(coordinates) || coordinates.length < 2) {
      continue;
    }

    const longitude = coordinates[0];

    const latitude = coordinates[1];

    if (
      typeof longitude !== "number" ||
      typeof latitude !== "number" ||
      !Number.isFinite(longitude) ||
      !Number.isFinite(latitude)
    ) {
      continue;
    }

    const town: OsmTown = {
      osmId,

      name,
      englishName,

      place: place as SettlementPlaceType,

      latitude,
      longitude,
    };

    const key = getSpatialCellKey(town.latitude, town.longitude);

    const bucket = index.get(key);

    if (bucket) {
      bucket.push(town);
    } else {
      index.set(key, [town]);
    }

    retainedSettlements += 1;

    if (processedFeatures % 250_000 === 0) {
      console.log(
        `Read ${processedFeatures.toLocaleString()} OSM settlement features...`,
      );
    }
  }

  console.log(
    `Loaded ${retainedSettlements.toLocaleString()} OSM settlement features into ${index.size.toLocaleString()} spatial-index cells.`,
  );

  return index;
}

/* -------------------------------------------------------------------------- */
/* OSM spatial index                                                          */
/* -------------------------------------------------------------------------- */

/**
 * Size of one geographic lookup cell in degrees.
 *
 * 0.1° is roughly 11 km latitude and is sufficiently small for our matching
 * radii while keeping lookup operations inexpensive.
 */
const SPATIAL_CELL_SIZE = 0.1;

/**
 * Creates a spatial-grid key.
 */
function getSpatialCellKey(
  latitude: number,
  longitude: number,
): string {
  const latitudeCell = Math.floor(latitude / SPATIAL_CELL_SIZE);

  const longitudeCell = Math.floor(longitude / SPATIAL_CELL_SIZE);

  return `${latitudeCell}:${longitudeCell}`;
}

/**
 * Returns OSM settlements in the candidate's cell and surrounding cells.
 */
function getNearbyOsmTowns(
  town: GeoNamesTown,
  index: Map<string, OsmTown[]>,
): OsmTown[] {
  const latitudeCell = Math.floor(town.latitude / SPATIAL_CELL_SIZE);

  const longitudeCell = Math.floor(
    town.longitude / SPATIAL_CELL_SIZE,
  );

  const nearby: OsmTown[] = [];

  /*
   * A 5x5 window safely covers the matching radii even at cell edges.
   */
  for (
    let latitudeOffset = -2;
    latitudeOffset <= 2;
    latitudeOffset += 1
  ) {
    for (
      let longitudeOffset = -2;
      longitudeOffset <= 2;
      longitudeOffset += 1
    ) {
      const key = `${latitudeCell + latitudeOffset}:${
        longitudeCell + longitudeOffset
      }`;

      const bucket = index.get(key);

      if (bucket) {
        nearby.push(...bucket);
      }
    }
  }

  return nearby;
}

/* -------------------------------------------------------------------------- */
/* GeoNames ↔ OSM matching                                                    */
/* -------------------------------------------------------------------------- */

/**
 * Determines how strongly a GeoNames settlement name matches an OSM
 * settlement.
 *
 * OSM's primary/local name and explicit English name are evaluated separately.
 * A GeoNames alternate name matching OSM's explicit English name is stronger
 * evidence than an alternate name matching only OSM's local name.
 */
function getGeoNamesNameMatchType(
  town: GeoNamesTown,
  osmTown: OsmTown,
): NameMatchType {
  const normalizedOsmName = normalizeTownName(osmTown.name);

  const normalizedOsmEnglishName = osmTown.englishName
    ? normalizeTownName(osmTown.englishName)
    : null;

  const normalizedGeoNamesPrimary = normalizeTownName(town.name);

  if (
    normalizedGeoNamesPrimary === normalizedOsmName ||
    normalizedGeoNamesPrimary === normalizedOsmEnglishName
  ) {
    return "primary";
  }

  if (town.asciiName) {
    const normalizedAsciiName = normalizeTownName(town.asciiName);

    if (
      normalizedAsciiName === normalizedOsmName ||
      normalizedAsciiName === normalizedOsmEnglishName
    ) {
      return "ascii";
    }
  }

  for (const alternateName of town.alternateNames) {
    const normalizedAlternateName = normalizeTownName(alternateName);

    /*
     * An explicit OSM English-name match is a strong cross-dataset identity
     * signal even when GeoNames stores that English spelling as an alternate.
     */
    if (
      normalizedOsmEnglishName &&
      normalizedAlternateName === normalizedOsmEnglishName
    ) {
      return "alternateEnglish";
    }

    if (normalizedAlternateName === normalizedOsmName) {
      return "alternate";
    }
  }

  return null;
}

/**
 * Returns the priority of one GeoNames name-match type.
 *
 * Lower values represent stronger identity signals.
 */
function getNameMatchPriority(
  matchType: Exclude<NameMatchType, null>,
): number {
  switch (matchType) {
    case "primary":
      return 0;

    case "ascii":
      return 1;

    case "alternateEnglish":
      return 2;

    case "alternate":
      return 3;
  }
}

/**
 * Finds the best OSM settlement corresponding to one GeoNames settlement while
 * considering only the requested OSM place classifications.
 *
 * Restricting place types at matching time allows primary city/town matching to
 * remain identical to the original generator while smaller villages can be
 * considered independently as supplemental quiz settlements.
 *
 * @param geoNamesTown - GeoNames settlement being matched.
 * @param osmIndex - Worldwide OSM settlement spatial index.
 * @param allowedPlaceTypes - OSM classifications eligible for this match.
 * @returns Best compatible OSM settlement, or `null` when none can be matched.
 */
function matchGeoNamesTownToOsm(
  geoNamesTown: GeoNamesTown,
  osmIndex: Map<string, OsmTown[]>,
  allowedPlaceTypes: ReadonlySet<SettlementPlaceType>,
): MatchedTown | null {
  const nearbyOsmTowns = getNearbyOsmTowns(geoNamesTown, osmIndex);

  //------------------------------------------------------------------ TEST
  if (geoNamesTown.id === "2028462") {
    console.log("\n========== ULAANBAATAR OSM DIAGNOSTIC ==========");

    console.log("GEONAMES", {
      id: geoNamesTown.id,
      name: geoNamesTown.name,
      asciiName: geoNamesTown.asciiName,
      featureCode: geoNamesTown.featureCode,
      population: geoNamesTown.population,
      latitude: geoNamesTown.latitude,
      longitude: geoNamesTown.longitude,
      hasUlaanbaatarAlternateName: geoNamesTown.alternateNames.some(
        (name) =>
          normalizeTownName(name) ===
          normalizeTownName("Ulaanbaatar"),
      ),
    });

    console.log(
      "NEARBY OSM SETTLEMENTS",
      nearbyOsmTowns
        .filter((town) => PRIMARY_OSM_PLACE_TYPES.has(town.place))
        .map((town) => ({
          name: town.name,
          englishName: town.englishName,
          place: town.place,
          latitude: town.latitude,
          longitude: town.longitude,
          distanceKm: getDistanceKm(
            geoNamesTown.latitude,
            geoNamesTown.longitude,
            town.latitude,
            town.longitude,
          ),
        }))
        .sort((a, b) => a.distanceKm - b.distanceKm),
    );

    console.log("===============================================\n");
  }
  //------------------------------------------------------------------ TEST

  let bestNameMatch:
    | {
        town: OsmTown;
        distanceKm: number;
        nameMatchType: Exclude<NameMatchType, null>;
      }
    | undefined;

  let bestCoordinateMatch:
    | {
        town: OsmTown;
        distanceKm: number;
      }
    | undefined;

  for (const osmTown of nearbyOsmTowns) {
    if (!allowedPlaceTypes.has(osmTown.place)) {
      continue;
    }

    const distanceKm = getDistanceKm(
      geoNamesTown.latitude,
      geoNamesTown.longitude,

      osmTown.latitude,
      osmTown.longitude,
    );

    const nameMatchType = getGeoNamesNameMatchType(
      geoNamesTown,
      osmTown,
    );

    /*
     * Primary and ASCII matches are strong identity signals and may tolerate
     * larger coordinate differences between GeoNames and OSM.
     *
     * Alternate-name matches use a much tighter distance threshold because
     * GeoNames alternate-name lists may also contain names associated with nearby
     * or administratively related places.
     */
    let nameMatchMaxDistanceKm: number | null = null;

    if (
      nameMatchType === "primary" ||
      nameMatchType === "ascii" ||
      nameMatchType === "alternateEnglish"
    ) {
      nameMatchMaxDistanceKm = PRIMARY_NAME_MATCH_MAX_DISTANCE_KM;
    } else if (nameMatchType === "alternate") {
      nameMatchMaxDistanceKm = ALTERNATE_NAME_MATCH_MAX_DISTANCE_KM;
    }

    if (
      nameMatchType !== null &&
      nameMatchMaxDistanceKm !== null &&
      distanceKm <= nameMatchMaxDistanceKm
    ) {
      const nonNullNameMatchType: Exclude<NameMatchType, null> =
        nameMatchType;

      if (
        !bestNameMatch ||
        getNameMatchPriority(nonNullNameMatchType) <
          getNameMatchPriority(bestNameMatch.nameMatchType) ||
        (getNameMatchPriority(nonNullNameMatchType) ===
          getNameMatchPriority(bestNameMatch.nameMatchType) &&
          distanceKm < bestNameMatch.distanceKm)
      ) {
        bestNameMatch = {
          town: osmTown,
          distanceKm,
          nameMatchType: nonNullNameMatchType,
        };
      }

      continue;
    }

    if (distanceKm <= COORDINATE_ONLY_MATCH_MAX_DISTANCE_KM) {
      if (
        !bestCoordinateMatch ||
        distanceKm < bestCoordinateMatch.distanceKm
      ) {
        bestCoordinateMatch = {
          town: osmTown,
          distanceKm,
        };
      }
    }
  }

  if (bestNameMatch) {
    return {
      geoNamesTown,

      osmTown: bestNameMatch.town,

      matchType: "name",

      nameMatchType: bestNameMatch.nameMatchType,

      distanceKm: bestNameMatch.distanceKm,
    };
  }

  if (bestCoordinateMatch) {
    return {
      geoNamesTown,

      osmTown: bestCoordinateMatch.town,

      matchType: "coordinates",

      nameMatchType: null,

      distanceKm: bestCoordinateMatch.distanceKm,
    };
  }

  return null;
}

/* -------------------------------------------------------------------------- */
/* Country generation                                                         */
/* -------------------------------------------------------------------------- */

/**
 * Returns which matched town should be preferred when multiple GeoNames
 * records resolve to the same underlying OSM settlement.
 *
 * Name-field quality is the strongest signal. Name-based matches are preferred
 * over coordinate-only matches, followed by geographic proximity, population,
 * and finally GeoNames ID for deterministic generation.
 */
function compareDuplicateOsmMatches(
  first: MatchedTown,
  second: MatchedTown,
): number {
  const getMatchPriority = (match: MatchedTown): number => {
    if (match.nameMatchType === "primary") {
      return 0;
    }

    if (match.nameMatchType === "ascii") {
      return 1;
    }

    if (match.nameMatchType === "alternateEnglish") {
      return 2;
    }

    if (match.nameMatchType === "alternate") {
      return 3;
    }

    return 4;
  };

  const priorityDifference =
    getMatchPriority(first) - getMatchPriority(second);

  if (priorityDifference !== 0) {
    return priorityDifference;
  }

  const distanceDifference = first.distanceKm - second.distanceKm;

  if (distanceDifference !== 0) {
    return distanceDifference;
  }

  const populationDifference =
    second.geoNamesTown.population - first.geoNamesTown.population;

  if (populationDifference !== 0) {
    return populationDifference;
  }

  return first.geoNamesTown.id.localeCompare(second.geoNamesTown.id);
}

/**
 * Removes duplicate GeoNames representations that matched the same OSM
 * settlement.
 *
 * Each OSM settlement may contribute at most one town to a country's quiz
 * dataset.
 */
function deduplicateOsmMatches(
  matchedTowns: MatchedTown[],
): MatchedTown[] {
  const matchesByOsmId = new Map<string, MatchedTown[]>();

  for (const match of matchedTowns) {
    const osmId = match.osmTown.osmId;

    const existing = matchesByOsmId.get(osmId);

    if (existing) {
      existing.push(match);
    } else {
      matchesByOsmId.set(osmId, [match]);
    }
  }

  return Array.from(matchesByOsmId.values()).map((matches) => {
    matches.sort(compareDuplicateOsmMatches);

    return matches[0];
  });
}

/**
 * Normalizes a settlement name for determining whether two rendered names
 * represent the same practical quiz label.
 *
 * The comparison ignores:
 *
 * - capitalization
 * - accents and diacritics
 * - punctuation
 * - hyphen-versus-space differences
 * - repeated whitespace
 *
 * Unlike `normalizeTownName`, spaces are retained here because later display
 * rules need to distinguish an optional `City` suffix from the underlying town
 * name.
 *
 * @param value - Settlement name to normalize.
 * @returns Comparable display-name representation.
 */
function normalizeDisplayNameForComparison(value: string): string {
  return value
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "")
    .toLocaleLowerCase()
    .replace(/[^\p{Letter}\p{Number}]+/gu, " ")
    .trim()
    .replace(/\s+/g, " ");
}

/**
 * Returns the normalized town name with one trailing `City` suffix removed.
 *
 * The suffix rule is intentionally narrow. Words such as `Town`,
 * `Municipality`, and `Village` are not treated as optional because doing so
 * would introduce much broader semantic assumptions.
 *
 * @param value - Already normalized display name.
 * @returns Name without a trailing `city` token.
 */
function removeOptionalCitySuffix(value: string): string {
  return value.replace(/\s+city$/u, "");
}

/**
 * Determines whether two settlement names differ only in presentation or by an
 * optional English `City` suffix.
 *
 * Examples treated as equivalent:
 *
 * - `Bacău` / `Bacau`
 * - `Thetford-Mines` / `Thetford Mines`
 * - `Ise-Ekiti` / `Ise - Ekiti`
 * - `Zacatecas` / `Zacatecas City`
 *
 * Genuine translated names such as `Wien` / `Vienna` and
 * `Ciudad de México` / `Mexico City` remain distinct.
 *
 * @param firstName - First settlement name.
 * @param secondName - Second settlement name.
 * @returns Whether only one quiz label should be retained.
 */
function areDisplayNamesEquivalent(
  firstName: string,
  secondName: string,
): boolean {
  const firstNormalized =
    normalizeDisplayNameForComparison(firstName);

  const secondNormalized =
    normalizeDisplayNameForComparison(secondName);

  if (firstNormalized === secondNormalized) {
    return true;
  }

  return (
    removeOptionalCitySuffix(firstNormalized) ===
    removeOptionalCitySuffix(secondNormalized)
  );
}

/**
 * Counts visible diacritic marks in a settlement name.
 *
 * This provides a small preference signal when two names are otherwise
 * equivalent. Native spellings such as `Bacău` are preferred over ASCII-only
 * equivalents such as `Bacau`.
 *
 * @param value - Settlement name to inspect.
 * @returns Number of decomposed Unicode diacritic marks.
 */
function countDiacritics(value: string): number {
  return value.normalize("NFD").match(/\p{Diacritic}/gu)?.length ?? 0;
}

/**
 * Removes hyphen-like separators from an equivalent display name.
 *
 * This cleanup is used only after two independent source names have established
 * that the spelling is equivalent. It therefore converts cases such as
 * `Thetford-Mines` / `Thetford Mines` to the cleaner `Thetford Mines` without
 * globally rewriting every hyphenated OSM settlement name.
 *
 * @param value - Preferred equivalent source name.
 * @returns Cleaned single quiz label.
 */
function normalizeEquivalentNameSeparators(value: string): string {
  return value
    .replace(/\s*[-‐-‒–—]\s*/gu, " ")
    .trim()
    .replace(/\s+/g, " ");
}

/**
 * Chooses which source spelling should represent two equivalent settlement
 * names.
 *
 * Rules:
 *
 * 1. When the only semantic difference is an optional `City` suffix, prefer
 *    OSM's primary/local name. This preserves names such as `Davao City` while
 *    avoiding English-only expansions such as `Zacatecas City`.
 * 2. Otherwise prefer the spelling containing more native diacritics.
 * 3. Ties prefer OSM's primary/local name.
 * 4. Equivalent hyphen/space formatting is rendered with spaces.
 *
 * @param nativeName - Primary locally used OSM name.
 * @param englishName - Explicit English/international name.
 * @returns Preferred single quiz label.
 */
function choosePreferredEquivalentName(
  nativeName: string,
  englishName: string,
): string {
  const normalizedNative =
    normalizeDisplayNameForComparison(nativeName);

  const normalizedEnglish =
    normalizeDisplayNameForComparison(englishName);

  const nativeWithoutCity =
    removeOptionalCitySuffix(normalizedNative);

  const englishWithoutCity =
    removeOptionalCitySuffix(normalizedEnglish);

  const differsOnlyByCitySuffix =
    normalizedNative !== normalizedEnglish &&
    nativeWithoutCity === englishWithoutCity;

  if (differsOnlyByCitySuffix) {
    return normalizeEquivalentNameSeparators(nativeName);
  }

  const nativeDiacritics = countDiacritics(nativeName);

  const englishDiacritics = countDiacritics(englishName);

  const preferredName =
    englishDiacritics > nativeDiacritics ? englishName : nativeName;

  return normalizeEquivalentNameSeparators(preferredName);
}

/**
 * Resolves the final names stored for one runtime town-quiz question.
 *
 * Equivalent native and English names collapse into one preferred `name`.
 * Genuine translations remain two labels, with the English/international name
 * stored as `name` and the local OSM name stored as `nativeName`.
 *
 * @param match - Matched GeoNames and OSM settlement.
 * @returns Final quiz name and optional distinct native name.
 */
function getQuizNames(
  match: MatchedTown,
): Pick<TownQuizTown, "name" | "nativeName"> {
  const nativeName = match.osmTown.name.trim();

  const englishName =
    match.osmTown.englishName?.trim() ||
    match.geoNamesTown.name.trim();

  if (
    nativeName &&
    areDisplayNamesEquivalent(nativeName, englishName)
  ) {
    return {
      name: choosePreferredEquivalentName(nativeName, englishName),
    };
  }

  return {
    name: englishName,

    ...(nativeName
      ? {
          nativeName,
        }
      : {}),
  };
}

/**
 * Produces the final runtime dataset for one country.
 */
function createCountryTownData(
  countryId: string,
  candidates: GeoNamesTown[],
  osmIndex: Map<string, OsmTown[]>,
): {
  data: TownQuizData;

  matchedTowns: MatchedTown[];
} {
  const primaryMatches: MatchedTown[] = [];

  const supplementalMatches: MatchedTown[] = [];

  for (const candidate of candidates) {
    /*
     * Preserve GeoPedia's existing city/town matching first. Supplemental
     * settlements must never replace an available primary match for the same
     * GeoNames record.
     */
    const primaryMatch = matchGeoNamesTownToOsm(
      candidate,
      osmIndex,
      PRIMARY_OSM_PLACE_TYPES,
    );

    if (primaryMatch) {
      primaryMatches.push(primaryMatch);

      continue;
    }

    /*
     * Only GeoNames records that could not resolve to a primary OSM city/town are
     * considered for the supplemental village pool.
     */
    const supplementalMatch = matchGeoNamesTownToOsm(
      candidate,
      osmIndex,
      SUPPLEMENTAL_OSM_PLACE_TYPES,
    );

    if (supplementalMatch) {
      supplementalMatches.push(supplementalMatch);
    }
  }

  const matchedTowns = [...primaryMatches, ...supplementalMatches];

  const deduplicatedPrimaryTowns =
    deduplicateOsmMatches(primaryMatches);

  const deduplicatedSupplementalTowns = deduplicateOsmMatches(
    supplementalMatches,
  );

  /**
   * Population remains the ranking signal within each settlement tier.
   */
  function compareMatchedTownPopulation(
    first: MatchedTown,
    second: MatchedTown,
  ): number {
    const populationDifference =
      second.geoNamesTown.population - first.geoNamesTown.population;

    if (populationDifference !== 0) {
      return populationDifference;
    }

    return first.geoNamesTown.id.localeCompare(
      second.geoNamesTown.id,
    );
  }

  deduplicatedPrimaryTowns.sort(compareMatchedTownPopulation);

  deduplicatedSupplementalTowns.sort(compareMatchedTownPopulation);

  /*
   * Preserve every eligible primary city/town up to the quiz limit before
   * supplementing the dataset with smaller OSM villages.
   *
   * This keeps existing town-quiz membership stable while allowing countries
   * with relatively few OSM cities/towns to gain substantially deeper coverage.
   */
  let selectedMatches = deduplicatedPrimaryTowns.slice(
    0,
    MAX_TOWN_COUNT,
  );

  const supplementalCapacity =
    MAX_TOWN_COUNT - selectedMatches.length;

  if (supplementalCapacity > 0) {
    selectedMatches.push(
      ...deduplicatedSupplementalTowns.slice(0, supplementalCapacity),
    );
  }

  /*
   * National capitals and seats of government should always remain available
   * even when unusual source classification or population causes the capital
   * to fall outside the normal 300-settlement selection.
   */
  const capitalMatch = matchedTowns.find((match) =>
    CAPITAL_GEONAMES_FEATURE_CODES.has(
      match.geoNamesTown.featureCode,
    ),
  );

  if (
    capitalMatch &&
    !selectedMatches.some(
      (match) =>
        match.geoNamesTown.id === capitalMatch.geoNamesTown.id,
    )
  ) {
    selectedMatches = [
      ...selectedMatches.slice(0, MAX_TOWN_COUNT - 1),
      capitalMatch,
    ];
  }

  selectedMatches.sort(compareMatchedTownPopulation);

  const rankedTowns = selectedMatches.map(
    (match, index): TownQuizTown => {
      const names = getQuizNames(match);

      return {
        id: match.geoNamesTown.id,

        ...names,

        latitude: match.geoNamesTown.latitude,

        longitude: match.geoNamesTown.longitude,

        population: match.geoNamesTown.population,

        populationRank: index + 1,

        isCapital: CAPITAL_GEONAMES_FEATURE_CODES.has(
          match.geoNamesTown.featureCode,
        ),
      };
    },
  );

  /*
   * Keep at most 300 records.
   */
  const retainedTowns = rankedTowns.slice(0, MAX_TOWN_COUNT);

  return {
    data: {
      towns: retainedTowns,
    },

    matchedTowns,
  };
}

/**
 * Writes one runtime town file.
 */
function writeCountryTownData(
  countryId: string,
  data: TownQuizData,
): void {
  const outputPath = path.join(OUTPUT_DIRECTORY, `${countryId}.json`);

  fs.writeFileSync(
    outputPath,

    `${JSON.stringify(data, null, 2)}\n`,

    "utf8",
  );
}

/* -------------------------------------------------------------------------- */
/* Main                                                                       */
/* -------------------------------------------------------------------------- */

async function main(): Promise<void> {
  if (!fs.existsSync(GEONAMES_PATH)) {
    throw new Error(
      `GeoNames source does not exist: ${GEONAMES_PATH}`,
    );
  }

  if (!fs.existsSync(OSM_TOWNS_PATH)) {
    throw new Error(
      `OSM towns GeoJSON does not exist: ${OSM_TOWNS_PATH}`,
    );
  }

  if (!fs.existsSync(WORLD_COUNTRIES_PATH)) {
    throw new Error(
      `World countries GeoJSON does not exist: ${WORLD_COUNTRIES_PATH}`,
    );
  }

  fs.mkdirSync(OUTPUT_DIRECTORY, {
    recursive: true,
  });

  /**
   * Removes town datasets produced by previous generator runs.
   *
   * Generation is authoritative, so leaving an old country file behind when that
   * country no longer produces valid towns would create stale runtime data.
   */
  for (const fileName of fs.readdirSync(OUTPUT_DIRECTORY)) {
    if (!fileName.endsWith(".json")) {
      continue;
    }

    fs.unlinkSync(path.join(OUTPUT_DIRECTORY, fileName));
  }

  const countryIdMap = loadCountryIdMap();

  console.log(
    `Loaded ${countryIdMap.size.toLocaleString()} GeoPedia country IDs.`,
  );

  console.log("");

  /*
   * GeoNames is processed first so only the largest candidate towns are retained
   * in memory. The reader performs a second streaming pass to recover
   * zero-population populated places whose population exists only on a nearby
   * matching administrative record.
   */
  const candidatesByCountry =
    await readGeoNamesCandidates(countryIdMap);

  console.log("");

  const osmIndex = await readOsmTownSpatialIndex();

  console.log(
    `Built ${osmIndex.size.toLocaleString()} OSM spatial-index cells.`,
  );

  console.log("");

  const stats: CountryGenerationStats[] = [];

  for (const [countryCode, candidates] of candidatesByCountry) {
    const countryId = countryIdMap.get(countryCode);

    if (!countryId) {
      continue;
    }

    const { data, matchedTowns } = createCountryTownData(
      countryId,
      candidates,
      osmIndex,
    );

    if (data.towns.length === 0) {
      continue;
    }

    writeCountryTownData(countryId, data);

    const nameMatches = matchedTowns.filter(
      (match) => match.matchType === "name",
    ).length;

    const coordinateMatches = matchedTowns.filter(
      (match) => match.matchType === "coordinates",
    ).length;

    stats.push({
      countryCode,

      countryId,

      geoNamesCandidates: candidates.length,

      matchedCitiesAndTowns: matchedTowns.filter((match) =>
        PRIMARY_OSM_PLACE_TYPES.has(match.osmTown.place),
      ).length,

      matchedVillages: matchedTowns.filter((match) =>
        SUPPLEMENTAL_OSM_PLACE_TYPES.has(match.osmTown.place),
      ).length,

      nameMatches,

      coordinateMatches,

      generatedTowns: data.towns.length,
    });
  }

  stats.sort((first, second) =>
    first.countryId.localeCompare(second.countryId),
  );

  console.log("TOWN QUIZ DATA GENERATION COMPLETE");

  console.log("----------------------------------");

  console.table(stats);

  const incompleteCountries = stats.filter(
    (country) => country.generatedTowns < MAX_TOWN_COUNT,
  );

  console.log("");

  console.log(
    `Countries generated: ${stats.length.toLocaleString()}`,
  );

  console.log(
    `Countries with fewer than ${MAX_TOWN_COUNT} towns: ${incompleteCountries.length.toLocaleString()}`,
  );

  if (incompleteCountries.length > 0) {
    console.log("");

    console.log(`COUNTRIES BELOW ${MAX_TOWN_COUNT} TOWNS`);

    console.log("-------------------------");

    console.table(
      incompleteCountries.map((country) => ({
        country: country.countryId,

        towns: country.generatedTowns,

        citiesAndTowns: country.matchedCitiesAndTowns,

        villages: country.matchedVillages,

        candidates: country.geoNamesCandidates,
      })),
    );
  }

  console.log("");

  console.log(`Output directory: ${OUTPUT_DIRECTORY}`);
}

main().catch((error: unknown) => {
  console.error(error);

  process.exitCode = 1;
});
