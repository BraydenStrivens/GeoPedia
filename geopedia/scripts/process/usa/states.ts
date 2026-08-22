import fs from "fs";
import type { GeoJSON } from "geojson";
import path from "path";

type RawGeoJSONFeature = {
  type: "Feature";
  geometry: GeoJSON.Geometry;
  properties: {
    name?: string;
    postal?: string;
    fips?: string;
    region?: string;
  };
};

type RawGeoJSONFeatureCollection = {
  type: "FeatureCollection";
  features: RawGeoJSONFeature[];
};

type GeoJSONFeature = {
  type: "Feature";
  id: string;
  properties: {
    name: string;
    abbreviation?: string;
    fips?: string;
    region?: string;
  };
  geometry: GeoJSON.Geometry;
};

type GeoJSONFeatureCollection = {
  type: "FeatureCollection";
  features: GeoJSONFeature[];
};

const inputPath = path.join(process.cwd(), "data/raw/us-states.geojson");

const outputPath = path.join(
  process.cwd(),
  "data/processed/us-states.geojson",
);

const publicOutputPath = path.join(
  process.cwd(),
  "public/data/us-states.geojson",
);

console.log("Processing US States...");

const rawData = fs.readFileSync(inputPath, "utf8");

const source = JSON.parse(rawData) as RawGeoJSONFeatureCollection;

console.log(`Found ${source.features.length} features.`);

if (source.features.length !== 50) {
  throw new Error(
    `Expected 50 states but found ${source.features.length} features`,
  );
}

const names = source.features.map((feature) => feature.properties.name);

const missingNames = names.filter((name) => !name);

if (missingNames.length > 0) {
  throw new Error(`${missingNames.length} features are missing a name.`);
}

const uniqueNames = new Set(names);

if (uniqueNames.size !== 50) {
  throw new Error(
    `Expected 50 unique state names but found ${uniqueNames.size}.`,
  );
}

const processedFeatures = source.features.map((feature) => {
  const name = feature.properties.name;

  return {
    type: "Feature" as const,

    id: name,

    properties: {
      name,
      abbreviation: feature.properties.postal ?? undefined,
      fips: feature.properties.fips ?? undefined,
      region: feature.properties.region ?? undefined,
    },

    geometry: feature.geometry,
  };
});

const processed: RawGeoJSONFeatureCollection = {
  type: "FeatureCollection",
  features: processedFeatures,
};

fs.mkdirSync(path.dirname(outputPath), { recursive: true });

fs.mkdirSync(path.dirname(publicOutputPath), { recursive: true });

const output = JSON.stringify(processed, null, 2);

fs.writeFileSync(outputPath, output);

fs.writeFileSync(publicOutputPath, output);

console.log("✓ Found exactly 50 states.");
console.log("✓ All states have names.");
console.log("✓ All state names are unique.");
console.log("✓ Added MapLibre feature IDs.");
console.log("✓ Removed unused properties.");
console.log("");
console.log(`✓ Saved processed data to:`);
console.log(`  ${outputPath}`);
console.log("");
console.log(`✓ Saved public copy to:`);
console.log(`  ${publicOutputPath}`);
