/**
 * Feature quiz for Japan's 9 broad telephone area-code prefixes.
 *
 * Questions use each prefix's stable ID as the answer and the 0X-
 * notation as the player-facing display.
 */
import type { FeatureQuiz, FeatureQuizQuestion } from "@/types/quiz";

import { JAPAN_AREA_CODE_PREFIXES_BY_ID } from "./data/areaCodes";

const QUESTIONS: FeatureQuizQuestion[] = Object.entries(
  JAPAN_AREA_CODE_PREFIXES_BY_ID,
).map(([prefixId, prefix]) => ({
  answer: prefixId,
  display: prefix.name,
}));

const DESCRIPTION =
  `Learn all ${QUESTIONS.length} broad telephone area-code prefixes of Japan. ` +
  `Japanese landlines have 10 digits, but the geographic area-code portion varies in length by region. ` +
  `For example, Osaka uses 06-XXXX-XXXX, while the Chitose area uses 0123-XX-XXXX. ` +
  `This quiz groups geographic area codes by their first significant digit, shown as 01- through 09-.`;

export const japanAreaCodePrefixesQuiz: FeatureQuiz = {
  id: "japan-area-code-prefixes",
  name: "Area Code Prefixes",
  description: DESCRIPTION,

  kind: "feature",
  mapId: "japan-area-code-prefixes",

  answerProperty: "prefix_id",
  answerType: "single",

  questions: QUESTIONS,
};
