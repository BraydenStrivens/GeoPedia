import fs from "node:fs";
import path from "node:path";

/**
 * Minimal shape of a REST Countries v5 record needed by GeoPedia.
 *
 * The API contains substantially more information, but the generator only
 * cares about fields that map to GeoPedia's CountryData model.
 */
type RestCountry = {
  names?: {
    common?: string;
    official?: string;
  };

  codes?: {
    alpha_3?: string;
  };

  capitals?: Array<{
    name?: string;
  }>;

  subregion?: string;

  calling_codes?: string[];

  cars?: {
    driving_side?: string;
  };

  continents?: string[];

  population?: number;

  flag?: {
    url_svg?: string;
  };
};

/**
 * Country metadata used by GeoPedia country pages.
 */
type CountryData = {
  /** Unique lowercase three-letter identifier used by GeoPedia. */
  id: string;

  /** Common user-facing name of the country. */
  name: string;

  /** Full official name of the country. */
  officialName: string;

  /** Continent or continents containing the country. */
  continent: string;

  /** Geographic subregion containing the country. */
  region: string;

  /** International telephone calling code or codes for the country. */
  callingCode: string;

  /** Side of the road on which vehicles drive in the country. */
  drivingSide: "left" | "right";

  /** Local URL of the country's flag SVG. */
  flagUrl: string;

  /** Local URL of the country's silhouette/image SVG. */
  imageUrl: string;

  /** Capital city or cities of the country. */
  capital: string;

  /** Population of the country. */
  population: number;
};

/* -------------------------------------------------------------------------- */
/*                                   Paths                                    */
/* -------------------------------------------------------------------------- */

const PROJECT_ROOT = process.cwd();

const SOURCE_PATH = path.join(
  PROJECT_ROOT,
  "data",
  "source",
  "countries.json",
);

const COUNTRY_IMAGES_DIRECTORY = path.join(
  PROJECT_ROOT,
  "public",
  "data",
  "country-images",
);

const COUNTRY_FLAGS_DIRECTORY = path.join(
  PROJECT_ROOT,
  "public",
  "data",
  "country-flags",
);

const OUTPUT_PATH = path.join(
  PROJECT_ROOT,
  "public",
  "data",
  "countries.json",
);

/* -------------------------------------------------------------------------- */
/*                              Helper functions                              */
/* -------------------------------------------------------------------------- */

/**
 * Converts a REST Countries alpha-3 code into GeoPedia's canonical country ID.
 *
 * Kosovo is returned by REST Countries as `UNK`, while GeoPedia's existing
 * geographic assets use the commonly used `XKX` code.
 *
 * @param alpha3 - Three-letter country code from REST Countries.
 * @returns GeoPedia's lowercase country identifier.
 */
function normalizeCountryId(alpha3: string): string {
  const normalizedCode = alpha3.toUpperCase();

  if (normalizedCode === "UNK") {
    return "xkx";
  }

  return normalizedCode.toLowerCase();
}

/**
 * Creates a case-insensitive lookup of SVG assets in a directory.
 *
 * Keys use the uppercase filename without its extension:
 *
 *     USA.svg -> USA
 *     usa.svg -> USA
 *
 * The original filename is retained so generated URLs exactly match the file
 * on disk. This avoids case-sensitivity problems when deploying from Windows
 * to a Linux server.
 *
 * @param directoryPath - Directory containing country SVG assets.
 */
function createAssetLookup(
  directoryPath: string,
): Map<string, string> {
  const files = fs.readdirSync(directoryPath, {
    withFileTypes: true,
  });

  const lookup = new Map<string, string>();

  for (const file of files) {
    if (!file.isFile()) {
      continue;
    }

    if (path.extname(file.name).toLowerCase() !== ".svg") {
      continue;
    }

    const code = path
      .basename(file.name, path.extname(file.name))
      .toUpperCase();

    lookup.set(code, file.name);
  }

  return lookup;
}

/**
 * Formats one or more telephone calling codes for display.
 *
 * REST Countries returns calling codes without the leading plus symbol.
 *
 * ["1"]       -> "+1"
 * ["1", "7"]  -> "+1, +7"
 */
function formatCallingCodes(
  callingCodes: string[] | undefined,
): string {
  if (!callingCodes?.length) {
    return "";
  }

  return callingCodes
    .filter(Boolean)
    .map((code) => {
      return code.startsWith("+") ? code : `+${code}`;
    })
    .join(", ");
}

/**
 * Converts the REST Countries driving-side value into the strict GeoPedia
 * union used by CountryData.
 */
function parseDrivingSide(
  value: string | undefined,
): "left" | "right" {
  if (value === "left" || value === "right") {
    return value;
  }

  throw new Error(`Unexpected driving-side value: ${String(value)}`);
}

/**
 * Downloads a country's SVG flag from REST Countries.
 *
 * The local file is always overwritten so every generated flag asset comes
 * from the same source and uses the same naming convention.
 *
 * @param flagUrl - Remote REST Countries SVG URL.
 * @param countryId - GeoPedia's lowercase country ID.
 * @returns The local SVG filename.
 */
