/**
 * Loads and validates the generated town datasets used by GeoPedia town
 * quizzes.
 *
 * Country town data is generated ahead of time and stored as JSON files under
 * `public/data/towns`. This module provides the server-side boundary between
 * those generated files and the application's strongly typed quiz models.
 *
 * Parsed JSON is validated before being returned so malformed, outdated, or
 * otherwise invalid generated data fails close to the loading boundary rather
 * than causing less obvious errors later in town quiz logic.
 */

import { readFile } from "node:fs/promises";
import path from "node:path";

import type { TownQuizData, TownQuizTown } from "@/types/quiz";

/**
 * Valid country IDs used by generated town-data filenames.
 *
 * GeoPedia's country identifiers use lowercase three-letter country codes,
 * including custom codes such as `xkx`.
 */
const COUNTRY_ID_PATTERN = /^[a-z]{3}$/;

/**
 * Returns whether an unknown value contains the runtime shape required by a
 * town quiz location.
 *
 * This validates generated JSON at the application boundary so malformed or
 * stale town data fails with a useful error rather than producing failures
 * later inside quiz logic.
 *
 * @param value - Unknown parsed JSON value.
 * @returns Whether the value is a valid town-quiz town.
 */
function isTownQuizTown(value: unknown): value is TownQuizTown {
  if (typeof value !== "object" || value === null) {
    return false;
  }

  const town = value as Record<string, unknown>;

  const nativeName = town.nativeName;

  const hasValidNativeName =
    nativeName === undefined ||
    (typeof nativeName === "string" && nativeName.trim().length > 0);

  return (
    typeof town.id === "string" &&
    typeof town.name === "string" &&
    town.name.trim().length > 0 &&
    hasValidNativeName &&
    typeof town.latitude === "number" &&
    Number.isFinite(town.latitude) &&
    typeof town.longitude === "number" &&
    Number.isFinite(town.longitude) &&
    typeof town.population === "number" &&
    Number.isFinite(town.population) &&
    typeof town.populationRank === "number" &&
    Number.isInteger(town.populationRank) &&
    typeof town.isCapital === "boolean"
  );
}

/**
 * Returns whether parsed JSON has the structure required by a generated town
 * quiz dataset.
 *
 * @param value - Unknown parsed JSON value.
 * @returns Whether the value is a valid town quiz dataset.
 */
function isTownQuizData(value: unknown): value is TownQuizData {
  if (typeof value !== "object" || value === null) {
    return false;
  }

  const data = value as Record<string, unknown>;

  return (
    Array.isArray(data.towns) && data.towns.every(isTownQuizTown)
  );
}

/**
 * Loads the generated town dataset belonging to a country.
 *
 * Generated datasets are stored under `public/data/towns` using GeoPedia's
 * lowercase three-letter country IDs as filenames.
 *
 * This function is intended for server-side quiz construction. Reading the
 * generated file directly avoids an unnecessary HTTP request from the
 * application to its own public directory.
 *
 * @param countryId - Lowercase three-letter country identifier.
 * @returns Validated town quiz dataset belonging to the country.
 * @throws When the country ID is invalid, the file cannot be read, or the
 * generated JSON does not contain the expected town-data structure.
 */
export async function loadTownQuizData(
  countryId: string,
): Promise<TownQuizData> {
  if (!COUNTRY_ID_PATTERN.test(countryId)) {
    throw new Error(`Invalid town quiz country ID: "${countryId}".`);
  }

  const filePath = path.join(
    process.cwd(),
    "public",
    "data",
    "global",
    "towns",
    "countries",
    `${countryId}.json`,
  );

  const fileContents = await readFile(filePath, "utf8");

  const parsedData: unknown = JSON.parse(fileContents);

  if (!isTownQuizData(parsedData)) {
    throw new Error(
      `Invalid town quiz data for country "${countryId}".`,
    );
  }

  return parsedData;
}
