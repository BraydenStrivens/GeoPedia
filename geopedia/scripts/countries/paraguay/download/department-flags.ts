/**
 * Downloads Paraguayan department-level flags from Wikimedia Commons.
 *
 * The script first tries several common exact Commons filenames. If none of
 * those exist, it searches Wikimedia Commons for likely SVG flag files using
 * the department name.
 *
 * Paraguay has 17 departments plus Asunción, the capital district.
 *
 * Output:
 *
 * public/data/countries/paraguay/flags/
 *
 * Runtime filenames use GeoPedia's stable Paraguay department IDs:
 *
 * PY00.svg
 * PY01.svg
 * ...
 * PY17.svg
 */

import fs from "node:fs/promises";
import path from "node:path";

/* -------------------------------------------------------------------------- */
/* Paths                                                                      */
/* -------------------------------------------------------------------------- */

const OUTPUT_DIRECTORY = path.resolve(
  "public/data/countries/paraguay/flags",
);

/* -------------------------------------------------------------------------- */
/* Wikimedia Commons                                                         */
/* -------------------------------------------------------------------------- */

const WIKIMEDIA_COMMONS_API_URL =
  "https://commons.wikimedia.org/w/api.php";

const WIKIMEDIA_REQUEST_DELAY_MS = 5000;

const MAX_WIKIMEDIA_REQUEST_ATTEMPTS = 5;

const MAX_SEARCH_RESULTS = 20;

type DepartmentFlagDefinition = {
  id: string;
  name: string;
  commonsFileName?: string;
};

const DEPARTMENT_FLAGS: DepartmentFlagDefinition[] = [
  { id: "PY00", name: "Asunción" },
  { id: "PY01", name: "Concepción" },
  { id: "PY02", name: "San Pedro" },
  { id: "PY03", name: "Cordillera" },
  { id: "PY04", name: "Guairá" },
  { id: "PY05", name: "Caaguazú" },
  { id: "PY06", name: "Caazapá" },
  { id: "PY07", name: "Itapúa" },
  {
    id: "PY08",
    name: "Misiones",
    commonsFileName: "Flag of Misiones Department.svg",
  },
  { id: "PY09", name: "Paraguarí" },
  { id: "PY10", name: "Alto Paraná" },
  { id: "PY11", name: "Central" },
  { id: "PY12", name: "Ñeembucú" },
  { id: "PY13", name: "Amambay" },
  { id: "PY14", name: "Canindeyú" },
  { id: "PY15", name: "Presidente Hayes" },
  { id: "PY16", name: "Boquerón" },
  { id: "PY17", name: "Alto Paraguay" },
];

/* -------------------------------------------------------------------------- */
/* Wikimedia types                                                            */
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
        "User-Agent":
          "GeoPedia/1.0 paraguay-department-flag-downloader",
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
/* Exact Wikimedia lookup                                                     */
/* -------------------------------------------------------------------------- */

function getCommonsFileNameCandidates(
  department: DepartmentFlagDefinition,
): string[] {
  if (department.commonsFileName) {
    return [department.commonsFileName];
  }

  return [
    `Flag of ${department.name}.svg`,
    `Flag of ${department.name} Department.svg`,
    `Flag of ${department.name} Department, Paraguay.svg`,
    `Flag of the Department of ${department.name}.svg`,
    `Flag of ${department.name}, Paraguay.svg`,
    `Bandera de ${department.name}.svg`,
    `Bandera del departamento de ${department.name}.svg`,
    `Bandera Departamento de ${department.name}.svg`,
    `Bandera Departamento ${department.name}.svg`,
  ];
}

async function tryGetCommonsSvgUrl(
  department: DepartmentFlagDefinition,
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
    return null;
  }

  const imageInfo = page.imageinfo?.[0];

  if (!imageInfo?.url) {
    return null;
  }

  if (imageInfo.mime && imageInfo.mime !== "image/svg+xml") {
    return null;
  }

  console.log(
    `  Found exact Commons file: ${page.title ?? commonsFileName}`,
  );

  return imageInfo.url;
}

