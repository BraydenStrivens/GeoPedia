/**
 * Generates GeoPedia's country-specific town quiz map and scoring
 * configurations.
 *
 * INITIAL MAP VIEW
 * ----------------
 *
 * Initial camera positioning is primarily derived from GeoPedia's country-page
 * geometry:
 *
 * public/data/global/countries/geojson/country-pages.geojson
 *
 * Country geometry is classified as either mainland-oriented or
 * archipelago-oriented.
 *
 * Mainland-oriented countries:
 *
 * - Begin with the country's largest polygon component.
 * - Repeatedly include any remaining component within a configured geographic
 *   distance of an already selected component.
 * - This allows nearby islands and detached regions to remain visible while
 *   excluding very remote territories that would make the starting camera far
 *   too wide.
 *
 * Examples of the intended behavior include:
 *
 * - Continental United States without Alaska/Hawaii expanding the camera.
 * - Mainland Chile without Easter Island expanding the camera.
 * - Metropolitan France with nearby Corsica but without remote territories.
 * - Norway without Svalbard.
 * - Japan retaining its major nearby islands.
 *
 * Archipelago-oriented countries:
 *
 * - Always include the largest polygon.
 * - Include additional polygons that contain at least one generated quiz town.
 *
 * This preserves useful quiz geography for countries such as Indonesia and the
 * Philippines, where populated islands are inherently distributed across
 * multiple disconnected landmasses.
 *
 * If a town dataset has no matching feature in `country-pages.geojson`, the
 * camera falls back to bounds calculated from all of that country's quiz towns.
 *
 * All longitude-bound calculations are date-line aware.
 *
 * MAXIMUM ERROR DISTANCE
 * ----------------------
 *
 * `maxErrorKm` remains entirely independent from country geometry.
 *
 * The scoring algorithm:
 *
 * 1. Finds the geographic medoid of all generated quiz towns.
 * 2. Retains the geographically closest 90% as the country's core town set.
 * 3. Calculates every unique pairwise geodesic distance between those towns.
 * 4. Uses the median pairwise distance as `maxErrorKm`.
 *
 * This scoring algorithm has already been validated through gameplay testing
 * and should not be changed by camera-generation refinements.
 *
 * OUTPUT
 * ------
 *
 * src/quiz/town/townCountryConfigs.ts
 */

import fs from "node:fs";
import path from "node:path";

/* -------------------------------------------------------------------------- */
/* Paths                                                                      */
/* -------------------------------------------------------------------------- */

/**
 * Directory containing one generated runtime town dataset per country.
 */
const TOWN_DATA_DIRECTORY = "public/data/towns";

/**
 * GeoJSON containing GeoPedia's country-page geography.
 */
const COUNTRY_GEOJSON_PATH =
  "public/data/global/countries/geojson/country-pages.geojson";

/**
 * Runtime TypeScript configuration produced by this generator.
 */
const OUTPUT_PATH = "src/quiz/town/townCountryConfigs.ts";

/* -------------------------------------------------------------------------- */
/* Scoring settings                                                           */
/* -------------------------------------------------------------------------- */

/**
 * Fraction of towns retained when determining the normal geographic scale of a
 * country's town distribution.
 */
const CORE_TOWN_FRACTION = 0.9;

/**
 * Minimum number of towns retained in the scoring core.
 */
const MIN_CORE_TOWN_COUNT = 3;

/**
 * Fallback score radius for a country containing only one generated town.
 */
const SINGLE_TOWN_MAX_ERROR_KM = 25;

/**
 * Mean Earth radius used for geographic distance calculations.
 */
const EARTH_RADIUS_KM = 6371;

/* -------------------------------------------------------------------------- */
/* Camera settings                                                            */
/* -------------------------------------------------------------------------- */

/**
 * A country is treated as mainland-oriented when its largest polygon accounts
 * for at least this fraction of its total approximate land area.
 *
 * Countries below this threshold are treated as archipelagos.
 */
const MAINLAND_LARGEST_POLYGON_FRACTION = 0.55;

/**
 * Maximum separation between polygon components that may be chained together
 * as part of the same mainland geographic cluster.
 *
 * Selection is iterative, so a nearby island can itself connect another nearby
 * island even when the second island is farther than this distance from the
 * original mainland polygon.
 */
const MAINLAND_COMPONENT_MAX_DISTANCE_KM = 300;

/**
 * Representative desktop dimensions used to derive generated MapLibre zooms.
 *
 * GeoPedia remains responsive at runtime; these dimensions simply establish a
 * consistent baseline.
 */
const REFERENCE_VIEWPORT_WIDTH = 1200;

const REFERENCE_VIEWPORT_HEIGHT = 800;

/**
 * Fraction of the representative viewport that the country's limiting
 * geographic dimension may occupy.
 */
const VIEWPORT_CONTENT_FRACTION = 0.75;

/**
 * MapLibre's effective world size at zoom zero.
 */
const MAPLIBRE_TILE_SIZE = 512;

/**
 * Safety limits for generated initial zoom levels.
 */
const MIN_INITIAL_ZOOM = 1;

const MAX_INITIAL_ZOOM = 11;

/* -------------------------------------------------------------------------- */
/* Town types                                                                 */
/* -------------------------------------------------------------------------- */

