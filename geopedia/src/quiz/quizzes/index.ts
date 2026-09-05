/**
 * Provides centralized access to GeoPedia's available quiz content.
 *
 * Feature quizzes are registered through country and Global quiz modules,
 * while town quizzes are generated from per-country settlement datasets.
 * This module hides those storage differences behind a small unified API for
 * checking quiz availability, retrieving lightweight quiz listings, and
 * resolving complete quiz definitions.
 *
 * Application code can therefore work with country and Global quizzes without
 * needing to know whether an individual quiz is registered or generated.
 */

import { access, readdir } from "node:fs/promises";
import { join } from "node:path";

import { getTownQuiz } from "@/quiz/town/getTownQuiz";
import type {
  FeatureQuiz,
  Quiz,
  QuizDifficulty,
  QuizListing,
  TownQuiz,
} from "@/types/quiz";

import * as globalQuizzes from "./global";
import * as usaQuizzes from "./usa";

/* ======================== QUIZ REGISTRIES ======================== */

/**
 * Maps country IDs to their registered feature quizzes.
 *
 * Each country's quiz index is converted to an array so newly exported feature
 * quizzes automatically become available through the centralized quiz API.
 */
const countryFeatureQuizzes = {
  usa: Object.values(usaQuizzes),
};

/**
 * Contains every feature quiz currently registered in GeoPedia's Global
 * section.
 *
 * The Global quiz index is converted to an array so newly exported quizzes
 * automatically become available through the centralized quiz API.
 */
const registeredGlobalQuizzes: FeatureQuiz[] =
  Object.values(globalQuizzes);

/* ======================== PRIVATE HELPERS ======================== */

/**
 * Defines the display order of quiz difficulty tiers from easiest to hardest.
 */
const QUIZ_DIFFICULTY_ORDER: Record<QuizDifficulty, number> = {
  easy: 0,
  medium: 1,
  hard: 2,
  extreme: 3,
};

/**
 * Derives a quiz difficulty tier from its total number of questions.
 *
 * Difficulty represents the size of the full quiz rather than any smaller
 * group or filtered subset the user may choose later.
 *
 * @param questionCount - Total number of questions in the full quiz.
 * @returns Difficulty tier corresponding to the quiz size.
 */
function getQuizDifficulty(questionCount: number): QuizDifficulty {
  if (questionCount <= 25) {
    return "easy";
  }

  if (questionCount <= 100) {
    return "medium";
  }

  if (questionCount <= 500) {
    return "hard";
  }

  return "extreme";
}

/**
 * Compares quiz listings by difficulty so easier quizzes appear first.
 *
 * Listings with the same difficulty retain their existing registry order.
 *
 * @param firstQuiz - First quiz listing being compared.
 * @param secondQuiz - Second quiz listing being compared.
 * @returns Negative, zero, or positive value describing their display order.
 */
function compareQuizListingDifficulty(
  firstQuiz: QuizListing,
  secondQuiz: QuizListing,
): number {
  return (
    QUIZ_DIFFICULTY_ORDER[firstQuiz.difficulty] -
    QUIZ_DIFFICULTY_ORDER[secondQuiz.difficulty]
  );
}

/**
 * Returns the registered feature quizzes for a country.
 *
 * This helper is kept private because callers should use the unified country
 * quiz API rather than depending directly on the feature-quiz registry.
 *
 * @param countryId - Country whose registered feature quizzes should be
 * retrieved.
 * @returns Registered feature quizzes for the country, or an empty array when
 * the country has no registered feature quizzes.
 */
function getCountryFeatureQuizzes(countryId: string): FeatureQuiz[] {
  const normalizedCountryId = countryId.toLowerCase();

  return (
    countryFeatureQuizzes[
      normalizedCountryId as keyof typeof countryFeatureQuizzes
    ] ?? []
  );
}

/**
 * Determines whether generated town quiz data exists for a country.
 *
 * Town quizzes are generated rather than registered through handwritten quiz
 * modules, so the presence of a JSON file under `public/data/global/towns/countries/`
 * determines whether a country has a town quiz available.
 *
 * This helper is kept private because callers should use the unified country
 * quiz availability API rather than checking individual quiz types.
 *
 * @param countryId - Country whose generated town quiz data should be checked.
 * @returns Whether generated town quiz data exists for the country.
 */
async function hasCountryTownQuiz(
  countryId: string,
): Promise<boolean> {
  const normalizedCountryId = countryId.toLowerCase();

  const filePath = join(
    process.cwd(),
    "public",
    "data",
    "global",
    "towns",
    "countries",
    `${normalizedCountryId}.json`,
  );

  try {
    await access(filePath);

    return true;
  } catch {
    return false;
  }
}

/**
 * Creates the lightweight listing metadata used by quiz-selection pages.
 *
 * Shared quiz metadata is copied directly from the complete quiz definition,
 * while difficulty is derived from the quiz's full question count.
 *
 * @param quiz - Complete feature or town quiz definition.
 * @returns Lightweight metadata used to display and route to the quiz.
 */
function createQuizListing(
  quiz: FeatureQuiz | TownQuiz,
): QuizListing {
  return {
    id: quiz.id,
    name: quiz.name,
    description: quiz.description,
    kind: quiz.kind,
    difficulty: getQuizDifficulty(getQuizQuestionCount(quiz)),
  };
}

/**
 * Returns the total number of questions belonging to a complete quiz.
 *
 * Feature quizzes store their questions directly, while town quizzes use
 * their town collection as the question set.
 *
 * The returned count represents the full quiz before any user-selected
 * grouping or filtering is applied.
 *
 * @param quiz - Complete feature or town quiz definition.
 * @returns Total number of questions in the full quiz.
 */