async function downloadFlagAsset(
  flagUrl: string | undefined,
  countryId: string,
): Promise<string> {
  if (!flagUrl) {
    throw new Error(
      `No flag SVG URL was provided for ${countryId.toUpperCase()}.`,
    );
  }

  const filename = `${countryId}.svg`;

  const outputPath = path.join(COUNTRY_FLAGS_DIRECTORY, filename);

  console.log(`Downloading flag: ${countryId.toUpperCase()}`);

  const response = await fetch(flagUrl);

  if (!response.ok) {
    throw new Error(
      `Failed to download flag for ${countryId.toUpperCase()}: ` +
        `${response.status} ${response.statusText}`,
    );
  }

  const svg = await response.text();

  if (!svg.includes("<svg")) {
    throw new Error(
      `Downloaded flag for ${countryId.toUpperCase()} was not valid SVG.`,
    );
  }

  fs.writeFileSync(outputPath, svg, "utf8");

  return filename;
}

/* -------------------------------------------------------------------------- */
/*                                 Generator                                  */
/* -------------------------------------------------------------------------- */

/**
 * Generates GeoPedia's country-page metadata from the REST Countries snapshot.
 *
 * Only countries with an existing country-image SVG are included. Countries
 * without dedicated country-page assets may still exist in other datasets,
 * such as countries.geojson, for global quizzes.
 */
async function generateCountryData(): Promise<void> {
  if (!fs.existsSync(SOURCE_PATH)) {
    throw new Error(
      `REST Countries source file was not found:\n${SOURCE_PATH}`,
    );
  }

  if (!fs.existsSync(COUNTRY_IMAGES_DIRECTORY)) {
    throw new Error(
      `Country image directory was not found:\n${COUNTRY_IMAGES_DIRECTORY}`,
    );
  }

  if (!fs.existsSync(COUNTRY_FLAGS_DIRECTORY)) {
    throw new Error(
      `Country flag directory was not found:\n${COUNTRY_FLAGS_DIRECTORY}`,
    );
  }

  const rawSource = fs
    .readFileSync(SOURCE_PATH, "utf8")
    .replace(/^\uFEFF/, "");

  const sourceCountries = JSON.parse(rawSource) as RestCountry[];

  const imageLookup = createAssetLookup(COUNTRY_IMAGES_DIRECTORY);

  const generatedCountries: CountryData[] = [];

  const skippedNoCode: string[] = [];
  const skippedNoImage: string[] = [];

  for (const country of sourceCountries) {
    const commonName = country.names?.common?.trim() || "Unknown";

    const alpha3 = country.codes?.alpha_3?.trim().toUpperCase();

    /**
     * Entries such as Abkhazia, Northern Cyprus, Somaliland, and South
     * Ossetia currently have no usable alpha-3 code in REST Countries.
     */
    if (!alpha3 || !/^[A-Z]{3}$/.test(alpha3)) {
      skippedNoCode.push(commonName);
      continue;
    }

    const id = normalizeCountryId(alpha3);
    const assetCode = id.toUpperCase();

    /**
     * Download the flag for every supported coded entity.
     *
     * A country does not need a dedicated GeoPedia country page in order to
     * participate in global quizzes such as World Flags.
     */
    const flagFilename = await downloadFlagAsset(
      country.flag?.url_svg,
      id,
    );

    const imageFilename = imageLookup.get(assetCode);

    /**
     * Only entities with a country silhouette receive a dedicated country page.
     */
    if (!imageFilename) {
      skippedNoImage.push(`${assetCode} — ${commonName}`);

      continue;
    }

    const continents = country.continents ?? [];

    const capitals = (country.capitals ?? [])
      .map((capital) => capital.name?.trim())
      .filter(
        (name): name is string =>
          typeof name === "string" && name.length > 0,
      );

    const generatedCountry: CountryData = {
      id,

      name: commonName,

      officialName: country.names?.official?.trim() || commonName,

      continent: continents.join(", "),

      region: country.subregion?.trim() ?? "",

      callingCode: formatCallingCodes(country.calling_codes),

      drivingSide: parseDrivingSide(country.cars?.driving_side),

      flagUrl: `/data/country-flags/${flagFilename}`,

      imageUrl: `/data/country-images/${imageFilename}`,

      capital: capitals.join(", "),

      population: country.population ?? 0,
    };

    generatedCountries.push(generatedCountry);
  }

  /**
   * Keep the generated file stable between runs regardless of the ordering
   * returned by the external API.
   */
  generatedCountries.sort((a, b) => a.name.localeCompare(b.name));

  fs.writeFileSync(
    OUTPUT_PATH,
    `${JSON.stringify(generatedCountries, null, 2)}\n`,
    "utf8",
  );

  /* ------------------------------------------------------------------------ */
  /*                                Summary                                   */
  /* ------------------------------------------------------------------------ */

  console.log(
    `\nGenerated ${generatedCountries.length} country records.`,
  );

  console.log(`Output: ${path.relative(PROJECT_ROOT, OUTPUT_PATH)}`);

  console.log(
    `Skipped without alpha-3 code: ${skippedNoCode.length}`,
  );

  console.log(
    `Skipped without country image: ${skippedNoImage.length}`,
  );

  if (skippedNoCode.length > 0) {
    console.log("\nNo alpha-3 code:");

    for (const name of skippedNoCode) {
      console.log(`  ${name}`);
    }
  }

  if (skippedNoImage.length > 0) {
    console.log("\nNo country-page image:");

    for (const country of skippedNoImage) {
      console.log(`  ${country}`);
    }
  }
}

generateCountryData().catch((error) => {
  console.error(error);
  process.exit(1);
});
