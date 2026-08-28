/**
 * Extracts named settlements from one OpenStreetMap PBF file or from every
 * `.osm.pbf` file inside a directory.
 *
 * Output is newline-delimited JSON (NDJSON), with one normalized settlement
 * object per line.
 *
 * This stage intentionally performs no ranking, label zoom calculation, or
 * spatial processing. Those operations happen later so they can be tuned
 * without rescanning large OSM PBF files.
 */

import fs from "node:fs";
import { createRequire } from "node:module";
import path from "node:path";

const require = createRequire(import.meta.url);

const OsmPbfParser =
  require("osm-pbf-parser") as new () => NodeJS.ReadWriteStream;

/**
 * OSM settlement classifications retained by GeoPedia.
 */
const INCLUDED_PLACE_TYPES = new Set([
  "city",
  "town",
  "village",
  "hamlet",
  "isolated_dwelling",
  "suburb",
]);

/**
 * Progress interval for very large regional extracts.
 */
const PROGRESS_INTERVAL = 100_000_000;

type SettlementPlaceType =
  | "city"
  | "town"
  | "village"
  | "hamlet"
  | "isolated_dwelling"
  | "suburb";

/**
 * Compact intermediate settlement representation.
 */
type RawOsmSettlement = {
  osmId: string;

  /** Primary local OSM settlement name. */
  name: string;

  place: SettlementPlaceType;

  latitude: number;

  longitude: number;

  population?: number;

  capital?: string;

  adminLevel?: string;

  /**
   * Explicit English-language name.
   *
   * This may be a transliteration or an established English exonym, so the
   * later processing stage decides whether it should actually be displayed.
   */
  nameEn?: string;

  /**
   * International settlement name.
   *
   * This is often Latin-script and can be useful when the primary OSM name
   * uses another writing system.
   */
  intName?: string;
};

/**
 * Minimal entity representation emitted by osm-pbf-parser.
 */
type OsmItem = {
  id?: number | string;

  type?: string;

  lat?: number;

  lon?: number;

  tags?: Record<string, string>;
};

/**
 * Processing statistics shared across every input PBF.
 */
type ExtractionStats = {
  parsedItems: number;

  extractedSettlements: number;

  placeCounts: Map<string, number>;
};

/**
 * Parses an OSM population value.
 */
function parsePopulation(
  value: string | undefined,
): number | undefined {
  if (!value) {
    return undefined;
  }

  const normalizedValue = value.replace(/[,\s]/g, "");

  const population = Number(normalizedValue);

  if (!Number.isFinite(population) || population <= 0) {
    return undefined;
  }

  return Math.round(population);
}

/**
 * Returns a trimmed OSM tag value or `undefined` when the tag is absent or
 * contains only whitespace.
 */
function getOptionalTag(
  tags: Record<string, string>,
  key: string,
): string | undefined {
  const value = tags[key]?.trim();

  return value ? value : undefined;
}

/**
 * Converts one OSM node into GeoPedia's compact settlement representation.
 */
function normalizeSettlement(item: OsmItem): RawOsmSettlement | null {
  if (
    item.type !== "node" ||
    item.id === undefined ||
    item.lat === undefined ||
    item.lon === undefined ||
    !item.tags
  ) {
    return null;
  }

  const tags = item.tags;

  const name = getOptionalTag(tags, "name");

  const place = getOptionalTag(tags, "place");

  if (!name || !place || !INCLUDED_PLACE_TYPES.has(place)) {
    return null;
  }

  return {
    osmId: String(item.id),

    name,

    place: place as SettlementPlaceType,

    latitude: item.lat,

    longitude: item.lon,

    population: parsePopulation(tags.population),

    capital: getOptionalTag(tags, "capital"),

    adminLevel: getOptionalTag(tags, "admin_level"),

    nameEn: getOptionalTag(tags, "name:en"),

    intName: getOptionalTag(tags, "int_name"),
  };
}

/**
 * Returns all PBF inputs represented by a file or directory argument.
 *
 * Directory inputs are scanned only one level deep and sorted by filename so
 * processing order remains deterministic.
 */
function getInputPbfPaths(inputPath: string): string[] {
  const stats = fs.statSync(inputPath);

  if (stats.isFile()) {
    if (!inputPath.toLowerCase().endsWith(".osm.pbf")) {
      throw new Error(
        `Input file must end in .osm.pbf: ${inputPath}`,
      );
    }

    return [inputPath];
  }

  if (!stats.isDirectory()) {
    throw new Error(
      `Input is neither a PBF file nor a directory: ${inputPath}`,
    );
  }

  return fs
    .readdirSync(inputPath, {
      withFileTypes: true,
    })
    .filter(
      (entry) =>
        entry.isFile() &&
        entry.name.toLowerCase().endsWith(".osm.pbf"),
    )
    .map((entry) => path.join(inputPath, entry.name))
    .sort((first, second) => first.localeCompare(second));
}

/**
 * Writes one settlement while respecting output-stream backpressure.
 */
async function writeSettlement(
  outputStream: fs.WriteStream,
  settlement: RawOsmSettlement,
): Promise<void> {
  const canContinue = outputStream.write(
    JSON.stringify(settlement) + "\n",
  );

  if (canContinue) {
    return;
  }

  await new Promise<void>((resolve) => {
    outputStream.once("drain", resolve);
  });
}

/**
 * Processes one OSM PBF and appends its normalized settlements to the shared
 * output stream.
 */
