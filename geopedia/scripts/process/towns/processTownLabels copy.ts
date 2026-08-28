/**
 * Processes normalized OpenStreetMap settlements into GeoPedia's runtime
 * town-label GeoJSON.
 *
 * The ranking model is significance-first:
 *
 * - Major cities receive their zoom primarily from population and OSM class.
 * - Administrative capitals receive a useful boost, but do not automatically
 *   outrank larger nearby cities.
 * - Villages, hamlets, suburbs, and other lower-significance places may be
 *   delayed slightly by spatial competition.
 * - Fractional minimum zooms create gradual increases in label density rather
 *   than large integer-zoom jumps.
 *
 * MapLibre remains responsible for final on-screen collision placement.
 */

import fs from "node:fs";
import path from "node:path";

const INPUT_PATH = "data/processed/towns/us-settlements.raw.json";

const OUTPUT_PATH = "public/data/geojson/world/towns.geojson";

const TILE_SIZE = 512;

const MIN_LABEL_ZOOM = 3.5;
const MAX_LABEL_ZOOM = 14;

const SPATIAL_ZOOM_STEP = 0.25;

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
 * Lower values represent greater significance.
 */
type TownSignificanceTier = 0 | 1 | 2 | 3 | 4 | 5;

type RawOsmSettlement = {
  osmId: string;
  name: string;
  place: SettlementPlaceType;
  latitude: number;
  longitude: number;
  population?: number;
  capital?: string;
  adminLevel?: string;
  wikidata?: string;
  wikipedia?: string;
  officialName?: string;
  shortName?: string;
};

type RawOsmSettlementFile = {
  source: string;
  extractedAt: string;
  settlementCount: number;
  placeCounts: Record<string, number>;
  settlements: RawOsmSettlement[];
};

type ProcessedTown = RawOsmSettlement & {
  significanceTier: TownSignificanceTier;
  importance: number;
  mercatorX: number;
  mercatorY: number;
  baseMinZoom: number;
  labelMinZoom?: number;
  markerType?: TownMarkerType;
};

type TownFeatureProperties = {
  osmId: string;
  name: string;
  place: SettlementPlaceType;

  population?: number;
  capital?: string;
  adminLevel?: string;
  wikidata?: string;
  wikipedia?: string;
  officialName?: string;
  shortName?: string;

  importance: number;
  significanceTier: TownSignificanceTier;
  labelMinZoom: number;

  markerType?: Exclude<TownMarkerType, null>;

  showMarker: boolean;
};

type TownFeature = {
  type: "Feature";

  id: string;

  geometry: {
    type: "Point";
    coordinates: [number, number];
  };

  properties: TownFeatureProperties;
};

type TownFeatureCollection = {
  type: "FeatureCollection";
  features: TownFeature[];
};

type ZoomSpatialGrid = Map<string, ProcessedTown[]>;

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
 * Determines whether a settlement represents a national capital.
 *
 * OSM may encode national capitals either with a numeric administrative level
 * such as `capital=2` or with the older/general `capital=yes` form.
 */
function isCountryCapital(town: RawOsmSettlement): boolean {
  if (town.capital === "yes") {
    return true;
  }

  const level = getCapitalLevel(town.capital);

  return level !== null && level <= 2;
}

function isFirstOrderCapital(town: RawOsmSettlement): boolean {
  const level = getCapitalLevel(town.capital);

  return level !== null && level > 2 && level <= 4;
}

function isRegionalCapital(town: RawOsmSettlement): boolean {
  const level = getCapitalLevel(town.capital);

  return level !== null && level > 4 && level <= 6;
}

/**
 * Assigns the broad typography/cartographic tier.
 *
 * Capital status matters, but population remains important enough that a
 * larger metro can still outrank its smaller administrative neighbor.
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
 * Returns a continuous cartographic importance score.
 *
 * Population strongly distinguishes large settlements when available.
 * OSM's semantic place class remains useful where population is absent.
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
    town.population && town.population > 0
      ? Math.log10(town.population) * 140
      : 0;

  let capitalScore = 0;

  if (isCountryCapital(town)) {
    capitalScore = 500;
  } else if (isFirstOrderCapital(town)) {
    /*
     * Noticeably important, but deliberately not enough to make Saint Paul
     * outrank Minneapolis solely because it is the capital.
     */
    capitalScore = 25;
  } else if (isRegionalCapital(town)) {
    capitalScore = 20;
  }

  return tierScore + placeScore + populationScore + capitalScore;
}

