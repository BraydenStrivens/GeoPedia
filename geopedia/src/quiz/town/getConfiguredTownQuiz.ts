/**
 * Resolves complete configured GeoPedia town quizzes from handwritten quiz
 * definitions and generated country town data.
 *
 * The handwritten configuration determines which canonical towns participate
 * and supplies question-specific prompts, while names, coordinates, population
 * data, and other town metadata continue to come from the generated dataset.
 */

import { createConfiguredTownQuiz } from "@/quiz/town/createConfiguredTownQuiz";
import { loadTownQuizData } from "@/quiz/town/loadTownQuizData";
import type { TownQuiz, TownQuizConfig } from "@/types/quiz";

/**
 * Values required to resolve a configured town quiz.
 */
export type GetConfiguredTownQuizOptions = {
  /** Stable country identifier used to locate generated town data. */
  countryId: string;

  /** Handwritten definition of the specialized town quiz. */
  config: TownQuizConfig;
};

/**
 * Loads canonical country town data and resolves a configured town quiz against
 * it.
 *
 * @param options - Country identifier and specialized quiz configuration.
 * @returns Fully constructed configured town quiz.
 */
export async function getConfiguredTownQuiz({
  countryId,
  config,
}: GetConfiguredTownQuizOptions): Promise<TownQuiz> {
  const townData = await loadTownQuizData(countryId);

  return createConfiguredTownQuiz({
    config,
    towns: townData.towns,
  });
}
