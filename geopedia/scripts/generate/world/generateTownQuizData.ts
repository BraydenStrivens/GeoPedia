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
 * Only settlements classified by OSM as `city` or `town` are accepted into
 * town quizzes.
 *
 * Source files:
 *
 *   data/raw/towns/allCountries.txt
 *   public/data/geojson/world/towns.geojson
 *   public/data/geojson/world/world-countries.geojson
 *
 * Output:
 *
 *   public/data/towns/{countryId}.json
 *
 * Example:
 *
 *   public/data/towns/usa.json
 *   public/data/towns/fra.json
 *   public/data/towns/jpn.json
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

const GEONAMES_PATH = "data/raw/towns/allCountries.txt";

const OSM_TOWNS_PATH = "public/data/geojson/world/towns.geojson";

const WORLD_COUNTRIES_PATH =
  "public/data/geojson/world/world-countries.geojson";

const OUTPUT_DIRECTORY = "public/data/towns";

/* -------------------------------------------------------------------------- */
/* Generation settings                                                        */
/* -------------------------------------------------------------------------- */

/**
 * Maximum number of towns stored for one country.
 */
const MAX_TOWN_COUNT = 200;

/**
 * We initially retain considerably more GeoNames candidates than the final
 * runtime count.
 *
 * Some GeoNames records will fail the OSM classification join because they are
 * suburbs, neighborhoods, villages, duplicate places, or otherwise unsuitable.
 *
 * Keeping 1,000 candidates gives the matching stage enough room to still find
 * 200 valid city/town records for most countries.
 */
const GEONAMES_CANDIDATE_COUNT = 1_000;

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
 * OSM place classifications allowed in town quizzes.
 *
 * Suburbs, villages, hamlets, and isolated dwellings are deliberately omitted.
 */
const INCLUDED_OSM_PLACE_TYPES = new Set(["city", "town"]);

/**
 * GeoNames populated-place feature codes worth considering.
 *
 * The OSM classification is ultimately responsible for deciding whether the
 * record represents a city/town rather than a suburb or subordinate place.
 */
const INCLUDED_GEONAMES_FEATURE_CODES = new Set([
  "PPL",
  "PPLA",
  "PPLA2",
  "PPLA3",
  "PPLA4",
  "PPLC",
]);

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

  name: string;

  latinName?: string;

  place: SettlementPlaceType;

  latitude: number;
  longitude: number;
};

type NameMatchType = "primary" | "ascii" | "alternate" | null;

type MatchedTown = {
  geoNamesTown: GeoNamesTown;

  osmTown: OsmTown;

  matchType: "name" | "coordinates";

  nameMatchType: NameMatchType;

  distanceKm: number;
};

type TownQuizTown = {
  id: string;

  name: string;

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
    latinName?: unknown;
    place?: unknown;
  };
};

