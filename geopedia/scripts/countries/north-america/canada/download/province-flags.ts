/**
 * Downloads the current flags of all 10 Canadian provinces and 3 territories
 * from Wikimedia Commons.
 *
 * Wikimedia Commons is queried through its MediaWiki API so this script does
 * not depend on hard-coded upload.wikimedia.org URLs.
 *
 * Output:
 *
 * public/data/countries/canada/flags/
 * ├── 10.svg
 * ├── 11.svg
 * ├── ...
 * └── 62.svg
 *
 * Runtime filenames use Statistics Canada's two-digit PRUID identifiers. These
 * are the same stable subdivision identifiers retained in GeoPedia's processed
 * Canada province and territory GeoJSON.
 */

import fs from "node:fs/promises";
import path from "node:path";

/* -------------------------------------------------------------------------- */
/* Paths                                                                      */
/* -------------------------------------------------------------------------- */

/**
 * Runtime directory containing the downloaded Canadian province and territory
 * flag SVGs.
 */
const OUTPUT_DIRECTORY = path.resolve(
  "public/data/countries/canada/flags",
);

/* -------------------------------------------------------------------------- */
/* Wikimedia Commons                                                         */
/* -------------------------------------------------------------------------- */

/**
 * MediaWiki API endpoint for Wikimedia Commons.
 */
const WIKIMEDIA_COMMONS_API_URL =
  "https://commons.wikimedia.org/w/api.php";

/**
 * Minimum delay between every request sent to Wikimedia Commons.
 *
 * Each flag normally requires two requests:
 *
 * 1. Resolve the Commons file through the MediaWiki API.
 * 2. Download the actual SVG.
 *
 * A conservative delay is used because these assets are generated
 * infrequently and reliability is more important than speed.
 */
const WIKIMEDIA_REQUEST_DELAY_MS = 5000;

/**
 * Maximum number of attempts for a Wikimedia request that is rate limited.
 */
const MAX_WIKIMEDIA_REQUEST_ATTEMPTS = 5;

/**
 * Information required to resolve and save one Canadian subdivision flag.
 */
type ProvinceFlagDefinition = {
  /** Full province or territory name used by GeoPedia. */
  name: string;

  /** Statistics Canada province/territory unique identifier. */
  pruid: string;

  /** Exact Wikimedia Commons filename for the flag SVG. */
  commonsFileName: string;
};

/**
 * All 10 Canadian provinces and 3 territories.
 *
 * PRUID values match Statistics Canada's province and territory identifiers
 * used by GeoPedia's processed Canada boundary dataset.
 *
 * Commons filenames are explicit because naming conventions vary between
 * Canadian province and territory flag files.
 */
const PROVINCE_FLAGS: ProvinceFlagDefinition[] = [
  {
    name: "Newfoundland and Labrador",
    pruid: "10",
    commonsFileName: "Flag of Newfoundland and Labrador.svg",
  },
  {
    name: "Prince Edward Island",
    pruid: "11",
    commonsFileName: "Flag of Prince Edward Island.svg",
  },
  {
    name: "Nova Scotia",
    pruid: "12",
    commonsFileName: "Flag of Nova Scotia.svg",
  },
  {
    name: "New Brunswick",
    pruid: "13",
    commonsFileName: "Flag of New Brunswick.svg",
  },
  {
    name: "Quebec",
    pruid: "24",
    commonsFileName: "Flag of Quebec.svg",
  },
  {
    name: "Ontario",
    pruid: "35",
    commonsFileName: "Flag of Ontario.svg",
  },
  {
    name: "Manitoba",
    pruid: "46",
    commonsFileName: "Flag of Manitoba.svg",
  },
  {
    name: "Saskatchewan",
    pruid: "47",
    commonsFileName: "Flag of Saskatchewan.svg",
  },
  {
    name: "Alberta",
    pruid: "48",
    commonsFileName: "Flag of Alberta.svg",
  },
  {
    name: "British Columbia",
    pruid: "59",
    commonsFileName: "Flag of British Columbia.svg",
  },
  {
    name: "Yukon",
    pruid: "60",
    commonsFileName: "Flag of Yukon.svg",
  },
  {
    name: "Northwest Territories",
    pruid: "61",
    commonsFileName: "Flag of the Northwest Territories.svg",
  },
  {
    name: "Nunavut",
    pruid: "62",
    commonsFileName: "Flag of Nunavut.svg",
  },
];

