/**
 * Quiz for Thailand's 21 geographic landline area-code regions.
 * Regions can be grouped by their one-digit area-code prefix.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { THAILAND_AREA_CODE_PREFIX_2_QUESTIONS } from "./data/areaCodes";

const DESCRIPTION =
  `Learn Thailand's ${THAILAND_AREA_CODE_PREFIX_2_QUESTIONS.length} geographic landline area codes. ` +
  `Domestic landlines have 9 digits: 02-xxx-xxxx around Bangkok or 0xx-xxx-xxx elsewhere. ` +
  `Mobile numbers have 10 digits and begin with 06, 08, or 09.`;

export const thailandAreaCodePrefixes2Quiz: FeatureQuiz = {
  id: "thailand-area-code-prefixes-2",
  name: "2-Digit Area Code Prefixes",
  description: DESCRIPTION,

  quizTopic: "Area Codes",
  kind: "feature",
  mapId: "thailand-area-code-prefixes-2",

  answerProperty: "area_code_prefix",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "area_code_group",
        label: "1-Digit Prefix",
        valueType: "string",
      },
    ],
  },

  questions: THAILAND_AREA_CODE_PREFIX_2_QUESTIONS,
};
