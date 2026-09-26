/**
 * Feature quiz for Japan's 59 telephone area-code regions.
 *
 * Questions use each normalized area code as the stable answer and
 * player-facing display. Area codes can be grouped by their broader
 * first-digit prefix.
 */
import type { FeatureQuiz, FeatureQuizQuestion } from "@/types/quiz";

import { JAPAN_AREA_CODES_BY_ID } from "./data/areaCodes";

const QUESTIONS: FeatureQuizQuestion[] = Object.entries(
  JAPAN_AREA_CODES_BY_ID,
).map(([areaCodeId, areaCode]) => ({
  answer: areaCodeId,
  display: areaCode.name,
}));

const DESCRIPTION =
  `Learn all ${QUESTIONS.length} telephone area-code regions of Japan. ` +
  `Japanese landlines have 10 digits, with geographic area codes of varying  ` +
  `lengths followed by local exchange and subscriber numbers. ` +
  `For example, Tokyo uses 03-XXXX-XXXX, while Kyoto uses 075-XXX-XXXX. ` +
  `This quiz focuses on the first two significant digits of each geographic area code.`;

export const japanAreaCodesQuiz: FeatureQuiz = {
  id: "japan-area-codes",
  name: "Area Codes",
  description: DESCRIPTION,

  kind: "feature",
  mapId: "japan-area-codes",

  answerProperty: "area_code_id",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "prefix",
        label: "Prefix",
        valueType: "string",
      },
    ],
  },

  questions: QUESTIONS,
};
