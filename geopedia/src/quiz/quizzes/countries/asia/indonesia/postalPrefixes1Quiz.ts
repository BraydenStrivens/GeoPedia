/**
 * Quiz configuration for Indonesia's 1-digit postal-code prefixes.
 */

import { FeatureQuiz } from "@/types/quiz";

import { INDONESIA_POSTAL_PREFIX_1_QUESTIONS } from "./data/postal-prefixes";

const INDONESIA_POSTAL_PREFIXES_1_DESCRIPTION =
  `Learn all ${INDONESIA_POSTAL_PREFIX_1_QUESTIONS.length} first-digit prefixes ` +
  `of Indonesia's 5-digit postal codes. The first digit identifies a broad geographic ` +
  `region; for example, 4---- covers West Java and Banten, while 9---- covers Sulawesi, ` +
  `Maluku, and Papua.`;

export const indonesiaPostalPrefixes1Quiz: FeatureQuiz = {
  id: "indonesia-postal-prefixes-1",
  name: "1-Digit Postal Code Prefixes",
  description: INDONESIA_POSTAL_PREFIXES_1_DESCRIPTION,

  kind: "feature",
  quizTopic: "Postal Codes",
  mapId: "indonesia-postal-prefixes-1",

  answerProperty: "prefix_1",
  answerType: "single",

  questions: INDONESIA_POSTAL_PREFIX_1_QUESTIONS,
};