async function processPbf(
  inputPath: string,
  outputStream: fs.WriteStream,
  globalStats: ExtractionStats,
  fileIndex: number,
  fileCount: number,
): Promise<void> {
  console.log("");

  console.log(
    `[${fileIndex}/${fileCount}] ${path.basename(inputPath)}`,
  );

  console.log(
    "-".repeat(Math.min(80, path.basename(inputPath).length + 8)),
  );

  const parser = new OsmPbfParser();

  const inputStream = fs.createReadStream(inputPath);

  let fileParsedItems = 0;

  let fileExtractedSettlements = 0;

  let nextProgressReport = PROGRESS_INTERVAL;

  await new Promise<void>((resolve, reject) => {
    let processing = Promise.resolve();

    inputStream
      .pipe(parser)
      .on("data", (items: OsmItem[]) => {
        parser.pause();

        processing = processing
          .then(async () => {
            fileParsedItems += items.length;

            globalStats.parsedItems += items.length;

            for (const item of items) {
              const settlement = normalizeSettlement(item);

              if (!settlement) {
                continue;
              }

              fileExtractedSettlements++;

              globalStats.extractedSettlements++;

              globalStats.placeCounts.set(
                settlement.place,
                (globalStats.placeCounts.get(settlement.place) ?? 0) +
                  1,
              );

              await writeSettlement(outputStream, settlement);
            }

            if (fileParsedItems >= nextProgressReport) {
              console.log(
                `  Parsed entities: ${fileParsedItems.toLocaleString()}`,
              );

              console.log(
                `  Extracted settlements: ${fileExtractedSettlements.toLocaleString()}`,
              );

              nextProgressReport += PROGRESS_INTERVAL;
            }
          })
          .then(() => {
            parser.resume();
          })
          .catch(reject);
      })
      .on("end", () => {
        processing
          .then(() => {
            console.log(
              `  Finished entities: ${fileParsedItems.toLocaleString()}`,
            );

            console.log(
              `  Finished settlements: ${fileExtractedSettlements.toLocaleString()}`,
            );

            resolve();
          })
          .catch(reject);
      })
      .on("error", reject);

    inputStream.on("error", reject);
  });
}

/**
 * Prints the cumulative place-class breakdown.
 */
function printPlaceCounts(placeCounts: Map<string, number>): void {
  console.table(
    Array.from(placeCounts.entries())
      .sort((first, second) => second[1] - first[1])
      .map(([place, count]) => ({
        place,
        count,
      })),
  );
}

/**
 * Command-line usage:
 *
 * Single PBF:
 *
 * npx tsx scripts/process/towns/extractOsmSettlements.ts \
 *   data/raw/osm/us-260825.osm.pbf \
 *   data/processed/towns/us-settlements.raw.ndjson
 *
 * Directory of world-region PBFs:
 *
 * npx tsx scripts/process/towns/extractOsmSettlements.ts \
 *   data/raw/osm/world \
 *   data/processed/towns/world-settlements.raw.ndjson
 */

const [inputPath, outputPath] = process.argv.slice(2);

if (!inputPath || !outputPath) {
  console.error("Usage:");

  console.error(
    "npx tsx scripts/process/towns/extractOsmSettlements.ts <input.osm.pbf | input-directory> <output.ndjson>",
  );

  process.exit(1);
}

if (!fs.existsSync(inputPath)) {
  console.error(`Input does not exist: ${inputPath}`);

  process.exit(1);
}

const inputPbfPaths = getInputPbfPaths(inputPath);

if (inputPbfPaths.length === 0) {
  console.error(`No .osm.pbf files found in: ${inputPath}`);

  process.exit(1);
}

console.log(
  `Found ${inputPbfPaths.length} PBF file${inputPbfPaths.length === 1 ? "" : "s"}.`,
);

for (const pbfPath of inputPbfPaths) {
  console.log(`  ${path.basename(pbfPath)}`);
}

fs.mkdirSync(path.dirname(outputPath), {
  recursive: true,
});

/**
 * Existing output is intentionally overwritten so rerunning extraction never
 * silently appends duplicate settlements.
 */
const outputStream = fs.createWriteStream(outputPath, {
  encoding: "utf8",

  flags: "w",
});

const globalStats: ExtractionStats = {
  parsedItems: 0,

  extractedSettlements: 0,

  placeCounts: new Map(),
};

async function main(): Promise<void> {
  try {
    for (let index = 0; index < inputPbfPaths.length; index++) {
      await processPbf(
        inputPbfPaths[index],
        outputStream,
        globalStats,
        index + 1,
        inputPbfPaths.length,
      );
    }

    await new Promise<void>((resolve, reject) => {
      outputStream.end(() => {
        resolve();
      });

      outputStream.once("error", reject);
    });

    console.log("");

    console.log("WORLD EXTRACTION COMPLETE");

    console.log("-------------------------");

    console.log(
      `PBF files processed: ${inputPbfPaths.length.toLocaleString()}`,
    );

    console.log(
      `Total OSM entities parsed: ${globalStats.parsedItems.toLocaleString()}`,
    );

    console.log(
      `Total settlements extracted: ${globalStats.extractedSettlements.toLocaleString()}`,
    );

    console.log(`Output: ${outputPath}`);

    console.log("");

    console.log("PLACE COUNTS");

    console.log("------------");

    printPlaceCounts(globalStats.placeCounts);
  } catch (error) {
    outputStream.destroy();

    console.error("");

    console.error("Settlement extraction failed:", error);

    process.exitCode = 1;
  }
}

void main();