type CountryGenerationStats = {
  countryCode: string;

  countryId: string;

  geoNamesCandidates: number;

  matchedCitiesAndTowns: number;

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
 * It does not attempt fuzzy spelling correction.
 */
function normalizeTownName(value: string): string {
  return value
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "");
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
 * Parses one GeoNames populated-place row.
 */
function parseGeoNamesTown(line: string): GeoNamesTown | null {
  const columns = line.split("\t");

  if (columns[GEONAMES_COLUMNS.featureClass] !== "P") {
    return null;
  }

  const featureCode = columns[GEONAMES_COLUMNS.featureCode];

  if (!INCLUDED_GEONAMES_FEATURE_CODES.has(featureCode)) {
    return null;
  }

  const population = parsePopulation(
    columns[GEONAMES_COLUMNS.population],
  );

  if (population === null) {
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

  const alternateNamesRaw =
    columns[GEONAMES_COLUMNS.alternateNames] ?? "";

  const alternateNames = alternateNamesRaw
    .split(",")
    .map((alternateName) => alternateName.trim())
    .filter(Boolean);

  return {
    id,

    name,
    asciiName,

    alternateNames,

    latitude,
    longitude,

    featureCode,

    countryCode,

    population,
  };
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
 * Reads GeoNames and keeps only the largest candidate settlements per country.
 */
async function readGeoNamesCandidates(
  countryIdMap: Map<string, string>,
): Promise<Map<string, GeoNamesTown[]>> {
  const candidatesByCountry = new Map<string, GeoNamesTown[]>();

  const inputStream = fs.createReadStream(GEONAMES_PATH, {
    encoding: "utf8",
  });

  const reader = readline.createInterface({
    input: inputStream,

    crlfDelay: Infinity,
  });

  let linesRead = 0;

  for await (const line of reader) {
    linesRead += 1;

    const town = parseGeoNamesTown(line);

    if (!town) {
      continue;
    }

    /*
     * Ignore GeoNames entries without a corresponding GeoPedia country ID.
     */
    if (!countryIdMap.has(town.countryCode)) {
      continue;
    }

    let candidates = candidatesByCountry.get(town.countryCode);

    if (!candidates) {
      candidates = [];

      candidatesByCountry.set(town.countryCode, candidates);
    }

    addGeoNamesCandidate(candidates, town);

    if (linesRead % 1_000_000 === 0) {
      console.log(
        `Read ${linesRead.toLocaleString()} GeoNames records...`,
      );
    }
  }

  /*
   * Final population ordering and truncation after the stream finishes.
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
    `Finished reading ${linesRead.toLocaleString()} GeoNames records.`,
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

    const latinName =
      typeof feature.properties?.latinName === "string" &&
      feature.properties?.latinName.trim()
        ? feature.properties?.latinName
        : undefined;

    const place = feature.properties?.place;

    if (
      typeof osmId !== "string" ||
      typeof name !== "string" ||
      typeof place !== "string"
    ) {
      continue;
    }

    if (!INCLUDED_OSM_PLACE_TYPES.has(place)) {
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
      latinName,

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
   * A 5x5 window safely covers the 10 km matching radius even at cell edges.
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
 * Both OSM's primary name and its Latin-script companion name are considered.
 * The companion name allows settlements whose primary OSM name uses a
 * non-Latin script to match their English or international GeoNames name
 * without treating that translation as a weaker alternate-name match.
 */
function getGeoNamesNameMatchType(
  town: GeoNamesTown,
  osmTown: OsmTown,
): NameMatchType {
  const normalizedOsmNames = [osmTown.name, osmTown.latinName]
    .filter(
      (name): name is string =>
        typeof name === "string" && name.trim().length > 0,
    )
    .map(normalizeTownName);

  /*
   * The primary GeoNames name provides the strongest identity match.
   */
  if (normalizedOsmNames.includes(normalizeTownName(town.name))) {
    return "primary";
  }

  /*
   * GeoNames' ASCII name is normally a transliteration of the primary name
   * and therefore remains a strong match.
   */
  if (
    town.asciiName &&
    normalizedOsmNames.includes(normalizeTownName(town.asciiName))
  ) {
    return "ascii";
  }

  /*
   * Alternate names are useful but weaker because they can sometimes refer
   * to nearby, historical, or administratively related places.
   */
  for (const alternateName of town.alternateNames) {
    if (
      normalizedOsmNames.includes(normalizeTownName(alternateName))
    ) {
      return "alternate";
    }
  }

  return null;
}

function getNameMatchPriority(
  matchType: Exclude<NameMatchType, null>,
): number {
  switch (matchType) {
    case "primary":
      return 0;

    case "ascii":
      return 1;

    case "alternate":
      return 2;
  }
}

/**
 * Finds the best OSM settlement corresponding to one GeoNames town.
 *
 * Matching occurs in two stages:
 *
 * 1. Prefer normalized-name matches within 10 km.
 * 2. If no name match exists, allow an extremely close coordinate-only match.
 *
 * The nearest valid match always wins.
 */
function matchGeoNamesTownToOsm(
  geoNamesTown: GeoNamesTown,
  osmIndex: Map<string, OsmTown[]>,
): MatchedTown | null {
  const nearbyOsmTowns = getNearbyOsmTowns(geoNamesTown, osmIndex);

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

    if (nameMatchType === "primary" || nameMatchType === "ascii") {
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

    if (match.nameMatchType === "alternate") {
      return 2;
    }

    return 3;
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
 * Prints detailed GeoNames and OSM matching information for a small set of
 * settlements that are being manually inspected for town-quiz data quality.
 *
 * This diagnostic is intentionally based on matched towns rather than the
 * final generated town list so that both source records and the matching
 * metadata can be inspected together.
 *
 * @param countryId - GeoPedia country ID currently being generated.
 * @param matchedTowns - GeoNames settlements that successfully matched an
 * OSM settlement.
 */
function printTownQualityDiagnostics(
  countryId: string,
  matchedTowns: MatchedTown[],
): void {
  const diagnosticTownNamesByCountry: Record<string, Set<string>> = {
    jpn: new Set([
      "Ōta",
      "Aihara",
      "Nakano",
      "Minato City",
      "Chūō",
      "Sagamihara",
    ]),

    ind: new Set(["Kallakurichi", "Najafgarh"]),

    isl: new Set(["Reykjanesbær", "Keflavík"]),
  };

  const diagnosticTownNames = diagnosticTownNamesByCountry[countryId];

  if (!diagnosticTownNames) {
    return;
  }

  const diagnosticMatches = matchedTowns.filter((match) =>
    diagnosticTownNames.has(match.geoNamesTown.name),
  );

  console.log(
    `\n========== ${countryId.toUpperCase()} TOWN QUALITY DIAGNOSTIC ==========`,
  );

  for (const match of diagnosticMatches) {
    console.log({
      geoNamesId: match.geoNamesTown.id,

      geoNamesName: match.geoNamesTown.name,

      geoNamesFeatureCode: match.geoNamesTown.featureCode,

      geoNamesPopulation: match.geoNamesTown.population,

      geoNamesLatitude: match.geoNamesTown.latitude,

      geoNamesLongitude: match.geoNamesTown.longitude,

      osmId: match.osmTown.osmId,

      osmName: match.osmTown.name,

      osmPlace: match.osmTown.place,

      osmLatitude: match.osmTown.latitude,

      osmLongitude: match.osmTown.longitude,

      matchType: match.matchType,

      nameMatchType: match.nameMatchType,

      distanceKm: Number(match.distanceKm.toFixed(3)),
    });

    console.log("OSM Latin name:", match.osmTown.latinName);
  }
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
  const matchedTowns: MatchedTown[] = [];

  const sagamiharaCandidates = candidates.filter((candidate) =>
    candidate.name.toLowerCase().includes("sagamihara"),
  );

  console.log(
    "\n========== SAGAMIHARA GEONAMES CANDIDATE ==========",
  );

  console.dir(sagamiharaCandidates, {
    depth: null,
  });

  for (const candidate of candidates) {
    const match = matchGeoNamesTownToOsm(candidate, osmIndex);

    if (!match) {
      continue;
    }

    /*
     * This is the key semantic filter.
     *
     * GeoNames supplies population and country membership. OSM decides whether
     * the feature is actually classified as a city/town.
     */
    if (!INCLUDED_OSM_PLACE_TYPES.has(match.osmTown.place)) {
      continue;
    }

    matchedTowns.push(match);
  }

  printTownQualityDiagnostics(countryId, matchedTowns);

  const deduplicatedTowns = deduplicateOsmMatches(matchedTowns);

  /*
   * GeoNames candidates were already population ordered, but sorting again
   * guarantees deterministic ranking after the OSM filtering stage.
   */
  deduplicatedTowns.sort((first, second) => {
    const populationDifference =
      second.geoNamesTown.population - first.geoNamesTown.population;

    if (populationDifference !== 0) {
      return populationDifference;
    }

    return first.geoNamesTown.id.localeCompare(
      second.geoNamesTown.id,
    );
  });

  const rankedTowns = deduplicatedTowns.map(
    (match, index): TownQuizTown => ({
      id: match.geoNamesTown.id,

      name: match.geoNamesTown.name,

      latitude: match.geoNamesTown.latitude,

      longitude: match.geoNamesTown.longitude,

      population: match.geoNamesTown.population,

      populationRank: index + 1,

      isCapital: match.geoNamesTown.featureCode === "PPLC",
    }),
  );

  /*
   * Keep at most 200 records.
   */
  let retainedTowns = rankedTowns.slice(0, MAX_TOWN_COUNT);

  /*
   * National capitals should always be available for town quizzes.
   *
   * If the capital lies outside the first 200 eligible towns, replace the
   * 200th town rather than creating a 201-record dataset.
   */
  const capital = rankedTowns.find((town) => town.isCapital);

  if (
    capital &&
    !retainedTowns.some((town) => town.id === capital.id)
  ) {
    retainedTowns = [
      ...retainedTowns.slice(0, MAX_TOWN_COUNT - 1),
      capital,
    ];
  }

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
   * in memory.
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

      matchedCitiesAndTowns: matchedTowns.length,

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

    console.log("COUNTRIES BELOW 200 TOWNS");

    console.log("-------------------------");

    console.table(
      incompleteCountries.map((country) => ({
        country: country.countryId,

        towns: country.generatedTowns,

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
