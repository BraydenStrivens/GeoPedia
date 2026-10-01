/**
 * Quiz configuration for Vietnam's two-digit telephone area-code prefixes.
 *
 * Uses regions created by dissolving provinces that share the same first
 * two area-code digits.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { VIETNAM_AREA_CODE_PREFIX_2_QUESTIONS } from "./data/area-codes";

const DESCRIPTION =
  `Learn all ${VIETNAM_AREA_CODE_PREFIX_2_QUESTIONS.length.toLocaleString()} two-digit ` +
  `telephone area-code prefixes of Vietnam. Domestic landline numbers are 10 digits ` +
  `including the leading 0; landline area codes start with 02, while cell phone numbers ` +
  `do not. For example, a Nghệ An landline may be 0238 444 5678, placing its 0238 area ` +
  `code in the 023- prefix region.`;

export const vietnamAreaCodePrefixes2Quiz: FeatureQuiz = {
  id: "vietnam-area-code-prefixes-2",
  name: "2-Digit Area Code Prefixes",
  description: DESCRIPTION,

  quizTopic: "Area Codes",
  kind: "feature",
  mapId: "vietnam-area-code-prefixes-2",

  answerProperty: "area_code_prefix",
  answerType: "single",

  questions: VIETNAM_AREA_CODE_PREFIX_2_QUESTIONS,
};
