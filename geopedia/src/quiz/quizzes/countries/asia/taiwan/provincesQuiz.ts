/**
 * Feature quiz for Taiwan's 7 province-level divisions.
 *
 * Questions use each division's stable canonical ID as the answer and
 * provide both English and Traditional Chinese player-facing names.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { TAIWAN_PROVINCE_QUESTIONS } from "./data/admin";

const DESCRIPTION =
  `Learn all ${TAIWAN_PROVINCE_QUESTIONS.length} province-level divisions ` +
  `of Taiwan. 省 (shěng) means province, while 市 (shì) means city and is ` +
  `used in the names of the special municipalities.`;

export const taiwanProvincesQuiz: FeatureQuiz = {
  id: "taiwan-provinces",
  name: "省 (Shěng) (Provinces)",
  description: DESCRIPTION,

  kind: "feature",
  mapId: "taiwan-provinces",

  answerProperty: "province_id",
  answerType: "single",

  questions: TAIWAN_PROVINCE_QUESTIONS,
};
