/**
 * Feature quiz for Ghana's geographic fixed-line area codes.
 *
 * The quiz uses the customary domestic notation 030 through 039. Several
 * current administrative regions share a code because Ghana's fixed-line
 * numbering areas reflect older regional boundaries.
 */

import type { FeatureQuiz } from "@/types/quiz";
import type { FeatureQuizQuestion } from "@/types/quiz";

/**
 * All geographic fixed-line area codes represented by Ghana's area-code map.
 */
export const GHANA_AREA_CODE_QUESTIONS: FeatureQuizQuestion[] = [
  { answer: "030" },
  { answer: "031" },
  { answer: "032" },
  { answer: "033" },
  { answer: "034" },
  { answer: "035" },
  { answer: "036" },
  { answer: "037" },
  { answer: "038" },
  { answer: "039" },
];

const DESCRIPTION =
  `Learn all ${GHANA_AREA_CODE_QUESTIONS.length} geographic fixed-line area ` +
  `codes of Ghana. Fixed-line numbers are commonly written with a leading ` +
  `0 followed by a 2-digit geographic code and the local number, such as ` +
  `032 for the Ashanti area or 038 for Upper East. Several of Ghana's ` +
  `current regions share codes because they were created by subdividing ` +
  `older administrative regions.`;

export const ghanaAreaCodesQuiz: FeatureQuiz = {
  id: "ghana-area-codes",
  name: "Landline Area Codes",
  description: DESCRIPTION,

  kind: "feature",
  mapId: "ghana-area-codes",

  answerProperty: "area_code",
  answerType: "single",

  questions: GHANA_AREA_CODE_QUESTIONS,
};
