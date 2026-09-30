/**
 * Quiz configuration for Indonesia's 2-digit landline area-code prefixes.
 *
 * Prefixes can be grouped by their first significant digit for more focused
 * practice.
 */

import { FeatureQuiz } from "@/types/quiz";

import { INDONESIA_AREA_CODE_PREFIX_2_QUESTIONS } from "./data/area-code-prefixes";

const INDONESIA_AREA_CODE_PREFIXES_2_DESCRIPTION =
  `Learn the ${INDONESIA_AREA_CODE_PREFIX_2_QUESTIONS.length} 2-digit landline area-code ` +
  `prefixes of Indonesia. Indonesian landline numbers are 9-11 digits and use 0 + a 2-3 ` +
  `digit area code + a 6-8 digit local number, e.g. Bali 0361-234567. ` +
  `Mobile numbers instead begin with 08, such as 0812-3456-7890.`;

export const indonesiaAreaCodePrefixes2Quiz: FeatureQuiz = {
  id: "indonesia-area-code-prefixes-2",
  name: "2-Digit Area Code Prefixes",
  description: INDONESIA_AREA_CODE_PREFIXES_2_DESCRIPTION,

  kind: "feature",
  mapId: "indonesia-area-code-prefixes-2",

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

  questions: INDONESIA_AREA_CODE_PREFIX_2_QUESTIONS,
};
