import type { FeatureQuiz } from "@/types/quiz";

import { SOUTH_KOREA_AREA_CODE_QUESTIONS } from "./data/areaCodeQuestions";

const DESCRIPTION =
  `Learn all ${SOUTH_KOREA_AREA_CODE_QUESTIONS.length} geographic telephone ` +
  `area codes of South Korea. Use first-digit groups to study them in smaller ` +
  `regional sets.`;

export const southKoreaAreaCodesQuiz: FeatureQuiz = {
  id: "south-korea-area-codes",
  name: "Area Codes",
  description: DESCRIPTION,
  kind: "feature",

  mapId: "south-korea-area-codes",

  answerProperty: "province_id",
  answerType: "single",

  questions: SOUTH_KOREA_AREA_CODE_QUESTIONS,

  grouping: {
    properties: [
      {
        property: "area_code_prefix",
        label: "First Digit",
        valueType: "string",
      },
    ],
  },
};
