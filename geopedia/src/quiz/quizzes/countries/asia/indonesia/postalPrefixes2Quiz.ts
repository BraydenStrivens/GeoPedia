/**
 * Quiz configuration for Indonesia's 2-digit postal-code prefixes.
 *
 * Prefixes can be grouped by their first digit for more focused practice.
 */

import { FeatureQuiz } from "@/types/quiz";

import { INDONESIA_POSTAL_PREFIX_2_QUESTIONS } from "./data/postal-prefixes";

const INDONESIA_POSTAL_PREFIXES_2_DESCRIPTION =
  `Learn all ${INDONESIA_POSTAL_PREFIX_2_QUESTIONS.length} two-digit prefixes of ` +
  `Indonesia's 5-digit postal codes. The first two digits narrow the location to a ` +
  `kabupaten or kota area; for example, 40--- corresponds to Bandung ` +
  `in West Java, while 80--- corresponds to Denpasar in Bali. ` +
  `Group prefixes by their first digit for more focused practice.`;

export const indonesiaPostalPrefixes2Quiz: FeatureQuiz = {
  id: "indonesia-postal-prefixes-2",
  name: "2-Digit Postal Code Prefixes",
  description: INDONESIA_POSTAL_PREFIXES_2_DESCRIPTION,

  kind: "feature",
  quizTopic: "Postal Codes",
  mapId: "indonesia-postal-prefixes-2",

  answerProperty: "prefix_2",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "prefix_1",
        label: "1-Digit Prefix",
        valueType: "string",
      },
    ],
  },

  questions: INDONESIA_POSTAL_PREFIX_2_QUESTIONS,
};
