/**
 * Downloads the current flags of Brazil's 26 states and Federal District from
 * Wikimedia Commons.
 *
 * Wikimedia Commons is queried through its MediaWiki API so this script does
 * not depend on hard-coded upload.wikimedia.org URLs.
 *
 * Because Brazilian state-flag filenames on Commons do not follow one perfectly
 * consistent naming convention, each state is resolved from a short list of
 * plausible Commons filenames.
 *
 * Output:
 *
 * public/data/countries/brazil/flags/
 * ├── ac.svg
 * ├── al.svg
 * ├── ...
 * └── to.svg
 *
 * Runtime filenames use lowercase Brazilian state abbreviations so they match
 * the paths referenced by GeoPedia's State Flags quiz.
 */

import fs from "node:fs/promises";
import path from "node:path";

/* -------------------------------------------------------------------------- */
/* Paths                                                                      */
/* -------------------------------------------------------------------------- */

/**
 * Runtime directory containing the downloaded Brazil state flag SVGs.
 */
const OUTPUT_DIRECTORY = path.resolve(
  "public/data/countries/brazil/flags",
);

/* -------------------------------------------------------------------------- */
/* Wikimedia Commons                                                          */
/* -------------------------------------------------------------------------- */

/**
 * MediaWiki API endpoint for Wikimedia Commons.
 */
const WIKIMEDIA_COMMONS_API_URL =
  "https://commons.wikimedia.org/w/api.php";

/**
 * Minimum delay between requests sent to Wikimedia Commons.
 *
 * A conservative delay keeps this infrequently run asset downloader friendly to
 * Wikimedia while also reducing the chance of temporary rate limiting.
 */
const WIKIMEDIA_REQUEST_DELAY_MS = 5000;

/**
 * Maximum number of attempts for a Wikimedia request that is rate limited.
 */
const MAX_WIKIMEDIA_REQUEST_ATTEMPTS = 5;

/**
 * Information required to resolve and save one Brazil state flag.
 */
type StateFlagDefinition = {
  /** Full state or Federal District name. */
  name: string;

  /** Official two-letter abbreviation. */
  abbreviation: string;

  /**
   * Optional Wikimedia Commons filenames that should be tried before the
   * automatically generated fallback candidates.
   */
  commonsFileNames?: readonly string[];
};

/**
 * Brazil's 26 states and Federal District.
 *
 * Explicit candidates are included only where the Commons filename is commonly
 * known to use wording that may not be covered cleanly by the generic fallback
 * patterns.
 */