/**
 * Minimal runtime town representation required by this generator.
 */
type TownQuizTown = {
  id: string;

  name: string;

  latitude: number;
  longitude: number;

  population: number;
  populationRank: number;

  isCapital: boolean;
};

/**
 * Structure of one generated runtime town data file.
 */
type TownQuizData = {
  towns: TownQuizTown[];
};

/* -------------------------------------------------------------------------- */
/* GeoJSON types                                                              */
/* -------------------------------------------------------------------------- */

type Position = [number, number, ...number[]];

type LinearRing = Position[];

type PolygonCoordinates = LinearRing[];

type MultiPolygonCoordinates = PolygonCoordinates[];

type PolygonGeometry = {
  type: "Polygon";

  coordinates: PolygonCoordinates;
};

type MultiPolygonGeometry = {
  type: "MultiPolygon";

  coordinates: MultiPolygonCoordinates;
};

type CountryGeometry = PolygonGeometry | MultiPolygonGeometry;

type CountryFeature = {
  type: "Feature";

  id?: string | number;

  properties: Record<string, unknown> | null;

  geometry: CountryGeometry | null;
};

type CountryFeatureCollection = {
  type: "FeatureCollection";

  features: CountryFeature[];
};

/* -------------------------------------------------------------------------- */
/* Generated configuration types                                              */
/* -------------------------------------------------------------------------- */

/**
 * Date-line-aware geographic bounds.
 *
 * A center plus span is used instead of ordinary minimum/maximum longitude
 * values because a country may cross the international date line.
 */
type GeographicBounds = {
  centerLongitude: number;

  longitudeSpan: number;

  minimumLatitude: number;
  maximumLatitude: number;
};

/**
 * Runtime town quiz configuration generated for one country.
 */
type GeneratedTownCountryConfig = {
  initialView: {
    center: [number, number];

    zoom: number;
  };

  maxErrorKm: number;
};

/**
 * Describes which geographic strategy generated a country's starting camera.
 */
type CameraSource =
  "geometry-mainland" | "geometry-archipelago" | "town-fallback";

/**
 * Additional information returned while selecting camera polygons.
 */
type CameraPolygonSelection = {
  polygons: PolygonCoordinates[];

  cameraSource: Exclude<CameraSource, "town-fallback">;

  totalPolygonCount: number;

  selectedPolygonCount: number;

  largestPolygonFraction: number;
};

/**
 * Diagnostics printed for each generated country.
 */
type CountryDiagnostics = {
  countryId: string;

  totalTownCount: number;
  coreTownCount: number;

  maxErrorKm: number;

  cameraSource: CameraSource;

  selectedPolygonCount: number | null;

  totalPolygonCount: number | null;

  largestPolygonFraction: number | null;

  centerLongitude: number;
  centerLatitude: number;

  longitudeSpan: number;
  latitudeSpan: number;

  zoom: number;
};

/* -------------------------------------------------------------------------- */
/* General numeric helpers                                                    */
/* -------------------------------------------------------------------------- */

/**
 * Converts degrees to radians.
 */
function degreesToRadians(degrees: number): number {
  return (degrees * Math.PI) / 180;
}

/**
 * Converts radians to degrees.
 */
function radiansToDegrees(radians: number): number {
  return (radians * 180) / Math.PI;
}

/**
 * Restricts a number to an inclusive range.
 */
function clamp(
  value: number,
  minimum: number,
  maximum: number,
): number {
  return Math.min(maximum, Math.max(minimum, value));
}

/**
 * Normalizes longitude into [-180, 180).
 */
function normalizeLongitude(longitude: number): number {
  return ((((longitude + 180) % 360) + 360) % 360) - 180;
}

/**
 * Normalizes longitude into [0, 360).
 */
function normalizePositiveLongitude(longitude: number): number {
  return ((longitude % 360) + 360) % 360;
}

/**
 * Returns an equivalent longitude positioned as closely as possible to a
 * supplied reference longitude.
 */
function normalizeLongitudeNear(
  longitude: number,
  referenceLongitude: number,
): number {
  let normalized = longitude;

  while (normalized - referenceLongitude > 180) {
    normalized -= 360;
  }

  while (normalized - referenceLongitude < -180) {
    normalized += 360;
  }

  return normalized;
}

/* -------------------------------------------------------------------------- */
/* Geographic distance                                                        */
/* -------------------------------------------------------------------------- */

/**
 * Calculates great-circle distance between two coordinate pairs using the
 * haversine formula.
 */
function getCoordinateDistanceKm(
  firstLatitude: number,
  firstLongitude: number,
  secondLatitude: number,
  secondLongitude: number,
): number {
  const firstLatitudeRadians = degreesToRadians(firstLatitude);

  const secondLatitudeRadians = degreesToRadians(secondLatitude);

  const latitudeDifference = degreesToRadians(
    secondLatitude - firstLatitude,
  );

  const longitudeDifference = degreesToRadians(
    secondLongitude - firstLongitude,
  );

  const haversine =
    Math.sin(latitudeDifference / 2) ** 2 +
    Math.cos(firstLatitudeRadians) *
      Math.cos(secondLatitudeRadians) *
      Math.sin(longitudeDifference / 2) ** 2;

  const angularDistance =
    2 * Math.atan2(Math.sqrt(haversine), Math.sqrt(1 - haversine));

  return EARTH_RADIUS_KM * angularDistance;
}

