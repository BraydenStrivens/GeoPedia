/**
 * Quiz configuration for Cambodia's two-digit geographic landline area codes.
 *
 * Reuses the province map because each area code maps directly to one province.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { CAMBODIA_AREA_CODE_QUESTIONS } from "./data/areaCodes";

const DESCRIPTION =
  `Learn Cambodia's ${CAMBODIA_AREA_CODE_QUESTIONS.length.toLocaleString()} geographic ` +
  `landline area codes. Domestic landline numbers are 9–10 digits and use a 0XX area ` +
  `code; for example, Siem Reap uses 063, as in 063 963 123.`;

export const cambodiaAreaCodesQuiz: FeatureQuiz = {
  id: "cambodia-area-codes",
  name: "2-Digit Area Codes",
  description: DESCRIPTION,

  quizTopic: "Area Codes",
  kind: "feature",
  mapId: "cambodia-provinces",

  answerProperty: "province_id",
  answerType: "single",

  questions: CAMBODIA_AREA_CODE_QUESTIONS,
};