function getQuizQuestionCount(quiz: FeatureQuiz | TownQuiz): number {
  if (quiz.kind === "feature") {
    return quiz.questions.length;
  }

  return quiz.towns.length;
}

/* ======================== COUNTRY QUIZZES ======================== */

/**
 * Determines whether a country currently has any available quizzes.
 *
 * A country is considered to have quizzes when it contains at least one
 * registered feature quiz or a generated town quiz dataset.
 *
 * @param countryId - Country whose quiz availability should be checked.
 * @returns Whether the country has at least one available quiz.
 */
export async function hasCountryQuizzes(
  countryId: string,
): Promise<boolean> {
  if (getCountryFeatureQuizzes(countryId).length > 0) {
    return true;
  }

  return hasCountryTownQuiz(countryId);
}

/**
 * Returns lightweight metadata for every quiz available for a country.
 *
 * Feature quiz listings are created from the country's registered quiz
 * definitions. When generated town data exists, a town quiz listing is added
 * without loading the complete town dataset.
 *
 * This function is intended for interfaces such as country pages that need to
 * display quiz links but do not need the complete quiz data.
 *
 * @param countryId - Country whose available quizzes should be listed.
 * @param countryName - User-facing country name used to construct the town
 * quiz title.
 * @returns Lightweight metadata for every quiz available for the country.
 */
export async function getCountryQuizListings(
  countryId: string,
  countryName: string,
): Promise<QuizListing[]> {
  const normalizedCountryId = countryId.toLowerCase();

  const quizListings: QuizListing[] = getCountryFeatureQuizzes(
    normalizedCountryId,
  ).map((quiz) => createQuizListing(quiz));

  if (await hasCountryTownQuiz(normalizedCountryId)) {
    const townQuiz = await getTownQuiz({
      countryId: normalizedCountryId,
      countryName,
    });

    quizListings.push(createQuizListing(townQuiz));
  }

  return quizListings.sort(compareQuizListingDifficulty);
}

/**
 * Returns a specific quiz available for a country.
 *
 * Registered feature quizzes are checked first. If no feature quiz matches,
 * the requested ID is checked against the country's generated town quiz ID.
 * Matching town quizzes are then loaded and constructed from their generated
 * settlement data.
 *
 * This provides country quiz routes with a single lookup function regardless
 * of the requested quiz type.
 *
 * @param countryId - Country containing the requested quiz.
 * @param quizId - Unique identifier of the requested quiz.
 * @param countryName - User-facing country name required when constructing a
 * generated town quiz.
 * @returns The matching feature or town quiz, or `undefined` when the requested
 * quiz does not exist.
 */
export async function getCountryQuiz(
  countryId: string,
  quizId: string,
  countryName: string,
): Promise<Quiz | undefined> {
  const normalizedCountryId = countryId.toLowerCase();

  const featureQuiz = getCountryFeatureQuizzes(
    normalizedCountryId,
  ).find((quiz) => quiz.id === quizId);

  if (featureQuiz) {
    return featureQuiz;
  }

  const townQuizId = `${normalizedCountryId}-towns`;

  if (quizId.toLowerCase() !== townQuizId) {
    return undefined;
  }

  if (!(await hasCountryTownQuiz(normalizedCountryId))) {
    return undefined;
  }

  return getTownQuiz({
    countryId: normalizedCountryId,
    countryName,
  });
}

/* ========================= GLOBAL QUIZZES ======================== */

/**
 * Determines whether GeoPedia's Global section currently has any available
 * quizzes.
 *
 * @returns Whether at least one Global quiz is registered.
 */
export function hasGlobalQuizzes(): boolean {
  return registeredGlobalQuizzes.length > 0;
}

/**
 * Returns lightweight metadata for every quiz available in GeoPedia's Global
 * section.
 *
 * @returns Lightweight metadata for every registered Global quiz.
 */
export function getGlobalQuizListings(): QuizListing[] {
  return registeredGlobalQuizzes
    .map((quiz) => createQuizListing(quiz))
    .sort(compareQuizListingDifficulty);
}

/**
 * Returns a specific quiz available in GeoPedia's Global section.
 *
 * @param quizId - Unique identifier of the Global quiz to retrieve.
 * @returns The matching Global quiz, or `undefined` when no registered quiz
 * uses the requested ID.
 */
export function getGlobalQuiz(
  quizId: string,
): FeatureQuiz | undefined {
  return registeredGlobalQuizzes.find((quiz) => quiz.id === quizId);
}

/**
 * Returns the IDs of every country containing at least one available quiz.
 *
 * Registered feature-quiz countries and countries containing generated town
 * quiz datasets are combined into a single deduplicated collection.
 *
 * This function is primarily used by the home world-navigation map so quiz
 * availability can be resolved server-side before its client-side MapLibre
 * interactions run.
 *
 * @returns Country IDs containing at least one feature or town quiz.
 */
export async function getCountryIdsWithQuizzes(): Promise<string[]> {
  const featureCountryIds = Object.entries(countryFeatureQuizzes)
    .filter(([, quizzes]) => quizzes.length > 0)
    .map(([countryId]) => countryId);

  const townsDirectoryPath = join(
    process.cwd(),
    "public",
    "data",
    "global",
    "towns",
    "countries",
  );

  let townCountryIds: string[] = [];

  try {
    const entries = await readdir(townsDirectoryPath, {
      withFileTypes: true,
    });

    townCountryIds = entries
      .filter(
        (entry) => entry.isFile() && entry.name.endsWith(".json"),
      )
      .map((entry) =>
        entry.name.slice(0, -".json".length).toLowerCase(),
      );
  } catch {
    // No generated town directory means there are no town quizzes available.
  }

  return [...new Set([...featureCountryIds, ...townCountryIds])];
}
