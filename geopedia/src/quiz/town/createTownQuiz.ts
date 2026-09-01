/**
 * Provides construction logic for GeoPedia town quiz definitions.
 *
 * Town quizzes are data-driven rather than being defined individually for each
 * country. This module converts country metadata and generated town data into
 * the shared `TownQuiz` model used by the application.
 *
 * The functions in this file are intentionally concerned only with creating
 * quiz definitions. Loading town datasets, resolving country-specific
 * configuration, scoring guesses, and rendering maps are handled elsewhere.
 */

import type { TownQuiz, TownQuizTown } from "@/types/quiz";

/**
 * Values required to construct a country town quiz.
 */
export type CreateTownQuizOptions = {
  /** Stable country identifier used by GeoPedia. */
  countryId: string;

  /** User-facing country name displayed in the quiz title. */
  countryName: string;

  /** Population-ranked towns available to the quiz. */
  towns: TownQuizTown[];
};

/**
 * Creates a town quiz definition for a country.
 *
 * Town quizzes are generated from country metadata and the country's processed
 * town dataset rather than requiring a separate handwritten quiz definition
 * for every country.
 *
 * The complete town dataset is attached to the quiz here. Population presets
 * and custom groups can later derive smaller town sets from this source
 * without modifying the underlying quiz definition.
 *
 * @param options - Country metadata and town data used to build the quiz.
 * @returns Complete town quiz definition.
 */
export function createTownQuiz({
  countryId,
  countryName,
  towns,
}: CreateTownQuizOptions): TownQuiz {
  return {
    id: `${countryId}-towns`,
    name: `${countryName} Towns`,
    kind: "town",
    towns,
  };
}
