/**
 * Processes GeoPedia's normalized worldwide OSM settlement NDJSON into the
 * lightweight GeoJSON used to generate runtime town-label vector tiles.
 *
 * The ranking model is significance-first:
 *
 * - Major cities derive their label zoom primarily from population and OSM
 *   settlement classification.
 * - Administrative capitals receive a useful boost without automatically
 *   outranking larger nearby cities.
 * - Villages, hamlets, suburbs, and isolated dwellings may be delayed by
 *   spatial competition.
 * - Fractional label zooms produce gradual density increases.
 *
 * The input is streamed from NDJSON so the entire raw file is never loaded as
 * one giant string.
 *
 * Spatial indexes store each processed settlement only once. This is important
 * at world scale, where the input contains millions of settlements.
 */

import fs from "node:fs";
import path from "node:path";
import readline from "node:readline";

/**
 * Worldwide settlement extraction produced by extractOsmSettlements.ts.
 */
const INPUT_PATH =
  "data/processed/towns/world-settlements.raw.ndjson";

/**
 * Lightweight intermediate GeoJSON consumed by Planetiler.
 */
const OUTPUT_PATH = "public/data/geojson/world/towns.geojson";

const TILE_SIZE = 512;

/**
 * Earliest zoom at which GeoPedia town labels may appear.
 *
 * This value was tuned against the US map so important cities begin appearing
 * shortly after broad country-level context becomes useful.
 */
const MIN_LABEL_ZOOM = 3.5;

const MAX_LABEL_ZOOM = 14;

/**
 * Spatial placement only needs half-zoom resolution.
 *
 * A deterministic fractional offset is added afterward, so labels still enter
 * progressively rather than in large half-zoom batches.
 */
const SPATIAL_ZOOM_STEP = 0.5;

/**
 * Console progress interval while reading millions of settlements.
 */
const READ_PROGRESS_INTERVAL = 250_000;

type SettlementPlaceType =
  | "city"
  | "town"
  | "village"
  | "hamlet"
  | "suburb"
  | "isolated_dwelling";

type TownMarkerType =
  "country-capital" | "admin-capital" | "major-city" | null;

/**
 * Lower values represent greater cartographic significance.
 */
type TownSignificanceTier = 0 | 1 | 2 | 3 | 4 | 5;

/**
 * One settlement from the raw OSM extraction.
 */
type RawOsmSettlement = {
  osmId: string;

  name: string;

  place: SettlementPlaceType;

  latitude: number;

  longitude: number;

  population?: number;

  capital?: string;

  adminLevel?: string;

  /**
   * Explicit English-language OSM name.
   *
   * This is GeoPedia's preferred Latin-script companion label when the primary
   * settlement name uses another writing system.
   */
  nameEn?: string;

  /**
   * International OSM name.
   *
   * This provides a fallback Latin-script companion label when `name:en` is
   * unavailable.
   */
  intName?: string;
};

/**
 * Compact in-memory representation.
 *
 * Fields unnecessary to label ranking are deliberately discarded while
 * reading the raw NDJSON.
 */
type ProcessedTown = {
  osmId: string;

  /**
   * Primary OSM settlement name.
   *
   * This normally represents the locally used/native name and may use either
   * Latin or non-Latin script.
   */
  name: string;

  /**
   * Explicit English or international OSM settlement name.
   *
   * Unlike `latinName`, this value is retained even when the primary name
   * already uses Latin script. This allows town quizzes to distinguish names
   * such as `Wien` / `Vienna` and `Firenze` / `Florence`.
   */
  englishName?: string;

  /**
   * Latin-script companion name used by GeoPedia's world-map town labels when
   * the primary settlement name uses a non-Latin script.
   */
  latinName?: string;

  place: SettlementPlaceType;

  latitude: number;

  longitude: number;

  population?: number;

  capital?: string;

  significanceTier: TownSignificanceTier;

  importance: number;

  mercatorX: number;

  mercatorY: number;

  baseMinZoom: number;

  labelMinZoom?: number;

  markerType?: TownMarkerType;
};

