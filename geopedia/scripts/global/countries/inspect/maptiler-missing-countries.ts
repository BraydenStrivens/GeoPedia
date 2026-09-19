/**
 * Inspects MapTiler place features around GeoPedia countries that were not
 * discovered as MapTiler `class: "country"` features during the broader
 * country-name coverage scan.
 *
 * This diagnostic focuses on the remaining exceptional countries/territories
 * and examines nearby MapTiler place features at a fixed zoom. It helps
 * determine whether an unresolved GeoPedia entity exists in MapTiler under a
 * different place class, ISO-2 code, name, or geographic representation.
 *
 * To keep the output manageable, the script reports:
 * - every place feature using the unresolved GeoPedia ISO-2 code;
 * - country, island, state, and province features in the searched tiles.
 *
 * Duplicate MapTiler features are collapsed using their relevant identifying
 * properties before being printed.
 *
 * This is an exploratory inspection script only. It does not generate
 * application data or modify GeoPedia's source datasets.
 *
 * The MapTiler API key is read from NEXT_PUBLIC_MAPTILER_KEY in .env.local and
 * is never written to the output.
 */

import fs from "node:fs";
import path from "node:path";

import { VectorTile } from "@mapbox/vector-tile";
import { PbfReader } from "pbf";

const ENV_PATH = path.resolve(".env.local");

const WORLD_COUNTRIES_PATH = path.resolve(
  "public/data/global/countries/geojson/world-countries.geojson",
);

const INSPECTION_ZOOM = 8;
const TILE_PADDING = 1;

const UNRESOLVED_ISO_A2 = [
  "BV",
  "BQ",
  "CX",
  "CC",
  "GF",
  "GP",
  "MQ",
  "YT",
  "RE",
  "SJ",
] as const;

const RELEVANT_PLACE_CLASSES = new Set([
  "country",
  "island",
  "state",
  "province",
]);

type Position = [number, number];

type PolygonCoordinates = Position[][];

type MultiPolygonCoordinates = Position[][][];

type CountryGeometry =
  | {
      type: "Polygon";
      coordinates: PolygonCoordinates;
    }
  | {
      type: "MultiPolygon";
      coordinates: MultiPolygonCoordinates;
    };

type GeoPediaCountryProperties = {
  name?: unknown;
  iso_a2?: unknown;
  iso_a3?: unknown;
};

type GeoPediaCountryFeature = {
  type?: unknown;
  properties?: GeoPediaCountryProperties;
  geometry?: CountryGeometry | null;
};

type GeoPediaWorldCountries = {
  type?: unknown;
  features?: GeoPediaCountryFeature[];
};

type Bounds = {
  minLongitude: number;
  minLatitude: number;
  maxLongitude: number;
  maxLatitude: number;
};

type GeoPediaCountry = {
  name: string;
  isoA2: string;
  isoA3: string;
  bounds: Bounds;
};

type PlaceProperties = Record<string, unknown> & {
  class?: string;
  iso_a2?: string;
  name?: string;
  "name:en"?: string;
  "name:latin"?: string;
  "name:nonlatin"?: string;
  rank?: number;
  wikidata?: string;
};

type TileCoordinate = {
  zoom: number;
  x: number;
  y: number;
};

type InspectedPlace = {
  class: string | undefined;
  iso_a2: string | undefined;
  name: string | undefined;
  english: string | undefined;
  latin: string | undefined;
  nonlatin: string | undefined;
  rank: number | undefined;
  wikidata: string | undefined;
};

function loadMapTilerApiKey(): string {
  if (!fs.existsSync(ENV_PATH)) {
    throw new Error(`Missing environment file: ${ENV_PATH}`);
  }

  const envContents = fs.readFileSync(ENV_PATH, "utf8");

  const match = envContents.match(
    /^NEXT_PUBLIC_MAPTILER_KEY\s*=\s*["']?([^"' \r\n]+)["']?\s*$/m,
  );

  if (!match?.[1]) {
    throw new Error(
      "NEXT_PUBLIC_MAPTILER_KEY was not found in .env.local.",
    );
  }

  return match[1];
}

function getGeometryPositions(geometry: CountryGeometry): Position[] {
  if (geometry.type === "Polygon") {
    return geometry.coordinates.flat();
  }

  return geometry.coordinates.flat(2);
}

