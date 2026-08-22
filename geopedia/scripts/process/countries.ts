import fs from "fs";
import type { GeoJSON } from "geojson";
import path from "path";

type RawCountryProperties = {
  NE_ID?: number;
  NAME_EN?: string;
  NAME?: string;
  ISO_A2?: string;
  ISO_A3?: string;
  CONTINENT?: string;
  REGION_UN?: string;
  SUBREGION?: string;
};

type RawGeoJSONFeature = {
  type: "Feature";
  geometry: GeoJSON.Geometry;
  properties: RawCountryProperties;
};

type RawGeoJSONFeatureCollection = {
  type: "FeatureCollection";
  features: RawGeoJSONFeature[];
};

type CountryProperties = {
  name: string;
  iso_a2: string | null;
  iso_a3: string | null;
  continent: string | null;
  region: string | null;
  subregion: string | null;
};

type CountryFeature = {
  type: "Feature";
  id: string;
  properties: CountryProperties;
  geometry: GeoJSON.Geometry;
};

type CountryFeatureCollection = {
  type: "FeatureCollection";
  features: CountryFeature[];
};

const inputPath = path.join(process.cwd(), "data/raw/countries.geojson");

const outputPath = path.join(process.cwd(), "data/processed/countries.geojson");

const publicOutputPath = path.join(
  process.cwd(),
  "public/data/countries.geojson",
);

console.log("Processing countries...");

const rawData = fs.readFileSync(inputPath, "utf8");

const source = JSON.parse(rawData) as RawGeoJSONFeatureCollection;

console.log(`Found ${source.features.length} features.`);

const excludedNames = new Set([
  "Dhekelia",
  "Akrotiri",
  "Somaliland",
  "USNB Guantanamo Bay",
  "Brazilian I.",
  "N. Cyprus",
  "Cyprus U.N. Buffer Zone",
  "Siachen Glacier",
  "Baikonur",
  "Southern Patagonian Ice Field",
  "Bir Tawil",
  "Indian Ocean Ter.",
  "Coral Sea Is.",
  "Spratly Is.",
  "Clipperton I.",
  "Ashmore and Cartier Is.",
  "Bajo Nuevo Bank",
  "Serranilla Bank",
  "Scarborough Reef",
]);

if (source.type !== "FeatureCollection") {
  throw new Error("Expected a GeoJSON FeatureCollection.");
}

if (source.features.length === 0) {
  throw new Error("No features were found in the GeoJSON file.");
}

const isoOverrides: Record<number, string> = {
  // Natural Earth does not provide standard ISO codes
  // for these features in this dataset.
  1159320637: "FRA", // France
  1159321109: "NOR", // Norway
  1159321007: "XKX", // Kosovo
};

const filteredFeatures = source.features.filter((feature) => {
  const name = feature.properties.NAME;

  if (!name) return false;

  return !excludedNames.has(name);
});

console.log(
  `Removed ${source.features.length - filteredFeatures.length} excluded features.`,
);

const processedFeatures = filteredFeatures.map((feature, index) => {
  const properties = feature.properties;

  if (!feature.geometry) {
    throw new Error(`Feature ${index} is missing geometry.`);
  }

  if (!properties.NE_ID) {
    throw new Error(`Feature ${index} is missing a Natural Earth ID.`);
  }

  const name = properties.NAME_EN ?? properties.NAME;

  if (!name) {
    throw new Error(`Feature ${index} is missing a name.`);
  }

  const isoA2 =
    properties.ISO_A2 && properties.ISO_A2 !== "-99" ? properties.ISO_A2 : null;

  const naturalEarthIsoA3 =
    properties.ISO_A3 && properties.ISO_A3 !== "-99" ? properties.ISO_A3 : null;

  const isoA3 = naturalEarthIsoA3 ?? isoOverrides[properties.NE_ID] ?? null;

  const id = isoA3 ?? `NE-${properties.NE_ID}`;

  return {
    type: "Feature" as const,

    id,

    properties: {
      name,
      iso_a2: isoA2,
      iso_a3: isoA3,
      continent: properties.CONTINENT ?? null,
      region: properties.REGION_UN ?? null,
      subregion: properties.SUBREGION ?? null,
    },

    geometry: feature.geometry,
  };
});

const ids = processedFeatures.map((feature) => feature.id);

const uniqueIds = new Set(ids);

if (uniqueIds.size !== ids.length) {
  throw new Error("Duplicate feature IDs were found.");
}

const processed: CountryFeatureCollection = {
  type: "FeatureCollection",
  features: processedFeatures,
};

fs.mkdirSync(path.dirname(outputPath), { recursive: true });

fs.mkdirSync(path.dirname(publicOutputPath), { recursive: true });

const output = JSON.stringify(processed, null, 2);

fs.writeFileSync(outputPath, output);

fs.writeFileSync(publicOutputPath, output);

const isoCount = processedFeatures.filter(
  (feature) => feature.properties.iso_a3 !== null,
).length;

const fallbackCount = processedFeatures.length - isoCount;

console.log("");
console.log(`✓ Processed ${processedFeatures.length} features.`);

console.log(`✓ ${isoCount} features have ISO-3 codes.`);

console.log(`✓ ${fallbackCount} features use Natural Earth IDs.`);

console.log("✓ Removed unused Natural Earth properties.");

console.log("✓ Added stable feature IDs.");

console.log("");
console.log("✓ Saved processed data to:");

console.log(`  ${outputPath}`);

console.log("");
console.log("✓ Saved public copy to:");

console.log(`  ${publicOutputPath}`);
