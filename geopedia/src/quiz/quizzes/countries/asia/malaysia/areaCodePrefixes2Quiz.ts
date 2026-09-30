/**
 * Quiz configuration for Malaysia's 2-digit telephone area-code prefixes.
 *
 * Area codes can be grouped by their first significant digit for more focused
 * practice.
 */

import { FeatureQuiz } from "@/types/quiz";

import { MALAYSIA_AREA_CODE_PREFIX_2_QUESTIONS } from "./data/area-codes";

const MALAYSIA_AREA_CODE_PREFIXES_2_DESCRIPTION =
  `Learn all ${MALAYSIA_AREA_CODE_PREFIX_2_QUESTIONS.length} two-digit prefixes of ` +
  `Malaysia's geographic landline area codes; group them by first digit for more focused ` +
  `practice. Landline numbers are 10 digits including the area code; for example, ` +
  `044-123 4567 is a landline, while a mobile number such as 019-876 5432 begins with 01 ` +
  `and is not geographically tied to a state.`;

export const malaysiaAreaCodePrefixes2Quiz: FeatureQuiz = {
  id: "malaysia-area-code-prefixes-2",
  name: "2-Digit Area Code Prefixes",
  description: MALAYSIA_AREA_CODE_PREFIXES_2_DESCRIPTION,

  quizTopic: "Area Codes",
  kind: "feature",
  mapId: "malaysia-area-code-prefixes-2",

  answerProperty: "area_code",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "area_code_1",
        label: "1-Digit Prefix",
        valueType: "string",
      },
    ],
  },

  questions: MALAYSIA_AREA_CODE_PREFIX_2_QUESTIONS,
};