/**
 * Calculates great-circle distance between two quiz towns.
 */
function getTownDistanceKm(
  firstTown: TownQuizTown,
  secondTown: TownQuizTown,
): number {
  return getCoordinateDistanceKm(
    firstTown.latitude,
    firstTown.longitude,
    secondTown.latitude,
    secondTown.longitude,
  );
}

/* -------------------------------------------------------------------------- */
/* Scoring calculations                                                       */
/* -------------------------------------------------------------------------- */

/**
 * Returns an interpolated percentile from an ascending numeric array.
 */
function getPercentile(
  sortedValues: number[],
  percentile: number,
): number {
  if (sortedValues.length === 0) {
    return 0;
  }

  if (sortedValues.length === 1) {
    return sortedValues[0];
  }

  const position = (sortedValues.length - 1) * percentile;

  const lowerIndex = Math.floor(position);

  const upperIndex = Math.ceil(position);

  if (lowerIndex === upperIndex) {
    return sortedValues[lowerIndex];
  }

  const interpolation = position - lowerIndex;

  return (
    sortedValues[lowerIndex] +
    (sortedValues[upperIndex] - sortedValues[lowerIndex]) *
      interpolation
  );
}

/**
 * Calculates every unique pairwise town distance.
 */
function getPairwiseDistances(towns: TownQuizTown[]): number[] {
  const distances: number[] = [];

  for (
    let firstIndex = 0;
    firstIndex < towns.length;
    firstIndex += 1
  ) {
    for (
      let secondIndex = firstIndex + 1;
      secondIndex < towns.length;
      secondIndex += 1
    ) {
      distances.push(
        getTownDistanceKm(towns[firstIndex], towns[secondIndex]),
      );
    }
  }

  distances.sort(
    (firstDistance, secondDistance) => firstDistance - secondDistance,
  );

  return distances;
}

/**
 * Finds the actual quiz town having the smallest combined geodesic distance to
 * every other generated town.
 */
function getGeographicMedoid(towns: TownQuizTown[]): TownQuizTown {
  if (towns.length === 0) {
    throw new Error(
      "Cannot calculate a geographic medoid for an empty town set.",
    );
  }

  let medoid = towns[0];

  let smallestTotalDistance = Number.POSITIVE_INFINITY;

  for (const candidate of towns) {
    let totalDistance = 0;

    for (const otherTown of towns) {
      if (candidate === otherTown) {
        continue;
      }

      totalDistance += getTownDistanceKm(candidate, otherTown);
    }

    if (totalDistance < smallestTotalDistance) {
      smallestTotalDistance = totalDistance;

      medoid = candidate;
    }
  }

  return medoid;
}

/**
 * Selects the central 90% of quiz towns used by the validated scoring
 * algorithm.
 */
function getCoreTowns(towns: TownQuizTown[]): TownQuizTown[] {
  if (towns.length <= MIN_CORE_TOWN_COUNT) {
    return [...towns];
  }

  const medoid = getGeographicMedoid(towns);

  const townsByDistance = [...towns].sort(
    (firstTown, secondTown) =>
      getTownDistanceKm(medoid, firstTown) -
      getTownDistanceKm(medoid, secondTown),
  );

  const requestedCoreCount = Math.ceil(
    towns.length * CORE_TOWN_FRACTION,
  );

  const coreTownCount = Math.min(
    towns.length,
    Math.max(MIN_CORE_TOWN_COUNT, requestedCoreCount),
  );

  return townsByDistance.slice(0, coreTownCount);
}

/**
 * Generates the tested `maxErrorKm` value for one country.
 */
function getMaxErrorKm(towns: TownQuizTown[]): {
  coreTownCount: number;
  maxErrorKm: number;
} {
  const coreTowns = getCoreTowns(towns);

  const pairwiseDistances = getPairwiseDistances(coreTowns);

  const medianDistanceKm =
    pairwiseDistances.length > 0
      ? getPercentile(pairwiseDistances, 0.5)
      : SINGLE_TOWN_MAX_ERROR_KM;

  return {
    coreTownCount: coreTowns.length,

    maxErrorKm: Math.max(1, Math.round(medianDistanceKm)),
  };
}

/* -------------------------------------------------------------------------- */
/* Country-feature identification                                             */
/* -------------------------------------------------------------------------- */

/**
 * Possible properties containing GeoPedia-compatible three-letter country IDs.
 */
const COUNTRY_ID_PROPERTY_NAMES = [
  "id",

  "countryId",
  "country_id",

  "iso_a3",
  "ISO_A3",

  "iso3",
  "ISO3",

  "adm0_a3",
  "ADM0_A3",

  "sov_a3",
  "SOV_A3",

  "gu_a3",
  "GU_A3",
] as const;

/**
 * Attempts to resolve a lowercase three-letter country ID from one country-page
 * feature.
 */