/* -------------------------------------------------------------------------- */
/* Commons search fallback                                                    */
/* -------------------------------------------------------------------------- */

async function searchCommonsForDepartmentFlag(
  department: DepartmentFlagDefinition,
): Promise<WikimediaPage[]> {
  const searchQueries = [
    `${department.name} flag Paraguay`,
    `${department.name} bandera Paraguay`,
    `${department.name} department flag Paraguay`,
    `${department.name} departamento bandera`,
  ];

  const results = new Map<string, WikimediaPage>();

  for (const searchQuery of searchQueries) {
    console.log(`  Searching Commons: ${searchQuery}`);

    const queryParameters = new URLSearchParams({
      action: "query",
      format: "json",

      generator: "search",
      gsrsearch: searchQuery,
      gsrnamespace: "6",
      gsrlimit: String(MAX_SEARCH_RESULTS),

      prop: "imageinfo",
      iiprop: "url|mime",

      origin: "*",
    });

    const requestUrl = `${WIKIMEDIA_COMMONS_API_URL}?${queryParameters.toString()}`;

    const response = await fetchFromWikimedia(
      requestUrl,
      `${department.name} Commons search`,
    );

    if (!response.ok) {
      throw new Error(
        `Wikimedia search failed for ${department.name}: ` +
          `${response.status} ${response.statusText}`,
      );
    }

    const data = (await response.json()) as WikimediaQueryResponse;

    for (const page of Object.values(data.query?.pages ?? {})) {
      if (!page.title) {
        continue;
      }

      const imageInfo = page.imageinfo?.[0];

      if (!imageInfo?.url || imageInfo.mime !== "image/svg+xml") {
        continue;
      }

      results.set(page.title, page);
    }
  }

  return Array.from(results.values());
}

/**
 * Scores likely Paraguay department-flag filenames.
 *
 * Positive signals:
 *
 * - department name
 * - "flag" or "bandera"
 * - Paraguay
 * - department/departamento
 * - SVG
 *
 * Negative signals:
 *
 * - coats of arms
 * - maps
 * - municipal/city flags
 * - unrelated historical or administrative graphics
 */
function scoreCommonsCandidate(
  department: DepartmentFlagDefinition,
  page: WikimediaPage,
): number {
  const title = (page.title ?? "").toLowerCase();

  const departmentName = department.name.toLowerCase();

  let score = 0;

  if (title.includes(departmentName)) {
    score += 100;
  }

  if (title.includes("flag")) {
    score += 50;
  }

  if (title.includes("bandera")) {
    score += 50;
  }

  if (title.includes("paraguay")) {
    score += 25;
  }

  if (title.includes("department")) {
    score += 15;
  }

  if (title.includes("departamento")) {
    score += 15;
  }

  if (title.endsWith(".svg")) {
    score += 10;
  }

  const unwantedTerms = [
    "coat of arms",
    "escudo",
    "seal",
    "map",
    "location",
    "locator",
    "municipality",
    "municipal",
    "city",
    "ciudad",
    "district",
    "distrito",
    "logo",
    "emblem",
    "argentina",
  ];

  for (const term of unwantedTerms) {
    if (title.includes(term)) {
      score -= 100;
    }
  }

  return score;
}

function chooseBestCommonsCandidate(
  department: DepartmentFlagDefinition,
  candidates: WikimediaPage[],
): WikimediaPage | null {
  const scoredCandidates = candidates
    .map((candidate) => ({
      candidate,
      score: scoreCommonsCandidate(department, candidate),
    }))
    .sort((a, b) => b.score - a.score);

  if (scoredCandidates.length === 0) {
    return null;
  }

  console.log("  Candidate Commons files:");

  for (const entry of scoredCandidates.slice(0, 10)) {
    console.log(
      `    ${entry.score
        .toString()
        .padStart(3)}  ${entry.candidate.title}`,
    );
  }

  const best = scoredCandidates[0];

  /*
   * Require a reasonably strong match rather than silently downloading an
   * unrelated SVG.
   */
  if (best.score < 150) {
    return null;
  }

  /*
   * Do not automatically choose between equally strong candidates.
   */
  const second = scoredCandidates[1];

  if (second && second.score === best.score) {
    console.warn(
      `  Top Commons candidates for ${department.name} are tied.`,
    );

    return null;
  }

  return best.candidate;
}

