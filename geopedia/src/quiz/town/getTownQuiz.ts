/**
 * Resolves complete GeoPedia town quizzes from generated country town data.
 *
 * This module coordinates the town quiz construction pipeline by loading a
 * country's generated town dataset and passing that data into the shared town
 * quiz factory.
 *
 * Keeping this orchestration separate allows town dataset storage and quiz
 * construction to evolve independently while exposing a simple entry point to
 * callers that need a complete `TownQuiz`.
 */

import { createTownQuiz } from "@/quiz/town/createTownQuiz";
import { loadTownQuizData } from "@/quiz/town/loadTownQuizData";
import type { TownQuiz } from "@/types/quiz";

/**
 * Values required to resolve a country's generated town quiz.
 */
export type GetTownQuizOptions = {
  /** Stable country identifier used by GeoPedia. */
  countryId: string;

  /** User-facing country name displayed in the quiz title. */
  countryName: string;
};

/**
 * Loads and constructs a complete GeoPedia town quiz for a country.
 *
 * Town quizzes are generated from country-specific settlement datasets rather
 * than handwritten quiz definitions. This function loads the generated town
 * data and passes it to the shared town quiz factory.
 *
 * Map configuration is intentionally not handled here. Country-specific map
 * behavior such as the initial camera position and scoring distance is resolved
 * separately through `TownCountryConfig`.
 *
 * @param options - Country information required to construct the town quiz.
 * @param options.countryId - GeoPedia country identifier used to locate the
 * generated town dataset.
 * @param options.countryName - User-facing country name used in the quiz title.
 * @returns Fully constructed town quiz.
 */
export async function getTownQuiz({
  countryId,
  countryName,
}: GetTownQuizOptions): Promise<TownQuiz> {
  const townData = await loadTownQuizData(countryId);

  return createTownQuiz({
    countryId,
    countryName,
    towns: townData.towns,
  });
}