/**
 * Matches any Unicode letter.
 */
const LETTER_REGEX = /\p{Letter}/u;

/**
 * Matches letters belonging to the Unicode Latin script.
 *
 * This includes extended Latin characters used by languages such as
 * Romanian, Vietnamese, Polish, Turkish, and Icelandic.
 */
const LATIN_SCRIPT_REGEX = /\p{Script=Latin}/u;

/**
 * Returns whether every letter in a name belongs to the Latin script.
 *
 * Spaces, punctuation, digits, and other non-letter characters are ignored.
 * At least one Latin letter must be present.
 */
function isLatinScript(value: string): boolean {
  let hasLetter = false;

  for (const character of value) {
    if (!LETTER_REGEX.test(character)) {
      continue;
    }

    hasLetter = true;

    if (!LATIN_SCRIPT_REGEX.test(character)) {
      return false;
    }
  }

  return hasLetter;
}

/**
 * Chooses the preferred explicit English/international OSM name.
 *
 * `name:en` is preferred because it explicitly represents the English name
 * used for the settlement. `int_name` provides a useful fallback when an
 * English-specific value is unavailable.
 *
 * Unlike `getLatinCompanionName`, this helper intentionally works for both
 * Latin- and non-Latin-script primary names. Town quizzes need to distinguish
 * Latin-script local names such as `Wien` from English names such as `Vienna`.
 *
 * @param settlement - Raw OSM settlement.
 * @returns Preferred English/international name when available.
 */
function getEnglishName(
  settlement: RawOsmSettlement,
): string | undefined {
  const candidates = [settlement.nameEn, settlement.intName];

  for (const candidate of candidates) {
    const trimmedCandidate = candidate?.trim();

    if (trimmedCandidate) {
      return trimmedCandidate;
    }
  }

  return undefined;
}

/**
 * Chooses GeoPedia's Latin-script companion name for a settlement.
 *
 * Primary names already written entirely in Latin script remain single-line
 * labels. For non-Latin primary names, the explicit English OSM name is
 * preferred because it is generally the most recognizable international name.
 * OSM's international name is used as a fallback.
 */
function getLatinCompanionName(
  settlement: RawOsmSettlement,
): string | undefined {
  if (isLatinScript(settlement.name)) {
    return undefined;
  }

  const candidates = [settlement.nameEn, settlement.intName];

  for (const candidate of candidates) {
    if (candidate && isLatinScript(candidate)) {
      return candidate;
    }
  }

  return undefined;
}

/**
 * One spatial-grid bucket.
 *
 * A town is stored only in the grid corresponding to the zoom at which it
 * first becomes spatially relevant.
 */
type ZoomSpatialGrid = Map<string, ProcessedTown[]>;

/**
 * All spatial grids keyed by half-zoom level.
 */
type SpatialGrids = Map<number, ZoomSpatialGrid>;

/**
 * Returns OSM's numeric capital level.
 */
function getCapitalLevel(capital: string | undefined): number | null {
  if (!capital) {
    return null;
  }

  const level = Number(capital);

  return Number.isFinite(level) ? level : null;
}

/**
 * Determines whether an OSM settlement is a national capital.
 *
 * OSM uses both `capital=yes` and numeric capital values.
 */
function isCountryCapital(
  town: Pick<RawOsmSettlement, "capital">,
): boolean {
  if (town.capital === "yes") {
    return true;
  }

  const level = getCapitalLevel(town.capital);

  return level !== null && level <= 2;
}

/**
 * Determines whether a settlement is a first-order administrative capital,
 * such as a US state capital.
 */
function isFirstOrderCapital(
  town: Pick<RawOsmSettlement, "capital">,
): boolean {
  const level = getCapitalLevel(town.capital);

  return level !== null && level > 2 && level <= 4;
}

/**
 * Determines whether a settlement is a lower-order regional administrative
 * center.
 */
