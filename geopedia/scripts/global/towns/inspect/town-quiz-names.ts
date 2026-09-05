/**
 * Inspects GeoPedia town-quiz naming data against the processed OSM town-label
 * dataset.
 *
 * This script is intended to help design the town quiz's English/local-language
 * name system before changing any runtime schemas or generators.
 *
 * It compares:
 *
 * - `public/data/global/towns/countries/{countryId}.json`
 *     The current runtime quiz name generated primarily from GeoNames.
 *
 * - `public/data/global/towns/towns.geojson`
 *     The processed OSM local `name` and optional `latinName`.
 *
 * The inspection focuses on countries where English/international and locally
 * displayed settlement names are especially useful to compare:
 *
 * - Austria
 * - Germany
 * - Italy
 * - Russia
 * - Ukraine
 * - Japan
 * - Bangladesh
 * - Greece
 * - Georgia
 * - Armenia
 * - India
 *
 * Only a small number of the most populous quiz towns from each country are
 * inspected. Matching is geographic rather than name-based so differences such
 * as `Vienna` / `Wien` do not prevent a successful comparison.
 *
 * The worldwide town GeoJSON is streamed because it can be too large to load
 * into memory as one JSON object.
 *
 * Run with:
 *
 *   npx tsx scripts/inspect/towns/inspectTownQuizNames.ts
 */

import fs from "node:fs";
import { createRequire } from "node:module";
import path from "node:path";

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

/**
 * Generated town-quiz runtime data.
 */
const TOWN_QUIZ_DIRECTORY = "public/data/towns";

/**
 * Processed worldwide OSM settlement labels.
 */
const OSM_TOWNS_PATH = "public/data/global/towns/towns.geojson";

/* -------------------------------------------------------------------------- */
/* Inspection settings                                                        */
/* -------------------------------------------------------------------------- */

/**
 * Countries selected because they exercise several important naming cases:
 *
 * - Latin local names differing from English.
 * - Cyrillic.
 * - Greek.
 * - Georgian.
 * - Armenian.
 * - Japanese.
 * - Bengali.
 * - India's multilingual edge case.
 */
const COUNTRIES = [
  {
    id: "aut",
    name: "Austria",
  },
  {
    id: "deu",
    name: "Germany",
  },
  {
    id: "ita",
    name: "Italy",
  },
  {
    id: "rus",
    name: "Russia",
  },
  {
    id: "ukr",
    name: "Ukraine",
  },
  {
    id: "jpn",
    name: "Japan",
  },
  {
    id: "bgd",
    name: "Bangladesh",
  },
  {
    id: "grc",
    name: "Greece",
  },
  {
    id: "geo",
    name: "Georgia",
  },
  {
    id: "arm",
    name: "Armenia",
  },
  {
    id: "ind",
    name: "India",
  },
] as const;

/**
 * Number of highest-population quiz towns inspected per country.
 *
 * Fifteen is large enough to catch naming patterns without creating an
 * overwhelming console table.
 */
const TOWNS_PER_COUNTRY = 15;

/**
 * Geographic spatial-index size.
 *
 * 0.1 degrees is roughly 11 km of latitude and matches the general scale used
 * elsewhere in GeoPedia's town-processing tools.
 */
const SPATIAL_CELL_SIZE = 0.1;

/**
 * Maximum geographic separation accepted between a generated quiz town and an
 * OSM city/town.
 *
 * The actual generator normally produces very close matches. Five kilometers
 * leaves enough room for different representative city-center coordinates
 * while avoiding unrelated nearby settlements.
 */
const MAX_MATCH_DISTANCE_KM = 5;

/**
 * Mean Earth radius used by the haversine distance calculation.
 */
const EARTH_RADIUS_KM = 6371;

/* -------------------------------------------------------------------------- */
/* Types                                                                      */
/* -------------------------------------------------------------------------- */

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

type OsmTownProperties = {
  name?: unknown;

  latinName?: unknown;

  place?: unknown;
};

type OsmTownFeature = {
  type?: unknown;

  geometry?: {
    type?: unknown;

    coordinates?: unknown;
  };

  properties?: OsmTownProperties | null;
};

type StreamArrayItem<T> = {
  key: number;

  value: T;
};

/**
 * One quiz town selected for inspection.
 */