function getCountryFeatureId(
  feature: CountryFeature,
): string | undefined {
  const properties = feature.properties;

  if (properties) {
    for (const propertyName of COUNTRY_ID_PROPERTY_NAMES) {
      const value = properties[propertyName];

      if (typeof value !== "string") {
        continue;
      }

      const normalizedValue = value.trim().toLowerCase();

      if (normalizedValue.length === 3) {
        return normalizedValue;
      }
    }
  }

  if (
    typeof feature.id === "string" ||
    typeof feature.id === "number"
  ) {
    const normalizedId = String(feature.id).trim().toLowerCase();

    if (normalizedId.length === 3) {
      return normalizedId;
    }
  }

  return undefined;
}

/**
 * Builds a lookup from GeoPedia country ID to country-page feature.
 */
function createCountryFeatureLookup(
  collection: CountryFeatureCollection,
): Map<string, CountryFeature> {
  const lookup = new Map<string, CountryFeature>();

  for (const feature of collection.features) {
    const countryId = getCountryFeatureId(feature);

    if (!countryId) {
      continue;
    }

    if (lookup.has(countryId)) {
      throw new Error(
        `Duplicate country-page GeoJSON feature ID: ${countryId}`,
      );
    }

    lookup.set(countryId, feature);
  }

  return lookup;
}

/* -------------------------------------------------------------------------- */
/* Polygon helpers                                                            */
/* -------------------------------------------------------------------------- */

/**
 * Returns the exterior ring of one polygon component.
 */
function getPolygonOuterRing(
  polygon: PolygonCoordinates,
): LinearRing {
  const outerRing = polygon[0];

  if (!outerRing || outerRing.length === 0) {
    throw new Error("Country geometry contains an empty polygon.");
  }

  return outerRing;
}

/**
 * Converts Polygon and MultiPolygon geometry into a common component array.
 */
function getPolygonComponents(
  geometry: CountryGeometry,
): PolygonCoordinates[] {
  if (geometry.type === "Polygon") {
    return [geometry.coordinates];
  }

  return geometry.coordinates;
}

/* -------------------------------------------------------------------------- */
/* Approximate polygon area                                                   */
/* -------------------------------------------------------------------------- */

/**
 * Produces a longitude sequence with date-line wrapping removed.
 *
 * Each coordinate is adjusted relative to the previous coordinate so polygon
 * area calculations do not interpret a short crossing near ±180° as an almost
 * full-world edge.
 */
function unwrapRingLongitudes(ring: LinearRing): number[] {
  if (ring.length === 0) {
    return [];
  }

  const longitudes: number[] = [ring[0][0]];

  for (let index = 1; index < ring.length; index += 1) {
    longitudes.push(
      normalizeLongitudeNear(ring[index][0], longitudes[index - 1]),
    );
  }

  return longitudes;
}

/**
 * Calculates an approximate polygon area in square kilometers.
 *
 * Exact geodesic area is unnecessary because this value is used only to compare
 * polygon components belonging to the same country.
 *
 * The ring is projected locally using an equirectangular approximation centered
 * on the ring's mean latitude.
 */
function getApproximatePolygonAreaKm2(
  polygon: PolygonCoordinates,
): number {
  const ring = getPolygonOuterRing(polygon);

  if (ring.length < 3) {
    return 0;
  }

  const unwrappedLongitudes = unwrapRingLongitudes(ring);

  const meanLatitude =
    ring.reduce((total, position) => total + position[1], 0) /
    ring.length;

  const latitudeScale = Math.cos(degreesToRadians(meanLatitude));

  let doubledArea = 0;

  for (let index = 0; index < ring.length; index += 1) {
    const nextIndex = (index + 1) % ring.length;

    const currentX =
      EARTH_RADIUS_KM *
      degreesToRadians(unwrappedLongitudes[index]) *
      latitudeScale;

    const currentY =
      EARTH_RADIUS_KM * degreesToRadians(ring[index][1]);

    const nextLongitude =
      nextIndex === 0
        ? normalizeLongitudeNear(
            unwrappedLongitudes[0],
            unwrappedLongitudes[index],
          )
        : unwrappedLongitudes[nextIndex];

    const nextX =
      EARTH_RADIUS_KM *
      degreesToRadians(nextLongitude) *
      latitudeScale;

    const nextY =
      EARTH_RADIUS_KM * degreesToRadians(ring[nextIndex][1]);

    doubledArea += currentX * nextY - nextX * currentY;
  }

  return Math.abs(doubledArea / 2);
}

/* -------------------------------------------------------------------------- */
/* Town-in-polygon calculations                                               */
/* -------------------------------------------------------------------------- */

/**
 * Determines whether a longitude/latitude point lies inside one ring.
 *
 * Ring longitudes are temporarily normalized around the tested longitude so
 * the ray-casting algorithm remains valid around the international date line.
 */
function isPointInRing(
  longitude: number,
  latitude: number,
  ring: LinearRing,
): boolean {
  let isInside = false;

  for (
    let currentIndex = 0, previousIndex = ring.length - 1;
    currentIndex < ring.length;
    previousIndex = currentIndex, currentIndex += 1
  ) {
    const current = ring[currentIndex];

    const previous = ring[previousIndex];

    const currentLongitude = normalizeLongitudeNear(
      current[0],
      longitude,
    );

    const previousLongitude = normalizeLongitudeNear(
      previous[0],
      longitude,
    );

    const currentLatitude = current[1];

    const previousLatitude = previous[1];

    const crossesLatitude =
      currentLatitude > latitude !== previousLatitude > latitude;

    if (!crossesLatitude) {
      continue;
    }

    const intersectionLongitude =
      ((previousLongitude - currentLongitude) *
        (latitude - currentLatitude)) /
        (previousLatitude - currentLatitude) +
      currentLongitude;

    if (longitude < intersectionLongitude) {
      isInside = !isInside;
    }
  }

  return isInside;
}