function isRegionalCapital(
  town: Pick<RawOsmSettlement, "capital">,
): boolean {
  const level = getCapitalLevel(town.capital);

  return level !== null && level > 4 && level <= 6;
}

/**
 * Assigns the broad cartographic significance tier.
 */
function getTownSignificanceTier(
  town: RawOsmSettlement,
): TownSignificanceTier {
  const population = town.population ?? 0;

  if (isCountryCapital(town) || population >= 1_000_000) {
    return 0;
  }

  if (population >= 250_000 || isFirstOrderCapital(town)) {
    return 1;
  }

  if (population >= 75_000) {
    return 2;
  }

  if (
    town.place === "city" ||
    population >= 20_000 ||
    town.place === "town"
  ) {
    return 3;
  }

  if (town.place === "village" || town.place === "hamlet") {
    return 4;
  }

  return 5;
}

/**
 * Computes continuous collision priority.
 *
 * Population strongly distinguishes larger settlements where OSM population
 * coverage is useful. Place classification remains important where population
 * is unavailable.
 */
function getTownImportance(
  town: RawOsmSettlement,
  significanceTier: TownSignificanceTier,
): number {
  const tierScore = (5 - significanceTier) * 1000;

  let placeScore: number;

  switch (town.place) {
    case "city":
      placeScore = 500;
      break;

    case "town":
      placeScore = 400;
      break;

    case "village":
      placeScore = 300;
      break;

    case "hamlet":
      placeScore = 200;
      break;

    case "suburb":
      placeScore = 125;
      break;

    case "isolated_dwelling":
      placeScore = 75;
      break;
  }

  const populationScore =
    town.population !== undefined && town.population > 0
      ? Math.log10(town.population) * 140
      : 0;

  let capitalScore = 0;

  if (isCountryCapital(town)) {
    capitalScore = 500;
  } else if (isFirstOrderCapital(town)) {
    /*
     * Capitals are promoted, but a much larger neighboring metro should still
     * win the earliest collision slot.
     */
    capitalScore = 25;
  } else if (isRegionalCapital(town)) {
    capitalScore = 20;
  }

  return tierScore + placeScore + populationScore + capitalScore;
}

/**
 * Returns a modest label-zoom adjustment based on OSM settlement class.
 */
function getPlaceZoomAdjustment(place: SettlementPlaceType): number {
  switch (place) {
    case "city":
      return -0.2;

    case "town":
      return 0;

    case "village":
      return 0.4;

    case "hamlet":
      return 1;

    case "suburb":
      return 1.5;

    case "isolated_dwelling":
      return 2;
  }
}

/**
 * Fallback zoom when OSM does not provide population.
 *
 * Worldwide OSM population coverage is weak for villages and hamlets, so
 * semantic place type becomes the primary signal for these features.
 */
function getUnknownPopulationMinZoom(
  place: SettlementPlaceType,
): number {
  switch (place) {
    case "city":
      return 6;

    case "town":
      return 7;

    case "village":
      return 8;

    case "hamlet":
      return 9.25;

    case "suburb":
      return 10.25;

    case "isolated_dwelling":
      return 11;
  }
}

/**
 * Calculates significance-driven label eligibility before spatial delay.
 */
function getTownBaseMinZoom(town: RawOsmSettlement): number {
  let zoom: number;

  if (town.population !== undefined && town.population > 0) {
    zoom = 10.5 - Math.log10(town.population);

    zoom += getPlaceZoomAdjustment(town.place);
  } else {
    zoom = getUnknownPopulationMinZoom(town.place);
  }

  /**
   * National capitals belong among the earliest town labels.
   */
  if (isCountryCapital(town)) {
    zoom = Math.min(zoom, 3.75);
  }

  /**
   * First-order capitals appear early without automatically beating larger
   * neighboring cities.
   */
  if (isFirstOrderCapital(town)) {
    zoom = Math.min(zoom - 0.05, 4.9);
  }

  if (isRegionalCapital(town)) {
    zoom -= 0.05;
  }

  return Math.max(MIN_LABEL_ZOOM, Math.min(MAX_LABEL_ZOOM, zoom));
}