function getGeometryBounds(geometry: CountryGeometry): Bounds {
  const positions = getGeometryPositions(geometry);

  if (positions.length === 0) {
    throw new Error("Country geometry contains no coordinates.");
  }

  let minLongitude = Number.POSITIVE_INFINITY;
  let minLatitude = Number.POSITIVE_INFINITY;
  let maxLongitude = Number.NEGATIVE_INFINITY;
  let maxLatitude = Number.NEGATIVE_INFINITY;

  for (const [longitude, latitude] of positions) {
    minLongitude = Math.min(minLongitude, longitude);
    minLatitude = Math.min(minLatitude, latitude);
    maxLongitude = Math.max(maxLongitude, longitude);
    maxLatitude = Math.max(maxLatitude, latitude);
  }

  return {
    minLongitude,
    minLatitude,
    maxLongitude,
    maxLatitude,
  };
}

function loadUnresolvedCountries(): GeoPediaCountry[] {
  if (!fs.existsSync(WORLD_COUNTRIES_PATH)) {
    throw new Error(
      `Missing GeoPedia world-country GeoJSON: ${WORLD_COUNTRIES_PATH}`,
    );
  }

  const raw = fs.readFileSync(WORLD_COUNTRIES_PATH, "utf8");
  const parsed = JSON.parse(raw) as GeoPediaWorldCountries;

  if (!Array.isArray(parsed.features)) {
    throw new Error(
      "GeoPedia world-country GeoJSON does not contain a features array.",
    );
  }

  const unresolvedCodes = new Set<string>(UNRESOLVED_ISO_A2);

  const countries: GeoPediaCountry[] = [];

  for (let index = 0; index < parsed.features.length; index += 1) {
    const feature = parsed.features[index];
    const properties = feature.properties;
    const geometry = feature.geometry;

    if (!properties) {
      continue;
    }

    const { name, iso_a2: isoA2, iso_a3: isoA3 } = properties;

    if (typeof isoA2 !== "string" || !unresolvedCodes.has(isoA2)) {
      continue;
    }

    if (typeof name !== "string" || typeof isoA3 !== "string") {
      throw new Error(
        `GeoPedia feature ${index} for ${isoA2} is missing ` +
          "a valid name or iso_a3.",
      );
    }

    if (
      !geometry ||
      (geometry.type !== "Polygon" &&
        geometry.type !== "MultiPolygon")
    ) {
      throw new Error(
        `GeoPedia feature ${index} for ${isoA2} does not ` +
          "contain a supported Polygon or MultiPolygon geometry.",
      );
    }

    countries.push({
      name,
      isoA2,
      isoA3,
      bounds: getGeometryBounds(geometry),
    });
  }

  const foundCodes = new Set(
    countries.map((country) => country.isoA2),
  );

  const missingFromGeoJson = UNRESOLVED_ISO_A2.filter(
    (isoA2) => !foundCodes.has(isoA2),
  );

  if (missingFromGeoJson.length > 0) {
    throw new Error(
      "Could not find unresolved GeoPedia countries: " +
        missingFromGeoJson.join(", "),
    );
  }

  return countries.sort((first, second) =>
    first.name.localeCompare(second.name),
  );
}

function longitudeToTileX(longitude: number, zoom: number): number {
  const tileCount = 2 ** zoom;

  return Math.floor(((longitude + 180) / 360) * tileCount);
}

function latitudeToTileY(latitude: number, zoom: number): number {
  const tileCount = 2 ** zoom;

  const clampedLatitude = Math.max(
    -85.05112878,
    Math.min(85.05112878, latitude),
  );

  const latitudeRadians = (clampedLatitude * Math.PI) / 180;

  return Math.floor(
    ((1 - Math.asinh(Math.tan(latitudeRadians)) / Math.PI) / 2) *
      tileCount,
  );
}

function clampTileIndex(value: number, zoom: number): number {
  const maxIndex = 2 ** zoom - 1;

  return Math.max(0, Math.min(maxIndex, value));
}

function getTilesForBounds(
  bounds: Bounds,
  zoom: number,
  padding: number,
): TileCoordinate[] {
  const minX = longitudeToTileX(bounds.minLongitude, zoom);

  const maxX = longitudeToTileX(bounds.maxLongitude, zoom);

  const minY = latitudeToTileY(bounds.maxLatitude, zoom);

  const maxY = latitudeToTileY(bounds.minLatitude, zoom);

  const tiles: TileCoordinate[] = [];

  for (
    let x = clampTileIndex(minX - padding, zoom);
    x <= clampTileIndex(maxX + padding, zoom);
    x += 1
  ) {
    for (
      let y = clampTileIndex(minY - padding, zoom);
      y <= clampTileIndex(maxY + padding, zoom);
      y += 1
    ) {
      tiles.push({
        zoom,
        x,
        y,
      });
    }
  }

  return tiles;
}