/**
 * Returns the place-class adjustment applied to population-derived zoom.
 *
 * Cities receive a modest promotion. Small semantic classes appear later.
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
 * Returns a reasonable fallback minimum zoom when OSM does not provide
 * population.
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
 * Calculates the significance-driven minimum zoom before spatial placement.
 *
 * For known population, the logarithmic formula produces smooth transitions:
 *
 * ~1,000,000 people -> around zoom 4.5
 * ~100,000          -> around zoom 5.5
 * ~10,000           -> around zoom 6.5
 * ~1,000            -> around zoom 7.5
 *
 * Place classification then makes a modest adjustment.
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
   * Country capitals belong among the first global settlement labels, but
   * towns as a whole still remain hidden at the farthest world zooms.
   */
  if (isCountryCapital(town)) {
    zoom = Math.min(zoom, 3.75);
  }

  /**
   * First-order capitals receive a guarantee that they appear reasonably
   * early, but only a very small direct promotion.
   *
   * This preserves cases such as:
   *
   * Minneapolis before Saint Paul
   * Las Vegas before Carson City
   * Seattle before Olympia
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
 * Returns how much spatial competition may delay one settlement.
 *
 * High-significance cities are not spatially delayed at preprocessing time.
 * MapLibre handles their actual collision.
 *
 * Lower-level settlements may be delayed modestly to preserve the excellent
 * high-zoom geographic distribution from the earlier prototype.
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
 * Returns desired anchor spacing.
 *
 * Spatial placement matters progressively more for local settlements than for
 * major cities.
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

function longitudeToMercatorX(longitude: number): number {
  return (longitude + 180) / 360;
}

function latitudeToMercatorY(latitude: number): number {
  const clampedLatitude = Math.max(
    -85.05112878,
    Math.min(85.05112878, latitude),
  );

  const latitudeRadians = clampedLatitude * (Math.PI / 180);

  return (
    (1 -
      Math.log(
        Math.tan(latitudeRadians) + 1 / Math.cos(latitudeRadians),
      ) /
        Math.PI) /
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

function getGridX(town: ProcessedTown, zoom: number): number {
  return Math.floor(
    getTownPixelX(town, zoom) / getMinimumLabelSpacingPixels(zoom),
  );
}

function getGridY(town: ProcessedTown, zoom: number): number {
  return Math.floor(
    getTownPixelY(town, zoom) / getMinimumLabelSpacingPixels(zoom),
  );
}

function getGridCellKey(gridX: number, gridY: number): string {
  return `${gridX}:${gridY}`;
}

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
 * Snaps a zoom upward to the next spatial-grid step.
 */
function getNextSpatialZoom(zoom: number): number {
  return Math.ceil(zoom / SPATIAL_ZOOM_STEP) * SPATIAL_ZOOM_STEP;
}

/**
 * Returns every spatial-grid zoom used by the processor.
 */
function getSpatialZooms(): number[] {
  const zooms: number[] = [];

  for (
    let zoom = getNextSpatialZoom(MIN_LABEL_ZOOM);
    zoom <= MAX_LABEL_ZOOM;
    zoom += SPATIAL_ZOOM_STEP
  ) {
    zooms.push(Number(zoom.toFixed(2)));
  }

  return zooms;
}

function createZoomSpatialGrids(): Map<number, ZoomSpatialGrid> {
  const grids = new Map<number, ZoomSpatialGrid>();

  for (const zoom of getSpatialZooms()) {
    grids.set(zoom, new Map());
  }

  return grids;
}

function hasSpatialConflict(
  town: ProcessedTown,
  zoom: number,
  grid: ZoomSpatialGrid,
): boolean {
  const spacing = getMinimumLabelSpacingPixels(zoom);

  const gridX = getGridX(town, zoom);

  const gridY = getGridY(town, zoom);

  for (let offsetX = -1; offsetX <= 1; offsetX++) {
    for (let offsetY = -1; offsetY <= 1; offsetY++) {
      const nearbyTowns = grid.get(
        getGridCellKey(gridX + offsetX, gridY + offsetY),
      );

      if (!nearbyTowns) {
        continue;
      }

      for (const nearbyTown of nearbyTowns) {
        if (
          getScreenDistancePixels(town, nearbyTown, zoom) < spacing
        ) {
          return true;
        }
      }
    }
  }

  return false;
}

/**
 * Returns a stable pseudo-random fraction from the OSM ID.
 *
 * This very small deterministic offset prevents large groups of otherwise
 * equivalent local settlements from all becoming visible at exactly the same
 * fractional zoom.
 */
function getStableZoomOffset(osmId: string): number {
  let hash = 0;

  for (let index = 0; index < osmId.length; index++) {
    hash = (hash * 31 + osmId.charCodeAt(index)) >>> 0;
  }

  return ((hash % 1000) / 1000) * 0.18;
}

/**
 * Determines final label zoom.
 *
 * Major settlements keep their significance-derived zoom unchanged.
 *
 * Lower-significance settlements may move slightly later if a stronger label
 * already occupies nearby map space.
 */
