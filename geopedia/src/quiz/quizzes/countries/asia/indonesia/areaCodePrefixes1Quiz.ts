/**
 * Quiz configuration for Indonesia's 1-digit landline area-code prefixes.
 */

import { FeatureQuiz } from "@/types/quiz";

import { INDONESIA_AREA_CODE_PREFIX_1_QUESTIONS } from "./data/area-code-prefixes";

const INDONESIA_AREA_CODE_PREFIXES_1_DESCRIPTION =
  `Learn the ${INDONESIA_AREA_CODE_PREFIX_1_QUESTIONS.length} 1-digit landline area-code ` +
  `prefixes of Indonesia. Indonesian landline numbers are 9-11 digits and use 0 + a 2-3 ` +
  `digit area code + a 6-8 digit local number, e.g. Jakarta 021-314-5678. ` +
  `Mobile numbers instead begin with 08.`;

export const indonesiaAreaCodePrefixes1Quiz: FeatureQuiz = {
  id: "indonesia-area-code-prefixes-1",
  name: "1-Digit Area Code Prefixes",
  description: INDONESIA_AREA_CODE_PREFIXES_1_DESCRIPTION,

  kind: "feature",
  mapId: "indonesia-area-code-prefixes-1",

  answerProperty: "prefix_1",
  answerType: "single",

  questions: INDONESIA_AREA_CODE_PREFIX_1_QUESTIONS,
};
