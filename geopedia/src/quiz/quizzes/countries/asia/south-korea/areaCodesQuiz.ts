import type { FeatureQuiz } from "@/types/quiz";

import { SOUTH_KOREA_AREA_CODE_QUESTIONS } from "./data/areaCodeQuestions";

const DESCRIPTION =
  `Learn all ${SOUTH_KOREA_AREA_CODE_QUESTIONS.length} geographic telephone ` +
  `area codes of South Korea. These codes are used for regional landline numbers, ` +
  `while mobile numbers use the nationwide 010 prefix. ` +
  `For example, a Seoul landline may be written as 02-1234-5678, ` +
  `a Busan landline as 051-987-6543, and a mobile number as 010-1234-5678. ` +
  `Use first-digit groups to study the area codes in smaller regional sets.`;

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
