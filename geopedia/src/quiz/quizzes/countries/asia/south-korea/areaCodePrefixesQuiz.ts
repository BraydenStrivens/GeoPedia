import type { FeatureQuiz } from "@/types/quiz";

import { SOUTH_KOREA_AREA_CODE_PREFIX_QUESTIONS } from "./data/areaCodeQuestions";

const DESCRIPTION =
  `Learn the ${SOUTH_KOREA_AREA_CODE_PREFIX_QUESTIONS.length} first-digit ` +
  `geographic telephone area-code regions of South Korea.`;

export const southKoreaAreaCodePrefixesQuiz: FeatureQuiz = {
  id: "south-korea-area-code-prefixes",
  name: "1-Digit Area Code Prefixes",
  description: DESCRIPTION,
  kind: "feature",

  mapId: "south-korea-area-code-prefixes",

  answerProperty: "area_code_prefix",
  answerType: "single",

  questions: SOUTH_KOREA_AREA_CODE_PREFIX_QUESTIONS,
};
