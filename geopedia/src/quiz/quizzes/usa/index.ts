/**
 * Provides a single export point for all United States quiz definitions.
 *
 * Each US quiz is defined in its own file and re-exported here. The root
 * quiz registry can then import all US quizzes from this folder at once
 * without needing to know about each individual quiz file.
 *
 * New United States quizzes should be exported here after their quiz
 * definition is created.
 */

export { usAreaCodesQuiz } from "./areaCodesQuiz";
export { usCountiesQuiz } from "./countiesQuiz";
export { usStateAbbreviationsQuiz } from "./stateAbbreviationsQuiz";
export { usStateFlagsQuiz } from "./stateFlags";
export { usStatesQuiz } from "./statesQuiz";
export { usZip1Quiz } from "./zip1Quiz";
export { usZip2Quiz } from "./zip2Quiz";
export { usZip3Quiz } from "./zip3Quiz";
