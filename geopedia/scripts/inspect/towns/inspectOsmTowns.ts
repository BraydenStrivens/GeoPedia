/**
 * Inspects OpenStreetMap populated-place nodes from a PBF extract.
 *
 * This script is intentionally diagnostic only. It lets GeoPedia evaluate
 * OSM settlement classifications and population coverage before building
 * the permanent town-processing pipeline.
 */

import fs from "node:fs";
import { createRequire } from "node:module";

/**
 * osm-pbf-parser does not provide TypeScript declarations, so it is loaded
 * through Node's CommonJS compatibility layer.
 */
const require = createRequire(import.meta.url);

const OsmPbfParser =
  require("osm-pbf-parser") as new () => NodeJS.ReadWriteStream;

/**
 * Colorado OSM extract being inspected.
 */
const INPUT_PATH = "data/raw/osm/us-260825.osm";

/**
 * Towns whose OSM records we specifically want to inspect.
 */
const TARGET_NAMES = new Set([
  "Craig",
  "Montrose",
  "Hamilton",
  "Denver",
  "Colorado Springs",
  "Silverton",
  "Hugo",
]);

/**
 * OSM settlement classifications that currently look relevant to GeoPedia.
 *
 * Suburbs are intentionally retained because they may eventually receive
 * their own label styling and higher minimum zoom.
 */
const RELEVANT_PLACE_TYPES = new Set([
  "city",
  "town",
  "village",
  "hamlet",
  "isolated_dwelling",
  "suburb",
]);

/**
 * OSM tags useful to the future GeoPedia town system.
 */
const INTERESTING_TAGS = [
  "name",
  "place",
  "population",
  "capital",
  "admin_level",
  "wikidata",
  "wikipedia",
  "official_name",
  "short_name",
] as const;

type OsmItem = {
  id?: number | string;
  type?: string;
  lat?: number;
  lon?: number;
  tags?: Record<string, string>;
};

type TargetResult = {
  id: number | string | undefined;
  type: string | undefined;
  latitude: number | undefined;
  longitude: number | undefined;
  tags: Record<string, string>;
};

type PopulationStats = {
  total: number;
  withPopulation: number;
};

/**
 * Matching records for the towns we're manually inspecting.
 */
const targetResults: TargetResult[] = [];

/**
 * Counts every named OSM place classification.
 */
const placeCounts = new Map<string, number>();

/**
 * Tracks population coverage for each place classification.
 */
const placePopulationStats = new Map<string, PopulationStats>();

/**
 * Total named place nodes, regardless of whether their place type will
 * eventually be included in GeoPedia.
 */
let totalNamedPlaces = 0;

/**
 * Number of named place nodes belonging to one of our currently relevant
 * settlement classifications.
 */
let totalRelevantPlaces = 0;

/**
 * Keeps only tags useful to this inspection.
 */
function getInterestingTags(
  tags: Record<string, string>,
): Record<string, string> {
  const result: Record<string, string> = {};

  for (const tagName of INTERESTING_TAGS) {
    const value = tags[tagName];

    if (value !== undefined) {
      result[tagName] = value;
    }
  }

  return result;
}

const parser = new OsmPbfParser();

fs.createReadStream(INPUT_PATH)
  .pipe(parser)
  .on("data", (items: OsmItem[]) => {
    for (const item of items) {
      const tags = item.tags;

      if (!tags) {
        continue;
      }

      const place = tags.place;
      const name = tags.name;

      /*
       * We're currently interested in named place nodes.
       *
       * This is the "named-place loop" I referred to previously:
       * everything below this condition runs once for every named
       * OSM place node in the Colorado extract.
       */
      if (item.type !== "node" || !place || !name) {
        continue;
      }

      totalNamedPlaces++;

      /*
       * Count each place classification.
       */
      placeCounts.set(place, (placeCounts.get(place) ?? 0) + 1);

      /*
       * Track how often each place classification has a population tag.
       */
      const populationStats = placePopulationStats.get(place) ?? {
        total: 0,
        withPopulation: 0,
      };

      populationStats.total++;

      if (tags.population !== undefined) {
        populationStats.withPopulation++;
      }

      placePopulationStats.set(place, populationStats);

      /*
       * Count classifications we're currently considering for GeoPedia's
       * town-label dataset.
       */
      if (RELEVANT_PLACE_TYPES.has(place)) {
        totalRelevantPlaces++;
      }

      /*
       * Save full diagnostic information for our manually selected towns.
       */
      if (TARGET_NAMES.has(name)) {
        targetResults.push({
          id: item.id,
          type: item.type,
          latitude: item.lat,
          longitude: item.lon,
          tags: getInterestingTags(tags),
        });
      }
    }
  })
  .on("end", () => {
    console.log(
      `Named OSM place nodes: ${totalNamedPlaces.toLocaleString()}`,
    );

    console.log(
      `Relevant settlement nodes: ${totalRelevantPlaces.toLocaleString()}`,
    );

    console.log("");

    console.log("PLACE CLASSIFICATIONS");
    console.log("---------------------");

    console.table(
      Array.from(placeCounts.entries())
        .sort((first, second) => second[1] - first[1])
        .map(([place, count]) => ({
          place,
          count,
          included: RELEVANT_PLACE_TYPES.has(place),
        })),
    );

    console.log("");

    console.log("POPULATION COVERAGE");
    console.log("-------------------");

    console.table(
      Array.from(placePopulationStats.entries())
        .filter(([place]) => RELEVANT_PLACE_TYPES.has(place))
        .map(([place, stats]) => ({
          place,
          total: stats.total,
          withPopulation: stats.withPopulation,
          withoutPopulation: stats.total - stats.withPopulation,
          coverage: `${(
            (stats.withPopulation / stats.total) *
            100
          ).toFixed(1)}%`,
        }))
        .sort((first, second) => second.total - first.total),
    );

    console.log("");

    console.log("TARGET TOWNS");
    console.log("------------");

    for (const result of targetResults) {
      console.log("");

      console.log(JSON.stringify(result, null, 2));
    }
  })
  .on("error", (error: Error) => {
    console.error("Failed to inspect OSM PBF:", error);

    process.exitCode = 1;
  });