/**
 * Returns the maximum amount of preprocessing spatial delay.
 *
 * Major settlements are never spatially delayed here. MapLibre's collision
 * engine decides whether their actual labels fit on screen.
 */
function getMaximumSpatialDelay(town: ProcessedTown): number {
  switch (town.significanceTier) {
    case 0:
    case 1:
    case 2:
      return 0;

    case 3:
      return 0.5;

    case 4:
      return 1.25;

    case 5:
      return 1.75;
  }
}

/**
 * Desired minimum label-anchor spacing.
 *
 * Lower zooms emphasize significance. Higher zooms permit dense local labels.
 */
function getMinimumLabelSpacingPixels(zoom: number): number {
  if (zoom < 5) {
    return 90;
  }

  if (zoom < 6) {
    return 80;
  }

  if (zoom < 7) {
    return 70;
  }

  if (zoom < 8) {
    return 60;
  }

  if (zoom < 9) {
    return 50;
  }

  if (zoom < 10) {
    return 42;
  }

  if (zoom < 11) {
    return 35;
  }

  if (zoom < 12) {
    return 30;
  }

  if (zoom < 13) {
    return 25;
  }

  return 20;
}

/**
 * Converts longitude to normalized Web Mercator X.
 */
function longitudeToMercatorX(longitude: number): number {
  return (longitude + 180) / 360;
}

/**
 * Converts latitude to normalized Web Mercator Y.
 */
function latitudeToMercatorY(latitude: number): number {
  const clampedLatitude = Math.max(
    -85.05112878,
    Math.min(85.05112878, latitude),
  );

  const radians = clampedLatitude * (Math.PI / 180);

  return (
    (1 -
      Math.log(Math.tan(radians) + 1 / Math.cos(radians)) / Math.PI) /
    2
  );
}

function getWorldSize(zoom: number): number {
  return TILE_SIZE * 2 ** zoom;
}

function getTownPixelX(town: ProcessedTown, zoom: number): number {
  return town.mercatorX * getWorldSize(zoom);
}

function getTownPixelY(town: ProcessedTown, zoom: number): number {
  return town.mercatorY * getWorldSize(zoom);
}

function getGridX(town: ProcessedTown, gridZoom: number): number {
  return Math.floor(
    getTownPixelX(town, gridZoom) /
      getMinimumLabelSpacingPixels(gridZoom),
  );
}

function getGridY(town: ProcessedTown, gridZoom: number): number {
  return Math.floor(
    getTownPixelY(town, gridZoom) /
      getMinimumLabelSpacingPixels(gridZoom),
  );
}

function getGridCellKey(gridX: number, gridY: number): string {
  return `${gridX}:${gridY}`;
}

/**
 * Calculates screen-space distance at the candidate's current zoom.
 */
function getScreenDistancePixels(
  firstTown: ProcessedTown,
  secondTown: ProcessedTown,
  zoom: number,
): number {
  const worldSize = getWorldSize(zoom);

  return Math.hypot(
    (firstTown.mercatorX - secondTown.mercatorX) * worldSize,

    (firstTown.mercatorY - secondTown.mercatorY) * worldSize,
  );
}

/**
 * Rounds upward to the next spatial-processing zoom.
 */
function getNextSpatialZoom(zoom: number): number {
  return Number(
    (Math.ceil(zoom / SPATIAL_ZOOM_STEP) * SPATIAL_ZOOM_STEP).toFixed(
      2,
    ),
  );
}

/**
 * Creates an empty spatial grid for every supported half-zoom level.
 *
 * Each town is ultimately stored in exactly one of these grids.
 */
