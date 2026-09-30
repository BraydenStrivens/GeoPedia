/**
 * Quiz configuration for Malaysia's 1-digit telephone area-code prefixes.
 */

import { FeatureQuiz } from "@/types/quiz";

import { MALAYSIA_AREA_CODE_PREFIX_1_QUESTIONS } from "./data/area-codes";

const MALAYSIA_AREA_CODE_PREFIXES_1_DESCRIPTION =
  `Learn all ${MALAYSIA_AREA_CODE_PREFIX_1_QUESTIONS.length} first-digit prefixes of ` +
  `Malaysia's geographic landline area codes. Landline numbers are 10 digits including ` +
  `the area code; for example, 082-123 4567 is a landline, while a mobile number such ` +
  `as 012-345 6789 begins with 01 and is not geographically tied to a state.`;

export const malaysiaAreaCodePrefixes1Quiz: FeatureQuiz = {
  id: "malaysia-area-code-prefixes-1",
  name: "1-Digit Area Code Prefixes",
  description: MALAYSIA_AREA_CODE_PREFIXES_1_DESCRIPTION,

  quizTopic: "Area Codes",
  kind: "feature",
  mapId: "malaysia-area-code-prefixes-1",

  answerProperty: "area_code",
  answerType: "single",

  questions: MALAYSIA_AREA_CODE_PREFIX_1_QUESTIONS,
};
