/**
 * Provides construction logic for GeoPedia town quiz definitions.
 *
 * Normal town quizzes are data-driven rather than being defined individually
 * for each country. This module converts canonical country town data into the
 * question objects used by the shared `TownQuiz` model.
 *
 * The functions in this file are intentionally concerned only with creating
 * quiz definitions. Loading town datasets, resolving country-specific
 * configuration, scoring guesses, and rendering maps are handled elsewhere.
 */

import type {
  TownData,
  TownQuiz,
  TownQuizQuestion,
} from "@/types/quiz";

/**
 * Values required to construct a country town quiz.
 */
export type CreateTownQuizOptions = {
  /** Stable country identifier used by GeoPedia. */
  countryId: string;

  /** User-facing country name displayed in the quiz title. */
  countryName: string;

  /** Population-ranked towns available to the quiz. */
  towns: TownData[];
};

/**
 * Creates a town quiz definition for a country.
 *
 * Normal town quizzes are generated from country metadata and the country's
 * processed town dataset rather than requiring a separate handwritten quiz
 * definition for every country.
 *
 * Each canonical town is converted into a question without an explicit prompt.
 * The normal town quiz experience therefore continues using the town's name as
 * its question presentation. Specialized town quizzes can later construct
 * questions with explicit prompts while reusing the same canonical town data.
 *
 * @param options - Country metadata and town data used to build the quiz.
 * @returns Complete town quiz definition.
 */
export function createTownQuiz({
  countryId,
  countryName,
  towns,
}: CreateTownQuizOptions): TownQuiz {
  const questions: TownQuizQuestion[] = towns.map((town) => ({
    town,
  }));

  const description: string = `Learn ${questions.length} towns across ${countryName}, with filtering options to practice any desired subset.`;

  return {
    id: `${countryId}-towns`,
    name: `${countryName} Towns`,
    description,
    kind: "town",
    questions,
  };
}
