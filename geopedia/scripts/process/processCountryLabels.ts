import fs from "node:fs";
import path from "node:path";

import area from "@turf/area";
import booleanPointInPolygon from "@turf/boolean-point-in-polygon";
import type {
  Feature,
  FeatureCollection,
  MultiPolygon,
  Point,
  Polygon,
} from "geojson";

/**
 * Country polygon properties stored in GeoPedia's canonical world-country
 * dataset.
 */
type CountryProperties = {
  name: string;
  iso_a2: string | null;
  iso_a3: string;
  continent?: string;
  region?: string;
  subregion?: string;
};

/**
 * Canonical country polygon feature.
 */
type CountryFeature = Feature<
  Polygon | MultiPolygon,
  CountryProperties
>;

/**
 * Raw MapTiler country-label anchor collected from the base-map vector tiles.
 */
type MapTilerCountryAnchor = {
  name: string;
  iso_a2: string | null;
  rank: number | null;
  longitude: number;
  latitude: number;
};

/**
 * Properties written to GeoPedia's generated country-label GeoJSON.
 */
type CountryLabelProperties = {
  name: string;

  iso_a2: string | null;

  iso_a3: string;

  /**
   * Geographic area of the canonical country polygon in square kilometers.
   *
   * Area is retained for diagnostics but does not currently control country
   * label visibility.
   */
  areaKm2: number;

  /**
   * Cartographic rank provided by MapTiler's country-label feature.
   *
   * Lower ranks represent higher-priority country labels.
   */
  rank: number | null;

  /**
   * Integer zoom at which the country label becomes eligible for placement.
   *
   * GeoPedia derives this primarily from MapTiler's country-label rank so the
   * resulting hierarchy more closely follows the base map's country labeling.
   */
  countryLabelMinZoom: number;

  /**
   * Integer zoom at which the country label stops being eligible for placement.
   *
   * Country labels provide broad geographic context at lower zooms, then
   * disappear as local settlement labels become more useful.
   */
  countryLabelMaxZoom: number;

  /**
   * Integer zoom at which national-capital labels may begin appearing.
   *
   * Capitals currently appear one zoom level after their country label.
   */
  capitalMinZoom: number;
};

/**
 * Generated country-label point feature.
 */
type CountryLabelFeature = Feature<Point, CountryLabelProperties>;

const PROJECT_ROOT = process.cwd();

const COUNTRIES_PATH = path.join(
  PROJECT_ROOT,
  "public",
  "data",
  "geojson",
  "world",
  "countries.geojson",
);

const MAPTILER_ANCHORS_PATH = path.join(
  PROJECT_ROOT,
  "data",
  "raw",
  "maptiler",
  "country-label-anchors.json",
);

const OUTPUT_PATH = path.join(
  PROJECT_ROOT,
  "public",
  "data",
  "geojson",
  "world",
  "country-labels.geojson",
);

/**
 * Earliest country-label zoom supported by GeoPedia's contextual map.
 */
const COUNTRY_LABEL_MIN_ZOOM = 1;

/**
 * Latest country-label zoom used for the lowest-priority country labels.
 */
const COUNTRY_LABEL_MAX_ZOOM = 6;

/**
 * Number of integer zoom levels between a country label and its national
 * capital labels.
 */
const CAPITAL_ZOOM_OFFSET = 1;

/**
 * Latest initial zoom assigned to a national-capital label.
 */
const CAPITAL_MAX_ZOOM = 7;

/**
 * Reads and parses a JSON file.
 *
 * @param filePath - Absolute path to the JSON file.
 */
function readJson<T>(filePath: string): T {
  return JSON.parse(fs.readFileSync(filePath, "utf8")) as T;
}

/**
 * Clamps a numeric value into an inclusive range.
 */
function clamp(
  value: number,
  minimum: number,
  maximum: number,
): number {
  return Math.min(maximum, Math.max(minimum, value));
}

/**
 * Normalizes longitude to the conventional [-180, 180] range.
 */
function normalizeLongitude(longitude: number): number {
  let normalized = longitude;

  while (normalized > 180) {
    normalized -= 360;
  }

  while (normalized < -180) {
    normalized += 360;
  }

  return normalized;
}

