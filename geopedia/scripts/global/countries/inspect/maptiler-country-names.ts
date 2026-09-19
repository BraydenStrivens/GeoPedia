/**
 * Inspects MapTiler Planet vector tiles for country-place metadata and compares
 * their coverage with GeoPedia's authoritative world-country dataset.
 *
 * The script scans every world tile from zoom 0 through GLOBAL_SCAN_MAX_ZOOM,
 * then uses the bounding boxes of unresolved GeoPedia countries to search
 * targeted tiles at TARGETED_SCAN_ZOOM.
 *
 * MapTiler country features are collected by canonical ISO-2 country code.
 * Known MapTiler-specific country-code aliases are normalized during
 * collection. When the same country occurs multiple times, properties from
 * every occurrence are merged so multilingual name metadata is not discarded
 * merely because it appears on a different tile occurrence.
 *
 * If different occurrences provide conflicting values for the same property,
 * the first encountered value is retained in the merged properties and every
 * distinct conflicting value is recorded separately for inspection.
 *
 * GeoPedia's world-countries GeoJSON remains authoritative for the set of
 * countries and their English names. MapTiler is being inspected only as a
 * potential source of local/native country-name metadata.
 *
 * The merged diagnostic output is written beneath this inspect directory in
 * output/maptiler-country-names.json. That output is exploratory inspection
 * data and should not be treated as a production source file.
 *
 * This is an exploratory inspection script only.
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

const OUTPUT_PATH = path.resolve(
  "scripts/global/countries/inspect/output/maptiler-country-names.json",
);

const GLOBAL_SCAN_MAX_ZOOM = 4;
const TARGETED_SCAN_ZOOM = 5;
const TARGETED_TILE_PADDING = 1;

/**
 * MapTiler country codes that differ from the ISO-2 codes used by GeoPedia.
 *
 * These aliases affect source interpretation only. GeoPedia's canonical
 * country identifiers remain unchanged.
 */
const MAPTILER_COUNTRY_CODE_ALIASES: Readonly<
  Record<string, string>
> = {
  GV: "GN",
  PU: "GW",
};

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

type CountryProperties = Record<string, unknown> & {
  class?: string;
  iso_a2?: string;
  name?: string;
  "name:en"?: string;
  "name:latin"?: string;
  "name:nonlatin"?: string;
};

type PropertyConflicts = Record<string, unknown[]>;