const STATE_FLAGS: StateFlagDefinition[] = [
  { name: "Rondônia", abbreviation: "RO" },
  { name: "Acre", abbreviation: "AC" },
  { name: "Amazonas", abbreviation: "AM" },
  { name: "Roraima", abbreviation: "RR" },
  { name: "Pará", abbreviation: "PA" },
  { name: "Amapá", abbreviation: "AP" },
  { name: "Tocantins", abbreviation: "TO" },

  { name: "Maranhão", abbreviation: "MA" },
  { name: "Piauí", abbreviation: "PI" },
  { name: "Ceará", abbreviation: "CE" },
  { name: "Rio Grande do Norte", abbreviation: "RN" },
  { name: "Paraíba", abbreviation: "PB" },
  { name: "Pernambuco", abbreviation: "PE" },
  { name: "Alagoas", abbreviation: "AL" },
  { name: "Sergipe", abbreviation: "SE" },
  { name: "Bahia", abbreviation: "BA" },

  { name: "Minas Gerais", abbreviation: "MG" },
  { name: "Espírito Santo", abbreviation: "ES" },
  { name: "Rio de Janeiro", abbreviation: "RJ" },
  { name: "São Paulo", abbreviation: "SP" },

  { name: "Paraná", abbreviation: "PR" },
  { name: "Santa Catarina", abbreviation: "SC" },
  { name: "Rio Grande do Sul", abbreviation: "RS" },

  { name: "Mato Grosso do Sul", abbreviation: "MS" },
  { name: "Mato Grosso", abbreviation: "MT" },
  { name: "Goiás", abbreviation: "GO" },

  {
    name: "Distrito Federal",
    abbreviation: "DF",
    commonsFileNames: [
      "Bandeira do Distrito Federal (Brasil).svg",
      "Flag of the Federal District (Brazil).svg",
    ],
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
 * is respected when available. Otherwise, an increasingly conservative delay
 * is used before retrying.
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
        "User-Agent": "GeoPedia/1.0 brazil-state-flag-downloader",
      },
    });

    if (response.status !== 429) {
      return response;
    }

    if (attempt === MAX_WIKIMEDIA_REQUEST_ATTEMPTS) {
      throw new Error(
        `Wikimedia rate limit persisted for ${description} after ` +
          `${MAX_WIKIMEDIA_REQUEST_ATTEMPTS} attempts.`,
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
      `Rate limited while requesting ${description}. Retrying in ` +
        `${Math.round(retryDelayMs / 1000)} seconds...`,
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
 * Builds the ordered list of Wikimedia Commons filenames that may contain a
 * state's flag.
 *
 * Explicit state-specific names are tried first, followed by Portuguese and
 * English naming patterns commonly used by Commons.
 */
function getCommonsFileNameCandidates(
  state: StateFlagDefinition,
): string[] {
  const candidates = [
    ...(state.commonsFileNames ?? []),

    `Bandeira de ${state.name}.svg`,
    `Bandeira do estado de ${state.name}.svg`,
    `Bandeira do Estado de ${state.name}.svg`,
    `Bandeira do ${state.name}.svg`,
    `Bandeira da ${state.name}.svg`,

    `Flag of ${state.name}.svg`,
    `Flag of ${state.name} (Brazil).svg`,
    `Flag of the state of ${state.name}.svg`,
  ];

  return Array.from(new Set(candidates));
}

/**
 * Attempts to resolve one Wikimedia Commons filename to an SVG source URL.
 *
 * Returns null when that particular Commons filename does not exist. Other
 * response problems still throw because they indicate an actual request or data
 * failure rather than an incorrect candidate title.
 */
async function tryResolveCommonsSvgUrl(
  state: StateFlagDefinition,
  commonsFileName: string,
): Promise<string | null> {
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
    return null;
  }

  const imageInfo = page.imageinfo?.[0];

  /*
   * A candidate title may resolve to a Commons page that is not an actual image
   * file, or otherwise does not expose imageinfo. Treat that the same as a
   * missing candidate so the resolver can try the next possible filename.
   */
  if (!imageInfo?.url) {
    return null;
  }

  if (imageInfo.mime && imageInfo.mime !== "image/svg+xml") {
    throw new Error(
      `${state.name} resolved to ${imageInfo.mime} instead of SVG.`,
    );
  }

  console.log(
    `${state.abbreviation}  ${state.name} -> Commons: ${page.title}`,
  );

  return imageInfo.url;
}

/**
 * Resolves a state's flag to its actual Wikimedia Commons SVG source URL.
 *
 * Candidate filenames are tried in order until one exists.
 */
async function getCommonsSvgUrl(
  state: StateFlagDefinition,
): Promise<string> {
  const candidates = getCommonsFileNameCandidates(state);

  for (const commonsFileName of candidates) {
    const imageUrl = await tryResolveCommonsSvgUrl(
      state,
      commonsFileName,
    );

    if (imageUrl !== null) {
      return imageUrl;
    }
  }

  throw new Error(
    `Could not find a Wikimedia Commons SVG flag for ${state.name}. ` +
      `Tried: ${candidates.join(", ")}`,
  );
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
   * Checking the first portion for an SVG element is safer than requiring the
   * document to begin exactly with "<svg".
   */
  const beginning = svg.slice(0, 2000).toLowerCase();

  if (!beginning.includes("<svg")) {
    throw new Error(
      `Downloaded file for ${state.name} does not appear to be SVG.`,
    );
  }

  await fs.writeFile(outputPath, svg, "utf8");

  console.log(
    `${state.abbreviation}  ${state.name} -> saved ${outputFileName}`,
  );
}

/* -------------------------------------------------------------------------- */
/* Validation                                                                 */
/* -------------------------------------------------------------------------- */

/**
 * Verifies that the metadata contains exactly Brazil's 26 states plus Federal
 * District, with unique names and abbreviations.
 */
function validateStateDefinitions(): void {
  if (STATE_FLAGS.length !== 27) {
    throw new Error(
      `Expected 27 state-level divisions but found ${STATE_FLAGS.length}.`,
    );
  }

  const names = new Set(STATE_FLAGS.map((state) => state.name));

  if (names.size !== 27) {
    throw new Error(
      "Brazil state flag definitions contain duplicate names.",
    );
  }

  const abbreviations = new Set(
    STATE_FLAGS.map((state) => state.abbreviation),
  );

  if (abbreviations.size !== 27) {
    throw new Error(
      "Brazil state flag definitions contain duplicate abbreviations.",
    );
  }

  for (const state of STATE_FLAGS) {
    if (!/^[A-Z]{2}$/.test(state.abbreviation)) {
      throw new Error(
        `Invalid abbreviation for ${state.name}: ${state.abbreviation}`,
      );
    }
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
 * Downloads and validates all 27 Brazil state-level flags.
 */
async function main(): Promise<void> {
  console.log("Downloading Brazil state flags...\n");

  validateStateDefinitions();

  await fs.mkdir(OUTPUT_DIRECTORY, {
    recursive: true,
  });

  /*
   * Process states sequentially rather than concurrently.
   *
   * Combined with request-level throttling, this keeps request volume low and
   * lets an interrupted run resume safely because completed SVGs are skipped.
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
