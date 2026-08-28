/**
 * Inspects a processed GeoPedia town GeoJSON file.
 *
 * This utility is intended for validating generated town datasets before they
 * are consumed by the application.
 */

import fs from "node:fs";

import type { ProcessedTownFeatureCollection } from "../../process/towns/townTypes";

/**
 * Processed town dataset to inspect.
 */
const INPUT_PATH = "public/data/geojson/usa/towns.geojson";

/**
 * Reads and parses the generated GeoJSON.
 */
const featureCollection = JSON.parse(
  fs.readFileSync(INPUT_PATH, "utf8"),
) as ProcessedTownFeatureCollection;

/**
 * Displays a concise dataset summary.
 */
console.log(
  `Total towns: ${featureCollection.features.length.toLocaleString()}`,
);

console.log("");

console.log("Top 30 towns by country rank:");

console.table(
  featureCollection.features
    .slice()
    .sort(
      (firstFeature, secondFeature) =>
        firstFeature.properties.countryRank -
        secondFeature.properties.countryRank,
    )
    .slice(0, 30)
    .map((feature) => ({
      rank: feature.properties.countryRank,

      name: feature.properties.name,

      admin1: feature.properties.admin1Code ?? "",

      population: feature.properties.population,

      featureCode: feature.properties.featureCode,

      geonameId: feature.properties.geonameId,
    })),
);
