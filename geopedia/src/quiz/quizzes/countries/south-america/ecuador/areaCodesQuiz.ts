/**
 * Quiz configuration for Ecuador's geographic fixed-line telephone area codes.
 */

import type { FeatureQuiz } from "@/types/quiz";

const ECUADOR_AREA_CODE_QUESTIONS = [
  { answer: "02" },
  { answer: "03" },
  { answer: "04" },
  { answer: "05" },
  { answer: "06" },
  { answer: "07" },
] as const;

const ECUADOR_AREA_CODES_DESCRIPTION =
  `Learn all ${ECUADOR_AREA_CODE_QUESTIONS.length} geographic fixed-line ` +
  `telephone area codes used across Ecuador. Ecuadorian geographic numbers ` +
  `use a 2-digit area code beginning with 0 followed by a 7-digit local ` +
  `number. For example, a Pichincha number can be written as 02-xxxxxxx. ` +
  `When calling internationally, Ecuador's country code is +593 and the ` +
  `leading 0 is dropped, producing a format such as +593-2-xxxxxxx.`;

export const ecuadorAreaCodesQuiz: FeatureQuiz = {
  id: "ecuador-area-codes",
  name: "Area Codes",
  description: ECUADOR_AREA_CODES_DESCRIPTION,

  kind: "feature",
  mapId: "ecuador-area-codes",

  answerProperty: "area_code_id",
  answerType: "single",

  questions: [...ECUADOR_AREA_CODE_QUESTIONS],
};
