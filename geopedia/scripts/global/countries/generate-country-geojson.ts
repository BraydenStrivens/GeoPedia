import fs from "node:fs";
import path from "node:path";

import { GEOGUESSR_COUNTRY_CODES } from "@/constants/geoguessrCountryCodes";

/* -------------------------------------------------------------------------- */
/*                                   Types                                    */
/* -------------------------------------------------------------------------- */

/**
 * Geometry types expected from Natural Earth's Admin 0 Map Units dataset.
 */
type PolygonGeometry = {
  type: "Polygon";
  coordinates: number[][][];
};

type MultiPolygonGeometry = {
  type: "MultiPolygon";
  coordinates: number[][][][];
};

type CountryGeometry = PolygonGeometry | MultiPolygonGeometry;

/**
 * Minimal Natural Earth Map Unit feature used by the generator.
 */
type NaturalEarthFeature = {
  type: "Feature";
  properties: {
    NAME?: string;
    GEOUNIT?: string;
    SUBUNIT?: string;

    ISO_A2?: string;
    ISO_A3?: string;

    ADM0_A3?: string;
    GU_A3?: string;
    SU_A3?: string;

    CONTINENT?: string;
    REGION_UN?: string;
    SUBREGION?: string;
  };
  geometry: CountryGeometry | null;
};

/**
 * Natural Earth GeoJSON structure.
 */
type NaturalEarthFeatureCollection = {
  type: "FeatureCollection";
  features: NaturalEarthFeature[];
};

/**
 * Minimal REST Countries record required to identify GeoPedia countries.
 */
type RestCountry = {
  names?: {
    common?: string;
    official?: string;
  };

  codes?: {
    alpha_2?: string;
    alpha_3?: string;
  };

  continents?: string[];

  subregion?: string;

  flag?: {
    url_svg?: string;
  };
};

/**
 * Existing GeoPedia country-page metadata.
 */
type CountryData = {
  id: string;
  name: string;
};

/**
 * Properties stored on each generated world-country feature.
 *
 * This intentionally preserves the same basic property structure as the
 * existing GeoPedia countries GeoJSON so current map code can continue using
 * the generated file without unnecessary changes.
 */
type GeneratedCountryProperties = {
  name: string;
  iso_a2: string;
  iso_a3: string;
  continent: string;
  region: string;
  subregion: string;
  geoguessr: boolean;
};

/**
 * Generated GeoJSON country feature.
 */
type GeneratedCountryFeature = {
  type: "Feature";
  properties: GeneratedCountryProperties;
  geometry: CountryGeometry;
};

/**
 * Generated GeoJSON feature collection.
 */
type GeneratedFeatureCollection = {
  type: "FeatureCollection";
  features: GeneratedCountryFeature[];
};

/**
 * Accumulated geometry and Natural Earth metadata for one GeoPedia country.
 */
type CountryGeometryAccumulator = {
  geometries: CountryGeometry[];
  sourceProperties: NaturalEarthFeature["properties"];
};

/* -------------------------------------------------------------------------- */
/*                                   Paths                                    */
/* -------------------------------------------------------------------------- */

const PROJECT_ROOT = process.cwd();

const NATURAL_EARTH_PATH = path.join(
  PROJECT_ROOT,
  "data",
  "raw",
  "world",
  "ne_10m_admin_0_map_units.json",
);

const REST_COUNTRIES_PATH = path.join(
  PROJECT_ROOT,
  "data",
  "source",
  "countries.json",
);

const COUNTRY_DATA_PATH = path.join(
  PROJECT_ROOT,
  "public",
  "data",
  "countries.json",
);

const WORLD_COUNTRIES_OUTPUT_PATH = path.join(
  PROJECT_ROOT,
  "public",
  "data",
  "geojson",
  "world",
  "world-countries.geojson",
);

const COUNTRY_PAGES_OUTPUT_PATH = path.join(
  PROJECT_ROOT,
  "public",
  "data",
  "geojson",
  "world",
  "country-pages.geojson",
);

/* -------------------------------------------------------------------------- */
/*                                ID Overrides                                */
/* -------------------------------------------------------------------------- */

/**
 * Converts Natural Earth map-unit identifiers that differ from the ISO-style
 * identifiers used by GeoPedia.
 *
 * Natural Earth splits Svalbard and Jan Mayen into two map units while REST
 * Countries represents them together as SJM. Both Natural Earth units are
 * therefore normalized to the same GeoPedia country ID and merged later.
 */
