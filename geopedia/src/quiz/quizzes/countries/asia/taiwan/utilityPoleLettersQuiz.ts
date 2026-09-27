/**
 * Feature quiz for Taiwan's utility-pole first-letter regions.
 *
 * Questions ask for the first letter found on Taiwan utility-pole plates.
 * Each letter corresponds to a large geographic grid region, allowing the
 * plate to provide a location clue in GeoGuessr.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { TAIWAN_UTILITY_POLE_LETTER_QUESTIONS } from "./data/utilityPoleLetters";

const DESCRIPTION =
  `Learn the ${TAIWAN_UTILITY_POLE_LETTER_QUESTIONS.length} first-letter ` +
  `regions used on Taiwan utility-pole plates. The first letter identifies ` +
  `a large geographic grid region, making utility-pole plates useful for ` +
  `narrowing down your location.`;

export const taiwanUtilityPoleLettersQuiz: FeatureQuiz = {
  id: "taiwan-utility-pole-letters",
  name: "Utility Pole First Letters",
  description: DESCRIPTION,

  kind: "feature",
  mapId: "taiwan-utility-pole-letters",

  answerProperty: "utility_pole_letter",
  answerType: "single",

  questions: TAIWAN_UTILITY_POLE_LETTER_QUESTIONS,
};
