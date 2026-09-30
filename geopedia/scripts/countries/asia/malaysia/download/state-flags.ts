/**
 * Downloads the current flags of Malaysia's 13 states and 3 federal
 * territories from Wikimedia Commons.
 *
 * Wikimedia Commons is queried through its MediaWiki API so this script does
 * not depend on hard-coded upload.wikimedia.org URLs.
 *
 * Output:
 *
 * public/data/countries/malaysia/flags/
 *
 * Runtime filenames use lowercase GeoPedia state IDs, such as my-01.svg and
 * my-14.svg, so they can be referenced directly by the State & Federal
 * Territory Flags quiz.
 */

import fs from "node:fs/promises";
import path from "node:path";

/* -------------------------------------------------------------------------- */
/* Paths                                                                      */
/* -------------------------------------------------------------------------- */

const OUTPUT_DIRECTORY = path.resolve(
  "public/data/countries/malaysia/flags",
);

/* -------------------------------------------------------------------------- */
/* Wikimedia Commons                                                          */
/* -------------------------------------------------------------------------- */

const WIKIMEDIA_COMMONS_API_URL =
  "https://commons.wikimedia.org/w/api.php";

const WIKIMEDIA_REQUEST_DELAY_MS = 5000;

const MAX_WIKIMEDIA_REQUEST_ATTEMPTS = 5;

type StateFlagDefinition = {
  stateId: string;
  name: string;
  commonsFileNames?: readonly string[];
};

const STATE_FLAGS: StateFlagDefinition[] = [
  { stateId: "MY-01", name: "Johor" },
  { stateId: "MY-02", name: "Kedah" },
  { stateId: "MY-03", name: "Kelantan" },
  { stateId: "MY-04", name: "Malacca" },
  { stateId: "MY-05", name: "Negeri Sembilan" },
  { stateId: "MY-06", name: "Pahang" },
  { stateId: "MY-07", name: "Penang" },
  { stateId: "MY-08", name: "Perak" },
  { stateId: "MY-09", name: "Perlis" },
  { stateId: "MY-10", name: "Selangor" },
  { stateId: "MY-11", name: "Terengganu" },
  { stateId: "MY-12", name: "Sabah" },
  { stateId: "MY-13", name: "Sarawak" },
  {
    stateId: "MY-14",
    name: "Kuala Lumpur",
    commonsFileNames: [
      "Flag of Kuala Lumpur, Malaysia.svg",
      "Flag of Kuala Lumpur.svg",
    ],
  },
  {
    stateId: "MY-15",
    name: "Labuan",
    commonsFileNames: [
      "Flag of Labuan, Malaysia.svg",
      "Flag of Labuan.svg",
    ],
  },
  {
    stateId: "MY-16",
    name: "Putrajaya",
    commonsFileNames: [
      "Flag of Putrajaya, Malaysia.svg",
      "Flag of Putrajaya.svg",
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

function sleep(milliseconds: number): Promise<void> {
  return new Promise((resolve) => {
    setTimeout(resolve, milliseconds);
  });
}

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
        "User-Agent": "GeoPedia/1.0 malaysia-state-flag-downloader",
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

function getCommonsFileNameCandidates(
  state: StateFlagDefinition,
): string[] {
  const candidates = [
    ...(state.commonsFileNames ?? []),

    `Flag of ${state.name}.svg`,
    `Flag of ${state.name}, Malaysia.svg`,
    `Flag of ${state.name} (Malaysia).svg`,
  ];

  return Array.from(new Set(candidates));
}

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

  if (!imageInfo?.url) {
    return null;
  }

  if (imageInfo.mime && imageInfo.mime !== "image/svg+xml") {
    throw new Error(
      `${state.name} resolved to ${imageInfo.mime} instead of SVG.`,
    );
  }

  console.log(
    `${state.stateId}  ${state.name} -> Commons: ${page.title}`,
  );

  return imageInfo.url;
}

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

async function downloadStateFlag(
  state: StateFlagDefinition,
): Promise<void> {
  const outputFileName = `${state.stateId.toLowerCase()}.svg`;

  const outputPath = path.join(OUTPUT_DIRECTORY, outputFileName);

  try {
    await fs.access(outputPath);

    console.log(
      `${state.stateId}  ${state.name} -> already exists, skipping`,
    );

    return;
  } catch {
    // File does not exist yet.
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

  const beginning = svg.slice(0, 2000).toLowerCase();

  if (!beginning.includes("<svg")) {
    throw new Error(
      `Downloaded file for ${state.name} does not appear to be SVG.`,
    );
  }

  await fs.writeFile(outputPath, svg, "utf8");

  console.log(
    `${state.stateId}  ${state.name} -> saved ${outputFileName}`,
  );
}

/* -------------------------------------------------------------------------- */
/* Validation                                                                 */
/* -------------------------------------------------------------------------- */

function validateStateDefinitions(): void {
  if (STATE_FLAGS.length !== 16) {
    throw new Error(
      `Expected 16 state-level divisions but found ${STATE_FLAGS.length}.`,
    );
  }

  const stateIds = new Set(STATE_FLAGS.map((state) => state.stateId));

  if (stateIds.size !== 16) {
    throw new Error(
      "Malaysia state flag definitions contain duplicate state IDs.",
    );
  }

  const names = new Set(STATE_FLAGS.map((state) => state.name));

  if (names.size !== 16) {
    throw new Error(
      "Malaysia state flag definitions contain duplicate names.",
    );
  }

  for (const state of STATE_FLAGS) {
    if (!/^MY-\d{2}$/.test(state.stateId)) {
      throw new Error(
        `Invalid state ID for ${state.name}: ${state.stateId}`,
      );
    }
  }
}

async function validateOutputFiles(): Promise<void> {
  const files = await fs.readdir(OUTPUT_DIRECTORY);

  const expectedFiles = new Set(
    STATE_FLAGS.map((state) => `${state.stateId.toLowerCase()}.svg`),
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

async function main(): Promise<void> {
  console.log(
    "Downloading Malaysia state and federal territory flags...\n",
  );

  validateStateDefinitions();

  await fs.mkdir(OUTPUT_DIRECTORY, {
    recursive: true,
  });

  for (const state of STATE_FLAGS) {
    await downloadStateFlag(state);
  }

  await validateOutputFiles();

  console.log("");

  console.log(`Downloaded or verified ${STATE_FLAGS.length} flags.`);

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