/**
 * Determines whether a town lies within one polygon while respecting holes.
 */
function isTownInPolygon(
  town: TownQuizTown,
  polygon: PolygonCoordinates,
): boolean {
  const outerRing = polygon[0];

  if (
    !outerRing ||
    !isPointInRing(town.longitude, town.latitude, outerRing)
  ) {
    return false;
  }

  for (
    let ringIndex = 1;
    ringIndex < polygon.length;
    ringIndex += 1
  ) {
    if (
      isPointInRing(town.longitude, town.latitude, polygon[ringIndex])
    ) {
      return false;
    }
  }

  return true;
}

/* -------------------------------------------------------------------------- */
/* Polygon-component proximity                                                */
/* -------------------------------------------------------------------------- */

/**
 * Determines whether two polygon components are geographically close enough to
 * belong to the same mainland camera cluster.
 *
 * Exterior-ring vertices are compared geodesically. Country-page geometry is
 * sufficiently detailed for this lightweight proximity test, and the function
 * exits immediately when a qualifying pair is found.
 */
function arePolygonsWithinDistance(
  firstPolygon: PolygonCoordinates,
  secondPolygon: PolygonCoordinates,
  maximumDistanceKm: number,
): boolean {
  const firstRing = getPolygonOuterRing(firstPolygon);

  const secondRing = getPolygonOuterRing(secondPolygon);

  for (const firstPosition of firstRing) {
    for (const secondPosition of secondRing) {
      const distanceKm = getCoordinateDistanceKm(
        firstPosition[1],
        firstPosition[0],
        secondPosition[1],
        secondPosition[0],
      );

      if (distanceKm <= maximumDistanceKm) {
        return true;
      }
    }
  }

  return false;
}

/* -------------------------------------------------------------------------- */
/* Camera polygon classification                                              */
/* -------------------------------------------------------------------------- */

/**
 * Selects a mainland polygon cluster.
 *
 * The largest component forms the initial cluster. Remaining components are
 * repeatedly checked against every already-selected component.
 *
 * Because the process repeats until no more polygons can be added, geographic
 * chains remain intact:
 *
 * mainland -> nearby island A -> nearby island B
 */
function getMainlandCameraPolygons(
  polygons: PolygonCoordinates[],
  largestPolygonIndex: number,
): PolygonCoordinates[] {
  const selectedIndices = new Set<number>([largestPolygonIndex]);

  let addedPolygon = true;

  while (addedPolygon) {
    addedPolygon = false;

    for (
      let candidateIndex = 0;
      candidateIndex < polygons.length;
      candidateIndex += 1
    ) {
      if (selectedIndices.has(candidateIndex)) {
        continue;
      }

      const candidatePolygon = polygons[candidateIndex];

      const isNearSelectedCluster = Array.from(selectedIndices).some(
        (selectedIndex) =>
          arePolygonsWithinDistance(
            candidatePolygon,
            polygons[selectedIndex],
            MAINLAND_COMPONENT_MAX_DISTANCE_KM,
          ),
      );

      if (!isNearSelectedCluster) {
        continue;
      }

      selectedIndices.add(candidateIndex);

      addedPolygon = true;
    }
  }

  return Array.from(selectedIndices)
    .sort((firstIndex, secondIndex) => firstIndex - secondIndex)
    .map((index) => polygons[index]);
}

/**
 * Selects useful populated polygons for a geographically dispersed
 * archipelago.
 *
 * The largest polygon is always retained. Every additional polygon containing
 * at least one quiz town is also retained.
 */
function getArchipelagoCameraPolygons(
  polygons: PolygonCoordinates[],
  largestPolygonIndex: number,
  towns: TownQuizTown[],
): PolygonCoordinates[] {
  const selectedPolygons: PolygonCoordinates[] = [];

  for (let index = 0; index < polygons.length; index += 1) {
    const polygon = polygons[index];

    if (index === largestPolygonIndex) {
      selectedPolygons.push(polygon);

      continue;
    }

    const containsQuizTown = towns.some((town) =>
      isTownInPolygon(town, polygon),
    );

    if (containsQuizTown) {
      selectedPolygons.push(polygon);
    }
  }

  return selectedPolygons;
}

/**
 * Classifies a country's multipart geography and returns the polygon components
 * that should determine its initial map camera.
 */