async function downloadTile(
  zoom: number,
  x: number,
  y: number,
  apiKey: string,
): Promise<VectorTile> {
  const tileUrl =
    `https://api.maptiler.com/tiles/v3/${zoom}/${x}/${y}.pbf?key=` +
    encodeURIComponent(apiKey);

  const response = await fetch(tileUrl);

  if (!response.ok) {
    throw new Error(
      `MapTiler request failed for ${zoom}/${x}/${y}: ` +
        `${response.status} ${response.statusText}`,
    );
  }

  const arrayBuffer = await response.arrayBuffer();

  return new VectorTile(new PbfReader(new Uint8Array(arrayBuffer)));
}

function shouldIncludePlace(
  properties: PlaceProperties,
  targetIsoA2: string,
): boolean {
  if (properties.iso_a2 === targetIsoA2) {
    return true;
  }

  return (
    typeof properties.class === "string" &&
    RELEVANT_PLACE_CLASSES.has(properties.class)
  );
}

function toInspectedPlace(
  properties: PlaceProperties,
): InspectedPlace {
  return {
    class: properties.class,
    iso_a2: properties.iso_a2,
    name: properties.name,
    english: properties["name:en"],
    latin: properties["name:latin"],
    nonlatin: properties["name:nonlatin"],
    rank: properties.rank,
    wikidata: properties.wikidata,
  };
}

function getPlaceKey(place: InspectedPlace): string {
  return JSON.stringify([
    place.class,
    place.iso_a2,
    place.name,
    place.english,
    place.latin,
    place.nonlatin,
    place.rank,
    place.wikidata,
  ]);
}

async function inspectCountry(
  country: GeoPediaCountry,
  apiKey: string,
): Promise<void> {
  const tiles = getTilesForBounds(
    country.bounds,
    INSPECTION_ZOOM,
    TILE_PADDING,
  );

  const placesByKey = new Map<string, InspectedPlace>();

  let placeFeatureCount = 0;

  for (const tileCoordinate of tiles) {
    const tile = await downloadTile(
      tileCoordinate.zoom,
      tileCoordinate.x,
      tileCoordinate.y,
      apiKey,
    );

    const placeLayer = tile.layers.place;

    if (!placeLayer) {
      continue;
    }

    placeFeatureCount += placeLayer.length;

    for (let index = 0; index < placeLayer.length; index += 1) {
      const feature = placeLayer.feature(index);

      const properties = feature.properties as PlaceProperties;

      if (!shouldIncludePlace(properties, country.isoA2)) {
        continue;
      }

      const place = toInspectedPlace(properties);

      placesByKey.set(getPlaceKey(place), place);
    }
  }

  const places = [...placesByKey.values()].sort((first, second) => {
    const firstMatches = first.iso_a2 === country.isoA2 ? 0 : 1;

    const secondMatches = second.iso_a2 === country.isoA2 ? 0 : 1;

    if (firstMatches !== secondMatches) {
      return firstMatches - secondMatches;
    }

    const classComparison = (first.class ?? "").localeCompare(
      second.class ?? "",
    );

    if (classComparison !== 0) {
      return classComparison;
    }

    return (first.name ?? "").localeCompare(second.name ?? "");
  });

  console.log("\n========================================");
  console.log(`${country.name} (${country.isoA2}/${country.isoA3})`);
  console.log("========================================");
  console.log(`Zoom: ${INSPECTION_ZOOM}`);
  console.log(`Tiles inspected: ${tiles.length}`);
  console.log(
    `Total place occurrences in tiles: ${placeFeatureCount}`,
  );
  console.log(`Relevant unique place features: ${places.length}`);

  const exactIsoPlaces = places.filter(
    (place) => place.iso_a2 === country.isoA2,
  );

  console.log(
    `Features using ${country.isoA2}: ` + `${exactIsoPlaces.length}`,
  );

  if (places.length === 0) {
    console.log("\nNo relevant place features found.");
    return;
  }

  console.log();

  console.table(places);
}

async function main(): Promise<void> {
  const apiKey = loadMapTilerApiKey();

  const countries = loadUnresolvedCountries();

  console.log(
    `Inspecting ${countries.length} unresolved ` +
      `GeoPedia countries at zoom ${INSPECTION_ZOOM}.`,
  );

  for (const country of countries) {
    await inspectCountry(country, apiKey);
  }
}

main().catch((error: unknown) => {
  console.error(error);
  process.exitCode = 1;
});
