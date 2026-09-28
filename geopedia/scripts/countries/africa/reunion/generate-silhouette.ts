/**
 * Generates GeoPedia's country silhouette SVG for Réunion.
 *
 * Réunion is intentionally generated separately because it is not represented
 * as its own feature in GeoPedia's `country-pages.geojson`, even though it is
 * present in the broader worldwide country dataset and has enough GeoGuessr
 * coverage to warrant a town quiz.
 *
 * Input:
 *
 *   public/data/global/countries/geojson/world-countries.geojson
 *
 * Output:
 *
 *   public/data/global/countries/silhouettes/reu.svg
 *
 * The generated SVG:
 *
 * - Finds the GeoJSON feature whose three-letter country code is REU.
 * - Supports Polygon and MultiPolygon geometry.
 * - Projects longitude/latitude directly into a normalized SVG view box.
 * - Preserves polygon holes.
 * - Adds padding around the silhouette.
 * - Uses `currentColor` so the application can control the silhouette color
 *   through CSS when the SVG is embedded appropriately.
 *
 * This is intended as a small one-off project utility rather than part of the
 * normal world-data generation pipeline.
 */

import fs from "node:fs";
import path from "node:path";

/* -------------------------------------------------------------------------- */
/* Paths                                                                      */
/* -------------------------------------------------------------------------- */

const INPUT_PATH =
  "public/data/global/countries/geojson/world-countries.geojson";

const OUTPUT_PATH =
  "public/data/global/countries/silhouettes/reu.svg";

/* -------------------------------------------------------------------------- */
/* Generation settings                                                        */
/* -------------------------------------------------------------------------- */

/**
 * SVG coordinate space.
 */
const VIEWBOX_SIZE = 1000;

/**
 * Empty space retained around the country's geographic bounds.
 */
const PADDING = 60;

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
/* Country identification                                                     */
/* -------------------------------------------------------------------------- */

/**
 * Property names commonly used by GeoPedia's worldwide country datasets for
 * three-letter ISO/country identifiers.
 */
const COUNTRY_CODE_PROPERTIES = [
  "id",

  "iso_a3",
  "ISO_A3",

  "adm0_a3",
  "ADM0_A3",

  "sov_a3",
  "SOV_A3",

  "gu_a3",
  "GU_A3",
] as const;

/**
 * Determines whether one feature represents Réunion.
 */
function isReunionFeature(feature: CountryFeature): boolean {
  const properties = feature.properties;

  if (properties) {
    for (const propertyName of COUNTRY_CODE_PROPERTIES) {
      const value = properties[propertyName];

      if (
        typeof value === "string" &&
        value.trim().toUpperCase() === "REU"
      ) {
        return true;
      }
    }

    /*
     * Name fallback protects against datasets where Réunion is present but its
     * ISO-3 code is stored under a property name not listed above.
     */
    for (const value of Object.values(properties)) {
      if (
        typeof value === "string" &&
        (value.trim().toLowerCase() === "réunion" ||
          value.trim().toLowerCase() === "reunion")
      ) {
        return true;
      }
    }
  }

  if (
    feature.id !== undefined &&
    String(feature.id).trim().toUpperCase() === "REU"
  ) {
    return true;
  }

  return false;
}

/* -------------------------------------------------------------------------- */
/* Geometry helpers                                                           */
/* -------------------------------------------------------------------------- */

/**
 * Converts Polygon and MultiPolygon geometry into one common polygon array.
 */
function getPolygons(
  geometry: CountryGeometry,
): PolygonCoordinates[] {
  if (geometry.type === "Polygon") {
    return [geometry.coordinates];
  }

  return geometry.coordinates;
}

/**
 * Returns every position contained in a country's polygon geometry.
 */
function getPositions(polygons: PolygonCoordinates[]): Position[] {
  const positions: Position[] = [];

  for (const polygon of polygons) {
    for (const ring of polygon) {
      positions.push(...ring);
    }
  }

  return positions;
}

/* -------------------------------------------------------------------------- */
/* SVG projection                                                             */
/* -------------------------------------------------------------------------- */

type GeographicBounds = {
  minimumLongitude: number;
  maximumLongitude: number;

  minimumLatitude: number;
  maximumLatitude: number;
};

/**
 * Calculates the country's complete geographic bounds.
 */
function getBounds(positions: Position[]): GeographicBounds {
  if (positions.length === 0) {
    throw new Error("Réunion geometry contains no positions.");
  }

  const longitudes = positions.map((position) => position[0]);

  const latitudes = positions.map((position) => position[1]);

  return {
    minimumLongitude: Math.min(...longitudes),

    maximumLongitude: Math.max(...longitudes),

    minimumLatitude: Math.min(...latitudes),

    maximumLatitude: Math.max(...latitudes),
  };
}