function getCameraPolygonSelection(
  geometry: CountryGeometry,
  towns: TownQuizTown[],
): CameraPolygonSelection {
  const polygons = getPolygonComponents(geometry);

  if (polygons.length === 0) {
    throw new Error(
      "Country geometry contains no polygon components.",
    );
  }

  const polygonAreas = polygons.map(getApproximatePolygonAreaKm2);

  let largestPolygonIndex = 0;

  for (let index = 1; index < polygonAreas.length; index += 1) {
    if (polygonAreas[index] > polygonAreas[largestPolygonIndex]) {
      largestPolygonIndex = index;
    }
  }

  const totalArea = polygonAreas.reduce(
    (total, area) => total + area,
    0,
  );

  const largestPolygonArea = polygonAreas[largestPolygonIndex];

  /*
   * Degenerate or extremely tiny geometry should still behave predictably.
   */
  const largestPolygonFraction =
    totalArea > 0 ? largestPolygonArea / totalArea : 1;

  const isMainlandOriented =
    largestPolygonFraction >= MAINLAND_LARGEST_POLYGON_FRACTION;

  const selectedPolygons = isMainlandOriented
    ? getMainlandCameraPolygons(polygons, largestPolygonIndex)
    : getArchipelagoCameraPolygons(
        polygons,
        largestPolygonIndex,
        towns,
      );

  return {
    polygons: selectedPolygons,

    cameraSource: isMainlandOriented
      ? "geometry-mainland"
      : "geometry-archipelago",

    totalPolygonCount: polygons.length,

    selectedPolygonCount: selectedPolygons.length,

    largestPolygonFraction,
  };
}

/* -------------------------------------------------------------------------- */
/* Date-line-aware bounds                                                     */
/* -------------------------------------------------------------------------- */

/**
 * Finds the smallest circular longitude interval containing all supplied
 * longitudes.
 *
 * The largest empty longitude gap is discarded, leaving the smallest arc that
 * contains the country's selected geography.
 */
function getLongitudeBounds(longitudes: number[]): {
  centerLongitude: number;

  longitudeSpan: number;
} {
  if (longitudes.length === 0) {
    throw new Error(
      "Cannot calculate longitude bounds from an empty coordinate set.",
    );
  }

  if (longitudes.length === 1) {
    return {
      centerLongitude: normalizeLongitude(longitudes[0]),

      longitudeSpan: 0,
    };
  }

  const normalizedLongitudes = longitudes
    .map(normalizePositiveLongitude)
    .sort((first, second) => first - second);

  let largestGap = Number.NEGATIVE_INFINITY;

  let largestGapStartIndex = 0;

  for (
    let index = 0;
    index < normalizedLongitudes.length;
    index += 1
  ) {
    const currentLongitude = normalizedLongitudes[index];

    const nextIndex = (index + 1) % normalizedLongitudes.length;

    const nextLongitude =
      nextIndex === 0
        ? normalizedLongitudes[0] + 360
        : normalizedLongitudes[nextIndex];

    const gap = nextLongitude - currentLongitude;

    if (gap > largestGap) {
      largestGap = gap;

      largestGapStartIndex = index;
    }
  }

  const intervalStart =
    normalizedLongitudes[
      (largestGapStartIndex + 1) % normalizedLongitudes.length
    ];

  const longitudeSpan = Math.max(0, 360 - largestGap);

  const centerLongitude = normalizeLongitude(
    intervalStart + longitudeSpan / 2,
  );

  return {
    centerLongitude,

    longitudeSpan,
  };
}

/**
 * Calculates geographic bounds from arbitrary coordinate positions.
 */
function getGeographicBoundsFromPositions(
  positions: Position[],
): GeographicBounds {
  if (positions.length === 0) {
    throw new Error(
      "Cannot calculate geographic bounds from an empty coordinate set.",
    );
  }

  const longitudes = positions.map((position) => position[0]);

  const latitudes = positions.map((position) => position[1]);

  const { centerLongitude, longitudeSpan } =
    getLongitudeBounds(longitudes);

  return {
    centerLongitude,

    longitudeSpan,

    minimumLatitude: Math.min(...latitudes),

    maximumLatitude: Math.max(...latitudes),
  };
}

/**
 * Calculates camera bounds from selected country polygon components.
 */
function getGeographicBoundsFromPolygons(
  polygons: PolygonCoordinates[],
): GeographicBounds {
  const positions: Position[] = [];

  for (const polygon of polygons) {
    positions.push(...getPolygonOuterRing(polygon));
  }

  return getGeographicBoundsFromPositions(positions);
}

/**
 * Calculates fallback camera bounds from all generated quiz towns.
 *
 * All towns participate because this fallback exists specifically for countries
 * lacking usable boundary geometry; unlike scoring, the camera should attempt
 * to show the full known quiz footprint.
 */
function getGeographicBoundsFromTowns(
  towns: TownQuizTown[],
): GeographicBounds {
  const positions: Position[] = towns.map((town) => [
    town.longitude,
    town.latitude,
  ]);

  return getGeographicBoundsFromPositions(positions);
}

/* -------------------------------------------------------------------------- */
/* Web Mercator camera calculations                                           */
/* -------------------------------------------------------------------------- */

/**
 * Converts latitude to normalized Web Mercator Y.
 */
function latitudeToMercatorY(latitude: number): number {
  const clampedLatitude = clamp(latitude, -85.051129, 85.051129);

  const latitudeRadians = degreesToRadians(clampedLatitude);

  return (
    (1 -
      Math.log(
        Math.tan(latitudeRadians) + 1 / Math.cos(latitudeRadians),
      ) /
        Math.PI) /
    2
  );
}

/**
 * Converts normalized Web Mercator Y back into geographic latitude.
 */
function mercatorYToLatitude(mercatorY: number): number {
  const mercatorRadians = Math.PI * (1 - 2 * mercatorY);

  return radiansToDegrees(Math.atan(Math.sinh(mercatorRadians)));
}