const NATURAL_EARTH_ID_OVERRIDES: Record<string, string> = {
  /**
   * Caribbean Netherlands.
   */
  NLY: "BES",

  /**
   * Jan Mayen.
   */
  NJM: "SJM",

  /**
   * Svalbard.
   */
  NSV: "SJM",

  /**
   * Natural Earth commonly identifies Kosovo as KOS, while GeoPedia uses XKX.
   */
  KOS: "XKX",

  /**
   * Palestine.
   *
   * Natural Earth uses PSX as its internal geographic identifier while
   * REST Countries and GeoPedia use PSE.
   */
  PSX: "PSE",
};

/**
 * REST Countries identifies Kosovo as UNK. GeoPedia uses XKX so its ID matches
 * the existing country image and other local assets.
 */
const REST_COUNTRY_ID_OVERRIDES: Record<string, string> = {
  UNK: "XKX",
};

/* -------------------------------------------------------------------------- */
/*                              General Helpers                               */
/* -------------------------------------------------------------------------- */

/**
 * Reads and parses a JSON file.
 *
 * @param filePath - Absolute path to the JSON file.
 */
function readJson<T>(filePath: string): T {
  return JSON.parse(fs.readFileSync(filePath, "utf8")) as T;
}

/**
 * Returns a normalized uppercase GeoPedia ID for a REST Countries alpha-3
 * code.
 *
 * @param alpha3 - REST Countries alpha-3 code.
 */
function normalizeRestCountryId(alpha3: string): string {
  const code = alpha3.toUpperCase();

  return REST_COUNTRY_ID_OVERRIDES[code] ?? code;
}

/**
 * Applies GeoPedia's Natural Earth ID aliases.
 *
 * @param code - Natural Earth identifier.
 */
function normalizeNaturalEarthId(code: string): string {
  const normalizedCode = code.toUpperCase();

  return NATURAL_EARTH_ID_OVERRIDES[normalizedCode] ?? normalizedCode;
}

/* -------------------------------------------------------------------------- */
/*                           Country ID Resolution                            */
/* -------------------------------------------------------------------------- */

/**
 * Determines which GeoPedia country a Natural Earth map unit belongs to.
 *
 * GU_A3 is checked first because it identifies geographic/map units such as
 * French Guiana, Réunion, Christmas Island, and Bouvet Island independently
 * from their administering countries.
 *
 * Additional Natural Earth code fields are used as fallbacks because their
 * contents vary for unusual political and geographic entities.
 *
 * A candidate is only accepted if it exists in GeoPedia's canonical set of
 * REST Countries IDs.
 *
 * @param properties - Natural Earth feature properties.
 * @param validCountryIds - Canonical GeoPedia country IDs.
 */
function resolveCountryId(
  properties: NaturalEarthFeature["properties"],
  validCountryIds: ReadonlySet<string>,
): string | null {
  const candidates = [
    properties.GU_A3,
    properties.SU_A3,
    properties.ISO_A3,
    properties.ADM0_A3,
  ];

  for (const candidate of candidates) {
    if (!candidate || candidate === "-99") {
      continue;
    }

    const normalizedId = normalizeNaturalEarthId(candidate);

    if (validCountryIds.has(normalizedId)) {
      return normalizedId;
    }
  }

  return null;
}

/* -------------------------------------------------------------------------- */
/*                            Geometry Processing                             */
/* -------------------------------------------------------------------------- */

/**
 * Converts a Polygon or MultiPolygon into a list of polygon coordinate arrays.
 *
 * This allows multiple Natural Earth map units belonging to the same GeoPedia
 * country to be combined into one final feature.
 *
 * @param geometry - Source GeoJSON geometry.
 */
function extractPolygons(geometry: CountryGeometry): number[][][][] {
  if (geometry.type === "Polygon") {
    return [geometry.coordinates];
  }

  return geometry.coordinates;
}

/**
 * Combines one or more source geometries into a single GeoJSON geometry.
 *
 * Countries represented by exactly one Polygon remain Polygons. Countries
 * consisting of multiple polygons or map units become MultiPolygons.
 *
 * This is particularly important for SJM, where Natural Earth supplies
 * separate Svalbard and Jan Mayen map units.
 *
 * @param geometries - Source geometries belonging to the country.
 */
