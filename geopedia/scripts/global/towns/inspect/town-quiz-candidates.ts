import fs from "node:fs";
import readline from "node:readline";

/**
 * Raw OSM settlement structure written by extractOsmSettlements.ts.
 *
 * Only the fields relevant to this diagnostic are declared here.
 */
type RawOsmSettlement = {
  osmId: string;
  name: string;
  nameEn?: string;
  intName?: string;
  place: string;
  latitude: number;
  longitude: number;
  population?: number;
  capital?: string;
  adminLevel?: string;
  wikidata?: string;
  wikipedia?: string;
  officialName?: string;
  shortName?: string;
};

/**
 * Worldwide normalized OSM settlement dataset.
 */
const INPUT_PATH =
  "data/intermediate/global/towns/world-settlements.raw.ndjson";

/**
 * OSM settlements currently being investigated for town-quiz data quality.
 *
 * These IDs come directly from the GeoNames-to-OSM matching diagnostic, so
 * matching by ID avoids ambiguity from repeated or translated place names.
 */
const TARGET_OSM_IDS = new Set([
  /*
   * India.
   */
  "245598247", // Kallakurichi
  "2727632679", // Najafgarh

  /*
   * Iceland.
   */
  "129958272", // Reykjanesbær
  "2876969801", // Keflavík

  /*
   * Japan.
   */
  "1111454606", // Ōta ward
  "2115186710", // Sagamihara / false Aihara match
  "622866764", // Nakano ward
  "1111454640", // Minato City
  "1111454595", // Chūō ward
  "1068823657", // Ōta city
  "702987403", // Nakano city
  "1812278654", // Chūō city
]);

/**
 * Streams the raw worldwide OSM settlement file and prints the complete
 * records for the settlements currently being inspected.
 *
 * The file is processed one line at a time so the several-million-record
 * NDJSON dataset never needs to be loaded into memory at once.
 */
async function main(): Promise<void> {
  const inputStream = fs.createReadStream(INPUT_PATH, {
    encoding: "utf8",
  });

  const lineReader = readline.createInterface({
    input: inputStream,
    crlfDelay: Infinity,
  });

  const foundIds = new Set<string>();

  for await (const line of lineReader) {
    if (!line.trim()) {
      continue;
    }

    const settlement = JSON.parse(line) as RawOsmSettlement;

    if (!TARGET_OSM_IDS.has(settlement.osmId)) {
      continue;
    }

    foundIds.add(settlement.osmId);

    console.log("\n========================================");

    console.log(`OSM ${settlement.osmId}: ${settlement.name}`);

    console.log(JSON.stringify(settlement, null, 2));
  }

  console.log("\n========================================");

  console.log(
    `Found ${foundIds.size}/${TARGET_OSM_IDS.size} target settlements.`,
  );

  const missingIds = [...TARGET_OSM_IDS].filter(
    (osmId) => !foundIds.has(osmId),
  );

  if (missingIds.length > 0) {
    console.log("Missing OSM IDs:", missingIds);
  }
}

void main();