/**
 * Generates a MapLibre center and zoom that comfortably frames supplied
 * geographic bounds.
 */
function getInitialView(
  bounds: GeographicBounds,
): GeneratedTownCountryConfig["initialView"] {
  const xSpan = Math.max(bounds.longitudeSpan / 360, Number.EPSILON);

  const northY = latitudeToMercatorY(bounds.maximumLatitude);

  const southY = latitudeToMercatorY(bounds.minimumLatitude);

  const ySpan = Math.max(southY - northY, Number.EPSILON);

  const availableWidth =
    REFERENCE_VIEWPORT_WIDTH * VIEWPORT_CONTENT_FRACTION;

  const availableHeight =
    REFERENCE_VIEWPORT_HEIGHT * VIEWPORT_CONTENT_FRACTION;

  const horizontalZoom = Math.log2(
    availableWidth / (MAPLIBRE_TILE_SIZE * xSpan),
  );

  const verticalZoom = Math.log2(
    availableHeight / (MAPLIBRE_TILE_SIZE * ySpan),
  );

  const zoom = clamp(
    Math.min(horizontalZoom, verticalZoom),
    MIN_INITIAL_ZOOM,
    MAX_INITIAL_ZOOM,
  );

  /*
   * Use the visual midpoint in Web Mercator space rather than the arithmetic
   * mean latitude. This keeps high-latitude countries visually centered.
   */
  const centerMercatorY = (northY + southY) / 2;

  const centerLatitude = mercatorYToLatitude(centerMercatorY);

  return {
    center: [
      Number(bounds.centerLongitude.toFixed(4)),

      Number(centerLatitude.toFixed(4)),
    ],

    zoom: Number(zoom.toFixed(2)),
  };
}

/* -------------------------------------------------------------------------- */
/* Country configuration generation                                           */
/* -------------------------------------------------------------------------- */

/**
 * Generates one country's complete town quiz configuration.
 *
 * Scoring always uses the existing town-based algorithm.
 *
 * Camera generation prefers country geometry and falls back to the complete
 * town distribution when no matching country-page feature exists.
 */
function generateCountryConfig(
  countryId: string,
  towns: TownQuizTown[],
  feature: CountryFeature | undefined,
): {
  config: GeneratedTownCountryConfig;

  diagnostics: CountryDiagnostics;
} {
  if (towns.length === 0) {
    throw new Error(`${countryId} contains no generated towns.`);
  }

  const { coreTownCount, maxErrorKm } = getMaxErrorKm(towns);

  let cameraSource: CameraSource;

  let bounds: GeographicBounds;

  let selectedPolygonCount: number | null = null;

  let totalPolygonCount: number | null = null;

  let largestPolygonFraction: number | null = null;

  if (feature?.geometry) {
    const selection = getCameraPolygonSelection(
      feature.geometry,
      towns,
    );

    cameraSource = selection.cameraSource;

    selectedPolygonCount = selection.selectedPolygonCount;

    totalPolygonCount = selection.totalPolygonCount;

    largestPolygonFraction = selection.largestPolygonFraction;

    bounds = getGeographicBoundsFromPolygons(selection.polygons);
  } else {
    cameraSource = "town-fallback";

    bounds = getGeographicBoundsFromTowns(towns);
  }

  const initialView = getInitialView(bounds);

  return {
    config: {
      initialView,

      maxErrorKm,
    },

    diagnostics: {
      countryId,

      totalTownCount: towns.length,

      coreTownCount,

      maxErrorKm,

      cameraSource,

      selectedPolygonCount,

      totalPolygonCount,

      largestPolygonFraction,

      centerLongitude: initialView.center[0],

      centerLatitude: initialView.center[1],

      longitudeSpan: bounds.longitudeSpan,

      latitudeSpan: bounds.maximumLatitude - bounds.minimumLatitude,

      zoom: initialView.zoom,
    },
  };
}

/* -------------------------------------------------------------------------- */
/* File loading                                                               */
/* -------------------------------------------------------------------------- */

/**
 * Loads one generated runtime town dataset.
 */
function loadTownData(filePath: string): TownQuizData {
  const rawData = fs.readFileSync(filePath, "utf8");

  const parsedData = JSON.parse(rawData) as TownQuizData;

  if (!Array.isArray(parsedData.towns)) {
    throw new Error(`Invalid town quiz data: ${filePath}`);
  }

  return parsedData;
}

/**
 * Loads GeoPedia's country-page GeoJSON.
 */
function loadCountryGeoJson(): CountryFeatureCollection {
  const rawData = fs.readFileSync(COUNTRY_GEOJSON_PATH, "utf8");

  const parsedData = JSON.parse(rawData) as CountryFeatureCollection;

  if (
    parsedData.type !== "FeatureCollection" ||
    !Array.isArray(parsedData.features)
  ) {
    throw new Error(
      `Invalid country-page GeoJSON: ${COUNTRY_GEOJSON_PATH}`,
    );
  }

  return parsedData;
}

/* -------------------------------------------------------------------------- */
/* Generated TypeScript output                                                */
/* -------------------------------------------------------------------------- */

/**
 * Serializes every generated town configuration into GeoPedia runtime source.
 */
