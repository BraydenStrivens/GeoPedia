/**
 * Downloads Ecuadorian province flags from Wikimedia Commons.
 *
 * The script first tries several common exact Commons filenames. If none of
 * those exist, it searches Wikimedia Commons for likely SVG flag files using
 * the province name.
 *
 * Output:
 *
 * public/data/countries/ecuador/flags/
 *
 * Runtime filenames use GeoPedia's stable Ecuador province IDs:
 *
 * ec01.svg
 * ec02.svg
 * ...
 * ec24.svg
 */

import fs from "node:fs/promises";
import path from "node:path";

/* -------------------------------------------------------------------------- */
/* Paths                                                                      */
/* -------------------------------------------------------------------------- */

const OUTPUT_DIRECTORY = path.resolve(
  "public/data/countries/ecuador/flags",
);

/* -------------------------------------------------------------------------- */
/* Wikimedia Commons                                                         */
/* -------------------------------------------------------------------------- */

const WIKIMEDIA_COMMONS_API_URL =
  "https://commons.wikimedia.org/w/api.php";

const WIKIMEDIA_REQUEST_DELAY_MS = 5000;

const MAX_WIKIMEDIA_REQUEST_ATTEMPTS = 5;

const MAX_SEARCH_RESULTS = 20;

type ProvinceFlagDefinition = {
  id: string;
  name: string;
  commonsFileName?: string;
};

const PROVINCE_FLAGS: ProvinceFlagDefinition[] = [
  { id: "EC01", name: "Azuay" },
  { id: "EC02", name: "Bolívar" },
  { id: "EC03", name: "Cañar" },
  { id: "EC04", name: "Carchi" },
  { id: "EC05", name: "Cotopaxi" },
  { id: "EC06", name: "Chimborazo" },
  { id: "EC07", name: "El Oro" },
  { id: "EC08", name: "Esmeraldas" },
  { id: "EC09", name: "Guayas" },
  { id: "EC10", name: "Imbabura" },
  { id: "EC11", name: "Loja" },
  { id: "EC12", name: "Los Ríos" },
  { id: "EC13", name: "Manabí" },
  { id: "EC14", name: "Morona Santiago" },
  { id: "EC15", name: "Napo" },
  { id: "EC16", name: "Pastaza" },
  { id: "EC17", name: "Pichincha" },
  { id: "EC18", name: "Tungurahua" },
  { id: "EC19", name: "Zamora Chinchipe" },
  { id: "EC20", name: "Galápagos" },
  { id: "EC21", name: "Sucumbíos" },
  { id: "EC22", name: "Orellana" },
  { id: "EC23", name: "Santo Domingo de los Tsáchilas" },
  { id: "EC24", name: "Santa Elena" },
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
        "User-Agent": "GeoPedia/1.0 ecuador-province-flag-downloader",
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
  province: ProvinceFlagDefinition,
): string[] {
  if (province.commonsFileName) {
    return [province.commonsFileName];
  }

  return [
    `Flag of ${province.name}.svg`,
    `Flag of ${province.name} Province.svg`,
    `Flag of ${province.name} Province, Ecuador.svg`,
    `Flag of the Province of ${province.name}.svg`,
    `Bandera de ${province.name}.svg`,
    `Bandera de la provincia de ${province.name}.svg`,
    `Bandera Provincia de ${province.name}.svg`,
    `Bandera Provincia ${province.name}.svg`,
  ];
}

