/**
 * Quiz configuration for Malaysia's 1-digit postal-code prefixes.
 */

import { FeatureQuiz } from "@/types/quiz";

import { MALAYSIA_POSTAL_PREFIX_1_QUESTIONS } from "./data/postal-codes";

const MALAYSIA_POSTAL_PREFIXES_1_DESCRIPTION =
  `Learn all ${MALAYSIA_POSTAL_PREFIX_1_QUESTIONS.length} first-digit prefixes of Malaysia's ` +
  `5-digit postal codes for broad regional identification.`;

export const malaysiaPostalPrefixes1Quiz: FeatureQuiz = {
  id: "malaysia-postal-prefixes-1",
  name: "1-Digit Postal Code Prefixes",
  description: MALAYSIA_POSTAL_PREFIXES_1_DESCRIPTION,

  quizTopic: "Postal Codes",
  kind: "feature",
  mapId: "malaysia-postal-prefixes-1",

  answerProperty: "post_code",
  answerType: "single",

  questions: MALAYSIA_POSTAL_PREFIX_1_QUESTIONS,
};