function createSpatialGrids(): SpatialGrids {
  const grids: SpatialGrids = new Map();

  for (
    let zoom = getNextSpatialZoom(MIN_LABEL_ZOOM);
    zoom <= MAX_LABEL_ZOOM;
    zoom += SPATIAL_ZOOM_STEP
  ) {
    grids.set(Number(zoom.toFixed(2)), new Map());
  }

  return grids;
}

/**
 * Checks previously accepted settlements that are already eligible at the
 * candidate zoom.
 *
 * Each prior town lives in only one grid, so this avoids the huge memory cost
 * of duplicating every world settlement into all later zoom grids.
 */
function hasSpatialConflict(
  town: ProcessedTown,
  candidateZoom: number,
  spatialGrids: SpatialGrids,
): boolean {
  const requiredSpacing = getMinimumLabelSpacingPixels(candidateZoom);

  for (const [gridZoom, grid] of spatialGrids) {
    if (gridZoom > candidateZoom) {
      break;
    }

    const gridX = getGridX(town, gridZoom);

    const gridY = getGridY(town, gridZoom);

    for (let offsetX = -1; offsetX <= 1; offsetX++) {
      for (let offsetY = -1; offsetY <= 1; offsetY++) {
        const nearby = grid.get(
          getGridCellKey(gridX + offsetX, gridY + offsetY),
        );

        if (!nearby) {
          continue;
        }

        for (const nearbyTown of nearby) {
          if (
            getScreenDistancePixels(town, nearbyTown, candidateZoom) <
            requiredSpacing
          ) {
            return true;
          }
        }
      }
    }
  }

  return false;
}

/**
 * Generates a stable fractional zoom offset from the OSM ID.
 *
 * This prevents large groups of equivalent local settlements from all becoming
 * eligible at one exact zoom threshold.
 */
function getStableZoomOffset(osmId: string): number {
  let hash = 0;

  for (let index = 0; index < osmId.length; index++) {
    hash = (hash * 31 + osmId.charCodeAt(index)) >>> 0;
  }

  return ((hash % 1000) / 1000) * 0.18;
}

/**
 * Determines the final label zoom.
 */
function getFinalLabelZoom(
  town: ProcessedTown,
  spatialGrids: SpatialGrids,
): number {
  const maximumDelay = getMaximumSpatialDelay(town);

  /**
   * Major settlements rely entirely on significance and MapLibre collision.
   */
  if (maximumDelay === 0) {
    return town.baseMinZoom;
  }

  const firstSpatialZoom = getNextSpatialZoom(town.baseMinZoom);

  const maximumZoom = Math.min(
    MAX_LABEL_ZOOM,
    town.baseMinZoom + maximumDelay,
  );

  for (
    let zoom = firstSpatialZoom;
    zoom <= maximumZoom;
    zoom += SPATIAL_ZOOM_STEP
  ) {
    const normalizedZoom = Number(zoom.toFixed(2));

    if (!hasSpatialConflict(town, normalizedZoom, spatialGrids)) {
      return Math.min(
        MAX_LABEL_ZOOM,
        normalizedZoom + getStableZoomOffset(town.osmId),
      );
    }
  }

  return Math.min(
    MAX_LABEL_ZOOM,
    maximumZoom + getStableZoomOffset(town.osmId),
  );
}

/**
 * Adds a processed town to exactly one spatial grid.
 */
function addTownToSpatialGrid(
  town: ProcessedTown,
  spatialGrids: SpatialGrids,
): void {
  if (town.labelMinZoom === undefined) {
    return;
  }

  const gridZoom = Math.min(
    MAX_LABEL_ZOOM,
    getNextSpatialZoom(town.labelMinZoom),
  );

  const grid = spatialGrids.get(gridZoom);

  if (!grid) {
    return;
  }

  const cellKey = getGridCellKey(
    getGridX(town, gridZoom),
    getGridY(town, gridZoom),
  );

  const existing = grid.get(cellKey);

  if (existing) {
    existing.push(town);
  } else {
    grid.set(cellKey, [town]);
  }
}

/**
 * Assigns final label minimum zooms in descending significance order.
 */
