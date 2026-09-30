/**
 * Feature quiz for the Philippines' one-digit telephone area-code prefixes.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { PHILIPPINES_AREA_CODE_PREFIX_QUESTIONS } from "./data/area-codes";

const DESCRIPTION =
  `Learn all ${PHILIPPINES_AREA_CODE_PREFIX_QUESTIONS.length} landline area ` +
  `code prefixes of the Philippines. Landlines have 9 digits in Metro Manila ` +
  `and 10 digits in the provinces; for example, Pampanga's 045-456-7890 ` +
  `belongs to the 04- prefix. Mobile numbers are 11 digits and start with 09.`;

export const philippinesAreaCodePrefixesQuiz: FeatureQuiz = {
  id: "philippines-area-code-prefixes",
  name: "1-Digit Area Code Prefixes",
  description: DESCRIPTION,

  kind: "feature",
  quizTopic: "Area Codes",
  mapId: "philippines-area-code-prefixes",

  answerProperty: "prefix_1",
  answerType: "single",

  questions: PHILIPPINES_AREA_CODE_PREFIX_QUESTIONS,
};