type InspectionTarget = {
  countryId: string;

  countryName: string;

  town: TownQuizTown;
};

/**
 * Best matching OSM settlement found for an inspection target.
 */
type OsmTownMatch = {
  name: string;

  latinName: string | undefined;

  place: string;

  latitude: number;
  longitude: number;

  distanceKm: number;
};

/* -------------------------------------------------------------------------- */
/* Geographic helpers                                                         */
/* -------------------------------------------------------------------------- */

/**
 * Converts degrees to radians.
 */
function degreesToRadians(degrees: number): number {
  return (degrees * Math.PI) / 180;
}

/**
 * Calculates great-circle distance between two geographic coordinates.
 */
function getDistanceKm(
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

/* -------------------------------------------------------------------------- */
/* Spatial index helpers                                                      */
/* -------------------------------------------------------------------------- */

/**
 * Creates the spatial-cell key containing one coordinate.
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
 * Creates every spatial-cell key that could contain a nearby target.
 */
function getNearbyCellKeys(
  latitude: number,
  longitude: number,
): string[] {
  const latitudeCell = Math.floor(latitude / SPATIAL_CELL_SIZE);

  const longitudeCell = Math.floor(longitude / SPATIAL_CELL_SIZE);

  const keys: string[] = [];

  for (
    let latitudeOffset = -1;
    latitudeOffset <= 1;
    latitudeOffset += 1
  ) {
    for (
      let longitudeOffset = -1;
      longitudeOffset <= 1;
      longitudeOffset += 1
    ) {
      keys.push(
        `${latitudeCell + latitudeOffset}:${
          longitudeCell + longitudeOffset
        }`,
      );
    }
  }

  return keys;
}

/**
 * Builds a lightweight geographic lookup from spatial cell to inspection
 * targets.
 */
function buildTargetSpatialIndex(
  targets: InspectionTarget[],
): Map<string, InspectionTarget[]> {
  const index = new Map<string, InspectionTarget[]>();

  for (const target of targets) {
    const key = getSpatialCellKey(
      target.town.latitude,
      target.town.longitude,
    );

    const existing = index.get(key);

    if (existing) {
      existing.push(target);
    } else {
      index.set(key, [target]);
    }
  }

  return index;
}

/* -------------------------------------------------------------------------- */
/* Quiz-town loading                                                          */
/* -------------------------------------------------------------------------- */

/**
 * Loads the largest quiz towns for every country selected for inspection.
 */
function loadInspectionTargets(): InspectionTarget[] {
  const targets: InspectionTarget[] = [];

  for (const country of COUNTRIES) {
    const filePath = path.join(
      TOWN_QUIZ_DIRECTORY,
      `${country.id}.json`,
    );

    if (!fs.existsSync(filePath)) {
      console.warn(`Skipping ${country.name}: missing ${filePath}`);

      continue;
    }

    const data = JSON.parse(
      fs.readFileSync(filePath, "utf8"),
    ) as TownQuizData;

    if (!Array.isArray(data.towns)) {
      throw new Error(`Invalid town quiz data: ${filePath}`);
    }

    /*
     * populationRank should already represent this ordering, but explicitly
     * sorting keeps the inspection deterministic.
     */
    const towns = [...data.towns]
      .sort(
        (firstTown, secondTown) =>
          firstTown.populationRank - secondTown.populationRank,
      )
      .slice(0, TOWNS_PER_COUNTRY);

    for (const town of towns) {
      targets.push({
        countryId: country.id,

        countryName: country.name,

        town,
      });
    }
  }

  return targets;
}

/* -------------------------------------------------------------------------- */
/* OSM matching                                                               */
/* -------------------------------------------------------------------------- */

/**
 * Streams the worldwide town GeoJSON and finds the nearest OSM city/town for
 * every selected runtime quiz town.
 *
 * Matching intentionally uses coordinates rather than names because detecting
 * differences such as Vienna/Wien is the purpose of this inspection.
 */
async function findOsmMatches(
  targets: InspectionTarget[],
): Promise<Map<string, OsmTownMatch>> {
  const targetIndex = buildTargetSpatialIndex(targets);

  const matches = new Map<string, OsmTownMatch>();

  const pipeline = fs
    .createReadStream(OSM_TOWNS_PATH)
    .pipe(parser.asStream())
    .pipe(
      pick.asStream({
        filter: "features",
      }),
    )
    .pipe(streamArray.asStream());

  let processedFeatureCount = 0;

  for await (const item of pipeline as unknown as AsyncIterable<
    StreamArrayItem<OsmTownFeature>
  >) {
    processedFeatureCount += 1;

    const feature = item.value;

    if (feature.geometry?.type !== "Point") {
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

    const name = feature.properties?.name;

    const place = feature.properties?.place;

    /*
     * Town quizzes themselves only accept OSM city/town classifications, so
     * applying the same semantic restriction avoids accidentally matching a
     * nearby suburb or village.
     */
    if (
      typeof name !== "string" ||
      (place !== "city" && place !== "town")
    ) {
      continue;
    }

    const latinNameValue = feature.properties?.latinName;

    const latinName =
      typeof latinNameValue === "string" ? latinNameValue : undefined;

    const candidateTargets: InspectionTarget[] = [];

    for (const key of getNearbyCellKeys(latitude, longitude)) {
      const bucket = targetIndex.get(key);

      if (bucket) {
        candidateTargets.push(...bucket);
      }
    }

    for (const target of candidateTargets) {
      const distanceKm = getDistanceKm(
        target.town.latitude,
        target.town.longitude,

        latitude,
        longitude,
      );

      if (distanceKm > MAX_MATCH_DISTANCE_KM) {
        continue;
      }

      const targetKey = `${target.countryId}:${target.town.id}`;

      const existing = matches.get(targetKey);

      if (existing && existing.distanceKm <= distanceKm) {
        continue;
      }

      matches.set(targetKey, {
        name,

        latinName,

        place,

        latitude,
        longitude,

        distanceKm,
      });
    }

    if (processedFeatureCount % 250_000 === 0) {
      console.log(
        `Scanned ${processedFeatureCount.toLocaleString()} OSM town features...`,
      );
    }
  }

  return matches;
}

/* -------------------------------------------------------------------------- */
/* Diagnostics                                                                */
/* -------------------------------------------------------------------------- */

/**
 * Prints one table per country so name differences are easy to inspect.
 */
function printResults(
  targets: InspectionTarget[],
  matches: Map<string, OsmTownMatch>,
): void {
  for (const country of COUNTRIES) {
    const countryTargets = targets.filter(
      (target) => target.countryId === country.id,
    );

    if (countryTargets.length === 0) {
      continue;
    }

    console.log("");

    console.log(`${country.name.toUpperCase()} (${country.id})`);

    console.log(
      "-".repeat(country.name.length + country.id.length + 3),
    );

    console.table(
      countryTargets.map((target) => {
        const targetKey = `${target.countryId}:${target.town.id}`;

        const match = matches.get(targetKey);

        const osmName = match?.name;

        const latinName = match?.latinName;

        return {
          rank: target.town.populationRank,

          quizName: target.town.name,

          osmLocal: osmName ?? "(no match)",

          osmLatin: latinName ?? "",

          differs: osmName ? target.town.name !== osmName : "",

          distanceKm: match
            ? Number(match.distanceKm.toFixed(2))
            : "",
        };
      }),
    );
  }
}

/* -------------------------------------------------------------------------- */
/* Main                                                                       */
/* -------------------------------------------------------------------------- */

/**
 * Runs the naming inspection.
 */
async function main(): Promise<void> {
  if (!fs.existsSync(OSM_TOWNS_PATH)) {
    throw new Error(
      `OSM town GeoJSON does not exist: ${OSM_TOWNS_PATH}`,
    );
  }

  const targets = loadInspectionTargets();

  if (targets.length === 0) {
    throw new Error("No town quiz inspection targets were loaded.");
  }

  console.log(`Loaded ${targets.length} quiz towns for inspection.`);

  console.log(`Scanning ${OSM_TOWNS_PATH}...`);

  const matches = await findOsmMatches(targets);

  console.log("");

  console.log(
    `Matched ${matches.size} / ${targets.length} quiz towns.`,
  );

  printResults(targets, matches);
}

void main().catch((error) => {
  console.error("");

  console.error("Town-name inspection failed:", error);

  process.exitCode = 1;
});