function assignLabelZooms(towns: ProcessedTown[]): void {
  console.log("");

  console.log("Sorting settlements by cartographic importance...");

  towns.sort(
    (firstTown, secondTown) =>
      firstTown.significanceTier - secondTown.significanceTier ||
      secondTown.importance - firstTown.importance ||
      firstTown.name.localeCompare(secondTown.name),
  );

  console.log("Assigning spatial label zooms...");

  const spatialGrids = createSpatialGrids();

  const progressInterval = 250_000;

  for (let index = 0; index < towns.length; index++) {
    const town = towns[index];

    town.labelMinZoom = getFinalLabelZoom(town, spatialGrids);

    addTownToSpatialGrid(town, spatialGrids);

    if ((index + 1) % progressInterval === 0) {
      console.log(
        `  Ranked ${(index + 1).toLocaleString()} / ${towns.length.toLocaleString()}`,
      );
    }
  }
}

/**
 * Determines cartographic marker style.
 */
function getTownMarkerType(town: ProcessedTown): TownMarkerType {
  if (isCountryCapital(town)) {
    return "country-capital";
  }

  if (isFirstOrderCapital(town)) {
    return "admin-capital";
  }

  const population = town.population ?? 0;

  if (population >= 100_000) {
    return "major-city";
  }

  if (
    town.place === "city" &&
    (population >= 50_000 || isRegionalCapital(town))
  ) {
    return "major-city";
  }

  return null;
}

/**
 * Converts one raw settlement into the compact in-memory representation used
 * during ranking.
 */
function createProcessedTown(
  settlement: RawOsmSettlement,
): ProcessedTown {
  const significanceTier = getTownSignificanceTier(settlement);

  return {
    osmId: settlement.osmId,

    name: settlement.name,

    englishName: getEnglishName(settlement),

    latinName: getLatinCompanionName(settlement),

    place: settlement.place,

    latitude: settlement.latitude,

    longitude: settlement.longitude,

    population: settlement.population,

    capital: settlement.capital,

    significanceTier,

    importance: getTownImportance(settlement, significanceTier),

    mercatorX: longitudeToMercatorX(settlement.longitude),

    mercatorY: latitudeToMercatorY(settlement.latitude),

    baseMinZoom: getTownBaseMinZoom(settlement),
  };
}

/**
 * Streams the world NDJSON file and retains only compact ranking records.
 */
async function readSettlements(): Promise<ProcessedTown[]> {
  console.log(`Reading settlements: ${INPUT_PATH}`);

  const towns: ProcessedTown[] = [];

  const inputStream = fs.createReadStream(INPUT_PATH, {
    encoding: "utf8",
  });

  const lines = readline.createInterface({
    input: inputStream,

    crlfDelay: Infinity,
  });

  let lineNumber = 0;

  for await (const line of lines) {
    lineNumber++;

    if (line.trim().length === 0) {
      continue;
    }

    try {
      const settlement = JSON.parse(line) as RawOsmSettlement;

      towns.push(createProcessedTown(settlement));
    } catch (error) {
      throw new Error(
        `Failed to parse NDJSON line ${lineNumber.toLocaleString()}: ${String(error)}`,
      );
    }

    if (lineNumber % READ_PROGRESS_INTERVAL === 0) {
      console.log(
        `  Read ${lineNumber.toLocaleString()} settlements`,
      );
    }
  }

  console.log(
    `Loaded ${towns.length.toLocaleString()} settlements for ranking.`,
  );

  return towns;
}

/**
 * Writes lightweight label GeoJSON without constructing a second giant
 * FeatureCollection string in memory.
 *
 * Runtime label properties are retained alongside the source OSM ID, which
 * allows downstream data generators to identify multiple records that matched
 * the same OSM settlement.
 */
