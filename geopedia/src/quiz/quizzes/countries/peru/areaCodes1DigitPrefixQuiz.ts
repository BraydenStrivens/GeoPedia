import type { FeatureQuiz } from "@/types/quiz";

const PERU_AREA_CODE_PREFIX_QUESTIONS: FeatureQuiz["questions"] = [
  { answer: "1" },
  { answer: "4", display: "4-" },
  { answer: "5", display: "5-" },
  { answer: "6", display: "6-" },
  { answer: "7", display: "7-" },
  { answer: "8", display: "8-" },
];

const PERU_AREA_CODE_PREFIXES_DESCRIPTION =
  `Learn all ${PERU_AREA_CODE_PREFIX_QUESTIONS.length} first-digit geographic ` +
  `telephone area-code prefixes used across Peru. Each prefix is the first ` +
  `digit of an otherwise 2-digit landline area code, such as 8 in Cusco's ` +
  `area code 84, giving a number like +51 84 234 567. ` +
  `Lima and Callao are the exception, using the single-digit area code ` +
  `1, as in +51 1 234 5678. Mobile numbers do not use these geographic area ` +
  `codes and instead use a 9-digit number beginning with 9, such as ` +
  `+51 912 345 678.`;

export const peruAreaCodes1DigitPrefixQuiz: FeatureQuiz = {
  id: "peru-area-code-prefixes",
  name: "1 Digit Area Code Prefixes",
  description: PERU_AREA_CODE_PREFIXES_DESCRIPTION,

  kind: "feature",
  mapId: "peru-area-code-prefixes",

  answerProperty: "area_code_prefix",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
  },

  questions: PERU_AREA_CODE_PREFIX_QUESTIONS,
};
