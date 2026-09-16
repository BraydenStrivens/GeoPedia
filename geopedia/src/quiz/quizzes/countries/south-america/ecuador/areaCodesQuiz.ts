import type { FeatureQuiz } from "@/types/quiz";

/**
 * Ecuador's geographic fixed-line telephone area codes.
 */
const ECUADOR_AREA_CODE_QUESTIONS = [
  { answer: "02", display: "02" },
  { answer: "03", display: "03" },
  { answer: "04", display: "04" },
  { answer: "05", display: "05" },
  { answer: "06", display: "06" },
  { answer: "07", display: "07" },
] as const;

/**
 * Description shown for Ecuador's Area Codes quiz.
 */
const ECUADOR_AREA_CODES_DESCRIPTION =
  `Learn all ${ECUADOR_AREA_CODE_QUESTIONS.length} geographic fixed-line ` +
  `telephone area codes used across Ecuador. Ecuadorian geographic numbers ` +
  `use a 2-digit area code beginning with 0 followed by a 7-digit local ` +
  `number. For example, a Pichincha number can be written as 02-xxxxxxx. ` +
  `When calling internationally, Ecuador's country code is +593 and the ` +
  `leading 0 is dropped, producing a format such as +593-2-xxxxxxx.`;

/**
 * Quiz for identifying Ecuador's geographic fixed-line telephone area-code
 * regions.
 */
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
