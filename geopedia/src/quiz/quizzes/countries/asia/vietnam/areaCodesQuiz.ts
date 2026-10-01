/**
 * Quiz configuration for Vietnam's telephone area codes.
 *
 * Uses the existing 63-province boundary map because the area-code regions
 * shown by Plonk It correspond to those province boundaries.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { VIETNAM_AREA_CODE_QUESTIONS } from "./data/area-codes";

const DESCRIPTION =
  `Learn all ${VIETNAM_AREA_CODE_QUESTIONS.length.toLocaleString()} telephone area codes ` +
  `of Vietnam. Domestic landline numbers are 10 digits including the leading 0; landline ` +
  `area codes start with 02, while cell phone numbers do not. For example, a Đà Nẵng ` +
  `landline may be 0236 555 1234, where 0236 identifies the Đà Nẵng area.`;

export const vietnamAreaCodesQuiz: FeatureQuiz = {
  id: "vietnam-area-codes",
  name: "Area Codes",
  description: DESCRIPTION,

  quizTopic: "Area Codes",
  kind: "feature",
  mapId: "vietnam-area-codes",

  answerProperty: "province_id",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "area_code_prefix",
        label: "2-Digit Prefix",
        valueType: "string",
      },
    ],
  },

  questions: VIETNAM_AREA_CODE_QUESTIONS,
};
