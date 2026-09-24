/**
 * Feature quiz configuration for Namibia's geographic telephone area codes.
 *
 * Namibia uses seven geographic landline area codes from 061 through 067.
 * The complete area code is used directly as both the quiz answer and the
 * map feature identity.
 */

import type { FeatureQuiz, FeatureQuizQuestion } from "@/types/quiz";

const NAMIBIA_AREA_CODE_QUESTIONS: FeatureQuizQuestion[] = [
  { answer: "061" },
  { answer: "062" },
  { answer: "063" },
  { answer: "064" },
  { answer: "065" },
  { answer: "066" },
  { answer: "067" },
];

const NAMIBIA_AREA_CODES_DESCRIPTION =
  "Learn all 7 geographic telephone area codes of Namibia.";

export const namibiaAreaCodesQuiz: FeatureQuiz = {
  id: "namibia-area-codes",
  name: "Area Codes",
  description: NAMIBIA_AREA_CODES_DESCRIPTION,

  kind: "feature",
  mapId: "namibia-area-codes",

  answerProperty: "area_code",
  answerType: "single",

  questions: NAMIBIA_AREA_CODE_QUESTIONS,
};
