/**
 * Defines Chile's geographic landline area-code quiz.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { CHILE_AREA_CODES } from "./data/areaCodes";

const CHILE_AREA_CODE_QUESTIONS: FeatureQuiz["questions"] =
  Object.entries(CHILE_AREA_CODES).map(([areaCode]) => ({
    answer: areaCode,
  }));

const CHILE_AREA_CODES_DESCRIPTION =
  `Learn the ${CHILE_AREA_CODE_QUESTIONS.length} geographic landline ` +
  `area codes of Chile. Chile uses the country calling code +56.`;

export const chileAreaCodesQuiz: FeatureQuiz = {
  id: "chile-area-codes",
  name: "Area Codes",
  description: CHILE_AREA_CODES_DESCRIPTION,

  kind: "feature",
  mapId: "chile-area-codes",

  answerProperty: "area_code_id",
  answerType: "single",

  questions: CHILE_AREA_CODE_QUESTIONS,
};
