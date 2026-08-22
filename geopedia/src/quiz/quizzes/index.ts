/**
 * Provides centralized access to GeoPedia's country quiz definitions.
 *
 * Each country's quizzes are stored in its own folder and exported through
 * that folder's index file. This file combines those exports into a country
 * quiz registry so the rest of the application can retrieve quizzes using
 * country and quiz IDs without needing to know where the quiz files are
 * physically stored.
 *
 * New countries should be imported and added to `countryQuizzes` as their
 * quizzes are added to GeoPedia.
 */

import * as usaQuizzes from "./usa";

/**
 * Maps each country ID to all quiz definitions exported for that country.
 *
 * Object.values() converts each country's module exports into an array,
 * allowing multiple quiz files to be added to a country without manually
 * maintaining a separate quiz array.
 */
const countryQuizzes = {
  usa: Object.values(usaQuizzes),
};

/**
 * Returns all quizzes available for a country.
 *
 * Country IDs are normalized to lowercase so lookups remain consistent
 * regardless of how the ID was provided by routing or map data.
 */
export function getCountryQuizzes(countryId: string) {
  const normalizedCountryId = countryId.toLowerCase();

  return (
    countryQuizzes[normalizedCountryId as keyof typeof countryQuizzes] ??
    []
  );
}

/**
 * Finds a specific quiz belonging to a country.
 *
 * Returns `undefined` when the country does not exist or when no quiz
 * with the provided quiz ID is registered for that country.
 */
export function getQuiz(countryId: string, quizId: string) {
  return getCountryQuizzes(countryId).find((quiz) => quiz.id === quizId);
}