/**
 * Creates a projection that scales Réunion proportionally into the SVG
 * coordinate system.
 *
 * Latitude is inverted because SVG Y coordinates increase downward.
 */
function createProjector(
  bounds: GeographicBounds,
): (position: Position) => [number, number] {
  const longitudeSpan = Math.max(
    bounds.maximumLongitude - bounds.minimumLongitude,
    Number.EPSILON,
  );

  const latitudeSpan = Math.max(
    bounds.maximumLatitude - bounds.minimumLatitude,
    Number.EPSILON,
  );

  const drawableSize = VIEWBOX_SIZE - PADDING * 2;

  /*
   * Use one scale for both axes so the island's actual proportions are
   * preserved rather than stretching it to fill the SVG.
   */
  const scale = Math.min(
    drawableSize / longitudeSpan,

    drawableSize / latitudeSpan,
  );

  const projectedWidth = longitudeSpan * scale;

  const projectedHeight = latitudeSpan * scale;

  const offsetX = (VIEWBOX_SIZE - projectedWidth) / 2;

  const offsetY = (VIEWBOX_SIZE - projectedHeight) / 2;

  return (position: Position): [number, number] => {
    const [longitude, latitude] = position;

    const x = offsetX + (longitude - bounds.minimumLongitude) * scale;

    const y = offsetY + (bounds.maximumLatitude - latitude) * scale;

    return [Number(x.toFixed(2)), Number(y.toFixed(2))];
  };
}

/* -------------------------------------------------------------------------- */
/* SVG path generation                                                        */
/* -------------------------------------------------------------------------- */

/**
 * Converts one GeoJSON linear ring into SVG path commands.
 */
function createRingPath(
  ring: LinearRing,
  project: (position: Position) => [number, number],
): string {
  if (ring.length === 0) {
    return "";
  }

  const [firstX, firstY] = project(ring[0]);

  const commands: string[] = [`M ${firstX} ${firstY}`];

  for (let index = 1; index < ring.length; index += 1) {
    const [x, y] = project(ring[index]);

    commands.push(`L ${x} ${y}`);
  }

  commands.push("Z");

  return commands.join(" ");
}

/**
 * Converts all polygon components and holes into one compound SVG path.
 */
function createCountryPath(
  polygons: PolygonCoordinates[],
  project: (position: Position) => [number, number],
): string {
  return polygons
    .flatMap((polygon) =>
      polygon.map((ring) => createRingPath(ring, project)),
    )
    .filter(Boolean)
    .join(" ");
}

/* -------------------------------------------------------------------------- */
/* Main                                                                       */
/* -------------------------------------------------------------------------- */

/**
 * Finds Réunion and writes its normalized SVG silhouette.
 */
function main(): void {
  if (!fs.existsSync(INPUT_PATH)) {
    throw new Error(`Country GeoJSON does not exist: ${INPUT_PATH}`);
  }

  const collection = JSON.parse(
    fs.readFileSync(INPUT_PATH, "utf8"),
  ) as CountryFeatureCollection;

  if (
    collection.type !== "FeatureCollection" ||
    !Array.isArray(collection.features)
  ) {
    throw new Error(`Invalid country GeoJSON: ${INPUT_PATH}`);
  }

  const reunionFeature = collection.features.find(isReunionFeature);

  if (!reunionFeature) {
    throw new Error(
      "Could not find Réunion (REU) in world-countries.geojson.",
    );
  }

  if (!reunionFeature.geometry) {
    throw new Error("Réunion feature has no geometry.");
  }

  const polygons = getPolygons(reunionFeature.geometry);

  const positions = getPositions(polygons);

  const bounds = getBounds(positions);

  const project = createProjector(bounds);

  const pathData = createCountryPath(polygons, project);

  if (!pathData) {
    throw new Error("Could not generate Réunion SVG path.");
  }

  const svg = `<svg
  xmlns="http://www.w3.org/2000/svg"
  viewBox="0 0 ${VIEWBOX_SIZE} ${VIEWBOX_SIZE}"
  role="img"
  aria-label="Réunion silhouette"
>
  <path
    d="${pathData}"
    fill="currentColor"
    fill-rule="evenodd"
    clip-rule="evenodd"
  />
</svg>
`;

  fs.mkdirSync(path.dirname(OUTPUT_PATH), {
    recursive: true,
  });

  fs.writeFileSync(OUTPUT_PATH, svg, "utf8");

  console.log(`Generated Réunion silhouette: ${OUTPUT_PATH}`);

  console.log(`Polygon components: ${polygons.length}`);

  console.log(
    `Bounds: ${bounds.minimumLongitude}, ${bounds.minimumLatitude} -> ${bounds.maximumLongitude}, ${bounds.maximumLatitude}`,
  );
}

main();
