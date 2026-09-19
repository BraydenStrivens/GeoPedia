import fs from "node:fs";
import path from "node:path";

/**
 * Minimal REST Countries response envelope used by the downloader.
 */
type RestCountriesResponse = {
  data?: {
    objects?: unknown[];
    meta?: {
      total?: number;
      count?: number;
      limit?: number;
      offset?: number;
      more?: boolean;
    };
  };
};

/* -------------------------------------------------------------------------- */
/*                                   Config                                   */
/* -------------------------------------------------------------------------- */

const PROJECT_ROOT = process.cwd();

const OUTPUT_PATH = path.join(
  PROJECT_ROOT,
  "data",
  "source",
  "countries.json",
);

const API_BASE_URL = "https://api.restcountries.com/countries/v5";

const PAGE_SIZE = 100;

/**
 * Only request fields used by GeoPedia's generated country metadata and flag
 * downloader.
 */
const RESPONSE_FIELDS = [
  "names.common",
  "names.official",
  "codes.alpha_2",
  "codes.alpha_3",
  "continents",
  "subregion",
  "calling_codes",
  "cars.driving_side",
  "flag.url_svg",
  "capitals.name",
  "population",
].join(",");

/* -------------------------------------------------------------------------- */
/*                                  Helpers                                   */
/* -------------------------------------------------------------------------- */

/**
 * Returns the REST Countries API key from the current environment.
 */
function getApiKey(): string {
  const apiKey = process.env.REST_COUNTRIES_API_KEY;

  if (!apiKey) {
    throw new Error(
      "REST_COUNTRIES_API_KEY is not set.\n" +
        "Set it before running this script.",
    );
  }

  return apiKey;
}

/**
 * Downloads one page of country records.
 *
 * @param apiKey - REST Countries bearer token.
 * @param offset - Number of records to skip.
 */
async function downloadPage(
  apiKey: string,
  offset: number,
): Promise<RestCountriesResponse> {
  const url = new URL(API_BASE_URL);

  url.searchParams.set("limit", String(PAGE_SIZE));

  url.searchParams.set("offset", String(offset));

  url.searchParams.set("response_fields", RESPONSE_FIELDS);

  const response = await fetch(url, {
    headers: {
      Authorization: `Bearer ${apiKey}`,
    },
  });

  if (!response.ok) {
    throw new Error(
      `REST Countries request failed at offset ${offset}: ` +
        `${response.status} ${response.statusText}`,
    );
  }

  return (await response.json()) as RestCountriesResponse;
}

/* -------------------------------------------------------------------------- */
/*                                 Downloader                                 */
/* -------------------------------------------------------------------------- */

/**
 * Downloads the complete REST Countries dataset used by GeoPedia.
 *
 * Data is fetched page-by-page and written directly as UTF-8 JSON. This avoids
 * encoding problems caused by passing Unicode country names through PowerShell
 * JSON serialization.
 */
async function downloadCountryData(): Promise<void> {
  const apiKey = getApiKey();

  const countries: unknown[] = [];

  let offset = 0;
  let expectedTotal: number | undefined;

  while (true) {
    console.log(`Downloading countries at offset ${offset}...`);

    const page = await downloadPage(apiKey, offset);

    const objects = page.data?.objects ?? [];
    const meta = page.data?.meta;

    countries.push(...objects);

    if (
      expectedTotal === undefined &&
      typeof meta?.total === "number"
    ) {
      expectedTotal = meta.total;
    }

    if (!meta?.more) {
      break;
    }

    offset += PAGE_SIZE;
  }

  fs.mkdirSync(path.dirname(OUTPUT_PATH), {
    recursive: true,
  });

  fs.writeFileSync(
    OUTPUT_PATH,
    `${JSON.stringify(countries, null, 2)}\n`,
    "utf8",
  );

  console.log(`\nDownloaded ${countries.length} country records.`);

  if (
    expectedTotal !== undefined &&
    countries.length !== expectedTotal
  ) {
    console.warn(
      `Warning: API reported ${expectedTotal} total records, ` +
        `but ${countries.length} were downloaded.`,
    );
  }

  console.log(`Output: ${path.relative(PROJECT_ROOT, OUTPUT_PATH)}`);
}

downloadCountryData().catch((error) => {
  console.error(error);
  process.exit(1);
});
