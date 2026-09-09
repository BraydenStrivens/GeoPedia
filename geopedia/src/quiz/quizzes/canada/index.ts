/**
 * Provides a single export point for all Canada quiz definitions.
 *
 * Each Canada quiz is defined in its own file and re-exported here. The root
 * quiz registry can then import all Canada quizzes from this folder at once
 * without needing to know about each individual quiz file.
 *
 * New Canada quizzes should be exported here after their quiz
 * definition is created.
 */

export { canadaCensusDivisionsQuiz } from "./canadaCensusDivisionsQuiz";
export { canadaPhoneCodesQuiz } from "./canadaPhoneCodesQuiz";
export { canadaProvinceFlagsQuiz } from "./canadaProvinceFlagsQuiz";
export { canadaProvincesQuiz } from "./canadaProvincesQuiz";