type CollectedCountry = {
  properties: CountryProperties;
  propertyConflicts: PropertyConflicts;
  rawIsoA2Codes: Set<string>;
  firstSeenZoom: number;
  lastSeenZoom: number;
  occurrences: number;
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

type TileCoordinate = {
  zoom: number;
  x: number;
  y: number;
};

type OutputCountry = {
  geoPediaName: string | null;
  iso_a2: string;
  iso_a3: string | null;
  rawMapTilerIsoA2Codes: string[];
  firstSeenZoom: number;
  lastSeenZoom: number;
  occurrences: number;
  properties: Record<string, unknown>;
  propertyConflicts: Record<string, unknown[]>;
};

/**
 * Loads the MapTiler API key from GeoPedia's local environment file.
 */
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

/**
 * Flattens supported country geometry into coordinate positions for bounds
 * calculation.
 */
function getGeometryPositions(geometry: CountryGeometry): Position[] {
  if (geometry.type === "Polygon") {
    return geometry.coordinates.flat();
  }

  return geometry.coordinates.flat(2);
}

/**
 * Calculates a simple longitude/latitude bounding box for a country geometry.
 */
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

/**
 * Loads GeoPedia's authoritative country list and validates the identifiers
 * needed to compare it with MapTiler.
 */
function loadGeoPediaCountries(): GeoPediaCountry[] {
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

  const countries = parsed.features.map(
    (feature, index): GeoPediaCountry => {
      const properties = feature.properties;
      const geometry = feature.geometry;

      if (!properties) {
        throw new Error(
          `GeoPedia country feature ${index} does not contain properties.`,
        );
      }

      if (
        !geometry ||
        (geometry.type !== "Polygon" &&
          geometry.type !== "MultiPolygon")
      ) {
        throw new Error(
          `GeoPedia country feature ${index} does not contain a supported ` +
            "Polygon or MultiPolygon geometry.",
        );
      }

      const { name, iso_a2: isoA2, iso_a3: isoA3 } = properties;

      if (
        typeof name !== "string" ||
        typeof isoA2 !== "string" ||
        typeof isoA3 !== "string"
      ) {
        throw new Error(
          `GeoPedia country feature ${index} is missing a valid name, ` +
            "iso_a2, or iso_a3.",
        );
      }

      return {
        name,
        isoA2,
        isoA3,
        bounds: getGeometryBounds(geometry),
      };
    },
  );

  const seenIsoA2 = new Set<string>();

  for (const country of countries) {
    if (seenIsoA2.has(country.isoA2)) {
      throw new Error(
        `Duplicate GeoPedia ISO-2 country code: ${country.isoA2}`,
      );
    }

    seenIsoA2.add(country.isoA2);
  }

  return countries;
}

/**
 * Converts known MapTiler-specific country codes to GeoPedia's canonical
 * ISO-2 identifiers.
 */
function canonicalizeMapTilerIsoA2(rawIsoA2: string): string {
  return MAPTILER_COUNTRY_CODE_ALIASES[rawIsoA2] ?? rawIsoA2;
}

/**
 * Tests whether two decoded vector-tile property values are equal for
 * diagnostic merging.
 */
function arePropertyValuesEqual(
  first: unknown,
  second: unknown,
): boolean {
  return JSON.stringify(first) === JSON.stringify(second);
}

/**
 * Adds a conflicting property value to the diagnostic conflict collection
 * while avoiding duplicate conflict values.
 */
function addPropertyConflict(
  conflicts: PropertyConflicts,
  propertyName: string,
  retainedValue: unknown,
  conflictingValue: unknown,
): void {
  const values =
    conflicts[propertyName] ??
    (conflicts[propertyName] = [retainedValue]);

  if (
    !values.some((value) =>
      arePropertyValuesEqual(value, conflictingValue),
    )
  ) {
    values.push(conflictingValue);
  }
}

/**
 * Merges one MapTiler country occurrence into an existing country's property
 * collection.
 *
 * Previously unseen properties are added directly. If an occurrence disagrees
 * with a retained property, the original value remains authoritative for this
 * diagnostic object and all distinct values are recorded in propertyConflicts.
 */
function mergeCountryProperties(
  country: CollectedCountry,
  incomingProperties: CountryProperties,
): void {
  for (const [propertyName, incomingValue] of Object.entries(
    incomingProperties,
  )) {
    if (!(propertyName in country.properties)) {
      country.properties[propertyName] = incomingValue;
      continue;
    }

    const retainedValue = country.properties[propertyName];

    if (!arePropertyValuesEqual(retainedValue, incomingValue)) {
      addPropertyConflict(
        country.propertyConflicts,
        propertyName,
        retainedValue,
        incomingValue,
      );
    }
  }
}

/**
 * Collects one MapTiler country feature.
 *
 * Features are grouped by canonical ISO-2 code. Every occurrence contributes
 * its properties to the merged country record so multilingual metadata spread
 * across multiple vector-tile occurrences is preserved.
 *
 * Returns the canonical ISO-2 code only when the country is first discovered.
 */
function collectCountryFeature(
  properties: CountryProperties,
  zoom: number,
  countries: Map<string, CollectedCountry>,
): string | null {
  if (properties.class !== "country") {
    return null;
  }

  const rawIsoA2 = properties.iso_a2;

  if (typeof rawIsoA2 !== "string" || rawIsoA2.length === 0) {
    return null;
  }

  const canonicalIsoA2 = canonicalizeMapTilerIsoA2(rawIsoA2);

  const existing = countries.get(canonicalIsoA2);

  if (!existing) {
    countries.set(canonicalIsoA2, {
      properties: { ...properties },
      propertyConflicts: {},
      rawIsoA2Codes: new Set([rawIsoA2]),
      firstSeenZoom: zoom,
      lastSeenZoom: zoom,
      occurrences: 1,
    });

    return canonicalIsoA2;
  }

  existing.lastSeenZoom = Math.max(existing.lastSeenZoom, zoom);
  existing.occurrences += 1;
  existing.rawIsoA2Codes.add(rawIsoA2);

  mergeCountryProperties(existing, properties);

  return null;
}

/**
 * Downloads and decodes one MapTiler Planet vector tile.
 */
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

/**
 * Converts longitude to an XYZ tile x-coordinate.
 */
function longitudeToTileX(longitude: number, zoom: number): number {
  const tileCount = 2 ** zoom;

  return Math.floor(((longitude + 180) / 360) * tileCount);
}

/**
 * Converts latitude to an XYZ tile y-coordinate.
 */
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

/**
 * Restricts a tile coordinate to the valid range for its zoom.
 */
function clampTileIndex(value: number, zoom: number): number {
  const maxIndex = 2 ** zoom - 1;

  return Math.max(0, Math.min(maxIndex, value));
}

/**
 * Returns XYZ tiles intersecting a simple country bounding box plus optional
 * surrounding tile padding.
 */
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

/**
 * Returns GeoPedia countries that have not yet been matched to a collected
 * MapTiler country feature.
 */
function getMissingCountries(
  geoPediaCountries: GeoPediaCountry[],
  mapTilerCountries: Map<string, CollectedCountry>,
): GeoPediaCountry[] {
  return geoPediaCountries.filter(
    (country) => !mapTilerCountries.has(country.isoA2),
  );
}

/**
 * Scans all MapTiler Planet tiles from zoom zero through the configured global
 * maximum and collects every country occurrence encountered.
 */
async function scanGlobalTiles(
  apiKey: string,
  countries: Map<string, CollectedCountry>,
): Promise<void> {
  for (let zoom = 0; zoom <= GLOBAL_SCAN_MAX_ZOOM; zoom += 1) {
    const tilesPerAxis = 2 ** zoom;
    const tileCount = tilesPerAxis ** 2;

    let placeFeatureCount = 0;
    let countryFeatureCount = 0;

    const countriesBeforeZoom = countries.size;

    console.log(
      `\nScanning zoom ${zoom}: ${tileCount} ` +
        `tile${tileCount === 1 ? "" : "s"}...`,
    );

    for (let x = 0; x < tilesPerAxis; x += 1) {
      for (let y = 0; y < tilesPerAxis; y += 1) {
        const tile = await downloadTile(zoom, x, y, apiKey);

        const placeLayer = tile.layers.place;

        if (!placeLayer) {
          continue;
        }

        placeFeatureCount += placeLayer.length;

        for (let index = 0; index < placeLayer.length; index += 1) {
          const feature = placeLayer.feature(index);

          const properties = feature.properties as CountryProperties;

          if (properties.class !== "country") {
            continue;
          }

          countryFeatureCount += 1;

          const rawIsoA2 = properties.iso_a2;

          if (typeof rawIsoA2 !== "string" || rawIsoA2.length === 0) {
            console.warn(
              `Country feature without ISO-2 at ` +
                `${zoom}/${x}/${y}:`,
              properties.name,
            );

            continue;
          }

          collectCountryFeature(properties, zoom, countries);
        }
      }
    }

    const addedAtZoom = countries.size - countriesBeforeZoom;

    console.log(`  Place features: ${placeFeatureCount}`);
    console.log(`  Country occurrences: ${countryFeatureCount}`);
    console.log(`  New unique countries: ${addedAtZoom}`);
    console.log(`  Total unique countries: ${countries.size}`);
  }
}

/**
 * Performs one targeted zoom scan around countries that were unresolved after
 * the global scan.
 *
 * Earlier exploration established that zoom 5 adds the remaining MapTiler
 * `country` features available through this strategy, while deeper scans did
 * not discover additional GeoPedia countries.
 */
async function scanMissingCountries(
  apiKey: string,
  geoPediaCountries: GeoPediaCountry[],
  countries: Map<string, CollectedCountry>,
): Promise<void> {
  const missingBeforeScan = getMissingCountries(
    geoPediaCountries,
    countries,
  );

  if (missingBeforeScan.length === 0) {
    console.log(
      "\nAll GeoPedia countries were found during the global scan.",
    );

    return;
  }

  const missingIsoA2BeforeScan = new Set(
    missingBeforeScan.map((country) => country.isoA2),
  );

  const tilesByKey = new Map<string, TileCoordinate>();

  for (const country of missingBeforeScan) {
    const tiles = getTilesForBounds(
      country.bounds,
      TARGETED_SCAN_ZOOM,
      TARGETED_TILE_PADDING,
    );

    for (const tile of tiles) {
      const key = `${tile.zoom}/${tile.x}/${tile.y}`;

      tilesByKey.set(key, tile);
    }
  }

  console.log(
    `\nTargeted zoom ${TARGETED_SCAN_ZOOM}: ` +
      `${missingBeforeScan.length} unresolved countries, ` +
      `${tilesByKey.size} unique tiles...`,
  );

  const newlyFound = new Set<string>();

  for (const tileCoordinate of tilesByKey.values()) {
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

    for (let index = 0; index < placeLayer.length; index += 1) {
      const feature = placeLayer.feature(index);

      const properties = feature.properties as CountryProperties;

      const addedIsoA2 = collectCountryFeature(
        properties,
        TARGETED_SCAN_ZOOM,
        countries,
      );

      if (addedIsoA2 && missingIsoA2BeforeScan.has(addedIsoA2)) {
        newlyFound.add(addedIsoA2);
      }
    }
  }

  const newlyFoundCountries = geoPediaCountries
    .filter((country) => newlyFound.has(country.isoA2))
    .map((country) => ({
      name: country.name,
      iso_a2: country.isoA2,
      iso_a3: country.isoA3,
    }))
    .sort((first, second) => first.name.localeCompare(second.name));

  const missingAfterScan = getMissingCountries(
    geoPediaCountries,
    countries,
  );

  console.log(
    `  Newly found GeoPedia countries: ` +
      `${newlyFoundCountries.length}`,
  );

  console.log(
    `  Remaining unresolved countries: ` +
      `${missingAfterScan.length}`,
  );

  if (newlyFoundCountries.length > 0) {
    console.table(newlyFoundCountries);
  }
}

/**
 * Sorts an object's property names to make generated diagnostic JSON stable
 * and easier to inspect.
 */
function sortObjectProperties(
  properties: Record<string, unknown>,
): Record<string, unknown> {
  return Object.fromEntries(
    Object.entries(properties).sort(([firstName], [secondName]) =>
      firstName.localeCompare(secondName),
    ),
  );
}

/**
 * Sorts conflict keys and their values for stable diagnostic output.
 */
function sortPropertyConflicts(
  conflicts: PropertyConflicts,
): PropertyConflicts {
  return Object.fromEntries(
    Object.entries(conflicts)
      .sort(([firstName], [secondName]) =>
        firstName.localeCompare(secondName),
      )
      .map(([propertyName, values]) => [
        propertyName,
        [...values].sort((first, second) =>
          JSON.stringify(first).localeCompare(JSON.stringify(second)),
        ),
      ]),
  );
}

/**
 * Writes all merged MapTiler country metadata to an exploratory JSON file.
 *
 * Every MapTiler property is retained so language-specific `name:*` fields can
 * be inspected before GeoPedia defines its final native-name extraction rules.
 */
function writeInspectionOutput(
  geoPediaCountries: GeoPediaCountry[],
  mapTilerCountries: Map<string, CollectedCountry>,
): void {
  const geoPediaByIsoA2 = new Map(
    geoPediaCountries.map((country) => [country.isoA2, country]),
  );

  const output: OutputCountry[] = [...mapTilerCountries.entries()]
    .map(([isoA2, country]) => {
      const geoPediaCountry = geoPediaByIsoA2.get(isoA2);

      return {
        geoPediaName: geoPediaCountry?.name ?? null,
        iso_a2: isoA2,
        iso_a3: geoPediaCountry?.isoA3 ?? null,
        rawMapTilerIsoA2Codes: [...country.rawIsoA2Codes].sort(),
        firstSeenZoom: country.firstSeenZoom,
        lastSeenZoom: country.lastSeenZoom,
        occurrences: country.occurrences,
        properties: sortObjectProperties(country.properties),
        propertyConflicts: sortPropertyConflicts(
          country.propertyConflicts,
        ),
      };
    })
    .sort((first, second) =>
      first.iso_a2.localeCompare(second.iso_a2),
    );

  fs.mkdirSync(path.dirname(OUTPUT_PATH), {
    recursive: true,
  });

  fs.writeFileSync(
    OUTPUT_PATH,
    `${JSON.stringify(output, null, 2)}\n`,
    "utf8",
  );

  console.log(
    `\nWrote merged MapTiler inspection data for ` +
      `${output.length} countries to:`,
  );

  console.log(OUTPUT_PATH);
}

/**
 * Prints GeoPedia/MapTiler ISO coverage after all configured scans.
 */
function printCoverageComparison(
  geoPediaCountries: GeoPediaCountry[],
  mapTilerCountries: Map<string, CollectedCountry>,
): void {
  const geoPediaByIsoA2 = new Map(
    geoPediaCountries.map((country) => [country.isoA2, country]),
  );

  const missingFromMapTiler = geoPediaCountries
    .filter((country) => !mapTilerCountries.has(country.isoA2))
    .map((country) => ({
      name: country.name,
      iso_a2: country.isoA2,
      iso_a3: country.isoA3,
    }))
    .sort((first, second) => first.name.localeCompare(second.name));

  const mapTilerOnly = [...mapTilerCountries.entries()]
    .filter(([isoA2]) => !geoPediaByIsoA2.has(isoA2))
    .map(([isoA2, country]) => ({
      iso_a2: isoA2,
      raw_iso_a2: [...country.rawIsoA2Codes].join(" / "),
      name: country.properties.name,
      english: country.properties["name:en"],
      latin: country.properties["name:latin"],
      nonlatin: country.properties["name:nonlatin"],
      firstZoom: country.firstSeenZoom,
    }))
    .sort((first, second) =>
      first.iso_a2.localeCompare(second.iso_a2),
    );

  const matchedCount =
    geoPediaCountries.length - missingFromMapTiler.length;

  console.log("\n========================================");
  console.log("Final GeoPedia / MapTiler coverage");
  console.log("========================================");

  console.log(`GeoPedia countries: ${geoPediaCountries.length}`);

  console.log(
    `MapTiler countries collected: ` + `${mapTilerCountries.size}`,
  );

  console.log(`Canonical ISO-2 matches: ${matchedCount}`);

  console.log(
    `GeoPedia countries still missing: ` +
      `${missingFromMapTiler.length}`,
  );

  console.log(
    `MapTiler-only canonical ISO-2 codes: ` +
      `${mapTilerOnly.length}`,
  );

  console.log("\nGeoPedia countries still missing from MapTiler:\n");

  if (missingFromMapTiler.length === 0) {
    console.log("None.");
  } else {
    console.table(missingFromMapTiler);
  }

  console.log("\nMapTiler-only canonical ISO-2 codes:\n");

  if (mapTilerOnly.length === 0) {
    console.log("None.");
  } else {
    console.table(mapTilerOnly);
  }
}

/**
 * Prints a compact summary of the merged MapTiler country records.
 */
function printCollectedCountrySummary(
  countries: Map<string, CollectedCountry>,
): void {
  const output = [...countries.entries()]
    .map(([isoA2, country]) => ({
      iso_a2: isoA2,
      raw_iso_a2: [...country.rawIsoA2Codes].join(" / "),
      name: country.properties.name,
      english: country.properties["name:en"],
      latin: country.properties["name:latin"],
      nonlatin: country.properties["name:nonlatin"],
      firstZoom: country.firstSeenZoom,
      lastZoom: country.lastSeenZoom,
      occurrences: country.occurrences,
      propertyCount: Object.keys(country.properties).length,
      conflictCount: Object.keys(country.propertyConflicts).length,
    }))
    .sort((first, second) =>
      first.iso_a2.localeCompare(second.iso_a2),
    );

  console.log("\n========================================");

  console.log(
    `Unique MapTiler countries collected: ` + `${output.length}`,
  );

  console.log("========================================\n");

  console.table(output);
}

/**
 * Runs the MapTiler country-name inspection.
 */
async function main(): Promise<void> {
  const apiKey = loadMapTilerApiKey();

  const geoPediaCountries = loadGeoPediaCountries();

  console.log(
    `Loaded ${geoPediaCountries.length} ` + "GeoPedia countries.",
  );

  const mapTilerCountries = new Map<string, CollectedCountry>();

  await scanGlobalTiles(apiKey, mapTilerCountries);

  const missingAfterGlobalScan = getMissingCountries(
    geoPediaCountries,
    mapTilerCountries,
  );

  console.log(
    `\nAfter canonicalizing MapTiler country codes, ` +
      `${missingAfterGlobalScan.length} GeoPedia countries ` +
      "remain unresolved after the global scan.",
  );

  await scanMissingCountries(
    apiKey,
    geoPediaCountries,
    mapTilerCountries,
  );

  printCollectedCountrySummary(mapTilerCountries);

  printCoverageComparison(geoPediaCountries, mapTilerCountries);

  writeInspectionOutput(geoPediaCountries, mapTilerCountries);
}

main().catch((error: unknown) => {
  console.error(error);
  process.exitCode = 1;
});