/**
 * Converts MapTiler's country-label rank into GeoPedia's integer country-label
 * zoom tier.
 *
 * MapTiler rank is intentionally the primary signal here. GeoPedia already
 * uses MapTiler's carefully selected anchor coordinates, and this mapping also
 * preserves more of the base map's original country-label priority.
 *
 * The tiers are intentionally aggressive because country names are primary
 * geographic context and should generally be present before dense settlement
 * labels appear.
 */
function calculateCountryLabelMinZoom(rank: number | null): number {
  switch (rank) {
    case 1:
      return 1;

    case 2:
      return 2;

    case 3:
      return 3;

    case 4:
      return 4;

    case 5:
      return 5;

    case 6:
      return 6;

    default:
      return 4;
  }
}

function calculateCountryLabelMaxZoom(rank: number | null): number {
  switch (rank) {
    case 1:
      return 6;

    case 2:
      return 7;

    case 3:
      return 7;

    case 4:
      return 8;

    case 5:
      return 8;

    case 6:
      return 9;

    default:
      return 8;
  }
}

/**
 * Calculates the national-capital minimum zoom from the country's final zoom.
 *
 * Capitals currently become eligible one integer zoom after their country
 * label. This preserves a simple hierarchy while we evaluate the rank-based
 * country-label system visually.
 */
function calculateCapitalMinZoom(
  countryLabelMinZoom: number,
): number {
  return clamp(
    countryLabelMinZoom + CAPITAL_ZOOM_OFFSET,
    COUNTRY_LABEL_MIN_ZOOM,
    CAPITAL_MAX_ZOOM,
  );
}

/**
 * Returns every canonical country polygon containing the supplied anchor.
 */
function findContainingCountries(
  anchor: MapTilerCountryAnchor,
  countries: CountryFeature[],
): CountryFeature[] {
  const point: Feature<Point> = {
    type: "Feature",

    properties: {},

    geometry: {
      type: "Point",

      coordinates: [
        normalizeLongitude(anchor.longitude),
        anchor.latitude,
      ],
    },
  };

  return countries.filter((country) =>
    booleanPointInPolygon(point, country),
  );
}

/**
 * Finds the most specific canonical polygon containing a MapTiler anchor.
 *
 * If multiple polygons contain the anchor, the smallest matching polygon is
 * preferred so enclaves and microstates are not automatically swallowed by a
 * larger surrounding country.
 */
function findCountryForAnchor(
  anchor: MapTilerCountryAnchor,
  countries: CountryFeature[],
): CountryFeature | null {
  const matches = findContainingCountries(anchor, countries);

  if (matches.length === 0) {
    return null;
  }

  if (matches.length === 1) {
    return matches[0];
  }

  return matches.reduce((smallest, candidate) =>
    area(candidate) < area(smallest) ? candidate : smallest,
  );
}

/**
 * Attempts to match a MapTiler anchor directly against GeoPedia's canonical
 * ISO-2 country code.
 *
 * The code is trusted only when it exactly matches a canonical GeoPedia code.
 * This avoids relying on MapTiler's known legacy/non-standard ISO-like values.
 */
function findCountryByMapTilerCode(
  anchor: MapTilerCountryAnchor,
  countries: CountryFeature[],
): CountryFeature | null {
  if (!anchor.iso_a2) {
    return null;
  }

  return (
    countries.find(
      (country) => country.properties.iso_a2 === anchor.iso_a2,
    ) ?? null
  );
}

/**
 * Resolves a MapTiler country-label anchor to GeoPedia's canonical country.
 *
 * Exact canonical ISO-2 matches are preferred because MapTiler's visual anchor
 * for tiny countries can occasionally lie slightly outside the canonical
 * polygon. Spatial containment is used as the fallback.
 */
function resolveCountryForAnchor(
  anchor: MapTilerCountryAnchor,
  countries: CountryFeature[],
): CountryFeature | null {
  const codeCountry = findCountryByMapTilerCode(anchor, countries);

  if (codeCountry) {
    return codeCountry;
  }

  return findCountryForAnchor(anchor, countries);
}

/**
 * Generates GeoPedia-owned country-label points using MapTiler's country-label
 * anchors and ranks.
 */
