/**
 * Quiz configuration for Malaysia's 2-digit postal-code prefixes.
 *
 * Prefixes can be grouped by their first digit for progressively more focused
 * practice.
 */

import { FeatureQuiz } from "@/types/quiz";

import { MALAYSIA_POSTAL_PREFIX_2_QUESTIONS } from "./data/postal-codes";

const MALAYSIA_POSTAL_PREFIXES_2_DESCRIPTION =
  `Learn all ${MALAYSIA_POSTAL_PREFIX_2_QUESTIONS.length} two-digit prefixes of Malaysia's ` +
  `5-digit postal codes; group them by first digit for more focused practice.`;

export const malaysiaPostalPrefixes2Quiz: FeatureQuiz = {
  id: "malaysia-postal-prefixes-2",
  name: "2-Digit Postal Code Prefixes",
  description: MALAYSIA_POSTAL_PREFIXES_2_DESCRIPTION,

  quizTopic: "Postal Codes",
  kind: "feature",
  mapId: "malaysia-postal-prefixes-2",

  answerProperty: "post_code",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "post_code_1",
        label: "1-Digit Prefix",
        valueType: "string",
      },
    ],
  },

  questions: MALAYSIA_POSTAL_PREFIX_2_QUESTIONS,
};