/* -------------------------------------------------------------------------- */
/* Wikimedia response types                                                   */
/* -------------------------------------------------------------------------- */

type WikimediaImageInfo = {
  url?: string;
  mime?: string;
};

type WikimediaPage = {
  pageid?: number;
  title?: string;
  missing?: boolean;
  imageinfo?: WikimediaImageInfo[];
};

type WikimediaQueryResponse = {
  query?: {
    pages?: Record<string, WikimediaPage>;
  };
};

/* -------------------------------------------------------------------------- */
/* Shared helpers                                                             */
/* -------------------------------------------------------------------------- */

/**
 * Pauses execution for the requested number of milliseconds.
 */
function sleep(milliseconds: number): Promise<void> {
  return new Promise((resolve) => {
    setTimeout(resolve, milliseconds);
  });
}

/**
 * Sends a throttled request to Wikimedia Commons.
 *
 * HTTP 429 responses are retried automatically. Wikimedia's Retry-After header
 * is respected when available. Otherwise, the script uses an increasingly
 * conservative delay before trying again.
 */
async function fetchFromWikimedia(
  url: string,
  description: string,
): Promise<Response> {
  for (
    let attempt = 1;
    attempt <= MAX_WIKIMEDIA_REQUEST_ATTEMPTS;
    attempt += 1
  ) {
    await sleep(WIKIMEDIA_REQUEST_DELAY_MS);

    const response = await fetch(url, {
      headers: {
        "User-Agent": "GeoPedia/1.0 canada-province-flag-downloader",
      },
    });

    if (response.status !== 429) {
      return response;
    }

    if (attempt === MAX_WIKIMEDIA_REQUEST_ATTEMPTS) {
      throw new Error(
        `Wikimedia rate limit persisted for ${description} after ${MAX_WIKIMEDIA_REQUEST_ATTEMPTS} attempts.`,
      );
    }

    const retryAfterHeader = response.headers.get("retry-after");

    const retryAfterSeconds =
      retryAfterHeader !== null
        ? Number(retryAfterHeader)
        : Number.NaN;

    const retryDelayMs = Number.isFinite(retryAfterSeconds)
      ? Math.max(retryAfterSeconds * 1000, WIKIMEDIA_REQUEST_DELAY_MS)
      : WIKIMEDIA_REQUEST_DELAY_MS * (attempt + 1);

    console.warn(
      `Rate limited while requesting ${description}. Retrying in ${Math.round(
        retryDelayMs / 1000,
      )} seconds...`,
    );

    await sleep(retryDelayMs);
  }

  throw new Error(
    `Unable to request ${description} from Wikimedia Commons.`,
  );
}

/* -------------------------------------------------------------------------- */
/* Wikimedia lookup                                                           */
/* -------------------------------------------------------------------------- */

/**
 * Resolves a Wikimedia Commons file title to its actual source SVG URL.
 *
 * Redirects are followed so Commons may reorganize or rename files without
 * requiring GeoPedia's downloader to know the final upload URL.
 */
async function getCommonsSvgUrl(
  province: ProvinceFlagDefinition,
): Promise<string> {
  const queryParameters = new URLSearchParams({
    action: "query",
    format: "json",

    titles: `File:${province.commonsFileName}`,

    prop: "imageinfo",
    iiprop: "url|mime",

    redirects: "1",

    origin: "*",
  });

  const requestUrl = `${WIKIMEDIA_COMMONS_API_URL}?${queryParameters.toString()}`;

  const response = await fetchFromWikimedia(
    requestUrl,
    `${province.name} flag metadata`,
  );

  if (!response.ok) {
    throw new Error(
      `Wikimedia request failed for ${province.name}: ` +
        `${response.status} ${response.statusText}`,
    );
  }

  const data = (await response.json()) as WikimediaQueryResponse;

  const pages = Object.values(data.query?.pages ?? {});

  if (pages.length !== 1) {
    throw new Error(
      `Unexpected Wikimedia response for ${province.name}.`,
    );
  }

  const page = pages[0];

  if (page.missing) {
    throw new Error(
      `Wikimedia Commons file was not found: ${province.commonsFileName}`,
    );
  }

  const imageInfo = page.imageinfo?.[0];

  if (!imageInfo?.url) {
    throw new Error(
      `Wikimedia Commons returned no image URL for ${province.name}.`,
    );
  }

  if (imageInfo.mime && imageInfo.mime !== "image/svg+xml") {
    throw new Error(
      `${province.name} resolved to ${imageInfo.mime} instead of SVG.`,
    );
  }

  return imageInfo.url;
}

