/**
 * Downloads the current flags of all 50 U.S. states from Wikimedia Commons.
 *
 * Wikimedia Commons is queried through its MediaWiki API so this script does
 * not depend on hard-coded upload.wikimedia.org URLs.
 *
 * Output:
 *
 * public/data/countries/usa/flags/
 * ├── al.svg
 * ├── ak.svg
 * ├── ...
 * └── wy.svg
 *
 * Runtime flag filenames use lowercase U.S. postal abbreviations so they match
 * GeoPedia's existing lowercase asset naming conventions.
 */

import fs from "node:fs/promises";
import path from "node:path";

/* -------------------------------------------------------------------------- */
/* Paths                                                                      */
/* -------------------------------------------------------------------------- */

/**
 * Runtime directory containing the downloaded U.S. state flag SVGs.
 */
const OUTPUT_DIRECTORY = path.resolve(
  "public/data/countries/usa/flags",
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
 * Each state normally requires two requests:
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
 * Information required to resolve and save one state flag.
 */
type StateFlagDefinition = {
  /** Full state name used for display and Wikimedia lookup. */
  name: string;

  /** Two-letter U.S. postal abbreviation. */
  abbreviation: string;

  /**
   * Wikimedia Commons filename when it differs from the normal
   * `Flag of {State}.svg` convention.
   */
  commonsFileName?: string;
};

/**
 * All 50 U.S. states.
 *
 * Most Wikimedia Commons files follow:
 *
 * Flag of {State}.svg
 *
 * Georgia requires an explicit title because "Georgia" may otherwise refer to
 * the country rather than the U.S. state.
 */
const STATE_FLAGS: StateFlagDefinition[] = [
  { name: "Alabama", abbreviation: "AL" },
  { name: "Alaska", abbreviation: "AK" },
  { name: "Arizona", abbreviation: "AZ" },
  { name: "Arkansas", abbreviation: "AR" },
  { name: "California", abbreviation: "CA" },
  { name: "Colorado", abbreviation: "CO" },
  { name: "Connecticut", abbreviation: "CT" },
  { name: "Delaware", abbreviation: "DE" },
  { name: "Florida", abbreviation: "FL" },

  {
    name: "Georgia",
    abbreviation: "GA",
    commonsFileName: "Flag of Georgia (U.S. state).svg",
  },

  { name: "Hawaii", abbreviation: "HI" },
  { name: "Idaho", abbreviation: "ID" },
  { name: "Illinois", abbreviation: "IL" },
  { name: "Indiana", abbreviation: "IN" },
  { name: "Iowa", abbreviation: "IA" },
  { name: "Kansas", abbreviation: "KS" },
  { name: "Kentucky", abbreviation: "KY" },
  { name: "Louisiana", abbreviation: "LA" },
  { name: "Maine", abbreviation: "ME" },
  { name: "Maryland", abbreviation: "MD" },
  { name: "Massachusetts", abbreviation: "MA" },
  { name: "Michigan", abbreviation: "MI" },
  { name: "Minnesota", abbreviation: "MN" },
  { name: "Mississippi", abbreviation: "MS" },
  { name: "Missouri", abbreviation: "MO" },
  { name: "Montana", abbreviation: "MT" },
  { name: "Nebraska", abbreviation: "NE" },
  { name: "Nevada", abbreviation: "NV" },
  { name: "New Hampshire", abbreviation: "NH" },
  { name: "New Jersey", abbreviation: "NJ" },
  { name: "New Mexico", abbreviation: "NM" },
  { name: "New York", abbreviation: "NY" },
  { name: "North Carolina", abbreviation: "NC" },
  { name: "North Dakota", abbreviation: "ND" },
  { name: "Ohio", abbreviation: "OH" },
  { name: "Oklahoma", abbreviation: "OK" },
  { name: "Oregon", abbreviation: "OR" },
  { name: "Pennsylvania", abbreviation: "PA" },
  { name: "Rhode Island", abbreviation: "RI" },
  { name: "South Carolina", abbreviation: "SC" },
  { name: "South Dakota", abbreviation: "SD" },
  { name: "Tennessee", abbreviation: "TN" },
  { name: "Texas", abbreviation: "TX" },
  { name: "Utah", abbreviation: "UT" },
  { name: "Vermont", abbreviation: "VT" },
  { name: "Virginia", abbreviation: "VA" },
  { name: "Washington", abbreviation: "WA" },
  { name: "West Virginia", abbreviation: "WV" },
  { name: "Wisconsin", abbreviation: "WI" },
  { name: "Wyoming", abbreviation: "WY" },
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
        "User-Agent": "GeoPedia/1.0 state-flag-downloader",
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
 * Returns the Wikimedia Commons filename that should be queried for a state.
 */
function getCommonsFileName(state: StateFlagDefinition): string {
  return state.commonsFileName ?? `Flag of ${state.name}.svg`;
}

/**
 * Resolves a Wikimedia Commons file title to its actual source SVG URL.
 *
 * Redirects are followed so Commons may reorganize or rename files without
 * requiring GeoPedia's downloader to know the final upload URL.
 */
async function getCommonsSvgUrl(
  state: StateFlagDefinition,
): Promise<string> {
  const commonsFileName = getCommonsFileName(state);

  const queryParameters = new URLSearchParams({
    action: "query",
    format: "json",

    titles: `File:${commonsFileName}`,

    prop: "imageinfo",
    iiprop: "url|mime",

    redirects: "1",

    origin: "*",
  });

  const requestUrl = `${WIKIMEDIA_COMMONS_API_URL}?${queryParameters.toString()}`;

  const response = await fetchFromWikimedia(
    requestUrl,
    `${state.name} flag metadata`,
  );

  if (!response.ok) {
    throw new Error(
      `Wikimedia request failed for ${state.name}: ` +
        `${response.status} ${response.statusText}`,
    );
  }

  const data = (await response.json()) as WikimediaQueryResponse;

  const pages = Object.values(data.query?.pages ?? {});

  if (pages.length !== 1) {
    throw new Error(
      `Unexpected Wikimedia response for ${state.name}.`,
    );
  }

  const page = pages[0];

  if (page.missing) {
    throw new Error(
      `Wikimedia Commons file was not found: ${commonsFileName}`,
    );
  }

  const imageInfo = page.imageinfo?.[0];

  if (!imageInfo?.url) {
    throw new Error(
      `Wikimedia Commons returned no image URL for ${state.name}.`,
    );
  }

  if (imageInfo.mime && imageInfo.mime !== "image/svg+xml") {
    throw new Error(
      `${state.name} resolved to ${imageInfo.mime} instead of SVG.`,
    );
  }

  return imageInfo.url;
}

/* -------------------------------------------------------------------------- */
/* Downloading                                                                */
/* -------------------------------------------------------------------------- */

/**
 * Downloads one state flag.
 *
 * Existing files are skipped so interrupted runs can safely resume without
 * redownloading flags that were already completed.
 */
async function downloadStateFlag(
  state: StateFlagDefinition,
): Promise<void> {
  const outputFileName = `${state.abbreviation.toLowerCase()}.svg`;

  const outputPath = path.join(OUTPUT_DIRECTORY, outputFileName);

  try {
    await fs.access(outputPath);

    console.log(
      `${state.abbreviation}  ${state.name} -> already exists, skipping`,
    );

    return;
  } catch {
    /*
     * File does not exist yet.
     *
     * Continue with the download.
     */
  }

  const imageUrl = await getCommonsSvgUrl(state);

  const response = await fetchFromWikimedia(
    imageUrl,
    `${state.name} flag SVG`,
  );

  if (!response.ok) {
    throw new Error(
      `Failed to download ${state.name}: ` +
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
      `Downloaded file for ${state.name} does not appear to be SVG.`,
    );
  }

  await fs.writeFile(outputPath, svg, "utf8");

  console.log(
    `${state.abbreviation}  ${state.name} -> ${outputFileName}`,
  );
}

/* -------------------------------------------------------------------------- */
/* Validation                                                                 */
/* -------------------------------------------------------------------------- */

/**
 * Verifies that the state metadata contains exactly 50 unique state
 * abbreviations.
 */
function validateStateDefinitions(): void {
  if (STATE_FLAGS.length !== 50) {
    throw new Error(
      `Expected 50 states but found ${STATE_FLAGS.length}.`,
    );
  }

  const abbreviations = new Set(
    STATE_FLAGS.map((state) => state.abbreviation),
  );

  if (abbreviations.size !== 50) {
    throw new Error(
      "State flag definitions contain duplicate abbreviations.",
    );
  }
}

/**
 * Verifies that every expected state flag SVG exists after the download pass.
 */
async function validateOutputFiles(): Promise<void> {
  const files = await fs.readdir(OUTPUT_DIRECTORY);

  const expectedFiles = new Set(
    STATE_FLAGS.map(
      (state) => `${state.abbreviation.toLowerCase()}.svg`,
    ),
  );

  const missingFiles = Array.from(expectedFiles).filter(
    (fileName) => !files.includes(fileName),
  );

  if (missingFiles.length > 0) {
    throw new Error(
      `Missing downloaded state flags: ${missingFiles.join(", ")}`,
    );
  }
}

/* -------------------------------------------------------------------------- */
/* Main                                                                       */
/* -------------------------------------------------------------------------- */

/**
 * Downloads and validates all 50 U.S. state flags.
 */
async function main(): Promise<void> {
  console.log("Downloading U.S. state flags...\n");

  validateStateDefinitions();

  await fs.mkdir(OUTPUT_DIRECTORY, {
    recursive: true,
  });

  /*
   * Process states sequentially rather than concurrently.
   *
   * Combined with fetchFromWikimedia's request-level throttling, this keeps
   * request volume low and makes interrupted runs easy to resume.
   */
  for (const state of STATE_FLAGS) {
    await downloadStateFlag(state);
  }

  await validateOutputFiles();

  console.log("");

  console.log(
    `Downloaded or verified ${STATE_FLAGS.length} state flags.`,
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
