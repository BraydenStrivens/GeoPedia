/**
 * Defines Chile's first-digit postal-code prefix quiz.
 *
 * Several prefixes may correspond to the same geographic feature, so the quiz
 * uses multiple-answer feature matching.
 */

import type { FeatureQuiz } from "@/types/quiz";

const CHILE_POSTAL_PREFIX_QUESTIONS: FeatureQuiz["questions"] = [
  { answer: "1", display: "1------" },
  { answer: "2", display: "2------" },
  { answer: "3", display: "3------" },
  { answer: "4", display: "4------" },
  { answer: "5", display: "5------" },
  { answer: "6", display: "6------" },
  { answer: "7", display: "7------" },
  { answer: "8", display: "8------" },
  { answer: "9", display: "9------" },
];

const CHILE_POSTAL_PREFIXES_DESCRIPTION =
  `Learn the ${CHILE_POSTAL_PREFIX_QUESTIONS.length} first-digit postal ` +
  `code prefixes of Chile. Chilean postal codes contain 7 digits, and the first digit identifies a broad ` +
  `geographic area. For example: 8320114 → 8------ (Santiago), ` +
  `1000003 → 1------ (Arica), and 2520847 → 2------ (Viña del Mar).`;

export const chilePostalPrefixesQuiz: FeatureQuiz = {
  id: "chile-postal-prefixes",
  name: "1-Digit Postal Prefixes",
  description: CHILE_POSTAL_PREFIXES_DESCRIPTION,

  kind: "feature",
  mapId: "chile-postal-prefixes",

  answerProperty: "postal_prefixes",
  answerType: "multiple",

  questions: CHILE_POSTAL_PREFIX_QUESTIONS,
};
