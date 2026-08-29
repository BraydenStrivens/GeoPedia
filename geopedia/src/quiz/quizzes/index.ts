/**
 * Provides centralized access to GeoPedia's quiz definitions.
 *
 * Individual quiz definitions are organized by country. Each country's
 * folder exports its quizzes through a country-level index file, while this
 * module combines those exports into one registry.
 *
 * Application code can therefore retrieve quizzes by country and quiz ID
 * without knowing where the underlying quiz definition files are stored.
 */

import * as usaQuizzes from "./usa";

/**
 * Maps a country ID to every quiz currently registered for that country.
 *
 * Each country's index module is converted to an array so adding another
 * exported quiz to that country automatically makes it available through
 * the registry.
 */
const countryQuizzes = {
  usa: Object.values(usaQuizzes),
};

/**
 * Determines whether a country currently has at least one registered quiz.
 *
 * @param countryId - Country to check.
 * @returns Whether at least one quiz is registered for the country.
 */
export function hasCountryQuizzes(countryId: string): boolean {
  return getCountryQuizzes(countryId).length > 0;
}

/**
 * Returns the IDs of every country that currently has registered quizzes.
 *
 * @returns Country IDs containing at least one quiz.
 */
export function getCountryIdsWithQuizzes(): string[] {
  return Object.entries(countryQuizzes)
    .filter(([, quizzes]) => quizzes.length > 0)
    .map(([countryId]) => countryId);
}

/**
 * Returns every quiz registered for a country.
 *
 * Country IDs are normalized to lowercase so routing and map data can use
 * different casing without affecting quiz lookup.
 *
 * @param countryId - Country whose quizzes should be retrieved.
 * @returns All quizzes registered for the country, or an empty array when
 * the country is not registered.
 */
export function getCountryQuizzes(countryId: string) {
  const normalizedCountryId = countryId.toLowerCase();

  return (
    countryQuizzes[
      normalizedCountryId as keyof typeof countryQuizzes
    ] ?? []
  );
}

/**
 * Finds a specific quiz registered for a country.
 *
 * @param countryId - Country containing the quiz.
 * @param quizId - Unique identifier of the quiz to retrieve.
 * @returns The matching quiz, or `undefined` when either the country or quiz
 * is not registered.
 */
export function getQuiz(countryId: string, quizId: string) {
  return getCountryQuizzes(countryId).find(
    (quiz) => quiz.id === quizId,
  );
}