function getFinalLabelZoom(
  town: ProcessedTown,
  zoomGrids: Map<number, ZoomSpatialGrid>,
): number {
  const maximumDelay = getMaximumSpatialDelay(town);

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

    const grid = zoomGrids.get(normalizedZoom);

    if (!grid) {
      continue;
    }

    if (!hasSpatialConflict(town, normalizedZoom, grid)) {
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
 * Adds a label to every later spatial grid.
 */
function addTownToSpatialGrids(
  town: ProcessedTown,
  zoomGrids: Map<number, ZoomSpatialGrid>,
): void {
  if (town.labelMinZoom === undefined) {
    return;
  }

  for (const [zoom, grid] of zoomGrids) {
    if (zoom < town.labelMinZoom) {
      continue;
    }

    const cellKey = getGridCellKey(
      getGridX(town, zoom),
      getGridY(town, zoom),
    );

    const existing = grid.get(cellKey);

    if (existing) {
      existing.push(town);
    } else {
      grid.set(cellKey, [town]);
    }
  }
}

/**
 * Assigns final label minimum zooms in significance order.
 */
function assignLabelZooms(towns: ProcessedTown[]): void {
  const orderedTowns = towns
    .slice()
    .sort(
      (firstTown, secondTown) =>
        firstTown.significanceTier - secondTown.significanceTier ||
        secondTown.importance - firstTown.importance ||
        firstTown.name.localeCompare(secondTown.name),
    );

  const zoomGrids = createZoomSpatialGrids();

  for (const town of orderedTowns) {
    town.labelMinZoom = getFinalLabelZoom(town, zoomGrids);

    addTownToSpatialGrids(town, zoomGrids);
  }
}

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

const rawData = JSON.parse(
  fs.readFileSync(INPUT_PATH, "utf8"),
) as RawOsmSettlementFile;

const processedTowns: ProcessedTown[] = rawData.settlements.map(
  (settlement) => {
    const significanceTier = getTownSignificanceTier(settlement);

    return {
      ...settlement,

      significanceTier,

      importance: getTownImportance(settlement, significanceTier),

      mercatorX: longitudeToMercatorX(settlement.longitude),

      mercatorY: latitudeToMercatorY(settlement.latitude),

      baseMinZoom: getTownBaseMinZoom(settlement),
    };
  },
);

console.log(
  `Processing settlements: ${processedTowns.length.toLocaleString()}`,
);

assignLabelZooms(processedTowns);

for (const town of processedTowns) {
  town.markerType = getTownMarkerType(town);
}

const features: TownFeature[] = processedTowns.map((town) => {
  const markerType = town.markerType ?? null;

  return {
    type: "Feature",

    id: town.osmId,

    geometry: {
      type: "Point",

      coordinates: [town.longitude, town.latitude],
    },

    properties: {
      osmId: town.osmId,

      name: town.name,

      place: town.place,

      ...(town.population !== undefined
        ? {
            population: town.population,
          }
        : {}),

      ...(town.capital
        ? {
            capital: town.capital,
          }
        : {}),

      ...(town.adminLevel
        ? {
            adminLevel: town.adminLevel,
          }
        : {}),

      ...(town.wikidata
        ? {
            wikidata: town.wikidata,
          }
        : {}),

      ...(town.wikipedia
        ? {
            wikipedia: town.wikipedia,
          }
        : {}),

      ...(town.officialName
        ? {
            officialName: town.officialName,
          }
        : {}),

      ...(town.shortName
        ? {
            shortName: town.shortName,
          }
        : {}),

      importance: Number(town.importance.toFixed(3)),

      significanceTier: town.significanceTier,

      labelMinZoom: Number(
        (town.labelMinZoom ?? MAX_LABEL_ZOOM).toFixed(3),
      ),

      ...(markerType
        ? {
            markerType,
          }
        : {}),

      showMarker: markerType !== null,
    },
  };
});

const featureCollection: TownFeatureCollection = {
  type: "FeatureCollection",

  features,
};

fs.mkdirSync(path.dirname(OUTPUT_PATH), {
  recursive: true,
});

fs.writeFileSync(
  OUTPUT_PATH,
  JSON.stringify(featureCollection),
  "utf8",
);

console.log(`Generated towns: ${features.length.toLocaleString()}`);

console.log(`Output: ${OUTPUT_PATH}`);

/**
 * Report counts using half-zoom buckets so the new fractional distribution is
 * easy to inspect without dumping hundreds of unique values.
 */
const zoomBucketCounts = new Map<number, number>();

for (const town of processedTowns) {
  const zoom = town.labelMinZoom ?? MAX_LABEL_ZOOM;

  const bucket = Math.floor(zoom * 2) / 2;

  zoomBucketCounts.set(
    bucket,
    (zoomBucketCounts.get(bucket) ?? 0) + 1,
  );
}

console.log("");
console.log("LABEL MIN ZOOM COUNTS (0.5-ZOOM BUCKETS)");
console.log("----------------------------------------");

console.table(
  Array.from(zoomBucketCounts.entries())
    .sort((first, second) => first[0] - second[0])
    .map(([zoom, count]) => ({
      zoom,
      count,
    })),
);