function processCountryLabels(): void {
  console.log("Processing GeoPedia country labels...");

  const countryCollection =
    readJson<
      FeatureCollection<Polygon | MultiPolygon, CountryProperties>
    >(COUNTRIES_PATH);

  const countries = countryCollection.features;

  const anchors = readJson<MapTilerCountryAnchor[]>(
    MAPTILER_ANCHORS_PATH,
  );

  console.log(`Country polygons: ${countries.length}`);

  console.log(`MapTiler anchors: ${anchors.length}`);

  const outputFeatures: CountryLabelFeature[] = [];

  const unmatchedAnchors: MapTilerCountryAnchor[] = [];

  const codeMismatches: Array<{
    mapTilerName: string;
    countryName: string;
    mapTilerCode: string | null;
    geoPediaCode: string | null;
    geoPediaId: string;
  }> = [];

  for (const anchor of anchors) {
    const country = resolveCountryForAnchor(anchor, countries);

    if (!country) {
      unmatchedAnchors.push(anchor);

      continue;
    }

    if (anchor.iso_a2 !== country.properties.iso_a2) {
      codeMismatches.push({
        mapTilerName: anchor.name,

        countryName: country.properties.name,

        mapTilerCode: anchor.iso_a2,

        geoPediaCode: country.properties.iso_a2,

        geoPediaId: country.properties.iso_a3,
      });
    }

    const areaKm2 = area(country) / 1_000_000;

    const countryLabelMinZoom = clamp(
      calculateCountryLabelMinZoom(anchor.rank),
      COUNTRY_LABEL_MIN_ZOOM,
      COUNTRY_LABEL_MAX_ZOOM,
    );

    const countryLabelMaxZoom = calculateCountryLabelMaxZoom(
      anchor.rank,
    );

    const capitalMinZoom = calculateCapitalMinZoom(
      countryLabelMinZoom,
    );

    outputFeatures.push({
      type: "Feature",

      id: country.properties.iso_a3,

      properties: {
        name: country.properties.name,

        iso_a2: country.properties.iso_a2,

        iso_a3: country.properties.iso_a3,

        areaKm2: Math.round(areaKm2),

        rank: anchor.rank,

        countryLabelMinZoom,

        countryLabelMaxZoom,

        capitalMinZoom,
      },

      geometry: {
        type: "Point",

        coordinates: [
          normalizeLongitude(anchor.longitude),
          anchor.latitude,
        ],
      },
    });
  }

  outputFeatures.sort((a, b) => {
    const zoomDifference =
      a.properties.countryLabelMinZoom -
      b.properties.countryLabelMinZoom;

    if (zoomDifference !== 0) {
      return zoomDifference;
    }

    return b.properties.areaKm2 - a.properties.areaKm2;
  });

  const outputCollection: FeatureCollection<
    Point,
    CountryLabelProperties
  > = {
    type: "FeatureCollection",

    features: outputFeatures,
  };

  fs.mkdirSync(path.dirname(OUTPUT_PATH), {
    recursive: true,
  });

  fs.writeFileSync(
    OUTPUT_PATH,
    `${JSON.stringify(outputCollection)}\n`,
    "utf8",
  );

  console.log(
    `Matched country anchors: ${outputFeatures.length}/${anchors.length}`,
  );

  console.log(
    `Unmatched country anchors: ${unmatchedAnchors.length}`,
  );

  if (unmatchedAnchors.length > 0) {
    console.table(
      unmatchedAnchors.map((anchor) => ({
        name: anchor.name,

        mapTilerCode: anchor.iso_a2,

        longitude: anchor.longitude,

        latitude: anchor.latitude,
      })),
    );
  }

  console.log(
    `MapTiler/GeoPedia country-code mismatches: ${codeMismatches.length}`,
  );

  if (codeMismatches.length > 0) {
    console.table(codeMismatches);
  }

  console.log("\nCountry-label zoom preview:");

  console.table(
    outputFeatures.map((feature) => ({
      name: feature.properties.name,

      areaKm2: feature.properties.areaKm2,

      rank: feature.properties.rank,

      countryZoom: feature.properties.countryLabelMinZoom,

      capitalZoom: feature.properties.capitalMinZoom,
    })),
  );

  const distribution = new Map<number, number>();

  for (const feature of outputFeatures) {
    const zoom = feature.properties.countryLabelMinZoom;

    distribution.set(zoom, (distribution.get(zoom) ?? 0) + 1);
  }

  console.log("\nCountry-label minimum-zoom distribution:");

  console.table(
    [...distribution.entries()]
      .sort(([zoomA], [zoomB]) => zoomA - zoomB)
      .map(([zoom, count]) => ({
        zoom,
        count,
      })),
  );

  console.log(`\nWrote ${OUTPUT_PATH}`);
}

processCountryLabels();
