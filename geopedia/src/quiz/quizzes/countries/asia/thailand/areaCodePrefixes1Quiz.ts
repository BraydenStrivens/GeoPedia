/**
 * Quiz for Thailand's five broad geographic landline area-code
 * prefixes. Reuses the dissolved one-digit prefix polygons.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { THAILAND_AREA_CODE_PREFIX_1_QUESTIONS } from "./data/areaCodes";

const DESCRIPTION =
  `Learn Thailand's ${THAILAND_AREA_CODE_PREFIX_1_QUESTIONS.length} geographic landline area-code prefix regions. ` +
  `Domestic landlines have 9 digits: 02-xxx-xxxx around Bangkok or 0xx-xxx-xxx elsewhere. ` +
  `Mobile numbers have 10 digits and begin with 06, 08, or 09.`;

export const thailandAreaCodePrefixes1Quiz: FeatureQuiz = {
  id: "thailand-area-code-prefixes-1",
  name: "1-Digit Area Code Prefixes",
  description: DESCRIPTION,

  quizTopic: "Area Codes",
  kind: "feature",
  mapId: "thailand-area-code-prefixes-1",

  answerProperty: "area_code_prefix",
  answerType: "single",

  questions: THAILAND_AREA_CODE_PREFIX_1_QUESTIONS,
};
