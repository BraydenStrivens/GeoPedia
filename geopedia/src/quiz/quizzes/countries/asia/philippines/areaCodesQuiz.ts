/**
 * Feature quiz for the Philippines' telephone area codes.
 *
 * Area codes can be grouped by their one-digit prefix or by region.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { PHILIPPINES_AREA_CODE_QUESTIONS } from "./data/area-codes";

const DESCRIPTION =
  `Learn all ${PHILIPPINES_AREA_CODE_QUESTIONS.length} landline area codes ` +
  `of the Philippines. Landlines have 9 digits in Metro Manila and 10 digits ` +
  `in the provinces, including the leading 0, such as 032-234-5678 in Cebu. ` +
  `Mobile numbers are 11 digits and start with 09.`;

export const philippinesAreaCodesQuiz: FeatureQuiz = {
  id: "philippines-area-codes",
  name: "Area Codes",
  description: DESCRIPTION,

  kind: "feature",
  quizTopic: "Area Codes",
  mapId: "philippines-area-codes",

  answerProperty: "area_code",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "prefix_1",
        label: "1-Digit Prefix",
        valueType: "string",
      },
      {
        property: "region",
        label: "Region",
        valueType: "string-array",
      },
    ],
  },

  questions: PHILIPPINES_AREA_CODE_QUESTIONS,
};