async function writeTownGeoJson(
  towns: ProcessedTown[],
): Promise<void> {
  fs.mkdirSync(path.dirname(OUTPUT_PATH), {
    recursive: true,
  });

  const outputStream = fs.createWriteStream(OUTPUT_PATH, {
    encoding: "utf8",

    flags: "w",
  });

  /**
   * Await output-stream backpressure when required.
   */
  async function write(value: string): Promise<void> {
    if (outputStream.write(value)) {
      return;
    }

    await new Promise<void>((resolve) => {
      outputStream.once("drain", resolve);
    });
  }

  await write('{"type":"FeatureCollection","features":[');

  for (let index = 0; index < towns.length; index++) {
    const town = towns[index];

    town.markerType = getTownMarkerType(town);

    const properties: Record<string, unknown> = {
      osmId: town.osmId,

      name: town.name,

      place: town.place,

      importance: Number(town.importance.toFixed(3)),

      significanceTier: town.significanceTier,

      labelMinZoom: Number(
        (town.labelMinZoom ?? MAX_LABEL_ZOOM).toFixed(3),
      ),
    };

    if (town.englishName) {
      properties.englishName = town.englishName;
    }

    if (town.latinName) {
      properties.latinName = town.latinName;
    }

    if (town.markerType) {
      properties.markerType = town.markerType;
    }

    const feature = {
      type: "Feature",

      geometry: {
        type: "Point",

        coordinates: [town.longitude, town.latitude],
      },

      properties,
    };

    if (index > 0) {
      await write(",");
    }

    await write(JSON.stringify(feature));

    if ((index + 1) % 250_000 === 0) {
      console.log(
        `  Wrote ${(index + 1).toLocaleString()} / ${towns.length.toLocaleString()} features`,
      );
    }
  }

  await write("]}");

  await new Promise<void>((resolve, reject) => {
    outputStream.end(resolve);

    outputStream.once("error", reject);
  });
}

/**
 * Prints half-zoom bucket counts for sanity checking.
 */
function printZoomDistribution(towns: ProcessedTown[]): void {
  const counts = new Map<number, number>();

  for (const town of towns) {
    const zoom = town.labelMinZoom ?? MAX_LABEL_ZOOM;

    const bucket = Math.floor(zoom * 2) / 2;

    counts.set(bucket, (counts.get(bucket) ?? 0) + 1);
  }

  console.log("");

  console.log("LABEL MIN ZOOM COUNTS (0.5-ZOOM BUCKETS)");

  console.log("----------------------------------------");

  console.table(
    Array.from(counts.entries())
      .sort((first, second) => first[0] - second[0])
      .map(([zoom, count]) => ({
        zoom,
        count,
      })),
  );
}

/**
 * Prints generated marker counts.
 */
function printMarkerDistribution(towns: ProcessedTown[]): void {
  const counts = new Map<string, number>();

  for (const town of towns) {
    const markerType = getTownMarkerType(town) ?? "none";

    counts.set(markerType, (counts.get(markerType) ?? 0) + 1);
  }

  console.log("");

  console.log("MARKER TYPE COUNTS");

  console.log("------------------");

  console.table(
    Array.from(counts.entries())
      .sort((first, second) => second[1] - first[1])
      .map(([markerType, count]) => ({
        markerType,
        count,
      })),
  );
}

async function main(): Promise<void> {
  if (!fs.existsSync(INPUT_PATH)) {
    throw new Error(
      `Input settlement file does not exist: ${INPUT_PATH}`,
    );
  }

  const towns = await readSettlements();

  assignLabelZooms(towns);

  printZoomDistribution(towns);

  printMarkerDistribution(towns);

  console.log("");

  console.log(`Writing ${OUTPUT_PATH}...`);

  await writeTownGeoJson(towns);

  console.log("");

  console.log("WORLD TOWN PROCESSING COMPLETE");

  console.log("------------------------------");

  console.log(`Processed towns: ${towns.length.toLocaleString()}`);

  console.log(`Output: ${OUTPUT_PATH}`);
}

void main().catch((error) => {
  console.error("");

  console.error("Town processing failed:", error);

  process.exitCode = 1;
});