function mergeGeometries(
  geometries: CountryGeometry[],
): CountryGeometry {
  if (geometries.length === 0) {
    throw new Error("Cannot merge an empty geometry collection.");
  }

  if (geometries.length === 1 && geometries[0].type === "Polygon") {
    return geometries[0];
  }

  const polygons = geometries.flatMap(extractPolygons);

  return {
    type: "MultiPolygon",
    coordinates: polygons,
  };
}

/* -------------------------------------------------------------------------- */
/*                         REST Countries Processing                          */
/* -------------------------------------------------------------------------- */

/**
 * Creates the canonical 250-country REST Countries lookup used by GeoPedia.
 *
 * Records without an alpha-3 code are intentionally excluded.
 */
function createRestCountryLookup(
  countries: RestCountry[],
): Map<string, RestCountry> {
  const lookup = new Map<string, RestCountry>();

  for (const country of countries) {
    const alpha3 = country.codes?.alpha_3;

    if (!alpha3) {
      continue;
    }

    const id = normalizeRestCountryId(alpha3);

    lookup.set(id, country);
  }

  return lookup;
}

/* -------------------------------------------------------------------------- */
/*                     Natural Earth Geometry Collection                      */
/* -------------------------------------------------------------------------- */

/**
 * Groups Natural Earth map units by canonical GeoPedia country ID.
 *
 * Extra Natural Earth map units that are not represented by the canonical
 * REST Countries dataset are ignored.
 */
function collectCountryGeometries(
  naturalEarth: NaturalEarthFeatureCollection,
  validCountryIds: ReadonlySet<string>,
): Map<string, CountryGeometryAccumulator> {
  const countries = new Map<string, CountryGeometryAccumulator>();

  for (const feature of naturalEarth.features) {
    if (!feature.geometry) {
      continue;
    }

    const countryId = resolveCountryId(
      feature.properties,
      validCountryIds,
    );

    if (!countryId) {
      continue;
    }

    const existing = countries.get(countryId);

    if (existing) {
      existing.geometries.push(feature.geometry);

      continue;
    }

    countries.set(countryId, {
      geometries: [feature.geometry],
      sourceProperties: feature.properties,
    });
  }

  return countries;
}

/* -------------------------------------------------------------------------- */
/*                           Feature Generation                               */
/* -------------------------------------------------------------------------- */

/**
 * Creates a cleaned runtime GeoJSON feature.
 *
 * Country names and ISO identifiers come from REST Countries because that is
 * GeoPedia's canonical country metadata source. Geographic region properties
 * come from Natural Earth to preserve compatibility with the existing
 * countries GeoJSON schema.
 */
function createCountryFeature(
  countryId: string,
  restCountry: RestCountry,
  geometryData: CountryGeometryAccumulator,
): GeneratedCountryFeature {
  const name = restCountry.names?.common;

  const alpha2 = restCountry.codes?.alpha_2;

  if (!name) {
    throw new Error(
      `REST Countries is missing a common name for ${countryId}.`,
    );
  }

  if (!alpha2) {
    throw new Error(
      `REST Countries is missing alpha-2 for ${countryId}. ` +
        "Make sure codes.alpha_2 is included in download-country-data.ts.",
    );
  }

  const source = geometryData.sourceProperties;

  return {
    type: "Feature",

    properties: {
      name,
      iso_a2: alpha2.toUpperCase(),
      iso_a3: countryId,
      continent:
        source.CONTINENT ?? restCountry.continents?.join(", ") ?? "",
      region:
        source.REGION_UN ?? restCountry.continents?.join(", ") ?? "",
      subregion: source.SUBREGION ?? restCountry.subregion ?? "",
      geoguessr: GEOGUESSR_COUNTRY_CODES.has(countryId.toUpperCase()),
    },

    geometry: mergeGeometries(geometryData.geometries),
  };
}

/**
 * Generates features for a requested set of canonical country IDs.
 */
