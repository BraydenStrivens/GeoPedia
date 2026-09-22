/**
 * Provides construction logic for handwritten GeoPedia town quiz definitions.
 *
 * Configured town quizzes reference towns from the canonical generated country
 * dataset by stable ID and add only question-specific presentation such as
 * image prompts. Canonical town metadata is never duplicated in quiz configs.
 */

import type {
  TownData,
  TownQuiz,
  TownQuizConfig,
  TownQuizQuestion,
} from "@/types/quiz";

/**
 * Values required to construct a configured town quiz.
 */
export type CreateConfiguredTownQuizOptions = {
  /** Handwritten definition describing the specialized town quiz. */
  config: TownQuizConfig;

  /** Canonical generated towns available for the quiz's country. */
  towns: TownData[];
};

/**
 * Resolves a configured town quiz against canonical generated town data.
 *
 * Every configured town ID must exist in the supplied country dataset. Missing
 * IDs indicate stale or invalid quiz configuration and cause construction to
 * fail rather than silently removing questions from the quiz.
 *
 * @param options - Quiz configuration and canonical country town data.
 * @returns Complete town quiz containing resolved town data and prompts.
 * @throws Error when a configured town ID does not exist in the dataset.
 */
export function createConfiguredTownQuiz({
  config,
  towns,
}: CreateConfiguredTownQuizOptions): TownQuiz {
  const townsById = new Map(towns.map((town) => [town.id, town]));

  const questions: TownQuizQuestion[] = config.questions.map(
    (questionConfig) => {
      const town = townsById.get(questionConfig.townId);

      if (!town) {
        throw new Error(
          `Town quiz "${config.id}" references unknown town ID "${questionConfig.townId}".`,
        );
      }

      return {
        town,
        prompt: questionConfig.prompt,
      };
    },
  );

  return {
    id: config.id,
    name: config.name,
    description: config.description,
    kind: "town",
    questions,
  };
}