/* -------------------------------------------------------------------------- */
/* Downloading                                                                */
/* -------------------------------------------------------------------------- */

/**
 * Downloads one Canadian province or territory flag.
 *
 * Existing files are skipped so interrupted runs can safely resume without
 * redownloading flags that were already completed.
 */
async function downloadProvinceFlag(
  province: ProvinceFlagDefinition,
): Promise<void> {
  const outputFileName = `${province.pruid}.svg`;

  const outputPath = path.join(OUTPUT_DIRECTORY, outputFileName);

  try {
    await fs.access(outputPath);

    console.log(
      `${province.pruid}  ${province.name} -> already exists, skipping`,
    );

    return;
  } catch {
    /*
     * File does not exist yet.
     *
     * Continue with the download.
     */
  }

  const imageUrl = await getCommonsSvgUrl(province);

  const response = await fetchFromWikimedia(
    imageUrl,
    `${province.name} flag SVG`,
  );

  if (!response.ok) {
    throw new Error(
      `Failed to download ${province.name}: ` +
        `${response.status} ${response.statusText}`,
    );
  }

  const svg = await response.text();

  /*
   * SVG files may begin with an XML declaration, comments, or whitespace.
   * Checking the first portion of the file for an SVG element is therefore
   * safer than requiring the document to start exactly with "<svg".
   */
  const beginning = svg.slice(0, 2000).toLowerCase();

  if (!beginning.includes("<svg")) {
    throw new Error(
      `Downloaded file for ${province.name} does not appear to be SVG.`,
    );
  }

  await fs.writeFile(outputPath, svg, "utf8");

  console.log(
    `${province.pruid}  ${province.name} -> ${outputFileName}`,
  );
}

/* -------------------------------------------------------------------------- */
/* Validation                                                                 */
/* -------------------------------------------------------------------------- */

/**
 * Verifies that the metadata contains exactly 13 subdivisions with unique
 * Statistics Canada PRUID values and unique names.
 */
function validateProvinceDefinitions(): void {
  if (PROVINCE_FLAGS.length !== 13) {
    throw new Error(
      `Expected 13 provinces and territories but found ${PROVINCE_FLAGS.length}.`,
    );
  }

  const pruids = new Set(
    PROVINCE_FLAGS.map((province) => province.pruid),
  );

  if (pruids.size !== 13) {
    throw new Error(
      "Province flag definitions contain duplicate PRUID values.",
    );
  }

  const names = new Set(
    PROVINCE_FLAGS.map((province) => province.name),
  );

  if (names.size !== 13) {
    throw new Error(
      "Province flag definitions contain duplicate names.",
    );
  }
}

/**
 * Verifies that every expected flag SVG exists after the download pass.
 */
async function validateOutputFiles(): Promise<void> {
  const files = await fs.readdir(OUTPUT_DIRECTORY);

  const expectedFiles = new Set(
    PROVINCE_FLAGS.map((province) => `${province.pruid}.svg`),
  );

  const missingFiles = Array.from(expectedFiles).filter(
    (fileName) => !files.includes(fileName),
  );

  if (missingFiles.length > 0) {
    throw new Error(
      `Missing downloaded province and territory flags: ${missingFiles.join(", ")}`,
    );
  }
}

/* -------------------------------------------------------------------------- */
/* Main                                                                       */
/* -------------------------------------------------------------------------- */

/**
 * Downloads and validates the flags of all 10 Canadian provinces and
 * 3 territories.
 */
async function main(): Promise<void> {
  console.log(
    "Downloading Canadian province and territory flags...\n",
  );

  validateProvinceDefinitions();

  await fs.mkdir(OUTPUT_DIRECTORY, {
    recursive: true,
  });

  /*
   * Process flags sequentially rather than concurrently.
   *
   * Combined with fetchFromWikimedia's request-level throttling, this keeps
   * request volume low and makes interrupted runs easy to resume.
   */
  for (const province of PROVINCE_FLAGS) {
    await downloadProvinceFlag(province);
  }

  await validateOutputFiles();

  console.log("");

  console.log(
    `Downloaded or verified ${PROVINCE_FLAGS.length} province and territory flags.`,
  );

  console.log(`Output: ${OUTPUT_DIRECTORY}`);
}

main().catch((error: unknown) => {
  console.error("");

  if (error instanceof Error) {
    console.error(error.message);
  } else {
    console.error(error);
  }

  process.exitCode = 1;
});