function createOutputSource(
  configurations: Map<string, GeneratedTownCountryConfig>,
): string {
  const configLines = Array.from(configurations.entries())
    .sort(([firstCountryId], [secondCountryId]) =>
      firstCountryId.localeCompare(secondCountryId),
    )
    .map(([countryId, config]) => {
      const [longitude, latitude] = config.initialView.center;

      return `  ${JSON.stringify(countryId)}: {
    initialView: {
      center: [${longitude}, ${latitude}],
      zoom: ${config.initialView.zoom},
    },
    maxErrorKm: ${config.maxErrorKm},
  },`;
    })
    .join("\n");

  return `/**
 * Defines country-specific map presentation and scoring configuration for
 * GeoPedia's town quizzes.
 *
 * This file is generated by:
 *
 * scripts/generate/world/generateTownCountryConfigs.ts
 *
 * Do not manually edit generated values here. Modify the generator and
 * regenerate this file instead.
 */

export type TownCountryConfig = {
  initialView: {
    center: [number, number];
    zoom: number;
  };

  maxErrorKm: number;
};

const townCountryConfigs: Record<string, TownCountryConfig> = {
${configLines}
};

/**
 * Returns the generated town quiz configuration for a country.
 *
 * @param countryId - GeoPedia's lowercase three-letter country identifier.
 * @returns The country's configuration when one exists.
 */
export function getTownCountryConfig(
  countryId: string,
): TownCountryConfig | undefined {
  return townCountryConfigs[
    countryId.toLowerCase()
  ];
}

/**
 * Determines whether a generated town quiz configuration exists.
 *
 * @param countryId - GeoPedia's lowercase three-letter country identifier.
 */
export function hasTownCountryConfig(
  countryId: string,
): boolean {
  return (
    getTownCountryConfig(
      countryId,
    ) !== undefined
  );
}
`;
}

/* -------------------------------------------------------------------------- */
/* Diagnostics                                                                */
/* -------------------------------------------------------------------------- */

/**
 * Prints camera/scoring diagnostics for every generated country.
 */
function printDiagnostics(diagnostics: CountryDiagnostics[]): void {
  console.table(
    diagnostics.map((country) => ({
      country: country.countryId,

      towns: country.totalTownCount,

      core: country.coreTownCount,

      source: country.cameraSource,

      polygons:
        country.selectedPolygonCount === null ||
        country.totalPolygonCount === null
          ? "-"
          : `${country.selectedPolygonCount}/${country.totalPolygonCount}`,

      largest:
        country.largestPolygonFraction === null
          ? "-"
          : Number((country.largestPolygonFraction * 100).toFixed(1)),

      maxErrorKm: country.maxErrorKm,

      lng: country.centerLongitude,

      lat: country.centerLatitude,

      lngSpan: Number(country.longitudeSpan.toFixed(1)),

      latSpan: Number(country.latitudeSpan.toFixed(1)),

      zoom: country.zoom,
    })),
  );
}

/* -------------------------------------------------------------------------- */
/* Main                                                                       */
/* -------------------------------------------------------------------------- */

/**
 * Generates town configurations for every available runtime town dataset.
 */
function main(): void {
  if (!fs.existsSync(TOWN_DATA_DIRECTORY)) {
    throw new Error(
      `Town data directory does not exist: ${TOWN_DATA_DIRECTORY}`,
    );
  }

  if (!fs.existsSync(COUNTRY_GEOJSON_PATH)) {
    throw new Error(
      `Country GeoJSON does not exist: ${COUNTRY_GEOJSON_PATH}`,
    );
  }

  const countryGeoJson = loadCountryGeoJson();

  const countryFeatures = createCountryFeatureLookup(countryGeoJson);

  console.log(
    `Loaded ${countryFeatures.size} identifiable country-page features.`,
  );

  const townFiles = fs
    .readdirSync(TOWN_DATA_DIRECTORY)
    .filter((fileName) => fileName.endsWith(".json"))
    .sort();

  const configurations = new Map<
    string,
    GeneratedTownCountryConfig
  >();

  const diagnostics: CountryDiagnostics[] = [];

  const fallbackCountryIds: string[] = [];

  for (const fileName of townFiles) {
    const countryId = path.basename(fileName, ".json").toLowerCase();

    const townData = loadTownData(
      path.join(TOWN_DATA_DIRECTORY, fileName),
    );

    const feature = countryFeatures.get(countryId);

    if (!feature?.geometry) {
      fallbackCountryIds.push(countryId);
    }

    const generated = generateCountryConfig(
      countryId,
      townData.towns,
      feature,
    );

    configurations.set(countryId, generated.config);

    diagnostics.push(generated.diagnostics);
  }

  printDiagnostics(diagnostics);

  if (fallbackCountryIds.length > 0) {
    console.log("");

    console.log("Countries using town-based camera fallback:");

    console.log(fallbackCountryIds.join(", "));
  }

  fs.mkdirSync(path.dirname(OUTPUT_PATH), {
    recursive: true,
  });

  fs.writeFileSync(
    OUTPUT_PATH,
    createOutputSource(configurations),
    "utf8",
  );

  console.log("");

  console.log(
    `Generated ${configurations.size} town country configurations.`,
  );

  console.log(`Output: ${OUTPUT_PATH}`);
}

main();