function generateFeatures(
  countryIds: ReadonlySet<string>,
  restCountries: ReadonlyMap<string, RestCountry>,
  geometryLookup: ReadonlyMap<string, CountryGeometryAccumulator>,
): GeneratedCountryFeature[] {
  const features: GeneratedCountryFeature[] = [];

  const missingGeometry: string[] = [];

  for (const countryId of countryIds) {
    const country = restCountries.get(countryId);

    if (!country) {
      throw new Error(
        `No REST Countries record exists for ${countryId}.`,
      );
    }

    const geometry = geometryLookup.get(countryId);

    if (!geometry) {
      missingGeometry.push(
        `${countryId} — ${country.names?.common ?? "Unknown"}`,
      );

      continue;
    }

    features.push(createCountryFeature(countryId, country, geometry));
  }

  if (missingGeometry.length > 0) {
    throw new Error(
      [
        "Missing Natural Earth geometry:",
        ...missingGeometry.map((country) => `  ${country}`),
      ].join("\n"),
    );
  }

  features.sort((a, b) =>
    a.properties.name.localeCompare(b.properties.name),
  );

  return features;
}

/**
 * Writes a GeoJSON FeatureCollection to disk.
 */
function writeGeoJson(
  outputPath: string,
  features: GeneratedCountryFeature[],
): void {
  const collection: GeneratedFeatureCollection = {
    type: "FeatureCollection",
    features,
  };

  fs.mkdirSync(path.dirname(outputPath), {
    recursive: true,
  });

  fs.writeFileSync(
    outputPath,
    `${JSON.stringify(collection)}\n`,
    "utf8",
  );
}

/* -------------------------------------------------------------------------- */
/*                                  Generator                                 */
/* -------------------------------------------------------------------------- */

/**
 * Generates both world-level GeoPedia country geometry datasets.
 *
 * world-countries.geojson:
 *   All 250 coded REST Countries entities. Used by global quizzes.
 *
 * country-pages.geojson:
 *   The 239 entities that have dedicated GeoPedia country pages.
 */
function generateCountryGeoJson(): void {
  const naturalEarth = readJson<NaturalEarthFeatureCollection>(
    NATURAL_EARTH_PATH,
  );

  const sourceCountries = readJson<RestCountry[]>(
    REST_COUNTRIES_PATH,
  );

  const countryPageData = readJson<CountryData[]>(COUNTRY_DATA_PATH);

  const restCountries = createRestCountryLookup(sourceCountries);

  /**
   * All coded REST Countries entities.
   */
  const worldCountryIds = new Set(restCountries.keys());

  /**
   * Only entities that have dedicated GeoPedia country pages.
   */
  const countryPageIds = new Set(
    countryPageData.map((country) => country.id.toUpperCase()),
  );

  console.log(
    `Natural Earth map units: ${naturalEarth.features.length}`,
  );

  console.log(`World country IDs: ${worldCountryIds.size}`);

  console.log(`Country-page IDs: ${countryPageIds.size}`);

  const geometryLookup = collectCountryGeometries(
    naturalEarth,
    worldCountryIds,
  );

  console.log(
    `Matched Natural Earth country IDs: ${geometryLookup.size}`,
  );

  const worldFeatures = generateFeatures(
    worldCountryIds,
    restCountries,
    geometryLookup,
  );

  const countryPageFeatures = generateFeatures(
    countryPageIds,
    restCountries,
    geometryLookup,
  );

  if (worldFeatures.length !== 250) {
    throw new Error(
      `Expected 250 world-country features, generated ${worldFeatures.length}.`,
    );
  }

  if (countryPageFeatures.length !== 239) {
    throw new Error(
      `Expected 239 country-page features, generated ${countryPageFeatures.length}.`,
    );
  }

  writeGeoJson(WORLD_COUNTRIES_OUTPUT_PATH, worldFeatures);

  writeGeoJson(COUNTRY_PAGES_OUTPUT_PATH, countryPageFeatures);

  console.log(
    `\nGenerated ${worldFeatures.length} world-country features.`,
  );

  console.log(
    `Output: ${path.relative(
      PROJECT_ROOT,
      WORLD_COUNTRIES_OUTPUT_PATH,
    )}`,
  );

  console.log(
    `\nGenerated ${countryPageFeatures.length} country-page features.`,
  );

  console.log(
    `Output: ${path.relative(
      PROJECT_ROOT,
      COUNTRY_PAGES_OUTPUT_PATH,
    )}`,
  );

  // TEST --------------------------------------------------------------------------
  // const sjm = geometryLookup.get("SJM");

  // if (sjm) {
  //   console.log(
  //     `\nSJM merged from ${sjm.geometries.length} Natural Earth map units.`,
  //   );
  // }
}

generateCountryGeoJson();