/* -------------------------------------------------------------------------- */
/* Combined lookup                                                            */
/* -------------------------------------------------------------------------- */

async function getCommonsSvgUrl(
  department: DepartmentFlagDefinition,
): Promise<string> {
  const exactCandidates = getCommonsFileNameCandidates(department);

  for (const commonsFileName of exactCandidates) {
    console.log(`  Trying: ${commonsFileName}`);

    const imageUrl = await tryGetCommonsSvgUrl(
      department,
      commonsFileName,
    );

    if (imageUrl) {
      return imageUrl;
    }
  }

  console.log(
    `  No exact filename matched ${department.name}. Searching Commons...`,
  );

  const searchResults =
    await searchCommonsForDepartmentFlag(department);

  const bestCandidate = chooseBestCommonsCandidate(
    department,
    searchResults,
  );

  const imageUrl = bestCandidate?.imageinfo?.[0]?.url;

  if (!bestCandidate?.title || !imageUrl) {
    throw new Error(
      `Could not confidently identify the Wikimedia Commons flag for ` +
        `${department.name}.\n\n` +
        `Review the candidate filenames printed above and add the correct ` +
        `one as commonsFileName in DEPARTMENT_FLAGS.`,
    );
  }

  console.log(`  Selected: ${bestCandidate.title}`);

  return imageUrl;
}

/* -------------------------------------------------------------------------- */
/* Downloading                                                                */
/* -------------------------------------------------------------------------- */

function getOutputFileName(
  department: DepartmentFlagDefinition,
): string {
  return `${department.id}.svg`;
}

async function downloadDepartmentFlag(
  department: DepartmentFlagDefinition,
): Promise<void> {
  const outputFileName = getOutputFileName(department);

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
     */
  }

  console.log(`${department.id}  ${department.name}`);

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

  const beginning = svg.slice(0, 2000).toLowerCase();

  if (!beginning.includes("<svg")) {
    throw new Error(
      `Downloaded file for ${department.name} does not appear to be SVG.`,
    );
  }

  await fs.writeFile(outputPath, svg, "utf8");

  console.log(`  Saved: ${outputFileName}\n`);
}

/* -------------------------------------------------------------------------- */
/* Validation                                                                 */
/* -------------------------------------------------------------------------- */

function validateDepartmentDefinitions(): void {
  if (DEPARTMENT_FLAGS.length !== 18) {
    throw new Error(
      `Expected 18 Paraguayan department-level regions but found ` +
        `${DEPARTMENT_FLAGS.length}.`,
    );
  }

  const ids = new Set(
    DEPARTMENT_FLAGS.map((department) => department.id),
  );

  if (ids.size !== 18) {
    throw new Error(
      "Paraguayan department flag definitions contain duplicate IDs.",
    );
  }

  const names = new Set(
    DEPARTMENT_FLAGS.map((department) => department.name),
  );

  if (names.size !== 18) {
    throw new Error(
      "Paraguayan department flag definitions contain duplicate names.",
    );
  }
}

async function validateOutputFiles(): Promise<void> {
  const files = await fs.readdir(OUTPUT_DIRECTORY);

  const expectedFiles = new Set(
    DEPARTMENT_FLAGS.map((department) =>
      getOutputFileName(department),
    ),
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

async function main(): Promise<void> {
  console.log("Downloading Paraguayan department flags...\n");

  validateDepartmentDefinitions();

  await fs.mkdir(OUTPUT_DIRECTORY, {
    recursive: true,
  });

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