async function tryGetCommonsSvgUrl(
  province: ProvinceFlagDefinition,
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

/**
 * Searches Wikimedia Commons' File namespace for likely flag files.
 */
async function searchCommonsForProvinceFlag(
  province: ProvinceFlagDefinition,
): Promise<WikimediaPage[]> {
  const searchQueries = [
    `${province.name} flag Ecuador`,
    `${province.name} bandera Ecuador`,
    `${province.name} province flag`,
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
      `${province.name} Commons search`,
    );

    if (!response.ok) {
      throw new Error(
        `Wikimedia search failed for ${province.name}: ` +
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
 * Gives likely province-flag filenames a score.
 *
 * This deliberately favors titles that:
 *
 * - contain the province name
 * - contain "flag" or "bandera"
 * - mention Ecuador
 * - are SVG files
 *
 * It penalizes obvious maps, seals, coats of arms, municipalities, cantons,
 * and other unrelated graphics.
 */
function scoreCommonsCandidate(
  province: ProvinceFlagDefinition,
  page: WikimediaPage,
): number {
  const title = (page.title ?? "").toLowerCase();

  const provinceName = province.name.toLowerCase();

  let score = 0;

  if (title.includes(provinceName)) {
    score += 100;
  }

  if (title.includes("flag")) {
    score += 50;
  }

  if (title.includes("bandera")) {
    score += 50;
  }

  if (title.includes("ecuador")) {
    score += 25;
  }

  if (title.includes("province")) {
    score += 15;
  }

  if (title.includes("provincia")) {
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
    "canton",
    "cantón",
    "city",
    "parish",
    "parroquia",
  ];

  for (const term of unwantedTerms) {
    if (title.includes(term)) {
      score -= 100;
    }
  }

  return score;
}

function chooseBestCommonsCandidate(
  province: ProvinceFlagDefinition,
  candidates: WikimediaPage[],
): WikimediaPage | null {
  const scoredCandidates = candidates
    .map((candidate) => ({
      candidate,
      score: scoreCommonsCandidate(province, candidate),
    }))
    .sort((a, b) => b.score - a.score);

  if (scoredCandidates.length === 0) {
    return null;
  }

  console.log("  Candidate Commons files:");

  for (const entry of scoredCandidates.slice(0, 10)) {
    console.log(
      `    ${entry.score.toString().padStart(3)}  ${entry.candidate.title}`,
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
   * If the top two candidates have exactly the same score, do not choose
   * automatically. That makes ambiguous cases visible instead of guessing.
   */
  const second = scoredCandidates[1];

  if (second && second.score === best.score) {
    console.warn(
      `  Top Commons candidates for ${province.name} are tied.`,
    );

    return null;
  }

  return best.candidate;
}

/* -------------------------------------------------------------------------- */
/* Combined lookup                                                            */
/* -------------------------------------------------------------------------- */

async function getCommonsSvgUrl(
  province: ProvinceFlagDefinition,
): Promise<string> {
  const exactCandidates = getCommonsFileNameCandidates(province);

  for (const commonsFileName of exactCandidates) {
    console.log(`  Trying: ${commonsFileName}`);

    const imageUrl = await tryGetCommonsSvgUrl(
      province,
      commonsFileName,
    );

    if (imageUrl) {
      return imageUrl;
    }
  }

  console.log(
    `  No exact filename matched ${province.name}. Searching Commons...`,
  );

  const searchResults = await searchCommonsForProvinceFlag(province);

  const bestCandidate = chooseBestCommonsCandidate(
    province,
    searchResults,
  );

  const imageUrl = bestCandidate?.imageinfo?.[0]?.url;

  if (!bestCandidate?.title || !imageUrl) {
    throw new Error(
      `Could not confidently identify the Wikimedia Commons flag for ` +
        `${province.name}.\n\n` +
        `Review the candidate filenames printed above and add the correct ` +
        `one as commonsFileName in PROVINCE_FLAGS.`,
    );
  }

  console.log(`  Selected: ${bestCandidate.title}`);

  return imageUrl;
}

/* -------------------------------------------------------------------------- */
/* Downloading                                                                */
/* -------------------------------------------------------------------------- */

function getOutputFileName(province: ProvinceFlagDefinition): string {
  return `${province.id.toLowerCase()}.svg`;
}

async function downloadProvinceFlag(
  province: ProvinceFlagDefinition,
): Promise<void> {
  const outputFileName = getOutputFileName(province);

  const outputPath = path.join(OUTPUT_DIRECTORY, outputFileName);

  try {
    await fs.access(outputPath);

    console.log(
      `${province.id}  ${province.name} -> already exists, skipping`,
    );

    return;
  } catch {
    /*
     * File does not exist yet.
     */
  }

  console.log(`${province.id}  ${province.name}`);

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

  const beginning = svg.slice(0, 2000).toLowerCase();

  if (!beginning.includes("<svg")) {
    throw new Error(
      `Downloaded file for ${province.name} does not appear to be SVG.`,
    );
  }

  await fs.writeFile(outputPath, svg, "utf8");

  console.log(`  Saved: ${outputFileName}\n`);
}

/* -------------------------------------------------------------------------- */
/* Validation                                                                 */
/* -------------------------------------------------------------------------- */

function validateProvinceDefinitions(): void {
  if (PROVINCE_FLAGS.length !== 24) {
    throw new Error(
      `Expected 24 Ecuadorian provinces but found ` +
        `${PROVINCE_FLAGS.length}.`,
    );
  }

  const ids = new Set(PROVINCE_FLAGS.map((province) => province.id));

  if (ids.size !== 24) {
    throw new Error(
      "Ecuadorian province flag definitions contain duplicate IDs.",
    );
  }

  const names = new Set(
    PROVINCE_FLAGS.map((province) => province.name),
  );

  if (names.size !== 24) {
    throw new Error(
      "Ecuadorian province flag definitions contain duplicate names.",
    );
  }
}

async function validateOutputFiles(): Promise<void> {
  const files = await fs.readdir(OUTPUT_DIRECTORY);

  const expectedFiles = new Set(
    PROVINCE_FLAGS.map((province) => getOutputFileName(province)),
  );

  const missingFiles = Array.from(expectedFiles).filter(
    (fileName) => !files.includes(fileName),
  );

  if (missingFiles.length > 0) {
    throw new Error(
      `Missing downloaded province flags: ${missingFiles.join(", ")}`,
    );
  }
}

/* -------------------------------------------------------------------------- */
/* Main                                                                       */
/* -------------------------------------------------------------------------- */

async function main(): Promise<void> {
  console.log("Downloading Ecuadorian province flags...\n");

  validateProvinceDefinitions();

  await fs.mkdir(OUTPUT_DIRECTORY, {
    recursive: true,
  });

  for (const province of PROVINCE_FLAGS) {
    await downloadProvinceFlag(province);
  }

  await validateOutputFiles();

  console.log("");

  console.log(
    `Downloaded or verified ${PROVINCE_FLAGS.length} province flags.`,
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
