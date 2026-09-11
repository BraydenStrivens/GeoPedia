/**
 * Downloads Colombian department flags from Wikimedia Commons.
 *
 * Wikimedia Commons is queried through its MediaWiki API so this script does
 * not depend on hard-coded upload.wikimedia.org URLs.
 *
 * Output:
 *
 * public/data/countries/colombia/flags/
 *
 * Runtime flag filenames use GeoPedia's existing two-digit Colombian
 * department IDs so they match the department IDs already used by the map and
 * quiz data.
 */

import fs from "node:fs/promises";
import path from "node:path";

/* -------------------------------------------------------------------------- */
/* Paths                                                                      */
/* -------------------------------------------------------------------------- */

/**
 * Runtime directory containing the downloaded Colombian department flag SVGs.
 */
const OUTPUT_DIRECTORY = path.resolve(
  "public/data/countries/colombia/flags",
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
 * Each department normally requires two requests:
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
 * Information required to resolve and save one Colombian department flag.
 */
type DepartmentFlagDefinition = {
  /** Two-digit department ID used by GeoPedia's Colombia geography. */
  id: string;

  /** Full department name used for display and Wikimedia lookup. */
  name: string;

  /**
   * Wikimedia Commons filename when it differs from the normal lookup
   * convention.
   */
  commonsFileName?: string;
};

/**
 * Colombia's 32 departments plus Bogotá D.C.
 *
 * Most Wikimedia Commons files are expected to follow:
 *
 * Flag of {Department}.svg
 *
 * Individual entries can override that convention if Commons uses a different
 * filename.
 */
const DEPARTMENT_FLAGS: DepartmentFlagDefinition[] = [
  { id: "05", name: "Antioquia" },
  { id: "08", name: "Atlántico" },
  {
    id: "11",
    name: "Bogotá D.C.",
    commonsFileName: "Flag of Bogotá.svg",
  },
  {
    id: "13",
    name: "Bolívar",
    commonsFileName: "Flag of Bolívar Department.svg",
  },
  { id: "15", name: "Boyacá" },
  { id: "17", name: "Caldas" },
  { id: "18", name: "Caquetá" },
  { id: "19", name: "Cauca" },
  { id: "20", name: "Cesar" },
  { id: "23", name: "Córdoba" },
  { id: "25", name: "Cundinamarca" },
  { id: "27", name: "Chocó" },
  { id: "41", name: "Huila" },
  { id: "44", name: "La Guajira" },
  { id: "47", name: "Magdalena" },
  { id: "50", name: "Meta" },
  { id: "52", name: "Nariño" },
  { id: "54", name: "Norte de Santander" },
  { id: "63", name: "Quindío" },
  { id: "66", name: "Risaralda" },
  { id: "68", name: "Santander" },
  { id: "70", name: "Sucre" },
  { id: "73", name: "Tolima" },
  { id: "76", name: "Valle del Cauca" },
  { id: "81", name: "Arauca" },
  { id: "85", name: "Casanare" },
  { id: "86", name: "Putumayo" },
  {
    id: "88",
    name: "San Andrés and Providencia",
    commonsFileName:
      "Flag of San Andrés and Providencia Department.svg",
  },
  { id: "91", name: "Amazonas" },
  { id: "94", name: "Guainía" },
  { id: "95", name: "Guaviare" },
  { id: "97", name: "Vaupés" },
  { id: "99", name: "Vichada" },
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
        "User-Agent":
          "GeoPedia/1.0 colombia-department-flag-downloader",
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
 * Returns the Wikimedia Commons filename that should be queried for a
 * department.
 */
function getCommonsFileName(
  department: DepartmentFlagDefinition,
): string {
  return (
    department.commonsFileName ?? `Flag of ${department.name}.svg`
  );
}

/**
 * Resolves a Wikimedia Commons file title to its actual source SVG URL.
 *
 * Redirects are followed so Commons may reorganize or rename files without
 * requiring GeoPedia's downloader to know the final upload URL.
 */
async function getCommonsSvgUrl(
  department: DepartmentFlagDefinition,
): Promise<string> {
  const commonsFileName = getCommonsFileName(department);

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
    `${department.name} flag metadata`,
  );

  if (!response.ok) {
    throw new Error(
      `Wikimedia request failed for ${department.name}: ` +
        `${response.status} ${response.statusText}`,
    );
  }

  const data = (await response.json()) as WikimediaQueryResponse;

  const pages = Object.values(data.query?.pages ?? {});

  if (pages.length !== 1) {
    throw new Error(
      `Unexpected Wikimedia response for ${department.name}.`,
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
      `Wikimedia Commons returned no image URL for ${department.name}.`,
    );
  }

  if (imageInfo.mime && imageInfo.mime !== "image/svg+xml") {
    throw new Error(
      `${department.name} resolved to ${imageInfo.mime} instead of SVG.`,
    );
  }

  return imageInfo.url;
}

/* -------------------------------------------------------------------------- */
/* Downloading                                                                */
/* -------------------------------------------------------------------------- */

/**
 * Downloads one Colombian department flag.
 *
 * Existing files are skipped so interrupted runs can safely resume without
 * redownloading flags that were already completed.
 */
async function downloadDepartmentFlag(
  department: DepartmentFlagDefinition,
): Promise<void> {
  const outputFileName = `${department.id}.svg`;

  const outputPath = path.join(OUTPUT_DIRECTORY, outputFileName);

  try {
    await fs.access(outputPath);

    console.log(
      `${department.id}  ${department.name} -> already exists, skipping`,
    );

    return;
  } catch {
    /*
     * File does not exist yet.
     *
     * Continue with the download.
     */
  }

  const imageUrl = await getCommonsSvgUrl(department);

  const response = await fetchFromWikimedia(
    imageUrl,
    `${department.name} flag SVG`,
  );

  if (!response.ok) {
    throw new Error(
      `Failed to download ${department.name}: ` +
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
      `Downloaded file for ${department.name} does not appear to be SVG.`,
    );
  }

  await fs.writeFile(outputPath, svg, "utf8");

  console.log(
    `${department.id}  ${department.name} -> ${outputFileName}`,
  );
}

/* -------------------------------------------------------------------------- */
/* Validation                                                                 */
/* -------------------------------------------------------------------------- */

/**
 * Verifies that the department metadata contains exactly 33 unique department
 * IDs.
 */
function validateDepartmentDefinitions(): void {
  if (DEPARTMENT_FLAGS.length !== 33) {
    throw new Error(
      `Expected 33 Colombian department-level regions but found ${DEPARTMENT_FLAGS.length}.`,
    );
  }

  const ids = new Set(
    DEPARTMENT_FLAGS.map((department) => department.id),
  );

  if (ids.size !== 33) {
    throw new Error(
      "Colombian department flag definitions contain duplicate IDs.",
    );
  }

  const names = new Set(
    DEPARTMENT_FLAGS.map((department) => department.name),
  );

  if (names.size !== 33) {
    throw new Error(
      "Colombian department flag definitions contain duplicate names.",
    );
  }
}

/**
 * Verifies that every expected department flag SVG exists after the download
 * pass.
 */
async function validateOutputFiles(): Promise<void> {
  const files = await fs.readdir(OUTPUT_DIRECTORY);

  const expectedFiles = new Set(
    DEPARTMENT_FLAGS.map((department) => `${department.id}.svg`),
  );

  const missingFiles = Array.from(expectedFiles).filter(
    (fileName) => !files.includes(fileName),
  );

  if (missingFiles.length > 0) {
    throw new Error(
      `Missing downloaded department flags: ${missingFiles.join(", ")}`,
    );
  }
}

/* -------------------------------------------------------------------------- */
/* Main                                                                       */
/* -------------------------------------------------------------------------- */

/**
 * Downloads and validates all Colombian department flags.
 */
async function main(): Promise<void> {
  console.log("Downloading Colombian department flags...\n");

  validateDepartmentDefinitions();

  await fs.mkdir(OUTPUT_DIRECTORY, {
    recursive: true,
  });

  /*
   * Process departments sequentially rather than concurrently.
   *
   * Combined with fetchFromWikimedia's request-level throttling, this keeps
   * request volume low and makes interrupted runs easy to resume.
   */
  for (const department of DEPARTMENT_FLAGS) {
    await downloadDepartmentFlag(department);
  }

  await validateOutputFiles();

  console.log("");

  console.log(
    `Downloaded or verified ${DEPARTMENT_FLAGS.length} department flags.`,
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
